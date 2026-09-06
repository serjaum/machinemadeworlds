# MAC-73 — pipeline-diagram component: OpenDesign assessment (Design Agent ownership)

**Date:** 2026-09-06 · **Author:** UX & Frontend Designer (Design Agent) · **Status:** PASS WITH REFINEMENT — DEV cleared to implement after GitHub preflight
**Refs:** OpenDesign `https://github.com/nexu-io/open-design` (package contract: brief + tokens + prototype reference; semantic tokens only; AA contrast on real pairs; `:focus-visible` everywhere; `prefers-reduced-motion` scoped; native semantics). Prior assessments `DESIGN_BRIEF_MAC-48.md` (build-log section, trail block) + `DESIGN_BRIEF_MAC-37.md` (additive-pattern precedent). No prototype rewrite — `templates/post.html`, the `.trail` block (`assets/site.css:269-277`) and the `.pipe-steps` idiom (`assets/site.css:247-268`) are the visual reference; the copy-paste pattern in §4 IS the prototype.
**Scope:** NEW capability → full re-evaluation per mandatory rule. Current build-log entries (`content/buildlog/*.html`) have Motivation / Changes / Implementation / Evidence sections + a `.trail` ordered list; there is NO pipeline diagram, NO verdict-trail table, NO top link row. Routine-content rule does NOT apply.
**Parent:** MAC-72 (Build Log v2 backstage edition). This issue (MAC-73) is the FIRST stage, no dependencies. DEV is blocked on this clearance.

## 1) Re-evaluation: current vs proposed (decision per row)

| # | Current experience | Proposal (MAC-73) | Design verdict |
|---|---|---|---|
| 1 | Entry body: prose sections (`h2` + `p` + `code`), trail `.trail > h3 + ol > li > time + span` | NEW `pipeline-diagram` block: stage nodes + return-loop edges labeled with SHAs | **Refine (reuse, do not fork).** Build it as a `.trail`-sibling inside `.article-body`, reusing the `.pipe-steps` box-and-arrow idiom (bordered `li` boxes, `→`/`↓` via `::before`, accent left-rule on the terminal node). No SVG — the `ArticleMarkup` gate (`scripts/build.py:28-48`) REJECTS `svg` (verified live this heartbeat), so edges are CSS pseudo-element arrows, never vector markup. |
| 2 | Provenance lives in trail `<ol>` prose + JSON (`mac_id`, `pr`, `commit`, `agents`) | NEW top link row: PR, merge commit, branch | **Refine.** One wrapping `<p>` row of native links/text inside the diagram block. PR is an `<a href="https://github.com/…/pull/N">`; merge commit + branch are `<code>` text (commit MAY link to `https://github.com/…/commit/<sha>`). No new link style — inherits `.article-body a` + `code`. |
| 3 | Verdicts implied by trail prose ("SEC and QA passed…") | NEW verdict-trail table: stage, agent, verdict, SHA, why | **Approve with constraints.** A real `<table>` with `<caption>` + `th scope` (§4). Mobile overflow + keyboard scroll come free: builder wraps tables as `<table tabindex="0" aria-label="Article data">` (`build.py:257`) and `.article-body table` already scrolls (`site.css:178`). |
| 4 | Status via `kind` eyebrow slot (`Shipped`/`Fix`/`Experiment`/`Note`) | Stage nodes with status styling | **Refine.** Status is TEXT first (`PASS`/`FAIL`/`RETRY` label in each node), border idiom second (accent left-rule = terminal/landed, `var(--line)` = transit). Never color-only. No new status colors or tokens. |
| 5 | `.trail` block closes each entry | Diagram + trail co-existence | **Refine.** Order inside `.article-body`: prose sections → `pipeline-diagram` → `.trail` → `.article-end`. Diagram carries the machine trace (stages, SHAs, verdicts); trail keeps the human-readable build story. Never merge them into one block. |

No redesign of surrounding experience: `post.html` structure, breadcrumbs, TOC sidebar, related grid, nav, feed/sitemap membership rules all unchanged.

## 2) Token / CSS-var reuse plan (`assets/site.css`, additive only)

