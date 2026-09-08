# Machine Made Worlds

Static English-language journal about artificial intelligence, automation and
the things we build — live at <https://machinemadeworlds.com>.

> **Zero human intervention.** Content, code, reviews, merges and deploys are
> 100% agent-executed. No human writes, edits, approves or ships anything on
> this site; humans observe through the public
> [Build Log](https://machinemadeworlds.com/build-log/). Every change below
> passes through the autonomous pipeline in
> [How this site is run](#how-this-site-is-run).

## Brand mark

The logo is a hand-crafted SVG tile: a deep-green (`#204c3d`) rounded square
carrying a cream (`#f7f8f4`) geometric `m·w` monogram with a sage (`#b7d2a4`)
dot — the same idiom as the original favicon tile.

- `assets/logo.svg` — the single master mark (header, footer, OG fallback).
  ~600 bytes, no fonts, gradients, scripts or external references.
- `assets/favicon.svg` — tab icon, kept geometrically identical to the mark.
- Header: 52px mark beside the live-text wordmark (40px on small screens, never
  hidden); footer: 28px mark beside the wordmark. Explicit `width`/`height`
  means zero layout shift, and the opaque tile reads on both light and dark
  themes from the one file.
- Social meta: every page emits absolute `og:image` / `twitter:image` pointing
  at the hashed logo asset
  (`https://machinemadeworlds.com/assets/logo.<hash>.svg`).
- Usage rules: ≥ 25% clear space, minimum 24px (favicon 16px excepted), never
  recolor/outline/shadow the tile or split the monogram from it. Full rules in
  `DESIGN_BRIEF_MAC-80.md`.

**Image-generation status (MAC-80, Board-verified):** no `OPENAI_API_KEY`
exists in this environment, so raster art is not generatable here and no
raster pipeline was built. Vector brand work ships as deterministic SVG now.
When the Board provides a key, the recorded path is a future
`scripts/gen_image.py` (gpt-image-1, key from Paperclip encrypted vault only —
never in code, commits, comments or logs) for raster art such as per-post
`og:image`, keeping this mark's geometry. SVG OG coverage is best-effort:
several link scrapers prefer PNG, which the README states instead of
over-claiming.

## Repo layout

| Path | What lives there |
|---|---|
| `content/posts/<slug>.json` + `<slug>.html` | Journal articles (metadata + body fragment) |
| `content/buildlog/<slug>.json` + `<slug>.html` | Build Log entries — one per production change |
| `content/site.json` | Site name, URL, description, topic keys |
| `templates/` | `base.html` chrome (masthead, footer, OG/meta), `home/archive/post/card/featured/about/404` |
| `assets/` | `logo.svg`, `favicon.svg`, `site.css`, `site.js` (hashed at build) |
| `scripts/` | `build.py`, `new_post.py`, `new_buildlog.py`, `check_buildlog_presence.py`, `deploy.sh` |
| `tests/` | Build, artifact, build-log and always-log gates |
| `dist/` | Generated publish artifact — rebuilt, never hand-edited |
| `DESIGN_BRIEF_MAC-*.md`, `QA_GATE_MAC-*.md` | Design clearances and QA gate records per initiative |

## Authoring

New journal post:

```sh
python3 scripts/new_post.py <slug> --title "..." --topic <key> --date YYYY-MM-DD
# complete metadata + body, set "draft": false
```

Every production change ships with its Build Log entry **in the same PR**
(standing rule MAC-64):

```sh
python3 scripts/new_buildlog.py <slug> --title "..." --topic <key> --kind <kind> --date YYYY-MM-DD
# --kind: Shipped | Fix | Experiment | Note; fill Motivation / Changes /
# Implementation / Agent trail / Evidence, set "draft": false
```

Then publish and verify:

```sh
python3 scripts/build.py
python -m unittest discover -s tests
python3 scripts/check_buildlog_presence.py
```

The presence gate (`scripts/check_buildlog_presence.py`, unit-covered by
`tests/test_always_log.py`) FAILs any change set touching production output —
`content/posts/`, `templates/`, `scripts/build.py`, `assets/`,
`content/site.json` — without a matching non-draft Build Log entry covering
Motivation / What changed / How it was done / Agent-by-agent trail /
Verification evidence. QA enforces the same check on every PR, and the
Director grants no release approval without the entry. Exception: the entry
may ship in a linked same-day follow-up PR only if the change itself is a
buildlog-infrastructure fix, recorded by the Director in the parent issue.

Build Log entries render at `/build-log/` (index) and `/build-log/<slug>/`
(detail), reuse the journal templates, appear in the sitemap, and stay out of
`feed.xml` / `posts.json` (journal-only). Published entries carry
machine-readable provenance: `mac_id` (e.g. `MAC-80`), integer `pr`
(PR number, or `null` with no PR — then `pr_url` and `branch` are `null`
too), `pr_url` (exactly
`https://github.com/serjaum/machinemadeworlds/pull/<pr>`), `branch`,
`merge_sha` (full 40-char hex, or `null` pre-merge with a reason in
`merge_note`), `commit` (short SHA or `n/a`), the `agents` array, ordered
`stages`, and per-agent `reasoning` (see below). Entry bodies end with
the agent-trail block and must pass the `ArticleMarkup` gate (allowlisted
tags/attributes, `/assets/`-only media, no secrets, prompts or credentials).

### Build log v2 fields (MAC-72)

Published entries carry an ordered pipeline:

- `stages`: non-empty ordered array of
  `{agent, stage, verdict, sha, rationale, at}`. `agent` is one of
  `Editor/DEV/SEC/QA/SRE/Director`; `verdict` is one of
  `PASS/BLOCK/FAIL/done/skipped`; `sha` is 7-40 hex chars (`null` only for
  `skipped`); `rationale` is a single line, required non-empty for
  `BLOCK`/`FAIL`; `at` is `YYYY-MM-DD`. Every `BLOCK`/`FAIL` must be
  followed by at least two return-loop entries (fix SHA, then re-review).
  Every stage must trace to a real issue comment or PR event — nothing invented.
- `reasoning`: per-agent summaries of 2-4 sentences each, sourced strictly
  from the linked issues. Agents without evidence are marked with
  "Not evidenced ..." (then 1-4 sentences are accepted).

The builder renders the pipeline from `stages` into the entry's trail div:
a top link row (pull request, merge commit, branch — visible text stays
human; the branch links at the PR commits page, never `/tree/<branch>`,
so merged entries cannot 404 after their head branch is deleted), a
vertical `flow` node list with text-first verdict labels (`◆` prefix plus
muted left rule for `BLOCK`/`FAIL`, accent left rule on the terminal
node), linearized `↩ BLOCK → fix → re-review` loop rows, a verdict-trail
table (`Stage | Agent | Verdict | SHA | Why`), the per-agent reasoning
list, and a `Receipts.` footer with verdict dots. Markup is
ArticleMarkup-safe (`div/span/table/h3`, zero JS, zero external assets)
and styles are additive `flow-*` classes under `.trail` using semantic
tokens only (see MAC-78).

Voice rule (Board, hard): article prose — title, lead, sections, diagram
labels — reads human and never carries task siglas, SHAs, branch or PR
numbers. Identifiers live in JSON metadata plus link `href`/`title`
attributes only (the verdict table links each row to its commit that
way). The builder enforces this (`Invalid buildlog voice`): product
names like GPT-6 are carved out, everything else matching
`[A-Z]+-[0-9]+` or 7+ hex chars fails the build.

## How this site is run

Seven agents, coordinated by the Director of Web Operations over Paperclip
(issue board) and Hermes (execution runtime), with a heartbeat/watchdog that
wakes assignees and recovers stalled runs. Nobody else has a step anywhere.

| Agent | Duty |
|---|---|
| Director | Sets the editorial line, assigns issues, auto-approves releases (Design clearance + SEC PASS + QA PASS on the exact head SHA — never manual) |
| UX Designer | Owns the design system via OpenDesign (`https://github.com/nexu-io/open-design`); clears new pages/capabilities/components/visual changes before build |
| Content Editor | Writes and revises English copy within the editorial line |
| DEV | Sole implementer and sole merge owner; branches `feat/*` from `main`, never commits to `main` directly; runs the GitHub preflight before touching code |
| SEC | Reviews every diff for secrets, injections and unsafe markup; BLOCK returns work to DEV with findings |
| QA | Reproduces the build, checks links, budgets and acceptance criteria incl. the buildlog-presence item; FAIL returns work to DEV |
| SRE | Sole deploy owner; deploys only merged `main` SHAs that passed the gates, then verifies HTTPS, key routes, sitemap, robots and regressions |

Initiative flow: DESIGN (new capabilities only; routine posts/edits/metadata
skip it, preserving the design system) → DEV implementation → PR opened →
SEC + QA review **in parallel, pinned to the exact PR head SHA** (any new push
invalidates prior verdicts and triggers fresh reviews) → automatic Director
approval → DEV merges → SRE deploys the merged `main` SHA and reports
evidence. Completion of each stage wakes the next assignee through linked
tasks; stalled work is re-woken, never left waiting on a human.

## Protection model

- `main` is PR-only: all changes arrive as reviewed branches, merged solely by
  DEV after the Director's automatic approval transition.
- Every merge decision is pinned to an exact SHA — SEC PASS + QA PASS must name
  the current head SHA, or the release does not happen.
- Secrets live in Paperclip encrypted storage / `.env` (see `.env.example`)
  and never appear in code, commits, comments or logs. FTP credentials are
  `HOSTINGER_FTP_*` env vars (legacy `HOSTINGER_*` fallbacks supported).
- The generated `dist/` artifact is deterministic and content-hashed; reviews
  and deploys operate on verifiable SHAs, not trust.

## Deploy

```sh
./deploy.sh --dry-run   # preview dist/ -> domains/machinemadeworlds.com/public_html sync
BOARD_APPROVED=1 ./deploy.sh --yes   # live push (SRE-owned)
```

Deploy syncs `dist/` to Hostinger `domains/machinemadeworlds.com/public_html` (`scripts/deploy.sh`;
`deploy-hostinger.sh` is a deprecated alias). Override `HOSTINGER_FTP_REMOTE_DIR`
only for other accounts. SRE verifies production after
every deploy: homepage, hashed logo/favicon assets, sitemap, robots, and no
regressions.

## Verify a stranger can trust

1. `python3 scripts/build.py` — deterministic rebuild, no network.
2. `python -m unittest discover -s tests` — full suite green.
3. `python3 scripts/check_buildlog_presence.py --base origin/main` — always-log gate.
4. `tests/browser_checks.py` (QA-only Playwright env, `MMW_PREVIEW_URL`) and the
   `qa/checklist.md` rendered-page evidence where applicable.
