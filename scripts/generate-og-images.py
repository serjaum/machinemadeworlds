#!/usr/bin/env python3
"""Deterministic per-post share cards (MAC-778, DESIGN_BRIEF_MAC-778.md).

Renders opaque 1200x630 PNG-24 cards: topic eyebrow + serif title + date
meta on the left, flat orbital motif on the right, existing brand tokens
only. Pure function of (title, topic, date, site name): no timestamps, no
network, no embedded metadata, so identical inputs give identical bytes.

Requires Pillow. scripts/build.py imports this module lazily: when Pillow
is missing (or rendering fails) the build warns and every page keeps the
generic social-card fallback instead of a broken og:image.

Usage: python3 scripts/generate-og-images.py [--out assets/og]
"""
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

WIDTH, HEIGHT = 1200, 630

# Existing brand tokens only (DESIGN_BRIEF_MAC-778 section 2, no new hex).
BG = (0x17, 0x1D, 0x1A)
CREAM = (0xF7, 0xF8, 0xF4)
CORE_GREEN = (0x20, 0x4C, 0x3D)
ACCENT = (0xB7, 0xD2, 0xA4)
MUTED = (0xAE, 0xBC, 0xAD)
RING = (0x65, 0x7D, 0x5D)
FIELD = (0x3B, 0x50, 0x36)

CONTENT_LEFT, CONTENT_RIGHT = 80, 780
COLUMN = CONTENT_RIGHT - CONTENT_LEFT
ART_CENTER = (985, 315)

FONT_CHAINS = {
    'serif': (('georgia.ttf', 'georgiab.ttf'),
              ('DejaVuSerif.ttf', 'DejaVuSerif-Bold.ttf')),
    'sans': (('arial.ttf', 'arialbd.ttf'),
             ('DejaVuSans.ttf', 'DejaVuSans-Bold.ttf')),
    'mono': (('consola.ttf', 'consolab.ttf'),
             ('DejaVuSansMono.ttf', 'DejaVuSansMono-Bold.ttf')),
}

_WINDOWS_FONTS = Path('C:/Windows/Fonts')


def _load_font(kind, size, bold=False):
    """First available face in the kind chain; system serif/sans/mono rasterization."""
    from PIL import ImageFont
    for regular, heavy in FONT_CHAINS[kind]:
        name = heavy if bold else regular
        for candidate in (_WINDOWS_FONTS / name, Path(name)):
            try:
                return ImageFont.truetype(str(candidate), size)
            except OSError:
                continue
    return ImageFont.load_default(size=size)


def _tracked_width(font, text, tracking):
    return sum(font.getlength(ch) for ch in text) + tracking * max(0, len(text) - 1)


def _draw_tracked(draw, xy, text, font, fill, tracking=0.0):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += font.getlength(ch) + tracking


def clean_title(title):
    """Collapse whitespace/newlines; raster carries no markup to escape."""
    return re.sub(r'\s+', ' ', title).strip()


def wrap_title(title, font, max_width, max_lines=3):
    """Word-boundary wrap; overflow truncates with an ellipsis on line 3."""
    words = clean_title(title).split(' ')
    lines, current = [], ''
    for word in words:
        trial = word if not current else current + ' ' + word
        if font.getlength(trial) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    if len(lines) <= max_lines:
        return lines
    kept = lines[:max_lines]
    tail = kept[-1]
    while tail and font.getlength(tail + ' …') > max_width:
        tail = tail.rsplit(' ', 1)[0] if ' ' in tail else tail[:-1]
    kept[-1] = (tail + ' …').strip()
    return kept