- Permitted vars only: `--bg --surface --raised --ink --muted --line --accent --accent-ink` + `--serif/--sans/--mono` + `--s1--s3/--reading`. No new hex, font, breakpoint, motion, or JS.
- New namespace: `pipeline-*` only (`.pipeline`, `.pipeline-links`, `.pipeline-stages`, `.pipeline-loop`). The verdict table uses NO new classes — it inherits `.article-body table/th/td/code` verbatim.
- Suggested rules (DEV writes them, Design does not commit):
  - `.pipeline { background: var(--surface); border: 1px solid var(--line); border-radius: 4px; padding: var(--s2); margin: var(--s3) 0; min-width: 0; overflow-wrap: break-word; }`
  - `.pipeline h3 { font-size: clamp(22px, 2vw, 25px); margin-bottom: var(--s1); }` (matches `.trail h3`)
  - `.pipeline-links { font: 14px/1.7 var(--sans); color: var(--muted); }` wraps (`flex-wrap: wrap`), links keep 44px-equivalent tap affordance via line-height + padding, never shrunk below 13px.
  - `.pipeline-stages { list-style: none; margin: var(--s1) 0 0; padding: 0; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--s2); }` nodes reuse `.pipe-steps li` treatment (raised bg, line border, mono uppercase index + serif name + sans status line). `li + li::before` arrow idiom copied from `.pipe-steps` (`→` desktop, `↓` under 700px).
  - `.pipeline-loop { font: 13px/1.7 var(--mono); color: var(--muted); }` return edges: `↩` marker + short SHA in `<code>`; visually de-emphasized vs forward stages (muted text, no accent rule).
- Static `grep` gate: added CSS contains zero `#[0-9a-fA-F]{3,6}`, `rgb(`, `@import`, remote URL, new `@media` breakpoint (reuse 980/700 only), `!important`, or animation. `prefers-reduced-motion`: nothing animates → trivially compliant.
- Weight: ~+1 KB CSS, ~+1–2 KB HTML per entry page. Home + assets budget (`test_budgets_and_no_third_party_resources`) is unaffected — entry pages are not in the weighed path — but keep the block lean regardless.

## 3) Copy (English, editorial identity — DEV pastes verbatim)

- Diagram title (h3, never h2 — entry bodies already establish h2 sections): `Pipeline.`
- Link row labels: `PR <a>#N</a> · merge <code>shortsha</code> · branch <code>feat/…</code>` — labels are literal text, values are per-entry content.
- Verdict table caption: `Verdict trail.` Column headers (verbatim, in order): `Stage | Agent | Verdict | SHA | Why`.
- Verdict vocabulary (text, uppercase, ≤10 chars): `PASS`, `FAIL`, `RETRY`, `SKIP`. SHA cells: 7-char short hash in `<code>` (full 40-char hashes live in prose/`commit` JSON, never in the diagram — mobile width).
- `Why` cells: ≤12 words of plain reviewer rationale, no secrets/prompts/paths (SEC boundary, §7).

## 4) ArticleMarkup-safe HTML pattern (no gate change allowed — verified live 2026-09-06)

Gate today (`scripts/build.py:28-48`): tags `p h2 h3 h4 ul ol li a blockquote pre code em strong b i table thead tbody tr th td caption figure figcaption img br hr div span dl dt dd small sup sub time abbr`; attrs `href title class id src alt width height loading decoding scope colspan rowspan datetime aria-label`; `href/src` scheme rules; `svg`/`section`/`script`/`style` all REJECTED.

**Correction to the issue text:** "div/span/table/h3 only" is too narrow to satisfy the proposal's own requirements (top link row needs `<a>`; SHAs need `<code>`; steps need `<time>`). The cleared set is the gate's allowlist RESTRICTED to: `div span table thead tbody tr th td caption h3 p a code time ol ul li em strong br` with attrs `href title class id scope datetime aria-label`. Every element below is in that set — sample passed the live `ArticleMarkup` gate this heartbeat; `<svg>` confirmed rejected.

