# MAC-649 — Star Drift arcade page family (`/games/` + game page): OpenDesign assessment (Design Agent ownership)

**Date:** 2026-09-19 · **Author:** UX & Frontend Designer (Design Agent) · **Status:** PASS — DEV cleared to implement after GitHub preflight
**Refs:** OpenDesign `https://github.com/nexu-io/open-design` (brief → direction → artifact → handoff loop; reuse-the-system contract: semantic tokens only, native semantics, `:focus-visible` everywhere, `prefers-reduced-motion`, AA on real pairs). Inspected `templates/base.html` (masthead/footer chrome), `templates/archive.html` (card-grid precedent), `templates/card.html`, `templates/home.html`, `assets/site.css` (tokens, breakpoints 980px/700px, reduced-motion guard, `.button`/`.text-link` targets). Prior assessments `DESIGN_BRIEF_MAC-484.md` (additive-placement precedent) + `DESIGN_BRIEF_MAC-80.md` (asset/token discipline).
**Scope:** NEW capability — no `/games/` route, game template, canvas, HUD, or game JS exists (`grep games|arcade|canvas` = zero hits outside this brief). Full re-evaluation per mandatory rule. Routine-content rule does NOT apply.

## 1) Evaluation: current vs proposed (decision per row)

| # | Current experience | Proposal (MAC-649) | Design verdict |
|---|---|---|---|
| 1 | No arcade index. Closest precedent: `archive.html` — `.container` > `.page-heading` + `.archive-list` 2-col card grid → 1-col mobile. | `/games/` index: card grid of games (title, one-line pitch, Play link) reusing the archive card idiom. | **Approve with refinement.** Reuse `.page-heading` + archive grid rhythm verbatim; new additive `.game-grid` / `.game-card` classes only where the story-card parts (topic label, dateline, reading time, arrow) do not apply. One game (Star Drift) ships first — grid must read correctly with a single card and scale to N cards with zero markup change. |
| 2 | No game page type. Closest precedents: `post.html` reading layout, `about.html` page-heading + body. | Per-game page: how-to, canvas + HUD + status line, restart/pause/mute buttons, devlog paragraph. Must reuse `base.html` chrome. | **Approve with refinement (fixed section order).** `.container` > breadcrumbs (Back to Games) > `header.page-heading` (eyebrow "Arcade", H1 game title, one-line standfirst) > `section.how-to` (controls list) > `section.game-stage` (HUD + canvas frame + controls + status line) > `section.devlog` (one paragraph, `.article-body` rhythm). Game is the terminal interactive element before the devlog so keyboard/screen-reader flow is: orient → learn → play → context. No redesign of masthead/footer/search/theme toggle. |
| 3 | No canvas/JS interaction anywhere (static article site). | `<canvas>` game viewport + HUD (score/lives/time) + three buttons + `aria-live` status line, small deferred per-game script. | **Approve with refinement.** Canvas is `role="img"` + `aria-label` (never `aria-live` — game-loop chatter); the separate status `<p role="status">` carries concise state changes only (ready / paused / game over + score). HUD values are mirrored as text in the DOM (screen-reader/keyboard users never depend on pixels). Pause on `visibilitychange`/`blur`; keyboard operable without pointer. |
| 4 | Masthead nav: Home / Journal / Build Log / About (`base.html` lines 57–62). No Games entry. | Add Games link to masthead + footer. | **Approve with refinement (exact placement).** Masthead: append `<a href="/games/">Games</a>` AFTER About (no reordering of existing items; existing `$*_current` / `aria-current` pattern extended, not reworked). Footer nav: append Games link after Build log. Five masthead items fit the existing 700px wrap pattern (nav `order:3` full-width row); no new breakpoint. |
| 5 | Dark-first aesthetic via semantic tokens (`--bg/--surface/--raised/--ink/--muted/--line/--accent/--accent-ink`), global reduced-motion kill-switch (`site.css:251`). | Dark-theme + reduced-motion treatment for game. | **Approve as specified in §5.** Frame/HUD/controls use semantic vars only (theme flips free). Canvas palette: two fixed pairs keyed to `data-theme`, values sampled from current tokens — documented in JS comments, zero new CSS hex. Reduced-motion: `matchMedia` gate + CSS guard kills shake/particles/starfield drift/decorative pulse; game still fully playable. |