def render_card(title, topic_name, date_label, site_name='Machine Made Worlds',
                site_domain='machinemadeworlds.com'):
    """1200x630 RGB card per DESIGN_BRIEF_MAC-778 section 2 (left content, right art)."""
    import math
    from PIL import Image, ImageDraw

    serif = lambda size: _load_font('serif', size)
    serif_bold = lambda size: _load_font('serif', size, bold=True)
    sans_bold = lambda size: _load_font('sans', size, bold=True)
    mono = lambda size: _load_font('mono', size)

    title = clean_title(title)
    eyebrow = re.sub(r'\s+', ' ', topic_name).strip().upper()[:28]
    meta = ('%s · %s' % (date_label, site_name)).upper()

    probe = serif(48)
    lines = wrap_title(title, probe, COLUMN)
    title_size = 48 if len(lines) <= 2 else 44
    title_font = serif(title_size)
    lines = wrap_title(title, title_font, COLUMN)
    line_height = round(title_size * 1.12)
    title_tracking = -0.035 * title_size

    eyebrow_font = sans_bold(24)
    meta_font = mono(22)
    micro_font = mono(20)

    block = 24 + 18 + line_height * len(lines) + 20 + 22
    top = max(80, 300 - block // 2)

    img = Image.new('RGB', (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    # Right art zone: flat field disc, three rotated orbit strokes echoing
    # the in-page .orbital language, solid core disc, accent dot. Decorative.
    cx, cy = ART_CENTER
    draw.ellipse([cx - 150, cy - 150, cx + 150, cy + 150], fill=FIELD)
    for angle in (-35, 35, 90):
        rad = math.radians(angle)
        points = []
        for step in range(257):
            theta = 2 * math.pi * step / 256
            ex, ey = 190 * math.cos(theta), 129 * math.sin(theta)
            rx = ex * math.cos(rad) - ey * math.sin(rad)
            ry = ex * math.sin(rad) + ey * math.cos(rad)
            points.append((cx + rx, cy + ry))
        draw.line(points, fill=RING, width=2, joint='curve')
    draw.ellipse([cx - 85, cy - 85, cx + 85, cy + 85], fill=CORE_GREEN)
    monogram = serif_bold(56)
    label = 'mw.'
    mw = _tracked_width(monogram, label, 0)
    ascent, descent = monogram.getmetrics()
    draw.text((cx - mw / 2, cy - (ascent + descent) / 2), label,
              font=monogram, fill=CREAM)
    draw.ellipse([1105 - 8, 220 - 8, 1105 + 8, 220 + 8], fill=ACCENT)

    # Left content column, vertically centered as a block.
    y = top
    _draw_tracked(draw, (CONTENT_LEFT, y), eyebrow, eyebrow_font, ACCENT,
                  tracking=0.12 * 24)
    y += 24 + 18
    for line in lines:
        _draw_tracked(draw, (CONTENT_LEFT, y), line, title_font, CREAM,
                      tracking=title_tracking)
        y += line_height
    y += 20 - 4
    _draw_tracked(draw, (CONTENT_LEFT, y), meta, meta_font, MUTED,
                  tracking=0.08 * 22)

    # Brand micro-lockup bottom-left inside the safe frame.
    draw.rounded_rectangle([80, 552, 108, 580], radius=7, fill=CORE_GREEN)
    glyph = serif_bold(20)
    mark = 'm'
    gw = glyph.getlength(mark)
    gascent, gdescent = glyph.getmetrics()
    draw.text((94 - gw / 2, 566 - (gascent + gdescent) / 2), mark,
              font=glyph, fill=CREAM)
    draw.text((120, 556), site_domain, font=micro_font, fill=MUTED)

    return img


def card_png_bytes(title, topic_name, date_label, site_name='Machine Made Worlds',
                   site_domain='machinemadeworlds.com'):
    """PNG-24 bytes for one card; deterministic, no metadata chunks."""
    import io
    card = render_card(title, topic_name, date_label, site_name, site_domain)
    buffer = io.BytesIO()
    card.save(buffer, format='PNG')
    return buffer.getvalue()


def generate_all(root=ROOT, out_dir=None):
    """Render every post + build-log card; return [(slug, bytes)]."""
    spec = importlib.util.spec_from_file_location(
        'mmw_og_build', Path(root) / 'scripts' / 'build.py')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    site = builder.load_site(root) if hasattr(builder, 'load_site') else None
    if site is None:
        import json
        site = json.loads((Path(root) / 'content/site.json').read_text(encoding='utf-8'))
    posts = builder.load_posts(Path(root), site)
    entries = builder.load_buildlog(Path(root), site)
    cards = []
    for item in posts + entries:
        data = card_png_bytes(item['title'], item['topic_name'],
                              item['date_label'], site['name'])
        cards.append((item['slug'], data))
        if out_dir is not None:
            target = Path(out_dir) / (item['slug'] + '.png')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    return cards


def main():
    cards = generate_all(ROOT, ROOT / 'assets' / 'og')
    total = sum(len(data) for _, data in cards)
    over = [(slug, len(data)) for slug, data in cards if len(data) > 300 * 1024]
    print('og-images: %d cards, %d bytes total' % (len(cards), total))
    for slug, size in over:
        print('og-images: WARNING %s is %d bytes (target <300KB)' % (slug, size),
              file=sys.stderr)
    if any(len(data) > 1024 * 1024 for _, data in cards):
        print('og-images: FAIL: a card exceeds the 1MB hard cap', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
