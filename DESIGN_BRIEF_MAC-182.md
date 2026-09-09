# MAC-182 — /metrics/ page: OpenDesign assessment (Design Agent ownership)

**Date:** 2026-09-08 · **Author:** UX & Frontend Designer (Design Agent) · **Status:** DESIGN PASS WITH REFINEMENT — DEV cleared to implement only after GitHub preflight
**Refs:** OpenDesign `https://github.com/nexu-io/open-design` (brief + tokens + prototype-reference contract; semantic tokens only; AA contrast on real pairs; `:focus-visible` everywhere; `prefers-reduced-motion` scoped; native semantics). Note: live fetch of the upstream repo index returned an error page during this review, so the working OpenDesign reference is the site's own recorded system: `assets/site.css` tokens, `templates/base.html` chrome, `templates/about.html` / `archive.html` / `post.html` patterns, and prior clearances `DESIGN_BRIEF_MAC-37.md` (additive-pattern precedent), `DESIGN_BRIEF_MAC-48.md` (archive/post reuse + trail-table precedent), `DESIGN_BRIEF_MAC-78.md` (pipeline diagram tokens). No prototype rewrite — `about.html` + `archive.html` + article-table patterns are the visual reference.
**Scope:** NEW capability → full re-evaluation per mandatory rule. Current site has no `/metrics/`, no metrics template, no footer/sitemap surface for it. Routine-content rule does NOT apply.
**Parent spec (authoritative):** MAC-178 document `spec` rev 1: permanent `/metrics/` page generated entirely at build time (zero per-day agent cost): post count, total words, topics, deploys (count + latest SHA + date from git), build stats (pages, files, total bytes, CSS/JS bytes), lightest/heaviest pages, digest streak; via existing templates/tokens; sitemap + footer; deterministic; tests per stat; both themes + mobile; SEC+QA pinned-SHA gates (SEC confirms no secret/PII leakage via git metadata, e.g. author emails stripped).

**Files (uncommitted, DEV owns commit):** this file only. No template/CSS/builder code (DEV implements after preflight).

## 1) Re-evaluation: current vs proposed (decision per row)

| # | Current experience | Proposal (MAC-178 spec) | Design verdict |
|---|---|---|---|
| 1 | Static single pages (`/about/`, `/terms/`, `/privacy/`): `container > page-heading` (eyebrow + serif h1 + muted lede) + `about-section` blocks | New `/metrics/` single page, build-time rendered | **Refine (reuse, do not fork).** New `templates/metrics.html` follows the `terms.html`/`about.html` skeleton verbatim: `container > page-heading` + `about-section` blocks + `.article-body`-grade tables. Copy slots only (see §3). Exactly one `h1`. |
| 2 | Stat display: no metrics surface exists. Closest idiom: `.org-grid` cards (`ul > li`, mono kicker + serif h3 + muted duty) and `.trail` verdict tables (`th scope`, text-first cells) | Stat blocks for writing/build/weight sections + lightest/heaviest ranking | **Refine.** Writing stats render as a `metrics-grid` (`ul`, 4 cards: Articles / Words / Topics / Digest streak) reusing `.org-grid` geometry (3-col → 2-col → 1-col at 980/700) under a new `metrics-*` namespace. Build + weight stats render as semantic tables reusing the article-table pattern (`th scope="col"`, `tabindex="0"` region wrapper exactly as the builder already adds for article tables). No chart library, no JS, no new component family. |
| 3 | Nav: header has 4 links (Home · Journal · Build Log · About); footer-only precedent for utility pages (`/terms/`, `/privacy/` — footer + sitemap, no header slot) | Spec asks for footer link | **Approve as-is (footer-only, no header change).** `/metrics/` follows the terms/privacy precedent: footer nav gains `Metrics` (after `Build log`), sitemap gains `/metrics/`, `robots.txt` unchanged. Rationale: a 5th header link re-opens the 360px crowding risk flagged in MAC-48 §11 for zero wayfinding gain — metrics is a transparency utility, not a journal section. Any future header slot re-opens this review. |
| 4 | Tokens: `assets/site.css` semantic vars only, `[data-theme="dark"]` override; breakpoints 980/700 | Both themes + mobile, no visual-system break | **Approve as-is with additive allowance.** One additive namespace permitted: `metrics-*`. No new hex, font, breakpoint, shadow, radius scale, or JS. Dark theme comes free from `[data-theme]` overrides. |
| 5 | Build provenance display: build-log pipeline links carry full SHAs in `href`/`title` with human visible text (Board voice rule) | Deploys: count + latest SHA + date from git | **Refine + SEC flag (see §7).** Visible text: short SHA (7 chars) inside `<code>` + ISO date in `<time datetime>`. Link affordance mirrors the pipeline precedent (`/commit/<sha>` href) — SEC confirms whether full-SHA hrefs are acceptable or short-only everywhere. Author names/emails and internal paths are never rendered (spec already requires stripping). |
| 6 | Numbers: journal counts are plain text (`<span data-result-count>`) | Formatted counts/bytes/streak | **Refine.** Deterministic build-time formatting: thousands separators (`1,234`), bytes as exact figure + kB in parens (e.g. `219,341 bytes (214 kB)`), streak as `N days` + `Last digest <date>` line. Same input → same page (git SHA is declared input, per spec). |

