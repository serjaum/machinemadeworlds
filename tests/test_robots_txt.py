"""Build-time robots.txt contract for explicit AI-crawler sections.

Run: python -m unittest discover -s tests -v.
"""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mmw_robots_build', ROOT / 'scripts/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

NAMED_BOTS = ('GPTBot', 'ChatGPT-User', 'ClaudeBot', 'anthropic-ai',
              'PerplexityBot', 'Google-Extended', 'CCBot')


class RobotsTxtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        builder.build(ROOT)
        cls.dist = ROOT / 'dist'
        cls.site = json.loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))
        cls.text = (cls.dist / 'robots.txt').read_text(encoding='utf-8')

    def test_default_section_preserved(self):
        self.assertIn('User-agent: *\nAllow: /', self.text)

    def test_each_named_crawler_has_allow_section(self):
        for bot in NAMED_BOTS:
            section = 'User-agent: %s\nAllow: /' % bot
            self.assertIn(section, self.text, bot)

    def test_sitemap_uses_canonical_site_url(self):
        self.assertIn('Sitemap: ' + self.site['url'] + '/sitemap.xml', self.text)

    def test_llms_txt_pointer_present(self):
        self.assertIn(self.site['url'] + '/llms.txt', self.text)

    def test_referenced_files_exist_in_dist(self):
        for name in ('robots.txt', 'sitemap.xml', 'llms.txt'):
            self.assertTrue((self.dist / name).is_file(), name)

    def test_rebuild_is_byte_identical(self):
        before = (self.dist / 'robots.txt').read_bytes()
        builder.build(ROOT)
        after = (self.dist / 'robots.txt').read_bytes()
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
