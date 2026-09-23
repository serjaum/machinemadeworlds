"""Star Relay arcade contract (MAC-700 parent spec sections 5-10, MAC-843 second pack).

Run: python -m pytest tests/test_games_arcade_star_relay.py -q
Gates: /games/star-relay/ renders the DOM-grid variant; zero external
URLs/imports/sinks in game files; JS <= 20KB and CSS <= 8KB unminified;
page weight (HTML+CSS+JS excl. shared chrome) <= 45KB; zero render work
idle (no RAF); pause/retry/level/mute hooks; reduced-motion branch plus
manual still toggle; single live region; 44px targets; sampled contrast
on real token pairs; all 12 levels plus the daily board solvable by
construction (node-driven generation test with a static fallback);
daily determinism (same UTC date, UTC seed math, no storage writes);
no secrets.
"""
import importlib.util
import json
import re
import shutil
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mmw_relay_build', ROOT / 'scripts/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

GAME_JS = ROOT / 'assets/games/star-relay.js'
GAME_CSS = ROOT / 'assets/games/star-relay.css'
GAME_JSON = ROOT / 'content/games/star-relay.json'
PROGRESS_KEY = 'mmw-star-relay-progress'
BEST_KEY = 'mmw-star-relay-best'

SITE_TOKENS = ('--bg', '--surface', '--raised', '--ink', '--muted', '--line',
               '--accent', '--accent-ink', '--art', '--art-line', '--art-core',
               '--art-ink', '--max', '--gutter', '--reading', '--s1', '--s2',
               '--s3', '--s4', '--s5', '--s6', '--serif', '--sans', '--mono')


def theme_tokens(source):
    light = dict(re.findall(r'(--[a-z-]+):\s*(#[0-9a-f]{6})',
                            source.split('[data-theme="dark"]')[0]))
    dark = dict(re.findall(r'(--[a-z-]+):\s*(#[0-9a-f]{6})',
                           source.split('[data-theme="dark"]')[1]))
    return light, dark