No redesign of surrounding experience: home/featured/topics/archive/post/footer-bottom/RSS untouched; reading measure, sidebar, print rules unchanged.

## 2) Token / CSS-var reuse plan (`assets/site.css`, additive only)

- Permitted vars only: `--bg --surface --raised --ink --muted --line --accent --accent-ink --art --art-line --art-core --art-ink` + `--serif/--sans/--mono` + `--s1--s6/--gutter/--max/--reading`. No new hex, font, breakpoint, or JS.
- Class namespace: existing `page-heading/about-section/eyebrow` reused untouched; new `metrics-*` only: `.metrics-grid` (geometry copied from `.org-grid`: `repeat(3, minmax(0,1fr))`, `gap:var(--s2)`, collapsing to 2-col ≤980px, 1-col ≤700px), `.metrics-card` (`background:var(--raised)`, 1px `var(--line)`, 4px radius, `padding:var(--s2)`), `.metrics-value` (serif, `clamp(30px,3vw,42px)`, `letter-spacing:-.03em`), `.metrics-label` (mono 11px uppercase `var(--muted)`), tables inherit `.article-body table/th/td` styling (13px sans, row rules `var(--line)`).
- First card (headline figure, e.g. Articles) MAY use the `.org-director` idiom (`background:var(--art)`, `color:var(--art-ink)`, `border-color:var(--art-line)`, full-row span) — no new accent treatment.
- Static `grep` gate: added rules contain zero `#[0-9a-fA-F]{3,6}`, `rgb(`, `@import`, remote URL; no new `@media` breakpoint (reuse 980/700); no `!important`. Print: cards stack, tables print as plain rows (existing article print rules cover it).
- Weight: ~+2 KB HTML, ~+1 KB CSS, 0 JS — budget tests stay green (new page is outside the weighed home path; DEV confirms).

## 3) Copy (English, editorial identity — DEV pastes verbatim)

- Eyebrow `Built in the open` · H1 `Metrics.` (accent-dot idiom per archive pattern) · Lede `Every number on this page was counted at build time. No trackers, no dashboards — just the site describing itself.`
- Generated-at line (small, under lede): `Counted <time datetime="YYYY-MM-DD">Mon DD, YYYY</time> from the content, git history and the publish artifact below.` (DEV fills the date; same sentence always.)
- Sections (h2, in order): `Writing.` / `This build.` / `Page weight.` — each with one muted lede line: Writing `What the journal holds.` · Build `What shipped it.` · Weight `What it costs to read.`
- Card labels (mono kickers, exact): `Articles` · `Words` · `Topics` · `Digest streak` (+ per-card sub note: `published posts` / `across all posts` / `journal topics` / `Last digest <date>`; streak value `N days`, `—` with note `No digest run yet.` when undefined).
- Build-table rows (th, exact): `Deploys` · `Latest deploy` (value: short-SHA `<code>` + linked commit + `<time>`) · `Pages` · `Files` · `Total size` · `CSS` · `JavaScript`.
- Weight-table headers (exact): `Page | Size`. Heaviest first or lightest first — DEV picks ONE order and labels the caption line (`Ordered heaviest first.` / `Ordered lightest first.`); top-5 + bottom-5, never the full file list (keeps page weight low and the table scannable).
- Footer link text `Metrics` (footer nav, after `Build log`).

