#!/usr/bin/env python3
"""Search GitHub for prior art via the public REST API. Stdlib only.

No third-party deps and no hard dependency on the `gh` CLI. The GitHub REST API
works unauthenticated (search: 10 req/min); if a token is available the limits
rise (search: 30/min, core: 5000/hr). Token is resolved, never logged, in order:

    1. env  GITHUB_TOKEN  or  GH_TOKEN
    2. `gh auth token`    (only if the gh CLI happens to be installed)
    3. none               (unauthenticated — still works, just slower)

Subcommands:
    search   <query...> [--topic T]...   -> ranked, de-duped candidate repos
    profile  <owner/repo...>             -> meta + README + file tree per repo

Output is JSON on stdout. Errors and rate-limit notices go to stderr.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import NoReturn

API = "https://api.github.com"
UA = "cba-searching/0.2"
README_CAP = 4000
TREE_CAP = 250


def _warn(msg: str) -> None:
    print(msg, file=sys.stderr)


def _die(msg: str, code: int = 1) -> NoReturn:
    print(msg, file=sys.stderr)
    sys.exit(code)


def resolve_token() -> str:
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        return tok
    if shutil.which("gh"):
        try:
            out = subprocess.run(
                ["gh", "auth", "token"], capture_output=True, text=True, timeout=10
            )
            if out.returncode == 0 and out.stdout.strip():
                return out.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
    return ""


def api_get(path: str, token: str, accept: str = "application/vnd.github+json",
            with_headers: bool = False) -> object:
    url = path if path.startswith("http") else API + path
    req = urllib.request.Request(url)
    req.add_header("User-Agent", UA)
    req.add_header("Accept", accept)
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            body = raw if accept.endswith("raw") else json.loads(raw)
            return (body, dict(resp.headers)) if with_headers else body
    except urllib.error.HTTPError as e:
        remaining = e.headers.get("X-RateLimit-Remaining")
        if e.code == 403 and remaining == "0":
            reset = e.headers.get("X-RateLimit-Reset", "")
            hint = ""
            if reset.isdigit():
                wait = max(0, int(reset) - int(time.time()))
                hint = f" (resets in ~{wait}s)"
            raise RuntimeError(
                f"rate limited{hint}. Set GITHUB_TOKEN or install gh to raise limits."
            )
        if e.code == 404:
            raise RuntimeError("404 not found")
        if e.code == 422:
            raise RuntimeError(f"422 invalid query: {e.read().decode('utf-8','replace')[:160]}")
        raise RuntimeError(f"HTTP {e.code} for {path}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"network error: {e.reason}")


def repo_row(item: dict) -> dict:
    return {
        "full_name": item.get("full_name"),
        "description": item.get("description"),
        "stars": item.get("stargazers_count"),
        "language": item.get("language"),
        "topics": item.get("topics", []),
        "open_issues": item.get("open_issues_count"),
        "pushed_at": (item.get("pushed_at") or "")[:10],
        "url": item.get("html_url"),
        "archived": item.get("archived", False),
    }


def do_search(args, token: str) -> None:
    queries = list(args.queries)
    queries += [f"topic:{t}" for t in (args.topic or [])]
    if not queries:
        _die("provide at least one query or --topic")

    seen: dict[str, dict] = {}
    errors: list[str] = []
    for q in queries:
        params = urllib.parse.urlencode(
            {"q": q, "sort": args.sort, "order": "desc", "per_page": str(args.limit)}
        )
        try:
            data = api_get(f"/search/repositories?{params}", token)
        except RuntimeError as e:
            errors.append(f"[{q}] {e}")
            continue
        if not isinstance(data, dict):
            continue
        for item in data.get("items", []):
            row = repo_row(item)
            if args.min_stars and (row["stars"] or 0) < args.min_stars:
                continue
            key = row["full_name"]
            if key in seen:
                if q not in seen[key]["matched"]:
                    seen[key]["matched"].append(q)
            else:
                row["matched"] = [q]
                seen[key] = row
        time.sleep(1.0)  # search is the tightest-limited endpoint

    rows = sorted(seen.values(), key=lambda r: (r["stars"] or 0), reverse=True)
    print(json.dumps({
        "meta": {"queries": queries, "sort": args.sort, "count": len(rows), "errors": errors},
        "repos": rows,
    }, indent=2))


def tree_signals(paths: list[str]) -> dict:
    """Cheap execution signals derived from the file tree (no extra API calls)."""
    low = [p.lower() for p in paths]

    def any_has(*frags: str) -> bool:
        return any(any(f in p for f in frags) for p in low)

    return {
        "has_ci": any(".github/workflows/" in p or p in
                      (".gitlab-ci.yml", ".circleci/config.yml", ".travis.yml") for p in low),
        "has_tests": any_has("test/", "tests/", "_test.", ".test.", "spec/", "__tests__"),
        "has_docs": any_has("docs/", "documentation/", "mkdocs.yml", "docusaurus"),
        "has_examples": any_has("example", "demo/", "samples/"),
        "has_changelog": any_has("changelog"),
        "file_count": len(paths),
    }


def link_last_count(path: str, token: str) -> int | None:
    """Read total item count from the Link rel=last header (page-1, per_page=1)."""
    try:
        body, headers = api_get(path, token, with_headers=True)  # type: ignore[misc]
    except RuntimeError:
        return None
    link = headers.get("Link", "") if isinstance(headers, dict) else ""
    for part in link.split(","):
        if 'rel="last"' in part:
            m = part.split("page=")
            if len(m) > 1:
                num = m[-1].split(">")[0].split("&")[0]
                if num.isdigit():
                    return int(num)
    return len(body) if isinstance(body, list) else None


def profile_one(slug: str, token: str, execution: bool = False) -> dict:
    out: dict = {"full_name": slug}
    try:
        meta = api_get(f"/repos/{slug}", token)
    except RuntimeError as e:
        return {"full_name": slug, "error": str(e)}
    branch = "HEAD"
    if isinstance(meta, dict):
        lic = meta.get("license") or {}
        out.update({
            "stars": meta.get("stargazers_count"),
            "forks": meta.get("forks_count"),
            "watchers": meta.get("subscribers_count"),
            "language": meta.get("language"),
            "topics": meta.get("topics", []),
            "open_issues": meta.get("open_issues_count"),
            "created_at": (meta.get("created_at") or "")[:10],
            "pushed_at": (meta.get("pushed_at") or "")[:10],
            "license": lic.get("spdx_id") if isinstance(lic, dict) else None,
            "homepage": meta.get("homepage") or None,
            "has_pages": meta.get("has_pages", False),
            "description": meta.get("description"),
            "url": meta.get("html_url"),
            "archived": meta.get("archived", False),
        })
        branch = meta.get("default_branch", "HEAD")

    try:
        readme = api_get(f"/repos/{slug}/readme", token, accept="application/vnd.github.raw")
        text = readme.decode("utf-8", "replace") if isinstance(readme, bytes) else ""
        out["readme"] = text[:README_CAP] + ("…" if len(text) > README_CAP else "")
        out["readme_chars"] = len(text)
    except RuntimeError:
        out["readme"] = None
        out["readme_chars"] = 0

    try:
        tree = api_get(f"/repos/{slug}/git/trees/{branch}?recursive=1", token)
        if isinstance(tree, dict):
            paths = [t["path"] for t in tree.get("tree", []) if t.get("type") == "blob"]
            out["truncated_tree"] = bool(tree.get("truncated")) or len(paths) > TREE_CAP
            out["signals"] = tree_signals(paths)
            out["tree"] = paths[:TREE_CAP]
    except RuntimeError:
        out["tree"] = None

    if execution:
        # +2 API calls: only worth spending on the heavy-overlap competitors.
        rel = None
        try:
            latest = api_get(f"/repos/{slug}/releases/latest", token)
            if isinstance(latest, dict):
                rel = {"tag": latest.get("tag_name"), "date": (latest.get("published_at") or "")[:10]}
        except RuntimeError:
            rel = None
        out["latest_release"] = rel
        out["contributors"] = link_last_count(f"/repos/{slug}/contributors?per_page=1&anon=1", token)
        time.sleep(0.4)
    return out


def do_profile(args, token: str) -> None:
    results = []
    for slug in args.repos:
        slug = slug.strip().removeprefix("https://github.com/").strip("/")
        results.append(profile_one(slug, token, execution=args.execution))
        time.sleep(0.4)
    print(json.dumps({"profiles": results}, indent=2))


def main() -> None:
    p = argparse.ArgumentParser(description="GitHub prior-art search (stdlib only).")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="search repos by query/topic")
    s.add_argument("queries", nargs="*", help="GitHub search queries (qualifiers allowed)")
    s.add_argument("--topic", action="append", help="repeatable; adds topic:<T> search")
    s.add_argument("--sort", default="stars", choices=["stars", "forks", "updated"])
    s.add_argument("--limit", type=int, default=30, help="results per query (max 100)")
    s.add_argument("--min-stars", type=int, default=0)
    s.set_defaults(func=do_search)

    pr = sub.add_parser("profile", help="meta + README + tree for repos")
    pr.add_argument("repos", nargs="+", help="owner/repo slugs")
    pr.add_argument("--execution", action="store_true",
                    help="also scout execution: latest release + contributor count (+2 calls/repo)")
    pr.set_defaults(func=do_profile)

    args = p.parse_args()
    token = resolve_token()
    if not token:
        _warn("note: no token (env GITHUB_TOKEN/GH_TOKEN or gh) — using lower unauth limits")
    args.func(args, token)


if __name__ == "__main__":
    main()
