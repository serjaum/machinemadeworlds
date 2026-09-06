#!/usr/bin/env python3
"""QA buildlog-presence gate (MAC-64 standing rule).

Fails any change set that touches production output without a matching
build-log entry covering Motivation / Changes / Implementation /
Agent trail / Evidence.

Production output sources: content/posts/, templates/, scripts/build.py,
assets/, content/site.json (topics live in site.json).
Generated dist/ is excluded: it is rebuilt, never hand-edited.

Usage: python3 scripts/check_buildlog_presence.py [--base origin/main]
Exit 0 when the gate passes (or when no git baseline exists: warn-and-pass
so local one-off checkouts never break); exit 1 with a FAIL line otherwise.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROD_PREFIXES = ('content/posts/', 'templates/', 'scripts/build.py',
                 'assets/', 'content/site.json')

SECTION_MARKERS = ('motivation', 'what changed', 'how it was done',
                   'evidence', 'class="trail"')


def production_changes(changed):
    """Return the subset of changed repo-relative paths that affect dist/."""
    hits = []
    for path in changed:
        posix = path.replace('\\', '/')
        for prefix in PROD_PREFIXES:
            if posix == prefix or posix.startswith(prefix):
                hits.append(path)
                break
    return sorted(hits)


def entry_covers_sections(body):
    """A matching entry must cover all five standing-rule sections."""
    lowered = body.lower()
    return all(marker in lowered for marker in SECTION_MARKERS)


def check(changed, entries):
    """Pure gate: (ok, reason). entries maps slug -> (meta_dict, body_str)."""
    prod = production_changes(changed)
    if not prod:
        return True, 'no production-output changes'
    ready = [slug for slug, (meta, body) in entries.items()
             if not meta.get('draft', False) and entry_covers_sections(body)]
    if ready:
        return True, 'covered by buildlog entry: %s' % ', '.join(sorted(ready))
    return (False, 'FAIL: production files changed (%s) with no matching '
                   'non-draft content/buildlog entry covering Motivation / '
                   'Changes / Implementation / Agent trail / Evidence'
            % ', '.join(prod))


def git_lines(*args):
    out = subprocess.run(['git'] + list(args), cwd=ROOT, capture_output=True,
                         text=True, check=False)
    if out.returncode != 0:
        raise RuntimeError('git %s failed' % ' '.join(args))
    return [line for line in out.stdout.splitlines() if line.strip()]


def working_tree_entries():
    entries = {}
    folder = ROOT / 'content/buildlog'
    if not folder.is_dir():
        return entries
    for path in sorted(folder.glob('*.json')):
        try:
            meta = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        try:
            body = path.with_suffix('.html').read_text(encoding='utf-8')
        except OSError:
            body = ''
        entries[path.stem] = (meta, body)
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='origin/main')
    args = parser.parse_args()
    try:
        base = git_lines('merge-base', 'HEAD', args.base)[0]
        committed = git_lines('diff', '--name-only', base + '...HEAD')
        uncommitted = [line[3:] for line in git_lines('status', '--porcelain')
                       if line[:2].strip()]
        changed = sorted(set(committed) | set(uncommitted))
    except (RuntimeError, IndexError) as error:
        print('buildlog-presence: SKIP (no git baseline: %s)' % error)
        return 0
    ok, reason = check(changed, working_tree_entries())
    print('buildlog-presence: %s (%s)' % ('PASS' if ok else 'FAIL', reason))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
