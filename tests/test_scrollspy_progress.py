"""Article scrollspy TOC + reading progress contract (MAC-579/MAC-581 spec).

Run: python -m unittest discover -s tests -v.
Static hooks only: exactly-one-aria-current after simulated scroll needs a
browser, so unit tests pin the markup, styles, script hooks, built output
and the <2KB asset-weight gate instead.
"""
import importlib.util
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

PROGRESS_DIV = '<div class="reading-progress" hidden aria-hidden="true"></div>'
ORIG_TOC_A = ('.toc a { display: block; color: var(--muted); font-size: 13px; '
              'text-decoration: none; padding: 9px 0; }')


def scrollspy_css_block(source):
    start = source.index('.toc a[aria-current')
    end = source.index('}', source.index('.reading-progress')) + 1
    return source[start:end]


def scrollspy_js_block(source):
    start = source.index('/* Scrollspy TOC + reading progress. */')
    return source[start:source.index('})();', start) + len('})();')]


class ScrollspyTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = (ROOT / 'templates/post.html').read_text(encoding='utf-8')

    def test_progress_element_sits_between_heading_and_reading_layout(self):
        self.assertIn(PROGRESS_DIV, self.template)
        self.assertLess(self.template.index('class="article-heading"'),
                        self.template.index(PROGRESS_DIV))
        self.assertLess(self.template.index(PROGRESS_DIV),
                        self.template.index('class="reading-layout"'))
        self.assertEqual(self.template.count('reading-progress'), 1)

    def test_article_scope_only(self):
        for name in ('base.html', 'home.html', 'archive.html', 'featured.html'):
            source = (ROOT / 'templates' / name).read_text(encoding='utf-8')
            self.assertNotIn('reading-progress', source, name)


class ScrollspyCssTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / 'assets/site.css').read_text(encoding='utf-8')

    def test_progress_bar_rule_uses_progress_var_only(self):
        rule = re.search(r'\.reading-progress \{([^}]*)\}', self.source)[1]
        self.assertIn('height: 3px', rule)
        self.assertIn('var(--progress, 0)', rule)
        self.assertIn('var(--accent)', rule)
        self.assertIn('var(--line)', rule)

    def test_no_motion_on_progress_element(self):
        block = scrollspy_css_block(self.source)
        self.assertNotIn('transition', block)
        self.assertNotIn('animation', block)

    def test_toc_active_edge_is_additive_and_shift_free(self):
        line = next(l for l in self.source.splitlines() if l.startswith('.toc a {'))
        for needle in ('border-left: 2px solid transparent', 'padding-left: 12px',
                       'min-height: 44px', 'display: flex', 'align-items: center'):
            self.assertIn(needle, line)
        self.assertIn('color: var(--muted)', line)
        active = re.search(r'\.toc a\[aria-current="true"\] \{([^}]*)\}', self.source)[1]
        self.assertIn('color: var(--ink)', active)
        self.assertIn('border-color: var(--accent)', active)
        self.assertNotIn('font-weight', active)
        self.assertNotIn('background', active)

    def test_new_css_is_token_only(self):
        block = scrollspy_css_block(self.source)
        self.assertNotRegex(block, r'#[0-9a-fA-F]{3,8}')
        self.assertNotIn('!important', block)
        for token in ('var(--accent)', 'var(--line)', 'var(--ink)'):
            self.assertIn(token, block)

    def test_print_hides_progress_bar(self):
        printed = self.source[self.source.index('@media print'):]
        self.assertIn('.reading-progress', printed)


class ScrollspyJsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / 'assets/site.js').read_text(encoding='utf-8')
        cls.block = scrollspy_js_block(cls.source)

    def test_guards_noop_without_toc(self):
        self.assertIn('if(!t||!b||!d)return', self.block)
        self.assertIn('if(!l.length)return', self.block)
        self.assertIn('if(!h.length)return', self.block)

    def test_observer_with_scroll_fallback_and_progress(self):
        self.assertIn('IntersectionObserver', self.block)
        self.assertIn('addEventListener("scroll"', self.block)
        self.assertIn('{passive:true}', self.block)
        self.assertIn('requestAnimationFrame', self.block)
        self.assertIn('aria-current', self.block)
        self.assertIn('setProperty("--progress"', self.block)
        self.assertIn('b.hidden=false', self.block)

    def test_first_link_current_and_last_at_bottom(self):
        self.assertIn('o=h[0].id', self.block)
        self.assertIn('h[h.length-1].id', self.block)
        self.assertIn('scrollHeight', self.block)

    def test_progressive_enhancement_restrictions(self):
        for needle in ('innerHTML', 'scrollIntoView', 'scrollTo', 'scroll-behavior',
                       'fetch(', 'XMLHttpRequest', 'localStorage', 'sessionStorage',
                       'details', 'smooth'):
            self.assertNotIn(needle, self.block)


class ScrollspyWeightTests(unittest.TestCase):
    def test_asset_delta_under_2kb(self):
        css = (ROOT / 'assets/site.css').read_text(encoding='utf-8')
        js = (ROOT / 'assets/site.js').read_text(encoding='utf-8')
        line = next(l for l in css.splitlines() if l.startswith('.toc a {'))
        delta = len(scrollspy_css_block(css)) + (len(line) - len(ORIG_TOC_A))
        delta += len(scrollspy_js_block(js))
        self.assertLess(delta, 2048)


class ScrollspyBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('mmw_scrollspy_build', ROOT / 'scripts/build.py')
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        builder.build(ROOT)
        cls.pages = sorted((ROOT / 'dist/posts').glob('*/index.html'))

    def test_built_articles_carry_hidden_progress_bar(self):
        self.assertTrue(self.pages)
        for page in self.pages:
            self.assertIn(PROGRESS_DIV, page.read_text(encoding='utf-8'), str(page))

    def test_toc_anchors_match_heading_ids(self):
        checked = 0
        for page in self.pages:
            source = page.read_text(encoding='utf-8')
            nav = re.search(r'<nav class="toc".*?</nav>', source, re.S)
            if not nav:
                continue
            hrefs = set(re.findall(r'href="#([^"]+)"', nav[0]))
            if not hrefs:
                continue
            body = re.search(r'<div class="article-body".*', source, re.S)[0]
            ids = set(re.findall(r'<h2 id="([^"]+)"', body))
            self.assertEqual(hrefs, ids & hrefs, str(page))
            self.assertTrue(hrefs <= ids, str(page))
            checked += 1
        self.assertGreater(checked, 0, 'Seed at least one article with a TOC')

    def test_no_js_keeps_bar_hidden_and_indexes_untouched(self):
        css = (ROOT / 'assets/site.css').read_text(encoding='utf-8')
        self.assertIn('[hidden] { display: none !important; }', css)
        for name in ('index.html', 'blog/index.html'):
            source = (ROOT / 'dist' / name).read_text(encoding='utf-8')
            self.assertNotIn('reading-progress', source, name)


if __name__ == '__main__':
    unittest.main()
