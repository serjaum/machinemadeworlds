# MAC-10 — OpenDesign Adoption: Design Brief for Machine Made Worlds

**Date:** 2026-09-05 · **Author:** UX & Frontend Designer · **Ref:** https://github.com/nexu-io/open-design
**Scope:** static site (`index.html`, `blog.html`, `about.html`, `posts/*/index.html`, `styles.css`, `sitemap.xml`, `404.html`)
**Prior art:** `UX_AUDIT_MAC-4.md` (baseline, still valid), `QA_GATE_MAC-5.md` (release gate)
**Constraint:** propose only — no commit, no deploy, no secrets.

## 1) Audit delta (what changed since MAC-4)

MAC-4 audited `/_default` vs `/dist` drift. That drift is now resolved: the
workspace root holds a single unified tree (root `styles.css` == `dist/styles.css`,
10118 B; root `index.html` == `dist/index.html`). Remaining open items from
MAC-4/MAC-5 that this brief carries forward:

- Card grids are still bare `<a class="card">` in a div grid — no list semantics
  (`index.html:56`, `blog.html:36`).
- Blog `h1 → h3` skip: `blog.html:26-38` page title `h1`, cards use `h3` with no
  intervening `h2` (MAC-5 gate FAIL, still present).
- Subscribe CTA still uses inline `style="background:var(--text);…"` (`index.html:36`,
  `blog.html:22`, `about.html:22`) — defeats token discipline and focus-ring theming.
- `og:image` (`index.html:18`) still references `/og-cover.jpg`, which does not
  exist in the tree (MAC-5 CRITICAL, still present).
- Sitemap still lists both `/about/` + `/about.html` (same for blog) — duplicate indexing.
- Filter chips (`blog.html:30-35`) are anchors to `#essay`/`#guide`/`#field-note`
  with no matching targets — dead filters, no filtering behavior.

## 2) OpenDesign reference — what we adopt (and what we don't)

OpenDesign (`nexu-io/open-design`) is an agent-native design-delivery tool, not a
single visual theme. What we adopt is its **package contract**, per
`design-systems/README.md` and `docs/design-systems.md`:

- **Three-file package:** `DESIGN.md` (prose, ≥7 substantive H2) + `tokens.css`
  (`:root` semantic custom properties) + `manifest`-equivalent (for us: a header
  comment in `tokens.css` + this brief as provenance, no daemon catalog needed).
- **Semantic tokens over raw values:** components reference `var(--accent)`,
  never repeat hex. Dark variant overrides tokens under a selector, never forks
  component rules.
- **Motion convention:** ease-out `cubic-bezier(0.23,1,0.32,1)`, ~200 ms enter /
  ~140 ms exit, never `ease-in` for UI, never `scale(0)`; continuous motion may
  stay linear. `prefers-reduced-motion` scopes to animated properties only
  (current `styles.css:178` nukes all transitions globally — tighten it).
- **Accessibility contract:** 4.5:1 normal / 3:1 large text on actual pairs,
  visible `:focus-visible` on every control, native semantics preserved, no
  conformance claims without checking each pair.
- **`USAGE.md`-style agent router:** the "Implementation tasks for DEV" (§5) plus
  acceptance criteria (§4) play that role — read-order for the implementer.

What we do NOT adopt: the 151-brand catalog itself, Tailwind mappings, component
fixtures requiring JS, webfonts, or any build step. The site stays zero-JS,
system-font, single-`styles.css`, <15 KB raw CSS.

## 3) Visual direction (locked)

Keep the current dark editorial identity — it already satisfies the OpenDesign
contrast and weight contracts. This is a **token-formalization + semantics +
rhythm** pass, not a rebrand:

- **Atmosphere:** quiet dark canvas (`--bg #0b0b10`), raised surfaces for cards
  (`--bg-raised`), single cyan signal (`--accent-2`) for links/focus/dots, violet
  reserved for brand gradient + guide tags. No new hues.
- **Type:** system stack stays (zero webfont cost). Formalize the scale already
  in use: hero `clamp(28px,7vw,40px)` / article `clamp(26px,6vw,38px)` / section
  `20px` / card `17px` / body `16px` / meta `12–14px`. Add a `--font-mono` token
  (currently bare `ui-monospace…` stack repeated in `styles.css:38`).
- **Spacing rhythm:** 4-pt base (`--space-1:4px` … `--space-7:32px`); grid gap
  `12px` → token; hero padding `28/18` mobile, `42/22` ≥700 px → tokens.
