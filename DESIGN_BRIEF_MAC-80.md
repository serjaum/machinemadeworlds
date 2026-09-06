# MAC-80 — Logo brand mark: OpenDesign assessment (Design Agent ownership)

**Date:** 2026-09-06 · **Author:** UX & Frontend Designer (Design Agent) · **Status:** PASS — DEV cleared to implement on a fresh branch from `97683bb` only after GitHub preflight
**Refs:** OpenDesign `https://github.com/nexu-io/open-design` (brief + tokens + prototype-reference contract; semantic tokens only; AA contrast on real pairs; `:focus-visible` everywhere; `prefers-reduced-motion`; native semantics). Prior assessments `DESIGN_BRIEF_MAC-78.md` (additive-pattern precedent, ArticleMarkup gate §4) + `DESIGN_BRIEF_MAC-48.md` (trail/TOC rules). No prototype rewrite — `templates/base.html` masthead/footer + `assets/favicon.svg` are the visual reference.
**Scope:** NEW visual-system element → full evaluation per mandatory rule. Site has no logo asset today: header uses a text-only `.brand-emblem` (`m·w` glyphs in a bordered box, hidden below ~720px), footer is wordmark text only, favicon is a one-off SVG tile, and no `og:image`/`twitter:image` exists. Routine-content rule does NOT apply.
**Parent spec:** issue MAC-80 document `spec` (hand-crafted SVG now, `m·w` monogram + `#204c3d`/`#f7f8f4` brand language; wire favicon/header/footer/OG; record raster/API path for later, do not build it).
**Image-generation situation (Board-verified):** no `OPENAI_API_KEY` in this environment, so raster generation is not callable. Deterministic hand-crafted SVG is the correct now-path; `scripts/gen_image.py` (gpt-image-1, Paperclip-vault key only) stays a recorded later step.

## 1) Evaluation: current vs proposed (decision per row)

| # | Current experience | Proposal (MAC-80) | Design verdict |
|---|---|---|---|
| 1 | Header `.brand-emblem`: serif `m·w` text in a 52px bordered box; `display:none` on small screens so mobile has NO mark | `assets/logo.svg`: opaque rounded-square tile (`#204c3d`), cream (`#f7f8f4`) geometric `m·w` monogram + `#b7d2a4` dot; header renders it as `<img class="brand-mark" width="52" height="52">` at all widths (40px on small screens, never hidden) | **Approve with refinement.** Tile keeps the favicon idiom users already see in the tab; explicit `width`/`height` = zero layout shift. Mobile-hiding the mark is removed — a brand mark that vanishes on phones fails the acceptance criterion. |
| 2 | Footer: wordmark text only, no mark | 28px logo `<img>` before the footer wordmark (`alt=""`, link already labelled) | **Approve as-is.** Same asset, no new file; minor size keeps footer hierarchy (wordmark stays dominant). |
| 3 | `assets/favicon.svg`: one-off tile whose monogram geometry differs from any header mark | Align favicon geometry with `logo.svg` (same tile radius, same monogram paths, same dot); keep file name/path so `build.py` hashing is untouched | **Approve as-is.** Tab icon and header mark read as one brand; zero build changes. |
| 4 | No `og:image` / `twitter:image` on any page | Absolute `https://machinemadeworlds.com/assets/logo.<hash>.svg` in both tags, hashed URL supplied by the builder (`assets/` hashing already exists) | **Approve with noted weakness.** SVG OG is best-effort (several scrapers prefer PNG); README records the raster upgrade path instead of over-claiming. No per-post images in this initiative. |
| 5 | Wordmark set in HTML serif text next to the emblem | Wordmark STAYS as HTML text (lockup = SVG mark + live text, not outlined paths) | **Approve as-is.** Preserves the editorial serif, i18n/zoom reflow, and avoids a second heavy asset. The "lockup" is mark+text in the existing `.brand` flex row. |
| 6 | Single theme-agnostic header (tokens flip via `[data-theme]`) | Single opaque tile for both themes — no `currentColor` split, no theme-specific file | **Refine (simpler than spec sketch).** The spec suggests `currentColor` where possible, but an opaque green tile passes AA on both `--bg` values and keeps one deterministic file. Tile-on-cream and tile-on-ink both read correctly; no variant files. |

