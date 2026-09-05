#!/usr/bin/env python3
"""Create a draft build-log entry without duplicating site chrome or overwriting files."""
import argparse
from datetime import date
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

KINDS = ('Shipped', 'Fix', 'Experiment', 'Note')


def create_buildlog(root, slug, title, topic, kind, published_date):
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
        raise ValueError('Slug must contain lowercase words separated by hyphens')
    if not title.strip() or len(title) > 180:
        raise ValueError('Title must contain 1–180 characters')
    if kind not in KINDS:
        raise ValueError('Kind must be one of: ' + ', '.join(KINDS))
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', published_date):
        raise ValueError('Date must be YYYY-MM-DD')
    date.fromisoformat(published_date)
    site = json.loads((root / 'content/site.json').read_text(encoding='utf-8'))
    if topic not in site['topics']:
        raise ValueError('Unknown topic; choose one from content/site.json')
    directory = root / 'content/buildlog'
    directory.mkdir(parents=True, exist_ok=True)
    meta, body = directory / (slug + '.json'), directory / (slug + '.html')
    if meta.exists() or body.exists():
        raise FileExistsError(f'Build-log entry already exists: {slug}')
    data = dict(title=title, description='', date=published_date, topic=topic,
                kind=kind, lead='', featured=False, draft=True)
    with meta.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    try:
        with body.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write('<!-- Entry body only. No header, footer, h1, script or inline styles.\n'
                         '     End the file with the agent-trail block: a div.trail with an h2/h3,\n'
                         '     an ol of steps, and a time datetime="YYYY-MM-DD" per step. -->\n<p></p>\n')
    except OSError:
        meta.unlink()
        raise
    return meta, body


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('slug')
    parser.add_argument('--title', required=True)
    parser.add_argument('--topic', required=True)
    parser.add_argument('--kind', required=True, choices=KINDS)
    parser.add_argument('--date', required=True, help='Actual publication date, YYYY-MM-DD')
    args = parser.parse_args()
    try:
        for path in create_buildlog(ROOT, args.slug, args.title, args.topic, args.kind, args.date):
            print(path.relative_to(ROOT))
        print('Draft created. Complete the metadata and body; set draft=false when ready.')
    except (ValueError, OSError) as error:
        parser.exit(1, str(error) + '\n')
