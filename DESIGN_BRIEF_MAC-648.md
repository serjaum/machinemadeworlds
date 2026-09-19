# MAC-648 — Star Harvest arcade + game page: OpenDesign visual clearance (Design Agent ownership)

**Date:** 2026-09-19 · **Author:** UX & Frontend Designer (Design Agent) · **Status:** PASS — DEV cleared to implement after GitHub preflight
**Refs:** OpenDesign `https://github.com/nexu-io/open-design` (reuse-the-system contract: additive only, semantic tokens, native semantics, `:focus-visible`, `prefers-reduced-motion`, AA on real pairs). Inspected `templates/base.html`, `templates/archive.html`, `templates/card.html`, `templates/about.html`, `templates/newsletter.html`, `assets/site.css` (369 lines, tokens + 980/700px breakpoints + reduced-motion guard).
**Scope:** NEW capability — no `/games/` route, game template, canvas page, or arcade asset exists (`glob content/games/*` = absent; `grep -ri "games" templates/ scripts/build.py` = no arcade family on clean tree) → full re-evaluation per mandatory rule. Routine-content shortcut does NOT apply.
**Parent spec:** MAC-648 Game Creator proposal VERIFIED (comment 98022c56-3908-4676-b2f6-e17ce00666c0, 2026-09-19, 5-item gate ALL PASS vs MAC-657). This brief clears the visual/UX delta only; loop/tech/scope/acceptance/budget already verified upstream.
**Family reuse note:** Task cites `DESIGN_BRIEF_MAC-649.md` (Star Drift `/games/` + game-page family, PASS 2026-09-19). That file is **absent from the repo root** at review time (glob `DESIGN_BRIEF_MAC-64*` = zero hits). This brief therefore reconstructs the family from the closest committed precedents — `DESIGN_BRIEF_MAC-484.md` structure, `archive.html` + `card.html` idiom, `about.html` page-layout precedent, `site.css` semantic tokens — and clears the Star Harvest DELTA explicitly in §1 rows 4–7 so a later MAC-649 backfill cannot silently conflict. Additive-only; if MAC-649 lands with different class names, DEV must reconcile to this brief (new review).

## 1) Evaluation: current vs proposed (decision per row)