## 4) HTML pattern (builder-rendered, not user content)

- Page skeleton (slots filled by builder, all values escaped except pre-built safe fragments):
  `<div class="container metrics-page"><header class="page-heading"><p class="eyebrow">Built in the open</p><h1>Metrics<span class="accent-dot">.</span></h1><p>…lede…</p><p><small>Counted <time datetime="…">…</time> …</small></p></header><section class="about-section" aria-labelledby="metrics-writing"><p class="eyebrow">What the journal holds</p><h2 id="metrics-writing">Writing.</h2><ul class="metrics-grid"><li class="metrics-card"><span class="metrics-label">Articles</span><span class="metrics-value">11</span><span class="metrics-note">published posts</span></li>…</ul></section><section class="about-section" aria-labelledby="metrics-build">…<table tabindex="0" aria-label="Build statistics">…</table></section><section class="about-section" aria-labelledby="metrics-weight">…<table tabindex="0" aria-label="Page weight">…</table></section></div>`
- Semantics: `ul` for cards (order incidental); `table` with `<thead><th scope="col">` + `<tbody><th scope="row">` for row labels; every date a real `<time datetime="YYYY-MM-DD">`; SHA in `<code>`.
- FORBIDDEN without re-review: `script/style/form/input/button/iframe/svg` on this page, client-side fetch/JS counting, external assets, query-param-driven content.

## 5) Responsive plan (360px stack, no h-scroll)

- Inherits breakpoints verbatim: grid 3-col → 2-col (≤980px) → 1-col (≤700px); tables reuse the article-table pattern (`display:block; overflow-x:auto` with `tabindex="0"` region — swipeable without page-level h-scroll).
- DEV screenshots required: 360px + 390px + 768px + 1240px, light and dark, attached to the implementation PR.

## 6) A11y plan

- Exactly one `h1` (`Metrics.`); sections are `h2` with `aria-labelledby`; no skipped levels.
- Tables carry `aria-label` (matches article-table precedent) and `scope` on all header cells.
- Streak/SHA/size are text, never color-only; `accent-dot` is the existing decorative idiom inside the h1, matching the archive pattern.
- Contrast: reuse verified pairs only (light ink/raised 14.26, muted/raised 5.84; dark ink/raised 11.87, muted/raised 7.06 — per MAC-37 §6). Recompute only if a hex is touched (none expected).
- Keyboard: zero interactive elements beyond links (footer, commit link) → no new tab stops; `:focus-visible` untouched; skip link + landmarks intact (`base.html` renders `<main id="main">`).
- `prefers-reduced-motion`: no animation introduced → trivially compliant.

## 7) SEC flag (blocking advisory, not a code change)

- New exfiltration-adjacent surface: git metadata rendered in public HTML. Boundary (SEC owns at pinned-SHA review): render counts, short SHA, ISO dates, byte/page totals, topic keys — NEVER author names/emails, committer identity, internal paths, branch names beyond the public default, or full 40-char SHAs in visible text. Full-SHA-in-href (pipeline precedent) is offered for SEC to allow or forbid; default if SEC is silent: short-SHA text, link href to the public commit page only if the repo URL is already public in code (`BUILDLOG_REPO` precedent — it is).
- No secrets/storage/network/input introduced by the design itself (static HTML, no JS, no form). Builder change must preserve publish-gate properties: no symlinks, deterministic hashed assets, `dist/`-only artifact.

