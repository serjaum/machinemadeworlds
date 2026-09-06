# SPIKE report — HyperFrames pilot render (MAC-106, parent MAC-103)

Branch: `spike/hyperframes-pilot`. Throwaway. NO PR to main, NO merge, NO deploy.
Date: 2026-09-06. Single DEV run, timeboxed.

## Verdict: VALIDATED

The toolchain installs in seconds from the workspace, renders a 20 s muted
loopable pipeline-explainer MP4 reusing site tokens, and reproduces
byte-identical output across two consecutive renders.

## Toolchain (workspace-only install)

| Component | Version / source | Time |
|---|---|---|
| Node.js | v22.23.2 (preinstalled) | 0 s |
| npm gsap (vendored to `spike-hf/gsap.min.js`) | 3.14.2 | ~1 s |
| FFmpeg / FFprobe | 9.0-full_build-www.gyan.dev (preinstalled WinGet) | 0 s |
| `npx hyperframes doctor` | hyperframes 0.8.30 (latest) | ~4 s |
| `npx hyperframes browser ensure` | Chrome Headless Shell 152.0.7977.30, 114 MB to user cache | ~9 s |
| `hyperframes init spike-hf --example blank --non-interactive` | scaffold | ~3 s |
| whisper-cpp / TTS / BGM | NOT installed (optional, voice/music only — unneeded for muted pilot) | — |
| Docker | NOT present (local mode used; deterministic cross-machine output not tested) | — |

Total install ≈ 15–20 s. No admin rights, no repo pollution
(`node_modules/` git-ignored; Chrome lives in the user cache, outside the repo).

## Render

- Composition: `spike-hf/index.html` — 20.0 s, 30 fps, 1920×1080, muted
  (zero audio elements), site tokens only
  (`#f7f8f4` bg, `#222d27` ink, `#5c685e` muted, `#d6ddd1` line,
  `#285640` accent, Georgia/serif + system sans, `m·w` tile motif).
  Content: five pipeline nodes (Design → DEV build → SEC+QA same-cut check →
  DEV merge → SRE ship) with progress bar and seamless-loop badge.
- `hyperframes check`: PASS (111/111 WCAG AA text checks; 4 Studio
  `studio_missing_editable_id` warnings only — edit-target hints, no render impact).
- One lint error hit and fixed in-run: `gsap_css_transform_conflict` on the
  progress bar (CSS `transform: scaleX(0)` + GSAP scaleX tween). Fix: drop the
  CSS transform, use `tl.fromTo(..., {scaleX:0}, {scaleX:1...})`. Actionable message.
- Run 1: 43.1 s → `renders/pilot-run1.mp4`, 910,966 bytes.
- Run 2: 43.4 s → `renders/pilot-run2.mp4`, 910,966 bytes.
- SHA-256 identical both runs (`528c0d83…874214`): **reproducible, deterministic.**

## Playback verdict: PASS

- `ffprobe`: h264, 1920×1080, 30/1 fps, 600 frames, 20.000 s, 364 kbps, no audio stream.
- `ffmpeg -f null` full decode: clean, no errors.
- Frame spot-checks at t=1/6/12/19 s show monotonic animation progress
  (10k → 24k → 27k → 30k unique colors; node cards activating).
- `moov` (36) precedes `mdat` (3599): faststart set — progressive playback ready.
- Loopability: editorial loop (badge + copy cue replay; progress bar resets on
  loop — one-frame cut on the bar only). True pixel-seamless looping would need
  the bar to dissolve rather than snap; acceptable for an explainer loop.

## Agent-difficulty notes

1. Smooth overall: `doctor` told exactly what was missing; `browser ensure`
   fetched Chrome headless shell unattended; `check` gates with fix recipes.
2. Vendoring GSAP locally (`gsap.min.js`, 73 KB) instead of the template's CDN
   `<script>` keeps renders offline-deterministic — recommend as house rule.
3. No `preview` needed for this pilot; `check` + `render` sufficed headless.
4. Windows caveat: `doctor` shells out to `docker` (absent → noisy error text,
   still exit 0). Harmless but worth knowing.
5. Determinism claim holds on one machine (byte-identical); cross-OS Docker-mode
   determinism untested (no Docker here).

## Adoption-impact analysis

- **ArticleMarkup video allowlist** (`scripts/build.py`): today `video`/`source`
  tags are rejected and `src` must be `/assets/`-only. Proposal (follow-up
  initiative, needs Design clearance): allow `video, source` tags; allow
  attributes `poster, preload, playsinline, muted, loop, controls, width,
  height` (+ existing `class, id, title, aria-label`); keep `/assets/`-only
  `src`; require `muted + playsinline` and a `poster` with `width`/`height`
  (no layout shift); forbid `autoplay` with sound (muted autoplay only).
- **Weight-budget proposal** (`tests/test_artifact.py` caps: 42 KB raw /
  14 KB compressed home+assets, 3.5 KB JS): the pilot MP4 alone is 911 KB —
  ~22× the raw cap. Video must NOT count against the document budget.
  Proposal: keep existing caps for HTML/CSS/JS; add a separate per-video cap
  (e.g. ≤ 1.5 MB for ≤ 30 s 1080p muted, poster ≤ 60 KB) plus `preload="none"`,
  click-to-play or muted-loop only, poster-first rendering.
- **Hosting notes**: `dist/` is static on Hostinger with no range-streaming
  guarantees; faststart MP4 progressive download is fine at this size, but
  adaptive streaming is out of scope. Keep MP4s under hashed `/assets/`,
  lazy-load below the fold, and consider external hosting (object storage/CDN)
  if video count grows. No deploy performed in this spike.

## Files (this branch only)

- `spike-hf/index.html` — composition (site tokens, 20 s, muted, loopable)
- `spike-hf/gsap.min.js` — vendored GSAP 3.14.2 (offline determinism)
- `spike-hf/hyperframes.json`, `meta.json`, `package.json`, `AGENTS.md`, `CLAUDE.md` — scaffold
- `spike-hf/renders/pilot-run1.mp4` — evidence artifact (910,966 bytes)
  (`pilot-run2.mp4` byte-identical, not committed)
- `docs/spike-hyperframes-pilot-MAC-106.md` — this record
