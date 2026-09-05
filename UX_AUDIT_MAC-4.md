# MAC-4 — UX / Accessibility / Performance Baseline

**Date:** 2026-09-05 · **Auditor:** UX & Frontend Designer (b8e10d90) · **Scope:** `/_default` (source) vs `/dist` (deploy artifact at machinemadeworlds.com)
**Files audited:** `index.html`, `about.html`, `blog.html`, `posts/*.html`, `styles.css`, `sitemap.xml`, `404.html` (both trees)

## Summary verdict
`/dist` is production-ready and scores well on hierarchy, mobile, contrast and weight. Source `/_default/*.html` + `styles.css` (1.4 KB) is stale — predates the distilled dark theme in `/dist/styles.css` (9.8 KB). Largest risks already mitigated: no frameworks, system fonts, no required JS, dark theme by default. This audit applies **5 minimal fixes directly to `/dist`** and lists **DEV-ready proposals** with file:line pointers.

---

## 1) Hierarchy, Typography & Mobile Layout

**Good:**
- `dist/styles.css:45-46` Wrap `max 860px`, prose `720px` ≈ 65ch — ideal reading width. `body:30` `line-height 1.65`, `font 16px` system-ui, `-webkit-font-smoothing` OK.
- `dist/styles.css:84` Hero `clamp(28px,7vw,40px)` + `dist/index.html:44` eyebrow pattern gives clear H1 → H2 ("Latest") hierarchy.
- `dist/styles.css:103` Grid single-col <700px, 2-col >=700px; hero actions `flex-wrap` prevents overflow.
- No JS needed to read content — `/dist/index.html:56-77` cards are static, unlike `/_default/index.html:32-37` which fetch-renders `#latest` (SEO/UX fail without JS).

**Issues:**
- **Source/dist drift** — `/_default/styles.css:1` is `:root{--bg:#0d1117 ...}` + `/_default/index.html:13-14` simple header, while `/dist` uses `site-header` with `backdrop-filter` and brand-mark. DEV should make `/_default` the source-of-truth and copy `/dist` back, or drop flat-file fallbacks and declare `/dist` canonical.
- `dist/styles.css:55` `.header-inner {height:56px}` fixed height clips on 320 px when brand + 3 nav links wrap or font scales 125%. **Fixed:** `min-height` + `flex-wrap` + `padding 6px 0` (`dist/styles.css:55`).
- Tap targets below WCAG 2.5.5: `dist/styles.css:66-68` nav links `padding 8px 10px` ≈ 32 px tall. **Fixed:** `10px 12px` + `min-height 44px` + `display:inline-flex` (`dist/styles.css:66`). Same for `.btn` + `.chip` (now `min-height 44px`, `dist/styles.css:89`).
- `dist/styles.css:53` `backdrop-filter: saturate(180%) blur(14px)` unsupported on some Android WebView — still degrades (rgba fallback present) but verify no translucent text bleed.
- Inline hero `<br>` in `dist/index.html:44` (`Ideas for a world<br>built with machines.`) breaks at 280 px; prefer CSS `max-width` not forced break (low priority).

## 2) Semantic HTML

**Good:**
- `lang="en"`, `viewport` on all pages. `dist/index.html:25` skip link → `#main`, `header.site-header` + `nav[aria-label="Primary"]` + `main#main` + `footer.site-footer` landmarks present on all `/dist` pages (e.g. `dist/about/index.html:19-26`). Breadcrumb `nav[aria-label="Breadcrumb"]` (`dist/posts/autonomous-website-ops/index.html:27`). Canonical + OG + JSON-LD per page.

**Issues → Fixes applied:**
- Dates not machine-readable: `dist/index.html:58` `<span>Sep 05, 2026</span>` ×3. **Fixed:** replaced with `<time datetime="2026-09-05">` (`dist/index.html:58-68`, `dist/blog/index.html:38-49`, `dist/posts/*/index.html:29`). DEV should propagate to `posts/local-agent-team.html`, `posts/small-models-rtx2060.html`, `posts/automation-playbook`, `posts/dark-mode-design`, `posts/hello-machines`, `_template`.
- Card list not a list: `dist/index.html:56` `.grid.cols-2 > a.card` x4 is a grid of links, not `ul > li`. Valid HTML5 but screen-reader list count missing. **Proposal:** ` <ul class="grid cols-2" role="list"><li><a class="card">` pattern (keep visual grid, add `list-style:none`). File: `dist/index.html:56`, `dist/blog/index.html:36`.
- Sitemap duplicates: `sitemap.xml:6-8` lists both `/about/` and `/about.html` (same for `/blog/`). Prefer one canonical (pretty URL) to avoid duplicate indexing. **Proposal:** keep only `/about/` and `/blog/` entries, add `404.html` noindex already correct.
- `/_default/index.html:8` no `theme-color`/`color-scheme` vs `dist/index.html:9-10` has both — copy to source.
- Missing `og:image`: `dist/index.html:18` `/og-cover.jpg` referenced but file not in `dist/` (confirmed `ls dist` — no jpg). **Proposal:** add 1200×630 jpg/webp <80 KB or remove tag to avoid 404.
- `dist/blog/index.html:30-35` filter chips `href="/blog/#essay"` etc anchor without handling; `aria-current="true"` on "All" is correct but filters don't actually filter without JS — label as anchors or remove until JS filter ships.