No redesign of surrounding experience: masthead layout, nav, theme toggle, footer nav/bottom, OG `title`/`description`/`url`, JSON-LD, feed, sitemap unchanged.

## 2) Token / class reuse plan (`assets/site.css`, additive only)

- Permitted vars only: `--bg --surface --raised --ink --muted --line --accent --accent-ink` + `--sans/--serif/--mono` + `--s1--s3`. The SVG's three hex values (`#204c3d #f7f8f4 #b7d2a4`) live INSIDE the opaque image asset (same status as the existing favicon tile), not as CSS — no new CSS hex.
- Additive classes only, existing selectors untouched except the mobile `display:none` refinement:
  - `.brand-mark { width:52px; height:52px; border-radius:12px; flex:none; display:block; }`
  - `.footer-mark { width:28px; height:28px; border-radius:7px; flex:none; display:block; }` + `.footer-brand { display:flex; align-items:center; gap:10px; }` (keeps current font/letterspacing).
  - Mobile rule change: replace `.brand-emblem { display:none; }` with `.brand-mark { width:40px; height:40px; border-radius:9px; }` — mark persists, layout holds (`flex:none` + fixed box = no shift).
  - Static `grep` gate: added CSS contains zero `#[0-9a-fA-F]{3,6}`, `rgb(`, `@import`, `http`, new `@media` width, `!important`.
- Weight budget: `logo.svg` ≤ 1KB, CSS delta ~+300B, HTML delta ~+200B/page — total added weight < 5KB per acceptance criterion.

## 3) Logo construction (DEV pastes verbatim as `assets/logo.svg`)

64×64 viewBox, `rx=12` tile, monogram drawn with two rounded arch paths + middle dot in cream, accent dot `#b7d2a4` lower-right (echoes favicon). No `<text>` (no font dependency), no gradients/filters/scripts, `role="img"` + `<title>` for standalone use; chrome `<img>` instances use `alt=""` (decorative inside labelled links).

## 4) Usage rules (ship verbatim in README brand section)

- Clear space: ≥ 25% of tile side on all sides; min size 24px (favicon 16px excepted — geometry holds to 16px, dot merges gracefully).
- Do: use the single `logo.svg` everywhere (header/footer/favicon/OG). Don't: recolor, outline, add shadow, place on photographic backgrounds without the tile, or split the monogram from the tile.
- Light/dark: same file both themes (opaque tile). OG/social: SVG is the best-effort fallback; raster PNG path (`scripts/gen_image.py`, gpt-image-1, vault key) is recorded for later and must keep this geometry.

## 5) Responsive / a11y plan

- 360px: 40px mark + 21px wordmark + caption (existing mobile type rule), masthead wraps as today; footer mark 28px inline, no new breakpoint.
- Decorative `<img alt="">` inside links that already carry `aria-label`/text — screen readers hear "Machine Made Worlds, home" once. `:focus-visible` on the link is unchanged. Contrast: cream-on-green ≈ 8.5:1 inside the tile; tile-on-page passes on both themes (opaque, bordered by shape not color).
- `prefers-reduced-motion`: nothing animates. Print: existing rule hides masthead/footer; logo prints nowhere new.

## 6) SEC / QA notes for the pinned-SHA reviews

- SEC: SVG is static paths only — no `script`, `handler`, `foreignObject`, external `href`, or data-URI payload. `build.py` asset hashing is content-addressed; no secret, key, or vault reference enters code (raster path is README prose only).
- QA: verify header/footer/favicon render light+dark at 360/768/1240px, `og:image` absolute URL 200s, added weight < 5KB, buildlog-presence gate green (production change ships its entry in the same PR per MAC-64).

**Clearance:** Design PASS for the tile concept + rules above. DEV is cleared to implement exactly this on `feat/logo-readme` from `origin/main` (`97683bb`). Raster/API work is explicitly out of scope.
