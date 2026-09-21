/* Star Relay — turn-based DOM-grid rotation puzzle.
   Zero dependencies, zero network, zero render loop: the board only
   changes on player moves, so idle pages do no work. Boards generate
   from a solved reactor-to-beacon path and then scramble, which keeps
   every level solvable by construction. Meaning never rides on color
   alone: glyph shape, lit class and labels all agree. Sound is bleeps
   made after the first gesture only. */
var StarRelay = (function () {
'use strict';
var N = 1, E = 2, S = 4, W = 8;
function rot(ports, turns) {
  var r = ((turns % 4) + 4) % 4, out = 0, i;
  for (i = 0; i < 4; i += 1) {
    if (ports & (1 << i)) out |= 1 << ((i + r) % 4);
  }
  return out;
}
function rng32(seed) {
  var a = seed >>> 0;
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    var t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
var LEVELS = [
  { size: 4, slack: 4, tees: 0, walls: 0 },
  { size: 4, slack: 4, tees: 1, walls: 0 },
  { size: 5, slack: 6, tees: 1, walls: 2 },
  { size: 5, slack: 6, tees: 2, walls: 3 },
  { size: 5, slack: 8, tees: 2, walls: 4 },
  { size: 5, slack: 8, tees: 3, walls: 5 }
];
function key(r, c) { return r + ':' + c; }
function stepTo(a, b) {
  if (b[0] === a[0] - 1) return N;
  if (b[0] === a[0] + 1) return S;
  if (b[1] === a[1] + 1) return E;
  return W;
}
/* Self-avoiding walk from beside the reactor to beside the beacon.
   Retries on dead ends; falls back to the straight row so generation
   always terminates. minLen keeps later boards from solving short. */
function buildPath(rng, size, row, minLen) {
  var t, r, c, i, guard, stuck, seen, path, opts, pick, line, c2;
  var start = [row, 1], target = [row, size - 2];
  for (t = 0; t < 400; t += 1) {
    seen = {}; path = [[row, 0], [row, 1]];
    seen[key(row, 0)] = 1; seen[key(row, 1)] = 1;
    r = start[0]; c = start[1]; stuck = false; guard = 0;
    while ((r !== target[0] || c !== target[1]) && guard < 400) {
      guard += 1; opts = [];
      var ns = [[r - 1, c], [r, c + 1], [r + 1, c], [r, c - 1]];
      for (i = 0; i < 4; i += 1) {
        var nr = ns[i][0], nc = ns[i][1];
        if (nr < 0 || nc < 0 || nr >= size || nc >= size) continue;
        if (nr === row && (nc === 0 || nc === size - 1)) continue;
        if (seen[key(nr, nc)]) continue;
        opts.push([nr, nc]);
      }
      if (!opts.length) { stuck = true; break; }
      pick = opts[Math.floor(rng() * opts.length)];
      r = pick[0]; c = pick[1];
      seen[key(r, c)] = 1; path.push([r, c]);
    }
    if (!stuck && path.length >= minLen) { path.push([row, size - 1]); return path; }
  }
  line = [];
  for (c2 = 0; c2 < size; c2 += 1) line.push([row, c2]);
  return line;
}
function kindOf(ports) {
  var n = 0, p = ports;
  while (p) { n += p & 1; p >>= 1; }
  if (n === 2) {
    if (ports === (N | S) || ports === (E | W)) return 'straight';
    return 'elbow';
  }
  return 'tee';
}
/* Cheapest clockwise turns restoring solved ports (straights match
   twice per revolution, so the fix can cost 0 even when twisted). */
function fixCost(base, turned, solved) {
  var t;
  for (t = 0; t < 4; t += 1) {
    if (rot(base, turned + t) === solved) return t;
  }
  return 0;
}
function generate(levelIdx, attempt) {
  var spec = LEVELS[levelIdx % LEVELS.length];
  var size = spec.size, row = (size - 1) >> 1;
  var rng = rng32(0x9E37 + levelIdx * 7919 + (attempt || 0) * 131);
  var minLen = size === 4 ? size : size + 2;
  var path = buildPath(rng, size, row, minLen);
  var onPath = {}, i, j;
  for (i = 0; i < path.length; i += 1) onPath[key(path[i][0], path[i][1])] = i;
  var tiles = new Array(size * size), solved = new Array(size * size);
  function at(r, c) { return tiles[r * size + c]; }
  for (i = 0; i < size; i += 1) {
    for (j = 0; j < size; j += 1) {
      var idx = i * size + j, ports = 0, fixed = false, wall = false, kind = 'fill';
      if (i === row && j === 0) { ports = E; fixed = true; kind = 'reactor'; }
      else if (i === row && j === size - 1) { ports = W; fixed = true; kind = 'beacon'; }
      else if (onPath[key(i, j)] !== undefined) {
        var pi = onPath[key(i, j)];
        ports = stepTo(path[pi], path[pi - 1]) | stepTo(path[pi], path[pi + 1]);
        kind = 'path';
      }
      tiles[idx] = { base: ports, rot: 0, fixed: fixed, wall: wall, kind: kind };
      solved[idx] = ports;
    }
  }
  /* Upgrade path tiles to tees: a third arm facing a cell off the
     solved line, so only one of four orientations is correct. */
  var upgraded = 0, guard = 0;
  while (upgraded < spec.tees && guard < 200) {
    guard += 1;
    var pi2 = 1 + Math.floor(rng() * (path.length - 2));
    var cell = path[pi2], pr = cell[0], pc = cell[1];
    var tile = at(pr, pc);
    if (tile.kind !== 'path' || kindOf(tile.base) !== 'elbow') continue;
    var used = tile.base, arms = [N, E, S, W], free = [];
    for (i = 0; i < 4; i += 1) {
      if (used & arms[i]) continue;
      var qr = pr + (arms[i] === N ? -1 : arms[i] === S ? 1 : 0);
      var qc = pc + (arms[i] === E ? 1 : arms[i] === W ? -1 : 0);
      if (qr < 0 || qc < 0 || qr >= size || qc >= size) continue;
      if (onPath[key(qr, qc)] !== undefined) continue;
      if (qr === row && (qc === 0 || qc === size - 1)) continue;
      free.push(arms[i]);
    }
    if (!free.length) continue;
    tile.base |= free[Math.floor(rng() * free.length)];
    tile.kind = 'tee';
    solved[pr * size + pc] = tile.base;
    upgraded += 1;
  }
  /* Walls on cells off the solved line, never touching the endpoints. */
  var placed = 0; guard = 0;
  while (placed < spec.walls && guard < 300) {
    guard += 1;
    var wr = Math.floor(rng() * size), wc = Math.floor(rng() * size);
    if (onPath[key(wr, wc)] !== undefined) continue;
    if (wr === row && (wc === 0 || wc === size - 1)) continue;
    var wt = at(wr, wc);
    if (wt.kind !== 'fill') continue;
    wt.kind = 'wall'; wt.wall = true; wt.fixed = true; wt.base = 0;
    solved[wr * size + wc] = 0;
    placed += 1;
  }
  /* Fillers: random tile, random facing. */
  var faces = [N | S, N | E, N | E | S];
  for (i = 0; i < tiles.length; i += 1) {
    if (tiles[i].kind === 'fill') {
      tiles[i].base = faces[Math.floor(rng() * faces.length)];
      tiles[i].rot = Math.floor(rng() * 4);
      solved[i] = tiles[i].base;
    }
  }
  /* Scramble: twist every loose tile, then price the cheapest fix.
     Boards that survive solved get twisted again. */
  var trips = 0, optimal = 0, k;
  while (trips < 20) {
    optimal = 0;
    for (i = 0; i < tiles.length; i += 1) {
      if (tiles[i].fixed) continue;
      if (trips === 0) {
        k = 1 + Math.floor(rng() * 3);
        tiles[i].rot = (tiles[i].rot + k) % 4;
      } else if (i === 1 + trips) {
        tiles[i].rot = (tiles[i].rot + 1) % 4;
      }
      optimal += fixCost(tiles[i].base, tiles[i].rot, solved[i]);
    }
    if (!flow(tiles, size, row).won) break;
    trips += 1;
  }
  var home = [];
  for (i = 0; i < tiles.length; i += 1) home.push(solved[i]);
  return { size: size, row: row, tiles: tiles, home: home, optimal: optimal,
    budget: optimal + spec.slack, slack: spec.slack };
}
/* Power flow: breadth search from the reactor through mutual ports.
   Walls carry no ports, so they never conduct. */
function flow(tiles, size, row) {
  function portsAt(idx) {
    var r = (idx / size) >> 0, c = idx % size, t = tiles[idx];
    if (t.wall) return 0;
    if (t.kind === 'reactor') return E;
    if (t.kind === 'beacon') return W;
    return rot(t.base, t.rot);
  }
  var lit = new Array(tiles.length), queue = [row * size], won = false, q = 0;
  for (var i = 0; i < lit.length; i += 1) lit[i] = false;
  lit[row * size] = true;
  while (q < queue.length) {
    var cur = queue[q++], cr = (cur / size) >> 0, cc = cur % size;
    var cp = portsAt(cur);
    var ns = [[cr - 1, cc, N, S], [cr, cc + 1, E, W], [cr + 1, cc, S, N], [cr, cc - 1, W, E]];
    for (i = 0; i < 4; i += 1) {
      var nr = ns[i][0], nc = ns[i][1];
      if (nr < 0 || nc < 0 || nr >= size || nc >= size) continue;
      var ni = nr * size + nc;
      if (lit[ni]) continue;
      if ((cp & ns[i][2]) && (portsAt(ni) & ns[i][3])) {
        lit[ni] = true;
        queue.push(ni);
        if (tiles[ni].kind === 'beacon') won = true;
      }
    }
  }
  return { lit: lit, won: won };
}
function glyphFor(kind, ports) {
  if (kind === 'reactor') return '●';
  if (kind === 'beacon') return '◆';
  if (ports === (N | S)) return '│';
  if (ports === (E | W)) return '─';
  if (ports === (N | E)) return '└';
  if (ports === (E | S)) return '┌';
  if (ports === (S | W)) return '┐';
  if (ports === (N | W)) return '┘';
  if (ports === (E | S | W)) return '┬';
  if (ports === (N | E | W)) return '┴';
  if (ports === (N | S | E)) return '├';
  if (ports === (N | S | W)) return '┤';
  return '·';
}
var api = { N: N, E: E, S: S, W: W, LEVELS: LEVELS, rot: rot,
  rng32: rng32, generate: generate, flow: flow, fixCost: fixCost,
  glyphFor: glyphFor, kindOf: kindOf };
/* DOM wiring (browsers only). */
if (typeof document === 'undefined') {
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  return api;
}
var PROGRESS_KEY = 'mmw-star-relay-progress';
var BEST_KEY = 'mmw-star-relay-best';
var stage = document.querySelector('.game-stage');
var boardNode = document.querySelector('[data-relay-board]');
if (!stage || !boardNode) return api;
var hud = {
  level: stage.querySelector('[data-hud="level"]'),
  moves: stage.querySelector('[data-hud="moves"]'),
  score: stage.querySelector('[data-hud="score"]'),
  best: stage.querySelector('[data-hud="best"]')
};
var statusNode = stage.querySelector('[data-game-status]');
var levelList = stage.querySelector('[data-level-list]');
var overlayRoot = stage.querySelector('[data-overlays]');
var motionBtn = stage.querySelector('[data-action="motion"]');
function setText(node, value) {
  if (node && node.textContent !== value) node.textContent = value;
}
function announce(message) { setText(statusNode, message); }
function loadInt(keyName, cap) {
  try {
    var raw = window.localStorage.getItem(keyName);
    var n = parseInt(raw, 10);
    if (!isFinite(n) || n < 0) return 0;
    return Math.min(Math.floor(n), cap);
  } catch (e) { return 0; }
}
function saveInt(keyName, value) {
  try {
    window.localStorage.setItem(keyName, String(Math.max(0, Math.floor(value))));
  } catch (e) { /* private mode: the run still counts */ }
}
var reduceMotion = false;
try {
  reduceMotion = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
} catch (e) { reduceMotion = false; }
if (reduceMotion) stage.classList.add('relay-still');
/* Bleeps only after a gesture: the context is born on first play. */
var muted = false, actx = null;
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
    var osc = actx.createOscillator(), gain = actx.createGain();
    osc.type = kind;
    osc.frequency.setValueAtTime(freq, t0);
    gain.gain.setValueAtTime(0.0001, t0);
    gain.gain.exponentialRampToValueAtTime(0.08, t0 + 0.012);
    gain.gain.exponentialRampToValueAtTime(0.0001, t0 + seconds);
    osc.connect(gain); gain.connect(actx.destination);
    osc.start(t0); osc.stop(t0 + seconds + 0.02);
  } catch (e) { /* silence is acceptable */ }
}
function sfxTurn() { tone(520, 0.05, 'square', 0); }
function sfxWin() { tone(660, 0.09, 'sine', 0); tone(990, 0.12, 'sine', 0.1); }
function sfxLose() { tone(150, 0.2, 'sawtooth', 0); }
function sfxPick() { tone(440, 0.06, 'sine', 0); }
var levelIdx = 0, unlocked = loadInt(PROGRESS_KEY, 5);
var banked = 0, best = loadInt(BEST_KEY, 999999);
var board = null, movesLeft = 0, tries = 0, shown = 'start', spins = [];
function tileName(t) {
  if (t.kind === 'reactor') return 'reactor';
  if (t.kind === 'beacon') return 'beacon';
  if (t.wall) return 'blocked cell';
  return kindOf(t.base) + ' relay';
}
function show(name) {
  shown = name;
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
function drawLevels() {
  if (!levelList) return;
  while (levelList.firstChild) levelList.removeChild(levelList.firstChild);
  for (var i = 0; i < LEVELS.length; i += 1) {
    (function (n) {
      var b = document.createElement('button');
      b.type = 'button'; b.className = 'relay-level';
      b.setAttribute('data-level', String(n + 1));
      b.disabled = n > unlocked;
      b.textContent = 'Level ' + (n + 1) + (n > unlocked ? ' (locked)' : '');
      b.addEventListener('click', function () { startLevel(n, 0); });
      levelList.appendChild(b);
    })(i);
  }
}
function paint(focusRC) {
  while (boardNode.firstChild) boardNode.removeChild(boardNode.firstChild);
  var res = flow(board.tiles, board.size, board.row);
  boardNode.style.setProperty('--cols', String(board.size));
  for (var r = 0; r < board.size; r += 1) {
    for (var c = 0; c < board.size; c += 1) {
      (function (rr, cc) {
        var t = board.tiles[rr * board.size + cc];
        var b = document.createElement('button');
        b.type = 'button'; b.className = 'relay-tile';
        b.setAttribute('data-r', String(rr));
        b.setAttribute('data-c', String(cc));
        var ports = t.wall ? 0 : (t.kind === 'reactor' ? E : t.kind === 'beacon' ? W : rot(t.base, t.rot));
        var g = document.createElement('span');
        g.className = 'relay-glyph';
        g.textContent = t.wall ? '' : glyphFor(t.kind, ports);
        var spin = spins[rr * board.size + cc] || 0;
        g.style.setProperty('transform', 'rotate(' + (spin * 90) + 'deg)');
        b.appendChild(g);
        if (t.fixed) b.disabled = t.wall || t.kind === 'reactor' || t.kind === 'beacon';
        if (res.lit[rr * board.size + cc]) b.classList.add('lit');
        if (t.wall) b.classList.add('wall');
        if (t.kind === 'reactor' || t.kind === 'beacon') b.classList.add('relay-endpoint');
        b.setAttribute('aria-label', 'Row ' + (rr + 1) + ' column ' + (cc + 1) + ': ' +
          tileName(t) + (t.wall ? '' : res.lit[rr * board.size + cc] ? ', powered' : ', unpowered'));
        b.addEventListener('click', function () { turn(rr, cc); });
        boardNode.appendChild(b);
      })(r, c);
    }
  }
  setText(hud.level, String(levelIdx + 1) + ' / 6');
  setText(hud.moves, String(movesLeft));
  setText(hud.score, String(banked));
  setText(hud.best, String(best));
  if (focusRC) {
    var next = boardNode.querySelector('[data-r="' + focusRC[0] + '"][data-c="' + focusRC[1] + '"]:not([disabled])')
      || boardNode.querySelector('.relay-tile:not([disabled])');
    if (next) next.focus();
  }
}
function startLevel(n, attempt) {
  levelIdx = n; tries = attempt || 0;
  board = generate(n, tries);
  movesLeft = board.budget;
  spins = [];
  for (var i = 0; i < board.tiles.length; i += 1) spins.push(0);
  drawLevels();
  show(null);
  paint(null);
  announce('Level ' + (n + 1) + ': connect the reactor to the beacon. ' + movesLeft + ' moves.');
}
function turn(r, c) {
  if (shown || !board) return;
  var t = board.tiles[r * board.size + c];
  if (t.fixed) return;
  t.rot = (t.rot + 1) % 4;
  spins[r * board.size + c] += 1;
  movesLeft -= 1;
  sfxTurn();
  var res = flow(board.tiles, board.size, board.row);
  if (res.won) {
    var gained = movesLeft * 100 + (levelIdx + 1) * 250;
    banked += gained;
    if (banked > best) { best = banked; saveInt(BEST_KEY, best); }
    if (levelIdx < 5) {
      if (levelIdx + 1 > unlocked) { unlocked = levelIdx + 1; saveInt(PROGRESS_KEY, unlocked); }
      paint([r, c]);
      setText(stage.querySelector('[data-complete-text]'), 'Level ' + (levelIdx + 1) +
        ' linked with ' + movesLeft + ' moves to spare. Plus ' + gained + ' points.');
      show('complete');
      announce('Level ' + (levelIdx + 1) + ' complete. Plus ' + gained + ' points.');
    } else {
      if (5 > unlocked) { unlocked = 5; saveInt(PROGRESS_KEY, 5); }
      paint([r, c]);
      setText(stage.querySelector('[data-campaign-text]'), 'All six relays hum. Final score ' + banked + '.');
      show('campaign');
      announce('Campaign complete. Final score ' + banked + '.');
    }
    sfxWin();
    return;
  }
  if (movesLeft <= 0) {
    paint([r, c]);
    show('stuck');
    announce('Out of moves on level ' + (levelIdx + 1) + '. Retry for a fresh scramble.');
    sfxLose();
    return;
  }
  paint([r, c]);
}
function doAction(name) {
  sfxPick();
  if (name === 'start') startLevel(Math.min(unlocked, 5), 0);
  else if (name === 'pause') { if (!shown && board) { show('paused'); announce('Paused.'); } }
  else if (name === 'resume') { if (shown === 'paused') { show(null); announce('Resumed.'); } }
  else if (name === 'retry') startLevel(levelIdx, tries + 1);
  else if (name === 'next') startLevel(Math.min(levelIdx + 1, 5), 0);
  else if (name === 'again') { banked = 0; startLevel(0, 0); }
  else if (name === 'levels') { drawLevels(); show('levels'); }
  else if (name === 'close') show(board ? null : 'start');
  else if (name === 'mute') {
    muted = !muted;
    var m = stage.querySelector('[data-action="mute"]');
    if (m) { m.textContent = muted ? 'Unmute' : 'Mute'; m.setAttribute('aria-pressed', muted ? 'true' : 'false'); }
  }
  else if (name === 'motion') {
    var still = stage.classList.toggle('relay-still');
    if (motionBtn) {
      motionBtn.textContent = still ? 'Motion off' : 'Motion on';
      motionBtn.setAttribute('aria-pressed', still ? 'true' : 'false');
    }
  }
}
stage.addEventListener('click', function (ev) {
  var el = ev.target;
  while (el && el !== stage) {
    if (el.getAttribute && el.getAttribute('data-action')) { doAction(el.getAttribute('data-action')); return; }
    el = el.parentNode;
  }
});
document.addEventListener('keydown', function (ev) {
  var code = ev.code || ev.key;
  if (code === 'KeyM') { doAction('mute'); return; }
  if (code === 'KeyN') { if (board && !shown) startLevel(levelIdx, tries + 1); return; }
  if (code === 'KeyP' || code === 'Escape') {
    if (shown === 'paused') doAction('resume');
    else if (!shown && board) doAction('pause');
    else if (shown === 'levels') doAction('close');
    return;
  }
  var active = document.activeElement;
  var onTile = active && active.className && active.className.indexOf('relay-tile') !== -1;
  if (code === 'Enter' || code === 'Space') {
    if (active && active.tagName === 'BUTTON') return;
    if (shown === 'start') doAction('start');
    else if (shown === 'complete') doAction('next');
    else if (shown === 'stuck') doAction('retry');
    else if (shown === 'campaign') doAction('again');
    else if (shown === 'paused') doAction('resume');
    return;
  }
  if (code === 'KeyR' && onTile) {
    turn(parseInt(active.getAttribute('data-r'), 10), parseInt(active.getAttribute('data-c'), 10));
    return;
  }
  if (!onTile || shown) return;
  var r = parseInt(active.getAttribute('data-r'), 10);
  var c = parseInt(active.getAttribute('data-c'), 10);
  var size = board.size, nr = r, nc = c;
  if (code === 'ArrowUp') nr = (r + size - 1) % size;
  else if (code === 'ArrowDown') nr = (r + 1) % size;
  else if (code === 'ArrowLeft') nc = (c + size - 1) % size;
  else if (code === 'ArrowRight') nc = (c + 1) % size;
  else return;
  ev.preventDefault();
  var sel = '[data-r="' + nr + '"][data-c="' + nc + '"]';
  var dest = boardNode.querySelector(sel + ':not([disabled])') || boardNode.querySelector(sel);
  if (dest) dest.focus();
});
if (motionBtn) {
  var still0 = stage.classList.contains('relay-still');
  motionBtn.textContent = still0 ? 'Motion off' : 'Motion on';
  motionBtn.setAttribute('aria-pressed', still0 ? 'true' : 'false');
}
drawLevels();
paint(null);
show('start');
announce('Star Relay ready. Open the start panel to play.');
return api;
})();
if (typeof module !== 'undefined' && module.exports) module.exports = StarRelay;
