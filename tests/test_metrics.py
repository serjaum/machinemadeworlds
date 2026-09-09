"""Metrics gates (MAC-178 spec, MAC-182 design brief). Run: python -m unittest discover -s tests -v."""
import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_builder():
    spec = importlib.util.spec_from_file_location('mmw_build_metrics', ROOT / 'scripts/build.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load_builder()


class FormatTests(unittest.TestCase):
    def test_fmt_int_groups_thousands(self):
        self.assertEqual(builder.fmt_int(0), '0')
        self.assertEqual(builder.fmt_int(11), '11')
        self.assertEqual(builder.fmt_int(1234), '1,234')
        self.assertEqual(builder.fmt_int(1234567), '1,234,567')

    def test_fmt_bytes_exact_plus_kb(self):
        self.assertEqual(builder.fmt_bytes(219341), '219,341 bytes (214 kB)')
        self.assertEqual(builder.fmt_bytes(1024), '1,024 bytes (1 kB)')
        self.assertEqual(builder.fmt_bytes(0), '0 bytes (0 kB)')

    def test_fmt_days_singular_plural(self):
        self.assertEqual(builder.fmt_days(1), '1 day')
        self.assertEqual(builder.fmt_days(0), '0 days')
        self.assertEqual(builder.fmt_days(5), '5 days')


class WritingStatsTests(unittest.TestCase):
    def test_counts_posts_words_topics(self):
        posts = [
            {'body': '<p>Hello world</p>'},
            {'body': '<p>One more test post here</p>'},
        ]
        site = {'topics': {'a': 'A', 'b': 'B'}}
        self.assertEqual(builder.writing_stats(posts, site),
                         {'posts': 2, 'words': 7, 'topics': 2})

    def test_empty_journal_is_zero(self):
        self.assertEqual(builder.writing_stats([], {'topics': {}}),
                         {'posts': 0, 'words': 0, 'topics': 0})


class DigestStreakTests(unittest.TestCase):
    def test_consecutive_digests_count_back_from_latest(self):
        posts = [
            {'kind': 'News digest', 'date': '2026-09-07'},
            {'kind': 'News digest', 'date': '2026-09-06'},
            {'kind': 'News digest', 'date': '2026-09-05'},
        ]
        self.assertEqual(builder.digest_info(posts), {'streak': 3, 'last': '2026-09-07'})

    def test_gap_breaks_streak_at_latest_run(self):
        posts = [
            {'kind': 'News digest', 'date': '2026-09-07'},
            {'kind': 'News digest', 'date': '2026-09-05'},
            {'kind': 'News digest', 'date': '2026-09-04'},
        ]
        self.assertEqual(builder.digest_info(posts), {'streak': 1, 'last': '2026-09-07'})

    def test_non_digest_kinds_ignored(self):
        posts = [{'kind': 'Essay', 'date': '2026-09-07'}]
        self.assertEqual(builder.digest_info(posts), {'streak': 0, 'last': None})

    def test_empty_journal_has_no_streak(self):
        self.assertEqual(builder.digest_info([]), {'streak': 0, 'last': None})


class GitInfoTests(unittest.TestCase):
    def test_repo_returns_counts_short_sha_iso_date(self):
        info = builder.git_info(ROOT)
        self.assertIsInstance(info['deploys'], int)
        self.assertGreaterEqual(info['deploys'], 1)
        self.assertRegex(info['short_sha'], r'^[0-9a-f]{7}$')
        self.assertRegex(info['date'], r'^\d{4}-\d{2}-\d{2}$')

    def test_non_git_checkout_falls_back_deterministically(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(builder.git_info(tmp),
                             {'deploys': 0, 'short_sha': '0000000', 'date': '1970-01-01'})


class WeightTests(unittest.TestCase):
    def test_page_weights_sorted_with_url_tiebreak(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            staging = Path(tmp)
            (staging / 'b').mkdir()
            (staging / 'index.html').write_bytes(b'x' * 10)
            (staging / 'b/index.html').write_bytes(b'x' * 10)
            (staging / '404.html').write_bytes(b'x' * 3)
            self.assertEqual(builder.page_weights(staging),
                             [('/404.html', 3), ('/', 10), ('/b/', 10)])

    def test_artifact_totals_counts_css_js(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            staging = Path(tmp)
            (staging / 'assets').mkdir()
            (staging / 'index.html').write_bytes(b'x' * 8)
            (staging / 'assets/a.css').write_bytes(b'y' * 6)
            (staging / 'assets/a.js').write_bytes(b'z' * 4)
            self.assertEqual(builder.artifact_totals(staging),
                             {'files': 3, 'bytes': 18, 'css': 6, 'js': 4})


class MetricsPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        builder.build(ROOT)
        cls.page = (ROOT / 'dist/metrics/index.html').read_text(encoding='utf-8')

    def test_metrics_page_exists_with_single_h1(self):
        self.assertTrue((ROOT / 'dist/metrics/index.html').is_file())
        self.assertEqual(self.page.count('<h1>'), 1)
        self.assertIn('Metrics<span class="accent-dot">.</span>', self.page)

    def test_sections_in_design_order(self):
        writing = self.page.index('Writing.')
        build = self.page.index('This build.')
        weight = self.page.index('Page weight.')
        self.assertLess(writing, build)
        self.assertLess(build, weight)

    def test_tables_are_scoped_regions(self):
        for label in ('Build statistics', 'Lightest pages', 'Heaviest pages'):
            self.assertIn('aria-label="%s"' % label, self.page)
        self.assertIn('<th scope="col">Page</th><th scope="col">Size</th>', self.page)
        self.assertIn('<th scope="row">Deploys</th>', self.page)
        self.assertIn('Ordered lightest first.', self.page)
        self.assertIn('Ordered heaviest first.', self.page)

    def test_every_date_is_time_element(self):
        # Link labels are page URLs (slugs may embed digits); dates shown
        # as content must be real <time> elements with ISO datetime.
        without_links = re.sub(r'<a\b[^>]*>.*?</a>', ' ', self.page, flags=re.S)
        text = re.sub(r'<[^>]+>', ' ', without_links)
        self.assertNotRegex(text, r'\d{4}-\d{2}-\d{2}')
        times = re.findall(r'<time datetime="(\d{4}-\d{2}-\d{2})">', self.page)
        self.assertGreaterEqual(len(times), 3)

    def test_sitemap_and_footer_surface_metrics(self):
        sitemap = (ROOT / 'dist/sitemap.xml').read_text(encoding='utf-8')
        self.assertIn('<loc>https://machinemadeworlds.com/metrics/</loc>', sitemap)
        home = (ROOT / 'dist/index.html').read_text(encoding='utf-8')
        self.assertIn('<a href="/build-log/">Build log</a><a href="/metrics/">Metrics</a>', home)

    def test_no_header_metrics_link(self):
        home = (ROOT / 'dist/index.html').read_text(encoding='utf-8')
        header = home[home.index('<header'):home.index('</header>')]
        self.assertNotIn('/metrics/', header)

    def test_sec_boundary_no_pii_or_full_sha(self):
        visible = re.sub(r'<[^>]+>', ' ', self.page)
        self.assertNotRegex(visible, r'[0-9a-f]{40}')
        self.assertNotRegex(self.page, r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
        self.assertRegex(self.page, r'<code>[0-9a-f]{7}</code>')

    def test_displayed_totals_match_artifact(self):
        total = sum(p.stat().st_size for p in (ROOT / 'dist').rglob('*') if p.is_file())
        match = re.search(r'Total size</th><td>([\d,]+) bytes', self.page)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), '{:,}'.format(total))

    def test_rebuild_is_byte_identical(self):
        before = (ROOT / 'dist/metrics/index.html').read_bytes()
        builder.build(ROOT)
        self.assertEqual((ROOT / 'dist/metrics/index.html').read_bytes(), before)

    def test_metrics_css_is_token_only(self):
        css = (ROOT / 'assets/site.css').read_text(encoding='utf-8')
        added = css[css.index('/* Metrics page'):]
        self.assertNotRegex(added, r'#[0-9a-fA-F]{3,6}')
        self.assertNotIn('rgb(', added)
        self.assertNotIn('@import', added)
        self.assertNotIn('!important', added)
        self.assertIn('.metrics-grid', added)


if __name__ == '__main__':
    unittest.main()