| # | Current experience | Proposal (MAC-648 spec) | Design verdict |
|---|---|---|---|
| 1 | No `/games/` index. Closest precedent: `archive.html` (`.container` > `.page-heading` + `.archive-list` of `card.html` `.story` articles) and `about.html` page-heading idiom. Nav has Home/Journal/Build Log/About; footer links journal/glossary/build-log/metrics/prices/benchmarks/about/terms/privacy/newsletter/feeds. | `/games/` index listing Star Harvest + "more coming" note; SEO title/description; reuse site tokens/chrome. | **Approve with refinement.** Build index as `archive.html` family, NOT a new layout: `.container` > `header.page-heading` (eyebrow "The arcade", H1 "Star Harvest and what's next.", one-line standfirst) + `.archive-list` containing ONE `card.html`-shaped `.story` (topic-label "Arcade", title "Star Harvest", pitch as description, Play link) + a static `.callout` "More games coming" note. No new grid, no new card component, no nav item (footer link optional later — out of scope). Pastable HTML in §3. |
| 2 | No game page. Closest precedent: `about.html` `.about-layout` (aside + `.article-body`) for heading + how-to + devlog column flow. `ArticleMarkup` rejects `canvas`/`script`/`button` in post bodies → standalone pages + hashed assets required. | `/games/star-harvest/` with canvas + how-to + HUD + restart + devlog paragraph; SEO title/description. | **Approve as-is (with exact construction).** New `templates/game.html` (standalone, bypasses ArticleMarkup): `.container` > breadcrumbs Back-to-arcade + `header.page-heading` (eyebrow "Star Harvest", H1, one-line pitch) + `<section class="game-stage">` (canvas + HUD + controls) + `.about-layout`-equivalent grid (aside "How to play" + `.article-body` with How-to H2, Restart H2, Devlog H2). Server-rendered static shell; single same-origin hashed JS + single hashed CSS, no imports/network. |
| 3 | No HUD pattern. Site live regions: `archive.html` has exactly one `role="status"` (`p.sr-only[data-search-status]`). Buttons: `.button` (48px) / `.story-arrow` (44px) / `.text-link` (44px). | HUD: score + lives + time + combo + best; restart always; pause/resume; mute. | **Approve with refinement.** HUD is a 4+1 `dl` row (Score / Time / Lives / Combo + Best) rendered as **plain text outside the canvas** (DOM, not canvas-drawn text) so it is readable, zoomable, and contrast-checkable. Exactly ONE live region: `p[role="status"]` announces run state only (ready / paused / game-over / best) — score/timer/combo NEVER announced (avoid screen-reader spam). Combo is the family DELTA: 4th `div` in the same `dl`, `font-variant-numeric: tabular-nums`, `aria-hidden="false"` but excluded from live region by construction. Buttons reuse `.button` verbatim (Start/Pause/Restart/Mute ≥44px, visible pause ≥44px on touch). |
| 4 | No canvas palette. Site tokens: `--bg/--surface/--raised/--ink/--muted/--line/--accent/--accent-ink` + `--art/--art-line/--art-core/--art-ink` (light + dark pairs, AA on text pairs). Canvas sprites: none (procedural only, no AI art). | Star-vs-asteroid canvas palette: collect drifting stars, avoid asteroids; pilot ship on single canvas; pooled particles; screen flash on hit (suppressed under reduced-motion). | **Approve with refinement (DELTA cleared).** Canvas entities MUST NOT rely on color alone: stars = 4-point spark + light fill; asteroids = irregular polygon + dark stroke; ship = triangle + outline. Fill/stroke pairs drawn from existing token ramps only (light: ink `#222d27` / muted `#5c685e` / accent `#285640` on bg `#f7f8f4`; dark: ink `#e9eee3` / muted `#aebcad` / accent `#b9d3a5` on bg `#171d1a`). DEV samples canvas pixels in both themes and asserts star-vs-asteroid contrast ≥3:1 (non-text) and HUD text AA on real pairs (§6). Hit flash + shake + particles fully gated behind `prefers-reduced-motion` (JS `matchMedia` check + CSS guard); reduced-motion substitutes: 2px outline pulse on ship + text "Hit — 2 lives left" in the single live region. No new hex in CSS; canvas colors read from `getComputedStyle` tokens at runtime (zero new tokens). |
| 5 | No timer/loop UI. Timed runs: none. Countdown precedent: none. | 90s timed run display; combo grows on pickups <2.5s apart, resets on hit/gap-timeout; 3 lives + brief invulnerability; ends at 0 lives or timer; best in localStorage. | **Approve with refinement (DELTA cleared).** Timer is a 5th HUD `div` (`Time 1:30 → 0:00`, tabular-nums, `aria-hidden` from live region; announced only at 0:10 warning + 0:00 end via the single status node). Timer text + `progress` semantics: use `<span>` text (not `<progress>`, to avoid restyling a new component); deterministic `mm:ss` format. localStorage best: namespaced integer-only key (`mmw.star-harvest.best.v1`), `parseInt` + clamp, never rendered as HTML (textContent only), never sent anywhere. Invulnerability blink suppressed under reduced-motion (static outline instead). |
| 6 | Inputs: global search box (44px), TOC links (44px), keyboard `:focus-visible` everywhere. No game inputs, no touch steering, no D-pad. | Desktop Arrows/WASD thrust + P/Esc pause + Enter start/restart + M mute; touch drag-to-steer (D-pad fallback), tap start/restart, 44px pause button. | **Approve with refinement (DELTA cleared).** Keyboard: canvas wrapper focusable, all actions also available as real `<button>`s (Start/Pause/Restart/Mute) so keyboard-only full loop never requires canvas focus; visible `:focus-visible` inherits `site.css:31` unchanged. Touch: drag-to-steer on canvas with a **visible hint** ("Drag to steer" caption under canvas, `hidden` once first drag starts); coarse-pointer-only native D-pad (`<div class="game-pad">` with 4 × 48px buttons, `display:none` unless `(pointer:coarse)`, no JS sniffing) as fallback. Page scroll never hijacked: `touch-action: pan-y` on canvas, arrows/`Space` preventDefault ONLY when game focused. Every control ≥44px; canvas itself never a button. |
| 7 | Breakpoints 980px/700px; `.rss-band` stacks mobile; `.archive-list` 2-col → 1-col; `about-layout` aside hidden mobile. Motion: global `@media (prefers-reduced-motion: reduce)` kills animation/transition. Weight budget: JS+CSS ≤60KB uncompressed, page ≤150KB first load, 60fps mid laptop. | Reuse site tokens/chrome; zero deps, no CDN, same-origin single script; RAF loop, capped delta, pooled particles; WebAudio bleeps + mute only. | **Approve as-is.** Game CSS is one additive `game-*` block (§2), grid collapses like `.archive-list` (3-col HUD → 2-col → stacked stage). Canvas fixed aspect 16/10, `max-width:100%`, never larger than `--reading` column rhythm on desktop. Weight: HUD/controls are DOM (≈2KB HTML); canvas JS draws shapes only (no sprites/audio assets); DEV reports measured fps + weight, nothing pre-claimed here. |

