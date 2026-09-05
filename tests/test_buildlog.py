"""Build-log section contract (MAC-48/MAC-49). Run: python -m unittest discover -s tests -v."""
import importlib.util
import json
import re
import tempfile
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mmw_buildlog_build', ROOT / 'scripts/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class BuildLogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        builder.build(ROOT)
        cls.dist = ROOT / 'dist'
        cls.index = (cls.dist / 'build-log/index.html').read_text(encoding='utf-8')
        site = json.loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))
        cls.published = builder.load_buildlog(ROOT, site)

    def test_index_renders_archive_pattern_with_build_copy(self):
        self.assertTrue((self.dist / 'build-log/index.html').is_file())
        for needle in ('Built in the open', 'What changed on this site, and why.',
                       'Search the build log', "Try 'deploy' or 'fix'",
                       'No entries found.', 'Try a different word, or return to the full log.'):
            self.assertIn(needle, self.index)
        self.assertIn('<span data-result-count>%d</span> entries' % len(self.published), self.index)
        # Topic-tabs row carries no topic links: only Everything, rooted at /build-log/.
        tabs = re.search(r'<nav class="topic-tabs".*?</nav>', self.index, re.S)[0]
        self.assertIn('href="/build-log/"', tabs)
        self.assertNotIn('/topics/', tabs)
        self.assertEqual(self.index.count('<h1>'), 1)

    def test_detail_pages_retarget_journal_links_to_build_log(self):
        self.assertGreater(len(self.published), 0, 'Seed at least one published entry')
        for entry in self.published:
            page = (self.dist / entry['url'].strip('/') / 'index.html').read_text(encoding='utf-8')
            self.assertEqual(page.count('<h1>'), 1, entry['slug'])
            self.assertIn('<a href="/build-log/">Build log</a>', page)
            self.assertIn('← Back to the build log', page)
            self.assertIn('All entries ↗', page)
            self.assertNotIn('← Back to the journal', page)
            self.assertNotIn('All articles ↗', page)
            # Every entry carries an allowlisted trail block with real <time> elements.
            self.assertIn('class="trail"', page)
            self.assertRegex(page, r'<time datetime="\d{4}-\d{2}-\d{2}">')

    def test_kind_allowlist_and_markup_gate_parity(self):
        site = json.loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / 'content/buildlog'
            folder.mkdir(parents=True)
            meta = dict(title='A valid title', description='A description.', date='2026-09-05',
                        topic='design', kind='Essay', lead='Introduction.', draft=False,
                        mac_id='MAC-47', pr='#5', commit='0e03e75', agents=['DEV'])
            (folder / 'wrong-kind.json').write_text(json.dumps(meta), encoding='utf-8')
            (folder / 'wrong-kind.html').write_text('<p>Hello</p>', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Invalid buildlog kind'):
                builder.load_buildlog(Path(tmp), site)
            for field, bad in [('mac_id', 'nope'), ('pr', '5'), ('commit', 'ZZZ'),
                               ('agents', []), ('agents', ['x' * 41])]:
                broken = dict(meta, kind='Shipped')
                broken[field] = bad
                (folder / 'wrong-kind.json').write_text(json.dumps(broken), encoding='utf-8')
                (folder / 'wrong-kind.html').write_text('<p>Hello</p>', encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'Invalid buildlog', msg=field):
                    builder.load_buildlog(Path(tmp), site)
            meta['kind'] = 'Shipped'
            (folder / 'wrong-kind.json').write_text(json.dumps(meta), encoding='utf-8')
            (folder / 'wrong-kind.html').write_text('<p>Hello</p><script>alert(1)</script>', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Unsafe'):
                builder.load_buildlog(Path(tmp), site)
            # Drafts never enter the publish artifact.
            meta['draft'] = True
            (folder / 'wrong-kind.json').write_text(json.dumps(meta), encoding='utf-8')
            (folder / 'wrong-kind.html').write_text('<p>Hello</p>', encoding='utf-8')
            self.assertEqual(builder.load_buildlog(Path(tmp), site), [])

    def test_nav_marks_build_log_current_and_footer_links_it(self):
        home = (self.dist / 'index.html').read_text(encoding='utf-8')
        header = re.search(r'<nav class="navigation".*?</nav>', home, re.S)[0]
        hrefs = re.findall(r'href="([^"]+)"', header)
        self.assertEqual(hrefs, ['/', '/blog/', '/build-log/', '/about/'])
        self.assertIn('<a href="/build-log/">Build log</a>', home)
        self.assertIn('<a href="/build-log/"  aria-current="page">Build Log</a', self.index)
        for entry in self.published:
            page = (self.dist / entry['url'].strip('/') / 'index.html').read_text(encoding='utf-8')
            self.assertIn('<a href="/build-log/"  aria-current="page">Build Log</a', page)

    def test_sitemap_includes_build_log_and_feeds_stay_journal_only(self):
        sitemap = (self.dist / 'sitemap.xml').read_text(encoding='utf-8')
        self.assertIn('https://machinemadeworlds.com/build-log/', sitemap)
        feed = (self.dist / 'feed.xml').read_text(encoding='utf-8')
        posts_json = (self.dist / 'posts.json').read_text(encoding='utf-8')
        for entry in self.published:
            self.assertIn('https://machinemadeworlds.com' + entry['url'], sitemap)
            self.assertNotIn(entry['url'], feed)
            self.assertNotIn(entry['url'], posts_json)
        ET.parse(self.dist / 'sitemap.xml')

    def test_trail_css_is_additive_and_token_only(self):
        source = (ROOT / 'assets/site.css').read_text(encoding='utf-8')
        trail = source.split('/* Build log')[1]
        self.assertNotRegex(trail, r'#[0-9a-fA-F]{3,6}')
        for needle in ('rgb(', '@import', 'http', '!important', '@media', '.js'):
            self.assertNotIn(needle, trail)
        for token in ('var(--surface)', 'var(--line)', 'var(--muted)', 'var(--accent)', 'var(--s1)', 'var(--s2)'):
            self.assertIn(token, trail)

    def test_new_buildlog_scaffold_is_a_draft_and_never_overwrites_content(self):
        script = ROOT / 'scripts/new_buildlog.py'
        self.assertTrue(script.exists(), 'Missing safe new-buildlog command')
        modspec = importlib.util.spec_from_file_location('mmw_new_buildlog', script)
        mod = importlib.util.module_from_spec(modspec)
        modspec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / 'content').mkdir()
            (target / 'content/site.json').write_text((ROOT / 'content/site.json').read_text(encoding='utf-8'), encoding='utf-8')
            mod.create_buildlog(target, 'another-fix', 'Another fix', 'local-ai', 'Fix', '2026-09-05')
            path = target / 'content/buildlog/another-fix.json'
            data = json.loads(path.read_text(encoding='utf-8'))
            self.assertTrue(data['draft'])
            self.assertEqual(data['kind'], 'Fix')
            self.assertTrue(path.with_suffix('.html').exists())
            with self.assertRaises(FileExistsError):
                mod.create_buildlog(target, 'another-fix', 'Overwrite', 'local-ai', 'Fix', '2026-09-05')
            self.assertEqual(json.loads(path.read_text())['title'], 'Another fix')
            with self.assertRaises(ValueError):
                mod.create_buildlog(target, '../escape', 'Title', 'local-ai', 'Fix', '2026-09-05')
            with self.assertRaises(ValueError):
                mod.create_buildlog(target, 'bad-kind', 'Title', 'local-ai', 'Essay', '2026-09-05')


if __name__ == '__main__':
    unittest.main()
