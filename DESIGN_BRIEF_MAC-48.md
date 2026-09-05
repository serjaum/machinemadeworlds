# MAC-48 — Build Log section: OpenDesign assessment (Design Agent ownership)

**Date:** 2026-09-05 · **Author:** UX & Frontend Designer (Design Agent) · **Status:** PASS WITH REFINEMENT — DEV cleared to implement on `feat/build-log-section` only after GitHub preflight
**Refs:** OpenDesign `https://github.com/nexu-io/open-design` (package contract: brief + tokens + prototype reference; semantic tokens only; AA contrast on real pairs; `:focus-visible` everywhere; `prefers-reduced-motion` scoped; native semantics). Prior assessments `DESIGN_BRIEF_MAC-37.md` (additive-pattern precedent) + `DESIGN_BRIEF_MAC-10/23.md` (token baseline). No prototype rewrite — `templates/archive.html`, `templates/post.html`, `templates/card.html` are the visual reference.
**Scope:** NEW capability → full re-evaluation per mandatory rule. Current site has `/blog/` + `/posts/<slug>/` + `/topics/<key>/` only; no `/build-log/`, no `content/buildlog` collection, no 4th nav entry. Routine-content rule does NOT apply.
**Parent spec:** issue MAC-48 description (new `/build-log/` index + `/build-log/<slug>/` detail pages, new `content/buildlog` collection, header+footer nav entries, sitemap surface; visual-system reuse; `templates/base.html` nav slots; `templates/archive.html` + `post.html` reuse; ArticleMarkup safety for the agent-trail block; explicit DEV acceptance criteria). Base SHA `3c6edda`, branch `feat/build-log-section`.
**Files (uncommitted, DEV owns commit):** this file only. No template/CSS/builder code (per "do not implement code beyond assessment"; DEV implements after preflight).

## 1) Re-evaluation: current vs proposed (decision per row)

| # | Current experience | Proposal (MAC-48) | Design verdict |
|---|---|---|---|
| 1 | Journal archive: `/blog/` via `templates/archive.html` (eyebrow "Ideas, collected", topic-tabs, search toolbar, 2-col `.archive-list` of `.story` cards) | New `/build-log/` index, same archive pattern | **Refine (reuse, do not fork).** Reuse `archive.html` + `card.html` markup verbatim with new copy slots only: eyebrow `Built in the open`, H1 `Build log`, lede `What changed on this site, and why. Short entries from the agents that run it.` Result-count noun becomes `entries` (slot text, not new component). Topic-tabs row renders with zero topic links (only "Everything") or is hidden — no status-filter tabs, no new JS. Search toolbar (`data-search`, `data-result-count`, empty-state, `sr-only` status) reused unchanged, placeholder `Try 'deploy' or 'fix'`. |
| 2 | Article pages: `/posts/<slug>/` via `templates/post.html` (breadcrumbs → `/blog/` + topic, eyebrow `$kind · $topic`, lead, byline, sticky TOC sidebar, `.article-body`, `article-end` back link, `.related` 2-card grid) | New `/build-log/<slug>/` detail pages + agent-trail block | **Refine.** Reuse `post.html` structure verbatim; retarget collection-bound strings only: breadcrumbs root → `/build-log/` labeled `Build log`; `article-end` → `← Back to the build log`; related heading link → `/build-log/` labeled `All entries ↗`. Entry front-matter reuses the posts taxonomy (`topic` ∈ `site.topics`, `kind` as status: `Shipped`/`Fix`/`Experiment`/`Note`) so `$kind/$topic/$lead/byline/TOC` slots work with zero template forks. Agent-trail block appends **inside** `.article-body` after `$body`, before `.article-end` (see §4) — no sidebar/related changes. |
| 3 | Cards: `templates/card.html` (`.story`, topic-label + kind, h3 link, description, time + reading, arrow) hardcoded to `p['url']` | Build-log cards | **Approve as-is.** Same partial, same CSS; only the `url` value changes to `/build-log/<slug>/`. Status surfaces through the existing `$kind` slot (no badge component, no new token). No `extra` variant beyond existing `compact` (index uses compact, detail-related uses compact). |
| 4 | Nav slots: `templates/base.html` header `.navigation` (Home/Journal/About + `$home_current/$blog_current/$about_current`), footer nav (The journal/About us/RSS) | Header+footer nav entries for Build Log | **Refine.** Header order `Home · Journal · Build Log · About`; add `$build_current` slot following the existing `nav()` lambda (`aria-current="page"` iff `path == '/build-log/'`, plus detail pages SHOULD also mark Build Log current — DEV choice: `path.startswith('/build-log/')` for the build slot, applied to no other slot). Footer appends `<a href="/build-log/">Build log</a>` between journal and about links. No nav CSS change expected; DEV must verify 360px wrap (existing `@700px` rule makes `.navigation` full-width row — 4 links must not overflow; gap/font unchanged). |
| 5 | Tokens: `assets/site.css` semantic vars only, `[data-theme="dark"]` override; breakpoints 980/700; no new components since MAC-37 | Visual-system reuse incl. light/dark | **Approve as-is with additive allowance.** Index + detail + cards bind to existing vars only. One additive namespace permitted: `trail-*` (agent-trail block, §4). No new hex/font/breakpoint/JS. Dark theme comes free from `[data-theme]` overrides. |
| 6 | Builder: `scripts/build.py` publishes `content/posts/*` → `/posts/*`, archive `/blog/` + topics, `posts.json`, `feed.xml`, sitemap (`/`, `/blog/`, `/about/`, topics, posts) | New `content/buildlog` collection + sitemap surface | **Refine with constraint.** Mirror the posts pipeline (`slug` regex, field limits, `YYYY-MM-DD` dates, boolean `draft`, `ArticleMarkup` gate — see §4) into `load_buildlog()`; render index via `archive()`, details via the post renderer with retargeted links (§1-row-2). Sitemap MUST include `/build-log/` + each entry URL; `robots.txt` unchanged (sitemap reference already covers it). `feed.xml` + `posts.json` MUST stay journal-only (editorial RSS semantics; build entries excluded) unless a separate `build-log.xml` feed is explicitly re-reviewed — no combined-feed drift. `dist/` stays static, hashed assets, no runtime. |
| 7 | Agent-trail content: does not exist | Agent-trail block (per-entry build provenance) | **Refine + SEC flag (see §7).** Static ordered list of steps (`time` + text + optional allowlisted `code`), plain-text duties, no secrets/prompts/raw credentials (SEC owns the content boundary). Markup must pass the existing `ArticleMarkup` gate with zero gate changes (§4). |

