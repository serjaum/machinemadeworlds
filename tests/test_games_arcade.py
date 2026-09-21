"""Star Harvest arcade contract (MAC-648 brief section 6 + parent spec section 8).

Run: python -m pytest tests/test_games_arcade.py -q
Gates: both routes render; zero external URLs/imports in game files;
JS+CSS <= 60KB and game page first load <= 150KB; pause/restart/score
hooks; reduced-motion branch; single live region; 44px targets;
sampled contrast on real token pairs; no secrets.
"""
import importlib.util
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mmw_games_build', ROOT / 'scripts/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

GAME_JS = ROOT / 'assets/games/star-harvest.js'
GAME_CSS = ROOT / 'assets/games/star-harvest.css'
BEST_KEY = 'mmw.star-harvest.best.v1'

SITE_TOKENS = ('--bg', '--surface', '--raised', '--ink', '--muted', '--line',
               '--accent', '--accent-ink', '--art', '--art-line', '--art-core',
               '--art-ink', '--max', '--gutter', '--reading', '--s1', '--s2',
               '--s3', '--s4', '--s5', '--s6', '--serif', '--sans', '--mono')
JS_TOKENS = ('--accent', '--ink', '--raised')


def theme_tokens(source):
    """Hex palette per theme parsed from the committed stylesheet."""
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


class ArcadeRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        builder.build(ROOT)
        cls.index = (ROOT / 'dist/games/index.html').read_text(encoding='utf-8')
        cls.page = (ROOT / 'dist/games/star-harvest/index.html').read_text(encoding='utf-8')
        cls.tags = TagCounter(cls.page)

    def test_index_lists_game_with_more_coming_note(self):
        self.assertEqual(self.index.count('<article class="story"'), 4)
        self.assertIn('<a href="/games/star-harvest/">Star Harvest</a>', self.index)
        self.assertIn('<a href="/games/star-relay/">Star Relay</a>', self.index)
        self.assertIn('<a href="/games/star-drift/">Star Drift</a>', self.index)
        self.assertIn('<a href="/games/star-chime/">Star Chime</a>', self.index)
        self.assertIn('More games coming.', self.index)
        self.assertIn('class="callout game-note"', self.index)
        self.assertIn('<title>The arcade', self.index)

    def test_game_page_shell_matches_brief(self):
        self.assertEqual(self.tags.h1, 1)
        self.assertEqual(len(self.tags.canvas), 1)
        canvas = self.tags.canvas[0]
        self.assertEqual(canvas.get('id'), 'star-harvest')
        self.assertEqual(canvas.get('role'), 'img')
        self.assertIn('aria-label', canvas)
        for hook in ('data-hud="score"', 'data-hud="time"', 'data-hud="lives"',
                     'data-hud="combo"', 'data-hud="best"'):
            self.assertIn(hook, self.page)
        for action in ('start', 'pause', 'restart', 'mute'):
            self.assertIn('data-action="%s"' % action, self.page)
        self.assertIn('data-hint', self.page)
        self.assertIn('data-pad', self.page)
        self.assertIn('How to play', self.page)
        self.assertIn('Devlog', self.page)
        self.assertIn('Star Harvest draws every sprite procedurally', self.page)

    def test_single_live_region_outside_hud(self):
        self.assertEqual(self.tags.status, 1)
        self.assertEqual(self.tags.live, 0)
        hud = self.page[self.page.index('class="game-hud"'):self.page.index('</dl>')]
        self.assertNotIn('role="status"', hud)
        self.assertNotIn('aria-live', hud)

    def test_all_controls_are_native_buttons(self):
        self.assertGreaterEqual(len(self.tags.buttons), 8)
        for attrs in self.tags.buttons:
            self.assertEqual(attrs.get('type'), 'button')

    def test_nav_surfaces_arcade(self):
        base = (ROOT / 'templates/base.html').read_text(encoding='utf-8')
        nav = base[base.index('<nav class="navigation"'):base.index('</nav>')]
        self.assertIn('<a href="/games/" $games_current>Arcade</a', nav)
        footer = base[base.index('<nav aria-label="Footer">'):base.index('</nav>', base.index('<nav aria-label="Footer">'))]
        self.assertIn('<a href="/games/">Arcade</a>', footer)
        self.assertEqual(base.count('$extra_js'), 1)

    def test_sitemap_lists_arcade_routes(self):
        sitemap = (ROOT / 'dist/sitemap.xml').read_text(encoding='utf-8')
        self.assertIn('<loc>https://machinemadeworlds.com/games/</loc>', sitemap)
        self.assertIn('<loc>https://machinemadeworlds.com/games/star-harvest/</loc>', sitemap)


class GameSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.js = GAME_JS.read_text(encoding='utf-8')
        cls.css = GAME_CSS.read_text(encoding='utf-8')
        cls.site_css = (ROOT / 'assets/site.css').read_text(encoding='utf-8')

    def test_zero_external_urls_imports_and_sinks(self):
        for name, source in (('game js', self.js), ('game css', self.css)):
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

    def test_pause_restart_score_hooks(self):
        for hook in ('data-hud="score"', 'data-hud="time"', 'data-hud="lives"',
                     'data-hud="combo"', 'data-hud="best"',
                     'data-action="pause"', 'data-action="restart"',
                     'data-action="start"', 'data-action="mute"', 'data-dir'):
            self.assertIn(hook, self.js)
        for key in ('Enter', 'KeyP', 'Escape', 'KeyM', 'ArrowLeft', 'KeyW'):
            self.assertIn(key, self.js)
        self.assertIn('requestAnimationFrame', self.js)
        self.assertIn('textContent', self.js)

    def test_best_score_storage_is_namespaced_integer_only(self):
        self.assertIn(BEST_KEY, self.js)
        self.assertIn('parseInt', self.js)
        self.assertIn('localStorage', self.js)
        self.assertIn('try', self.js)

    def test_reduced_motion_branch_kills_startle(self):
        self.assertIn('prefers-reduced-motion', self.js)
        self.assertIn('matchMedia', self.js)
        for gate in ('reduceMotion',):
            self.assertIn(gate, self.js)
        self.assertIn('if (reduceMotion) return', self.js)
        self.assertNotIn('animation', self.css)
        self.assertNotIn('@keyframes', self.css)
        self.assertNotIn('transition', self.css)

    def test_loop_budget_construction(self):
        self.assertIn('PARTICLE_CAP', self.js)
        self.assertIn('0.05', self.js)
        self.assertIn('COMBO_WINDOW', self.js)
        self.assertIn('2.5', self.js)
        self.assertIn('MAX_LIVES = 3', self.js)
        self.assertIn('RUN_SECONDS = 90', self.js)

    def test_palette_comes_from_computed_tokens(self):
        self.assertIn('getComputedStyle', self.js)
        for token in JS_TOKENS:
            self.assertIn(token, self.js)
        # Offline-safe initializer only: every other canvas color resolves
        # from computed site tokens at boot, never from literals.
        hexes = set(re.findall(r'#[0-9a-fA-F]{6}', self.js))
        self.assertLessEqual(hexes, {'#ffffff', '#000000'})

    def test_css_is_semantic_vars_only(self):
        self.assertNotRegex(self.css, r'#[0-9a-fA-F]{3,8}')
        self.assertNotIn('!important', self.css)
        for token in re.findall(r'var\((--[a-z0-9-]+)\)', self.css):
            self.assertIn(token, SITE_TOKENS, token)
        self.assertIn('touch-action: pan-y', self.css)
        self.assertIn('@media (pointer: coarse)', self.css)
        self.assertIn('@media (max-width: 700px)', self.css)

    def test_targets_stay_44px(self):
        self.assertIn('48px', self.css)
        match = re.search(r'\.button \{([^}]*)\}', self.site_css)
        self.assertIsNotNone(match)
        self.assertIn('min-height: 48px', match[1])

    def test_no_secrets_in_game_files(self):
        for name, source in (('game js', self.js), ('game css', self.css)):
            lowered = source.lower()
            for marker in ('api_key', 'apikey', 'password', 'private key',
                           'github_pat_', 'ghp_', 'bearer '):
                self.assertNotIn(marker, lowered, name)

    def test_legacy_storage_key_absent(self):
        tree = [GAME_JS, GAME_CSS, ROOT / 'templates/game.html',
                ROOT / 'templates/games-index.html',
                ROOT / 'content/games/star-harvest.json']
        for path in tree:
            self.assertNotIn('mmw-star-harvest-best', path.read_text(encoding='utf-8'), str(path))


