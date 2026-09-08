"""JSON Feed 1.1 contract (MAC-265). Run: python -m unittest discover -s tests -v."""
import importlib.util
import json
import re
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mmw_json_feed_build', ROOT / 'scripts/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

RFC3339 = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}([+-]\d{2}:\d{2}|Z)$')


class JsonFeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        builder.build(ROOT)
        cls.dist = ROOT / 'dist'
        cls.site = json.loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))
        cls.feed = json.loads((cls.dist / 'feed.json').read_text(encoding='utf-8'))
        rss = ET.parse(cls.dist / 'feed.xml').getroot()
        cls.rss_urls = [item.findtext('link') for item in rss.find('channel').findall('item')]

    def test_required_top_level_fields(self):
        self.assertEqual(self.feed['version'], 'https://jsonfeed.org/version/1.1')
        self.assertEqual(self.feed['title'], self.site['name'])
        self.assertEqual(self.feed['home_page_url'], self.site['url'] + '/')
        self.assertEqual(self.feed['feed_url'], self.site['url'] + '/feed.json')
        self.assertEqual(self.feed['description'], self.site['description'])
        self.assertEqual(self.feed['language'], 'en')
        self.assertIsInstance(self.feed['items'], list)
        self.assertGreater(len(self.feed['items']), 0)

    def test_items_have_ids_urls_dates_and_tags(self):
        seen = set()
        for item in self.feed['items']:
            for key in ('id', 'url', 'title', 'summary', 'content_text', 'date_published'):
                self.assertIsInstance(item[key], str, key)
                self.assertTrue(item[key].strip(), key)
            self.assertEqual(item['id'], item['url'])
            self.assertTrue(item['url'].startswith(self.site['url'] + '/posts/'))
            self.assertEqual(item['summary'], item['content_text'])
            self.assertRegex(item['date_published'], RFC3339)
            datetime.fromisoformat(item['date_published'].replace('Z', '+00:00'))
            self.assertIsInstance(item['tags'], list)
            self.assertEqual(len(item['tags']), 1)
            self.assertIn(item['tags'][0], self.site['topics'])
            self.assertNotIn(item['id'], seen)
            seen.add(item['id'])

    def test_count_and_order_match_rss(self):
        self.assertEqual(len(self.feed['items']), len(self.rss_urls))
        self.assertEqual([item['url'] for item in self.feed['items']], self.rss_urls)

    def test_journal_only_and_discovery_links(self):
        published = builder.load_buildlog(ROOT, self.site)
        for entry in published:
            self.assertNotIn(entry['url'], json.dumps(self.feed))
        home = (self.dist / 'index.html').read_text(encoding='utf-8')
        self.assertIn('type="application/feed+json"', home)
        self.assertIn('href="/feed.json"', home)
        self.assertIn('type="application/rss+xml"', home)
        self.assertIn('href="/feed.xml"', home)
        self.assertIn('href="/feed.json"', home)

    def test_sitemap_url_set_unchanged(self):
        sitemap = (self.dist / 'sitemap.xml').read_text(encoding='utf-8')
        self.assertNotIn('feed.json', sitemap)


if __name__ == '__main__':
    unittest.main()