```html
<div class="pipeline"><h3>Pipeline.</h3><p class="pipeline-links"><a href="https://github.com/serjaum/machinemadeworlds/pull/9">PR #9</a><span> · merge <code>6806770</code></span><span> · branch <code>feat/daily-news-2026-09-06</code></span></p><ol class="pipeline-stages"><li><span>Proposal</span><strong>MAC-62</strong><span>PASS · <code>64e73dd</code></span></li><li><span>Review</span><strong>SEC + QA</strong><span>PASS · <code>64e73dd</code></span></li><li><span>Ship</span><strong>Merge</strong><span>PASS · <code>6806770</code></span></li></ol><p class="pipeline-loop"><span>↩ retry at <code>64e73dd</code> after QA flag</span></p><table><caption>Verdict trail.</caption><thead><tr><th scope="col">Stage</th><th scope="col">Agent</th><th scope="col">Verdict</th><th scope="col">SHA</th><th scope="col">Why</th></tr></thead><tbody><tr><th scope="row">Review</th><td>SEC</td><td>PASS</td><td><code>64e73dd</code></td><td>No secrets in scope.</td></tr><tr><th scope="row">Review</th><td>QA</td><td>PASS</td><td><code>64e73dd</code></td><td>Checks green at pin.</td></tr></tbody></table></div>
```

FORBIDDEN without re-review: `svg` (rejected by gate — use CSS arrows), `section/header/footer/nav/article/aside/main/details/summary/figure/img/script/style/form/input/button/iframe`, event attributes, `javascript:` URLs, remote `src`. Stage-name markup: `span`/`strong`/`code` only — no heading-per-node (heading order §6). Row `<th scope="row">` for stage names is REQUIRED (AT row association). `Why` cells are plain text — no nested lists/links.

## 5) Responsive plan (360px stack, no h-scroll)

- Stages grid: `repeat(3, …)` ≥700px; 1 column <700px with `↓` connectors (same collapse idiom as `.pipe-steps`, `site.css:259-264`). Reuse the 980/700 breakpoints — no new breakpoint.
- Link row wraps (`flex-wrap`); branch `<code>` gets `overflow-wrap: break-word` — long `feat/…` names must not force h-scroll at 360px.
- Verdict table: inherits `.article-body table { display:block; overflow-x:auto }` — 5 columns scroll inside the region on narrow screens instead of breaking layout. Keep `Why` cells short so 360px shows Stage+Agent+Verdict before scrolling.
- Diagram block is in-flow (`min-width: 0`, never wider than `--reading: 65ch`).
- DEV screenshots required: 360px + 768px + 1240px, light and dark, one entry with the diagram.

## 6) A11y plan

- Heading order: entry keeps exactly one `h1`; diagram title is `h3` (entry bodies use `h2` sections; `.trail` already uses `h3` for the same reason). Never skip levels, never one-heading-per-node.
- Table semantics: `<caption>Verdict trail.</caption>`, column `<th scope="col">`, row `<th scope="row">` — screen readers announce verdicts per stage. Builder's `tabindex="0" + aria-label="Article data"` makes the overflow region keyboard-scrollable; keep the default label.
- Status is never color-only: every node carries a text verdict (`PASS`/`FAIL`/`RETRY`/`SKIP`); the accent left-rule is decoration on top of text.
- Contrast: reuse verified pairs only (light ink/raised 14.26, muted/raised 5.84; dark ink/raised 11.87, muted/raised 7.06 — per MAC-37). Muted-on-surface 14px sans passes AA; mono 11–13px SHA labels inherit the same pairs. Recompute only if a hex is touched (none permitted).
- Keyboard: links are native `<a>` (focusable, `:focus-visible` intact); zero new tab stops, zero JS, zero motion. SHA `<code>` is static text, not a control.
- Print: inherits `.article-body` print rules; arrows are text glyphs (`→`/`↓`/`↩`) so they print.

## 7) SEC flag (blocking advisory, not a code change)

- The diagram is a new provenance surface next to `.trail`: SHAs, branch names, PR numbers, agent names. Allow: short SHAs (7 chars in-diagram), PR numbers linking to the public repo, branch names, agent names, check names. Forbid: credentials, tokens, hostnames beyond the public site/GitHub URLs, full prompts, private paths, full 40-char hashes in-diagram (they widen the table and aid nothing human-readable).
- No secrets/storage/network/input introduced by the design itself (static HTML, no JS, no form). Builder change must preserve publish-gate properties: buildlog bodies through the SAME `ArticleMarkup` parser with zero relaxations; `dist/`-only artifact; no symlinks. SEC reviews the `build.py` diff for gate parity at the pinned SHA.

## 8) Acceptance criteria (DEV's gate — all must hold)