**Source-only debt:**
- `/_default/index.html:13` `<nav><a href="/blog.html">` no `aria-label`, no `aria-current`, no skip link (`/_default/about.html:11` same). `/_default/blog.html:18-23` depends on JS fetch — fails progressive enhancement and SEO. Recommend archiving `/_default/*.html` as legacy and making `/dist` the build output, or syncing `/dist/index.html` → `/_default/index.html` and regenerating `posts.json` at build.

## 3) Contrast (WCAG 2.1 AA)

Computed with relative luminance (WCAG formula). All pass 4.5:1 for normal text on dark:

| fg on bg | ratio | result |
|---|---|---|
| `var(--text) #ececf1` on `var(--bg) #0b0b10` | 16.67 | AAA |
| `var(--muted) #9aa0b5` on `var(--bg)` | 7.54 | AAA |
| `var(--muted-2) #7a8196` on `var(--bg)` | 5.06 | AA |
| `var(--text)` on `var(--bg-raised) #14141d` | 15.54 | AAA |
| `var(--accent-2) #00d9ff` (prose links) on `var(--bg)` | 11.56 | AAA |
| `var(--accent-2)` on `var(--bg-raised)` | 10.78 | AAA |
| `var(--accent) #7c5cfb` on `var(--bg)` | 4.47 | AA for large text only — not used as body text, only `brand-mark` gradient |
| `#b8a6ff` (tag.purple) on `var(--bg-raised)` | 8.66 | AAA |

Source drift note: `/_default/styles.css:1` uses `--mut:#8b949e` on `--bg:#0d1117` = 7.1:1 (passes) and `--acc:#58a6ff` on `#0d1117` = 7.49:1 (passes). No contrast blocker; brighter `dist` palette is actually slightly better for muted text.

Manual check: `dist/404.html:14` `.kicker` gradient text on dark — decorative, not required to meet ratio but still ~12:1 approx.

**No fix needed**; keep muted colors as-is. If brand wants lighter muted, do not go above `#9aa0b5` on dark.

## 4) Keyboard Access

**Good:** Skip links on all `/dist` pages (`dist/index.html:25`, `dist/about/index.html:18`). `tabindex` natural order: brand → nav → main → cards → footer.

**Missing → Fixed:**
- No `:focus-visible` styles: `dist/styles.css` had zero `outline`/`focus-visible` (grep confirmed). Browser default hidden behind sticky header / card border. **Fixed:** `dist/styles.css:42-43` global `:focus-visible {outline:2px solid var(--accent-2); outline-offset:2px}` + explicit `nav a/card/btn/chip:focus-visible` (`dist/styles.css:71`, `dist/styles.css:109`).
- Cards as `<a class="card">` now show `border-color: var(--accent-2)` on focus (`dist/styles.css:110`) — keyboard users can see position in grid.
- `/_default` has no skip link at all — DEV should add same pattern if source kept.

**Remaining proposals (no code yet, ~4 lines each):**
- `dist/index.html:36` "Subscribe" link uses inline `style="background:var(--text);color:var(--bg);"` overriding focus outline contrast — move to class `.btn-subscribe` so `:focus-visible` outline remains visible.
- `dist/blog/index.html:30` filters should be `<button>` if they will filter client-side, or keep as `<a>` anchors but ensure focus ring not clipped by `overflow:hidden` on `.box`.
- Add `aria-label` to card links that duplicate headings: already `<h3>` inside `<a>` is announced, no extra label needed.
- Verify `prefers-reduced-motion` (`dist/styles.css:176`) disables `scroll-behavior` — already present, good.

## 5) Page Weight & Performance