No redesign of surrounding experience: masthead layout, search, theme toggle, footer bottom, feeds, sitemap, JSON-LD, OG defaults unchanged (game pages get standard title/description/canonical/OG like any page).

## 2) Token / class reuse plan (`assets/site.css`, additive only)

- Permitted vars only: `--bg --surface --raised --ink --muted --line --accent --accent-ink` + `--sans/--serif/--mono` + `--s1--s3` + `--reading`. Zero new hex / `rgb(` / `@import` / font / `!important` in CSS (static `grep` gate). Expected CSS delta ~+120 lines, all under a `/* Arcade (MAC-649) … Additive only */` banner.
- Additive classes (DEV pastes; existing selectors untouched):
  - `.game-grid { display:grid; grid-template-columns:1fr 1fr; gap:var(--s2); }` (mirrors `.archive-list`; collapses to 1fr at 700px in the existing media query).
  - `.game-card { background:var(--raised); border:1px solid var(--line); border-radius:4px; padding:var(--s2); display:flex; flex-direction:column; gap:var(--s1); }` + `.game-card h2` (serif, ~25px) + `.game-card p` (muted 14px) + `.game-card .button { margin-top:auto; align-self:flex-start; }`.
  - `.game-stage { background:var(--surface); border:1px solid var(--line); border-radius:4px; padding:var(--s2); display:grid; gap:var(--s2); }`.
  - `.game-hud { display:flex; flex-wrap:wrap; gap:var(--s1) var(--s3); list-style:none; margin:0; padding:0; font:11px/1.6 var(--mono); letter-spacing:.1em; text-transform:uppercase; color:var(--muted); }` + `.game-hud b { display:block; font-family:var(--serif); font-size:24px; letter-spacing:-.02em; color:var(--ink); font-variant-numeric:tabular-nums; }`.
  - `.game-frame { border:1px solid var(--line); border-radius:4px; background:var(--raised); overflow:hidden; }` + `.game-frame canvas { display:block; width:100%; height:auto; aspect-ratio:16/10; touch-action:none; }`.
  - `.game-controls { display:flex; flex-wrap:wrap; gap:var(--s1); }` + `.game-btn { min-width:44px; min-height:44px; …reuse .button secondary idiom: transparent bg, `border:1px solid var(--line)`, `color:var(--ink)`; primary Restart uses `.button` verbatim }`.
  - `.game-status { font:13px/1.7 var(--sans); color:var(--muted); min-height:44px; display:flex; align-items:center; }` (`role="status"`, `aria-live="polite"`).
  - `.how-to kbd { font:12px/1.6 var(--mono); background:var(--raised); border:1px solid var(--line); border-radius:3px; padding:2px 6px; }`.
- Touch: every button/link target ≥ 44×44px (`.button` 48px / nav 44px precedent already compliant; new `.game-btn` explicitly 44px min both axes).
- `:focus-visible`: inherited global rule (`site.css:31`) — no override; canvas wrapper gets visible outline when `tabindex="0"` canvas is focused.

## 3) Page construction (DEV pastes structure, fills `$slots`)

`/games/` index (`templates/games.html`): `.container` > `header.page-heading` (eyebrow "Arcade", H1 "Games.", lede one line) + `<div class="game-grid">` of `.game-card` articles (each: H2 linked title, one-line pitch, `<a class="button" href="/games/star-drift/">Play Star Drift →</a>`). Single H1; cards are `<article>` with headings (not list-items without headings).

