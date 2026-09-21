/* Star Chime — audio-first sequence-memory game.
   Four pads sing a tune that grows by one note each round. The rules
   live in a small state machine (idle, showing, input, round-clear,
   mistake, gameover, victory) that only wakes on player gestures or
   one playback timer, so an idle page does zero work. Sound is a
   Web Audio oscillator voice born on the first gesture. Pads glow
   through a lit class plus number and solfege labels, so pitch never
   rides on color alone. */
var StarChime = (function () {
'use strict';
var WIN_ROUNDS = 12;
var MAX_LIVES = 3;
var MAX_HINTS = 2;
var BASE_FLASH = 450;
var BASE_GAP = 250;
var MIN_FLASH = 280;
var MIN_GAP = 140;
var QUICKEN = 0.95;
var FREQS = [261.63, 329.63, 392.0, 523.25];
var NAMES = ['Do', 'Mi', 'Sol', 'La'];
function rng32(seed) {
  var a = seed >>> 0;
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    var t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
/* Round length grows by one note per round: round 1 sings 3 pads,
   round 12 sings 14. Every round is generatable, so twelve wins in
   a row are winnable by construction. */
function roundLen(round) { return round + 2; }
function buildRound(seed, len) {
  var rng = rng32(seed), seq = [], i;
  for (i = 0; i < len; i += 1) seq.push(1 + Math.floor(rng() * 4));
  return seq;
}
/* Playback quickens five percent per round toward a floor, so later
   rounds feel brisk without ever dropping past the floor. */
function flashMs(round) {
  var ms = Math.round(BASE_FLASH * Math.pow(QUICKEN, round - 1));
  return ms < MIN_FLASH ? MIN_FLASH : ms;
}
function gapMs(round) {
  var ms = Math.round(BASE_GAP * Math.pow(QUICKEN, round - 1));
  return ms < MIN_GAP ? MIN_GAP : ms;
}
var api = { WIN_ROUNDS: WIN_ROUNDS, MAX_LIVES: MAX_LIVES,
  MAX_HINTS: MAX_HINTS, BASE_FLASH: BASE_FLASH, BASE_GAP: BASE_GAP,
  MIN_FLASH: MIN_FLASH, QUICKEN: QUICKEN, FREQS: FREQS,
  flashMs: flashMs, gapMs: gapMs, roundLen: roundLen,
  buildRound: buildRound, rng32: rng32 };
/* DOM wiring (browsers only). */
if (typeof document === 'undefined') {
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  return api;
}
var BEST_KEY = 'mmw.star-chime.best.v1';
var stage = document.querySelector('.game-stage');
var padWrap = document.querySelector('[data-chime-pads]');
if (!stage || !padWrap) return api;
var pads = [];
(function collect() {
  var nodes = padWrap.querySelectorAll('[data-pad]'), i;
  for (i = 0; i < nodes.length; i += 1) pads.push(nodes[i]);
})();
var hud = {
  round: stage.querySelector('[data-hud="round"]'),
  score: stage.querySelector('[data-hud="score"]'),
  lives: stage.querySelector('[data-hud="lives"]'),
  best: stage.querySelector('[data-hud="best"]')
};
var statusNode = stage.querySelector('[data-game-status]');
var overlayRoot = stage.querySelector('[data-overlays]');
var hintBtn = stage.querySelector('[data-action="hint"]');
var muteBtn = stage.querySelector('[data-action="mute"]');
function setText(node, value) {
  if (node && node.textContent !== value) node.textContent = value;
}
function announce(message) { setText(statusNode, message); }
function loadBest() {
  try {
    var raw = window.localStorage.getItem(BEST_KEY);
    var n = parseInt(raw, 10);
    if (!isFinite(n) || n < 0) return 0;
    return Math.floor(n);
  } catch (e) { return 0; }
}
function saveBest(value) {
  try {
    window.localStorage.setItem(BEST_KEY, String(Math.max(0, Math.floor(value))));
  } catch (e) { /* private mode: the run still counts */ }
}
var reduceMotion = false;
try {
  reduceMotion = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
} catch (e) { reduceMotion = false; }
if (reduceMotion) stage.classList.add('chime-still');
/* Voice is born on the first gesture: no sound object exists until
   the player starts or taps a pad. */
var muted = false, actx = null;
function ensureAudio() {
  try {
    if (!actx) {
      var AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return false;
      actx = new AC();
    }
    if (actx.state === 'suspended') actx.resume();
    return true;
  } catch (e) { return false; }
}
function tone(pad, seconds, when) {
  if (muted) return;
  if (!ensureAudio()) return;
  try {
    var t0 = actx.currentTime + (when || 0);
    var osc = actx.createOscillator(), gain = actx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(FREQS[pad - 1], t0);
    gain.gain.setValueAtTime(0.0001, t0);
    gain.gain.exponentialRampToValueAtTime(0.12, t0 + 0.015);
    gain.gain.exponentialRampToValueAtTime(0.0001, t0 + seconds);
    osc.connect(gain); gain.connect(actx.destination);
    osc.start(t0); osc.stop(t0 + seconds + 0.02);
  } catch (e) { /* silence is acceptable */ }
}
function sfxBad() {
  if (muted) return;
  if (!ensureAudio()) return;
  try {
    var t0 = actx.currentTime;
    var osc = actx.createOscillator(), gain = actx.createGain();
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(160, t0);
    gain.gain.setValueAtTime(0.0001, t0);
    gain.gain.exponentialRampToValueAtTime(0.1, t0 + 0.015);
    gain.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.22);
    osc.connect(gain); gain.connect(actx.destination);
    osc.start(t0); osc.stop(t0 + 0.24);
  } catch (e) { /* silence is acceptable */ }
}
var state = 'idle';
var round = 1, lives = MAX_LIVES, score = 0, best = loadBest();
var seq = [], pos = 0, hintsUsed = 0, runSeed = 1, pausedFrom = null;
var pending = [];
function later(fn, ms) {
  var id = window.setTimeout(function () {
    pending = pending.filter(function (x) { return x !== id; });
    fn();
  }, ms);
  pending.push(id);
  return id;
}
function clearPending() {
  for (var i = 0; i < pending.length; i += 1) window.clearTimeout(pending[i]);
  pending = [];
}
function unlit() {
  for (var i = 0; i < pads.length; i += 1) pads[i].classList.remove('lit');
}
function paint() {
  setText(hud.round, String(round) + ' / ' + String(WIN_ROUNDS));
  setText(hud.score, String(score));
  setText(hud.lives, String(lives));
  setText(hud.best, String(best));
  if (hintBtn) {
    var left = MAX_HINTS - hintsUsed;
    setText(hintBtn, left > 0 ? 'Hint (' + left + ' left)' : 'Hint (none left)');
  }
}
function show(name) {
  if (!overlayRoot) return;
  var panels = overlayRoot.querySelectorAll('[data-overlay]');
  for (var i = 0; i < panels.length; i += 1) {
    panels[i].hidden = panels[i].getAttribute('data-overlay') !== name;
  }
  if (name) {
    var first = overlayRoot.querySelector('[data-overlay="' + name + '"] button:not([disabled])');
    if (first) first.focus();
  }
}
function flashPad(pad, ms) {
  var node = pads[pad - 1];
  if (!node) return;
  node.classList.add('lit');
  tone(pad, Math.min(0.6, ms / 1000));
  later(function () { node.classList.remove('lit'); }, ms);
}
function playSeq() {
  state = 'showing';
  unlit();
  paint();
  show(null);
  var step = flashMs(round) + gapMs(round), i;
  announce('Round ' + round + ': watch the ' + seq.length + ' notes.');
  for (i = 0; i < seq.length; i += 1) {
    (function (n, at) {
      later(function () {
        if (state !== 'showing') return;
        flashPad(n, flashMs(round));
      }, at);
    })(seq[i], i * step);
  }
  later(function () {
    if (state !== 'showing') return;
    state = 'input';
    pos = 0;
    paint();
    announce('Your turn: repeat the ' + seq.length + ' notes.');
  }, seq.length * step + gapMs(round));
}
function startRun() {
  ensureAudio();
  clearPending();
  round = 1; lives = MAX_LIVES; score = 0;
  hintsUsed = 0; pausedFrom = null;
  runSeed += 1;
  seq = buildRound(runSeed, roundLen(round));
  playSeq();
  if (reduceMotion) announce('Round 1: watch the 3 notes. Reduced motion on: pads glow steady.');
}
function winRound() {
  if (round >= WIN_ROUNDS) {
    state = 'victory';
    clearPending();
    unlit();
    if (score > best) { best = score; saveBest(best); }
    paint();
    setText(stage.querySelector('[data-victory-text]'),
      'Twelve rounds, ' + score + ' true notes, best ' + best + '. The last tune rang clean.');
    show('victory');
    tone(4, 0.4, 0); tone(3, 0.4, 0.18); tone(2, 0.4, 0.36); tone(1, 0.6, 0.54);
    announce('Victory. All twelve rounds ring out. Score ' + score + '.');
    return;
  }
  state = 'round-clear';
  paint();
  announce('Round ' + round + ' clear. Listen for round ' + (round + 1) + '.');
  later(function () {
    if (state !== 'round-clear') return;
    round += 1;
    hintsUsed = 0;
    seq = buildRound(runSeed * 31 + round, roundLen(round));
    playSeq();
  }, 900);
}
function miss(pad) {
  lives -= 1;
  sfxBad();
  if (lives <= 0) {
    state = 'gameover';
    clearPending();
    unlit();
    if (score > best) { best = score; saveBest(best); }
    paint();
    setText(stage.querySelector('[data-complete-text]'),
      'Round ' + round + ', score ' + score + ', best ' + best + '. The tune outlasted three lives.');
    show('complete');
    announce('No lives left. Score ' + score + '.');
    return;
  }
  state = 'mistake';
  paint();
  announce('Pad ' + pad + ' is not next. ' + lives + ' lives left; the round replays.');
  later(function () {
    if (state !== 'mistake') return;
    playSeq();
  }, 900);
}
function press(pad) {
  if (state !== 'input') return;
  ensureAudio();
  flashPad(pad, 220);
  if (pad === seq[pos]) {
    pos += 1;
    score += 1;
    if (pos >= seq.length) { paint(); winRound(); return; }
    paint();
    return;
  }
  paint();
  miss(pad);
}
function hint() {
  if (state !== 'input') return;
  if (hintsUsed >= MAX_HINTS) {
    announce('No hints left this round. ' + seq.length + ' notes; you hold ' + pos + '.');
    return;
  }
  hintsUsed += 1;
  var next = seq[pos];
  paint();
  flashPad(next, 450);
  announce('Hint: pad ' + next + ' sings ' + NAMES[next - 1] + '. ' +
    (MAX_HINTS - hintsUsed) + ' hints left this round.');
}
function doAction(name) {
  if (name === 'start') { startRun(); return; }
  if (name === 'replay') { startRun(); return; }
  if (name === 'pause') {
    if (state === 'showing' || state === 'input' ||
        state === 'round-clear' || state === 'mistake') {
      pausedFrom = state;
      clearPending();
      unlit();
      state = 'idle';
      show('paused');
      announce('Paused. Resume replays round ' + round + ' from the top.');
    }
    return;
  }
  if (name === 'resume') {
    if (pausedFrom) {
      pausedFrom = null;
      seq = seq.length ? seq : buildRound(runSeed, roundLen(round));
      playSeq();
      announce('Resumed. Round ' + round + ' replays from the top.');
    }
    return;
  }
  if (name === 'hint') { hint(); return; }
  if (name === 'mute') {
    muted = !muted;
    if (muteBtn) {
      setText(muteBtn, muted ? 'Unmute' : 'Mute');
      muteBtn.setAttribute('aria-pressed', muted ? 'true' : 'false');
    }
    announce(muted ? 'Muted.' : 'Sound on.');
  }
}
for (var p = 0; p < pads.length; p += 1) {
  (function (n) {
    pads[n].addEventListener('click', function () { press(n + 1); });
  })(p);
}
stage.addEventListener('click', function (ev) {
  var el = ev.target;
  while (el && el !== stage) {
    if (el.getAttribute && el.getAttribute('data-action')) {
      doAction(el.getAttribute('data-action'));
      return;
    }
    el = el.parentNode;
  }
});
document.addEventListener('keydown', function (ev) {
  var code = ev.code || ev.key;
  if (code === 'KeyM') { doAction('mute'); return; }
  if (code === 'KeyP' || code === 'Escape') {
    if (state === 'idle' && overlayRoot &&
        overlayRoot.querySelector('[data-overlay="paused"]') &&
        !overlayRoot.querySelector('[data-overlay="paused"]').hidden) {
      doAction('resume');
    } else {
      doAction('pause');
    }
    return;
  }
  if (code === 'KeyH') { hint(); return; }
  if (code === 'Enter') {
    var shown = overlayRoot ? overlayRoot.querySelector('[data-overlay]:not([hidden])') : null;
    var which = shown ? shown.getAttribute('data-overlay') : null;
    if (which === 'start' || which === 'complete' || which === 'victory') doAction('start');
    else if (which === 'paused') doAction('resume');
    return;
  }
  var pad = 0;
  if (code === 'Digit1' || code === 'Numpad1' || code === '1') pad = 1;
  else if (code === 'Digit2' || code === 'Numpad2' || code === '2') pad = 2;
  else if (code === 'Digit3' || code === 'Numpad3' || code === '3') pad = 3;
  else if (code === 'Digit4' || code === 'Numpad4' || code === '4') pad = 4;
  if (pad) press(pad);
});
paint();
show('start');
announce('Star Chime ready. Open the start panel to play.');
return api;
})();
if (typeof module !== 'undefined' && module.exports) module.exports = StarChime;
