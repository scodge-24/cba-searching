# Collection workflow — `gh` CLI installed

`gh` is present. Use it directly — it's authenticated, so rate limits are high (search: 30/min, core: 5000/hr). Confirm auth once:

```bash
gh auth status
```

If not logged in, either run `gh auth login`, or just use `workflow-no-gh.md` instead (the bundled script works unauthenticated). Don't block on it.

You came here from **SKILL.md Step 2** with a feature list `F1…FM`, a category, and the claimed differentiator. Collect, then return to **SKILL.md Step 3**.

## A. Search for candidates → X

Cast several nets — repo names rarely match the author's mental model. Use keyword, topic, and code search, sorted by stars, and dedupe into one set:

```bash
# keyword search on name/description/readme
gh search repos "<category keywords>" --sort stars --limit 40 \
  --json fullName,description,stargazersCount,language,url,updatedAt

# topic search (try the obvious topics for the category)
gh search repos --topic <topic-1> --topic <topic-2> --sort stars --limit 40 \
  --json fullName,description,stargazersCount,language,url

# code search — catches repos whose distinctiveness is in the code, not the pitch
gh search code "<distinctive symbol, import, or dependency>" --limit 30 --json repository,path
```

Run 3–6 query variants covering: the category noun, the **problem** it solves (not your solution), and obvious competitor names if known. Don't search only the project's brand name — it finds nothing and proves nothing. Do one `--sort updated` pass too, to catch fresh competitors, not just star incumbents.

## B. Triage to the genuinely similar set → X

From description / topics / stars / `updatedAt`, drop false positives: forks, tutorials, name collisions, archived or dead repos. What remains — repos that actually attempt the same job — is **X**. State the bar you used so X isn't hand-wavy.

## C. Profile the closest repos

For the closest ~5–10 (more detail for the nearest 2–4):

```bash
gh api repos/{owner}/{repo} --jq '{stars:.stargazers_count, forks:.forks_count, watchers:.subscribers_count, lang:.language, topics:.topics, issues:.open_issues_count, created:.created_at, pushed:.pushed_at, license:.license.spdx_id, homepage:.homepage, pages:.has_pages, archived:.archived}'
gh api repos/{owner}/{repo}/readme -H "Accept: application/vnd.github.raw"     # raw README
gh api "repos/{owner}/{repo}/git/trees/HEAD?recursive=1" --jq '.tree[].path'   # file tree = architecture shape
```

For each profiled repo, from the README + tree determine:

- **Feature coverage** — which of `F1…FM` it implements (✓ / partial / ✗).
- **Architecture** — how it actually does the job (in-process lib vs hosted service, API-per-call vs batched, plugin vs monolith, language/runtime). The file tree is your evidence.

**Read past the marketing.** READMEs are sales copy. "Revolutionary", "blazing-fast", "production-ready", "the first tool to…", emoji headers and a feature wishlist tell you nothing — and competitors spin just like the target does. Judge by evidence, not adjectives: what's actually in the tree, what the deps imply, whether tests/CI/releases exist, when it last shipped. State what the project **really is** in one plain sentence, not what it claims to be. Fetch a key source file when the README is thin or all hype:

```bash
gh api repos/{owner}/{repo}/contents/path/to/file -H "Accept: application/vnd.github.raw" | head -120
```

## D. Scout execution on the heavy overlappers (the part that actually matters)

Ideas are cheap; **execution is the moat.** For the repos that heavily overlap with the target (high feature coverage), scout execution:

```bash
gh api repos/{owner}/{repo}/releases/latest --jq '{tag:.tag_name, date:.published_at}'   # latest release (404 = none)
gh api "repos/{owner}/{repo}/contributors?per_page=1&anon=1" -i | grep -i '^link:'         # contributor count via Link rel=last
gh api "repos/{owner}/{repo}/git/trees/HEAD?recursive=1" --jq '.tree[].path' | grep -iE 'test|\.github/workflows|docs/'  # tests/CI/docs present?
```

Combine into an **execution read** per competitor:

- **Adoption** — stars, forks, watchers. Is anyone actually using it?
- **Aliveness** — `pushed_at` recency, `archived`, latest-release date. Maintained or a graveyard?
- **Maturity / polish** — tests, CI, docs/pages/homepage, releases, contributors, README depth, file count. A real product or a weekend prototype?

Capture the **target repo's own** execution read from the same signals (note if it's pre-release, untested, solo, days old). You'll compare target-vs-incumbent execution back in SKILL.

## Done

Hand back to **SKILL.md Step 3** with: the similar set **X**, the profiled closest repos with `F1…FM` coverage + architecture + **what each really is** (past the spin), and the **execution read** (adoption / aliveness / maturity) for each heavy overlapper and for the target itself.