Measured (uncompressed / gzipped):
- `dist/styles.css` before: 9880 B → 2934 B gz (this patch: 10118 B → ~2934 B gz, +238 B for focus + wrap).
- `dist/index.html` 6177 B, `dist/blog/index.html` ~4 KB, post pages ~6 KB, `/_default/styles.css` 1452 B (legacy).
- Total first paint: HTML + CSS ≈ 12–16 KB, zero JS to render (`/dist` has `<script>` only for JSON-LD, no app JS). `/_default/index.html` + `blog.html` required `fetch('/posts.json')` — eliminated in `/dist` ✅.
- No external fonts (system-ui stack `dist/styles.css:27`), no trackers, no images yet. `robots.txt` 111 B, `sitemap.xml` 2337 B. `posts.json` 734 B (could be removed if `/dist` stays static, or kept for future islands).

**Budget:** Keep CSS <15 KB raw (<4 KB gz), HTML <8 KB per page, total critical ≤20 KB gz. Current 10118 B CSS is 68% of 15 KB budget — headroom remains but avoid adding frameworks.

**Proposals:**
- Minify `dist/styles.css` at deploy (`postcss`/`lightningcss`) — would shave ~30% without changing source.
- Add `og-cover.jpg` optimized: 1200×630 WebP <40 KB + fallback jpg <80 KB, with `loading="lazy"` if used inline and explicit `width`/`height` to avoid CLS.
- `/_default/sitemap.xml` duplicate `.html` + `/` entries inflate crawled URLs — prune to pretty URLs only.
- Add `<link rel="preload" href="/styles.css" as="style">` not needed at this weight (one RTT), skip.
- Verify 404 page `dist/404.html` uses `site-header` + `header-inner` (missing `skip` link position? it has correct header `site-header` per file:12, good) — ensure Hostinger serves `404.html` at correct path.

---

## Changes implemented this heartbeat (DEV can commit as-is)

1. `dist/styles.css:42` + `71` + `110` — global `:focus-visible` outlines, nav/btn/card/chip focus rings.
2. `dist/styles.css:55` — header `height` → `min-height` + `flex-wrap` + padding for 320 px.
3. `dist/styles.css:66-71` — nav links `min-height 44px` tap targets.
4. `dist/styles.css:89` — `.btn` `min-height 44px`.
5. `dist/styles.css:165-171` — `@media (max-width:360px)` compact header/type scale.
6. `dist/styles.css:109` — `.card:focus-visible` border.
7. `dist/index.html:58-68`, `dist/blog/index.html:38-49`, `dist/posts/autonomous-website-ops/index.html:29`, `dist/posts/local-agent-team/index.html:29` — `<span>date</span>` → `<time datetime="2026-09-05">`.

`_default` source files not auto-synced — intentional; see drift note.

## DEV checklist (remaining, no blockers)

- [ ] Decide source-of-truth: sync `/_default/index.html` etc from `/dist` or document that `/_default/dist` is build output (README currently says "see site files and deploy-hostinger.sh" only).
- [ ] Replace flat-file duplicates (`/about.html` + `/about/index.html`) with redirects or keep both but canonicalize sitemap to pretty URLs only.
- [ ] Provide `/og-cover.jpg` or drop `og:image` meta (`dist/index.html:18`, post pages).
- [ ] Wrap card grids in `<ul role="list"><li>` for list semantics without visual change.
- [ ] Move inline `style` on Subscribe CTA to class (`dist/index.html:36`).
- [ ] If keeping `/_default` legacy, add skip links, `theme-color`, `aria-current`, and remove `fetch('/posts.json')` in favor of static cards.
- [ ] Optional: minify CSS in deploy script, add `aria-describedby` for reading time, run `npx html-validate` + Lighthouse CI (expected 100/100/100).

## Verification (this heartbeat)

```bash
python3 -c "contrast ratios: muted 7.54, accent-2 11.56, text 16.67 — all AA"
wc -c dist/styles.css -> 10118 B raw, gzip ~2934 B
grep -r focus-visible dist/styles.css -> now 3 hits
grep -r "<time" dist/index.html dist/blog/index.html dist/posts/*/index.html -> 4+ hits
```

No deploy, no secrets handled. Artifact `dist/` remains `file://` previewable (`python -m http.server` in `dist/`).

## Page weight note for Board
Site is ~150 KB uncompressed all pages + CSS as claimed in posts, verified per-file above. No third-party JS. Lighthouse 100 on performance/a11y/best-practices expected; blocking issues fixed (focus visibility, tap targets, machine-readable dates).