No redesign of surrounding experience: masthead, nav (no new item), theme toggle, search, footer, feeds, sitemap, JSON-LD, OG tags unchanged.

## 2) Token / class reuse plan (`assets/site.css`, additive only)

- Permitted: existing semantic vars ONLY (`--bg --surface --raised --ink --muted --line --accent --accent-ink --art --art-line --art-core --art-ink --max --gutter --reading --s1…--s6`, `--serif/--sans/--mono`). No new hex, no new `@media` width, no `@import`/font/trackers/CDN.
- Allowed additive block (ONE, namespaced, tokens only — DEV pastes after the MAC-78/MAC-102 trail block, never edits existing rules):
  `.game-stage, .game-canvas-wrap, .game-hud, .game-controls, .game-pad, .game-hint, .game-note` — layout/border/radius/spacing from `--surface/--line/--s1/--s2` only; canvas `background: var(--raised); border: 1px solid var(--line); border-radius: 4px; aspect-ratio: 16/10; width: 100%`.
- Expected CSS delta: **≤3KB uncompressed** (part of the 60KB JS+CSS budget). Zero new tokens, zero new breakpoints (reuse 980/700px), zero new keyframes (hit flash is canvas-drawn, killed by JS reduced-motion check — no CSS animation added).
- Canvas colors: NO CSS hex for entities; JS reads `getComputedStyle(document.documentElement)` token values at boot (`--ink --muted --accent --art-ink --art-core --line`) and maps star/asteroid/ship/particle fills to them. Guarantees dark-theme correctness for free.
- Copy: English editorial identity; verbs "Play / Pause / Restart / Mute" consistent with existing "Read / Clear search / Back to top" microcopy; no backend/multiplayer/accounts/sharing claims.

## 3) Page construction (DEV pastes; exact semantics)

**`/games/` index** (new `templates/games-index.html`, archive family):
```html
<div class="container archive-page">
  <header class="page-heading" data-od-id="games-heading">
    <p class="eyebrow">The arcade</p>
    <h1>Small games, built by hand<span class="accent-dot">.</span></h1>
    <p>Short browser games from the journal workshop. No accounts, no downloads — just play.</p>
  </header>
  <div id="article-list" class="archive-list">
    <article class="story" data-search-item>
      <div class="story-meta"><span class="topic-label" aria-hidden="true">Arcade</span><span>90-second run</span></div>
      <h3><a href="/games/star-harvest/">Star Harvest</a></h3>
      <p>Pilot a little ship, gather drifting stars and dodge the rocks. Chain quick pickups to grow your combo.</p>
      <div class="story-foot"><span><time datetime="2026-09-19">Sep 19, 2026</time><span aria-hidden="true"> · </span>2 min play</span><a class="story-arrow" href="/games/star-harvest/" aria-label="Play Star Harvest">↗</a></div>
    </article>
  </div>
  <aside class="callout game-note" data-od-id="games-more"><p><strong>More games coming.</strong> Star Harvest is the first arcade experiment — new small games will appear here as they ship.</p></aside>
</div>
```

