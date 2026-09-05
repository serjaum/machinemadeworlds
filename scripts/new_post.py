#!/usr/bin/env python3
"""Create a draft article without duplicating site chrome or overwriting files."""
import argparse
from datetime import date
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def create_post(root, slug, title, topic, published_date):
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
        raise ValueError('Slug must contain lowercase words separated by hyphens')
    if not title.strip() or len(title) > 180:
        raise ValueError('Title must contain 1–180 characters')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', published_date):
        raise ValueError('Date must be YYYY-MM-DD')
    date.fromisoformat(published_date)
    site = json.loads((root / 'content/site.json').read_text(encoding='utf-8'))
    if topic not in site['topics']:
        raise ValueError('Unknown topic; choose one from content/site.json')
    directory = root / 'content/posts'
    directory.mkdir(parents=True, exist_ok=True)
    meta, body = directory / (slug + '.json'), directory / (slug + '.html')
    if meta.exists() or body.exists():
        raise FileExistsError(f'Post already exists: {slug}')
    data = dict(title=title, description='', date=published_date, topic=topic,
                kind='Essay', lead='', featured=False, draft=True)
    with meta.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    try:
        with body.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write('<!-- Article body only. No header, footer, h1, script or inline styles. -->\n<p></p>\n')
    except OSError:
        meta.unlink()
        raise
    return meta, body


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('slug')
    parser.add_argument('--title', required=True)
    parser.add_argument('--topic', required=True)
    parser.add_argument('--date', required=True, help='Actual publication date, YYYY-MM-DD')
    args = parser.parse_args()
    try:
        for path in create_post(ROOT, args.slug, args.title, args.topic, args.date):
            print(path.relative_to(ROOT))
        print('Draft created. Complete the metadata and body; set draft=false when ready.')
    except (ValueError, OSError) as error:
        parser.exit(1, str(error) + '\n')