def luminance(hexcode):
    rgb = [int(hexcode[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    rgb = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def contrast(first, second):
    low, high = sorted([luminance(first), luminance(second)])
    return (high + 0.05) / (low + 0.05)


class TagCounter(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.h1 = 0
        self.status = 0
        self.live = 0
        self.canvas = []
        self.buttons = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'h1':
            self.h1 += 1
        if attrs.get('role') == 'status':
            self.status += 1
        if 'aria-live' in attrs:
            self.live += 1
        if tag == 'canvas':
            self.canvas.append(attrs)
        if tag == 'button':
            self.buttons.append(attrs)


class RelayRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        builder.build(ROOT)
        cls.page = (ROOT / 'dist/games/star-relay/index.html').read_text(encoding='utf-8')
        cls.tags = TagCounter(cls.page)

    def test_grid_variant_shell(self):
        self.assertEqual(self.tags.h1, 1)
        self.assertEqual(len(self.tags.canvas), 0)
        self.assertIn('data-relay-board', self.page)
        self.assertIn('role="group"', self.page)
        for hook in ('data-hud="level"', 'data-hud="moves"',
                     'data-hud="score"', 'data-hud="best"'):
            self.assertIn(hook, self.page)
        for action in ('start', 'pause', 'retry', 'levels', 'motion', 'mute',
                       'resume', 'next', 'again', 'close'):
            self.assertIn('data-action="%s"' % action, self.page)
        for panel in ('start', 'paused', 'complete', 'campaign', 'stuck', 'levels'):
            self.assertIn('data-overlay="%s"' % panel, self.page)
        self.assertIn('data-level-list', self.page)
        self.assertIn('data-complete-text', self.page)
        self.assertIn('data-campaign-text', self.page)
        self.assertIn('How to play', self.page)
        self.assertIn('Devlog', self.page)
        self.assertIn('no canvas, no animation loop, no timer', self.page)
        self.assertIn('Twelve relays in two packs', self.page)
        self.assertIn('All twelve relays hum', self.page)
        self.assertIn('1 / 12', self.page)
        self.assertIn('<noscript>', self.page)

    def test_single_live_region_outside_hud(self):
        self.assertEqual(self.tags.status, 1)
        self.assertEqual(self.tags.live, 0)
        hud = self.page[self.page.index('class="game-hud"'):self.page.index('</dl>')]
        self.assertNotIn('role="status"', hud)
        self.assertNotIn('aria-live', hud)

    def test_all_controls_are_native_buttons(self):
        self.assertGreaterEqual(len(self.tags.buttons), 17)
        for attrs in self.tags.buttons:
            self.assertEqual(attrs.get('type'), 'button')

    def test_sitemap_lists_relay_route(self):
        sitemap = (ROOT / 'dist/sitemap.xml').read_text(encoding='utf-8')
        self.assertIn('<loc>https://machinemadeworlds.com/games/star-relay/</loc>', sitemap)


class RelaySourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.js = GAME_JS.read_text(encoding='utf-8')
        cls.css = GAME_CSS.read_text(encoding='utf-8')
        cls.site_css = (ROOT / 'assets/site.css').read_text(encoding='utf-8')

    def test_zero_external_urls_imports_and_sinks(self):
        for name, source in (('relay js', self.js), ('relay css', self.css)):
            lowered = source.lower()
            self.assertNotIn('http', lowered, name)
            self.assertNotIn('import', lowered, name)
            self.assertNotIn('fetch(', lowered, name)
            self.assertNotIn('xmlhttprequest', lowered, name)
            self.assertNotIn('websocket', lowered, name)
            self.assertNotIn('@import', source, name)
            self.assertNotIn('url(', lowered, name)
        self.assertNotIn('innerHTML', self.js)
        self.assertNotIn('eval(', self.js)
        self.assertNotIn('document.write', self.js)

    def test_zero_render_work_idle(self):
        self.assertNotIn('requestAnimationFrame', self.js)
        self.assertNotIn('setInterval', self.js)
        self.assertNotIn('setTimeout', self.js)

    def test_flow_input_and_audio_hooks(self):
        for hook in ('data-relay-board', 'data-hud="level"', 'data-hud="moves"',
                     'data-hud="score"', 'data-hud="best"', 'data-action',
                     'data-overlay', 'data-level-list'):
            self.assertIn(hook, self.js)
        for action in ("'pause'", "'retry'", "'levels'", "'motion'",
                        "'start'", "'mute'", "'resume'", "'next'", "'again'",
                        "'close'", "'daily'"):
            self.assertIn(action, self.js)
        for key in ('ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight',
                    'KeyR', 'KeyP', 'KeyM', 'KeyN', 'KeyD', 'Escape', 'Enter', 'Space'):
            self.assertIn(key, self.js)
        self.assertIn('AudioContext', self.js)
        self.assertIn('textContent', self.js)

    def test_progress_storage_is_namespaced_integer_only(self):
        for key in (PROGRESS_KEY, BEST_KEY):
            self.assertIn(key, self.js)
        self.assertIn('parseInt', self.js)
        self.assertIn('localStorage', self.js)
        self.assertIn('try', self.js)

    def test_reduced_motion_branch_plus_manual_still(self):
        self.assertIn('prefers-reduced-motion', self.js)
        self.assertIn('matchMedia', self.js)
        self.assertIn('relay-still', self.js)
        self.assertIn('prefers-reduced-motion', self.css)
        self.assertNotIn('@keyframes', self.css)
        self.assertNotIn('animation', self.css)

    def test_solvable_by_construction_markers(self):
        for marker in ('buildPath', 'scramble', 'flow(', 'fixCost', 'optimal', 'budget'):
            self.assertIn(marker, self.js)
        self.assertIn('LEVELS', self.js)

    def test_no_secrets_in_game_files(self):
        for name, source in (('relay js', self.js), ('relay css', self.css),
                             ('relay json', GAME_JSON.read_text(encoding='utf-8'))):
            lowered = source.lower()
            for marker in ('api_key', 'apikey', 'password', 'private key',
                           'github_pat_', 'ghp_', 'bearer '):
                self.assertNotIn(marker, lowered, name)

    def test_css_is_semantic_vars_only(self):
        self.assertNotRegex(self.css, r'#[0-9a-fA-F]{3,8}')
        self.assertNotIn('!important', self.css)
        for token in re.findall(r'var\((--[a-z0-9-]+)\)', self.css):
            self.assertIn(token, SITE_TOKENS, token)
        self.assertIn('touch-action: manipulation', self.css)
        self.assertIn('@media (prefers-reduced-motion: no-preference)', self.css)
        self.assertIn('@media (max-width: 700px)', self.css)

    def test_targets_stay_44px(self):
        self.assertIn('min-height: 44px', self.css)
        self.assertIn('min-height: 52px', self.css)
        self.assertIn('min-width: 48px', self.css)

    def test_metadata_levels_match_script(self):
        meta = json.loads(GAME_JSON.read_text(encoding='utf-8'))
        self.assertEqual(len(meta['levels']), 12)
        block = re.search(r'var LEVELS=\[(.*?)\];', self.js, re.S).group(1)
        script_levels = re.findall(r'\[(\d+),(\d+),(\d+),(\d+)\]', block)
        self.assertEqual(len(script_levels), 12)
        for (size, slack, tees, walls), level in zip(script_levels, meta['levels']):
            self.assertEqual(
                (int(size), int(slack), int(tees), int(walls)),
                (level['size'], level['slack'], level['tees'], level['walls']))
        expected = [(4, 4, 0, 0), (4, 4, 1, 0), (5, 6, 1, 2), (5, 6, 2, 3),
                    (5, 8, 2, 4), (5, 8, 3, 5), (6, 10, 3, 5), (6, 10, 3, 6),
                    (6, 12, 4, 7), (6, 12, 4, 8), (6, 12, 5, 8), (6, 14, 5, 9)]
        self.assertEqual([(l['size'], l['slack'], l['tees'], l['walls'])
                          for l in meta['levels']], expected)

    def test_second_pack_daily_and_progress_gates(self):
        self.assertIn('dailySeedUTC', self.js)
        self.assertIn('generateDaily', self.js)
        self.assertIn('getUTCFullYear', self.js)
        self.assertIn('Relay I', self.js)
        self.assertIn('Relay II', self.js)
        self.assertIn('relay-group', (ROOT / 'assets/games/star-relay.css').read_text(encoding='utf-8'))
        self.assertIn('/ 12', self.js)
        self.assertIn('Daily', self.js)
        self.assertIn('All twelve relays hum', self.js)
        self.assertIn('LEVELS.length - 1', self.js)
        self.assertRegex(self.js, r'var DAILY=\[6,12,4,7\];')
        for fname, end in (('function generateDaily', 'function flow'),
                           ('function startDaily', 'function turn')):
            chunk = self.js.split(fname)[1].split(end)[0]
            for marker in ('PROGRESS_KEY', 'BEST_KEY', 'saveInt', 'unlocked', 'banked'):
                self.assertNotIn(marker, chunk, fname)


class RelayBudgetTests(unittest.TestCase):
    def test_js_within_20kb(self):
        self.assertLessEqual(GAME_JS.stat().st_size, 20 * 1024)

    def test_css_within_8kb(self):
        self.assertLessEqual(GAME_CSS.stat().st_size, 8 * 1024)

    def test_page_weight_within_45kb_excl_chrome(self):
        page_path = ROOT / 'dist/games/star-relay/index.html'
        html = page_path.read_bytes()
        refs = set(re.findall(rb'(?:href|src)="(/assets/[^"]+)"', html))
        relay_refs = [ref for ref in refs if b'star-relay.' in ref]
        self.assertTrue(relay_refs)
        game_bytes = sum((ROOT / 'dist' / ref.decode('ascii').lstrip('/')).stat().st_size
                         for ref in relay_refs)
        self.assertLess(len(html) + game_bytes, 45 * 1024)


class RelayContrastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        site_css = (ROOT / 'assets/site.css').read_text(encoding='utf-8')
        cls.light, cls.dark = theme_tokens(site_css)

    def test_lit_and_hud_pairs_in_both_themes(self):
        for name, theme in (('light', self.light), ('dark', self.dark)):
            self.assertGreaterEqual(contrast(theme['--accent'], theme['--accent-ink']), 4.5, name)
            self.assertGreaterEqual(contrast(theme['--ink'], theme['--raised']), 4.5, name)
            self.assertGreaterEqual(contrast(theme['--muted'], theme['--surface']), 4.5, name)


class RelaySolvabilityTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'node is required for the generation gate')
    def test_all_twelve_levels_and_daily_solvable_by_construction(self):
        harness = (
            "const R = require(%s);" % json.dumps(str(GAME_JS)) +
            "if (R.LEVELS.length !== 12) throw new Error('level count ' + R.LEVELS.length);"
            "for (let L = 0; L < 12; L++) {"
            "  for (let a = 0; a < 6; a++) {"
            "    const g = R.generate(L, a);"
            "    if (R.flow(g.tiles, g.size, g.row).won) throw new Error('pre-solved L' + L);"
            "    const fixed = g.tiles.map((t, i) => Object.assign({}, t,"
            "      { rot: (t.rot + R.fixCost(t.base, t.rot, g.home[i])) % 4 }));"
            "    if (!R.flow(fixed, g.size, g.row).won) throw new Error('unsolvable L' + L);"
            "    if (g.budget !== g.optimal + g.slack) throw new Error('budget L' + L);"
            "  }"
            "}"
            "if (R.dailySeedUTC(new Date(Date.UTC(2026, 8, 23))) !== 20260923)"
            "  throw new Error('daily seed math');"
            "const dA = R.generateDaily('2026-09-23', 0);"
            "const dB = R.generateDaily(20260923, 0);"
            "if (!dA.daily || dA.seed !== 20260923) throw new Error('daily flags');"
            "if (JSON.stringify(dA.tiles) !== JSON.stringify(dB.tiles))"
            "  throw new Error('daily string/int seed parity');"
            "for (let a = 0; a < 6; a++) {"
            "  const g = R.generateDaily('2026-09-23', a);"
            "  const h = R.generateDaily('2026-09-23', a);"
            "  if (JSON.stringify(g.tiles) !== JSON.stringify(h.tiles))"
            "    throw new Error('daily determinism a' + a);"
            "  if (g.size !== 6 || g.slack !== 12) throw new Error('daily spec');"
            "  if (R.flow(g.tiles, g.size, g.row).won) throw new Error('daily pre-solved');"
            "  const fixed = g.tiles.map((t, i) => Object.assign({}, t,"
            "    { rot: (t.rot + R.fixCost(t.base, t.rot, g.home[i])) % 4 }));"
            "  if (!R.flow(fixed, g.size, g.row).won) throw new Error('daily unsolvable');"
            "  if (g.budget !== g.optimal + g.slack) throw new Error('daily budget');"
            "}"
            "const dX = R.generateDaily('2026-09-24', 0);"
            "if (JSON.stringify(dX.tiles) === JSON.stringify(dA.tiles))"
            "  throw new Error('daily does not vary by date');"
            "console.log('SOLVABILITY OK');"
        )
        proc = subprocess.run(['node', '-e', harness], capture_output=True,
                              text=True, timeout=180)
        self.assertEqual(proc.returncode, 0, proc.stderr[-2000:])
        self.assertIn('SOLVABILITY OK', proc.stdout)


class RelayIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        builder.build(ROOT)

    def test_relay_strings_stay_in_carriers(self):
        carriers = {'index.html',
                    'games/index.html',
                    'games/star-harvest/index.html',
                    'games/star-relay/index.html',
                    'games/star-drift/index.html',
                    'sitemap.xml',
                    'metrics/index.html',
                    'llms.txt',
                    'llms-full.txt'}
        for path in sorted((ROOT / 'dist').rglob('*')):
            if not path.is_file() or path.suffix not in ('.html', '.txt', '.xml', '.json'):
                continue
            rel = path.relative_to(ROOT / 'dist').as_posix()
            if rel in carriers or rel.startswith('build-log/'):
                continue
            source = path.read_text(encoding='utf-8')
            self.assertNotIn('star-relay', source.lower(), rel)

    def test_relay_game_accepted_by_loader(self):
        games = builder.load_games(ROOT)
        slugs = [g['slug'] for g in games]
        self.assertEqual(sorted(slugs), ['star-drift', 'star-harvest', 'star-relay'])


if __name__ == '__main__':
    unittest.main()
