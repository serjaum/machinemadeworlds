#!/usr/bin/env python3
"""Create a draft article without duplicating site chrome or overwriting files."""
import argparse
from datetime import date
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

# SEO guard (MAC-647): SERP snippets truncate past ~155 chars; below ~50
# chars the snippet has no substance. Drafts may still be created with an
# empty description and completed later; any caller-supplied description
# must already sit inside the band.
DESCRIPTION_MIN = 50
DESCRIPTION_MAX = 155


def validate_description(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            'Description must contain %d-%d characters' % (DESCRIPTION_MIN, DESCRIPTION_MAX))
    if len(value) != len(value.strip()) or any(ord(c) < 32 for c in value):
        raise ValueError('Description must be a single trimmed line')
    if not DESCRIPTION_MIN <= len(value) <= DESCRIPTION_MAX:
        raise ValueError(
            'Description must contain %d-%d characters (got %d)'
            % (DESCRIPTION_MIN, DESCRIPTION_MAX, len(value)))
    return value


def create_post(root, slug, title, topic, published_date, description=None):
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
    pack = directory / (slug + '.dist-pack.md')
    if meta.exists() or body.exists() or pack.exists():
        raise FileExistsError(f'Post already exists: {slug}')
    data = dict(title=title, description='', date=published_date, topic=topic,
                kind='Essay', lead='', featured=False, draft=True)
    if description is not None:
        data['description'] = validate_description(description)
    with meta.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    try:
        with body.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write('<!-- Article body only. No header, footer, h1, script or inline styles. -->\n<p></p>\n')
        with pack.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write('X (0 chars):\n\n\nLinkedIn (0 words):\n\n\n'
                         'https://machinemadeworlds.com/posts/%s/\n\nRSS (0 chars):\n\n' % slug)
    except OSError:
        meta.unlink(missing_ok=True)
        body.unlink(missing_ok=True)
        pack.unlink(missing_ok=True)
        raise
    return meta, body, pack


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('slug')
    parser.add_argument('--title', required=True)
    parser.add_argument('--topic', required=True)
    parser.add_argument('--date', required=True, help='Actual publication date, YYYY-MM-DD')
    parser.add_argument('--description', default=None,
                        help='Optional meta description; when given it must be 50-155 chars')
    args = parser.parse_args()
    try:
        if args.description is not None:
            validate_description(args.description)
        for path in create_post(ROOT, args.slug, args.title, args.topic, args.date,
                                description=args.description):
            print(path.relative_to(ROOT))
        print('Draft created. Complete the metadata and body; set draft=false when ready.')
    except (ValueError, OSError) as error:
        parser.exit(1, str(error) + '\n')