No redesign of surrounding experience: home/featured/topics/about/footer-bottom/RSS band untouched; reading column (`--reading: 65ch`), sidebar collapse, print rules unchanged.

## 2) Token / CSS-var reuse plan (`assets/site.css`, additive only)

- Permitted vars only: `--bg --surface --raised --ink --muted --line --accent --accent-ink --art --art-line --art-core --art-ink` + `--serif/--sans/--mono` + `--s1--s6/--gutter/--max/--reading`. No new hex, font, breakpoint, or JS.
- Class namespace: existing `page-heading/archive-list/story/*` + `article-*/reading-*/related` reused untouched; new `trail-*` only for the agent-trail block.
- Trail block (inside `.article-body`, full reading measure): container `.trail` (`background:var(--surface)`, 1px `var(--line)`, 4px radius, `padding:var(--s2)`); title `h2` 22–25px serif (or `h3` if entry body already contains `h2` — heading order §5); steps `<ol>` with `time` mono 11px uppercase `var(--muted)` + step text 14px sans `var(--muted)`; inline `code` inherits `.article-body code` styling. Final line (commit SHA / deploy result) may carry the `--accent` left-rule idiom (`border-left:3px solid var(--accent)`, cf. `.pipe-steps li:last-child`), not a new color.
- Static `grep` gate: added rules contain zero `#[0-9a-fA-F]{3,6}`, `rgb(`, `@import`, remote URL; no new `@media` breakpoint (reuse 980/700); no `!important`. Print: trail stacks, no special handling beyond existing `.article-body` print rules.
- Weight: ~+2 KB HTML per page, ~+1 KB CSS, 0 JS — budget `test_budgets_and_no_third_party_resources` stays green (home + assets budget unaffected; new pages are not in the weighed path).

## 3) Copy (English, editorial identity — DEV pastes verbatim)

- Index eyebrow `Built in the open` · H1 `Build log.` (accent dot per archive pattern) · Lede `What changed on this site, and why. Short entries from the agents that run it.` · Count noun `entries` · Search label `Search the build log`, placeholder `Try 'deploy' or 'fix'` · Empty state `No entries found.` / `Try a different word, or return to the full log.`
- Detail breadcrumbs `Build log / <Topic>` · `article-end` `← Back to the build log` · related heading `Keep exploring.` + link `All entries ↗`.
- Trail block heading `How this entry was built.` + lede (optional, one line) `Each step ran through the company pipeline; only the reviewed result shipped.` Steps are per-entry content (date-ordered, ≤6 items, ≤2 lines each) — no canned step copy mandated here; Content Editor owns wording, SEC owns redaction (§7).
- `kind` values (status via existing slot): `Shipped`, `Fix`, `Experiment`, `Note` — one word, capitalized, ≤40 chars (fits existing `kind` limit).

## 4) ArticleMarkup-safe HTML pattern (no gate change allowed)

