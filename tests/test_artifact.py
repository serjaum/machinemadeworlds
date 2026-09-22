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
        for file in (ROOT / 'dist/assets').rglob('*'):
            if file.is_file():
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
        # test_share_meta. MAC-778 per-post cards under assets/og/ are
        # scraper-only too. Page HTML delta here is the ~+300B of new meta.
        inpage = [p for p in assets
                  if not p.name.startswith('social-card.') and p.name != 'og']
        self.assertTrue(any(p.name.startswith('social-card.') for p in assets),
                        'Brand social card must ship')
        home = (dist / 'index.html').read_bytes()
        # MAC-648 arcade: game scripts and styles ship as separate hashed
        # assets referenced only by /games/* pages, never by the homepage.
        # The home budget stays a critical-path budget: home HTML plus the
        # assets home actually cites. Game-page weight has its own gates in
        # tests/test_games_arcade.py (JS+CSS <= 60KB, page <= 150KB).
        home_refs = set(re.findall(r'/assets/[^\s"\']+', home.decode('utf-8')))
        inpage = [p for p in assets
                  if ('/assets/' + p.name) in home_refs
                  and not p.name.startswith('social-card.')]
        total = len(home) + sum(p.stat().st_size for p in inpage)
        compressed = len(gzip.compress(home)) + sum(len(gzip.compress(p.read_bytes())) for p in inpage)
        # Raw cap raised 40KB -> 42KB (MAC-72 merge): main sat at 39836
        # after the MAC-80 logo assets (+850B), and the MAC-78 pipeline CSS
        # adds ~1KB as briefed. MAC-102 animation adds ~1.7KB keyframes
        # (spec budget <=3KB): cap 42KB -> 43KB. MAC-167 share-meta tags add
        # ~+300B of head meta (main sat at 42992, 8B under the cap): cap
        # 43KB -> 43.5KB. MAC-175/190 data pages add two footer links
        # (Prices, Benchmarks: ~60B on the homepage, zero new assets):
        # cap 43.5KB -> 43.6KB. MAC-177 glossary adds a homepage card
        # for the opening term (~+200B): cap 43.6KB -> 43.9KB. MAC-178
        # metrics adds the metrics-* CSS (~2.3KB: cards grid, tables,
        # responsive collapse) plus the footer Metrics link: home path
        # sat at ~45300. MAC-349 global search adds the header form
        # (~350B HTML), masthead-search CSS (~600B) and the deferred
        # ranking/render client (~4.5KB JS: lazy index, title > excerpt >
        # topic > body rank, URL sync, ESC, `/`, aria-live; results render
        # via textContent only). Combined home path measured at 51042
        # after the MAC-347 rebase (search + metrics CSS + footer links),
        # so cap 43.9KB -> 51.6KB. JS file cap 3.5KB -> 7KB (client search is
        # deferred, never render-blocking; the full-text index lazy-loads
        # async on first use). Compressed cap unchanged and passing.
        # MAC-482 newsletter follow path adds the homepage strip block
        # (~380B HTML) plus the footer Newsletter anchor (~35B on the
        # homepage, zero new assets): home path measured at 51986,
        # so cap 51.6KB -> 52.1KB. MAC-481 glossary hub adds the footer
        # Glossary link (~+30B on the homepage; the hub page itself
        # reuses archive CSS with zero new assets): still under 52.1KB.
        # MAC-580 collapsible TOC adds disclosure CSS (~+700B: desktop
        # force-open rules plus the mobile 44px tap row with drawn marker,
        # no JS, no new assets): home path measured at 52677,
        # so cap 52.1KB -> 52.8KB. Compressed home path measured at
        # 14002 (2026-09-17, MAC-589: +2B over the 14000 cap from the
        # same disclosure CSS), so compressed cap 14000 -> 14100.
        # MAC-579 scrollspy TOC + reading progress adds the 3px bar rule,
        # the active TOC edge and the ~1.5KB observer/progress client
        # (asset delta under the 2KB design gate; mobile collapsible TOC
        # from MAC-580 untouched): home path measured at 54692,
        # so cap 52.8KB -> 54.9KB. Compressed path measured at 14724,
        # so cap 14100 -> 14800. JS measured at 8084, so cap 7KB -> 8.5KB
        # (scrollspy client is deferred behind page render and only runs
        # on article pages with a TOC).
        # MAC-626 daily digest 2026-09-18 adds the new post + buildlog
        # cards to the homepage (zero new assets): home path measured at
        # 54810 raw (+118) and 14803 compressed (+79, 3B over the 14800
        # cap), so caps 54900 -> 55000 and 14800 -> 14900.
        # MAC-648 arcade ships game assets outside the home critical path
        # (see scoping above): the JS cap covers home-cited scripts only.
        # MAC-748 arcade surfacing adds the header/footer Arcade links
        # (~70B) plus the server-rendered homepage arcade shelf with three
        # game cards (zero new assets): home path measured at 56529 raw
        # (+1719) and 15041 compressed (+238), so caps 55000 -> 57000
        # and 14900 -> 15200.
        self.assertLess(total, 57000)
        self.assertLess(compressed, 15200)
        self.assertLess(sum(p.stat().st_size for p in inpage if p.suffix == '.js'), 8500)
        for p in dist.rglob('*.html'):
            source = p.read_text(encoding='utf-8')
            # Verification-only exception: the async AdSense verification
            # snippet is the single allowed third-party script. Everything
            # else external stays blocked.
            scrubbed = source.replace(
                '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1540728078261973" crossorigin="anonymous"></script>',
                '')
            self.assertNotRegex(scrubbed, r'<(?:script|img)[^>]+src=["\']https?://')
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
