"""Meta-description length contract (MAC-647). Run: python -m unittest discover -s tests -v."""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIN_LEN = 50
MAX_LEN = 155


def _load(name):
    spec = importlib.util.spec_from_file_location('mmw_meta_' + name.replace('.', '_'),
                                                  ROOT / 'scripts' / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MetaDescriptionTests(unittest.TestCase):
    def test_every_published_post_description_fits_the_serp_band(self):
        bad = []
        for path in sorted((ROOT / 'content/posts').glob('*.json')):
            if path.name.endswith('.dist-pack.json'):
                continue
            data = json.loads(path.read_text(encoding='utf-8'))
            if data.get('draft', False):
                continue
            length = len(data.get('description', ''))
            if not MIN_LEN <= length <= MAX_LEN:
                bad.append('%s is %d chars' % (path.stem, length))
        self.assertEqual(bad, [], 'Descriptions must stay within %d-%d chars' % (MIN_LEN, MAX_LEN))

    def test_new_post_rejects_out_of_band_descriptions(self):
        module = _load('new_post.py')
        with self.assertRaises(ValueError):
            module.validate_description('x' * (MAX_LEN + 1))
        with self.assertRaises(ValueError):
            module.validate_description('too short')
        self.assertEqual(module.validate_description('x' * MIN_LEN), 'x' * MIN_LEN)

    def test_build_reports_out_of_band_descriptions(self):
        module = _load('build.py')
        self.assertEqual(module.meta_description_violations(
            [{'slug': 'ok', 'description': 'x' * MIN_LEN}]), [])
        self.assertEqual(module.meta_description_violations(
            [{'slug': 'long', 'description': 'x' * (MAX_LEN + 1)}]),
            [('long', MAX_LEN + 1)])


if __name__ == '__main__':
    unittest.main()
