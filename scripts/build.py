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
    attributes = set('href title class id data-step src alt width height loading decoding scope colspan rowspan datetime aria-label'.split())

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
            if key == 'data-step' and not re.fullmatch(r'[0-9]{1,3}', value):
                raise ValueError('Unsafe data-step: sequencing integers only')
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
        # Belt-and-braces: distribution packs (*.dist-pack.md) are never
        # article sources and must never enter the publish artifact.
        if path.name.endswith('.dist-pack.json'):
            continue
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
    posts = sorted(posts, key=lambda p: (p['date'], p['slug']), reverse=True)
    featured = [p['slug'] for p in posts if p.get('featured')]
    if len(featured) > 1:
        raise ValueError(
            'Multiple featured posts (%s): only one non-draft post may set featured:true'
            % ', '.join(sorted(featured)))
    for missing in missing_dist_packs(root, posts):
        print('WARNING: post %s has no dist-pack (expected content/posts/%s.dist-pack.md)'
              % (missing, missing), file=sys.stderr)
    return posts


def missing_dist_packs(root, posts):
    """Slugs of non-draft posts without a beside-each-article pack file.

    Packs live at content/posts/<slug>.dist-pack.md and are never published;
    this is a warn-only presence gate (exit 0) so existing CI stays green."""
    missing = []
    folder = Path(root) / 'content/posts'
    for p in posts:
        # Drafts never enter the publish artifact, so they need no pack.
        if p.get('draft', False):
            continue
        if not (folder / (p['slug'] + '.dist-pack.md')).is_file():
            missing.append(p['slug'])
    return sorted(missing)


BUILDLOG_KINDS = frozenset(('Shipped', 'Fix', 'Experiment', 'Note'))

BUILDLOG_VERDICTS = frozenset(('PASS', 'BLOCK', 'FAIL', 'done', 'skipped'))
BUILDLOG_AGENTS = frozenset(('Editor', 'DEV', 'SEC', 'QA', 'SRE', 'Director'))
BUILDLOG_REPO = 'https://github.com/serjaum/machinemadeworlds'


def _require_iso_date(value, message):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError(message)
    date.fromisoformat(value)


def _sentence_count(text):
    return len([part for part in re.split(r'[.!?]+', text) if part.strip()])


VOICE_SIGLA = re.compile(r'[A-Z]+-[0-9]+')
VOICE_HEX = re.compile(r'[0-9a-f]{7,}')
VOICE_PR = re.compile(r'#\d+\b')
VOICE_BRANCH = re.compile(
    r'(?:feat|fix|chore|docs|content|scripts|assets|templates)/[A-Za-z0-9_.\-]+')
# Product names are human prose, not pipeline jargon (e.g. the GPT-6
# article subject); the voice gate carves them out.
VOICE_ALLOW = ('GPT-6',)


GLOSSARY_BACKLOG = 'content/data/glossary-backlog.json'