- **Radius/shadow/motion:** `--radius 14px / --radius-sm 9px / --pill 999px`
  (pill is currently a bare `999px` ×7 — tokenize); `--shadow`; `--ease-standard`,
  `--motion-enter 200ms`, `--motion-exit 140ms`.
- **Anti-patterns (do not):** add webfonts or frameworks; use `--accent #7c5cfb`
  as body text (4.47:1 on bg — large-text only); reintroduce `fetch(posts.json)`
  render-blocking; force `<br>` line breaks in hero; inline-style one-off CTAs.

## 4) Acceptance criteria

### Responsive
- [ ] 320 px: header wraps without clipping (brand + 3 links), no horizontal scroll.
- [ ] <700 px single column; ≥700 px two-column card grid; hero actions wrap.
- [ ] Tap targets ≥44 px on nav links, `.btn`, `.chip` (already patched per MAC-4 — regression-guard).
- [ ] Hero `h1` fluid via clamp; remove forced `<br>` or prove no overflow at 280–320 px.
- [ ] CSS budget: `styles.css` <15 KB raw (<4 KB gz); HTML <8 KB/page; zero render-blocking JS.

### Accessibility (WCAG 2.1 AA)
- [ ] Contrast (verified pairs, §6): text 16.67, muted 7.54, muted-2 5.06,
  prose links 11.56, purple tags 8.66 — all ≥4.5:1. No new pair ships below 4.5:1
  (3:1 large-text-only exception documented if ever used).
- [ ] Visible `:focus-visible` (cyan 2 px + 2 px offset) on all links/buttons/cards/chips.
- [ ] Landmarks intact: skip link → `#main`, `header/nav[Primary]/main/footer`,
  breadcrumb `nav`, exactly one `h1`/page, no skipped heading levels
  (fix `blog.html` h1→h3 skip).
- [ ] Card grids use `<ul role="list"><li>` (visuals unchanged, `list-style:none`).
- [ ] Dates in `<time datetime>`, filters operable + honest (real targets or real
  buttons — no dead `#essay` anchors), `prefers-reduced-motion` scoped.
- [ ] Keyboard-only run: brand → nav → main → cards → footer, every stop visible.

### Semantic HTML / SEO
- [ ] Sitemap lists pretty URLs only (`/about/`, `/blog/` — drop `.html` dupes).
- [ ] `og-cover.jpg` ships (1200×630, <80 KB) or `og:image` tags removed (no 404 refs).
- [ ] No inline `style=` attributes in HTML (Subscribe CTA → `.btn-subscribe` class).

## 5) Implementation tasks for DEV (→ child issues)

1. **Tokens pass** — add `tokens.css` semantic layer (§6) and rebind `styles.css`
   to tokens (no visual change; pill radius, mono stack, spacing, motion tokens).
2. **Card-list semantics** — `<ul role="list"><li>` wrap on index + blog grids.
3. **Heading + filter honesty** — fix blog h1→h3 skip; make chips real filters or
   honest anchors; move Subscribe inline style to class; scope reduced-motion.
4. **SEO hygiene** — pretty-URL-only sitemap; og-cover ship-or-remove; keep
   `<time>` pattern on all new posts.

## 6) Tokens (normative — also shipped as `open-design-tokens.css`)

See `open-design-tokens.css` beside this brief. Summary of bindings:

- Color: `--bg #0b0b10`, `--bg-raised #14141d`, `--bg-elevated #1c1c26`,
  `--border #242433`, `--border-soft #2a2a3a`, `--text #ececf1`,
  `--muted #9aa0b5` (7.54), `--muted-2 #7a8196` (5.06), `--accent #7c5cfb`
  (decorative only), `--accent-2 #00d9ff` (links/focus, 11.56),
  `--tag-purple #b8a6ff` (8.66 on raised), `--accent-hover #9376ff`.
- Type: `--font-sans` (system stack, as today), `--font-mono`; scale tokens
  `--text-hero`, `--text-h1`, `--text-h2`, `--text-card`, `--text-body`,
  `--text-meta`; `--leading-body 1.65`, `--leading-tight 1.1`.
- Layout: `--max 860px`, `--content 720px`, `--header-h 56px`,
  `--space-1…7` (4/8/12/16/20/24/32), `--radius 14px`, `--radius-sm 9px`,
  `--pill 999px`, `--shadow`.
- Motion: `--ease-standard cubic-bezier(0.23,1,0.32,1)`, `--motion-enter 200ms`,
  `--motion-exit 140ms`; focus `--focus-ring` (2 px solid cyan, offset 2 px).

No commit, no deploy performed. Files for DEV to commit: this brief +
`open-design-tokens.css`.
