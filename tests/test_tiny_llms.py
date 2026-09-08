"""Tiny LLM capability lab contract. Run: python -m unittest discover -s tests -v."""
import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mmw_lab_build', ROOT / 'scripts/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

LAB_URLS = ['/tiny-llms/', '/tiny-llms/methodology/',
            '/tiny-llms/qwen25-05b/', '/tiny-llms/llama-32-1b/', '/tiny-llms/phi-35-mini/']


class TinyLabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        builder.build(ROOT)

    def test_lab_pages_render_with_one_h1_and_canonical(self):
        for url in LAB_URLS:
            page = (ROOT / 'dist' / url.strip('/') / 'index.html').read_text(encoding='utf-8')
            self.assertEqual(len(re.findall(r'<h1[ >]', page)), 1, url)
            self.assertIn('rel="canonical"', page)
            self.assertIn('og:type" content="website"', page)
            self.assertIn('"@type": "WebPage"', page)

    def test_matrix_cells_use_text_plus_symbol(self):
        index = (ROOT / 'dist/tiny-llms/index.html').read_text(encoding='utf-8')
        for verdict, symbol in (('PASS', '●'), ('PARTIAL', '◐'), ('FAIL', '○')):
            self.assertIn(verdict, index)
            self.assertIn(symbol, index)
        self.assertIn('<caption>', index)
        self.assertIn('scope="col"', index)
        self.assertIn('scope="row"', index)
        self.assertIn('role="region"', index)
        # Index matrix must agree with the builder model data.
        for model in builder.LAB_MODELS:
            for key, _ in builder.LAB_TASKS:
                cell = builder._lab_cell(model['results'][key])
                self.assertIn(cell, index, (model['slug'], key))

    def test_model_pages_carry_verdict_blocks_and_toc(self):
        for model in builder.LAB_MODELS:
            page = (ROOT / 'dist/tiny-llms' / model['slug'] / 'index.html').read_text(encoding='utf-8')
            self.assertIn(model['verdict'], page)
            self.assertIn('<time datetime="%s">' % model['date'], page)
            for key, _ in builder.heading_anchors(
                    builder.template(ROOT, 'lab-model.html', toc='', task_rows='',
                                     name='', params='', lead='', date='2000-01-01',
                                     date_label='', verdict='', verdict_class='',
                                     symbol='', why='', limits='', repro=''))[1]:
                self.assertIn('href="#%s"' % key, page, (model['slug'], key))

    def test_methodology_uses_toc_and_portuguese_probe(self):
        page = (ROOT / 'dist/tiny-llms/methodology/index.html').read_text(encoding='utf-8')
        self.assertIn('lang="pt-BR"', page)
        self.assertIn('<time datetime="2026-09-08">', page)
        self.assertIn('href="#scoring-rubric"', page)

    def test_sitemap_gains_lab_urls_and_feed_unchanged(self):
        sitemap = (ROOT / 'dist/sitemap.xml').read_text(encoding='utf-8')
        for url in LAB_URLS:
            self.assertIn(url, sitemap)
        feed = (ROOT / 'dist/feed.xml').read_text(encoding='utf-8')
        for url in LAB_URLS:
            self.assertNotIn(url, feed)
        posts = (ROOT / 'dist/posts.json').read_text(encoding='utf-8')
        for url in LAB_URLS:
            self.assertNotIn(url, posts)

    def test_footer_links_lab_and_css_delta_is_token_only(self):
        home = (ROOT / 'dist/index.html').read_text(encoding='utf-8')
        self.assertIn('href="/tiny-llms/"', home)
        css = (ROOT / 'assets/site.css').read_text(encoding='utf-8')
        delta = css.split('Tiny LLM capability lab', 1)[1]
        self.assertNotRegex(delta, r'#[0-9a-fA-F]{3,8}\b')
        self.assertNotIn('rgb(', delta)
        self.assertNotIn('@import', delta)
        self.assertNotIn('!important', delta)
        self.assertNotIn('@media', delta)

    def test_lab_index_template_has_no_placeholders(self):
        text = (ROOT / 'templates/lab-index.html').read_text(encoding='utf-8')
        self.assertNotIn('$', text)


if __name__ == '__main__':
    unittest.main()
