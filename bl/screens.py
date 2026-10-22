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


def main():
    os.makedirs(TEX, exist_ok=True)
    app(768, 1120).save(os.path.join(TEX, 'screen_tablet.png'))
    app(512, 1088, phone=True).save(os.path.join(TEX, 'screen_phone.png'))
    print('wrote', os.path.join(TEX, 'screen_tablet.png'), 'and screen_phone.png')


if __name__ == '__main__':
    main()
