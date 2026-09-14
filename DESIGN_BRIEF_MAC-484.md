# MAC-484 — Newsletter follow path: OpenDesign placement sign-off (Design Agent ownership)

**Date:** 2026-09-14 · **Author:** UX & Frontend Designer (Design Agent) · **Status:** PASS — DEV cleared to implement after GitHub preflight
**Refs:** OpenDesign `https://github.com/nexu-io/open-design` (reuse-the-system contract: no new tokens, no new components, additive placement only; semantic HTML; `:focus-visible`; `prefers-reduced-motion`; AA on existing token pairs). Inspected `templates/home.html`, `templates/post.html`, `templates/base.html`, `assets/site.css`, `templates/about.html` (page-layout precedent).
**Scope:** NEW capability (no `/newsletter/` route, strip, or follow block exists — `grep newsletter` = zero hits) → full re-evaluation per mandatory rule, LIGHT depth: placement sign-off, not a new system. Routine-content rule does NOT apply.

## 1) Evaluation: current vs proposed (decision per row)

| # | Current experience | Proposal (parent MAC-482) | Design verdict |
|---|---|---|---|
| 1 | Homepage ends: `topic-section[data-od-id="topics"]` → single `rss-band[data-od-id="follow"]` ("An open invitation / Good reading. On your terms." + `.button[href="/feed.xml"]`) → footer. No mention of newsletter anywhere. | (a) Homepage subscribe strip BELOW the featured/digest section, before footer, linking to `/newsletter/`. | **Approve with refinement.** Insert as a SECOND `rss-band` block with `data-od-id="newsletter-strip"`, placed immediately AFTER `section.topic-section` and BEFORE the existing `section.rss-band[data-od-id="follow"]` (`templates/home.html` lines 57–61). Reuses `.rss-band` + `.button` verbatim — zero new CSS. Existing RSS band stays untouched (RSS-first positioning is current editorial policy; newsletter is additive, not a replacement). Distinct eyebrow copy ("The newsletter" vs "An open invitation") so two adjacent bands do not read as duplicates. |
| 2 | Post template: `.article-body` → `$body` → `.article-end` (back-link row) → `section.related`. Sidebar has a small `.text-link[href="/feed.xml"]` ("Follow the journal ↗"). No end-of-article follow CTA. | (b) End-of-article follow block on post template (reused component) linking to `/newsletter/`. | **Approve with refinement.** Insert `<aside class="callout follow-block" data-od-id="follow-block">` INSIDE `.article-body`, immediately AFTER `$body` and BEFORE `.article-end` (`templates/post.html` lines 31–32). Reuses existing `.article-body .callout` (`site.css:185`) + `.text-link`/`button` — zero new CSS. Sidebar link (line 28) unchanged. Heading + one sentence + single `.button[href="/newsletter/"]`; keeps the back-link row as the terminal element so reading flow (finish → follow → back → related) is preserved. |
| 3 | No `/newsletter/` route or template. Closest precedent: `templates/about.html` (`.container` + `.page-heading` + `.about-layout`/`.article-body`) and footer feed links (`/feed.xml`, `/feed.json`). | (c) `/newsletter/` landing layout (cadence: daily digest + link radar + term-a-day glossary; follow buttons hrefs `/feed.xml` and `/feed.json`) reusing existing styles. | **Approve as-is (with exact construction).** New `templates/newsletter.html`: `.container` > `header.page-heading` (eyebrow "The newsletter", H1, one-line standfirst) + `.about-layout`-equivalent grid (aside motto + `.article-body` with three H2 cadence sections: Daily digest / Link radar / Term-a-day glossary) + a closing `.callout` with TWO `.button` follow links (`href="/feed.xml"`, `href="/feed.json"`). No new tokens, classes, breakpoints, JS, or third-party code. Server-rendered static HTML via `build.py`; nav `aria-current` handling follows existing page pattern (no new nav item — footer already links both feeds). |
| 4 | Footer (`base.html` lines 82–98): journal/build-log/metrics/prices/benchmarks/about/terms/privacy + RSS + JSON feed links. | No footer change proposed. | **Approve as-is: no footer change.** Footer already exposes both feeds; adding a third follow link would crowd the nav row. `/newsletter/` is reached via the two new in-flow CTAs. |

