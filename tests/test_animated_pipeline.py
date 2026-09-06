"""Animated pipeline diagram contract (MAC-102): CSS-only motion.

Run: python -m unittest discover -s tests -v.
"""
import importlib.util
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mmw_animated_build', ROOT / 'scripts/build.py')
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
                mac_id='MAC-102', pr=11,
                pr_url='https://github.com/serjaum/machinemadeworlds/pull/11',
                branch='feat/example', commit='5e54ca2',
                merge_sha='5e54ca2572844bca81cdf38d673d05355596e133',
                merge_note='', agents=['DEV'],
                stages=[stage()],
                reasoning={'DEV': 'First sentence here. Second sentence here.'})
    data.update(overrides)
    return data


class AnimatedPipelineTests(unittest.TestCase):
    def test_animation_classes_render_with_data_step_sequencing(self):
        stages = [stage(agent='Editor', stage='draft', verdict='done',
                        sha='1111111', rationale='Drafted.'),
                  stage(agent='DEV', stage='implement', verdict='BLOCK',
                        sha='2222222', rationale='Needs work.'),
                  stage(agent='DEV', stage='fix', verdict='done',
                        sha='3333333', rationale='Fixed.'),
                  stage(agent='SEC', stage='re-review', verdict='PASS',
                        sha='4444444', rationale='All green.')]
        html = builder.render_pipeline(meta(stages=stages))
        # Animation hook on the ordered list; every row sequenced.
        self.assertIn('<ol class="flow flow-anim">', html)
        steps = [int(v) for v in re.findall(r'data-step="(\d+)"', html)]
        self.assertEqual(steps, [1, 2, 3, 4, 5],
                         'stage rows plus one return-loop row, in order')
        self.assertIn('<li data-step="3" class="flow-loop">', html)
        # Existing diagram shapes keep rendering beside the hooks.
        for needle in ('flow-status', 'flow-flag', 'flow-why', 'flow-dots',
                       'PASS — re-review', '◆ BLOCK — implement', '↩ BLOCK → fix'):
            self.assertIn(needle, html)
        # Generated markup still passes the publish gate, deterministically.
        parser = builder.ArticleMarkup()
        parser.feed(html)
        parser.close()
        self.assertEqual(html, builder.render_pipeline(meta(stages=stages)))
        # Sequencing hooks are integers only at the gate.
        with self.assertRaisesRegex(ValueError, 'Unsafe data-step'):
            builder.ArticleMarkup().feed('<li data-step="1;drop">x</li>')

    def test_reduced_motion_block_disables_all_animation(self):
        source = (ROOT / 'assets/site.css').read_text(encoding='utf-8')
        match = re.search(r'@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{([^}]*)\}',
                          source)
        self.assertIsNotNone(match, 'reduced-motion block missing')
        block = match[0]
        self.assertIn('animation: none', block)
        self.assertIn('transition: none', block)

    def test_animation_css_stays_within_budget_and_token_only(self):
        source = (ROOT / 'assets/site.css').read_text(encoding='utf-8')
        anim = source.split('/* Pipeline animation')[1]
        self.assertLessEqual(len(anim.encode('utf-8')), 3072,
                             'animation addition exceeds 3KB raw')
        self.assertNotRegex(anim, r'#[0-9a-fA-F]{3,6}')
        for needle in ('rgb(', '@import', 'http', '!important', '@media', '.js'):
            self.assertNotIn(needle, anim)
        for needle in ('flow-anim', '@keyframes flow-stage', '@keyframes flow-loop',
                       '@keyframes flow-dot', 'flow-dots', 'animation-delay'):
            self.assertIn(needle, anim)

    def test_keyframes_animate_opacity_and_transform_only(self):
        source = (ROOT / 'assets/site.css').read_text(encoding='utf-8')
        anim = source.split('/* Pipeline animation')[1]
        frames = re.findall(r'@keyframes\s+\S+\s*\{((?:[^{}]|\{[^{}]*\})*)\}', anim)
        self.assertGreaterEqual(len(frames), 3)
        for body in frames:
            props = set(re.findall(r'([a-z-]+)\s*:', body))
            self.assertTrue(props, 'empty keyframe block')
            self.assertLessEqual(props, {'opacity', 'transform'},
                                 'keyframes must not shift layout: %s' % sorted(props))


if __name__ == '__main__':
    unittest.main()
