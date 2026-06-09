# Collection workflow — no `gh` CLI (default path)

`gh` is not installed. Use the bundled, dependency-free script `scripts/gh_prior_art.py` — stdlib Python only, no install. It talks to GitHub's public REST API, which works **unauthenticated** (search: ~10 requests/min). If `GITHUB_TOKEN`/`GH_TOKEN` happens to be set the limits rise, but nothing here requires it.

Resolve the absolute path to `scripts/gh_prior_art.py` in this skill's directory and run it from there.

You came here from **SKILL.md Step 2** with a feature list `F1…FM`, a category, and the claimed differentiator. Collect, then return to **SKILL.md Step 3**.

## A. Search for candidates → X

Cast several nets — repo names rarely match the author's mental model. One run can take multiple queries and topics:

```bash
python3 scripts/gh_prior_art.py search \
  "<category keywords>" "<problem it solves, not the solution>" "<known competitor name>" \
  --topic <topic-1> --topic <topic-2> \
  --sort stars --limit 30
```

- Queries accept GitHub search qualifiers, e.g. `"markdown notes language:python stars:>20"`.
- Run 3–6 variants covering: the category noun, the **problem** (not your solution), and obvious competitor names if known. Don't search only the project's brand name — it finds nothing and proves nothing.
- Also do one `--sort updated` pass to catch fresh competitors entering the lane, not just star incumbents.
- Output is JSON: `{meta:{...,errors}, repos:[{full_name, description, stars, language, topics, pushed_at, url, archived, matched}]}`. Check `meta.errors` (rate-limit or bad-query notices). If rate-limited, wait the stated seconds or set a token.

## B. Triage to the genuinely similar set → X

From description / topics / stars / `pushed_at`, drop false positives: forks, tutorials, name collisions, archived or dead repos (0 stars, no push in years). What remains — repos that actually attempt the same job — is **X**. State the bar you used so X isn't hand-wavy.

## C. Profile the closest repos

For the closest ~5–10 (more detail for the nearest 2–4):

```bash
python3 scripts/gh_prior_art.py profile owner/repo-a owner/repo-b owner/repo-c
```

Returns per repo: `stars, forks, watchers, language, topics, open_issues, created_at, pushed_at, license, homepage, has_pages, description, readme` (first ~4k chars), `readme_chars`, `signals` (`has_ci/has_tests/has_docs/has_examples/has_changelog/file_count`, derived free from the tree), and `tree` (file paths = architecture shape; `truncated_tree` flags big repos).

For each profiled repo, from the README + tree determine:

- **Feature coverage** — which of `F1…FM` it implements (✓ / partial / ✗).
- **Architecture** — how it actually does the job (in-process lib vs hosted service, API-per-call vs batched, plugin vs monolith, language/runtime). The file tree is your evidence.

**Read past the marketing.** READMEs are sales copy. "Revolutionary", "blazing-fast", "production-ready", "the first tool to…", emoji headers and a feature wishlist tell you nothing — and competitors spin just like the target does. Judge by evidence, not adjectives: what's actually in the `tree`, what the deps imply, whether tests/CI/releases exist, when it last shipped. State what the project **really is** in one plain sentence ("a thin wrapper around X with a CLI", "a fancy README and 40 lines of glue"), not what it claims to be. If a README is thin or all hype, fetch a key source file to see the substance:

```bash
curl -s "https://raw.githubusercontent.com/owner/repo/HEAD/path/to/file" | head -120
```

## D. Scout execution on the heavy overlappers (the part that actually matters)

Ideas are cheap; **execution is the moat.** For the repos that heavily overlap with the target (high feature coverage), add the execution scout — only on these, since it costs +2 API calls each:

```bash
python3 scripts/gh_prior_art.py profile owner/heavy-1 owner/heavy-2 --execution
```

Adds `latest_release` (tag + date) and `contributors` count. Combine with the free signals into an **execution read** per competitor:

- **Adoption** — stars, forks, watchers. Is anyone actually using it?
- **Aliveness** — `pushed_at` recency, `archived`, `latest_release` date. Maintained or a 2022 graveyard?
- **Maturity / polish** — `has_tests`, `has_ci`, `has_docs`/`has_pages`/`homepage`, `latest_release`, `contributors`, README depth (`readme_chars`), `file_count`. A real product or a weekend prototype?

Capture the **target repo's own** execution read from the same signals (you already saw its tree/README in SKILL Step 1; note if it's pre-release, untested, solo, days old). You'll compare target-vs-incumbent execution back in SKILL.

## Done

Hand back to **SKILL.md Step 3** with: the similar set **X**, the profiled closest repos with `F1…FM` coverage + architecture + **what each really is** (past the spin), and the **execution read** (adoption / aliveness / maturity) for each heavy overlapper and for the target itself.
