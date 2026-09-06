# MAC-78 — Pipeline-diagram component: OpenDesign assessment (Design Agent ownership)

**Date:** 2026-09-06 · **Author:** UX & Frontend Designer (Design Agent) · **Status:** PASS WITH REFINEMENT — DEV cleared to implement on a fresh branch from `97683bb` only after GitHub preflight
**Refs:** OpenDesign `https://github.com/nexu-io/open-design` (brief + tokens + prototype-reference contract; semantic tokens only; AA contrast on real pairs; `:focus-visible` everywhere; `prefers-reduced-motion`; native semantics). Prior assessments `DESIGN_BRIEF_MAC-48.md` (trail block, ArticleMarkup gate §4) + `DESIGN_BRIEF_MAC-37.md` (additive-pattern precedent). No prototype rewrite — `templates/post.html` + `.trail` + `.pipe-steps` + `.article-body table` are the visual reference.
**Scope:** NEW capability → full re-evaluation per mandatory rule. Site has no pipeline-diagram component today; `.pipe-steps` lives only on the About page (full-width, 6-col), `.trail` is a flat ordered list, tables are generic. Routine-content rule does NOT apply.
**Parent spec:** issue MAC-78 description (pure HTML+CSS task-pipeline diagram from buildlog stages data: stage nodes with PASS/BLOCK/FAIL/done/skipped styling, return-loop edges BLOCK→fix→re-review labeled with SHAs, verdict-trail table, top link row; ArticleMarkup tags only, zero JS/assets; light/dark + mobile + keyboard; reuse post.html + agent-trail block). Base `97683bb`, fresh branch from `origin/main`.

## 1) Re-evaluation: current vs proposed (decision per row)

