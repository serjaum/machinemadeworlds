"""Glossary term-a-day contract (MAC-177).

Covers: seeded backlog (30 terms, first shipped), opening term validity,
careful auto-linking (allowlist, no false positives, anchors untouched,
self-links skipped) and the auto-inserted related-terms block.

Run: python -m unittest discover -s tests -v.
"""
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_builder(name='mmw_build_glossary'):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts/build.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stage_tree(target):
    for name in ('content', 'templates', 'assets'):
        shutil.copytree(ROOT / name, target / name)
    shutil.copytree(ROOT / 'scripts', target / 'scripts')


class GlossaryTests(unittest.TestCase):
    def test_backlog_seeded_with_thirty_terms(self):
        backlog = json.loads((ROOT / 'content/data/glossary-backlog.json').read_text(encoding='utf-8'))
        terms = backlog['terms']
        self.assertGreaterEqual(len(terms), 30)
        slugs = [t['slug'] for t in terms]
        self.assertEqual(len(set(slugs)), len(slugs))
        orders = [t['order'] for t in terms]
        self.assertEqual(sorted(orders), list(range(1, len(terms) + 1)))
        for term in terms:
            self.assertRegex(term['slug'], r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
            self.assertTrue(term['term'].strip())
            self.assertTrue(term['aliases'])
            self.assertIn(term['status'], ('open', 'shipped'))
        shipped = [t for t in terms if t['status'] == 'shipped']
        self.assertTrue(shipped)
        first = next(t for t in terms if t['order'] == 1)
        self.assertEqual(first['status'], 'shipped')

    def test_opening_term_loads_as_glossary_post(self):
        module = load_builder('mmw_build_glossary_post')
        site = json.loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            stage_tree(target)
            posts = module.load_posts(target, site)
            opening = next(p for p in posts if p['slug'] == 'glossary-prompt-injection')
            self.assertEqual(opening['kind'], 'Glossary')
            self.assertEqual(opening['topic'], 'essays')
            self.assertTrue(opening['title'].startswith('What is'))
            words = len(opening['body'].split())
            self.assertGreaterEqual(words, 80)

    def test_autolink_fires_only_for_shipped_allowlist(self):
        module = load_builder('mmw_build_glossary_links')
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            stage_tree(target)
            shipped = module.load_glossary_links(target)
            self.assertTrue(any(url == '/posts/glossary-prompt-injection/' for _, url, _ in shipped))
            # Unshipped backlog aliases must never fire.
            fired_urls = {url for _, url, _ in shipped}
            self.assertNotIn('/posts/glossary-quantization/', fired_urls)
            digest = (target / 'content/posts/ai-news-2026-09-05.html').read_text(encoding='utf-8')
            flat = [(alias, url) for _, url, aliases in shipped for alias in aliases]
            linked = module.autolink_glossary(digest, flat)
            self.assertIn('<a href="/posts/glossary-prompt-injection/">prompt injections</a>', linked)
            # Existing anchors stay untouched: the source URL keeps exactly one href.
            self.assertEqual(linked.count('https://the-decoder.com/openais-gpt-6-astra-hallucinates-less-but-remains-vulnerable-to-hidden-prompt-injections/'), 1)
            # No false positive inside ordinary words.
            coverage = module.autolink_glossary('<p>Independent coverage of the launch.</p>', flat)
            self.assertNotIn('/posts/glossary-', coverage)

    def test_hyphenated_compounds_never_link(self):
        module = load_builder('mmw_build_glossary_hyphen')
        body = '<p>Halved capability-hallucination to a low rate.</p>'
        out = module.autolink_glossary(body, [('hallucination', '/posts/glossary-hallucination/')])
        self.assertEqual(out, body)

    def test_glossary_page_skips_self_link_but_links_outward(self):
        module = load_builder('mmw_build_glossary_self')
        body = '<p>Prompt injection differs from jailbreaking.</p>'
        out = module.autolink_glossary(
            body,
            [('prompt injection', '/posts/glossary-prompt-injection/'),
             ('jailbreaking', '/posts/glossary-jailbreaking/')],
            skip_url='/posts/glossary-prompt-injection/')
        self.assertNotIn('/posts/glossary-prompt-injection/', out)
        self.assertIn('<a href="/posts/glossary-jailbreaking/">jailbreaking</a>', out)

    def test_autolink_leaves_tag_attributes_untouched(self):
        module = load_builder('mmw_build_glossary_attrs')
        links = [('prompt injection', '/posts/glossary-prompt-injection/')]
        body = ('<p><img src="/assets/x.png" alt="prompt injection diagram" '
                'title="prompt injection overview"></p>')
        self.assertEqual(module.autolink_glossary(body, links), body)
        body2 = ('<p title="prompt injection">Prompt injection matters.</p>')
        out2 = module.autolink_glossary(body2, links)
        self.assertIn('title="prompt injection"', out2)
        self.assertIn('<a href="/posts/glossary-prompt-injection/">Prompt injection</a> matters.', out2)

    def test_related_block_covers_first_and_later_terms(self):
        module = load_builder('mmw_build_glossary_related')
        first = module.glossary_related_block('glossary-prompt-injection',
                                              [('Prompt injection', '/posts/glossary-prompt-injection/', ['prompt injection'])])
        self.assertIn('Related terms', first)
        self.assertIn('/blog/', first)
        later = module.glossary_related_block(
            'glossary-prompt-injection',
            [('Prompt injection', '/posts/glossary-prompt-injection/', ['prompt injection']),
             ('Benchmark', '/posts/glossary-benchmark/', ['benchmark']),
             ('Evals', '/posts/glossary-evals/', ['evals'])])
        self.assertIn('/posts/glossary-benchmark/', later)
        self.assertIn('/posts/glossary-evals/', later)
        self.assertNotIn('/posts/glossary-prompt-injection/', later)

    def test_built_digest_links_to_opening_term(self):
        module = load_builder('mmw_build_glossary_render')
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            stage_tree(target)
            module.build(target)
            digest = (target / 'dist/posts/ai-news-2026-09-05/index.html').read_text(encoding='utf-8')
            self.assertIn('/posts/glossary-prompt-injection/', digest)
            term = (target / 'dist/posts/glossary-prompt-injection/index.html').read_text(encoding='utf-8')
            self.assertIn('Related terms', term)
            self.assertNotIn('href="/posts/glossary-prompt-injection/"', term)


if __name__ == '__main__':
    unittest.main()
