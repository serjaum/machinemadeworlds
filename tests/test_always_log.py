"""Always-log gate contract (MAC-64). Run: python -m unittest discover -s tests -v."""
import importlib.util
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'mmw_buildlog_presence', ROOT / 'scripts/check_buildlog_presence.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

FULL_BODY = ('<h2>Motivation</h2><p>Why.</p><h2>What changed</h2><p>What.</p>'
             '<h2>How it was done</h2><p>How.</p><h2>Verification evidence</h2>'
             '<p>Proof.</p><div class="trail"><h3>Trail.</h3><ol><li>'
             '<time datetime="2026-09-06">Sep 06, 2026</time><span>DEV.</span>'
             '</li></ol></div>')


def entry(draft=False, body=FULL_BODY):
    return ({'draft': draft}, body)


class AlwaysLogTests(unittest.TestCase):
    def test_non_production_changes_pass_without_an_entry(self):
        ok, _ = gate.check(['README.md', 'scripts/check_buildlog_presence.py',
                            'dist/index.html'], {})
        self.assertTrue(ok)

    def test_production_change_without_entry_fails(self):
        for changed in (['content/posts/new-post.json'], ['templates/post.html'],
                        ['scripts/build.py'], ['assets/site.css'],
                        ['content/site.json']):
            ok, reason = gate.check(changed, {})
            self.assertFalse(ok, changed)
            self.assertIn('FAIL', reason)

    def test_production_change_with_draft_entry_still_fails(self):
        ok, _ = gate.check(['content/posts/new-post.json'],
                           {'wip': entry(draft=True)})
        self.assertFalse(ok)

    def test_production_change_with_covering_entry_passes(self):
        ok, reason = gate.check(['content/posts/new-post.json'],
                                {'ship': entry()})
        self.assertTrue(ok)
        self.assertIn('ship', reason)

    def test_entry_missing_a_section_does_not_cover(self):
        thin = ({'draft': False}, '<h2>Motivation</h2><p>Why.</p>')
        ok, _ = gate.check(['templates/post.html'], {'thin': thin})
        self.assertFalse(ok)

    def test_hook_script_exists_and_passes_on_this_branch(self):
        self.assertTrue((ROOT / 'scripts/check_buildlog_presence.py').is_file())
        try:
            base = subprocess.run(['git', 'merge-base', 'HEAD', 'origin/main'],
                                  cwd=ROOT, capture_output=True, text=True,
                                  check=True).stdout.strip()
        except (subprocess.CalledProcessError, OSError, FileNotFoundError):
            self.skipTest('no git baseline available')
        if not base:
            self.skipTest('no git baseline available')
        proc = subprocess.run(['git', 'diff', '--name-only', base + '...HEAD'],
                              cwd=ROOT, capture_output=True, text=True)
        tracked = [l for l in proc.stdout.splitlines() if l.strip()]
        porcelain = subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT,
                                   capture_output=True, text=True)
        working = [l[3:] for l in porcelain.stdout.splitlines() if l.strip()]
        ok, reason = gate.check(sorted(set(tracked) | set(working)),
                                gate.working_tree_entries())
        self.assertTrue(ok, reason)


if __name__ == '__main__':
    unittest.main()