Game page (`templates/game.html`, first instance Star Drift): breadcrumbs (`<nav class="breadcrumbs" aria-label="Breadcrumb">` — reuse post pattern: Games / Star Drift) + `header.page-heading` + `<section class="how-to" aria-labelledby="howto">` (H2 "How to play", `<ul>` of 3–4 items with `<kbd>` for ←/→/Space/P/M) + `<section class="game-stage" aria-labelledby="play">`:
```html
<section class="game-stage" aria-labelledby="play-heading">
  <h2 id="play-heading">Play Star Drift</h2>
  <ul class="game-hud" aria-label="Scoreboard">
    <li>Score <b data-hud="score">0</b></li>
    <li>Lives <b data-hud="lives">3</b></li>
    <li>Time <b data-hud="time">0:00</b></li>
  </ul>
  <div class="game-frame">
    <canvas id="star-drift" width="800" height="500" role="img" tabindex="0"
      aria-label="Star Drift playfield: steer the ship with arrow keys, dodge debris, survive as long as you can."></canvas>
  </div>
  <div class="game-controls">
    <button type="button" class="button" data-game="restart">Restart</button>
    <button type="button" class="game-btn" data-game="pause" aria-pressed="false">Pause</button>
    <button type="button" class="game-btn" data-game="mute" aria-pressed="false">Mute</button>
  </div>
  <p class="game-status" role="status" aria-live="polite" data-game="status">Press Play or focus the playfield to start.</p>
  <noscript><p>Star Drift needs JavaScript to play. The controls are arrow keys to steer, Space to brake, P to pause, M to mute.</p></noscript>
</section>
<section class="devlog" aria-labelledby="devlog-heading">
  <h2 id="devlog-heading">Devlog</h2>
  <p><!-- one English editorial paragraph: what this first ship taught us --></p>
</section>
```
Canvas internal resolution fixed (`800×500`); CSS scales it (`width:100%; height:auto`) — zero layout shift, DPR capped at 2 in JS. Status line is the ONLY live region; HUD `<b>` values are plain text mirrors (no live announcements per keystroke/score tick — announce only ready/paused/resumed/game-over + final score).

## 4) Dark-theme + reduced-motion treatment

- Dark theme: all chrome/HUD/frame/controls inherit `[data-theme]` token flips — no per-theme CSS. Canvas render palette reads `document.documentElement.dataset.theme` once per frame-batch (or on toggle): light = ink `#222d27` ship on raised `#ffffff` field with muted debris; dark = ink `#e9eee3` on raised `#252e28`. Values equal existing tokens (comment cites `site.css:3-19`); no new hues, no neon outside the `--accent` family for the ship accent.
- Reduced motion (both layers, either suffices alone): CSS global guard already zeroes transitions/animations; JS additionally gates ALL of: screen shake, particle bursts, starfield drift/parallax, HUD pulse, canvas fade trails — via `matchMedia('(prefers-reduced-motion: reduce)')` checked at boot + change listener. Reduced-mode game: instant state changes, static starfield, debris moves only as gameplay (no decorative drift), no shake offset. No separate toggle required — OS setting is the switch; document it in how-to ("Motion: follows your system's reduce-motion setting").

## 5) Responsive / a11y / weight plan

