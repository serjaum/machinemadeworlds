"""Single-featured enforcement contract (MAC-129/MAC-130).

Run: python -m unittest discover -s tests -v.
"""
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_builder(name='mmw_build_featured'):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts/build.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stage_tree(target):
    for name in ('content', 'templates', 'assets'):
        shutil.copytree(ROOT / name, target / name)


def set_featured(target, slugs):
    for path in (target / 'content/posts').glob('*.json'):
        data = json.loads(path.read_text(encoding='utf-8'))
        data['featured'] = path.stem in slugs
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


class FeaturedTests(unittest.TestCase):
    def test_two_featured_fails_loudly(self):
        module = load_builder('mmw_build_featured_two')
        site = json.loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            stage_tree(target)
            set_featured(target, {'hello-machines', 'small-models-rtx2060'})
            with self.assertRaisesRegex(ValueError, 'hello-machines.*small-models-rtx2060|small-models-rtx2060.*hello-machines'):
                module.load_posts(target, site)
            with self.assertRaisesRegex(ValueError, 'featured'):
                module.build(target)

    def test_two_featured_cli_exits_nonzero(self):
        # build.py resolves the tree from its own location, not the cwd,
        # so the CLI check stages the patched builder inside the temp tree.
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            stage_tree(target)
            set_featured(target, {'hello-machines', 'small-models-rtx2060'})
            shutil.copytree(ROOT / 'scripts', target / 'scripts')
            result = subprocess.run([sys.executable, str(target / 'scripts/build.py')],
                                    cwd=target, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn('Build failed', result.stderr)
            self.assertIn('hello-machines', result.stderr)
            self.assertIn('small-models-rtx2060', result.stderr)

    def test_zero_featured_falls_back_to_newest(self):
        module = load_builder('mmw_build_featured_zero')
        site = json.loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            stage_tree(target)
            set_featured(target, set())
            posts = module.load_posts(target, site)
            self.assertTrue(posts)
            self.assertEqual([p for p in posts if p.get('featured')], [])
            newest = posts[0]
            module.build(target)
            homepage = (target / 'dist/index.html').read_text(encoding='utf-8')
            feature = homepage.split('<article class="featured">', 1)[1]
            self.assertIn(newest['url'], feature)
            self.assertIn(newest['title'], feature)

    def test_one_featured_wins(self):
        module = load_builder('mmw_build_featured_one')
        site = json.loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            stage_tree(target)
            set_featured(target, {'hello-machines'})
            posts = module.load_posts(target, site)
            self.assertEqual([p['slug'] for p in posts if p.get('featured')], ['hello-machines'])
            module.build(target)
            homepage = (target / 'dist/index.html').read_text(encoding='utf-8')
            feature = homepage.split('<article class="featured">', 1)[1]
            self.assertIn('/posts/hello-machines/', feature)


if __name__ == '__main__':
    unittest.main()