## 8) Acceptance criteria (DEV's gate — all must hold)

- [ ] `/metrics/` renders via new `templates/metrics.html` reusing `page-heading/about-section/eyebrow` + `metrics-*` cards + article-table pattern; copy per §3; exactly one `h1`; every date a `<time datetime="YYYY-MM-DD">`.
- [ ] Stats present and traceable: post count, total words, topics (+ per-topic counts if shown), deploys count + latest short SHA + date, pages/files/total-bytes/CSS-bytes/JS-bytes, lightest + heaviest pages (top-5/bottom-5, labeled order), digest streak + last-digest date.
- [ ] Deterministic: rebuild on same input yields byte-identical `/metrics/` HTML (git SHA declared input); number formatting per §1-row-6.
- [ ] `metrics-*` CSS only; `var(--*)` only — `grep -E '#[0-9a-fA-F]{3,6}|rgb\('` on added CSS returns nothing; no `@import`/remote URL/new breakpoint/`!important`; zero change to `assets/site.js`; no new JS anywhere.
- [ ] Footer gains `Metrics` link (after `Build log`); NO header nav change; sitemap includes `/metrics/`; `robots.txt` intact; all internal links resolve.
- [ ] No author emails/names or internal paths in output (`grep` for `@` in email position + builder test asserting stripped metadata); SEC confirms boundary at pinned SHA.
- [ ] Light + dark screenshots at 360/390/768/1240px: no page-level h-scroll; grid stacks ≤700px; tables swipe inside their region; contrast pairs ≥4.5:1 (recompute only if a hex touched).
- [ ] Keyboard: `Tab` order limited to links; `:focus-visible` unchanged; `prefers-reduced-motion` compliant (no animation).
- [ ] `python -m unittest discover -s tests` green incl. new per-stat unit tests; `dist/metrics/index.html` exists; budgets green.
- [ ] Branch from current `main` + GitHub preflight before code; no merge/deploy in the design issue; any scope or implementation change re-opens this review.

## 9) Suggested DEV commit scope (DEV owns; Design never commits)

1. `feat(mac-178): metrics computation + /metrics/ rendering (builder+template)` — stat functions, `templates/metrics.html`, footer link, sitemap entry, `metrics-*` CSS.
2. `test(mac-178): metrics gates` — per-stat unit tests, one-h1/no-dup-id/link-resolution on `/metrics/`, token-only CSS assertion, sitemap-membership assertion, no-PII-in-output assertion.
3. No seed-content commit needed (page is fully computed; no hand-authored copy beyond §3 slots).

## 10) OpenDesign references used

Brief artifact (this file); tokens live in `assets/site.css`; `about/terms/archive/post` templates as the prototype reference (no throwaway prototype — reuse is verbatim/near-verbatim); semantic-token dark override; motion convention (no animation); AA contract on real pairs (§6); native semantics (`ul`/`table`/`th scope`/`time`/landmarks + skip link intact).

## 11) Remaining visual risks

- Weight table at 360px: URL slugs in row headers may force region-internal scroll — accepted (region scroll is the established article-table idiom), but DEV must prove with 360px screenshots; truncate display slugs only if needed and only with re-review (truncation changes traceability).
- Streak semantics are a product definition (`digest` = ?): if DEV's deterministic definition differs from readers' expectation, the card note (`Last digest <date>`) carries the disambiguation — no design change needed.
- Byte figures grow over time; 7-digit groupings (`1,234,567 bytes`) must not wrap the card value — `.metrics-value` allows wrap (`overflow-wrap:break-word`, inherited from grid `min-width:0`); DEV verifies at 360px.
- SEC: metadata-boundary risk logged in §7. If metrics ever become client-rendered or data-fetched, re-flag SEC + repeat this review.

**Verdict: DESIGN PASS WITH REFINEMENT.** Clearance granted for DEV implementation within the acceptance criteria above. Any scope or implementation change re-opens this review.
