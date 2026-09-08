#!/usr/bin/env python3
"""Weekly data refresh check (MAC-175/MAC-190).

Validates content/data/prices.json + benchmarks.json through the same
gate the builder enforces (https source + YYYY-MM-DD per row), then
applies the staleness rule: any file-level or per-row `updated` older
than 10 days is STALE and the script exits 1 so the weekly digest job
opens a refresh PR instead of stamping a clean digest line.

Digest wiring (08:00 digest job): on success, copy the printed
`data updated YYYY-MM-DD` line into the digest PR body. On STALE,
open the refresh PR first; the digest goes out only after it merges.

Usage: python3 scripts/refresh_data.py [--today YYYY-MM-DD]
"""
import argparse
import importlib.util
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_builder():
    spec = importlib.util.spec_from_file_location(
        'mmw_build_data', ROOT / 'scripts/build.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(today):
    builder = load_builder()
    data = builder.load_data(ROOT)
    stale = []
    for name, doc in sorted(data.items()):
        age = (today - date.fromisoformat(doc['updated'])).days
        if age > 10:
            stale.append('%s file updated %s (%dd old)' % (name, doc['updated'], age))
        for row in doc['rows']:
            row_age = (today - date.fromisoformat(row['updated'])).days
            if row_age > 10:
                stale.append('%s row %s updated %s (%dd old)'
                             % (name, row.get('model', '?'), row['updated'], row_age))
    latest = max(doc['updated'] for doc in data.values())
    if stale:
        print('data STALE:')
        for line in stale:
            print('  - ' + line)
        return 1
    print('data updated %s' % latest)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--today', default=date.today().isoformat())
    args = parser.parse_args()
    try:
        today = date.fromisoformat(args.today)
    except ValueError:
        parser.exit(1, 'Date must be YYYY-MM-DD\n')
    try:
        code = check(today)
    except (ValueError, OSError, KeyError) as error:
        print('data refresh FAILED: %s' % error, file=sys.stderr)
        return 1
    return code


if __name__ == '__main__':
    sys.exit(main())
