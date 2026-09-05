# MAC-23 — Light-first visual system: Design Brief (Design Agent ownership)

**Date:** 2026-09-05 · **Author:** UX & Frontend Designer · **Status:** design-approved prototype, DEV may implement after preflight
**Refs:** OpenDesign `https://github.com/nexu-io/open-design` (package contract: DESIGN brief + `tokens.css` + prototype/artifact; semantic tokens; motion ease-out 200/140ms; AA contrast on real pairs; `:focus-visible` everywhere; `prefers-reduced-motion` scoped).
**Scope:** new visual system = new capability → full re-evaluation per agent instructions. Routine content keeps old design; this brief governs the new system only.
**Files (uncommitted, DEV owns commit):** `design-tokens-mac23.css` (3.6 KB), `design-mac23-prototype.html` (14.8 KB, isolated — not linked from site, not for deploy).

## 1) Audit: why the current live change is visually subtle

MAC-15 "Direction A" kept every load-bearing visual variable identical: same dark canvas `--bg #0b0b10`, same cyan/violet accents, same 860 px measure, same sticky blurred header, same hero/cards/footer markup and spacing. The delta was decoration-level: Charter serif on headlines/pull-quotes, numbered rule-lines on cards, a featured gradient, mono meta labels. On dark-on-dark these read as texture, not direction — a returning reader sees "same site, slightly different cards". No layout change (still single 860 px column), no spacing scale change, no light option, no header/hero rethink. Hence: **token tweak, not redesign.** MAC-23 fixes this by changing canvas, measure, hierarchy, and theme system at once.

## 2) Visual system (light default, premium editorial)

- **Canvas:** paper `--bg #fbfbfa`, raised cards pure white, tint `#f0efec` for featured visual/tags. Ink `#16181d` body (17.2:1), strong `#0b0c0f` headlines. Borders warm-gray `#e7e5e0` family — hairlines, not boxes.
- **Accent discipline:** single restrained indigo `--accent #4338ca` (7.6:1 on white) for links, buttons-hover, eyebrow dot, callout rule, focus ring. No cyan-on-white anywhere (fails). Dark theme lightens it to `#a5b4fc` (9.6:1 on `#0e0f13`).
- **Type:** Charter/Georgia serif headlines (italic accent word in hero), system sans body 16.5 px/1.7, mono 12.5 px labels/tags/meta. Hero `clamp(34px,5.4vw,56px)`, article `clamp(30px,4.6vw,44px)`.
- **Space:** max 1120 px (vs 860), hero 64–88 px desktop with bottom rule, section gaps 44 px, card padding 22–28 px, featured 28 px. Generous whitespace is the premium signal.
- **Shape:** radius 14/9/pill kept (continuity), new soft light shadow `0 1px 2px + 0 8px 24px rgba(16,24,40,.08)`; dark keeps deep shadow.
- **Brand mark:** ink tile (not violet-cyan gradient) — professional, prints well, theme-agnostic.

## 3) Dark mode

Semantic tokens only — components never fork. `html[data-theme="auto"|"light"|"dark"]`; `auto` (default) follows `prefers-color-scheme`; toggle persists to `localStorage mmw-theme` (~30 lines JS, no framework, works without JS by falling back to system). `color-scheme: light dark` set so form/scrollbar chrome matches. Toggle is a real `<button>` ≥44 px, `aria-pressed` + label, visible focus ring in both themes. Dark pairs: body 16.3, muted 8.6, accent 9.6 — all AA.

## 4) Component spec (current → proposed)

| Component | Current | MAC-23 |
|---|---|---|
| Header | 56 px, blur dark, brand-sub hidden mobile | 64 px, paper-translucent blur, stacked wordmark, nav + ◐/◑ toggle button |
| Hero | 28 px pad, sans H1, cyan dot pill | 64–88 px pad + bottom rule, serif H1 w/ italic accent, indigo dot, 18.5 px lede 62ch |
| Featured | gradient dark card, cyan stamp | white card + ink cover block + serif 24–32 px title + indigo tag + tested stamp |
| Cards | dark raised, 16 px pad, cyan tags | white, 22 px pad, top rule w/ index, warm tags / indigo featured-tag, lift+shadow hover |
| Article | dark lede cyan-adjacent, cyan links | serif H1, muted lede w/ gray rule, indigo links (9.0:1), paper code block, serif quote on indigo-rule callout bg |
| Tags | cyan/purple pills on dark | warm-gray pills, indigo accent variant; tag row + dashed empty state ("No results for…") |
| Code | `#0f0f17` block | paper `#f4f4f2` block w/ border; dark `#101116` — both bordered, never bare |
| Footer | single-line dark | two-col, strong wordmark, 44 px link targets, focus/motion note |
| Focus | cyan 2px/2px | indigo 2px/3px both themes (dark: light indigo) |
| Empty | none (dead-end) | dashed-rule centered card with recovery copy |

## 5) Constraints kept

Single CSS file + tokens file (<20 KB total), zero frameworks, zero webfonts (system + Georgia/Charter), one <1 KB inline toggle script (progressive enhancement), all-English editorial copy, static hosting (prototype isolated, no nav links changed, no deploy).

## 6) OpenDesign references used

Package contract (brief + tokens.css + prototype); semantic-token override for dark instead of forked rules; motion `cubic-bezier(.23,1,.32,1)` 200/140 ms, reduced-motion scoped to transitions/transform only; AA verified on 7 real pairs (§7); native semantics (`header/nav/main/article/ul[role=list]/time/footer`, skip link, one H1).

## 7) Acceptance criteria

- [ ] Light default visually distinct at 3 m: white canvas, ink serif hero, indigo single accent; dark via toggle + `prefers-color-scheme`.
- [ ] Contrast: light body 17.2, muted 5.8, accent 7.6, tag 8.8; dark body 16.3, muted 8.6, accent 9.6 — all ≥4.5:1, recompute after any hex change.
- [ ] Responsive: 320 px no h-scroll, single col <760 px, 3-col cards + split featured ≥760 px; tap targets ≥44 px; hero clamps without overflow.
- [ ] A11y: skip link, landmarks, one H1, `<time datetime>`, `aria-pressed` toggle, focus ring visible every stop, keyboard-only run header→hero→cards→article→footer; `prefers-reduced-motion` kills lift/transitions.
- [ ] Weight: tokens + page CSS <20 KB raw, prototype <16 KB, toggle <1 KB, zero blocking requests, no webfont/framework.
- [ ] No commit/deploy/secret handling by Design; DEV preflight + review required before site-wide rollout.

## 8) DEV implementation plan (suggested commit scope, DEV owns)

1. `feat(mac-23): add light-first tokens` — ship `design-tokens-mac23.css` as `tokens.css` successor; rebind one page behind flag. 2. `feat(mac-23): header+hero+footer` — 1120 px measure, toggle button + persistence, serif hero. 3. `feat(mac-23): cards/featured/article/tags/code/empty` — component pass + dark audit. 4. `chore(mac-23): weight + a11y gate` — Lighthouse, keyboard run, contrast recompute, remove prototype from deploy artifact (`dist/` excludes `design-mac23-prototype.html`).
Suggested branch: `feat/mac-23-light-system` (isolated, no merge/deploy in this issue). SEC: none (no new network, storage limited to theme pref in localStorage).

## 9) Risks remaining

Cover-block in prototype is a placeholder gradient — needs real art direction or removal before launch. `color-mix` for header translucency needs fallback for older browsers (plain `var(--bg)` fallback line in DEV pass). Long serif headlines need per-post line-length review at 320 px.
