/* Star Drift — 90-second vanilla canvas arcade dodger.
   Zero dependencies, zero network, zero remote pulls. Same-origin only.
   Palette is read from site tokens at boot (no hex here); canvas shapes
   carry the meaning (spark vs polygon vs triangle), never color alone.
   Motion that startles (shake, flash, particles, blink) is created only
   when the viewer has not asked for reduced motion. */
(function () {
  'use strict';

  var BEST_KEY = 'mmw.star-drift.best.v1';
  var RUN_SECONDS = 90;
  var COMBO_WINDOW = 2.5;
  var COMBO_CAP = 8;
  var MAX_LIVES = 3;
  var INVULN_SECONDS = 1.5;
  var PARTICLE_CAP = 96;
  var STAR_TARGET = 6;
  var W = 800;
  var H = 500;

  var reduceMotion = false;
  try {
    reduceMotion = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  } catch (e) { reduceMotion = false; }

  var stage = document.querySelector('.game-stage');
  var canvas = document.getElementById('star-drift');
  if (!stage || !canvas) return;
  var ctx = canvas.getContext('2d');
  if (!ctx) return;

  /* Palette from computed site tokens: solid star fill vs hollow rock
     (rock fill matches the canvas face, rock reads through its stroke).
     Both faces keep star-vs-face and stroke-vs-face above 3:1. */
  var pal = { star: '#ffffff', core: '#000000', rock: '#ffffff', edge: '#000000', ship: '#000000', face: '#ffffff' };
  try {
    var cs = window.getComputedStyle(document.documentElement);
    var tok = function (name, fallback) {
      var v = cs.getPropertyValue(name);
      v = (v || '').trim();
      return v || fallback;
    };
    pal.star = tok('--accent', pal.star);
    pal.edge = tok('--ink', pal.edge);
    pal.ship = tok('--ink', pal.ship);
    pal.face = tok('--raised', pal.face);
    pal.rock = tok('--raised', pal.rock);
    pal.core = tok('--raised', pal.core);
  } catch (e) { /* token fallbacks above keep the game playable */ }

  var hud = {
    score: stage.querySelector('[data-hud="score"]'),
    time: stage.querySelector('[data-hud="time"]'),
    lives: stage.querySelector('[data-hud="lives"]'),
    combo: stage.querySelector('[data-hud="combo"]'),
    best: stage.querySelector('[data-hud="best"]')
  };
  var statusNode = stage.querySelector('[data-game-status]');
  var hint = stage.querySelector('[data-hint]');
  var buttons = {
    start: stage.querySelector('[data-action="start"]'),
    pause: stage.querySelector('[data-action="pause"]'),
    restart: stage.querySelector('[data-action="restart"]'),
    mute: stage.querySelector('[data-action="mute"]')
  };
  var padButtons = stage.querySelectorAll('[data-dir]');

  function setText(node, value) {
    if (node && node.textContent !== value) node.textContent = value;
  }
  function announce(message) {
    setText(statusNode, message);
  }

  function loadBest() {
    try {
      var raw = window.localStorage.getItem(BEST_KEY);
      var n = parseInt(raw, 10);
      if (!isFinite(n) || n < 0) return 0;
      return Math.min(Math.floor(n), 999999);
    } catch (e) { return 0; }
  }
  function saveBest(value) {
    try {
      window.localStorage.setItem(BEST_KEY, String(Math.max(0, Math.floor(value))));
    } catch (e) { /* private mode: the run still counts */ }
  }

  /* Tiny synthesized bleeps. Created on first player gesture only;
     mute silences the gain. No audio files, no autoplay. */
  var muted = false;
  var actx = null;
  function tone(freq, seconds, kind, when) {
    if (muted) return;
    try {
      if (!actx) {
        var AC = window.AudioContext || window.webkitAudioContext;
        if (!AC) return;
        actx = new AC();
      }
      if (actx.state === 'suspended') actx.resume();
      var t0 = actx.currentTime + (when || 0);
      var osc = actx.createOscillator();
      var gain = actx.createGain();
      osc.type = kind;
      osc.frequency.setValueAtTime(freq, t0);
      gain.gain.setValueAtTime(0.0001, t0);
      gain.gain.exponentialRampToValueAtTime(0.08, t0 + 0.012);
      gain.gain.exponentialRampToValueAtTime(0.0001, t0 + seconds);
      osc.connect(gain);
      gain.connect(actx.destination);
      osc.start(t0);
      osc.stop(t0 + seconds + 0.02);
    } catch (e) { /* silence is acceptable */ }
  }
  function sfxPickup() { tone(740, 0.07, 'sine', 0); tone(1108, 0.06, 'sine', 0.05); }
  function sfxHit() { tone(140, 0.18, 'sawtooth', 0); }
  function sfxEnd() { tone(520, 0.1, 'sine', 0); tone(390, 0.14, 'sine', 0.11); }

  var state = 'ready'; /* ready | running | paused | over */
  var ship = { x: W / 2, y: H / 2, vx: 0, vy: 0, r: 12, angle: -Math.PI / 2 };
  var stars = [];
  var rocks = [];
  var parts = [];
  var score = 0;
  var combo = 1;
  var lives = MAX_LIVES;
  var timeLeft = RUN_SECONDS;
  var best = loadBest();
  var sincePickup = 99;
  var invuln = 0;
  var flash = 0;
  var shake = 0;
  var rockTimer = 0;
  var warnedTen = false;
  var keys = {};
  var pad = { up: false, down: false, left: false, right: false };
  var dragging = false;
  var dragX = 0;
  var dragY = 0;
  var lastStamp = 0;

  function fmtTime(seconds) {
    var s = Math.max(0, Math.ceil(seconds));
    var m = Math.floor(s / 60);
    var r = s - m * 60;
    return m + ':' + (r < 10 ? '0' + r : '' + r);
  }

  function refreshHud() {
    setText(hud.score, '' + score);
    setText(hud.time, fmtTime(timeLeft));
    setText(hud.lives, '' + lives);
    setText(hud.combo, '×' + combo);
    setText(hud.best, '' + best);
  }

  function rnd(a, b) { return a + Math.random() * (b - a); }

  function spawnStar(fromTop) {
    stars.push({
      x: rnd(24, W - 24),
      y: fromTop ? -18 : rnd(0, H - 60),
      vx: rnd(-14, 14),
      vy: rnd(18, 46),
      r: rnd(8, 11),
      tw: rnd(0, 6.28)
    });
  }
  function spawnRock() {
    var progress = 1 - timeLeft / RUN_SECONDS;
    rocks.push({
      x: rnd(30, W - 30),
      y: -26,
      vx: rnd(-30, 30),
      vy: rnd(60, 110) + progress * 70,
      r: rnd(13, 22),
      rot: rnd(0, 6.28),
      spin: rnd(-1.6, 1.6),
      verts: 7 + Math.floor(Math.random() * 3)
    });
  }
  function burst(x, y, n, fast) {
    if (reduceMotion) return;
    for (var i = 0; i < n; i++) {
      if (parts.length >= PARTICLE_CAP) parts.shift();
      var a = rnd(0, 6.283);
      var sp = rnd(40, fast ? 260 : 150);
      parts.push({ x: x, y: y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, life: rnd(0.3, 0.7) });
    }
  }

  function resetWorld() {
    ship.x = W / 2; ship.y = H / 2; ship.vx = 0; ship.vy = 0;
    stars = []; rocks = []; parts = [];
    for (var i = 0; i < STAR_TARGET; i++) spawnStar(false);
    score = 0; combo = 1; lives = MAX_LIVES;
    timeLeft = RUN_SECONDS; sincePickup = 99; invuln = 0;
    flash = 0; shake = 0; rockTimer = 0.8; warnedTen = false;
    refreshHud();
  }

  function startRun(label) {
    resetWorld();
    state = 'running';
    lastStamp = 0;
    if (buttons.pause) {
      buttons.pause.textContent = 'Pause';
      buttons.pause.setAttribute('aria-pressed', 'false');
    }
    announce(label || 'Run started. Collect stars, avoid rocks.');
  }

  function pauseRun() {
    if (state !== 'running') return;
    state = 'paused';
    if (buttons.pause) {
      buttons.pause.textContent = 'Resume';
      buttons.pause.setAttribute('aria-pressed', 'true');
    }
    announce('Paused. Press P or Resume to continue.');
  }
  function resumeRun() {
    if (state !== 'paused') return;
    state = 'running';
    lastStamp = 0;
    if (buttons.pause) {
      buttons.pause.textContent = 'Pause';
      buttons.pause.setAttribute('aria-pressed', 'false');
    }
    announce('Resumed.');
  }

  function endRun(reason) {
    state = 'over';
    sfxEnd();
    var isBest = score > best;
    if (isBest) {
      best = score;
      saveBest(best);
    }
    refreshHud();
    if (reason === 'time') {
      announce('Time. Final score ' + score + '.' + (isBest ? ' New best.' : ' Best ' + best + '.'));
    } else {
      announce('Game over. Final score ' + score + '.' + (isBest ? ' New best.' : ' Best ' + best + '.'));
    }
  }

  function collectStar(s) {
    if (sincePickup < COMBO_WINDOW) {
      combo = Math.min(combo + 1, COMBO_CAP);
    } else {
      combo = 1;
    }
    sincePickup = 0;
    score += 10 * combo;
    burst(s.x, s.y, 8, false);
    sfxPickup();
    refreshHud();
  }

  function hitRock(r) {
    if (invuln > 0 || state !== 'running') return;
    lives -= 1;
    combo = 1;
    invuln = INVULN_SECONDS;
    burst(r.x, r.y, 16, true);
    sfxHit();
    if (!reduceMotion) { flash = 0.35; shake = 0.3; }
    refreshHud();
    if (lives <= 0) {
      endRun('lives');
    } else {
      announce('Hit. ' + lives + (lives === 1 ? ' life' : ' lives') + ' left.');
    }
  }

  function step(dt) {
    /* steering: keys, coarse D-pad, or drag-to-steer toward the pointer */
    var ax = 0;
    var ay = 0;
    if (keys.ArrowLeft || keys.KeyA || pad.left) ax -= 1;
    if (keys.ArrowRight || keys.KeyD || pad.right) ax += 1;
    if (keys.ArrowUp || keys.KeyW || pad.up) ay -= 1;
    if (keys.ArrowDown || keys.KeyS || pad.down) ay += 1;
    if (dragging) {
      var dx = dragX - ship.x;
      var dy = dragY - ship.y;
      var d = Math.sqrt(dx * dx + dy * dy);
      if (d > 6) { ax = dx / d; ay = dy / d; }
    }
    var thrust = 900;
    ship.vx += ax * thrust * dt;
    ship.vy += ay * thrust * dt;
    var braking = !!keys.Space;
    var damp = Math.pow(braking ? 0.02 : 0.35, dt);
    ship.vx *= damp;
    ship.vy *= damp;
    var vmax = 380;
    var sp = Math.sqrt(ship.vx * ship.vx + ship.vy * ship.vy);
    if (sp > vmax) { ship.vx = ship.vx / sp * vmax; ship.vy = ship.vy / sp * vmax; }
    ship.x += ship.vx * dt;
    ship.y += ship.vy * dt;
    if (ship.x < ship.r) { ship.x = ship.r; ship.vx = Math.abs(ship.vx) * 0.4; }
    if (ship.x > W - ship.r) { ship.x = W - ship.r; ship.vx = -Math.abs(ship.vx) * 0.4; }
    if (ship.y < ship.r) { ship.y = ship.r; ship.vy = Math.abs(ship.vy) * 0.4; }
    if (ship.y > H - ship.r) { ship.y = H - ship.r; ship.vy = -Math.abs(ship.vy) * 0.4; }
    if (sp > 20) ship.angle = Math.atan2(ship.vy, ship.vx);

    sincePickup += dt;
    if (sincePickup >= COMBO_WINDOW && combo !== 1) {
      combo = 1;
      refreshHud();
    }

    timeLeft -= dt;
    var wholeBefore = Math.ceil(timeLeft + dt);
    var wholeNow = Math.ceil(timeLeft);
    if (wholeNow !== wholeBefore) refreshHud();
    if (timeLeft <= 10 && !warnedTen && timeLeft > 0) {
      warnedTen = true;
      announce('10 seconds left. Score ' + score + '.');
    }
    if (timeLeft <= 0) {
      timeLeft = 0;
      refreshHud();
      endRun('time');
      return;
    }

    if (invuln > 0) invuln -= dt;
    if (flash > 0) flash -= dt;
    if (shake > 0) shake -= dt;

    while (stars.length < STAR_TARGET) spawnStar(true);
    rockTimer -= dt;
    if (rockTimer <= 0) {
      spawnRock();
      var progress = 1 - timeLeft / RUN_SECONDS;
      rockTimer = 1.4 - progress * 0.7;
    }

    var i, e;
    for (i = stars.length - 1; i >= 0; i--) {
      e = stars[i];
      e.x += e.vx * dt; e.y += e.vy * dt; e.tw += dt * 3;
      if (e.y > H + 20 || e.x < -20 || e.x > W + 20) { stars.splice(i, 1); continue; }
      var sdx = e.x - ship.x;
      var sdy = e.y - ship.y;
      if (sdx * sdx + sdy * sdy < (e.r + ship.r) * (e.r + ship.r)) {
        stars.splice(i, 1);
        collectStar(e);
      }
    }
    for (i = rocks.length - 1; i >= 0; i--) {
      e = rocks[i];
      e.x += e.vx * dt; e.y += e.vy * dt; e.rot += e.spin * dt;
      if (e.y > H + 30 || e.x < -40 || e.x > W + 40) { rocks.splice(i, 1); continue; }
      var rdx = e.x - ship.x;
      var rdy = e.y - ship.y;
      if (rdx * rdx + rdy * rdy < (e.r + ship.r - 3) * (e.r + ship.r - 3)) {
        rocks.splice(i, 1);
        hitRock(e);
        if (state !== 'running') return;
      }
    }
    for (i = parts.length - 1; i >= 0; i--) {
      e = parts[i];
      e.life -= dt;
      if (e.life <= 0) { parts.splice(i, 1); continue; }
      e.x += e.vx * dt; e.y += e.vy * dt;
      e.vx *= Math.pow(0.2, dt); e.vy *= Math.pow(0.2, dt);
    }
  }

  /* Shapes: star = 4-point spark (solid) + pale core; rock = irregular
     polygon (hollow, dark/light edge); ship = triangle with outline. */
  function drawStar(e, t) {
    var pulse = 1 + 0.08 * Math.sin(e.tw);
    var R = e.r * pulse;
    var r = R * 0.38;
    ctx.beginPath();
    for (var i = 0; i < 8; i++) {
      var rad = (i % 2 === 0) ? R : r;
      var a = (Math.PI / 4) * i + t * 0.4;
      var px = e.x + Math.cos(a) * rad;
      var py = e.y + Math.sin(a) * rad;
      if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    }
    ctx.closePath();
    ctx.fillStyle = pal.star;
    ctx.fill();
    ctx.beginPath();
    ctx.arc(e.x, e.y, R * 0.22, 0, 6.283);
    ctx.fillStyle = pal.core;
    ctx.fill();
  }
  function drawRock(e) {
    ctx.beginPath();
    for (var i = 0; i < e.verts; i++) {
      var a = e.rot + (6.283 * i) / e.verts;
      var rad = e.r * (0.78 + 0.22 * Math.sin(i * 2.7 + e.rot));
      var px = e.x + Math.cos(a) * rad;
      var py = e.y + Math.sin(a) * rad;
      if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    }
    ctx.closePath();
    ctx.fillStyle = pal.rock;
    ctx.fill();
    ctx.lineWidth = 2.5;
    ctx.strokeStyle = pal.edge;
    ctx.stroke();
  }
  function drawShip(t) {
    var blinkOff = invuln > 0 && !reduceMotion && (Math.floor(t * 10) % 2 === 0);
    ctx.save();
    ctx.translate(ship.x, ship.y);
    ctx.rotate(ship.angle + Math.PI / 2);
    ctx.beginPath();
    ctx.moveTo(0, -14);
    ctx.lineTo(10, 10);
    ctx.lineTo(0, 5);
    ctx.lineTo(-10, 10);
    ctx.closePath();
    if (!blinkOff) {
      ctx.fillStyle = pal.ship;
      ctx.fill();
    }
    ctx.lineWidth = reduceMotion && invuln > 0 ? 3.5 : 2;
    ctx.strokeStyle = pal.star;
    ctx.stroke();
    ctx.restore();
  }

  function draw(t) {
    ctx.save();
    ctx.clearRect(0, 0, W, H);
    if (shake > 0 && !reduceMotion) {
      ctx.translate(rnd(-4, 4) * shake * 3, rnd(-4, 4) * shake * 3);
    }
    var i;
    for (i = 0; i < rocks.length; i++) drawRock(rocks[i]);
    for (i = 0; i < stars.length; i++) drawStar(stars[i], t);
    for (i = 0; i < parts.length; i++) {
      var p = parts[i];
      ctx.globalAlpha = Math.max(0, p.life * 1.6);
      ctx.fillStyle = pal.star;
      ctx.fillRect(p.x - 1.5, p.y - 1.5, 3, 3);
    }
    ctx.globalAlpha = 1;
    if (state !== 'over') drawShip(t);
    if (flash > 0 && !reduceMotion) {
      ctx.globalAlpha = Math.min(0.28, flash);
      ctx.fillStyle = pal.star;
      ctx.fillRect(-10, -10, W + 20, H + 20);
      ctx.globalAlpha = 1;
    }
    if (state === 'ready' || state === 'paused' || state === 'over') {
      /* State scrim: fixed dark veil + fixed light label so the message
         reads over live game art in both themes (functional overlay,
         not part of the entity palette). */
      ctx.fillStyle = 'rgba(0, 0, 0, 0.45)';
      ctx.fillRect(0, H / 2 - 34, W, 68);
      ctx.fillStyle = '#ffffff';
      ctx.font = '24px Georgia, serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      var label = state === 'ready' ? 'Press Start or Enter' : (state === 'paused' ? 'Paused — P to resume' : 'Score ' + score + ' — Enter to retry');
      ctx.fillText(label, W / 2, H / 2);
    }
    ctx.restore();
  }

  var elapsed = 0;
  function frame(stamp) {
    if (state === 'running') {
      if (!lastStamp) lastStamp = stamp;
      var dt = (stamp - lastStamp) / 1000;
      lastStamp = stamp;
      if (dt > 0.05) dt = 0.05; /* capped delta: tabs and hitches cost no physics */
      if (dt > 0) { elapsed += dt; step(dt); }
    } else {
      lastStamp = 0;
      /* Idle attract screen stays still for reduced motion. */
      if (!reduceMotion) elapsed += 1 / 60;
    }
    draw(elapsed);
    window.requestAnimationFrame(frame);
  }

  /* Input: keyboard everywhere, drag on the canvas, coarse D-pad buttons.
     Page scroll is never hijacked: arrows and space are claimed only when
     the game is engaged (focus inside the stage, or body focus mid-run),
     never in fields and never through native button keys. */
  function inStage(node) {
    return !!(node && stage.contains(node));
  }
  function gameKey(code) {
    return code === 'ArrowLeft' || code === 'ArrowRight' || code === 'ArrowUp' || code === 'ArrowDown' ||
      code === 'Space' || code === 'KeyA' || code === 'KeyD' || code === 'KeyW' || code === 'KeyS' ||
      code === 'KeyP' || code === 'KeyM' || code === 'Enter' || code === 'Escape';
  }
  document.addEventListener('keydown', function (ev) {
    var target = ev.target;
    var tag = target && target.tagName ? target.tagName : '';
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
    if (!gameKey(ev.code)) return;
    /* Engaged = focus inside the stage, or body focus while a run is
       live (canvas is not focusable; clicking it leaves focus on body).
       Otherwise arrows and space keep their page behavior. */
    var engaged = inStage(target) || (target === document.body && (state === 'running' || state === 'paused'));
    if (!engaged) return;
    if ((ev.code === 'Space' || ev.code === 'Enter') && tag === 'BUTTON') return; /* native click covers it */
    if (ev.code === 'ArrowLeft' || ev.code === 'ArrowRight' || ev.code === 'ArrowUp' ||
      ev.code === 'ArrowDown' || ev.code === 'Space') {
      ev.preventDefault();
    }
    if (ev.repeat) {
      keys[ev.code] = true;
      return;
    }
    keys[ev.code] = true;
    if (ev.code === 'Enter') {
      if (state === 'running') startRun('Fresh drift. Thread the debris, brake with Space.');
      else startRun();
    } else if (ev.code === 'KeyP' || ev.code === 'Escape') {
      if (state === 'running') pauseRun();
      else if (state === 'paused') resumeRun();
    } else if (ev.code === 'KeyM') {
      toggleMute();
    }
  });
  document.addEventListener('keyup', function (ev) {
    keys[ev.code] = false;
  });
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) pauseRun();
  });
  window.addEventListener('blur', function () {
    pauseRun();
  });

  function canvasPoint(ev) {
    var rect = canvas.getBoundingClientRect();
    return {
      x: (ev.clientX - rect.left) * (W / rect.width),
      y: (ev.clientY - rect.top) * (H / rect.height)
    };
  }
  canvas.addEventListener('pointerdown', function (ev) {
    var p = canvasPoint(ev);
    dragging = true;
    dragX = p.x; dragY = p.y;
    try { canvas.setPointerCapture(ev.pointerId); } catch (e) { /* mouse stays fine */ }
    if (hint && !hint.hidden) hint.hidden = true;
  });
  canvas.addEventListener('pointermove', function (ev) {
    if (!dragging) return;
    var p = canvasPoint(ev);
    dragX = p.x; dragY = p.y;
  });
  function endDrag() { dragging = false; }
  canvas.addEventListener('pointerup', endDrag);
  canvas.addEventListener('pointercancel', endDrag);

  function eachPad(fn) {
    for (var i = 0; i < padButtons.length; i++) fn(padButtons[i]);
  }
  eachPad(function (btn) {
    var dir = btn.getAttribute('data-dir');
    btn.addEventListener('pointerdown', function (ev) {
      ev.preventDefault();
      pad[dir] = true;
      try { btn.setPointerCapture(ev.pointerId); } catch (e) { /* tap still steers */ }
    });
    var release = function () { pad[dir] = false; };
    btn.addEventListener('pointerup', release);
    btn.addEventListener('pointercancel', release);
    btn.addEventListener('lostpointercapture', release);
  });

  function toggleMute() {
    muted = !muted;
    if (buttons.mute) buttons.mute.setAttribute('aria-pressed', muted ? 'true' : 'false');
    if (!muted) tone(660, 0.06, 'sine', 0);
  }

  if (buttons.start) buttons.start.addEventListener('click', function () {
    if (state === 'running') startRun('Fresh drift. Thread the debris, brake with Space.');
    else startRun();
  });
  if (buttons.restart) buttons.restart.addEventListener('click', function () {
    startRun('Fresh drift. Thread the debris, brake with Space.');
  });
  if (buttons.pause) buttons.pause.addEventListener('click', function () {
    if (state === 'running') pauseRun();
    else if (state === 'paused') resumeRun();
    else startRun();
  });
  if (buttons.mute) buttons.mute.addEventListener('click', toggleMute);

  resetWorld();
  state = 'ready';
  refreshHud();
  window.requestAnimationFrame(frame);
})();
