"""Mobile collapsible TOC contract (MAC-580). Run: python -m unittest discover -s tests -v."""
import importlib.util
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mmw_mobile_toc_build', ROOT / 'scripts/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def _media_block(source, query):
    """Return the concatenated bodies of @media blocks matching query."""
    bodies = []
    for match in re.finditer(r'@media\s*\(([^)]+)\)\s*\{', source):
        if query not in match.group(1):
            continue
        depth = 1
        pos = match.end()
        while depth and pos < len(source):
            char = source[pos]
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
            pos += 1
        bodies.append(source[match.end():pos - 1])
    return '\n'.join(bodies)


class MobileTocTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # dist/ is a committed build artifact refreshed by scripts/build.py
        # before this suite runs; read it as-is instead of rebuilding here
        # (repeated rebuilds race file locks on this host).
        cls.template = (ROOT / 'templates/post.html').read_text(encoding='utf-8')
        cls.css = (ROOT / 'assets/site.css').read_text(encoding='utf-8')
        cls.mobile = _media_block(cls.css, 'max-width: 700px')
        cls.desktop = _media_block(cls.css, 'min-width: 701px')

    def test_template_uses_native_disclosure_without_duplication(self):
        self.assertIn('<details class="toc-details">', self.template)
        self.assertIn('<summary class="toc-summary">', self.template)
        self.assertIn('In this article', self.template)
        # Collapsed by default: markup ships without the open flag.
        self.assertNotIn('<details class="toc-details" open', self.template)
        self.assertNotIn(' open>', self.template.replace('$toc_hidden', ''))
        # No duplication: exactly one outline nav, still fed by the builder.
        self.assertEqual(self.template.count('<nav class="toc"'), 1)
        self.assertIn('$toc', self.template)
        # Sidebar shell is untouched: hidden flag, follow link, body slot.
        self.assertIn('<aside class="reading-sidebar" $toc_hidden>', self.template)
        self.assertIn('href="/feed.xml"', self.template)

    def test_mobile_toggle_affordance_exists(self):
        self.assertTrue(self.mobile, 'Missing the <=700px media block')
        self.assertIn('.toc-summary', self.mobile)
        self.assertRegex(self.mobile, r'min-height:\s*44px')
        self.assertIn('cursor: pointer', self.mobile)
        # CSS-only chevron plus its open-state turn.
        self.assertIn('.toc-summary::after', self.mobile)
        self.assertIn('.toc-details[open]', self.mobile)

    def test_desktop_forces_open_look(self):
        self.assertTrue(self.desktop, 'Missing the >=701px media block')
        # Content stays visible even though markup ships closed.
        self.assertIn('.toc-details:not([open])', self.desktop)
        self.assertIn('display: block', self.desktop)
        # Label is inert on desktop.
        self.assertIn('.toc-summary', self.desktop)
        self.assertIn('pointer-events: none', self.desktop)

    def test_desktop_sidebar_rules_unchanged(self):
        base = self.css.split('@media')[0]
        self.assertIn('.reading-layout', base)
        self.assertIn('grid-template-columns: 230px', base)
        self.assertIn('.reading-sidebar', base)
        self.assertIn('.toc a', base)

    def test_built_articles_carry_collapsible_toc(self):
        pages = list((ROOT / 'dist/posts').glob('*/index.html'))
        self.assertTrue(pages, 'No built article pages')
        checked = 0
        for page in pages:
            source = page.read_text(encoding='utf-8')
            if '<aside class="reading-sidebar"' not in source:
                continue
            self.assertIn('<details class="toc-details">', source, str(page))
            self.assertIn('<summary class="toc-summary">', source, str(page))
            self.assertEqual(source.count('<nav class="toc"'), 1, str(page))
            checked += 1
        self.assertGreater(checked, 0, 'No article page renders the sidebar')


if __name__ == '__main__':
    unittest.main()
