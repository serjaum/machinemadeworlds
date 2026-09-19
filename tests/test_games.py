"""Arcade presence gate (MAC-649/MAC-653). Run: python -m unittest discover -s tests -v."""
import importlib.util
import re
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mmw_games_build', ROOT / 'scripts/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class H1Counter(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.h1 = 0
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        if tag == 'h1':
            self.h1 += 1


class GamesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        builder.build(ROOT)
        cls.dist = ROOT / 'dist'
        cls.site = __import__('json').loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))
        cls.games = builder.load_games(ROOT)
        cls.index = (cls.dist / 'games/index.html').read_text(encoding='utf-8')
        cls.page = (cls.dist / 'games/star-drift/index.html').read_text(encoding='utf-8')

    def test_games_content_source_validates(self):
        import json
        import tempfile
        self.assertEqual(len(self.games), 1)
        game = self.games[0]
        self.assertEqual(game['slug'], 'star-drift')
        self.assertEqual(game['url'], '/games/star-drift/')
        self.assertTrue(game['pitch'].strip())
        self.assertTrue(game['devlog'].strip())
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / 'content/games'
            folder.mkdir(parents=True)
            (folder / 'Bad Slug.json').write_text(json.dumps({
                'title': 'Bad', 'description': 'Bad entry.',
                'pitch': 'Bad.', 'devlog': 'Bad.', 'date': '2026-09-19'}),
                encoding='utf-8')
            with self.assertRaises(ValueError):
                builder.load_games(Path(tmp))

    def test_routes_render_with_single_h1(self):
        for name, source in (('index', self.index), ('game', self.page)):
            self.assertEqual(H1Counter(source).h1, 1, name)
            self.assertIn('id="main"', source)
            self.assertIn('rel="canonical"', source)

    def test_index_lists_playable_card(self):
        self.assertIn('class="game-grid"', self.index)
        self.assertIn('class="game-card"', self.index)
        self.assertIn('href="/games/star-drift/"', self.index)
        self.assertIn('aria-current="page"', self.index)

    def test_game_page_structure_and_labels(self):
        self.assertIn('aria-label="Breadcrumb"', self.page)
        self.assertIn('id="howto-heading"', self.page)
        self.assertIn('<kbd>', self.page)
        self.assertIn('class="game-stage"', self.page)
        self.assertIn('class="game-hud"', self.page)
        self.assertIn('data-hud="score"', self.page)
        self.assertIn('data-hud="lives"', self.page)
        self.assertIn('data-hud="time"', self.page)
        self.assertIn('role="img"', self.page)
        self.assertIn('tabindex="0"', self.page)
        self.assertIn('aria-label="Star Drift playfield', self.page)
        self.assertIn('data-game="restart"', self.page)
        self.assertIn('data-game="pause"', self.page)
        self.assertIn('data-game="mute"', self.page)
        self.assertIn('role="status"', self.page)
        self.assertIn('aria-live="polite"', self.page)
        self.assertIn('<noscript>', self.page)
        self.assertIn('id="devlog-heading"', self.page)
        self.assertIn('<script src="/assets/star-drift.', self.page)
        self.assertIn('defer></script>', self.page)

    def test_nav_footer_sitemap_and_search_include_games(self):
        self.assertIn('href="/games/"', self.index)
        self.assertIn('href="/games/"', self.page)
        sitemap = (self.dist / 'sitemap.xml').read_text(encoding='utf-8')
        self.assertIn('<loc>https://machinemadeworlds.com/games/</loc>', sitemap)
        self.assertIn('<loc>https://machinemadeworlds.com/games/star-drift/</loc>', sitemap)
        search = (self.dist / 'search-index.json').read_text(encoding='utf-8')
        self.assertIn('/games/star-drift/', search)

    def test_weight_budgets(self):
        source = (ROOT / 'assets/star-drift.js').read_bytes()
        self.assertLessEqual(len(source), 15 * 1024)
        self.assertLess(len(self.page.encode('utf-8')), 60 * 1024)
        added = (self.dist / 'games/index.html').stat().st_size
        added += (self.dist / 'games/star-drift/index.html').stat().st_size
        added += sum(p.stat().st_size for p in (self.dist / 'assets').glob('star-drift.*.js'))
        self.assertLess(added, 120 * 1024)

    def test_token_only_styles_and_clean_script(self):
        css = (ROOT / 'assets/site.css').read_text(encoding='utf-8')
        block = css[css.index('/* Arcade (MAC-649).'):]
        self.assertNotRegex(block, r'#[0-9a-fA-F]{3,6}')
        self.assertNotIn('rgb(', block)
        self.assertNotIn('@import', block)
        self.assertNotIn('!important', block)
        self.assertNotIn('http', block)
        self.assertIn('@media print', block)
        js = (ROOT / 'assets/star-drift.js').read_text(encoding='utf-8')
        self.assertNotIn('innerHTML', js)
        self.assertNotIn('eval(', js)
        self.assertNotIn('http', js)
        self.assertIn("prefers-reduced-motion", js)
        self.assertIn("textContent", js)


if __name__ == '__main__':
    unittest.main()