- 360px: single-column grid; HUD wraps 2+1; controls wrap full-width buttons (each ≥44px, labels never truncated); canvas `aspect-ratio:16/10` letterboxes via CSS width — no horizontal scroll. 768px: 2-col game grid holds; game-stage single column (canvas max `--reading`-ish width, centered). 1240px: index grid max 2 cols (not 3 — one ship today, editorial restraint); game page `.container` standard width, stage capped at ~800px canvas + full-width HUD row.
- Semantics/keyboard: single H1; H2 order How to play → Play → Devlog; canvas `tabindex="0"` + visible `:focus-visible`; full keyboard map (←/→ or A/D steer, Space brake, P pause, M mute, R restart) listed in how-to AND announced via `aria-describedby` on canvas pointing at the how-to list id; focus never trapped; `Escape`/`blur` pauses. Buttons are native `<button>` with `aria-pressed` on pause/mute.
- Contrast: HUD labels muted-on-surface + values ink-on-surface reuse existing AA-passing pairs (same as `.story-meta`/`.metrics-label`); status muted 13px on surface — same pair as body-muted prose. Canvas is game art (WCAG non-text contrast: ship vs field ≥ 3:1 in both palettes — DEV verifies by sampling).
- Weight: one deferred per-game script (`star-drift.js`, budget ≤ 15KB unminified, no libs, no audio assets — WebAudio bleeps synthesized, off by default behind Mute toggle state); index adds ~1KB HTML; no new fonts/images/requests; static hosting holds (two new static routes, no backend, no query handling).
- Print: `.game-stage` hidden in print (game is interactive, not content); devlog + how-to print normally (additive `@media print` line).

## 6) SEC / QA notes for the pinned-SHA reviews

- SEC: no secrets/keys/env in markup, JS, or comments; no external URLs (AdSense in `base.html` stays untouched — game templates add zero third-party requests); canvas uses no external images; script uses no `innerHTML` with game data (textContent only for HUD/status), no `eval`, no URL-param parsing; mute/pause state in memory only (localStorage optional — if used, namespaced key, no PII). Flag SEC only if scope adds network/storage beyond this.
- QA: verify `/games/` + `/games/star-drift/` 200 at 360/768/1240px light+dark (screenshots); keyboard-only full play session; screen-reader pass (status announces pause/game-over, HUD not chatty); reduced-motion OS setting kills shake/particles (visual check); buttons ≥44px (measure); HTML valid (one H1, labelled sections, canvas labelled); internal-link crawl gains 2 routes, zero new 404s; build green + buildlog-presence gate green (production change ships its entry in same PR per MAC-64).

## 7) Acceptance criteria (DEV gate)

- [ ] `/games/` index renders page-heading + card grid (1 card today, N-ready) with working Play link; reuses `base.html` chrome with Games `aria-current` on index.
- [ ] `/games/star-drift/` renders breadcrumbs → heading → how-to (`<kbd>` controls) → game-stage (HUD + labelled canvas + 3 buttons + `role=status` line + `<noscript>`) → one-paragraph devlog; single H1; heading order intact.
- [ ] Tokens: CSS uses semantic vars only (grep gate: no `#[0-9a-fA-F]{3,6}`/`rgb(`/`@import`/`http`/`!important` in added CSS); canvas JS palettes document token source.
- [ ] Targets: all interactive elements ≥44×44px; `:focus-visible` visible on canvas + buttons in both themes.
- [ ] Status line `role="status"` + `aria-live="polite"`, announces ready/paused/game-over only; canvas `role="img"` + `aria-label`, `tabindex="0"`.
- [ ] Reduced-motion: shake/particles/drift/decorative pulse all gated behind `matchMedia`; verified with OS setting on.
- [ ] Nav: Games appended after About (masthead) + after Build log (footer); mobile 360px no overflow; existing items byte-identical order.
- [ ] Weight/perf: game JS ≤15KB, deferred, DPR ≤ 2, pause on hidden tab; print hides `.game-stage`.
- [ ] English editorial copy throughout; no secrets; no new third-party requests.

**Clearance:** Design PASS for the `/games/` index + game-page family exactly as specified above. DEV is cleared to implement after GitHub preflight. Suggested commit scope: `DESIGN_BRIEF_MAC-649.md` (this file) + `templates/games.html` + `templates/game.html` + `assets/site.css` (additive arcade block) + per-game JS + `scripts/build.py` routes + Build Log entry (same PR, MAC-64) — DEV owns commits/merges. Any scope change (leaderboards, accounts, audio assets, additional games beyond the family template, new nav pattern, new tokens) re-triggers design review per the mandatory rule. No SEC pre-gate required (no security concern introduced).
