"""Share-card + article-metadata contract (MAC-167, per-post cards MAC-778). Run: python -m unittest discover -s tests -v."""
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


def page_url(path, dist):
    rel = path.relative_to(dist).as_posix()
    if rel == '404.html':
        return '/404.html'
    return '/' + rel[:rel.rindex('/') + 1] if '/' in rel else '/'


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
        cls.detail = {p['url']: p for p in cls.published + cls.entries}
        home = (cls.dist / 'index.html').read_text(encoding='utf-8')
        cls.home_card = meta_content(home, 'property', 'og:image')

    def test_fallback_pages_keep_generic_social_card(self):
        fallback = [path for path in self.pages
                    if page_url(path, self.dist) not in self.detail]
        self.assertGreater(len(fallback), 10, 'Indexes and static pages must all render')
        for path in fallback:
            page = path.read_text(encoding='utf-8')
            og_image = meta_content(page, 'property', 'og:image')
            self.assertTrue(og_image.startswith(self.site['url'] + '/assets/social-card.'),
                            '%s og:image %s' % (path, og_image))
            self.assertTrue(og_image.endswith('.png'), '%s og:image %s' % (path, og_image))
            self.assertNotIn('logo.', og_image, path)
            self.assertNotIn('/assets/og/', og_image, path)
            self.assertEqual(meta_content(page, 'property', 'og:image:width'), '1200', path)
            self.assertEqual(meta_content(page, 'property', 'og:image:height'), '630', path)
            self.assertEqual(meta_content(page, 'property', 'og:image:type'), 'image/png', path)
            self.assertEqual(meta_content(page, 'property', 'og:image:alt'),
                             'Machine Made Worlds — a journal of artificial intelligence', path)
            self.assertEqual(meta_content(page, 'name', 'twitter:image'), og_image, path)
            self.assertEqual(meta_content(page, 'name', 'twitter:card'),
                             'summary_large_image', path)

    def test_detail_pages_carry_unique_per_post_cards(self):
        self.assertGreater(len(self.detail), 10, 'Posts and build-log entries must all render')
        seen = set()
        for url, item in sorted(self.detail.items()):
            page = (self.dist / url.strip('/') / 'index.html').read_text(encoding='utf-8')
            og_image = meta_content(page, 'property', 'og:image')
            self.assertRegex(og_image, r'/assets/og/%s\.[a-f0-9]{12}\.png$'
                             % re.escape(item['slug']), url)
            self.assertNotEqual(og_image, self.home_card, url)
            seen.add(og_image)
            target = self.dist / 'assets/og' / og_image.rsplit('/assets/og/', 1)[1]
            self.assertTrue(target.is_file(), '%s card missing: %s' % (url, og_image))
            self.assertEqual(meta_content(page, 'property', 'og:image:width'), '1200', url)
            self.assertEqual(meta_content(page, 'property', 'og:image:height'), '630', url)
            self.assertEqual(meta_content(page, 'property', 'og:image:type'), 'image/png', url)
            self.assertEqual(meta_content(page, 'property', 'og:image:alt'),
                             '%s — %s · %s' % (item['title'], item['topic_name'],
                                               self.site['name']), url)
            self.assertEqual(meta_content(page, 'name', 'twitter:image'), og_image, url)
            self.assertEqual(meta_content(page, 'name', 'twitter:card'),
                             'summary_large_image', url)
            match = re.search(r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>',
                              page, re.S)
            self.assertTrue(match, url)
            self.assertEqual(json.loads(match.group(1))['image'], og_image, url)
        # Cards distinct per page except where a post and its build-log entry
        # share a slug and identical card inputs (same bytes, one file).
        self.assertGreaterEqual(len(seen), len(self.detail) - 15,
                                'Per-post cards must be unique per page')

    def test_acceptance_sample_cards(self):
        samples = ('ai-news-2026-09-21', 'link-radar-2026-09-21', 'glossary-system-prompt',
                   'glossary-kv-cache', 'jev-vs-open-decision-models')
        for slug in samples:
            url = '/posts/' + slug + '/'
            self.assertIn(url, self.detail, slug)
            page = (self.dist / url.strip('/') / 'index.html').read_text(encoding='utf-8')
            og_image = meta_content(page, 'property', 'og:image')
            self.assertIn('/assets/og/%s.' % slug, og_image, slug)
            self.assertNotEqual(og_image, self.home_card, slug)

    def test_social_card_asset_is_1200x630_png_under_budget(self):
        source = ROOT / 'assets/social-card.png'
        self.assertTrue(source.is_file(), 'Missing brand social card source')
        self.assertLess(source.stat().st_size, 300 * 1024, 'Card must stay under 300KB')
        rendered = sorted((self.dist / 'assets').glob('social-card.*.png'))
        self.assertEqual(len(rendered), 1, 'Hashed card must ship exactly once')
        header = rendered[0].read_bytes()[:32]
        self.assertEqual(header[16:24], b'\x00\x00\x04\xb0\x00\x00\x02v',
                         'Card must decode as exactly 1200x630 PNG')

    def test_per_post_card_assets_are_1200x630_png_under_budget(self):
        cards = sorted((self.dist / 'assets/og').glob('*.png'))
        self.assertGreater(len(cards), 10, 'Per-post cards must ship')
        by_slug = {}
        for card in cards:
            self.assertRegex(card.name, r'^[a-z0-9]+(?:-[a-z0-9]+)*\.[a-f0-9]{12}\.png$',
                             card.name)
            self.assertLess(card.stat().st_size, 300 * 1024, card.name)
            header = card.read_bytes()[:32]
            self.assertEqual(header[16:24], b'\x00\x00\x04\xb0\x00\x00\x02v', card.name)
            by_slug.setdefault(card.name.rsplit('.', 2)[0], card.name)
        for item in self.published + self.entries:
            self.assertIn(item['slug'], by_slug, item['slug'])

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
            self.assertEqual(schema['image'], meta_content(page, 'property', 'og:image'),
                             post['slug'])
            self.assertIn('/assets/og/%s.' % post['slug'], schema['image'], post['slug'])
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


    def test_sitemap_lastmod_covers_every_url(self):
        sitemap = (self.dist / 'sitemap.xml').read_text(encoding='utf-8')
        root = ET.fromstring(sitemap)
        seen = {}
        for url in root.iter():
            if not url.tag.endswith('url'):
                continue
            loc = lastmod = None
            for child in url:
                if child.tag.endswith('loc'):
                    loc = child.text
                elif child.tag.endswith('lastmod'):
                    lastmod = child.text
            self.assertTrue(loc, 'Every sitemap entry must carry a loc')
            self.assertRegex(lastmod or '', r'^\d{4}-\d{2}-\d{2}$', loc)
            seen[loc] = lastmod
        self.assertGreater(len(seen), 10)
        self.assertEqual(seen[self.site['url'] + '/posts/ai-news-2026-09-08/'],
                         '2026-09-08')
        prices = json.loads((ROOT / 'content/data/prices.json').read_text(encoding='utf-8'))
        self.assertEqual(seen[self.site['url'] + '/prices/'], prices['updated'])
        ET.parse(self.dist / 'sitemap.xml')


if __name__ == '__main__':
    unittest.main()