No redesign of surrounding experience: masthead, nav, theme toggle, search, footer, feed files, sitemap, JSON-LD, OG tags unchanged.

## 2) Token / class reuse plan (`assets/site.css`, additive only)

- Permitted: existing semantic vars only; no new hex, no new `@media` width, no new `@import`/font/trackers. Expected CSS delta: **zero bytes** (all three placements reuse `.rss-band`, `.button`, `.text-link`, `.callout`, `.page-heading`, `.article-body`, `.eyebrow`).
- Allowed additive markup only: `data-od-id="newsletter-strip"` / `data-od-id="follow-block"` hooks + one `newsletter-strip`/`follow-block` selector IF a spacing tweak is needed (prefer none; adjacent `.rss-band` blocks already carry `margin-bottom` rhythm).
- Copy language: English editorial identity; "follow" verbs consistent with existing "Follow via RSS" / "Follow the journal" microcopy; no inbox/email claims (feeds only).

## 3) Exact placement selectors (DEV pastes)

1. `templates/home.html`: after `section.topic-section[data-od-id="topics"]` closing tag, before `section.rss-band[data-od-id="follow"]` — insert `<section class="rss-band newsletter-strip" data-od-id="newsletter-strip">` (div: eyebrow "The newsletter" + H2 + one-line copy; `<a class="button" href="/newsletter/">`).
2. `templates/post.html`: inside `div.article-body[data-od-id="article-body"]`, after `$body`, before `div.article-end` — insert `<aside class="callout follow-block" data-od-id="follow-block">` (H2 or strong lead + one sentence + `<a class="button" href="/newsletter/">`).
3. New `templates/newsletter.html` + `build.py` static route `/newsletter/` (server-rendered, static links only): page-heading + three H2 cadence sections + closing `.callout` with `<a class="button" href="/feed.xml">` and secondary link/button `href="/feed.json"`.
4. Footer, sidebar, `.article-end`, `section.related`: untouched.

## 4) Responsive / a11y plan

- Inherits existing breakpoints (980px/700px): `.rss-band` already stacks (`flex-direction:column`, `margin-bottom:44px` mobile, `site.css:222`); `.callout` is fluid inside `--reading:65ch`; newsletter page follows `about.html` collapse (single column mobile).
- Semantics: `section` with implicit heading for strip; `aside` with heading for follow block; single H1 on `/newsletter/`; heading order H1→H2 preserved in all three insertions.
- Targets: `.button` (48px) / `.text-link` (44px) already meet touch size; `:focus-visible` unchanged; contrast unchanged (existing token pairs); `prefers-reduced-motion`: nothing animates; print: follow block prints with article (acceptable — it is content, not chrome).
- Page weight: est. +0.6KB home, +0.5KB post, one new static page reusing cached CSS — no budget risk.

## 5) SEC / QA notes

- SEC: static `href` only (`/newsletter/`, `/feed.xml`, `/feed.json`); no form, no POST, no query handling, no third-party scripts/trackers/vendor code (explicit parent constraint — preserved).
- QA: verify strip renders above existing RSS band on `/` (360/768/1240px, light+dark); follow block present on posts before `.article-end`; `/newsletter/` 200s with both feed buttons; internal-link crawl gains `/newsletter/` with zero new 404s; HTML stays valid (one H1, labelled sections).

## 6) Acceptance criteria (DEV gate)

- [ ] Home strip links to `/newsletter/` via `.button`; existing RSS band + footer byte-identical.
- [ ] Post follow block sits between `$body` and `.article-end` on every post; sidebar/related unchanged.
- [ ] `/newsletter/` serves static HTML describing daily digest + link radar + term-a-day glossary with working `/feed.xml` + `/feed.json` buttons.
- [ ] Zero new CSS tokens/classes (or documented single-class exception), zero JS, zero third-party requests, English copy throughout.

**Clearance:** Design PASS for the three placements above. DEV is cleared to implement exactly this after GitHub preflight. Any scope change (e.g. email capture, new nav item, footer rework, new visual treatment) re-triggers design review per the mandatory rule. No SEC concern introduced — no SEC pre-gate required.
