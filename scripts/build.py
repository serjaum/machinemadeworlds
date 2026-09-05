#!/usr/bin/env python3
"""Deterministic static publishing. Python 3.10+, standard library only.

Content lives in content/posts/*.json + matching HTML fragments. Layout lives
in templates/. No runtime rendering, fetches, plugins, or build dependencies.
"""
from datetime import date, datetime, timezone
from email.utils import format_datetime
from hashlib import sha256
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
from string import Template
import json
import math
import re
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def plain(value):
    return unescape(re.sub(r'<[^>]+>', ' ', value))


class ArticleMarkup(HTMLParser):
    """Reject executable content; this is a publish gate, not an HTML sanitizer."""
    tags = set('p h2 h3 h4 ul ol li a blockquote pre code em strong b i table thead tbody tr th td caption figure figcaption img br hr div span dl dt dd small sup sub time abbr'.split())
    attributes = set('href title class id src alt width height loading decoding scope colspan rowspan datetime aria-label'.split())

    def handle_starttag(self, tag, attrs):
        if tag not in self.tags:
            raise ValueError(f'Unsafe article element: {tag}')
        for key, value in attrs:
            value = value or ''
            if key not in self.attributes:
                raise ValueError(f'Unsafe article attribute: {key}')
            if key in ('href', 'src'):
                if any(ord(c) < 32 for c in value) or value != value.strip() or '\\' in value:
                    raise ValueError('Unsafe URL characters')
                if not value.startswith(('/', '#', 'https://', 'http://', 'mailto:')) or value.startswith('//'):
                    raise ValueError('Unsafe URL scheme')
                if key == 'src' and not value.startswith('/assets/'):
                    raise ValueError('Unsafe media: store images under /assets/')
        if tag == 'img' and not {'alt', 'width', 'height'}.issubset(dict(attrs)):
            raise ValueError('Images require alt, width and height')


