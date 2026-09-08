# MAC-167 — 1200×630 brand social card: OpenDesign clearance (Design Agent ownership)

**Date:** 2026-09-08 · **Author:** UX & Frontend Designer (Design Agent) · **Status:** PASS — DEV cleared to generate `assets/social-card.png` to this spec
**Refs:** OpenDesign `https://github.com/nexu-io/open-design` (brief → direction → artifact → handoff loop; brand contract = design system + tokens; agent-native deterministic artifacts). Prior clearances `DESIGN_BRIEF_MAC-80.md` (logo tile geometry + usage rules) + `DESIGN_BRIEF_MAC-78.md` (additive-pattern precedent). Visual reference: `assets/logo.svg` tile + `templates/base.html` masthead lockup.
**Scope:** NEW visual-system element → full evaluation per mandatory rule. Site has no raster social card today: every page emits `og:image`/`twitter:image` pointing at the hashed `logo.svg` (`scripts/build.py:434`), and `twitter:card` is `summary`. Routine-content rule does NOT apply. Everything else — header, footer, favicon, masthead lockup, OG title/description/URL, JSON-LD, feed, sitemap — reuses the existing system unchanged. `logo.svg` stays the single master mark for favicon/header/footer. No code changes in this task; this brief is the clearance record only.

## 1) Evaluation: current vs proposed (decision per row)

| # | Current experience | Proposal (MAC-167) | Design verdict |
|---|---|---|---|
| 1 | `og:image` = 64×64 SVG tile (`logo.svg`). Several scrapers (X, LinkedIn, iMessage) prefer or require PNG ≥ 600px wide; link shares render small, cropped, or fall back to no image | New `assets/social-card.png`, exactly 1200×630, brand lockup on theme background | **Approve.** Closes the documented MAC-80 weakness ("SVG OG is best-effort"). One static file, no template redesign. |
| 2 | No small-card legibility story: the SVG tile alone at 120px reads as a green square, wordmark absent | Card carries mark + live-wordmark-equivalent raster text; lockup legible at 300px wide, mark identifiable at 120px thumbnail | **Approve with constraint.** Tagline/URL are decorative below ~300px; mark + wordmark must carry identity alone (see §3 safe margins + §5 checks). |
| 3 | `twitter:card` = `summary` (correct for the tiny SVG) | DEV switches to `summary_large_image` + adds `og:image:width/height` (1200/630) when wiring the PNG | **Refine (DEV scope).** Design mandates it; without it scrapers downscale the card to a thumbnail and the clearance intent is lost. |
| 4 | Single SVG hashed by the builder; no weight concern (~442 bytes) | PNG <300KB target (<1MB hard fail). Flat token colors, no photo/gradient/texture — compresses deterministically | **Approve as-is.** Flat dark card of this type typically lands 40–120KB; budget is generous but binding (see acceptance criteria). |
| 5 | Favicon/header/footer share `logo.svg` geometry | `logo.svg` and `favicon.svg` untouched; social card reuses the tile geometry at large size, never redraws it | **Approve as-is.** No new mark, no variant tile, no recolor — MAC-80 usage rules extend verbatim to the card. |

No redesign of surrounding experience: masthead, nav, theme toggle, footer, OG `title`/`description`/`url`, JSON-LD, feed, sitemap, print/reduced-motion rules unchanged.

## 2) Card spec (DEV builds exactly this)

- **Canvas:** 1200×630px PNG-24, opaque (no alpha). Landscape lockup, optically centered.
- **Background:** dark-first theme background `--bg` = `#171d1a` (flat fill, zero gradients/textures — keeps weight low and matches the dark-first editorial identity; dark cards also stand out in light feeds).
- **Lockup (left-to-right, vertically centered):**
  - Brand tile: `logo.svg` geometry rendered at 200×200px (tile `#204c3d`, cream `#f7f8f4` monogram, sage `#b7d2a4` dot — MAC-80 paths verbatim, scaled only).
  - Wordmark: `machine made worlds`, serif (site `--serif`: Iowan Old Style / Palatino Linotype / Georgia fallback rasterized), ~76px, cream `#f7f8f4`, `letter-spacing: -0.04em`.
  - Tagline: `A journal of artificial intelligence`, sans (`--sans` stack), ~26px, muted `#aebcad`, uppercase `letter-spacing: .08em` (echoes `.brand-caption`).
  - URL line (optional, small): `machinemadeworlds.com`, mono (`--mono` stack), ~22px, muted `#aebcad`.