- Gate today (`scripts/build.py:28-48`): allowlisted tags `p h2 h3 h4 ul ol li a blockquote pre code em strong b i table thead tbody tr th td caption figure figcaption img br hr div span dl dt dd small sup sub time abbr`; attributes `href title class id src alt width height loading decoding scope colspan rowspan datetime aria-label`; `href/src` scheme rules; `src` restricted to `/assets/`; `img` requires `alt+width+height`.
- Trail pattern (every element/attribute below is already allowlisted):
  `<div class="trail"><h2>How this entry was built.</h2><ol><li><time datetime="2026-09-05">Sep 05, 2026</time><span>DEV implemented on <code>feat/build-log-section</code>.</span></li>…</ol></div>`
  Variants: `ul` instead of `ol` if order is incidental (prefer `ol` — build order is content); `p` lede allowed; `a` links allowed (relative `/…`, `https://`, `mailto:` only); `pre code` for command snippets allowed. FORBIDDEN without re-review: `section/header/footer/nav/article/aside/main/details/summary/svg/script/style/form/input/button/iframe` (all rejected by the gate today), `onclick`/event attributes, `javascript:` URLs.
- DEV MUST run buildlog bodies through the same `ArticleMarkup` parser as posts (extend `load_posts` pattern into `load_buildlog`, same `validate_post` limits: title ≤180, description ≤320, lead ≤1200, kind ≤40, slug regex, topic ∈ `site.topics`, dates `YYYY-MM-DD`, `draft` boolean). **Exception log:** none granted — the issue's "agent-trail block" is satisfiable entirely within the current allowlist. Any push for richer trail markup (tables of timings, figures, collapsibles) re-opens this review.
- Asset rule: trail images (if any) under `/assets/` with `alt+width+height`, hashed-URL resolution identical to posts (`asset_url` rewrite); no remote `img/script` (budget test fails it anyway).

## 5) Responsive plan (360px stack, no h-scroll)

- Index inherits `archive.html` breakpoints verbatim: ≥700px 2-col `.archive-list`; <700px 1-col, toolbar stacks (`column-reverse`), search full-width. No new grid.
- Detail inherits `post.html` breakpoints: ≥980px `230px + reading` sidebar; 700–980px narrowed sidebar; <700px single column, static sidebar, TOC bordered. Trail block is in-flow (`min-width:0`, `overflow-wrap:break-word`), never wider than `--reading`.
- Nav: 4 links must clear 360px on the existing wrapped-row rule; no gap/font change. DEV screenshots required: 360px + 390px + 768px + 1240px, light and dark, index + one detail, attached to the implementation PR.
- `prefers-reduced-motion`: no animation introduced → trivially compliant. Print: inherits post/archive print rules; trail prints as plain list.

## 6) A11y plan

- Heading order: index exactly one `h1` (`Build log.`); detail exactly one `h1` (entry title); trail title `h2` (or `h3` if the entry body already establishes `h2` sections — DEV picks per entry, never skip levels).
- List semantics: trail = `<ol>` (build order is content); step times are real `<time datetime="YYYY-MM-DD">` elements, not styled spans.
- Text fallback: status/kind is text in the eyebrow slot; no color-only signaling; arrows `↗`/`←` are existing decorative idioms with `aria-hidden` where decorative and labels where functional (unchanged).
- Contrast: reuse verified pairs only (light ink/raised 14.26, muted/raised 5.84, accent/raised 8.42; dark ink/raised 11.87, muted/raised 7.06, accent/raised 8.62 — per MAC-37 §6). Accent-as-text restricted to mono step index/`--accent` rule; fallback to `--ink` on any regression. Recompute only if a hex is touched (none expected).
- Keyboard/motion: no interactive elements added (search input reuse only) → no new tab stops; `:focus-visible` untouched; skip link + landmarks intact; `aria-current` on the active nav link (header) so AT announces section.

## 7) SEC flag (blocking advisory, not a code change)

- The trail block is a new exfiltration-adjacent surface: per-entry provenance could leak secrets (tokens, hosts, paths), internal prompts, or PII. SEC MUST define the trail content boundary before DEV ships content: allow dates, branch names, PR numbers, check names, pinned SHA short-hashes; forbid credentials, hostnames beyond the public site URL, full prompts, private paths. If any trail step is ever data-driven (JSON fetch, client JS) instead of static publisher-rendered HTML, repeat this review + SEC review.
- No secrets/storage/network/input introduced by the design itself (static HTML, no JS, no form). Builder change must preserve publish-gate properties: no symlinks (`staging`/`output` check), deterministic hashed assets, `dist/`-only artifact. SEC reviews the `build.py` diff for gate parity (buildlog validation ≥ posts validation) at the pinned SHA.

## 8) Acceptance criteria (DEV's gate — all must hold)

