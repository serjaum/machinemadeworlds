"""Star Chime arcade contract (MAC-756 parent spec sections 5-8).

Run: python -m pytest tests/test_games_arcade_star_chime.py -q
Gates: /games/star-chime/ renders the audio-first memory variant; zero
external URLs/imports/sinks in game files; JS <= 20KB and CSS <= 8KB
unminified; page weight (HTML+CSS+JS excl. shared chrome) <= 45KB;
timer-only playback idle (setTimeout, no RAF, no intervals);
start/pause/replay/hint/mute hooks; reduced-motion branch; single live
region; 48px targets; sampled contrast on real token pairs; all 12
rounds winnable by construction (node-driven generation test);
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
spec = importlib.util.spec_from_file_location('mmw_chime_build', ROOT / 'scripts/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

GAME_JS = ROOT / 'assets/games/star-chime.js'
GAME_CSS = ROOT / 'assets/games/star-chime.css'
GAME_JSON = ROOT / 'content/games/star-chime.json'
BEST_KEY = 'mmw.star-chime.best.v1'

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


class ChimeRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        builder.build(ROOT)
        cls.page = (ROOT / 'dist/games/star-chime/index.html').read_text(encoding='utf-8')
        cls.tags = TagCounter(cls.page)

    def test_pads_and_hud_shell(self):
        self.assertEqual(self.tags.h1, 1)
        self.assertEqual(len(self.tags.canvas), 0)
        self.assertIn('data-chime-pads', self.page)
        self.assertIn('role="group"', self.page)
        for pad in ('data-pad="1"', 'data-pad="2"', 'data-pad="3"', 'data-pad="4"'):
            self.assertIn(pad, self.page)
        for hook in ('data-hud="round"', 'data-hud="score"',
                     'data-hud="lives"', 'data-hud="best"'):
            self.assertIn(hook, self.page)
        for action in ('start', 'pause', 'replay', 'hint', 'mute', 'resume'):
            self.assertIn('data-action="%s"' % action, self.page)
        for panel in ('start', 'paused', 'complete', 'victory'):
            self.assertIn('data-overlay="%s"' % panel, self.page)
        self.assertIn('data-complete-text', self.page)
        self.assertIn('data-victory-text', self.page)
        self.assertIn('How to play', self.page)
        self.assertIn('Devlog', self.page)
        self.assertIn('state machine', self.page)
        self.assertIn('<noscript>', self.page)

    def test_single_live_region_outside_hud(self):
        self.assertEqual(self.tags.status, 1)
        self.assertEqual(self.tags.live, 0)
        hud = self.page[self.page.index('class="game-hud"'):self.page.index('</dl>')]
        self.assertNotIn('role="status"', hud)
        self.assertNotIn('aria-live', hud)

    def test_all_controls_are_native_buttons(self):
        self.assertGreaterEqual(len(self.tags.buttons), 14)
        for attrs in self.tags.buttons:
            self.assertEqual(attrs.get('type'), 'button')

    def test_sitemap_lists_chime_route(self):
        sitemap = (ROOT / 'dist/sitemap.xml').read_text(encoding='utf-8')
        self.assertIn('<loc>https://machinemadeworlds.com/games/star-chime/</loc>', sitemap)

    def test_index_lists_fourth_game_with_note(self):
        index = (ROOT / 'dist/games/index.html').read_text(encoding='utf-8')
        self.assertIn('<a href="/games/star-chime/">Star Chime</a>', index)
        self.assertIn('More games coming.', index)


class ChimeSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.js = GAME_JS.read_text(encoding='utf-8')
        cls.css = GAME_CSS.read_text(encoding='utf-8')
        cls.site_css = (ROOT / 'assets/site.css').read_text(encoding='utf-8')

    def test_zero_external_urls_imports_and_sinks(self):
        for name, source in (('chime js', self.js), ('chime css', self.css)):
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

    def test_timer_only_playback_idle(self):
        self.assertIn('setTimeout', self.js)
        self.assertNotIn('requestAnimationFrame', self.js)
        self.assertNotIn('setInterval', self.js)

    def test_flow_input_and_audio_hooks(self):
        for hook in ('data-chime-pads', 'data-hud="round"', 'data-hud="score"',
                     'data-hud="lives"', 'data-hud="best"', 'data-action',
                     'data-overlay', 'data-pad'):
            self.assertIn(hook, self.js)
        for action in ("'pause'", "'replay'", "'hint'",
                       "'start'", "'mute'", "'resume'"):
            self.assertIn(action, self.js)
        for key in ('Enter', 'Digit1', 'Digit2', 'Digit3', 'Digit4',
                    'KeyP', 'KeyH', 'KeyM', 'Escape'):
            self.assertIn(key, self.js)
        for state in ("'idle'", "'showing'", "'input'", "'round-clear'",
                      "'mistake'", "'gameover'", "'victory'"):
            self.assertIn(state, self.js)
        self.assertIn('AudioContext', self.js)
        self.assertIn('textContent', self.js)

    def test_timing_constants_and_rules(self):
        for marker in ('WIN_ROUNDS', 'MAX_LIVES = 3', 'MAX_HINTS = 2',
                       '450', '250', '280', '0.95'):
            self.assertIn(marker, self.js)
        self.assertIn('12', self.js)

    def test_best_storage_is_namespaced_integer_only(self):
        self.assertIn(BEST_KEY, self.js)
        self.assertIn('parseInt', self.js)
        self.assertIn('localStorage', self.js)
        self.assertIn('try', self.js)

    def test_reduced_motion_branch_without_motion_css(self):
        self.assertIn('prefers-reduced-motion', self.js)
        self.assertIn('matchMedia', self.js)
        self.assertIn('chime-still', self.js)
        self.assertIn('prefers-reduced-motion', self.css)
        self.assertNotIn('@keyframes', self.css)
        self.assertNotIn('animation', self.css)
        self.assertNotIn('transition', self.css)

    def test_no_secrets_in_game_files(self):
        for name, source in (('chime js', self.js), ('chime css', self.css),
                             ('chime json', GAME_JSON.read_text(encoding='utf-8'))):
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
        self.assertIn('@media (pointer: coarse)', self.css)
        self.assertIn('@media (max-width: 700px)', self.css)

    def test_targets_stay_48px(self):
        self.assertIn('min-width: 48px', self.css)
        self.assertIn('min-height: 88px', self.css)
        self.assertIn('min-height: 48px', self.css)

    def test_metadata_matches_brief(self):
        meta = json.loads(GAME_JSON.read_text(encoding='utf-8'))
        self.assertEqual(meta['format'], 'Turn-based memory')
        self.assertEqual(meta['playtime'], '5 min play')
        self.assertLessEqual(len(meta['title']), 80)
        self.assertNotIn('http', meta['pitch'])


class ChimeBudgetTests(unittest.TestCase):
    def test_js_within_20kb(self):
        self.assertLessEqual(GAME_JS.stat().st_size, 20 * 1024)

    def test_css_within_8kb(self):
        self.assertLessEqual(GAME_CSS.stat().st_size, 8 * 1024)

    def test_page_weight_within_45kb_excl_chrome(self):
        page_path = ROOT / 'dist/games/star-chime/index.html'
        html = page_path.read_bytes()
        refs = set(re.findall(rb'(?:href|src)="(/assets/[^"]+)"', html))
        chime_refs = [ref for ref in refs if b'star-chime.' in ref]
        self.assertTrue(chime_refs)
        game_bytes = sum((ROOT / 'dist' / ref.decode('ascii').lstrip('/')).stat().st_size
                         for ref in chime_refs)
        self.assertLess(len(html) + game_bytes, 45 * 1024)


class ChimeContrastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        site_css = (ROOT / 'assets/site.css').read_text(encoding='utf-8')
        cls.light, cls.dark = theme_tokens(site_css)

    def test_lit_and_hud_pairs_in_both_themes(self):
        for name, theme in (('light', self.light), ('dark', self.dark)):
            self.assertGreaterEqual(contrast(theme['--accent'], theme['--accent-ink']), 4.5, name)
            self.assertGreaterEqual(contrast(theme['--ink'], theme['--raised']), 4.5, name)
            self.assertGreaterEqual(contrast(theme['--muted'], theme['--surface']), 4.5, name)


class ChimeWinnabilityTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'node is required for the generation gate')
    def test_all_twelve_rounds_winnable_by_construction(self):
        harness = (
            "const C = require(%s);" % json.dumps(str(GAME_JS)) +
            "if (C.WIN_ROUNDS !== 12) throw new Error('win rounds');"
            "if (C.MAX_LIVES !== 3) throw new Error('lives');"
            "if (C.MAX_HINTS !== 2) throw new Error('hints');"
            "if (C.flashMs(1) !== 450) throw new Error('base flash');"
            "if (C.gapMs(1) !== 250) throw new Error('base gap');"
            "let total = 0;"
            "for (let r = 1; r <= C.WIN_ROUNDS; r++) {"
            "  const len = C.roundLen(r);"
            "  if (len !== r + 2) throw new Error('length r' + r);"
            "  const seq = C.buildRound(1000 + r, len);"
            "  if (seq.length !== len) throw new Error('seq r' + r);"
            "  for (const pad of seq) {"
            "    if (pad < 1 || pad > 4) throw new Error('pad range r' + r);"
            "    total += 1;"
            "  }"
            "  if (r > 1 && C.flashMs(r) > C.flashMs(r - 1)) throw new Error('quicken r' + r);"
            "}"
            "if (C.flashMs(500) !== 280) throw new Error('flash floor');"
            "if (total !== 102) throw new Error('score ' + total);"
            "console.log('WINNABILITY OK');"
        )
        proc = subprocess.run(['node', '-e', harness], capture_output=True,
                              text=True, timeout=120)
        self.assertEqual(proc.returncode, 0, proc.stderr[-2000:])
        self.assertIn('WINNABILITY OK', proc.stdout)


class ChimeIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        builder.build(ROOT)

    def test_chime_strings_stay_in_carriers(self):
        carriers = {'index.html',
                    'games/index.html',
                    'games/star-harvest/index.html',
                    'games/star-relay/index.html',
                    'games/star-drift/index.html',
                    'games/star-chime/index.html',
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
            self.assertNotIn('star-chime', source.lower(), rel)

    def test_chime_game_accepted_by_loader(self):
        games = builder.load_games(ROOT)
        slugs = [g['slug'] for g in games]
        self.assertIn('star-chime', slugs)


if __name__ == '__main__':
    unittest.main()
