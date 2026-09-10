"""Build-time llms.txt contract (MAC-391). Run: python -m unittest discover -s tests -v."""
import importlib.util
import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mmw_llms_build', ROOT / 'scripts/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

LINK = re.compile(r'^- \[(?P<label>.+?)\]\((?P<url>https://[^)]+)\): (?P<desc>.+)$')


class LlmsTxtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        builder.build(ROOT)
        cls.dist = ROOT / 'dist'
        cls.site = json.loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))
        cls.index = (cls.dist / 'llms.txt').read_text(encoding='utf-8')
        cls.full = (cls.dist / 'llms-full.txt').read_text(encoding='utf-8')
        cls.rows = [LINK.match(line) for line in cls.index.splitlines()]
        cls.rows = [match for match in cls.rows if match]
        sitemap = ET.parse(cls.dist / 'sitemap.xml').getroot()
        cls.sitemap_urls = {node.findtext('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                            for node in sitemap}
        cls.posts = builder.load_posts(ROOT, cls.site)
        cls.entries = builder.load_buildlog(ROOT, cls.site)

    def test_files_exist_valid_utf8_and_plain_text(self):
        for name in ('llms.txt', 'llms-full.txt'):
            raw = (self.dist / name).read_bytes()
            self.assertGreater(len(raw), 0, name)
            raw.decode('utf-8')
            self.assertNotIn(b'\x00', raw, name)

    def test_header_sections_and_site_description(self):
        self.assertTrue(self.index.startswith('# Machine Made Worlds\n'))
        self.assertIn(self.site['description'], self.index)
        self.assertIn(self.site['url'] + '/llms-full.txt', self.index)
        for section in ('## Journal', '## Glossary', '## Build Log', '## Data pages'):
            self.assertIn(section, self.index)

    def test_rows_capped_single_line_and_canonical(self):
        self.assertLessEqual(len(self.rows), builder.LLMS_LINK_CAP)
        self.assertGreaterEqual(len(self.rows), 10)
        seen = set()
        for match in self.rows:
            label, url, desc = match.group('label'), match.group('url'), match.group('desc')
            self.assertTrue(label.strip() and desc.strip())
            self.assertNotIn(match.group('url'), seen)
            seen.add(url)
        for line in self.index.splitlines():
            if line.startswith('- ['):
                self.assertRegex(line, r'^- \[.+?\]\(https://[^)]+\): .+$')

    def test_every_url_resolves_to_sitemap_page(self):
        for match in self.rows:
            self.assertIn(match.group('url'), self.sitemap_urls, match.group('url'))

    def test_no_drafts_listed(self):
        drafts = set()
        for path in list((ROOT / 'content/posts').glob('*.json')) + \
                list((ROOT / 'content/buildlog').glob('*.json')):
            try:
                meta = json.loads(path.read_text(encoding='utf-8'))
            except (OSError, ValueError):
                continue
            if meta.get('draft', False):
                drafts.add(path.stem)
        text = self.index + self.full
        for slug in drafts:
            self.assertNotIn('/' + slug + '/', text, slug)

    def test_glossary_evergreen_and_latest_journal_pinned(self):
        urls = [match.group('url') for match in self.rows]
        for post in self.posts:
            if post['slug'].startswith('glossary-'):
                self.assertIn(self.site['url'] + post['url'], urls, post['slug'])
        for post in self.posts[:3]:
            if not post['slug'].startswith('glossary-'):
                self.assertIn(self.site['url'] + post['url'], urls, post['slug'])

    def test_full_carries_index_and_body_text_within_cap(self):
        self.assertLessEqual(len(self.full.encode('utf-8')), builder.LLMS_FULL_CAP)
        self.assertTrue(self.full.startswith(self.index))
        for match in self.rows:
            self.assertIn(match.group('url'), self.full)
        sample = builder._llms_single_line(builder.plain(self.posts[0]['body']))[:80]
        self.assertIn(sample, self.full)
        self.assertNotRegex(self.full, r'<[a-z]+[ >]')

    def test_journal_sorted_newest_first(self):
        journal = [match.group('url') for match in self.rows
                   if '/posts/' in match.group('url')
                   and not re.search(r'/glossary-[a-z0-9-]+/$', match.group('url'))]
        dated = {self.site['url'] + p['url']: p['date'] for p in self.posts}
        dates = [dated[url] for url in journal if url in dated]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_rebuild_is_byte_identical(self):
        before = ((self.dist / 'llms.txt').read_bytes(),
                  (self.dist / 'llms-full.txt').read_bytes())
        builder.build(ROOT)
        after = ((self.dist / 'llms.txt').read_bytes(),
                 (self.dist / 'llms-full.txt').read_bytes())
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
