# MAC-107 spike report — HyperFrames pilot render

Parent MAC-103. Throwaway spike on branch `spike/hyperframes-pilot`. NO PR to main, NO merge, NO deploy.

## 1. Preflight (2026-09-06)

- Remote: `origin https://github.com/serjaum/machinemadeworlds.git` (fetch+push).
- Auth: `gh auth status` → logged in as `serjaum`; `git ls-remote origin HEAD` OK.
- NOTE: repo visibility is **PUBLIC** (`gh repo view` → `isPrivate:false`), not private as the
  issue text assumes. Push access verified by the spike-branch push below.
- Branch: `git fetch origin && git checkout -B spike/hyperframes-pilot origin/main` (base `c71faa4`).

## 2. Install (per HyperFrames docs: Node + headless Chrome/Puppeteer + FFmpeg)

All timings UTC 2026-09-06, single heartbeat, wall-clock:

| Step | Result | Time |
|---|---|---|
| `node --version` / `npm --version` | v22.23.2 / 12.0.2 (meets `>=22`) | 0 min (preinstalled) |
| `ffmpeg -version` | 9.0-full_build-www.gyan.dev (meets requirement) | 0 min (preinstalled) |
| `npx --yes hyperframes --version` | **0.8.30** (latest at run time; fetched, ~35 s first npx) | ~1 min |
| `npx hyperframes doctor` | Node/CPU/RAM/Disk/FFmpeg/FFprobe PASS; Chrome missing → hint `browser ensure`; whisper-cpp/TTS/BGM optional-missing (not needed for muted MP4); Docker missing (not needed) | <1 min |
| `npx hyperframes browser ensure` | chrome-headless-shell `152.0.7977.30` resolved from cache | ~3 s |
| `hyperframes init -e blank` (learning scaffold, deleted after) | OK | <1 min |
| **Total install time** | | **~2–3 min, zero manual installs** |

## 3. Composition

- Path: `spike/hyperframes-pilot/index.html` (+ `hyperframes.json`, `package.json` pinned to
  `hyperframes@0.8.30`, `meta.json`).
- 20.0 s, 1920×1080, 30 fps (600 frames), muted, H.264.
- Content: pipeline explainer reusing site tokens from `assets/site.css` (light theme:
  `--bg #f7f8f4`, `--surface #eef1e9`, `--ink #222d27`, `--muted #5c685e`,
  `--line #d6ddd1`, `--accent #285640`, `--art #e1e9d9`) and site wording
  (Draft → DEV → SEC → QA → Publish; `↩ BLOCK → fix (abc1234) → re-review (def5678)` loop row;
  "ArticleMarkup gate", "exact SHA", `machinemadeworlds.com` footer).
- Loopability: title card 0–3 s is pixel-identical to tail card 18–20 s (same markup/text), so
  the loop point is seamless by construction (same palette/layout; first/tail frames match).
- Animation: single paused GSAP timeline on `window.__timelines["pipeline"]`, absolute positions
  only, no `Date.now()`/`Math.random()`/network fetch. GSAP via the same jsdelivr CDN pin
  (`3.14.2`) the `blank` template uses.
- Gates: `lint` 0 errors 0 warnings (after adding one missing stable `id`);
  `check` PASS — lint 0/0, runtime 0/0, layout 0 issues / 9 samples, motion 0, contrast 35/35 AA.

## 4. Measurements

- Render 1: **31.4 s** (CLI-reported) for 20.0 s video → ~0.64× realtime at 1920×1080/30fps,
  4 workers, `beginframe` capture, no audio.
- Render 2 (reproducibility): **32.4 s**.
- Artifact: `spike/hyperframes-pilot/renders/pipeline-explainer.mp4`
  - bytes: **1,896,024**; bytes/sec: **94,801.2** (÷20 s); bitrate ~744–759 kbit/s.
  - codec: H.264 High, `yuv420p`, 1920×1080, 30/1 fps, 600 frames, 20.000 s exactly.
  - sha256 (both renders): `5edd40d27bcbb1b2d662f6dce1dff8c7521dd8f49f8f561e00c1dbb61ac5c67c`
  - **Reproducibility: BYTE-IDENTICAL across two renders** (same size + same sha256).
- Playback check (format-level, no live browser run — timeboxed):
  `ffprobe` confirms H.264 High / yuv420p / 30 fps (universally playable:
  Chrome/Firefox/Safari); `ffmpeg -f null` full decode OK. No browser playback run performed.
- Earlier pre-loop-fix build (different tail text) also reproduced byte-identically
  (`cee71a3b…`, 1,862,238 B), confirming determinism is not input-luck.

## 5. Agent-difficulty notes / skill-coverage gaps

- What worked: `doctor` hint was exact (`browser ensure`); `lint` warning gave the fix
  (stable `id`); `check` one-shot gate is excellent; `render -o` just works; AGENTS.md in the
  scaffolded project carries the composition rules (clips, paused timelines, no wall-clock).
