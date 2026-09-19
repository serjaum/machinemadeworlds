/* Star Drift (MAC-649 arcade family). No libraries, no assets, no network.
   Canvas palette is sampled from the site semantic tokens (site.css):
   light theme uses ink on raised, dark theme uses ink on raised.
   All HUD and status updates use textContent. Audio is WebAudio bleeps,
   created lazily on first user gesture; the Mute button toggles output. */
(() => {
  "use strict";
  const canvas = document.getElementById("star-drift");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const W = 800, H = 500;
  const hud = {
    score: document.querySelector('[data-hud="score"]'),
    lives: document.querySelector('[data-hud="lives"]'),
    time: document.querySelector('[data-hud="time"]')
  };
  const status = document.querySelector('[data-game="status"]');
  const restartBtn = document.querySelector('[data-game="restart"]');
  const pauseBtn = document.querySelector('[data-game="pause"]');
  const muteBtn = document.querySelector('[data-game="mute"]');

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  let reduced = reduceMotion.matches;
  if (typeof reduceMotion.addEventListener === "function") {
    reduceMotion.addEventListener("change", (event) => { reduced = event.matches; });
  }

  // Palette follows the active site theme; values mirror the CSS tokens.
  function palette() {
    const dark = document.documentElement.dataset.theme === "dark";
    return dark
      ? { field: "#252e28", ship: "#e9eee3", accent: "#b9d3a5", debris: "#aebcad" }
      : { field: "#ffffff", ship: "#222d27", accent: "#285640", debris: "#5c685e" };
  }

  const state = {
    mode: "ready", score: 0, lives: 3, ticks: 0,
    shipX: W / 2, vx: 0, braking: false, muted: false,
    debris: [], stars: [], particles: [], shake: 0
  };

  function resetStars() {
    state.stars = [];
    for (let i = 0; i < 70; i++) {
      state.stars.push({ x: Math.random() * W, y: Math.random() * H, s: Math.random() < 0.5 ? 1 : 2 });
    }
  }

  function reset() {
    state.mode = "running";
    state.score = 0; state.lives = 3; state.ticks = 0;
    state.shipX = W / 2; state.vx = 0; state.braking = false;
    state.debris = []; state.particles = []; state.shake = 0;
    resetStars();
    setStatus("Flying. Dodge the debris.");
    syncPause();
    paintHud();
  }

  function fmtTime(ticks) {
    const seconds = Math.floor(ticks / 60);
    return Math.floor(seconds / 60) + ":" + String(seconds % 60).padStart(2, "0");
  }

  function paintHud() {
    hud.score.textContent = String(state.score);
    hud.lives.textContent = String(state.lives);
    hud.time.textContent = fmtTime(state.ticks);
  }

  // The status line is the only live region; announce state changes only,
  // never per-tick score motion.
  function setStatus(text) {
    if (status.textContent !== text) status.textContent = text;
  }

  function syncPause() {
    const paused = state.mode === "paused";
    pauseBtn.textContent = paused ? "Resume" : "Pause";
    pauseBtn.setAttribute("aria-pressed", String(paused));
  }

  function togglePause() {
    if (state.mode === "running") {
      state.mode = "paused";
      setStatus("Paused.");
    } else if (state.mode === "paused") {
      state.mode = "running";
      setStatus("Flying. Dodge the debris.");
    } else {
      reset();
      return;
    }
    syncPause();
  }

  // Lazy audio: the context is created on the first gesture only.
  let audioCtx = null;
  function beep(freq) {
    if (state.muted) return;
    try {
      if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      if (audioCtx.state === "suspended") audioCtx.resume();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.frequency.value = freq;
      gain.gain.value = 0.04;
      osc.connect(gain); gain.connect(audioCtx.destination);
      osc.start(); osc.stop(audioCtx.currentTime + 0.08);
    } catch (_) { /* Audio stays silent when unavailable. */ }
  }

  function toggleMute() {
    state.muted = !state.muted;
    muteBtn.textContent = state.muted ? "Unmute" : "Mute";
    muteBtn.setAttribute("aria-pressed", String(state.muted));
  }

  const keys = Object.create(null);
  function isTyping(target) {
    return target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA");
  }

  window.addEventListener("keydown", (event) => {
    if (isTyping(event.target)) return;
    const key = event.key;
    if (key === "ArrowLeft" || key === "ArrowRight" || key === " ") event.preventDefault();
    if (key === "p" || key === "P") { togglePause(); return; }
    if (key === "m" || key === "M") { toggleMute(); return; }
    if (key === "r" || key === "R") { reset(); return; }
    if (key === "Escape" && state.mode === "running") { togglePause(); return; }
    keys[key.length === 1 ? key.toLowerCase() : key] = true;
    if (state.mode === "ready" && (key === "ArrowLeft" || key === "ArrowRight" || key === " " || key === "a" || key === "A" || key === "d" || key === "D")) {
      reset();
    }
  });
  window.addEventListener("keyup", (event) => {
    const key = event.key;
    keys[key.length === 1 ? key.toLowerCase() : key] = false;
  });
  canvas.addEventListener("focus", () => {
    if (state.mode === "ready") reset();
  });
  canvas.addEventListener("pointerdown", () => {
    canvas.focus();
    if (state.mode === "ready") reset();
  });

  restartBtn.addEventListener("click", reset);
  pauseBtn.addEventListener("click", togglePause);
  muteBtn.addEventListener("click", toggleMute);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden && state.mode === "running") togglePause();
  });
  window.addEventListener("blur", () => {
    if (state.mode === "running") togglePause();
  });

  function spawnDebris() {
    const speed = Math.min(2 + state.ticks / 3600, 5) * (state.braking ? 0.45 : 1);
    state.debris.push({
      x: 20 + Math.random() * (W - 40),
      y: -20, r: 8 + Math.random() * 14, v: speed + Math.random() * 1.5
    });
  }

  function burst(x, y, colors, count) {
    if (reduced) return;
    for (let i = 0; i < count; i++) {
      const angle = Math.random() * Math.PI * 2;
      state.particles.push({
        x, y, vx: Math.cos(angle) * (1 + Math.random() * 2),
        vy: Math.sin(angle) * (1 + Math.random() * 2),
        life: 24, color: colors[i % colors.length]
      });
    }
  }

  function step() {
    state.ticks++;
    if (state.ticks % 12 === 0) state.score += 1;
    const left = keys.ArrowLeft || keys.a, right = keys.ArrowRight || keys.d;
    state.braking = !!keys[" "];
    const accel = state.braking ? 0.25 : 0.6;
    if (left) state.vx -= accel;
    if (right) state.vx += accel;
    state.vx *= 0.96;
    state.shipX = Math.max(24, Math.min(W - 24, state.shipX + state.vx));
    if (state.ticks % 24 === 0) spawnDebris();
    const shipY = H - 60;
    for (let i = state.debris.length - 1; i >= 0; i--) {
      const d = state.debris[i];
      d.y += d.v;
      const hit = Math.abs(d.x - state.shipX) < d.r + 12 && Math.abs(d.y - shipY) < d.r + 12;
      if (hit) {
        state.debris.splice(i, 1);
        state.lives -= 1;
        const pal = palette();
        burst(state.shipX, shipY, [pal.accent, pal.debris], 14);
        if (!reduced) state.shake = 8;
        beep(140);
        paintHud();
        if (state.lives <= 0) {
          state.mode = "over";
          setStatus("Game over. Final score " + state.score + ". Press Restart to fly again.");
          syncPause();
          return;
        }
      } else if (d.y > H + 30) {
        state.debris.splice(i, 1);
      }
    }
    for (let i = state.particles.length - 1; i >= 0; i--) {
      const p = state.particles[i];
      p.x += p.vx; p.y += p.vy; p.life -= 1;
      if (p.life <= 0) state.particles.splice(i, 1);
    }
    if (state.shake > 0) state.shake -= 1;
    if (!reduced) {
      for (const s of state.stars) {
        s.y += 0.3;
        if (s.y > H) { s.y = 0; s.x = Math.random() * W; }
      }
    }
    if (state.ticks % 6 === 0) paintHud();
  }

  function draw() {
    // Internal resolution is fixed; CSS scales the element. Cap DPR at 2.
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    if (canvas.width !== Math.round(W * dpr) || canvas.height !== Math.round(H * dpr)) {
      canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const pal = palette();
    ctx.save();
    if (state.shake > 0) ctx.translate((Math.random() - 0.5) * state.shake, (Math.random() - 0.5) * state.shake);
    ctx.fillStyle = pal.field;
    ctx.fillRect(-12, -12, W + 24, H + 24);
    ctx.fillStyle = pal.debris;
    for (const s of state.stars) ctx.fillRect(s.x, s.y, s.s, s.s);
    ctx.fillStyle = pal.debris;
    for (const d of state.debris) {
      ctx.beginPath();
      ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2);
      ctx.fill();
    }
    for (const p of state.particles) {
      ctx.fillStyle = p.color;
      ctx.fillRect(p.x, p.y, 3, 3);
    }
    const shipY = H - 60;
    ctx.fillStyle = pal.ship;
    ctx.beginPath();
    ctx.moveTo(state.shipX, shipY - 16);
    ctx.lineTo(state.shipX - 12, shipY + 12);
    ctx.lineTo(state.shipX + 12, shipY + 12);
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = pal.accent;
    ctx.fillRect(state.shipX - 2, shipY - 6, 4, 10);
    ctx.restore();
    if (state.mode === "ready") {
      ctx.fillStyle = pal.debris;
      ctx.font = "16px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("Focus here or press an arrow key to launch.", W / 2, H / 2);
    } else if (state.mode === "over") {
      ctx.fillStyle = pal.ship;
      ctx.font = "28px serif";
      ctx.textAlign = "center";
      ctx.fillText("Game over. " + state.score + " points.", W / 2, H / 2);
    } else if (state.mode === "paused") {
      ctx.fillStyle = pal.ship;
      ctx.font = "28px serif";
      ctx.textAlign = "center";
      ctx.fillText("Paused", W / 2, H / 2);
    }
  }

  resetStars();
  function frame() {
    requestAnimationFrame(frame);
    if (state.mode === "running") step();
    draw();
  }
  frame();
})();