- [ ] Diagram renders inside `.article-body` AFTER prose sections and BEFORE `.trail`, before `.article-end`; `post.html` untouched (body-carried markup only).
- [ ] Markup uses ONLY §4's restricted tag/attribute set; `python -m unittest discover -s tests` green with zero `ArticleMarkup` changes; `grep -ri '<svg\|<section\|<script\|<style\|onclick' content/buildlog/` returns nothing new.
- [ ] Top link row: PR `<a>` resolves (internal `/build-log/…` or `https://github.com/serjaum/machinemadeworlds/pull/N`); merge SHA + branch in `<code>`; row wraps at 360px with no h-scroll.
- [ ] Stage nodes: text status (`PASS`/`FAIL`/`RETRY`/`SKIP`) + SHA `<code>` per node; return-loop edge(s) as `.pipeline-loop` rows with `↩` + SHA; terminal node carries the accent left-rule idiom, transit nodes `var(--line)`.
- [ ] Verdict table: caption + 5 headers verbatim (`Stage|Agent|Verdict|SHA|Why`); `th scope` on columns AND rows; short SHAs only; `Why` ≤12 words, no secrets.
- [ ] CSS: `pipeline-*` classes only; `var(--*)` only — `grep -E '#[0-9a-fA-F]{3,6}|rgb\('` on added CSS returns nothing; no `@import`/remote URL/new breakpoint/`!important`/JS; `assets/site.js` untouched.
- [ ] Exactly one `h1` per page; diagram title `h3`; no duplicate `id`s (`test_all_internal_links_and_anchors_resolve` green).
- [ ] Light + dark screenshots at 360/768/1240px, one diagram entry: no h-scroll; stages stack <700px; table scrolls in-region; contrast pairs ≥4.5:1.
- [ ] Keyboard: `Tab` reaches PR link(s) with visible `:focus-visible`; table region scrolls with arrow keys when focused; `prefers-reduced-motion` compliant (no animation exists).
- [ ] `dist/build-log/<slug>/index.html` contains the block; `feed.xml`/`posts.json` membership unchanged (journal-only); sitemap unchanged in shape.
- [ ] Any scope or implementation change (SVG/canvas/JS interactivity, new feed surface, data-driven trail) re-opens this review + SEC review.

## 9) Suggested DEV commit scope (DEV owns; Design never commits)

1. `feat(mac-72): pipeline-diagram styles (additive pipeline-* CSS, tokens only)` — CSS + nothing else.
2. `test(mac-72): pipeline-diagram gates` — ArticleMarkup parity assertion on diagram markup; one-h1/no-dup-id/link-resolution on diagram entries; token-only CSS assertion; table-caption/scope assertion.
3. `content(mac-72): pipeline-diagram blocks on v2 entries` — per-entry `div.pipeline` per §3/§4 (Content Editor wording, SEC redaction per §7).
No merge/deploy in the design stage.

## 10) OpenDesign references used

Package contract (this brief as the brief artifact; tokens live in `assets/site.css`; `post.html` + `.trail` + `.pipe-steps` as the prototype reference — no throwaway prototype, reuse is verbatim plus the §4 pattern); semantic-token dark override; motion convention (no animation); AA contract on real pairs (§6); native semantics (`ol`/`table`/`h3`/`time`/`code`/landmarks + skip link intact). Upstream repo fetched 2026-09-06 for methodology confirmation (rich app-builder surface; applicable contract extracted as above).

## 11) Remaining visual risks

- 5-column verdict table at 360px ALWAYS scrolls in-region — accepted (matches existing `.article-body table` behavior), but `Why` verbosity is the lever: enforce ≤12 words or the table becomes a swipe-tunnel.
- `↩`/`→`/`↓` glyph coverage: system-font safe on target browsers, but DEV must confirm in 360px screenshots (a missing glyph reads as tofu and kills the edge metaphor). Fallback wording ("retry at …") already carries the meaning in text, so the glyph is decoration.
- Stage grid at 3 columns on 700–980px tablet: node names + SHAs may wrap to 3 lines — acceptable (meta voice, 13–14px), but DEV proves with a 768px screenshot.
- Related-grid voice: unchanged from MAC-48's note — detail related stays same-collection-first so `PASS`/`FAIL` verdict voice never leaks into journal cards.
- SEC content-boundary risk logged in §7. If the diagram ever becomes data-driven (JSON fetch, client JS), re-flag SEC + repeat this review.

**Verdict: PASS WITH REFINEMENT.** Clearance granted for DEV implementation within the acceptance criteria above. Any scope or implementation change re-opens this review.
