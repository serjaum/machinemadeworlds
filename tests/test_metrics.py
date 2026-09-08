"""Open metrics page contract (MAC-178). Run: python -m unittest discover -s tests -v."""
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


class MetricsStatTests(unittest.TestCase):
    def test_format_int_is_deterministic(self):
        builder = load_builder()
        self.assertEqual(builder.format_int(1234), '1,234')
        self.assertEqual(builder.format_int(0), '0')

    def test_format_bytes_uses_bytes_and_kb(self):
        builder = load_builder()
        self.assertIn('bytes', builder.format_bytes(512))
        self.assertIn('kB', builder.format_bytes(2048))
        self.assertIn('bytes', builder.format_bytes(2048))

    def test_format_days_singular_and_plural(self):
        builder = load_builder()
        self.assertEqual(builder.format_days(1), '1 day')
        self.assertEqual(builder.format_days(3), '3 days')

    def test_writing_stats_counts_and_topics(self):
        builder = load_builder()
        site = {'topics': {'design': 'Design', 'essays': 'Essays'}}
        posts = [
            {'slug': 'a', 'topic': 'design', 'body': '<p>one two three</p>'},
            {'slug': 'b', 'topic': 'design', 'body': '<p>four five</p>'},
            {'slug': 'c', 'topic': 'essays', 'body': '<p>six</p>'},
        ]
        stats = builder.writing_stats(posts, site)
        self.assertEqual(stats['post_count'], 3)
        self.assertEqual(stats['total_words'], 6)
        self.assertEqual(stats['topic_count'], 2)
        self.assertEqual({row['key']: row['count'] for row in stats['per_topic']},
                         {'design': 2, 'essays': 1})

    def test_digest_streak_counts_consecutive_days(self):
        builder = load_builder()
        posts = [{'slug': 'ai-news-2026-09-07', 'date': '2026-09-07'},
                 {'slug': 'ai-news-2026-09-06', 'date': '2026-09-06'},
                 {'slug': 'ai-news-2026-09-04', 'date': '2026-09-04'}]
        streak = builder.digest_streak(posts)
        self.assertEqual(streak['streak_days'], 2)
        self.assertEqual(streak['latest'], '2026-09-07')

    def test_digest_streak_zero_without_digests(self):
        builder = load_builder()
        streak = builder.digest_streak([{'slug': 'hello', 'date': '2026-09-07'}])
        self.assertEqual(streak['streak_days'], 0)
        self.assertIsNone(streak['latest'])

    def test_git_stats_never_touches_identity_metadata(self):
        builder = load_builder()
        import inspect
        source = inspect.getsource(builder.git_stats)
        self.assertNotIn('%an', source)
        self.assertNotIn('%ae', source)
        self.assertNotIn('show -s', source)
        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(' '.join(cmd))
            class Result:
                returncode = 0
                stdout = 'abc123def456abc123def456abc123def456abcd|2026-09-08\n' if 'log' in cmd else '42\n'
            return Result()
        stats = builder.git_stats(ROOT, _run=fake_run)
        self.assertEqual(stats['deploys'], 42)
        self.assertEqual(stats['short_sha'], 'abc123d')
        self.assertEqual(stats['date'], '2026-09-08')
        for call in calls:
            self.assertNotIn('an}', call)
            self.assertNotIn('ae}', call)

    def test_build_stats_orders_lightest_and_heaviest(self):
        import tempfile
        builder = load_builder()
        with tempfile.TemporaryDirectory() as tmp:
            staging = Path(tmp)
            (staging / 'assets').mkdir()
            (staging / 'assets/site.abc.css').write_bytes(b'x' * 100)
            (staging / 'assets/site.abc.js').write_bytes(b'y' * 50)
            for name, size in (('a/index.html', 10), ('b/index.html', 30), ('c/index.html', 20)):
                target = staging / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b'z' * size)
            stats = builder.build_stats(staging)
            self.assertEqual(stats['pages'], 3)
            self.assertEqual(stats['css_bytes'], 100)
            self.assertEqual(stats['js_bytes'], 50)
            self.assertEqual([row['url'] for row in stats['lightest']],
                             ['/a/', '/c/', '/b/'])
            self.assertEqual([row['url'] for row in stats['heaviest']],
                             ['/b/', '/c/', '/a/'])

    def test_metrics_page_has_no_pii_or_full_sha_in_visible_text(self):
        builder = load_builder()
        result = builder.build(ROOT)
        self.assertGreater(result['posts'], 0)
        page = (ROOT / 'dist/metrics/index.html').read_text(encoding='utf-8')
        visible = re.sub(r'<a[^>]*>.*?</a>', ' ', page, flags=re.S)
        visible = re.sub(r'<[^>]+>', ' ', visible)
        self.assertIsNone(re.search(r'[0-9a-f]{40}', visible),
                          'full SHA must not appear in visible text')
        self.assertNotRegex(visible, r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
        for token in ('C:\\', '/home/', '/Users/', 'sergi'):
            self.assertNotIn(token, visible)
        sitemap = (ROOT / 'dist/sitemap.xml').read_text(encoding='utf-8')
        self.assertIn('/metrics/', sitemap)
        self.assertEqual(page.count('<h1'), 1)


if __name__ == '__main__':
    unittest.main()