class ArcadeBudgetTests(unittest.TestCase):
    def test_js_plus_css_within_60kb(self):
        total = GAME_JS.stat().st_size + GAME_CSS.stat().st_size
        self.assertLessEqual(total, 60 * 1024)

    def test_game_page_first_load_within_150kb(self):
        page_path = ROOT / 'dist/games/star-harvest/index.html'
        html = page_path.read_bytes()
        refs = set(re.findall(rb'(?:href|src)="(/assets/[^"]+)"', html))
        total = len(html) + sum((ROOT / 'dist' / ref.decode('ascii').lstrip('/')).stat().st_size
                                for ref in refs)
        self.assertLess(total, 150 * 1024)


class ArcadeContrastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        site_css = (ROOT / 'assets/site.css').read_text(encoding='utf-8')
        cls.light, cls.dark = theme_tokens(site_css)

    def test_star_and_edge_beat_face_in_both_themes(self):
        for name, theme in (('light', self.light), ('dark', self.dark)):
            self.assertGreaterEqual(contrast(theme['--accent'], theme['--raised']), 3.0, name)
            self.assertGreaterEqual(contrast(theme['--ink'], theme['--raised']), 3.0, name)

    def test_hud_text_is_aa_in_both_themes(self):
        for name, theme in (('light', self.light), ('dark', self.dark)):
            self.assertGreaterEqual(contrast(theme['--ink'], theme['--raised']), 4.5, name)
            self.assertGreaterEqual(contrast(theme['--muted'], theme['--surface']), 4.5, name)


class ArcadeIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        builder.build(ROOT)

    def test_game_strings_stay_in_carriers(self):
        # New build-log entries surface in sibling related grids by design,
        # so every build-log page may carry the arcade title and link.
        # The journal, topics, glossary, data pages and feeds stay clean.
        carriers = {'index.html',
                    'about/index.html',
                    'games/index.html',
                    'games/star-harvest/index.html',
                    'games/star-relay/index.html',
                    'games/star-drift/index.html',
                    'games/star-chime/index.html',
                    'games/star-relay/index.html',
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
            self.assertNotIn('star-harvest', source.lower(), rel)

    def test_homepage_surfaces_arcade(self):
        home = (ROOT / 'dist/index.html').read_text(encoding='utf-8')
        self.assertIn('data-od-id="arcade"', home)
        self.assertIn('href="/games/"', home)
        self.assertIn('Play in the arcade', home)
        for slug in ('star-harvest', 'star-drift', 'star-relay', 'star-chime'):
            self.assertIn('/games/%s/' % slug, home)
        self.assertIn('/games/', home)


class GameValidationTests(unittest.TestCase):
    def test_load_games_accepts_family_file(self):
        site = json.loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))
        games = builder.load_games(ROOT)
        slugs = [g['slug'] for g in games]
        self.assertIn('star-harvest', slugs)
        game = next(g for g in games if g['slug'] == 'star-harvest')
        self.assertTrue(game['url'].startswith('/games/'))
        self.assertIn('date_label', game)

    def test_load_games_rejects_bad_metadata(self):
        site = json.loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))
        good = json.loads((ROOT / 'content/games/star-harvest.json').read_text(encoding='utf-8'))
        import tempfile as temp_module
        with temp_module.TemporaryDirectory() as tmp:
            folder = Path(tmp) / 'content' / 'games'
            folder.mkdir(parents=True)
            (folder / 'star-harvest.json').write_text(json.dumps(good), encoding='utf-8')
            self.assertEqual(len(builder.load_games(Path(tmp))), 1)
            bad = dict(good, title='x' * 81)
            (folder / 'star-harvest.json').write_text(json.dumps(bad), encoding='utf-8')
            with self.assertRaises(ValueError):
                builder.load_games(Path(tmp))
            bad = dict(good, pitch='see https://example.com for more')
            (folder / 'star-harvest.json').write_text(json.dumps(bad), encoding='utf-8')
            with self.assertRaises(ValueError):
                builder.load_games(Path(tmp))

    def test_unknown_game_slug_fails_fast(self):
        import tempfile as temp_module
        good = json.loads((ROOT / 'content/games/star-harvest.json').read_text(encoding='utf-8'))
        with temp_module.TemporaryDirectory() as tmp:
            target = Path(tmp)
            for name in ('content', 'templates', 'assets'):
                import shutil
                shutil.copytree(ROOT / name, target / name)
            (target / 'content/games/mystery.json').write_text(json.dumps(good), encoding='utf-8')
            with self.assertRaises(ValueError):
                builder.build(target)


if __name__ == '__main__':
    unittest.main()
