"""Share-card + article-metadata contract (MAC-167). Run: python -m unittest discover -s tests -v."""
import importlib.util
import json
import re
import unittest
import xml.etree.ElementTree as ET
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mmw_share_meta_build', ROOT / 'scripts/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def meta_content(page, attr, name):
    match = re.search(r'(?:property|name)="%s" content="([^"]*)"' % re.escape(name), page)
    return unescape(match.group(1)) if match else None


class ShareMetaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        builder.build(ROOT)
        cls.dist = ROOT / 'dist'
        cls.site = json.loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))
        cls.published = [p for p in builder.load_posts(ROOT, cls.site)]
        cls.entries = builder.load_buildlog(ROOT, cls.site)
        cls.pages = sorted(cls.dist.rglob('index.html'))
        cls.pages.append(cls.dist / '404.html')

    def test_every_page_has_absolute_png_og_image_with_dimensions_and_large_card(self):
        self.assertGreater(len(self.pages), 10, 'Key routes must all render')
        for path in self.pages:
            page = path.read_text(encoding='utf-8')
            og_image = meta_content(page, 'property', 'og:image')
            self.assertTrue(og_image.startswith(self.site['url'] + '/assets/social-card.'),
                            '%s og:image %s' % (path, og_image))
            self.assertTrue(og_image.endswith('.png'), '%s og:image %s' % (path, og_image))
            self.assertNotIn('logo.', og_image, path)
            self.assertEqual(meta_content(page, 'property', 'og:image:width'), '1200', path)
            self.assertEqual(meta_content(page, 'property', 'og:image:height'), '630', path)
            self.assertEqual(meta_content(page, 'property', 'og:image:type'), 'image/png', path)
            self.assertTrue(meta_content(page, 'property', 'og:image:alt'), path)
            self.assertEqual(meta_content(page, 'name', 'twitter:image'), og_image, path)
            self.assertEqual(meta_content(page, 'name', 'twitter:card'),
                             'summary_large_image', path)

    def test_social_card_asset_is_1200x630_png_under_budget(self):
        source = ROOT / 'assets/social-card.png'
        self.assertTrue(source.is_file(), 'Missing brand social card source')
        self.assertLess(source.stat().st_size, 300 * 1024, 'Card must stay under 300KB')
        rendered = sorted((self.dist / 'assets').glob('social-card.*.png'))
        self.assertEqual(len(rendered), 1, 'Hashed card must ship exactly once')
        header = rendered[0].read_bytes()[:32]
        self.assertEqual(header[16:24], b'\x00\x00\x04\xb0\x00\x00\x02v',
                         'Card must decode as exactly 1200x630 PNG')

    def test_post_pages_carry_article_meta_and_jsonld_image(self):
        self.assertGreater(len(self.published), 0, 'Seed at least one published post')
        for post in self.published:
            page = (self.dist / post['url'].strip('/') / 'index.html').read_text(encoding='utf-8')
            self.assertEqual(meta_content(page, 'property', 'article:published_time'),
                             post['date'] + 'T00:00:00+00:00', post['slug'])
            self.assertEqual(meta_content(page, 'property', 'article:modified_time'),
                             post.get('updated', post['date']) + 'T00:00:00+00:00', post['slug'])
            self.assertEqual(meta_content(page, 'property', 'article:section'),
                             post['topic_name'], post['slug'])
            self.assertEqual(meta_content(page, 'property', 'article:author'),
                             self.site['name'], post['slug'])
            match = re.search(r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>',
                              page, re.S)
            self.assertTrue(match, post['slug'])
            schema = json.loads(match.group(1))
            self.assertTrue(schema['image'].startswith(self.site['url'] + '/assets/social-card.'),
                            post['slug'])
            self.assertTrue(schema['image'].endswith('.png'), post['slug'])

    def test_non_post_pages_carry_no_article_meta(self):
        for rel in ('index.html', 'blog/index.html', 'build-log/index.html',
                    'about/index.html', 'terms/index.html', 'privacy/index.html',
                    'topics/design/index.html', '404.html'):
            page = (self.dist / rel).read_text(encoding='utf-8')
            self.assertNotIn('article:published_time', page, rel)
            self.assertNotIn('article:modified_time', page, rel)

    def test_topic_pages_have_distinct_editor_descriptions(self):
        seen = set()
        for key in self.site['topics']:
            page = (self.dist / 'topics' / key / 'index.html').read_text(encoding='utf-8')
            expected = self.site['topic_descriptions'][key]
            self.assertEqual(meta_content(page, 'name', 'description'), expected, key)
            self.assertEqual(meta_content(page, 'property', 'og:description'), expected, key)
            seen.add(expected)
        self.assertEqual(len(seen), len(self.site['topics']), 'Topic descriptions must be unique')
        self.assertNotIn(self.site['description'], seen)

    def test_sitemap_robots_feed_stay_green(self):
        sitemap = (self.dist / 'sitemap.xml').read_text(encoding='utf-8')
        root = ET.fromstring(sitemap)
        locs = [node.text for node in root.iter()
                if node.tag.endswith('loc')]
        self.assertGreater(len(locs), 10)
        for loc in locs:
            self.assertTrue(loc.startswith(self.site['url'] + '/'), loc)
        robots = (self.dist / 'robots.txt').read_text(encoding='utf-8')
        self.assertIn('Allow: /', robots)
        self.assertIn('Sitemap: ' + self.site['url'] + '/sitemap.xml', robots)
        feed = ET.fromstring((self.dist / 'feed.xml').read_text(encoding='utf-8'))
        items = [node for node in feed.iter() if node.tag == 'item']
        self.assertEqual(len(items), len(self.published))


if __name__ == '__main__':
    unittest.main()
