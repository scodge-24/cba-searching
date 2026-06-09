# cba-searching

**AI-powered competitive intelligence for builders who can't be arsed to search.**

A [Claude Code](https://claude.com/claude-code) skill that runs instant **competitor analysis** and **market validation** on your repo — before you waste another weekend reinventing something with 4,000 stars.

> You had the idea. Did you have the search? `cba-searching` does it for you.

---

## The pitch

Every day someone ships "the first tool that does X." It's usually the fifteenth. `cba-searching` is your automated **market-research analyst**, **prior-art scanner**, and **brutally honest co-founder** rolled into one slash command. Point it at a repo or an idea and it will:

- 🔭 **Scan the landscape** — searches GitHub for every similar project and counts the field.
- 🧬 **Feature-overlap analysis** — maps your features against the incumbents and tells you exactly how much overlap exists.
- 🏗️ **Architecture teardown** — reads past the README spin to figure out what each project *really is*.
- 📈 **Execution due-diligence** — adoption, maintenance, releases, test coverage. Because **ideas don't win — execution does.**
- ⚖️ **Go / no-go verdict** — a blunt, evidence-backed call on whether you've found a gap or just rebuilt a wheel.

It opens with the number that matters:

> **I found 7 similar repositories, of which 4 share 5+ of your features and 2 fully cover your application.**

…and closes with one quotable line you can paste straight into the comment thread.

---

## Why builders use it

- **Validate before you build.** Kill the dead-on-arrival project on day zero, not after launch.
- **Find the real gap.** If the incumbents are stale, untested, and abandoned, that *is* your opening — `cba-searching` finds it.
- **Stop arguing on Reddit.** It's a meme-ready reality check for "I built a revolutionary new agent tool" posts. Drop the verdict, move on.

---

## Install

```bash
git clone https://github.com/scodge-24/cba-searching.git ~/.claude/skills/cba-searching
```

Or symlink your local checkout:

```bash
ln -s /path/to/cba-searching ~/.claude/skills/cba-searching
```

That's it. Zero dependencies — the no-`gh` path is **stdlib Python only** and hits GitHub's public API with no auth required. If you have the [GitHub CLI](https://cli.github.com/) installed it'll use that automatically for higher rate limits.

## Use

```
/cba-searching
```

Run it inside the repo you want to check, or just describe the idea. It does the rest.

---

## How it works

1. **Familiarize** — reads the README / `AGENTS.md` / `CLAUDE.md` / manifest to learn what the thing actually is (concept + architecture, not a line-by-line code read).
2. **Search** — GitHub repo, topic, and code search across multiple query angles.
3. **Profile** — feature coverage + architecture + execution signals (stars, forks, last release, contributors, tests/CI/docs) for the closest matches.
4. **Judge** — three questions: real unsolved problem? actually unique? better executed than what exists?
5. **Verdict** — ship it, shelve it, or "you just rebuilt `awesome-existing-tool`."

---

## We ran it on itself (it was not kind)

Obviously the first thing we did was point `cba-searching` at its own repo. The verdict it returned:

> **I found 7 similar repositories, of which 1 shares 4+ of its 8 features and 0 fully cover the application.**

The one that matters: **[r14dd/patent](https://github.com/r14dd/patent)** (360★, Rust, tested, CI, actively shipping) — prior-art search for code ideas across 11 package registries with an Open / Crowded / Saturated verdict. If you want a mature, multi-registry, battle-tested tool, genuinely go use it. It's excellent and it's further along than this.

So why does this exist? **Execution scoring.** `cba-searching` doesn't just count similar repos — it grades the *incumbents*: stars, releases, tests, CI, contributors, maintained-vs-graveyard. `patent` tells you the space is crowded; `cba-searching` tells you whether the crowd is **asleep** — which is the only thing that decides whether a "done" idea is still worth building. That's the gap, and it's the whole pitch.

The skill's own closing line about itself:

> *"…everything else is a Claude-skill repackage with zero tests and zero stars. Build the execution-scoring angle or don't build at all — the search box you're selling would've told you `patent` existed in 30 seconds."*

So we built the execution-scoring angle. You're looking at it. (Tests and stars: still pending. Baby steps.)

---

<sub>Yes — this README is exactly the kind of buzzword-stuffed marketing spin the skill is built to see through. It ran on itself anyway and lived. Run it on <em>your</em> repo and find out if yours does.</sub>
