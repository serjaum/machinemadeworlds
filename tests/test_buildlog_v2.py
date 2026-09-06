"""Build-log v2 contract (MAC-72): stages, return loops, links, reasoning, diagram.

Run: python -m unittest discover -s tests -v.
"""
import importlib.util
import json
import re
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mmw_buildlog_v2_build', ROOT / 'scripts/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def stage(**overrides):
    entry = dict(agent='DEV', stage='implement', verdict='PASS',
                 sha='5e54ca2572844bca81cdf38d673d05355596e133',
                 rationale='Did the work.', at='2026-09-06')
    entry.update(overrides)
    return entry


def meta(**overrides):
    data = dict(title='A valid title', description='A description.', date='2026-09-06',
                topic='design', kind='Shipped', lead='Introduction.', draft=False,
                mac_id='MAC-72', pr=11,
                pr_url='https://github.com/serjaum/machinemadeworlds/pull/11',
                branch='feat/example', commit='5e54ca2',
                merge_sha='5e54ca2572844bca81cdf38d673d05355596e133',
                merge_note='', agents=['DEV'],
                stages=[stage()],
                reasoning={'DEV': 'First sentence here. Second sentence here.'})
    data.update(overrides)
    return data


def load_one(data):
    site = json.loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        folder = root / 'content/buildlog'
        folder.mkdir(parents=True)
        (folder / 'entry.json').write_text(json.dumps(data), encoding='utf-8')
        (folder / 'entry.html').write_text('<p>Hello</p>', encoding='utf-8')
        return builder.load_buildlog(root, site)


