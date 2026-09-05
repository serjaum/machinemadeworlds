"""End-to-end publishing contract. Run: python -m unittest discover -s tests -v."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]

class PublishingTests(unittest.TestCase):
    def test_new_post_scaffold_is_a_draft_and_never_overwrites_content(self):
        import importlib.util
        import tempfile
        script = ROOT / 'scripts/new_post.py'
        self.assertTrue(script.exists(), 'Missing safe new-post command')
        spec = importlib.util.spec_from_file_location('mmw_new_post', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / 'content').mkdir()
            (target / 'content/site.json').write_text((ROOT / 'content/site.json').read_text(encoding='utf-8'), encoding='utf-8')
            module.create_post(target, 'another-guide', 'Another guide', 'local-ai', '2026-09-05')
            path = target / 'content/posts/another-guide.json'
            data = json.loads(path.read_text(encoding='utf-8'))
            self.assertTrue(data['draft'])
            self.assertTrue(path.with_suffix('.html').exists())
            with self.assertRaises(FileExistsError):
                module.create_post(target, 'another-guide', 'Overwrite', 'local-ai', '2026-09-05')
            self.assertEqual(json.loads(path.read_text())['title'], 'Another guide')
            with self.assertRaises(ValueError):
                module.create_post(target, '../escape', 'Title', 'local-ai', '2026-09-05')

    def test_draft_to_publication_updates_every_index_without_editing_templates(self):
        import importlib.util
        import tempfile
        import shutil
        spec = importlib.util.spec_from_file_location('mmw_build_cycle', ROOT / 'scripts/build.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            for name in ('content', 'templates', 'assets'):
                shutil.copytree(ROOT / name, target / name)
            path = target / 'content/posts/future-test.json'
            data = dict(title='A test-only new article', description='', date='2026-09-06',
                        topic='design', kind='Essay', lead='', draft=True)
            path.write_text(json.dumps(data), encoding='utf-8')
            path.with_suffix('.html').write_text('<p>Test article content.</p>', encoding='utf-8')
            self.assertEqual(module.build(target)['posts'], 6)
            self.assertNotIn('future-test', (target / 'dist/feed.xml').read_text(encoding='utf-8'))
            data.update(draft=False, description='A fixture for the publishing contract.', lead='Test introduction.')
            path.write_text(json.dumps(data), encoding='utf-8')
            self.assertEqual(module.build(target)['posts'], 7)
            for f in ('index.html', 'blog/index.html', 'topics/design/index.html', 'posts.json', 'feed.xml', 'sitemap.xml'):
                self.assertIn('/posts/future-test/', (target / 'dist' / f).read_text(encoding='utf-8'), f)
            self.assertTrue((target / 'dist/posts/future-test/index.html').is_file())

    def test_invalid_content_cannot_escape_publish_boundary(self):
        import importlib.util
        import tempfile
        spec = importlib.util.spec_from_file_location('mmw_build', ROOT / 'scripts/build.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        site = json.loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / 'content/posts'
            folder.mkdir(parents=True)
            metadata = dict(title='A valid title', description='A description.', date='2026-09-05',
                            topic='design', kind='Essay', lead='Introduction.', draft=False)
            (folder / 'unsafe.json').write_text(json.dumps(metadata), encoding='utf-8')
            (folder / 'unsafe.html').write_text('<p>Hello</p><script>alert(1)</script>', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Unsafe'):
                module.load_posts(Path(tmp), site)

    def test_one_build_publishes_every_existing_article_in_index_and_feed(self):
        builder = ROOT / 'scripts/build.py'
        self.assertTrue(builder.is_file(), 'Missing shared static-site builder')
        result = subprocess.run([sys.executable, str(builder)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        posts = json.loads((ROOT / 'dist/posts.json').read_text(encoding='utf-8'))
        self.assertEqual(len(posts), 6, 'Preserve all six existing articles')
        archive = (ROOT / 'dist/blog/index.html').read_text(encoding='utf-8')
        feed = (ROOT / 'dist/feed.xml').read_text(encoding='utf-8')
        for post in posts:
            self.assertIn(post['url'], archive)
            self.assertIn(post['url'], feed)
            page = (ROOT / 'dist' / post['url'].strip('/') / 'index.html').read_text(encoding='utf-8')
            self.assertIn('id="main"', page)
            self.assertIn('rel="canonical"', page)
            self.assertIn('data-theme-toggle', page)

if __name__ == '__main__':
    unittest.main()