- **Colors (only these five):** `#171d1a` bg · `#f7f8f4` wordmark/monogram · `#204c3d` tile · `#b7d2a4` accent dot · `#aebcad` secondary text. All are existing semantic tokens / MAC-80 asset hex — no new palette.
- **Typography:** rasterized equivalents of the live site stacks only; no webfonts embedded, no outlined-logo lockup. Wordmark stays live HTML text on the site itself — the PNG text is a frozen instance for scrapers only.
- **Safe margins:** 64px clear space on all sides (≥ 10% of height, extends MAC-80's ≥25%-of-tile rule to card scale). Critical content (tile + wordmark) inside x 120–1080 / y 110–520 so platform crops (Slack/X ~60px bands) never clip identity. Tagline/URL may sit lower but inside the 64px frame.
- **Small-card behavior:** at 300px wide, wordmark ≈ 19px effective — legible; at 120px thumbnail, tile + first words identifiable, tagline drops out gracefully (accepted, documented).
- **Contrast:** cream on ink-green/dark ≈ 12+:1; muted `#aebcad` on `#171d1a` ≈ 7+:1 — AA/AAA for the large-text card use. Decorative `<img>`-equivalent: scrapers pair it with `og:title`/`og:description`, so no information lives in the image alone.
- **Export settings:** 1200×630 exact, PNG-24, no transparency, no ICC bloat (sRGB default), post-process with `optipng -o7` or `pngquant` (256-color acceptable — flat palette degrades losslessly); strip metadata. Target <300KB, hard fail ≥1MB. Deterministic re-export must be byte-reproducible from the checked-in vector source + script (DEV records the recipe in the build-log entry).

## 3) Token / asset reuse plan (additive only, DEV scope)

- No new CSS, no new tokens, no new breakpoints, no template restyle. The PNG's hex values live INSIDE the opaque image asset (same status as the existing favicon/logo tiles per MAC-80 §2).
- `logo.svg` / `favicon.svg` / header (52px, 40px mobile) / footer (28px) byte-identical. Builder change is wiring-only: emit hashed `social-card.png` as absolute `og:image`/`twitter:image`, flip `twitter:card` to `summary_large_image`, add `og:image:width`/`height` + `og:image:alt` ("Machine Made Worlds — a journal of artificial intelligence").
- Weight delta: one PNG (<300KB, single shared file, cacheable, preconnect-free) — page HTML delta ~+200B meta. No render-blocking impact; card loads only on scraper fetch, never in-page.

## 4) Responsive / a11y / performance checks (for QA pin)

- Scraper matrix: validate rendered card via X Card Validator / LinkedIn inspector / Slack unfurl equivalents at full + small sizes; wordmark legible at 300px, tile identifiable at 120px.
- `og:image` absolute URL 200s; dimensions exactly 1200×630; file size <300KB (<1MB hard fail); `twitter:card` = `summary_large_image`.
- In-page a11y unchanged: no new `<img>` in chrome, masthead/footer semantics untouched, `:focus-visible` and `prefers-reduced-motion` unaffected (static asset, nothing animates).
- English editorial identity preserved: wordmark + tagline copy verbatim from `content/site.json` + masthead caption; no new slogans.

## 5) SEC notes

Static PNG, no script/handlers/external refs — nothing to inject. No secrets in the export path; if DEV rasterizes from SVG, the recipe uses local deterministic tooling only (no API keys, no vault access, no network fetch at build). No SEC blocker anticipated; SEC still reviews the wiring diff per standing flow.

## 6) Acceptance criteria (DEV done ⇔ all true)

1. `assets/social-card.png` exists at exactly 1200×630, <300KB (<1MB hard fail), five approved colors only, 64px safe margins, tile geometry identical to `logo.svg`.
2. Mark + wordmark legible at 300px-wide render; tile identifiable at 120px thumbnail (screenshot evidence in build-log entry).
3. `logo.svg`/`favicon.svg`/header/footer unchanged; wordmark remains live HTML text on-site.
4. Wiring (separate DEV implementation): absolute hashed `og:image`/`twitter:image`, `twitter:card` = `summary_large_image`, `og:image:width/height/alt` present; scraper previews verified.
5. Build + full test suite + buildlog-presence gate green; production change ships its Build Log entry in the same PR per MAC-64.

**Clearance:** Design PASS for the spec above. DEV is cleared to generate + wire `assets/social-card.png` exactly to §2/§6 after GitHub preflight. Any scope change (per-post cards, new palette, layout/texture additions, template restyle) re-opens design review before implementation.

**Handoff:** changed file in this task: `DESIGN_BRIEF_MAC-167.md` (this record) only — no code, no assets, no commits (DEV owns commits). OpenDesign refs used: brief→direction→artifact→handoff loop, brand-contract tokens, deterministic-agent-artifact pattern. Remaining visual risk: low — scraper-side recompression may soften the 22px URL line; accepted since tile + wordmark carry identity.