def validate_post(p, site):
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', p['slug']):
        raise ValueError('Invalid post slug')
    for key, limit in [('title', 180), ('description', 320), ('lead', 1200), ('kind', 40)]:
        if not isinstance(p.get(key), str) or not p[key].strip() or len(p[key]) > limit:
            raise ValueError(f'Invalid post {key}')
    if p.get('topic') not in site['topics']:
        raise ValueError('Unknown post topic')
    for key in ('date', 'updated'):
        if key == 'date' or key in p:
            if not isinstance(p[key], str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', p[key]):
                raise ValueError('Dates require YYYY-MM-DD')
            date.fromisoformat(p[key])
    for key in ('draft', 'featured'):
        if key in p and type(p[key]) is not bool:
            raise ValueError(f'{key} must be a JSON boolean')
    parser = ArticleMarkup()
    parser.feed(p['body'])
    parser.close()


def load_posts(root, site):
    posts = []
    for path in sorted((root / 'content/posts').glob('*.json')):
        p = json.loads(path.read_text(encoding='utf-8'))
        if type(p.get('draft', False)) is not bool:
            raise ValueError('draft must be a JSON boolean')
        # Drafts may be incomplete and never enter the publish artifact.
        if p.get('draft', False):
            continue
        p['slug'] = path.stem
        p['body'] = path.with_suffix('.html').read_text(encoding='utf-8')
        validate_post(p, site)
        p['url'] = '/posts/' + p['slug'] + '/'
        p['topic_name'] = site['topics'][p['topic']]
        p['reading'] = max(1, math.ceil(len(plain(p['body']).split()) / 220))
        p['date_label'] = date.fromisoformat(p['date']).strftime('%b %d, %Y')
        posts.append(p)
    return sorted(posts, key=lambda p: (p['date'], p['slug']), reverse=True)


BUILDLOG_KINDS = frozenset(('Shipped', 'Fix', 'Experiment', 'Note'))


def validate_buildlog(p, site):
    # Gate parity with posts: same allowlist, same field limits, zero relaxations.
    validate_post(p, site)
    if p.get('kind') not in BUILDLOG_KINDS:
        raise ValueError('Invalid buildlog kind')
    # Spec MAC-47 item 1: provenance metadata, required on published entries.
    if not isinstance(p.get('mac_id'), str) or not re.fullmatch(r'MAC-\d{1,6}', p['mac_id']):
        raise ValueError('Invalid buildlog mac_id')
    if not isinstance(p.get('pr'), str) or not re.fullmatch(r'(#\d{1,6}|n/a)', p['pr']):
        raise ValueError('Invalid buildlog pr')
    if not isinstance(p.get('commit'), str) or not re.fullmatch(r'([0-9a-f]{7,40}|n/a)', p['commit']):
        raise ValueError('Invalid buildlog commit')
    agents = p.get('agents')
    if (not isinstance(agents, list) or not agents
            or any(not isinstance(a, str) or not a.strip() or len(a) > 40 for a in agents)):
        raise ValueError('Invalid buildlog agents')


def load_buildlog(root, site):
    entries = []
    folder = root / 'content/buildlog'
    if not folder.is_dir():
        return []
    for path in sorted(folder.glob('*.json')):
        p = json.loads(path.read_text(encoding='utf-8'))
        if type(p.get('draft', False)) is not bool:
            raise ValueError('draft must be a JSON boolean')
        # Drafts may be incomplete and never enter the publish artifact.
        if p.get('draft', False):
            continue
        p['slug'] = path.stem
        p['body'] = path.with_suffix('.html').read_text(encoding='utf-8')
        validate_buildlog(p, site)
        p['url'] = '/build-log/' + p['slug'] + '/'
        p['topic_name'] = site['topics'][p['topic']]
        p['reading'] = max(1, math.ceil(len(plain(p['body']).split()) / 220))
        p['date_label'] = date.fromisoformat(p['date']).strftime('%b %d, %Y')
        entries.append(p)
    return sorted(entries, key=lambda p: (p['date'], p['slug']), reverse=True)


def template(root, filename, **values):
    return Template((root / 'templates' / filename).read_text(encoding='utf-8')).substitute(values)


def heading_anchors(body):
    """Stable, unique anchors for the server-rendered table of contents."""
    headings, seen = [], {}
    def replace(match):
        label = plain(match[1]).strip()
        base = re.sub(r'[^a-z0-9]+', '-', label.lower()).strip('-') or 'section'
        seen[base] = seen.get(base, 0) + 1
        key = base if seen[base] == 1 else f'{base}-{seen[base]}'
        headings.append((key, label))
        return f'<h2 id="{key}">{match[1]}</h2>'
    return re.sub(r'<h2>(.*?)</h2>', replace, body, flags=re.S), headings


def build(root=ROOT):
    root = Path(root)
    site = json.loads((root / 'content/site.json').read_text(encoding='utf-8'))
    posts = load_posts(root, site)
    entries = load_buildlog(root, site)
    output = root / 'dist'
    staging = root / '.build-staging'
    if staging.is_symlink() or output.is_symlink():
        raise ValueError('Build directories must not be symlinks')
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir()

    def put(path, text):
        target = staging / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8', newline='\n')

    assets = {}
    for source in sorted((root / 'assets').iterdir()):
        data = source.read_bytes()
        name = f'{source.stem}.{sha256(data).hexdigest()[:12]}{source.suffix}'
        assets[source.name] = '/assets/' + name
        target = staging / 'assets' / name
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(data)

    def render(path, title, description, content, kind='WebPage', post=None):
        canonical = site['url'] + path
        schema = {'@context': 'https://schema.org', '@type': kind, 'name': title,
                  'url': canonical, 'inLanguage': 'en'}
        if post:
            schema.update(headline=title, description=description,
                          datePublished=post['date'], dateModified=post.get('updated', post['date']),
                          mainEntityOfPage=canonical,
                          author={'@type': 'Organization', 'name': site['name']},
                          publisher={'@type': 'Organization', 'name': site['name']})
        jsonld = json.dumps(schema, ensure_ascii=False).replace('<', '\\u003c')
        nav = lambda href: ' aria-current="page"' if path == href else ''
        build_current = ' aria-current="page"' if path.startswith('/build-log/') else ''
        text = template(root, 'base.html', title=escape(title), name=escape(site['name']),
                        description=escape(description), canonical=escape(canonical),
                        og_type='article' if post else 'website', jsonld=jsonld,
                        css=assets['site.css'], js=assets['site.js'], favicon=assets['favicon.svg'],
                        theme_init=(root / 'templates/theme-init.js').read_text(encoding='utf-8').strip(),
                        content=content, year=max((p['date'][:4] for p in posts), default='2026'),
                        home_current=nav('/'), blog_current=nav('/blog/'),
                        build_current=build_current, about_current=nav('/about/'))
        put('404.html' if path == '/404.html' else path.strip('/') + '/index.html' if path != '/' else 'index.html', text)

    def card(p, compact=False):
        return template(root, 'card.html', url=p['url'], title=escape(p['title']),
                        topic=p['topic'], topic_name=escape(p['topic_name']),
                        description=escape(p['description']), date=p['date'],
                        date_label=p['date_label'], reading=p['reading'],
                        kind=escape(p['kind']), extra=' compact' if compact else '')

    topic_links = ''.join(f'<a href="/topics/{key}/">{escape(label)} <span aria-hidden="true">↗</span></a>'
                          for key, label in site['topics'].items())
    featured = next((p for p in posts if p.get('featured')), posts[0] if posts else None)
    feature = template(root, 'featured.html', url=featured['url'],
                       title=escape(featured['title']), description=escape(featured['description']),
                       topic_name=escape(featured['topic_name']), kind=escape(featured['kind']),
                       date=featured['date'], date_label=featured['date_label'], reading=featured['reading']) if featured else ''
    remaining = [p for p in posts if p != featured]
    home = template(root, 'home.html', featured=feature,
                    stories=''.join(card(p) for p in remaining[:2]),
                    more=''.join(card(p, compact=True) for p in remaining[2:5]), topics=topic_links)
    render('/', site['name'] + ' — AI, considered.', site['description'], home, 'WebSite')

    JOURNAL_COPY = dict(eyebrow='Ideas, collected',
                        lede='Essays, guides and observations. Find something worth sitting with.',
                        archive_root='/blog/', count_noun='articles',
                        search_label='Search the journal', search_placeholder='Try ‘models’ or ‘design’',
                        empty_title='No articles found.',
                        empty_text='Try a different word, or return to the full collection.')
    BUILDLOG_COPY = dict(eyebrow='Built in the open',
                         lede='What changed on this site, and why. Short entries from the agents that run it.',
                         archive_root='/build-log/', count_noun='entries',
                         search_label='Search the build log', search_placeholder="Try 'deploy' or 'fix'",
                         empty_title='No entries found.',
                         empty_text='Try a different word, or return to the full log.')

    def archive(path, title, selected, copy, topics=topic_links):
        body = template(root, 'archive.html', heading=escape(title), count=len(selected),
                        topics=topics, cards=''.join(card(p, True) for p in selected), **copy)
        render(path, title + ' — ' + site['name'], site['description'], body, 'CollectionPage')
    archive('/blog/', 'The journal', posts, JOURNAL_COPY)
    for key, label in site['topics'].items():
        archive('/topics/' + key + '/', label, [p for p in posts if p['topic'] == key], JOURNAL_COPY)
    # Build-log index reuses the archive pattern with retargeted copy and no topic tabs.
    archive('/build-log/', 'Build log', entries, BUILDLOG_COPY, topics='')

    def detail(p, pool, index_url, index_label, back_label, related_label):
        body, headings = heading_anchors(p['body'])
        # Content refers to stable source names; publishing resolves hashed URLs.
        asset_urls = {'/assets/' + key: value for key, value in assets.items()}
        asset_urls.update({'/styles.css': assets['site.css'], '/tokens.css': assets['site.css']})
        def asset_url(match):
            if match[2] not in asset_urls:
                raise ValueError(f'Unknown article asset: {match[2]}')
            return match[1] + asset_urls[match[2]] + match[3]
        body = re.sub(r'''((?:href|src)=["'])(/assets/[^"']+|/styles.css|/tokens.css)(["'])''', asset_url, body)
        body = body.replace('<pre>', '<pre tabindex="0" role="region" aria-label="Code example">')
        body = body.replace('<table>', '<table tabindex="0" aria-label="Article data">')
        toc = ''.join(f'<a href="#{key}">{escape(label)}</a>' for key, label in headings)
        # Same-collection-first so build-log status voice never mixes into journal related grids.
        related = sorted((q for q in pool if q != p), key=lambda q: q['topic'] != p['topic'])[:2]
        content = template(root, 'post.html', title=escape(p['title']), lead=escape(p['lead']),
                           topic=p['topic'], topic_name=escape(p['topic_name']), kind=escape(p['kind']),
                           date=p['date'], date_label=p['date_label'], reading=p['reading'],
                           body=body, toc=toc, toc_hidden='' if headings else ' hidden',
                           related=''.join(card(q, True) for q in related),
                           index_url=index_url, index_label=index_label,
                           back_label=back_label, related_label=related_label)
        render(p['url'], p['title'], p['description'], content, 'BlogPosting', post=p)

    for p in posts:
        detail(p, posts, '/blog/', 'The journal', '← Back to the journal', 'All articles ↗')
    for p in entries:
        detail(p, entries, '/build-log/', 'Build log', '← Back to the build log', 'All entries ↗')

    render('/about/', 'About — ' + site['name'], site['description'],
           template(root, 'about.html'), 'AboutPage')
    render('/404.html', 'Page not found — ' + site['name'], 'Find your way back to the journal.',
           template(root, '404.html'))
    index = [{k: p[k] for k in ('url', 'title', 'description', 'date', 'reading', 'topic')} for p in posts]
    put('posts.json', json.dumps(index, ensure_ascii=False, indent=2) + '\n')
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    for key, value in [('title', site['name']), ('link', site['url']), ('description', site['description']), ('language', 'en')]:
        ET.SubElement(channel, key).text = value
    for p in posts:
        item = ET.SubElement(channel, 'item')
        for key, value in [('title', p['title']), ('link', site['url'] + p['url']),
                           ('guid', site['url'] + p['url']), ('description', p['description']),
                           ('pubDate', format_datetime(datetime.fromisoformat(p['date']).replace(tzinfo=timezone.utc)))]:
            ET.SubElement(item, key).text = value
    put('feed.xml', ET.tostring(rss, encoding='unicode', xml_declaration=True))
    urls = ['/', '/blog/', '/build-log/', '/about/'] + [f'/topics/{k}/' for k in site['topics']] + [p['url'] for p in posts] + [p['url'] for p in entries]
    sitemap = ET.Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    for path in urls:
        ET.SubElement(ET.SubElement(sitemap, 'url'), 'loc').text = site['url'] + path
    put('sitemap.xml', ET.tostring(sitemap, encoding='unicode', xml_declaration=True))
    put('robots.txt', 'User-agent: *\nAllow: /\nSitemap: ' + site['url'] + '/sitemap.xml\n')
    put('.htaccess', (root / 'templates/htaccess').read_text(encoding='utf-8'))
    # Replace only the generated directory, and only after a successful render.
    if output.exists():
        shutil.rmtree(output)
    staging.rename(output)
    return {'posts': len(posts), 'buildlog': len(entries), 'pages': len(urls) + 1, 'files': len(list(output.rglob('*.*')))}


if __name__ == '__main__':
    try:
        print(json.dumps(build(), indent=2))
    except (ValueError, OSError, KeyError) as error:
        print(f'Build failed: {error}', file=sys.stderr)
        sys.exit(1)