def load_glossary_links(root):
    """Shipped glossary terms as (term, url, aliases) triples.

    Only backlog entries marked shipped whose non-draft post exists are
    returned; unshipped aliases never fire. This allowlist keeps short
    acronyms from matching inside ordinary words while long unambiguous
    phrases still link. Deterministic order: by backlog order.
    """
    try:
        backlog = json.loads((root / GLOSSARY_BACKLOG).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []
    entries = backlog.get('terms', backlog) if isinstance(backlog, dict) else backlog
    if not isinstance(entries, list):
        return []
    shipped = []
    for item in entries:
        if not isinstance(item, dict) or item.get('status') != 'shipped':
            continue
        slug = item.get('slug', '')
        if not isinstance(slug, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
            continue
        try:
            meta = json.loads((root / 'content/posts' / ('glossary-' + slug + '.json')).read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        if meta.get('draft', False):
            continue
        aliases = [a.strip() for a in item.get('aliases', []) if isinstance(a, str) and a.strip()]
        if not aliases:
            continue
        term = item.get('term', slug).strip() or slug
        shipped.append((term, '/posts/glossary-' + slug + '/', sorted(aliases, key=len, reverse=True)))
    return shipped


def autolink_glossary(body, links, skip_url=None):
    """Link the first occurrence of each allowlisted alias.

    Matching is case-insensitive with strict boundaries (no adjacent
    letters, digits or hyphens), so a term never fires inside a longer
    word or a hyphenated compound, and text inside existing anchors
    (link labels and destinations alike) is left untouched. Only text
    nodes are scanned: markup itself is split into tags vs text first,
    so an alias inside a title/alt attribute (or any tag) can never be
    linkified and corrupt the tag.
    """
    if not links:
        return body
    ordered = sorted(links, key=lambda pair: (-len(pair[0]), pair[0].lower()))
    parts = re.split(r'(<a\b[^>]*>.*?</a>)', body, flags=re.S | re.I)
    subs = {}
    for index in range(0, len(parts), 2):
        subs[index] = re.split(r'(<[^>]*>)', parts[index])
    for alias, url in ordered:
        if skip_url is not None and url == skip_url:
            continue
        pattern = re.compile(r'(?<![A-Za-z0-9-])' + re.escape(alias) + r'(?![A-Za-z0-9-])', re.I)
        for index in range(0, len(parts), 2):
            sub = subs[index]
            for j in range(0, len(sub), 2):
                match = pattern.search(sub[j])
                if match:
                    sub[j] = (sub[j][:match.start()] + '<a href="%s">%s</a>' % (url, match.group(0))
                              + sub[j][match.end():])
                    break
            else:
                continue
            break
    for index, sub in subs.items():
        parts[index] = ''.join(sub)
    return ''.join(parts)


def glossary_related_block(slug, shipped):
    """Auto-inserted related-terms block for glossary detail pages."""
    others = sorted(((term, url) for term, url, _ in shipped if url != '/posts/' + slug + '/'),
                    key=lambda pair: pair[0].lower())
    if not others:
        return ('<h2>Related terms</h2><p>This is the first entry in the glossary series. '
                'New terms land here every weekday; browse <a href="/blog/">the journal</a> meanwhile.</p>')
    items = ''.join('<li><a href="%s">%s</a></li>' % (url, escape(term)) for term, url in others[:4])
    return '<h2>Related terms</h2><ul>' + items + '</ul>'


def validate_buildlog_voice(text, message):
    """Board voice rule (spec rev 4): article prose carries no task
    siglas, SHAs, branch or PR numbers. Traceability lives in JSON
    metadata plus link hrefs/titles only."""
    if not isinstance(text, str):
        raise ValueError(message)
    cleaned = text
    for token in VOICE_ALLOW:
        cleaned = cleaned.replace(token, '')
    if (VOICE_SIGLA.search(cleaned) or VOICE_HEX.search(cleaned)
            or VOICE_PR.search(cleaned) or VOICE_BRANCH.search(cleaned)):
        raise ValueError(message)


def validate_buildlog_stage(entry):
    """One ordered pipeline stage. Every stage traces to a real issue
    comment or PR event; the builder cannot check provenance, but it
    enforces shape: verdict allowlist, SHA presence (except skipped),
    rationale on BLOCK/FAIL, single-line rationale, valid date."""
    required = ('agent', 'stage', 'verdict', 'sha', 'rationale', 'at')
    if not isinstance(entry, dict) or set(entry) != set(required):
        raise ValueError('Invalid buildlog stage keys')
    if entry.get('agent') not in BUILDLOG_AGENTS:
        raise ValueError('Invalid buildlog stage agent')
    name = entry.get('stage')
    if not isinstance(name, str) or not name.strip() or len(name) > 80:
        raise ValueError('Invalid buildlog stage name')
    validate_buildlog_voice(name, 'Invalid buildlog stage voice')
    if entry.get('verdict') not in BUILDLOG_VERDICTS:
        raise ValueError('Invalid buildlog stage verdict')
    sha = entry.get('sha')
    if entry['verdict'] == 'skipped':
        if sha is not None:
            raise ValueError('Invalid buildlog stage sha')
    elif not isinstance(sha, str) or not re.fullmatch(r'[0-9a-f]{7,40}', sha):
        raise ValueError('Invalid buildlog stage sha')
    rationale = entry.get('rationale')
    if (not isinstance(rationale, str) or len(rationale) > 500
            or '\n' in rationale):
        raise ValueError('Invalid buildlog stage rationale')
    if entry['verdict'] in ('BLOCK', 'FAIL') and not rationale.strip():
        raise ValueError('Invalid buildlog stage rationale')
    validate_buildlog_voice(rationale, 'Invalid buildlog stage voice')
    _require_iso_date(entry.get('at'), 'Invalid buildlog stage date')


def validate_buildlog_reasoning(reasoning):
    """Per-agent reasoning summaries: 2-4 sentences each. Entries marked
    as unevidenced ('not evidenced' in the text) may use 1-4 sentences."""
    if not isinstance(reasoning, dict) or not reasoning:
        raise ValueError('Invalid buildlog reasoning')
    for agent, text in reasoning.items():
        if agent not in BUILDLOG_AGENTS:
            raise ValueError('Invalid buildlog reasoning agent')
        if not isinstance(text, str) or not text.strip() or len(text) > 1200:
            raise ValueError('Invalid buildlog reasoning')
        sentences = _sentence_count(text)
        if 'not evidenced' in text.lower():
            if not 1 <= sentences <= 4:
                raise ValueError('Invalid buildlog reasoning')
        elif not 2 <= sentences <= 4:
            raise ValueError('Invalid buildlog reasoning')
        validate_buildlog_voice(text, 'Invalid buildlog reasoning voice')


def validate_buildlog(p, site):
    # Gate parity with posts: same allowlist, same field limits, zero relaxations.
    validate_post(p, site)
    if p.get('kind') not in BUILDLOG_KINDS:
        raise ValueError('Invalid buildlog kind')
    for key in ('title', 'lead', 'description'):
        validate_buildlog_voice(p.get(key, ''), 'Invalid buildlog voice')
    # Spec MAC-47 item 1: provenance metadata, required on published entries.
    if not isinstance(p.get('mac_id'), str) or not re.fullmatch(r'MAC-\d{1,6}', p['mac_id']):
        raise ValueError('Invalid buildlog mac_id')
    # Spec MAC-72 item 2: machine-readable provenance. pr is an int PR
    # number (or null when there is no PR); pr_url must be the full public
    # PR URL for that number; merge_sha is the full 40-char merge SHA, or
    # null pre-merge with a reason in merge_note.
    pr = p.get('pr')
    if pr is not None and (type(pr) is not int or pr < 1):
        raise ValueError('Invalid buildlog pr')
    pr_url = p.get('pr_url')
    branch = p.get('branch')
    if pr is None:
        if pr_url is not None or branch is not None:
            raise ValueError('Invalid buildlog pr link')
    else:
        if pr_url != '%s/pull/%d' % (BUILDLOG_REPO, pr):
            raise ValueError('Invalid buildlog pr_url')
        if (not isinstance(branch, str)
                or not re.fullmatch(r'[A-Za-z0-9_.\-/]{1,120}', branch)):
            raise ValueError('Invalid buildlog branch')
    merge_sha = p.get('merge_sha')
    if (merge_sha is not None
            and (not isinstance(merge_sha, str)
                 or not re.fullmatch(r'[0-9a-f]{40}', merge_sha))):
        raise ValueError('Invalid buildlog merge_sha')
    merge_note = p.get('merge_note', '')
    if not isinstance(merge_note, str) or len(merge_note) > 300:
        raise ValueError('Invalid buildlog merge_note')
    if merge_sha is None and not merge_note.strip():
        raise ValueError('Invalid buildlog merge_note')
    stages = p.get('stages')
    if not isinstance(stages, list) or not stages:
        raise ValueError('Invalid buildlog stages')
    for entry in stages:
        validate_buildlog_stage(entry)
    for index, entry in enumerate(stages):
        # BLOCK/FAIL must be followed by return-loop entries
        # (fix SHA -> re-review), never left dangling.
        if entry['verdict'] in ('BLOCK', 'FAIL') and len(stages) < index + 3:
            raise ValueError('Invalid buildlog return loop')
    validate_buildlog_reasoning(p.get('reasoning'))
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
        validate_buildlog_voice(plain(p['body']), 'Invalid buildlog body voice')
        p['url'] = '/build-log/' + p['slug'] + '/'
        p['topic_name'] = site['topics'][p['topic']]
        p['reading'] = max(1, math.ceil(len(plain(p['body']).split()) / 220))
        p['date_label'] = date.fromisoformat(p['date']).strftime('%b %d, %Y')
        entries.append(p)
    return sorted(entries, key=lambda p: (p['date'], p['slug']), reverse=True)


DATA_FILES = {
    'prices': ('content/data/prices.json', ('model', 'input_per_1m_usd', 'output_per_1m_usd')),
    'benchmarks': ('content/data/benchmarks.json', ('model', 'benchmark', 'score')),
}


def _require_data_source(value):
    if (not isinstance(value, str) or not value.strip() or len(value) > 500
            or value != value.strip() or '\\' in value
            or any(ord(c) < 32 for c in value)
            or not value.startswith('https://') or value.startswith('//')):
        raise ValueError('Data rows require an https source URL')


def validate_data_doc(data, required):
    _require_iso_date(data.get('updated'), 'Data file requires updated YYYY-MM-DD')
    rows = data.get('rows')
    if not isinstance(rows, list) or not rows:
        raise ValueError('Data file requires a non-empty rows list')
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Data rows must be objects')
        for key in required:
            value = row.get(key)
            if not isinstance(value, str) or not value.strip() or len(value) > 120:
                raise ValueError('Data row requires %s' % key)
        _require_data_source(row.get('source'))
        _require_iso_date(row.get('updated'), 'Data rows require updated YYYY-MM-DD')
    return data


def load_data_file(root, relpath, required):
    path = root / relpath
    data = json.loads(path.read_text(encoding='utf-8'))
    validate_data_doc(data, required)
    data['updated_label'] = date.fromisoformat(data['updated']).strftime('%B %d, %Y')
    return data


def load_data(root=ROOT):
    root = Path(root)
    return {name: load_data_file(root, relpath, required)
            for name, (relpath, required) in DATA_FILES.items()}


def data_rows_html(data, cells):
    lines = []
    for row in data['rows']:
        tds = ''.join('<td>%s</td>' % escape(row[key]) for key in cells)
        lines.append(
            '<tr>%s<td><a href="%s">Source ↗</a></td>'
            '<td><time datetime="%s">%s</time></td></tr>'
            % (tds, escape(row['source'], quote=True),
               row['updated'], row['updated']))
    return '\n'.join(lines)


def _commit_link(sha, text):
    """Full SHA lives in the href + title only; visible text stays human
    (Board voice rule, spec rev 4)."""
    return '<a href="%s/commit/%s" title="%s">%s</a>' % (
        BUILDLOG_REPO, sha, sha, text)


def _stage_link(entry, text):
    sha = entry.get('sha')
    if isinstance(sha, str):
        return _commit_link(sha, text)
    return escape(text)


def render_pipeline(p):
    """Pipeline diagram block (MAC-78 clearance + Board voice rule, MAC-102
    animation): pure HTML+CSS rendered from the entry stages.
    ArticleMarkup-allowed tags only (div/span/table subset, h3, a), zero JS,
    zero external assets. Animation is decorative CSS sequencing: every
    list row carries a deterministic data-step hook (no schema change) and
    nth-child delays light stages up in execution order; all stage data
    stays in text/table for screen readers. Visible text is human prose —
    no siglas, SHAs, branch or PR numbers; identifiers live in link
    hrefs/titles and JSON metadata only. Deterministic."""
    links = []
    if p.get('pr_url') is not None:
        links.append('<a href="%s">the pull request</a>'
                     % escape(p['pr_url'], quote=True))
    if p.get('merge_sha') is not None:
        links.append(_commit_link(p['merge_sha'], 'the merge commit'))
    else:
        links.append('merge pending')
    if p.get('branch') is not None:
        # Branch heads are deleted after merge, so /tree/<branch> 404s on
        # merged entries. Point at the PR commits page instead: same branch
        # context, public-repo target, stays HTTP 200 after deletion.
        links.append('<a href="%s/commits" title="%s">the branch</a>'
                     % (escape(p['pr_url'], quote=True),
                        escape(p['branch'])))
    stages = p['stages']
    items = []
    step = 0
    for index, entry in enumerate(stages):
        verdict, agent, name = entry['verdict'], entry['agent'], entry['stage']
        label = '%s — %s' % (verdict, name)
        flagged = ' class="flow-flag"' if verdict in ('BLOCK', 'FAIL') else ''
        if verdict in ('BLOCK', 'FAIL'):
            label = '◆ ' + label
        duty = '%s · <time datetime="%s">%s</time>' % (
            escape(agent), entry['at'], entry['at'])
        if entry['rationale'].strip():
            duty += ' — %s' % escape(entry['rationale'].strip())
        step += 1
        items.append('<li data-step="%d"%s><span class="flow-status">%s</span><span>%s</span></li>'
                     % (step, flagged, escape(label), duty))
        # Linearized return loop: BLOCK/FAIL is followed by fix -> re-review.
        if verdict in ('BLOCK', 'FAIL'):
            fix, review = stages[index + 1], stages[index + 2]
            step += 1
            items.append('<li data-step="%d" class="flow-loop"><span>↩ %s → fix (%s) → re-review (%s)</span></li>'
                         % (step, escape(verdict), _stage_link(fix, 'the fix'),
                            _stage_link(review, 'the re-review')))
    rows = []
    for entry in stages:
        why = escape(entry['rationale'].strip()) if entry['rationale'].strip() else '—'
        rows.append('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                    % (escape(entry['stage']), escape(entry['agent']),
                       escape(entry['verdict']), _stage_link(entry, 'commit'), why))
    order = ('Editor', 'DEV', 'SEC', 'QA', 'SRE', 'Director')
    reasoning = p.get('reasoning') or {}
    whys = ''.join('<dt>%s</dt><dd>%s</dd>' % (agent, escape(reasoning[agent].strip()))
                   for agent in order if agent in reasoning)
    dots = ''.join('<span title="%s">●</span>'
                   % escape('%s — %s' % (entry['verdict'], entry['stage']))
                   for entry in stages)
    return ('<h3>Pipeline.</h3>'
            '<p>Each stage ran in order; blocked stages looped back through fix and re-review.</p>'
            '<p>%s</p>'
            '<ol class="flow flow-anim">%s</ol>'
            '<h3>Verdict trail.</h3>'
            '<table><thead><tr><th scope="col">Stage</th><th scope="col">Agent</th>'
            '<th scope="col">Verdict</th><th scope="col">SHA</th><th scope="col">Why</th></tr></thead>'
            '<tbody>%s</tbody></table>'
            '<h3>Why each step ran.</h3><dl class="flow-why">%s</dl>'
            '<h3>Receipts.</h3><p class="flow-dots">%s</p>'
            % (' · '.join(links), ''.join(items), ''.join(rows), whys, dots))


def insert_pipeline(body, pipeline_inner):
    """Nest the pipeline block inside the existing trail div (after its
    steps list); fall back to appending a standalone trail block."""
    match = None
    for found in re.finditer(r'</ol>\s*</div>', body):
        match = found
    if match is None:
        return body + '<div class="trail">' + pipeline_inner + '</div>'
    div_start = match.end() - len('</div>')
    return body[:match.start()] + '</ol>' + pipeline_inner + body[div_start:]


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
    # MAC-167: every topic carries its own Editor-drafted description, unique
    # sitewide, used for that topic page's meta/og description.
    topic_descriptions = site.get('topic_descriptions', {})
    if (set(topic_descriptions) != set(site['topics'])
            or any(not isinstance(v, str) or not v.strip() or len(v) > 320
                   for v in topic_descriptions.values())
            or len(set(topic_descriptions.values())) != len(topic_descriptions)):
        raise ValueError('Per-topic descriptions must be unique and cover every topic')
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

    def render(path, title, description, content, kind='WebPage', post=None, article=False):
        canonical = site['url'] + path
        # MAC-167 share card: one brand raster card (1200x630 PNG) for every
        # page. Site-wide defaults live here; the template only interpolates.
        og_image = site['url'] + assets['social-card.png']
        schema = {'@context': 'https://schema.org', '@type': kind, 'name': title,
                  'url': canonical, 'inLanguage': 'en'}
        if post:
            schema.update(headline=title, description=description,
                          datePublished=post['date'], dateModified=post.get('updated', post['date']),
                          mainEntityOfPage=canonical,
                          author={'@type': 'Organization', 'name': site['name']},
                          publisher={'@type': 'Organization', 'name': site['name']})
            if article:
                schema['image'] = og_image
        if article and post:
            stamp = lambda day: day + 'T00:00:00+00:00'
            article_meta = (
                '<meta property="article:published_time" content="%s" />\n    '
                '<meta property="article:modified_time" content="%s" />\n    '
                '<meta property="article:section" content="%s" />\n    '
                '<meta property="article:author" content="%s" />\n    '
                % (stamp(post['date']), stamp(post.get('updated', post['date'])),
                   escape(post['topic_name']), escape(site['name'])))
        else:
            article_meta = ''
        jsonld = json.dumps(schema, ensure_ascii=False).replace('<', '\\u003c')
        nav = lambda href: ' aria-current="page"' if path == href else ''
        build_current = ' aria-current="page"' if path.startswith('/build-log/') else ''
        text = template(root, 'base.html', title=escape(title), name=escape(site['name']),
                        description=escape(description), canonical=escape(canonical),
                        og_type='article' if post else 'website', jsonld=jsonld,
                        css=assets['site.css'], js=assets['site.js'], favicon=assets['favicon.svg'],
                        logo=assets['logo.svg'], og_image=og_image,
                        og_image_width='1200', og_image_height='630',
                        og_image_type='image/png',
                        og_image_alt='Machine Made Worlds — a journal of artificial intelligence',
                        twitter_card='summary_large_image', article_meta=article_meta,
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

    def archive(path, title, selected, copy, topics=topic_links, description=None):
        body = template(root, 'archive.html', heading=escape(title), count=len(selected),
                        topics=topics, cards=''.join(card(p, True) for p in selected), **copy)
        render(path, title + ' — ' + site['name'], description or site['description'], body, 'CollectionPage')
    archive('/blog/', 'The journal', posts, JOURNAL_COPY)
    for key, label in site['topics'].items():
        archive('/topics/' + key + '/', label, [p for p in posts if p['topic'] == key],
                JOURNAL_COPY, description=topic_descriptions[key])
    # Build-log index reuses the archive pattern with retargeted copy and no topic tabs.
    archive('/build-log/', 'Build log', entries, BUILDLOG_COPY, topics='')

    def detail(p, pool, index_url, index_label, back_label, related_label, pipeline=False, article=False):
        body = p['body']
        if p['url'].startswith('/posts/'):
            shipped = load_glossary_links(root)
            flat = [(alias, url) for _, url, aliases in shipped for alias in aliases]
            skip = p['url'] if p['slug'].startswith('glossary-') else None
            body = autolink_glossary(body, flat, skip_url=skip)
            if p['slug'].startswith('glossary-'):
                body = body + glossary_related_block(p['slug'], shipped)
        body, headings = heading_anchors(body)
        if pipeline and p.get('stages'):
            body = insert_pipeline(body, render_pipeline(p))
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
        render(p['url'], p['title'], p['description'], content, 'BlogPosting', post=p, article=article)

    for p in posts:
        detail(p, posts, '/blog/', 'The journal', '← Back to the journal', 'All articles ↗', article=True)
    for p in entries:
        detail(p, entries, '/build-log/', 'Build log', '← Back to the build log', 'All entries ↗',
               pipeline=True)

    render('/about/', 'About — ' + site['name'], site['description'],
           template(root, 'about.html'), 'AboutPage')
    render('/terms/', 'Terms of use — ' + site['name'],
           'Terms of Service for Segredo de Arquivo, the TikTok auto-upload service (forthcoming channel @segredodearquivo).',
           template(root, 'terms.html'), 'WebPage')
    render('/privacy/', 'Privacy notice — ' + site['name'],
           'Privacy Policy for Segredo de Arquivo: data for authentication and upload only, encrypted storage, no sale.',
           template(root, 'privacy.html'), 'WebPage')
    data = load_data(root)
    render('/prices/', 'Model API prices — ' + site['name'],
           'Indicative per-token list prices for widely used models, refreshed weekly.',
           template(root, 'prices.html', updated=data['prices']['updated'],
                    updated_label=data['prices']['updated_label'],
                    rows=data_rows_html(data['prices'], ('model', 'input_per_1m_usd', 'output_per_1m_usd'))),
           'WebPage')
    render('/benchmarks/', 'Model benchmarks — ' + site['name'],
           'Public eval scores for reference, refreshed weekly.',
           template(root, 'benchmarks.html', updated=data['benchmarks']['updated'],
                    updated_label=data['benchmarks']['updated_label'],
                    rows=data_rows_html(data['benchmarks'], ('model', 'benchmark', 'score'))),
           'WebPage')
    render('/404.html', 'Page not found — ' + site['name'], 'Find your way back to the journal.',
           template(root, '404.html'))
    render('/search/', 'Search — ' + site['name'],
           'Search every article in the journal. Results rank title matches first, then excerpts, then body text.',
           template(root, 'search.html'), 'SearchResultsPage')
    index = [{k: p[k] for k in ('url', 'title', 'description', 'date', 'reading', 'topic')} for p in posts]
    put('posts.json', json.dumps(index, ensure_ascii=False, indent=2) + '\n')
    search_docs = []
    for p in sorted(posts, key=lambda q: q['url']):
        text = re.sub(r'\s+', ' ', plain(p['body'])).strip()
        search_docs.append({'url': p['url'], 'title': p['title'],
                            'description': p['description'], 'date': p['date'],
                            'topic': p['topic'], 'topic_name': p['topic_name'],
                            'body': text})
    put('search-index.json', json.dumps(search_docs, ensure_ascii=False, indent=2) + '\n')
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
    feed_items = []
    for p in posts:
        canonical = site['url'] + p['url']
        published = datetime.fromisoformat(p['date']).replace(tzinfo=timezone.utc).isoformat()
        feed_items.append({'id': canonical, 'url': canonical, 'title': p['title'],
                           'summary': p['description'], 'content_text': p['description'],
                           'date_published': published, 'tags': [p['topic']]})
    feed = {'version': 'https://jsonfeed.org/version/1.1', 'title': site['name'],
            'home_page_url': site['url'] + '/', 'feed_url': site['url'] + '/feed.json',
            'description': site['description'], 'language': 'en', 'items': feed_items}
    put('feed.json', json.dumps(feed, ensure_ascii=False, indent=2) + '\n')
    urls = ['/', '/blog/', '/search/', '/build-log/', '/about/', '/terms/', '/privacy/', '/prices/', '/benchmarks/'] + [f'/topics/{k}/' for k in site['topics']] + [p['url'] for p in posts] + [p['url'] for p in entries]
    # Sitemap <lastmod> in W3C date form (YYYY-MM-DD). Date-only (not full
    # datetime) because every source date in this repo is day-granular, so a
    # timestamp would invent precision the content does not have.
    # Deterministic sources: post and build-log entry URLs use their own
    # date field; /prices/ and /benchmarks/ use their data file's updated
    # field; listing pages use the max date of the content they list
    # (/ is the journal home, so max post date; /blog/ max post date;
    # /build-log/ max entry date; each topic page max date of its posts);
    # pages that list nothing (/about/, /terms/, /privacy/, empty topics)
    # fall back to the UTC build date. All values clamp to the build date
    # so no URL ever carries a future date.
    today = datetime.now(timezone.utc).date().isoformat()
    def sitemap_date(value):
        if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            return today
        return min(value, today)
    lastmod = {p['url']: p['date'] for p in posts}
    lastmod.update({p['url']: p['date'] for p in entries})
    for p in posts:
        key = '/topics/' + p['topic'] + '/'
        if key not in lastmod or p['date'] > lastmod[key]:
            lastmod[key] = p['date']
    latest_post = max([p['date'] for p in posts], default='')
    latest_entry = max([p['date'] for p in entries], default='')
    lastmod['/'] = latest_post
    lastmod['/blog/'] = latest_post
    lastmod['/search/'] = latest_post
    lastmod['/build-log/'] = latest_entry
    lastmod['/prices/'] = data['prices']['updated']
    lastmod['/benchmarks/'] = data['benchmarks']['updated']
    sitemap = ET.Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    for path in urls:
        node = ET.SubElement(sitemap, 'url')
        ET.SubElement(node, 'loc').text = site['url'] + path
        ET.SubElement(node, 'lastmod').text = sitemap_date(lastmod.get(path))
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
