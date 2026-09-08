"""Data-pages contract (MAC-175/MAC-190). Run: python -m unittest discover -s tests -v."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_builder():
    spec = importlib.util.spec_from_file_location('mmw_build_data', ROOT / 'scripts/build.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DataPagesTests(unittest.TestCase):
    def test_data_files_validate(self):
        builder = load_builder()
        data = builder.load_data(ROOT)
        self.assertIn('prices', data)
        self.assertIn('benchmarks', data)
        for doc in data.values():
            for row in doc['rows']:
                self.assertTrue(row['source'].startswith('https://'))
                self.assertRegex(row['updated'], r'^\d{4}-\d{2}-\d{2}$')

    def test_missing_source_fails_build(self):
        builder = load_builder()
        prices = json.loads((ROOT / 'content/data/prices.json').read_text(encoding='utf-8'))
        bad = copy.deepcopy(prices)
        del bad['rows'][0]['source']
        with self.assertRaisesRegex(ValueError, 'source'):
            builder.validate_data_doc(bad, ('model', 'input_per_1m_usd', 'output_per_1m_usd'))

    def test_bad_date_fails_build(self):
        builder = load_builder()
        prices = json.loads((ROOT / 'content/data/prices.json').read_text(encoding='utf-8'))
        bad = copy.deepcopy(prices)
        bad['rows'][0]['updated'] = 'not-a-date'
        with self.assertRaises(ValueError):
            builder.validate_data_doc(bad, ('model', 'input_per_1m_usd', 'output_per_1m_usd'))

    def test_built_pages_carry_tables_stamps_sitemap_and_footer(self):
        builder = load_builder()
        result = builder.build(ROOT)
        self.assertGreaterEqual(result['pages'], 2)
        for path in ('prices/index.html', 'benchmarks/index.html'):
            page = (ROOT / 'dist' / path).read_text(encoding='utf-8')
            self.assertIn('<table', page)
            self.assertIn('Last updated', page)
            self.assertIn('Source', page)
        # Zero page-specific JS: content fragments carry no script tags.
        for name in ('prices.html', 'benchmarks.html'):
            fragment = (ROOT / 'templates' / name).read_text(encoding='utf-8')
            self.assertNotIn('<script', fragment)
        sitemap = (ROOT / 'dist/sitemap.xml').read_text(encoding='utf-8')
        self.assertIn('/prices/', sitemap)
        self.assertIn('/benchmarks/', sitemap)
        home = (ROOT / 'dist/index.html').read_text(encoding='utf-8')
        self.assertIn('/prices/', home)
        self.assertIn('/benchmarks/', home)


if __name__ == '__main__':
    unittest.main()