class BuildLogV2Tests(unittest.TestCase):
    def test_block_without_rationale_fails(self):
        tail = [stage(agent='DEV', stage='fix', verdict='done', sha='aaaaaaa'),
                stage(agent='SEC', stage='re-review', verdict='PASS', sha='bbbbbbb')]
        for verdict in ('BLOCK', 'FAIL'):
            for bad in ('', '   '):
                with self.assertRaisesRegex(ValueError, 'Invalid buildlog stage rationale',
                                            msg=(verdict, repr(bad))):
                    load_one(meta(stages=[stage(verdict=verdict, rationale=bad)] + tail))

    def test_block_with_rationale_still_needs_return_loop(self):
        fix = stage(agent='DEV', stage='fix', verdict='done', sha='aaaaaaa')
        review = stage(agent='SEC', stage='re-review', verdict='PASS', sha='bbbbbbb')
        with self.assertRaisesRegex(ValueError, 'Invalid buildlog return loop'):
            load_one(meta(stages=[stage(verdict='BLOCK', rationale='Needs work.')]))
        with self.assertRaisesRegex(ValueError, 'Invalid buildlog return loop'):
            load_one(meta(stages=[stage(verdict='FAIL', rationale='Broke it.'), fix]))
        # Fix SHA -> re-review satisfies the loop.
        entries = load_one(meta(stages=[stage(verdict='BLOCK', rationale='Needs work.'),
                                        fix, review]))
        self.assertEqual(len(entries), 1)

    def test_stage_without_sha_fails_except_skipped(self):
        with self.assertRaisesRegex(ValueError, 'Invalid buildlog stage sha'):
            load_one(meta(stages=[stage(sha=None)]))
        with self.assertRaisesRegex(ValueError, 'Invalid buildlog stage sha'):
            load_one(meta(stages=[stage(sha='ZZZ')]))
        with self.assertRaisesRegex(ValueError, 'Invalid buildlog stage sha'):
            load_one(meta(stages=[stage(verdict='skipped', sha='aaaaaaa')]))
        entries = load_one(meta(stages=[stage(verdict='skipped', sha=None,
                                              rationale='Not needed.')]))
        self.assertEqual(len(entries), 1)

    def test_stage_shape_rules(self):
        base = stage()
        for key in ('agent', 'stage', 'verdict', 'sha', 'rationale', 'at'):
            broken = dict(base)
            del broken[key]
            with self.assertRaisesRegex(ValueError, 'Invalid buildlog stage keys', msg=key):
                load_one(meta(stages=[broken]))
        for field, bad in [('agent', 'Designer'), ('stage', ''), ('stage', 'x' * 81),
                           ('verdict', 'pass'), ('verdict', 'BLOCKED'),
                           ('rationale', 'has\nnewline'),
                           ('rationale', 'x' * 501), ('at', '09/06/2026')]:
            with self.assertRaisesRegex(ValueError, 'Invalid buildlog', msg=(field, bad)):
                load_one(meta(stages=[stage(**{field: bad})]))

    def test_pr_and_merge_link_rules(self):
        with self.assertRaisesRegex(ValueError, 'Invalid buildlog pr'):
            load_one(meta(pr='#11'))
        with self.assertRaisesRegex(ValueError, 'Invalid buildlog pr_url'):
            load_one(meta(pr_url='https://github.com/serjaum/machinemadeworlds/pull/12'))
        with self.assertRaisesRegex(ValueError, 'Invalid buildlog branch'):
            load_one(meta(branch='has space'))
        with self.assertRaisesRegex(ValueError, 'Invalid buildlog merge_sha'):
            load_one(meta(merge_sha='5e54ca2'))
        # Pre-merge entries carry a null SHA with a written reason.
        with self.assertRaisesRegex(ValueError, 'Invalid buildlog merge_note'):
            load_one(meta(merge_sha=None, merge_note=''))
        entries = load_one(meta(merge_sha=None, merge_note='Pre-merge: ships in the same PR.'))
        self.assertEqual(len(entries), 1)
        # Entries without a PR carry null links.
        with self.assertRaisesRegex(ValueError, 'Invalid buildlog pr link'):
            load_one(meta(pr=None, pr_url='https://github.com/serjaum/machinemadeworlds/pull/11'))
        entries = load_one(meta(pr=None, pr_url=None, branch=None))
        self.assertEqual(len(entries), 1)

    def test_reasoning_sentence_rules(self):
        with self.assertRaisesRegex(ValueError, 'Invalid buildlog reasoning'):
            load_one(meta(reasoning={'DEV': 'Only one sentence.'}))
        with self.assertRaisesRegex(ValueError, 'Invalid buildlog reasoning'):
            load_one(meta(reasoning={'DEV': 'One. Two. Three. Four. Five.'}))
        with self.assertRaisesRegex(ValueError, 'Invalid buildlog reasoning'):
            load_one(meta(reasoning={'Designer': 'First. Second.'}))
        with self.assertRaisesRegex(ValueError, 'Invalid buildlog reasoning'):
            load_one(meta(reasoning={}))
        entries = load_one(meta(reasoning={'QA': 'Not evidenced in the linked issues.'}))
        self.assertEqual(len(entries), 1)

    def test_diagram_renders_all_verdict_shapes_and_passes_markup_gate(self):
        stages = [stage(agent='Editor', stage='draft', verdict='done',
                        sha='1111111', rationale='Drafted.') ,
                  stage(agent='DEV', stage='implement', verdict='BLOCK',
                        sha='2222222', rationale='Needs work.'),
                  stage(agent='DEV', stage='fix', verdict='done',
                        sha='3333333', rationale='Fixed.'),
                  stage(agent='SEC', stage='re-review', verdict='FAIL',
                        sha='4444444', rationale='Still broken.'),
                  stage(agent='DEV', stage='fix-again', verdict='done',
                        sha='5555555', rationale='Fixed again.'),
                  stage(agent='QA', stage='review', verdict='PASS',
                        sha='6666666', rationale='All green.'),
                  stage(agent='SRE', stage='deploy', verdict='skipped',
                        sha=None, rationale='Not needed.')]
        data = meta(stages=stages)
        html = builder.render_pipeline(data)
        for needle in ('Pipeline.', 'Verdict trail.', 'Why each step ran.',
                       'Receipts.', 'flow-status', 'flow-loop', 'flow-flag',
                       'flow-why', 'flow-dots',
                       'PASS — review', '◆ BLOCK — implement', '◆ FAIL — re-review',
                       'done — draft', 'skipped — deploy', '↩ BLOCK → fix',
                       'the pull request', 'the merge commit', 'the branch',
                       'the fix', 'the re-review', '>commit</a>',
                       'title="5e54ca2572844bca81cdf38d673d05355596e133"',
                       'pull/11', 'commit/5e54ca2572844bca81cdf38d673d05355596e133',
                       '<th scope="col">Stage</th>', '<th scope="col">Why</th>'):
            self.assertIn(needle, html)
        self.assertEqual(html.count('class="flow-loop"'), 2)
        # Voice rule: no visible siglas, SHAs, branch or PR numbers.
        visible = re.sub(r'<[^>]+>', ' ', html)
        for token in ('1111111', '2222222', '#11', 'feat/example'):
            self.assertNotIn(token, visible)
        # ArticleMarkup parity: zero gate relaxations for generated markup.
        parser = builder.ArticleMarkup()
        parser.feed(html)
        parser.close()
        # Deterministic: same input renders byte-identical output.
        self.assertEqual(html, builder.render_pipeline(meta(stages=stages)))

    def test_diagram_pending_merge_row(self):
        html = builder.render_pipeline(meta(merge_sha=None, merge_note='Pre-merge.'))
        self.assertIn('merge pending', html)
        self.assertNotIn('the merge commit</a>', html)
        parser = builder.ArticleMarkup()
        parser.feed(html)
        parser.close()

    def test_branch_link_never_points_at_deleted_tree(self):
        # Merged PR head branches are deleted, so /tree/<branch> 404s (QA
        # FAIL on PR #11). The branch link must target the PR commits page,
        # which survives deletion, with human visible text.
        for data in (meta(),
                     meta(merge_sha=None, merge_note='Pre-merge.')):
            html = builder.render_pipeline(data)
            self.assertNotIn('/tree/', html)
            self.assertIn('pull/11/commits', html)
            self.assertIn('>the branch</a>', html)
            self.assertNotIn('feat/example</code>', html)

    def test_voice_rule_rejects_siglas_and_hashes_in_prose(self):
        for field, bad in [('title', 'Fix for MAC-72'),
                           ('lead', 'See PR #11.'),
                           ('description', 'At 5e54ca2.'),
                           ('reasoning', {'DEV': 'Fixed MAC-72. It works now.'})]:
            with self.assertRaisesRegex(ValueError, 'voice', msg=(field, bad)):
                load_one(meta(**{field: bad}))
        with self.assertRaisesRegex(ValueError, 'voice'):
            load_one(meta(stages=[stage(rationale='Pinned to 5e54ca2. Fix MAC-1.')] +
                                   [stage(agent='SEC', stage='re-review',
                                          verdict='PASS', sha='bbbbbbb'),
                                    stage(agent='QA', stage='recheck',
                                          verdict='PASS', sha='ccccccc')]))
        with self.assertRaisesRegex(ValueError, 'voice'):
            load_one(meta(stages=[stage(stage='fix MAC-2')]))
        # Product names are prose, not pipeline jargon.
        entries = load_one(meta(title='Shipping the GPT-6 Astra launch article'))
        self.assertEqual(len(entries), 1)

    def test_insert_pipeline_nests_inside_trail(self):
        body = ('<p>Hi</p><div class="trail"><h3>Trail.</h3><ol><li>x</li></ol></div>')
        merged = builder.insert_pipeline(body, '<h3>Pipeline.</h3>')
        self.assertLess(merged.index('<h3>Pipeline.</h3>'), merged.rindex('</div>'))
        self.assertIn('</ol><h3>Pipeline.</h3>', merged)
        fallback = builder.insert_pipeline('<p>No trail here.</p>', '<h3>Pipeline.</h3>')
        self.assertTrue(fallback.endswith('<div class="trail"><h3>Pipeline.</h3></div>'))

    def test_published_entries_all_carry_v2_provenance(self):
        site = json.loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))
        entries = builder.load_buildlog(ROOT, site)
        self.assertGreater(len(entries), 0)
        for entry in entries:
            for key in ('pr', 'pr_url', 'branch', 'merge_sha', 'merge_note',
                        'stages', 'reasoning'):
                self.assertIn(key, entry, '%s missing %s' % (entry['slug'], key))

    def test_flow_css_is_additive_and_token_only(self):
        source = (ROOT / 'assets/site.css').read_text(encoding='utf-8')
        flow = source.split('/* Pipeline diagram')[1]
        self.assertNotRegex(flow, r'#[0-9a-fA-F]{3,6}')
        for needle in ('rgb(', '@import', 'http', '!important', '@media', '.js'):
            self.assertNotIn(needle, flow)
        for token in ('var(--raised)', 'var(--surface)', 'var(--line)',
                      'var(--muted)', 'var(--accent)', 'var(--mono)',
                      'var(--sans)', 'var(--s1)', 'var(--s2)',
                      '.flow-dots'):
            self.assertIn(token, flow)

    def test_new_buildlog_scaffold_covers_v2_fields(self):
        modspec = importlib.util.spec_from_file_location(
            'mmw_new_buildlog_v2', ROOT / 'scripts/new_buildlog.py')
        mod = importlib.util.module_from_spec(modspec)
        modspec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / 'content').mkdir()
            (target / 'content/site.json').write_text(
                (ROOT / 'content/site.json').read_text(encoding='utf-8'), encoding='utf-8')
            mod.create_buildlog(target, 'v2-draft', 'V2 draft', 'design', 'Note', '2026-09-06')
            data = json.loads((target / 'content/buildlog/v2-draft.json').read_text(encoding='utf-8'))
            for key in ('pr', 'pr_url', 'branch', 'merge_sha', 'merge_note',
                        'stages', 'reasoning', 'commit', 'agents', 'mac_id'):
                self.assertIn(key, data)


if __name__ == '__main__':
    unittest.main()