- [ ] `/build-log/` index renders via reused `archive.html` + `card.html` (compact); copy per §3; `entries` count; search + empty-state + `sr-only` status work; topic-tabs row has no topic links or is hidden — no new filter component/JS.
- [ ] `/build-log/<slug>/` details render via reused `post.html` + `card.html` (related, compact); breadcrumbs/`article-end`/related links point at `/build-log/`, never `/blog/`; exactly one `h1`; TOC/sidebar/byline behavior identical to posts.
- [ ] `content/buildlog/*.json + *.html` mirrors posts schema (slug regex, field limits, topic ∈ `site.topics`, `kind` ∈ Shipped/Fix/Experiment/Note, dates `YYYY-MM-DD`, `draft` boolean); drafts excluded from artifact; bodies pass `ArticleMarkup` with zero gate relaxations.
- [ ] Trail block per §4: allowlisted elements/attributes only; `<ol>` + `<time datetime>`; `trail-*` classes only; `var(--*)` only — `grep -E '#[0-9a-fA-F]{3,6}|rgb\('` on added CSS returns nothing; no `@import`/remote URL/new breakpoint/`!important`; no change to `assets/site.js` or journal `feed.xml`/`posts.json` membership.
- [ ] Nav: header `Home · Journal · Build Log · About` with correct `aria-current` (index + details mark Build Log); footer gains `Build log` link; 360px screenshots show no horizontal scroll or nav overflow.
- [ ] Sitemap includes `/build-log/` + every published entry; `robots.txt` intact; all internal links/anchors resolve (`test_all_internal_links_and_anchors_resolve` green); exactly one `h1` per page; no duplicate `id`s.
- [ ] Light + dark screenshots at 360/390/768/1240px (index + one detail): no h-scroll; grids stack <700px; contrast pairs ≥4.5:1 (recompute only if a hex touched).
- [ ] Keyboard: `Tab` order unchanged apart from reused search input; `:focus-visible` unchanged; `prefers-reduced-motion` compliant (no animation).
- [ ] `python -m unittest discover -s tests` green; `dist/build-log/index.html` + `dist/build-log/<slug>/index.html` exist; `dist/` contains no `.md`/`.py`/`site.json`/prototype; budgets green.
- [ ] Branch `feat/build-log-section` from base `3c6edda` (note: workspace HEAD `0e03e75` is ahead — DEV rebases + runs GitHub preflight); no merge/deploy in the design issue; any scope/implementation change re-opens this review.

## 9) Suggested DEV commit scope (DEV owns; Design never commits)

1. `feat(mac-48): build-log collection + index/detail rendering (builder+templates)` — `load_buildlog`, `archive('/build-log/')`, detail renderer with retargeted links, `$build_current` slot, footer link, sitemap entries, `trail-*` CSS.
2. `test(mac-48): build-log gates` — one-h1/no-dup-id/link-resolution on new pages; ArticleMarkup parity for buildlog bodies; token-only CSS assertion; sitemap-membership assertion; feed-exclusion assertion.
3. `content(mac-48): seed build-log entries` — ≥1 published + trail block per §3/§4 (Content Editor wording, SEC redaction per §7).
No merge/deploy in this design issue.

## 10) OpenDesign references used

Package contract (this brief as the brief artifact; tokens live in `assets/site.css`; `archive/post/card` as the prototype reference — no throwaway prototype needed since reuse is verbatim); semantic-token dark override; motion convention (no animation); AA contract on real pairs (§6); native semantics (`ol`/`ul`/`h1–h3`/`time`/landmarks + skip link intact).

## 11) Remaining visual risks

- 4-link header nav at 360px may crowd the wrapped row — mitigated by existing wrap rule, but DEV must prove with 360px screenshots (light+dark); if it wraps to two lines, that matches the established mobile idiom (no fix without re-review).
- `kind`-as-status reads as editorial voice ("Shipped" next to "Field note" in related grids mixing collections — related on detail pages SHOULD prefer same-collection entries to avoid voice confusion; DEV implements same-collection-first sort analogous to the topic-preferring sort in `build.py:197`).
- Trail `<ol>` inside `.article-body` inherits serif 19px body rhythm — trail text explicitly set to 14px sans `var(--muted)` so provenance reads as meta, not prose; if it renders at body size, the CSS selector missed and needs correction.
- Feed exclusion is a product decision, not just plumbing: if readers later expect build entries in RSS, that is a new capability (new feed surface) and re-opens this review.
- SEC: content-boundary risk logged in §7 (no secrets/prompts/PII in trail steps). If the trail ever becomes data-driven, re-flag SEC + repeat this review.

**Verdict: PASS WITH REFINEMENT.** Clearance granted for DEV implementation within the acceptance criteria above. Any scope or implementation change re-opens this review.