- Confusing parts:
  1. `init` wrote to a `./hf-blank-demo` relative path while an absolute `/tmp/...` target
     silently went elsewhere under git-bash on Windows — use repo-relative paths.
  2. `render --help` is huge; the 3 flags an agent needs (`-o`, `-f`, `-q`) are buried.
  3. `tl.call()` position args for the gate-word swap are seek-fragile (verified only at
     full-render level, not per-frame seek); prefer `tl.set(..., position)` for text swaps.
  4. FFmpeg 9 removed `-vsync` (use `-fps_mode passthrough`) — unrelated to HyperFrames but
     bit during frame-extraction verification.
- Skill gaps: no checked-in skill in this repo; the CLI's `AGENTS.md`/`docs` topics
  (`data-attributes`, `gsap`, `rendering`, `troubleshooting`) covered everything used here.
  Missing: a "loopable composition" pattern (match head/tail cards) and a
  "verify determinism" recipe (render twice → `sha256sum`).

## 6. Adoption-impact analysis (NO implementation — analysis only)

1. **ArticleMarkup `<video>` allowlist + attrs needed** (`scripts/build.py:28-48` today: no
   `video`/`source`, `src` restricted to `/assets/`, no boolean media attrs).
   Minimal proposal for a follow-up Design + SEC review: allowlist tags `video` (+`source`
   iff multi-codec is wanted; single MP4 needs only `video src`); allowlist attrs
   `src poster preload` + boolean `muted loop playsinline controls` (booleans need a parser
   change — today any value passes the attr-name check, but valueless attrs must be confirmed
   against `HTMLParser` handling); keep `href/src` scheme rules and extend the
   `/assets/`-prefix rule to video `src`/`poster`; require `aria-label` on non-decorative video
   (already allowlisted); gate rule: `video` MUST carry `muted loop playsinline` and MUST NOT
   carry `autoplay` without `muted` (autoplay-with-sound is blocked by browsers anyway).
   No implementation done here — needs Design assessment + SEC gate review first.
2. **Media weight-budget proposal (per-page video cap):** this spike's 20 s 1080p30 explainer
   costs **~1.9 MB (~95 kB/s)**. Proposal: cap **1 video per page, ≤2 MB per file, ≤30 s**,
   prefer 720p for inline explainers (~half the bytes), always `preload="metadata"` +
   poster frame, never autoplay with sound. A page with one such video stays lighter than
   most image carousels; two+ videos per page should require explicit weight sign-off.
3. **Hosting notes (static Hostinger, no live test):** deploy path is `dist/` → `public_html`
   via FTP mirror (`scripts/deploy.sh`); Apache serves `.mp4` as `video/mp4` via default MIME
   maps and supports HTTP Range requests (byte-serving core) so `<video>` seeking works with
   no app server. `dist/.htaccess` today has **no MP4-specific rules** — a follow-up should add
   long-cache `Cache-Control: public, max-age=31536000, immutable` for hashed video filenames
   (mirroring the existing hashed css/js/svg rule) and confirm `Accept-Ranges` post-deploy
   with `curl -I -r 0-1`. No live test performed per spike contract. Videos must live under
   `/assets/` to satisfy the existing `src` rule and must be mirrored into `dist/assets/`.
4. **CI reproducibility verdict:** **REPRODUCIBLE — render twice → byte-identical** on this
   machine (same sha256, same byte count). Determinism inputs: pinned `hyperframes@0.8.30`,
   pinned GSAP CDN, absolute-timeline composition, no wall-clock/random. CI caveats (not
   tested): font fetching (check fetched Google Fonts at render time — vendor fonts for
   hermetic CI), `chrome-headless-shell` version pin, worker-count independence (4 workers
   here; 1-worker re-run recommended before claiming worker-invariance).

## Verdict: VALIDATED

- What worked: toolchain installed in ~2–3 min with zero manual steps; `check` fully green;
  20 s muted loopable H.264 rendered in ~31–32 s; **two renders byte-identical**
  (`5edd40d2…`, 1,896,024 B); site tokens/wording reused verbatim; no secrets touched.
- What didn't: live browser playback check (format-level only); live Hostinger range/cache
  check (docs-level only, per contract); per-frame seek-safety of `tl.call` text swaps.
- Surprises: repo is PUBLIC, not private (issue text assumes private); determinism held even
  across a content edit (both builds reproduced exactly); `browser ensure` was a 3 s cache hit.
- Recommendation: adopt HyperFrames for pipeline-explainer style motion; next step is a
  Design assessment for the ArticleMarkup `<video>` gate change + weight budget above
  (MAC-103), with SEC owning the `build.py` diff. No main-branch impact from this spike:
  branch-only, `main` untouched, no PR, no merge, no deploy.
