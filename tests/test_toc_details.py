"""Collapsible TOC contract: native details/summary, mobile-only behavior.

Run: python -m unittest discover -s tests -v.
"""
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TocDetailsTests(unittest.TestCase):
    def test_template_wraps_toc_in_native_details(self):
        template = (ROOT / 'templates/post.html').read_text(encoding='utf-8')
        self.assertIn('<details class="toc-details">', template)
        self.assertIn('<summary class="toc-summary">', template)
        self.assertIn('<nav class="toc" aria-label="In this article">', template)
        self.assertNotIn(' open', template.split('toc-details')[0][-200:] if 'toc-details' in template else '')
        # Collapsed by default: markup ships WITHOUT the open attribute.
        self.assertNotRegex(template, r'<details[^>]*\bopen\b')

    def test_desktop_forces_open_inert_summary(self):
        source = (ROOT / 'assets/site.css').read_text(encoding='utf-8')
        start = source.find('@media (min-width: 701px)')
        self.assertNotEqual(start, -1, 'desktop force-open block missing')
        block = source[start:start + 500]
        self.assertIn('.toc-details:not([open])', block)
        self.assertIn('pointer-events: none', block)

    def test_mobile_toggle_target_and_chevron(self):
        source = (ROOT / 'assets/site.css').read_text(encoding='utf-8')
        mobile = source.split('@media (max-width: 700px)')[1]
        # Cut before the next top-level section comment to stay in scope.
        mobile = mobile.split('/* Metrics page')[0]
        self.assertIn('.toc-summary', mobile)
        self.assertIn('min-height: 44px', mobile)
        self.assertIn('.toc-details[open]', mobile)

    def test_built_article_renders_collapsible_toc(self):
        pages = sorted((ROOT / 'dist/posts').glob('*/index.html'))
        self.assertTrue(pages, 'no built post pages')
        checked = 0
        for page in pages:
            html = page.read_text(encoding='utf-8')
            if 'reading-sidebar' in html and 'class="toc"' in html:
                self.assertIn('<details class="toc-details">', html)
                checked += 1
        self.assertGreater(checked, 0, 'no article with TOC found')


if __name__ == '__main__':
    unittest.main()
