"""BreadcrumbList JSON-LD parity contract (MAC-453). Run: python -m unittest discover -s tests -v."""
import importlib.util
import json
import re
import unittest
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mmw_breadcrumb_build', ROOT / 'scripts/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def ld_blocks(page):
    return [json.loads(b) for b in
            re.findall(r'ld\+json">\s*(.*?)\s*</script>', page, re.S)]


def visible_breadcrumb(page):
    nav = re.search(r'<nav class="breadcrumbs"[^>]*>(.*?)</nav>', page, re.S)
    if not nav:
        return None
    return [(unescape(href), unescape(label)) for href, label in
            re.findall(r'<a href="([^"]*)">(.*?)</a>', nav.group(1))]


class BreadcrumbJsonLdTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        builder.build(ROOT)
        cls.dist = ROOT / 'dist'
        cls.site = json.loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))
        cls.posts = [p for p in builder.load_posts(ROOT, cls.site)]
        cls.entries = builder.load_buildlog(ROOT, cls.site)

    def assert_crumb(self, page, url, index_label, index_href, topic, topic_name, title):
        blocks = ld_blocks(page)
        by_type = [b for b in blocks if b.get('@type') == 'BreadcrumbList']
        self.assertEqual(len(by_type), 1, url)
        items = by_type[0]['itemListElement']
        self.assertEqual(len(items), 3, url)
        self.assertEqual([i['position'] for i in items], [1, 2, 3], url)
        self.assertEqual(items[0]['name'], index_label, url)
        self.assertEqual(items[0]['item'], self.site['url'] + index_href, url)
        self.assertEqual(items[1]['name'], topic_name, url)
        self.assertEqual(items[1]['item'],
                         self.site['url'] + '/topics/' + topic + '/', url)
        self.assertEqual(items[2]['name'], title, url)
        self.assertEqual(items[2]['item'], self.site['url'] + url, url)
        for item in items:
            self.assertTrue(item['item'].startswith(self.site['url'] + '/'), url)
        # Parity with the visible breadcrumb trail.
        trail = visible_breadcrumb(page)
        self.assertTrue(trail, url)
        self.assertEqual(trail[0][0], index_href, url)
        self.assertEqual(trail[1][0], '/topics/' + topic + '/', url)

    def test_post_pages_carry_breadcrumblist_with_canonical_final_item(self):
        self.assertGreater(len(self.posts), 0, 'Seed at least one published post')
        for post in self.posts:
            page = (self.dist / post['url'].strip('/') / 'index.html').read_text(encoding='utf-8')
            self.assert_crumb(page, post['url'], 'The journal', '/blog/',
                              post['topic'], post['topic_name'], post['title'])

    def test_buildlog_entries_carry_breadcrumblist(self):
        self.assertGreater(len(self.entries), 0, 'Seed at least one buildlog entry')
        for entry in self.entries:
            page = (self.dist / entry['url'].strip('/') / 'index.html').read_text(encoding='utf-8')
            self.assert_crumb(page, entry['url'], 'Build log', '/build-log/',
                              entry['topic'], entry['topic_name'], entry['title'])

    def test_blogposting_block_unchanged_and_escaping_preserved(self):
        for post in self.posts:
            page = (self.dist / post['url'].strip('/') / 'index.html').read_text(encoding='utf-8')
            blocks = ld_blocks(page)
            posting = [b for b in blocks if b.get('@type') == 'BlogPosting']
            self.assertEqual(len(posting), 1, post['slug'])
            for field in ('headline', 'description', 'datePublished', 'dateModified',
                          'mainEntityOfPage', 'author', 'publisher', 'image'):
                self.assertIn(field, posting[0], post['slug'])
            raw = re.search(r'ld\+json">\s*(.*?)\s*</script>', page, re.S).group(1)
            self.assertNotIn('<', raw.replace('\\u003c', ''), post['slug'])

    def test_non_detail_pages_carry_no_breadcrumb_list(self):
        for rel in ('index.html', 'blog/index.html', 'build-log/index.html',
                    'about/index.html', 'topics/automation/index.html', '404.html'):
            page = (self.dist / rel).read_text(encoding='utf-8')
            types = [b.get('@type') for b in ld_blocks(page)]
            self.assertNotIn('BreadcrumbList', types, rel)
            self.assertEqual(len(types), 1, rel)


if __name__ == '__main__':
    unittest.main()