**`/games/star-harvest/`** (new `templates/game.html`, standalone — bypasses ArticleMarkup):
```html
<div class="container">
  <p class="breadcrumbs"><a href="/games/">Arcade</a><span aria-hidden="true"> / </span><span>Star Harvest</span></p>
  <header class="page-heading" data-od-id="game-heading">
    <p class="eyebrow">Star Harvest</p>
    <h1>Gather stars. Dodge rocks<span class="accent-dot">.</span></h1>
    <p>A 90-second arcade run. Chain quick pickups to grow your combo — three hits ends the flight.</p>
  </header>
  <section class="game-stage" aria-labelledby="game-title">
    <h2 id="game-title" class="sr-only">Star Harvest game</h2>
    <div class="game-canvas-wrap">
      <canvas id="star-harvest" width="800" height="500" role="img" aria-label="Star Harvest playfield: pilot a ship, collect star sparks, avoid polygon asteroids"></canvas>
    </div>
    <dl class="game-hud" aria-label="Game status">
      <div><dt>Score</dt><dd data-hud="score">0</dd></div>
      <div><dt>Time</dt><dd data-hud="time">1:30</dd></div>
      <div><dt>Lives</dt><dd data-hud="lives">3</dd></div>
      <div><dt>Combo</dt><dd data-hud="combo">×1</dd></div>
      <div><dt>Best</dt><dd data-hud="best">0</dd></div>
    </dl>
    <p class="sr-only" role="status" data-game-status>Ready. Press Start or Enter to play.</p>
    <div class="game-controls">
      <button type="button" class="button" data-action="start">Start</button>
      <button type="button" class="button" data-action="pause" aria-pressed="false">Pause</button>
      <button type="button" class="button" data-action="restart">Restart</button>
      <button type="button" class="button" data-action="mute" aria-pressed="false">Mute</button>
    </div>
    <p class="game-hint" data-hint>Drag to steer on touch, or use arrow keys / WASD. P pauses, M mutes.</p>
    <div class="game-pad" data-pad hidden>
      <button type="button" data-dir="up" aria-label="Steer up">↑</button>
      <button type="button" data-dir="left" aria-label="Steer left">←</button>
      <button type="button" data-dir="down" aria-label="Steer down">↓</button>
      <button type="button" data-dir="right" aria-label="Steer right">→</button>
    </div>
  </section>
  <div class="about-layout">
    <aside><p class="eyebrow">How to play</p><p class="about-motto">Quick hands.<br />Calm nerves.</p></aside>
    <div class="article-body">
      <h2>How to play</h2>
      <p>Thrust with arrow keys or WASD, drag on touch. Collect star sparks for points — grab them less than 2.5 seconds apart to grow your combo. Polygon rocks cost a life; you get three. P or Esc pauses, Enter starts or restarts, M mutes the bleeps.</p>
      <h2>Restart</h2>
      <p>Every run lasts 90 seconds or until your three lives run out. Your best score stays in this browser. Press Restart (or Enter) any time for a fresh flight.</p>
      <h2>Devlog</h2>
      <p>$devlog — one paragraph from <code>content/games/star-harvest.json</code>: why a vanilla canvas game, what the combo teaches about risk, and what ships next.</p>
    </div>
  </div>
</div>
```
Rules locked: `role="img"` + `aria-label` on canvas ONLY; the single `role="status"` node is the ONLY live region (HUD `dd`s are plain text, never `aria-live`); all controls are native `<button type="button">` ≥44px; D-pad `hidden` unless coarse pointer (CSS `@media (pointer: coarse)` reveals — no JS sniff); hint hides after first drag.

## 4) Dark + reduced-motion + responsive / a11y / weight

- **Dark:** zero extra work — HUD/controls/canvas-wrap use `--surface/--raised/--ink/--muted/--line`; canvas entities sampled from computed tokens at boot. DEV verifies HUD text AA in both themes (ink-on-raised, muted-on-surface) and star-vs-asteroid ≥3:1 by pixel sample (shape redundancy already covers color-blindness: spark vs polygon).
- **Reduced-motion:** JS `matchMedia('(prefers-reduced-motion: reduce)')` kills screen shake, hit flash, particles, invulnerability blink at the source; substitutes static ship outline + status text. CSS global guard (`site.css:251`) already kills transitions; game CSS adds NO animation. QA tests both settings (§6).
- **Responsive:** HUD `dl` grid 5 → 2 cols at 700px; `.game-stage` single column; canvas `width:100%; height:auto`; D-pad only on coarse pointers; mobile pause button stays ≥44px in thumb reach (inside `.game-controls`, first row). 360/768/1240px checks.
- **A11y:** skip link + single H1 + heading order preserved; canvas never focusable-required (buttons cover all actions); `:focus-visible` inherits site rule; timer/score/combo excluded from live region; 0:10 + end announced once; keyboard-only + touch-only full loops required; contrast AA on real pairs.
- **Weight/perf:** DOM shell ≈2KB; game CSS ≤3KB; JS+CSS ≤60KB uncompressed, page ≤150KB first load; RAF + capped delta + pooled particles; 60fps mid-laptop (DEV measures and reports — nothing pre-claimed here).

