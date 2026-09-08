"""Distribution-pack presence gate (MAC-179/MAC-186).

Run: python -m unittest discover -s tests -v.
"""
import importlib.util
import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_builder(name='mmw_build_distpack'):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts/build.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stage_tree(target):
    for name in ('content', 'templates', 'assets'):
        shutil.copytree(ROOT / name, target / name)


class DistPackTests(unittest.TestCase):
    def test_missing_pack_warns_loudly(self):
        module = load_builder('mmw_build_distpack_missing')
        site = json.loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            stage_tree(target)
            # Ensure at least one non-draft post lacks its pack.
            for pack in (target / 'content/posts').glob('*.dist-pack.md'):
                pack.unlink()
            buf = io.StringIO()
            with redirect_stderr(buf):
                posts = module.load_posts(target, site)
            self.assertTrue(posts)
            missing = module.missing_dist_packs(target, posts)
            self.assertTrue(missing)
            self.assertIn('WARNING', buf.getvalue())
            self.assertIn(missing[0], buf.getvalue())

    def test_present_pack_stays_silent(self):
        module = load_builder('mmw_build_distpack_present')
        site = json.loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            stage_tree(target)
            for path in (target / 'content/posts').glob('*.json'):
                data = json.loads(path.read_text(encoding='utf-8'))
                if data.get('draft', False):
                    continue
                (target / 'content/posts' / (path.stem + '.dist-pack.md')).write_text(
                    '# pack\n', encoding='utf-8')
            buf = io.StringIO()
            with redirect_stderr(buf):
                posts = module.load_posts(target, site)
            self.assertEqual(module.missing_dist_packs(target, posts), [])
            self.assertNotIn('WARNING', buf.getvalue())

    def test_pack_text_never_leaks_into_article_pages(self):
        module = load_builder('mmw_build_distpack_noleak')
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            stage_tree(target)
            marker = 'DISTPACK-NOLEAK-MARKER-9f3a7'
            for path in (target / 'content/posts').glob('*.json'):
                data = json.loads(path.read_text(encoding='utf-8'))
                if data.get('draft', False):
                    continue
                (target / 'content/posts' / (path.stem + '.dist-pack.md')).write_text(
                    marker + ' ' + path.stem + '\n', encoding='utf-8')
            with redirect_stderr(io.StringIO()):
                module.build(target)
            for page in (target / 'dist/posts').rglob('index.html'):
                self.assertNotIn(marker, page.read_text(encoding='utf-8'))
            self.assertFalse(list((target / 'dist').rglob('*.dist-pack.md')))


if __name__ == '__main__':
    unittest.main()
