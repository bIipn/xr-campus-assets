"""The lit screens of the held props: a mock of the XR Libraries library app, drawn as textures for the tablet
(portrait, held by its short edge) and the phone. Swappable per client: change TITLE, the tiles and the
colours, or drop in a screenshot of their own app at the same size.

    python3 bl/screens.py   ->  assets/tex/screen_tablet.png, assets/tex/screen_phone.png (bl/props.py embeds them)
"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(os.path.dirname(HERE), 'assets', 'tex')

TITLE = 'XR Libraries'
TAGLINE = 'Learn anywhere'
BG = (14, 18, 24)
PANEL = (24, 30, 40)
INK = (236, 240, 244)
DIM = (150, 160, 172)
BRASS = (214, 174, 96)
TILES = [
    ('Ocean Dive', 'Science · 12 min', (24, 86, 128)),
    ('Dialysis Tech', 'Workforce · Course', (120, 48, 60)),
    ('Lost Stories', 'Oral history', (84, 64, 120)),
    ('World Builder', 'Make XR · Lesson 3', (36, 110, 80)),
    ('Pollinators', 'Climate · 8 min', (150, 110, 30)),
    ('Charleston 1865', 'History · Tour', (90, 90, 100)),
]


def font(size, weight='Regular'):
    for path in ('/usr/share/fonts/opentype/inter/Inter-%s.otf' % weight,
                 '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf' % ('-Bold' if weight in ('Bold', 'SemiBold') else '')):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def rounded(draw, box, radius, fill):
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def app(w, h, phone=False):
    im = Image.new('RGB', (w, h), BG)
    d = ImageDraw.Draw(im)
    s = w / 768.0                                  # everything scales with the width
    pad = int(40 * s)
    # status bar and header
    d.text((pad, int(26 * s)), '9:41', font=font(int(26 * s), 'Medium'), fill=DIM)
    d.text((w - pad - int(110 * s), int(26 * s)), '●●●  ▮', font=font(int(24 * s)), fill=DIM)
    y = int(84 * s)
    d.text((pad, y), TITLE, font=font(int(54 * s), 'SemiBold'), fill=INK)
    d.text((pad, y + int(66 * s)), TAGLINE, font=font(int(28 * s)), fill=BRASS)
    # search field
    y += int(128 * s)
    rounded(d, (pad, y, w - pad, y + int(68 * s)), int(20 * s), PANEL)
    d.text((pad + int(26 * s), y + int(18 * s)), 'Search experiences', font=font(int(28 * s)), fill=DIM)
    # tiles: two columns, a cover band and a caption each
    y += int(100 * s)
    cols = 1 if phone else 2
    gap = int(28 * s)
    tw = (w - 2 * pad - gap * (cols - 1)) // cols
    th = int((200 if phone else 250) * s)
    for i, (name, sub, colour) in enumerate(TILES):
        c, r = i % cols, i // cols
        x0 = pad + c * (tw + gap)
        y0 = y + r * (th + gap)
        if y0 + th > h - int(120 * s):
            break
        rounded(d, (x0, y0, x0 + tw, y0 + th), int(22 * s), PANEL)
        cover_h = int(th * 0.58)
        rounded(d, (x0, y0, x0 + tw, y0 + cover_h), int(22 * s), colour)
        d.rectangle((x0, y0 + cover_h - int(22 * s), x0 + tw, y0 + cover_h), fill=colour)
        # a little "3D" glyph on the cover
        gx, gy = x0 + tw - int(70 * s), y0 + int(22 * s)
        d.polygon([(gx, gy + int(14 * s)), (gx + int(24 * s), gy), (gx + int(48 * s), gy + int(14 * s)), (gx + int(24 * s), gy + int(28 * s))], outline=INK, width=max(1, int(3 * s)))
        d.text((x0 + int(22 * s), y0 + cover_h + int(16 * s)), name, font=font(int(30 * s), 'SemiBold'), fill=INK)
        d.text((x0 + int(22 * s), y0 + cover_h + int(56 * s)), sub, font=font(int(24 * s)), fill=DIM)
    # tab bar
    bar = int(110 * s)
    d.rectangle((0, h - bar, w, h), fill=PANEL)
    tabs = ['Home', 'Library', 'Courses', 'Me']
    for i, t in enumerate(tabs):
        cx = int((i + 0.5) * w / len(tabs))
        colour = BRASS if i == 0 else DIM
        d.ellipse((cx - int(14 * s), h - bar + int(22 * s), cx + int(14 * s), h - bar + int(50 * s)), outline=colour, width=max(1, int(3 * s)))
        f = font(int(22 * s), 'Medium')
        tw_ = d.textlength(t, font=f)
        d.text((cx - tw_ / 2, h - bar + int(60 * s)), t, font=f, fill=colour)
    return im


BOOK_TITLE = 'Lost Stories'
BOOK_TEXT = [
    "Every library keeps two collections. One sits on the shelves, catalogued and lent. The other is carried in "
    "through the door each morning by the people who come to read, to ask, to wait out the rain: the stories "
    "they have not written down. A branch that records them, even badly, keeps a town's memory from thinning.",
    "The first headsets arrived in boxes marked FRAGILE and spent a month under the reference desk. Nobody was "
    "sure who was allowed to touch them. Then a Saturday class of twelve-year-olds put them on, stood in a "
    "rainforest for six minutes, and came back asking where the books about frogs were. That was the day the "
    "boxes came out from under the desk.",
    "What a visit to a far place teaches is not the place but the wanting to know more about it. A good "
    "collection, like a good teacher, is mostly a way of keeping that wanting alive for a little longer than "
    "it would last on its own.",
    "The oral histories in this volume were recorded in branch libraries between 2019 and 2025. Where a "
    "speaker asked for a name to be changed, it has been. Where a story could be checked against the record, "
    "it was, and the record was sometimes the one that turned out to be wrong.",
    "A librarian in a mountain town kept a list, in pencil, of every question she could not answer. By the "
    "third year the list ran to nine pages, and the branch had become a place people came to with questions "
    "they had not thought were askable: how a grandfather's village had looked, what a river sounded like "
    "before the dam, whether the night sky had really been that full.",
    "The headsets answered some of these. Most of the rest were answered by the people in the room, who had "
    "been waiting, it turned out, for someone to ask.",
    "What follows is a selection, arranged by the year each story was told rather than the year it happened, "
    "because the telling is the part a library can keep.",
]


def wrap(draw, text, f, width):
    words, lines, line = text.split(), [], ''
    for w in words:
        t = (line + ' ' + w).strip()
        if draw.textlength(t, font=f) <= width:
            line = t
        else:
            lines.append(line); line = w
    if line:
        lines.append(line)
    return lines


def page(w, h, number, paragraphs, title=None, first=False):
    """One printed page: a running head, justified-looking paragraphs, a page number. Returns the image and
    the paragraphs that did not fit."""
    im = Image.new('RGB', (w, h), (246, 242, 232))
    d = ImageDraw.Draw(im)
    ink = (40, 36, 32)
    s = w / 640.0
    margin = int(58 * s)
    body = font(int(21 * s))
    y = int(54 * s)
    head = font(int(16 * s), 'Medium')
    d.text((margin, int(26 * s)), BOOK_TITLE.upper() if number % 2 == 0 else 'XR LIBRARIES', font=head, fill=(120, 112, 100))
    if first and title:
        tf = font(int(40 * s), 'SemiBold')
        d.text((margin, y), title, font=tf, fill=ink)
        y += int(70 * s)
        d.line((margin, y - int(12 * s), w - margin, y - int(12 * s)), fill=(160, 150, 136), width=max(1, int(2 * s)))
    leading = int(31 * s)
    left = list(paragraphs)
    while left:
        lines = wrap(d, left[0], body, w - 2 * margin)
        if y + leading * len(lines) > h - int(70 * s):
            break
        for i, ln in enumerate(lines):
            x = margin + (int(28 * s) if i == 0 else 0)
            d.text((x, y), ln, font=body, fill=ink)
            y += leading
        y += int(12 * s)
        left.pop(0)
    nf = font(int(17 * s))
    num = str(number)
    d.text((w - margin - d.textlength(num, font=nf) if number % 2 == 1 else margin, h - int(48 * s)), num, font=nf, fill=(110, 104, 94))
    return im, left


def main():
    os.makedirs(TEX, exist_ok=True)
    app(768, 1120).save(os.path.join(TEX, 'screen_tablet.png'))
    app(512, 1088, phone=True).save(os.path.join(TEX, 'screen_phone.png'))
    # the open book: 12.8 x 19 cm pages, the spread's left page first
    left, rest = page(640, 950, 42, BOOK_TEXT, title='The Boxes Under the Desk', first=True)
    right, _ = page(640, 950, 43, rest or BOOK_TEXT[2:])
    left.save(os.path.join(TEX, 'page_left.png')); right.save(os.path.join(TEX, 'page_right.png'))
    print('wrote', os.path.join(TEX, 'screen_tablet.png'), 'screen_phone.png, page_left.png, page_right.png')


if __name__ == '__main__':
    main()