| # | Current experience | Proposal (MAC-78) | Design verdict |
|---|---|---|---|
| 1 | About-page `.pipe-steps`: 6-col grid of stage cards with `→`/`↓` `::before` connectors, collapse 6→3→1, print hides arrows | Stage-node diagram inside buildlog article bodies | **Refine (reuse idiom, new scope).** Reuse the `.pipe-steps` card language (raised bg, line border, 4px radius, mono uppercase step label, muted duty text) but render as a **vertical stack (1 col, `↓` connectors) at all widths** — the reading column never exceeds `--reading: 65ch`, so the 6-col About idiom would crush nodes to ~100px. New additive namespace `flow-*` scoped inside `.trail` (see §2). No new breakpoint. |
| 2 | Status surfaces only as text (`kind` eyebrow: Shipped/Fix/Experiment/Note); system has **no status colors** | Node styling for PASS/BLOCK/FAIL/done/skipped | **Refine (text-first, zero new hex).** Status is a mono uppercase text label in the existing `.pipe-step`-style slot — never color-only. BLOCK/FAIL nodes add `border-left: 3px solid var(--muted)` + `◆` text prefix; terminal PASS/done node keeps the established `--accent` left-rule idiom (`cf. .pipe-steps li:last-child`, `.trail li:last-child`). No red/green/amber tokens (would break the token-only rule + need new AA pairs for both themes). |
| 3 | Connectors are linear `→`/`↓` glyphs; **no loop primitive** exists; `svg` is **rejected** by ArticleMarkup | Return-loop edges BLOCK→fix→re-review labeled with SHAs | **Redesign the edge (linearize the loop).** Drawn loop lines are impossible: `svg`/`style` tags are gate-rejected, zero-JS forbids canvas, `::before` can only emit linear glyphs. Render the loop as an explicit full-width re-entry row: `↩ BLOCK → fix (<code>abc1234</code>) → re-review (<code>def5678</code>)` inside a `surface`-bg list item. Same information, zero gate risk, mobile/print safe. Short 7-char SHAs in `<code>` only (full 40-char hashes overflow the column). |
| 4 | `.article-body table` (block scroll wrapper, builder injects `tabindex="0"` + `aria-label`) | Verdict-trail table (stage, agent, verdict, SHA, why) | **Approve as-is (reuse, no new table CSS).** 5 columns will overflow 65ch on mobile → the existing `overflow-x: auto` + keyboard-focusable scroll region is the correct, already-reviewed idiom. Require `<th scope="col">` (allowlisted), `why` ≤ 1 short line, SHA in `<code>`. |
| 5 | Links use inherited article-link style | Top link row (PR, merge-commit, branch) | **Approve as-is.** Plain `<p>` with three `<a>` links; relative `/…` or `https://` pass the scheme gate. SEC note §7: branch/commit links MUST point at the public repo only; never render internal hosts/paths. |
| 6 | `.trail` container (surface bg, line border, 4px radius, `padding:var(--s2)`, in-flow, `overflow-wrap:break-word`) | New component wrapper | **Refine (nest, don't fork).** The whole pipeline block nests **inside** the existing `.trail` div (after the steps `<ol>` or as its own `<h3>` section): `<div class="trail"><h3>…</h3><p>link row</p><ol class="flow">…</ol><table>…</table></div>`. No new container token, no template fork, TOC/heading-order rules from MAC-48 §5/§6 carry over (`h3` since entry bodies establish `h2`). |

No redesign of surrounding experience: post.html, breadcrumbs, TOC sidebar, related grid, archive index, nav, feed exclusion, sitemap behavior unchanged.

## 2) Token / class reuse plan (`assets/site.css`, additive only)

- Permitted vars only: `--bg --surface --raised --ink --muted --line --accent --accent-ink` + `--sans/--serif/--mono` + `--s1--s3`. No new hex, font, breakpoint, JS, `!important`, `@import`, remote URL.
- New namespace (additive, scoped under `.trail` so About-page `.pipe-steps` is untouched):
  - `.trail .flow { list-style:none; margin:var(--s1) 0 0; padding:0; display:grid; grid-template-columns:1fr; gap:var(--s2); }`
  - `.trail .flow > li { background:var(--raised); border:1px solid var(--line); border-radius:4px; padding:var(--s2); min-width:0; overflow-wrap:break-word; }`
  - `.trail .flow > li + li::before { content:"↓"; display:block; text-align:center; color:var(--muted); margin:calc(var(--s2) * -1) 0 0; }` (linear glyph idiom mirrors `.pipe-steps` mobile rule; `position:static` — no absolute offsets to break at 360px)
  - `.trail .flow-status { display:block; font:11px/1.6 var(--mono); letter-spacing:.1em; text-transform:uppercase; color:var(--accent); margin-bottom:var(--s1); }` (mirrors `.pipe-step`; BLOCK/FAIL override: `color:var(--muted)` + `◆` prefix in content, `border-left:3px solid var(--muted)` on the `li`)
  - `.trail .flow > li:last-child { border-left:3px solid var(--accent); }` (terminal-step idiom, verbatim reuse)
  - `.trail .flow-loop { background:var(--surface); }` + loop text `font:13px/1.7 var(--sans); color:var(--muted)` with `code` inheriting `.article-body code`
  - Print: `.trail .flow > li + li::before { content:none; }` (mirrors pipe-steps print rule).
- Static `grep` gate: added CSS contains zero `#[0-9a-fA-F]{3,6}`, `rgb(`, `@import`, `http`, new `@media` width, `!important`.
- Weight: ~+1 KB CSS, ~+2–3 KB HTML per entry. Budget tests unaffected (new pages not in the weighed home+assets path).

## 3) Copy (English, editorial identity — DEV/Content pastes verbatim)

- Section heading (inside `.trail`, `h3`): `Pipeline.` Lede (optional one line): `Each stage ran in order; blocked stages looped back through fix and re-review.`
- Link row: `PR <a>#NN</a> · merge <a><code>abcdef1</code></a> · branch <a><code>feat/…</code></a>` (one `<p>`, 13–14px sans muted).
- Node content: `<span class="flow-status">PASS — stage name</span>` + one duty line (`done`/`skipped` likewise; `BLOCK`/`FAIL` prefixed `◆`). Status words verbatim: `PASS`, `BLOCK`, `FAIL`, `done`, `skipped`.
- Loop row: `↩ <span>BLOCK → fix (<code>abc1234</code>) → re-review (<code>def5678</code>)</span>` — arrow glyphs are text (screen readers get the words BLOCK/fix/re-review; mark glyphs `aria-hidden="true"` via… note: `aria-hidden` is NOT in the ArticleMarkup attribute allowlist — so keep glyphs unmarked; they are decorative but harmless, and the words carry meaning. Do NOT add `aria-hidden`; the gate rejects it).
- Table: caption or preceding `h3` `Verdict trail.`; headers exactly `Stage | Agent | Verdict | SHA | Why`.

## 4) ArticleMarkup-safe HTML pattern (no gate change allowed)

- Gate today (`scripts/build.py:28-48`): tags `p h2 h3 h4 ul ol li a blockquote pre code em strong b i table thead tbody tr th td caption figure figcaption img br hr div span dl dt dd small sup sub time abbr`; attrs `href title class id src alt width height loading decoding scope colspan rowspan datetime aria-label`.
- Pipeline pattern (every element/attribute below already allowlisted):
  `<div class="trail"><h3>Pipeline.</h3><p><a href="https://github.com/serjaum/machinemadeworlds/pull/10">#10</a> · …</p><ol class="flow"><li><span class="flow-status">PASS — plan</span><span>DEV …</span></li><li class="flow-loop"><span>↩ BLOCK → fix (<code>abc1234</code>) → re-review (<code>def5678</code>)</span></li>…</ol><table><thead><tr><th scope="col">Stage</th>…</tr></thead><tbody><tr><td>…</td>…</tr></tbody></table></div>`
- FORBIDDEN without re-review: `svg section article aside details summary style script iframe` (gate-rejected today), `aria-hidden`/`style`/`onclick` attributes (not allowlisted), full 40-char SHAs in flow text (overflow), `javascript:`/`//` URLs.
- **Exception log:** none granted — the proposal is satisfiable within the current allowlist after the §1-row-3 loop linearization.

## 5) Responsive plan (360px stack, no h-scroll)

- Flow list is 1-col at every width by construction — no breakpoint, nothing to collapse, nothing to overflow. `min-width:0` + `overflow-wrap:break-word` on items; SHAs short + in `<code>` (wraps with the line).
- Table reuses the builder's scroll-region idiom (`display:block; overflow-x:auto`, `tabindex="0"` injected) — keyboard-scrollable on mobile, no page-level h-scroll.
- Link row wraps as normal inline text. Print: arrows hidden, flow prints as stacked cards, table prints full-width (existing print rules cover both).
- DEV screenshots required: 360px + 768px + 1240px, light and dark, one entry with the pipeline block.

## 6) A11y plan

- Heading order: entry `h1` → body `h2`s → trail `h3` (MAC-48 §5 rule carries over; pipeline adds no new heading level — link row is a `p`, flow is a list, table uses `th scope`).
- List semantics: flow = `<ol>` (stage order is content); loop row is a list item (it IS a step in the sequence), not a separate div.
- Status is text, never color-only (BLOCK/FAIL also carry the `◆` text prefix + words). Contrast: all text uses verified pairs only (muted/raised 5.84 light / 7.06 dark; accent text restricted to the 11px mono status label per MAC-48 §6 precedent).
- Keyboard: zero new interactives beyond native links + builder-focusable table region; `:focus-visible`, skip link, landmarks untouched.
- Reduced motion: no animation → trivially compliant.

## 7) SEC flag (advisory, no code change)

- Same surface class as MAC-48 §7: SHAs, branch names, PR numbers are allowlisted content; forbid credentials, non-public hosts, full prompts, private paths. Branch link target MUST be the public GitHub repo.
- No secrets/storage/network/input introduced (static HTML, no JS/form). Builder change must preserve publish-gate properties; SEC reviews the `build.py`/content diff for ArticleMarkup parity at the merge SHA.

## 8) Acceptance criteria (DEV's gate — all must hold)

- [ ] Pipeline block nests inside `.trail` (`h3` heading, never `h1`/`h2`); `flow-*` classes only; `var(--*)` only — `grep -E '#[0-9a-fA-F]{3,6}|rgb\('` on added CSS returns nothing; no new `@media` width / `@import` / remote URL / `!important`; `assets/site.js` untouched.
- [ ] Status is text-first: every node carries a `.flow-status` text label with one of PASS/BLOCK/FAIL/done/skipped; BLOCK/FAIL also carry `◆` prefix + `border-left:3px solid var(--muted)`; terminal node carries the `--accent` left rule.
- [ ] Loop rendered as full-width `.flow-loop` re-entry row with `↩` + short 7-char `<code>` SHAs; no `svg`/`style`/`details` elements; bodies pass `ArticleMarkup` with zero gate relaxations.
- [ ] Verdict table uses `<th scope="col">`, headers exactly Stage/Agent/Verdict/SHA/Why, `why` ≤1 line, SHA in `<code>`; mobile scrolls inside the table region with no page-level h-scroll.
- [ ] Link row: 3 links max (PR, merge commit, branch), public-repo targets only, wraps without overflow.
- [ ] Light + dark screenshots at 360/768/1240px: no h-scroll; contrast pairs ≥4.5:1 (recompute only if a hex touched — none expected).
- [ ] Keyboard: `Tab` order = native links + table region only; `:focus-visible` unchanged; `prefers-reduced-motion` compliant.
- [ ] `python -m unittest discover -s tests` green; internal-link/one-h1/no-dup-id gates green on entries carrying the block; budgets green.
- [ ] Fresh branch from `origin/main` at/after `97683bb` + GitHub preflight; no merge/deploy in the design issue; any scope/implementation change re-opens this review.

## 9) Suggested DEV commit scope (DEV owns; Design never commits)

1. `feat(mac-78): pipeline-diagram styles (flow-* additive CSS)` — scoped flow classes + print rule, token-only.
2. `content(mac-78): build-log v2 entry with pipeline block` — link row + flow list + verdict table per §3/§4 (Content Editor wording, SEC redaction per §7); builder change only if stages become data-driven (static HTML preferred — if DEV code-gens the block from stages JSON, that generator diff needs SEC + Design re-review).
3. `test(mac-78): pipeline gates` — ArticleMarkup parity on the block, token-only CSS assertion, table-scope/header assertion, short-SHA assertion, link-target assertion.

## 10) OpenDesign references used

Brief-as-artifact contract (this file); semantic-token dark override (`:root` / `[data-theme="dark"]` pairs); prototype reference = live `post.html` + `.trail` + `.pipe-steps` + `.article-body table` (no throwaway prototype — reuse is near-verbatim); AA contract on real pairs (§6); native semantics (`ol`/`h3`/`th scope`/`time`/`code`); motion convention (no animation).

## 11) Remaining visual risks

- Vertical-stack choice trades the "diagram" look for robustness: at 65ch a horizontal node graph is unreadable, so the design deliberately reads as a sequenced ledger, not a flowchart. If MAC-72 wants a true branching graph, that is a new proposal (needs SVG-or-canvas exception → full re-review + gate change + SEC).
- 5-col verdict tables with long `why` text will scroll on mobile — accepted via the existing scroll-region idiom, but Content must keep `why` to one line or the table dominates the entry.
- `◆`/`↩`/`↓` glyph coverage: system sans/serif fonts render these on all target platforms; if QA spots tofu on any device font, fall back to ASCII (`*`, `<`, `v`) without re-review (content-only change).
- `aria-hidden` on decorative glyphs is desirable but gate-forbidden — accepted as-is since adjacent words carry meaning; if the gate ever allowlists `aria-hidden`, adopt it then.

**Verdict: PASS WITH REFINEMENT.** Clearance granted for DEV implementation within the acceptance criteria above. Key adjustments vs the proposal: (1) vertical 1-col stack, not a horizontal graph; (2) return loops linearized as full-width `↩` re-entry rows — no drawn loop lines; (3) status as text labels + border idioms, zero new color tokens. Any scope or implementation change re-opens this review.
