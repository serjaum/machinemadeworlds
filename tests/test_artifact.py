"""Built artifact checks: links, content integrity, determinism and size budgets."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, unquote
import gzip
import importlib.util
import json
import re
import subprocess
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mmw_artifact_build', ROOT / 'scripts/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class Page(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.links, self.ids, self.h1 = [], [], 0
        self.feed(source)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a: self.ids.append(a['id'])
        if tag == 'h1': self.h1 += 1
        for key in ('href', 'src'):
            if a.get(key): self.links.append(a[key])

class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        builder.build(ROOT)

    def test_all_internal_links_and_anchors_resolve(self):
        dist = ROOT / 'dist'
        for file in dist.rglob('*.html'):
            source = file.read_text(encoding='utf-8')
            parsed = Page(source)
            self.assertEqual(parsed.h1, 1, str(file))
            self.assertEqual(len(parsed.ids), len(set(parsed.ids)), str(file))
            for link in parsed.links:
                url = urlsplit(urljoin('https://machinemadeworlds.com/' + file.relative_to(dist).as_posix(), link))
                if url.scheme not in ('https', 'http') or url.netloc != 'machinemadeworlds.com': continue
                target = dist / unquote(url.path).lstrip('/')
                if url.path.endswith('/'): target /= 'index.html'
                self.assertTrue(target.is_file(), f'{file.relative_to(dist)} → {link}')
                if url.fragment and target.suffix == '.html':
                    self.assertIn(unquote(url.fragment), Page(target.read_text(encoding='utf-8')).ids, link)

    def test_deploy_artifact_excludes_sources_and_templates(self):
        for file in (ROOT / 'dist').rglob('*'):
            self.assertNotIn('_template', str(file))
            if file.is_file():
                self.assertNotIn(file.suffix, ('.md', '.py'))
                self.assertNotIn(file.name, ('.env', 'site.json'))
        self.assertFalse((ROOT / 'dist/styles.css').exists())
        for file in (ROOT / 'dist/assets').iterdir():
            self.assertRegex(file.name, r'\.[a-f0-9]{12}\.')

    def test_byte_identical_rebuild(self):
        before = {p.relative_to(ROOT / 'dist'): p.read_bytes() for p in (ROOT / 'dist').rglob('*') if p.is_file()}
        builder.build(ROOT)
        after = {p.relative_to(ROOT / 'dist'): p.read_bytes() for p in (ROOT / 'dist').rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_budgets_and_no_third_party_resources(self):
        dist = ROOT / 'dist'
        assets = list((dist / 'assets').iterdir())
        # MAC-167: the brand social card is scraper-only (og/twitter meta,
        # never an in-page <img>/preload), so it sits outside the
        # render-blocking weight budget; its own <300KB cap is pinned in
        # test_share_meta. Page HTML delta here is the ~+300B of new meta.
        inpage = [p for p in assets if not p.name.startswith('social-card.')]
        self.assertTrue(any(p.name.startswith('social-card.') for p in assets),
                        'Brand social card must ship')
        home = (dist / 'index.html').read_bytes()
        total = len(home) + sum(p.stat().st_size for p in inpage)
        compressed = len(gzip.compress(home)) + sum(len(gzip.compress(p.read_bytes())) for p in inpage)
        # Raw cap raised 40KB -> 42KB (MAC-72 merge): main sat at 39836
        # after the MAC-80 logo assets (+850B), and the MAC-78 pipeline CSS
        # adds ~1KB as briefed. MAC-102 animation adds ~1.7KB keyframes
        # (spec budget <=3KB): cap 42KB -> 43KB. MAC-167 share-meta tags add
        # ~+300B of head meta (main sat at 42992, 8B under the cap): cap
        # 43KB -> 43.5KB. MAC-194 tiny-LLMs lab adds ~1KB of additive
        # lab-* matrix rules plus the footer link bytes on the homepage
        # (total sat at 44483); MAC-175/190 data pages add two more footer
        # links (Prices, Benchmarks: ~60B on the homepage, zero new
        # assets): cap 43.5KB -> 45KB. Compressed/JS caps unchanged
        # and passing.
        self.assertLess(total, 45000)
        self.assertLess(compressed, 14000)
        self.assertLess(sum(p.stat().st_size for p in assets if p.suffix == '.js'), 3500)
        for p in dist.rglob('*.html'):
            source = p.read_text(encoding='utf-8')
            self.assertNotRegex(source, r'<(?:script|img)[^>]+src=["\']https?://')
            self.assertNotIn('@import', source)
        ET.parse(dist / 'feed.xml')
        ET.parse(dist / 'sitemap.xml')

    def test_existing_article_bodies_preserved(self):
        for path in (ROOT / 'content/posts').glob('*.html'):
            try:
                original = subprocess.check_output(['git', 'show', '9a962ce:posts/' + path.stem + '/index.html'], cwd=ROOT).decode('utf-8')
            except subprocess.CalledProcessError:
                # New posts have no legacy body to preserve; nothing to compare.
                continue
            body = re.search(r'<div class="prose">\s*(.*?)\s*</div>\s*(?:<hr|</article>)', original, re.S)[1]
            self.assertEqual(path.read_text(encoding='utf-8').strip(), body.strip())

    def test_rejects_executable_attributes_and_urls(self):
        for text in ['<p onclick="run()">x</p>', '<a href="javascript:alert(1)">x</a>', '<iframe src="/x"></iframe>', '<a href="java&#10;script:alert(1)">x</a>']:
            with self.assertRaises(ValueError, msg=text):
                builder.ArticleMarkup().feed(text)

    def test_repeated_headings_receive_unique_anchors(self):
        _, toc = builder.heading_anchors('<h2>Getting started</h2><h2>Getting started</h2>')
        self.assertEqual([key for key, _ in toc], ['getting-started', 'getting-started-2'])

if __name__ == '__main__':
    unittest.main()