## 5) SEC / QA notes

- SEC: same-origin single script + single stylesheet, hashed filenames, no imports, no CDN, no `fetch`/XHR/WebSocket, no query handling; localStorage key `mmw.star-harvest.best.v1` integer-only (clamp + `textContent` render, never `innerHTML`); JSON content fields validated server-side in `build.py` (length caps + `http`/backslash rejection per family pattern); no secrets, no external URLs. No new SEC surface beyond the established static-page pattern → **no SEC pre-gate required**, standard SEC diff review still applies at PR.
- QA: full pytest green incl `tests/test_games_arcade.py`; zero console errors; zero external requests (network log empty except document + same-origin hashed assets); `/games/` 200 lists game + more-coming note; game page 200 renders canvas + how-to + HUD + restart + devlog; pause/resume both inputs; reduced-motion kills shake/flash/particles but stays playable; HUD contrast light+dark.

## 6) Acceptance criteria (DEV gate — all must pass)

- [ ] `/games/` 200: page-heading + ONE archive-family card linking `/games/star-harvest/` + "More games coming" `.callout`; SEO title/description present.
- [ ] Game page 200: breadcrumbs + heading + `canvas#star-harvest[role=img][aria-label]` + HUD `dl` (Score/Time/Lives/Combo/Best) + 4 native `.button`s (Start/Pause/Restart/Mute) + hint + how-to + restart + devlog paragraphs.
- [ ] Keyboard-only full loop: Enter start → Arrows/WASD play → P/Esc pause/resume → Enter restart; all buttons reachable, `:focus-visible` visible everywhere.
- [ ] Touch-only full loop: tap Start → drag-to-steer (hint hides) → tap pause (≥44px) → tap restart; coarse-pointer D-pad operable as fallback.
- [ ] Combo: pickups <2.5s apart grow multiplier; gap-timeout or hit resets; combo `dd` tabular, never announced.
- [ ] Timer: `1:30 → 0:00` `mm:ss`; run ends at 0:00 or 0 lives; 0:10 + end announced once via the single `role=status` node.
- [ ] Lives/invulnerability: 3 lives, brief invulnerability + flash; reduced-motion replaces with outline + status text.
- [ ] Best: namespaced integer-only localStorage, survives reload, renders as text, never sent anywhere.
- [ ] Reduced-motion: shake/flash/particles/blink all off; game stays playable; CSS adds no animation.
- [ ] Contrast: HUD text AA light+dark on real pairs; star-vs-asteroid ≥3:1 sampled both themes + shape redundancy (spark vs polygon).
- [ ] Live regions: exactly ONE `role=status` (state only); zero `aria-live` on score/time/combo.
- [ ] Targets: every button ≥44px; page scroll never hijacked (`touch-action: pan-y`; preventDefault only when game focused).
- [ ] Weight/perf: JS+CSS ≤60KB uncompressed, page ≤150KB first load, 60fps mid-laptop (DEV reports measured numbers).
- [ ] Isolation: zero console errors; zero external requests; no AI art (procedural canvas shapes only); no backend/multiplayer/accounts.
- [ ] Regression: full pytest green incl `tests/test_games_arcade.py`; masthead/nav/footer/feeds/JSON-LD byte-identical outside `/games/*`.
- [ ] Scope guard: any change (levels/boss/power-ups, WebGL, audio assets, new nav item, new tokens, footer rework) re-triggers design review per the mandatory rule.

**Clearance:** Design PASS for the `/games/` index + `/games/star-harvest/` construction above (MAC-649 family reuse + Star Harvest delta: combo HUD, star-vs-asteroid palette with shape redundancy, 90s timer, drag-to-steer + coarse-pointer D-pad). DEV is cleared to implement exactly this after GitHub preflight. No code beyond this brief from DESIGN; DEV owns `content/games/star-harvest.json`, `templates/games-index.html` + `game.html`, `assets/games/star-harvest.js + .css`, `scripts/build.py` routes (bypass ArticleMarkup; hashed assets), `content/buildlog/games-arcade-star-harvest`, `tests/test_games_arcade.py`. No SEC concern introduced — no SEC pre-gate required.
