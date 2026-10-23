"""The slides every talk and class shows on its screens, drawn from unreal/Pipeline/content/talks.json (or the client
pack's own talks.json): a title slide, content slides with the exhibit art or a line drawing beside the points, and a
closing slide. Same look as the campus UI: ink and teal panels, brass rules and kickers, bone text, Cormorant Garamond
titles, Inter for the points.

    python3 bl/slides.py            ->  unreal/Pipeline/out/slides/<talk>/<nn>.png + index.json

In another language (WTA_LANG, or the pack's "language") the slides' words come from lang/<lang>/tables.json
(the DT_Talks rows) and the builder's own few words ("A talk", the venue names) from lang/<lang>/builders.json.

Each slide is drawn at 1920 x 1080 and stored at 2048 x 1024 (a power of two, so Unreal can mip it; the screen quads
are 16:9 with UVs 0..1, so the squeeze is undone on the wall). index.json lists the slides per talk for the importer.
"""
import json
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import clientpack  # noqa: E402

ROOT = os.path.dirname(HERE)
CONTENT = os.path.join(ROOT, 'unreal', 'Pipeline', 'content')
ART = os.path.join(ROOT, 'unreal', 'Pipeline', 'out', 'campus', 'art')
OUT = os.path.join(ROOT, 'unreal', 'Pipeline', 'out', 'slides')
FONTS = os.path.join(HERE, 'fonts')

W, H = 1920, 1080
STORE = (2048, 1024)
INK = (13, 22, 19)
PANEL = (21, 34, 30)
TEAL = (28, 52, 47)
BRASS = (205, 169, 97)
BRASS_DIM = (125, 104, 64)
BONE = (239, 231, 213)
BONE_DIM = (190, 184, 170)


def talks_file():
    """The client pack's talks.json when it has one, else the campus default."""
    pack = clientpack.folder() if hasattr(clientpack, 'folder') else None
    if pack:
        p = os.path.join(pack, 'talks.json')
        if os.path.exists(p):
            return p
    return os.path.join(CONTENT, 'talks.json')


def language():
    """WTA_LANG (build_client.py sets it from the pack's campus.json "language"), else the pack's, else English."""
    return (os.environ.get('WTA_LANG') or clientpack.get('language') or 'en').strip().lower()


def builder_words(lang):
    """lang/<lang>/builders.json: the few words this builder draws itself ("A talk", the venue names); English otherwise."""
    p = os.path.join(CONTENT, 'lang', lang, 'builders.json')
    if lang == 'en' or not os.path.exists(p):
        return {}
    with open(p, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def apply_language(talks, lang):
    """The talks' words from lang/<lang>/tables.json (the DT_Talks rows, the shape extract_tables.py lists; the
    slides line up with talks.json's one for one) over talks.json, so the slides are drawn in the pack's language.
    Returns how many fields changed."""
    p = os.path.join(CONTENT, 'lang', lang, 'tables.json')
    if lang == 'en' or not os.path.exists(p):
        return 0
    with open(p, 'r', encoding='utf-8') as fh:
        rows = json.load(fh).get('DT_Talks', {})
    n = 0
    for talk in talks:
        row = rows.get(talk['id']) or {}
        for src, dst in (('Title', 'title'), ('Subtitle', 'subtitle')):
            if row.get(src):
                talk[dst] = row[src]
                n += 1
        if row.get('SpeakerRole') and isinstance(talk.get('speaker'), dict):
            talk['speaker']['role'] = row['SpeakerRole']
            n += 1
        for i, over in enumerate(row.get('Slides') or []):
            if not over or i >= len(talk['slides']):
                continue
            slide = talk['slides'][i]
            if over.get('Title'):
                slide['title'] = over['Title']
                n += 1
            if over.get('Points'):
                old = slide.get('points', [])
                slide['points'] = [pt if pt is not None else (old[j] if j < len(old) else '') for j, pt in enumerate(over['Points'])]
                n += 1
    return n


def font(kind, size):
    paths = {
        'title': os.path.join(FONTS, 'CormorantGaramond-SemiBold.ttf'),
        'title_b': os.path.join(FONTS, 'CormorantGaramond-Bold.ttf'),
        'italic': os.path.join(FONTS, 'CormorantGaramond-MediumItalic.ttf'),
        'text': '/usr/share/fonts/opentype/inter/Inter-Regular.otf',
        'text_m': '/usr/share/fonts/opentype/inter/Inter-Medium.otf',
        'text_sb': '/usr/share/fonts/opentype/inter/Inter-SemiBold.otf',
    }
    p = paths[kind]
    if not os.path.exists(p):
        p = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    return ImageFont.truetype(p, size)


def background():
    """A deep teal-ink field, lighter toward the upper left, with a faint vignette."""
    im = Image.new('RGB', (W, H), INK)
    px = im.load()
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            t = max(0.0, 1.0 - math.hypot((x - W * 0.28) / W, (y - H * 0.2) / H) * 1.25)
            c = tuple(int(INK[i] + (TEAL[i] - INK[i]) * t * 0.85) for i in range(3))
            px[x, y] = c
            if x + 1 < W: px[x + 1, y] = c
            if y + 1 < H:
                px[x, y + 1] = c
                if x + 1 < W: px[x + 1, y + 1] = c
    return im


BG = None


def kicker(d, xy, text, size=26, fill=BRASS):
    f = font('text_sb', size)
    x, y = xy
    for ch in text.upper():
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + size * 0.16
    return x


def wrap(d, text, f, width):
    words, lines, line = text.split(), [], ''
    for w in words:
        t = (line + ' ' + w).strip()
        if d.textlength(t, font=f) <= width:
            line = t
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def framed(im, art, box):
    """Paste an exhibit image into box (x0, y0, x1, y1), fitted, with a brass hairline and a soft shadow."""
    x0, y0, x1, y1 = box
    a = Image.open(art).convert('RGBA')
    a.thumbnail((x1 - x0, y1 - y0), Image.LANCZOS)
    ax = x0 + (x1 - x0 - a.width) // 2
    ay = y0 + (y1 - y0 - a.height) // 2
    sh = Image.new('RGBA', (a.width + 80, a.height + 80), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle((40, 40, 40 + a.width, 40 + a.height), fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    im.paste(sh, (ax - 40 + 10, ay - 40 + 16), sh)
    im.paste(a, (ax, ay), a)
    ImageDraw.Draw(im).rectangle((ax - 1, ay - 1, ax + a.width, ay + a.height), outline=BRASS_DIM, width=2)


# ---------------------------------------------------------------- line drawings for the class
FIG = (980, 820)        # every drawing is made on a canvas this size, then fitted into its panel


def figure(name, im, box):
    """Draw figure `name` on its own canvas and fit it into box on the slide."""
    canvas = Image.new('RGB', FIG, PANEL)
    draw_figure(name, canvas)
    # crop to what was drawn, so every drawing fills its panel whatever its own size
    bb = ImageChops.difference(canvas, Image.new('RGB', FIG, PANEL)).getbbox() or (0, 0, FIG[0], FIG[1])
    pad = 36
    canvas = canvas.crop((max(0, bb[0] - pad), max(0, bb[1] - pad), min(FIG[0], bb[2] + pad), min(FIG[1], bb[3] + pad)))
    x0, y0, x1, y1 = box
    k = min((x1 - x0) / canvas.width, (y1 - y0) / canvas.height, 1.7)
    fit = canvas.resize((int(canvas.width * k), int(canvas.height * k)), Image.LANCZOS)
    im.paste(fit, (x0 + (x1 - x0 - fit.width) // 2, y0 + (y1 - y0 - fit.height) // 2))


def draw_figure(name, im):
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = 40, 40, FIG[0] - 40, FIG[1] - 40
    cx, cy = FIG[0] // 2, FIG[1] // 2 - 30
    w = x1 - x0
    lw = 5
    lab = font('text_m', 30)
    small = font('text', 26)

    def label(text, x, y, f=lab, fill=BONE):
        tw = d.textlength(text, font=f)
        d.text((x - tw / 2, y), text, font=f, fill=fill)

    if name == 'vr_ar_mr':
        # three panels: a world that fills the frame, a cube over a room, a cube sitting on a table
        pw = (w - 60) // 3
        for i, (title, kind) in enumerate((('VR', 'vr'), ('AR', 'ar'), ('MR', 'mr'))):
            px0 = x0 + i * (pw + 30); py0 = cy - 190; px1 = px0 + pw; py1 = cy + 150
            d.rounded_rectangle((px0, py0, px1, py1), 18, outline=BRASS_DIM, width=3, fill=PANEL)
            mx = (px0 + px1) // 2
            if kind == 'vr':
                # stars and hills: a whole new world
                for k in range(14):
                    sx = px0 + 20 + (k * 67) % (pw - 40); sy = py0 + 30 + (k * 41) % 120
                    d.ellipse((sx - 3, sy - 3, sx + 3, sy + 3), fill=BONE)
                d.polygon([(px0 + 4, py1 - 4), (px0 + pw * 0.35, py0 + 190), (px0 + pw * 0.6, py1 - 70), (px0 + pw * 0.8, py0 + 210), (px1 - 4, py1 - 4)], fill=TEAL, outline=BRASS)
                d.ellipse((mx + 40, py0 + 40, mx + 90, py0 + 90), outline=BRASS, width=lw)
            else:
                # the room: a floor line and a window; AR floats a cube, MR rests it on a table
                d.line((px0 + 10, py1 - 70, px1 - 10, py1 - 70), fill=BONE_DIM, width=3)
                d.rectangle((px0 + 30, py0 + 40, px0 + 110, py0 + 130), outline=BONE_DIM, width=3)
                d.line((px0 + 70, py0 + 40, px0 + 70, py0 + 130), fill=BONE_DIM, width=2)
                if kind == 'mr':
                    d.rectangle((mx - 80, py1 - 140, mx + 80, py1 - 128), fill=BONE_DIM)
                    d.line((mx - 70, py1 - 128, mx - 70, py1 - 70), fill=BONE_DIM, width=4)
                    d.line((mx + 70, py1 - 128, mx + 70, py1 - 70), fill=BONE_DIM, width=4)
                    base = py1 - 140
                else:
                    base = py0 + 210
                s = 46
                d.polygon([(mx, base - 2 * s), (mx + s, base - 1.5 * s), (mx, base - s), (mx - s, base - 1.5 * s)], outline=BRASS, fill=(70, 60, 36))
                d.polygon([(mx - s, base - 1.5 * s), (mx, base - s), (mx, base), (mx - s, base - 0.5 * s)], outline=BRASS, fill=(52, 46, 30))
                d.polygon([(mx + s, base - 1.5 * s), (mx, base - s), (mx, base), (mx + s, base - 0.5 * s)], outline=BRASS, fill=(90, 76, 44))
            label(title, mx, py1 + 22, f=font('title', 56), fill=BRASS)
    elif name == 'headset':
        # top-down: the face, two eyes, two lenses, two screens, and the two slightly different pictures
        hx0, hx1 = cx - 300, cx + 300
        d.rounded_rectangle((hx0, cy - 230, hx1, cy - 60), 40, outline=BONE, width=lw, fill=PANEL)
        for s in (-1, 1):
            ex = cx + s * 120
            d.rectangle((ex - 95, cy - 210, ex + 95, cy - 180), fill=BRASS)               # a screen
            d.ellipse((ex - 80, cy - 135, ex + 80, cy - 105), outline=BONE, width=4)     # a lens
            d.ellipse((ex - 28, cy + 20, ex + 28, cy + 76), outline=BONE, width=lw)      # an eye
            d.line((ex, cy + 20, ex - 70, cy - 105), fill=BRASS_DIM, width=2)
            d.line((ex, cy + 20, ex + 70, cy - 105), fill=BRASS_DIM, width=2)
        d.arc((cx - 230, cy - 20, cx + 230, cy + 260), 200, 340, fill=BONE_DIM, width=3)  # the head
        label('screens', hx1 + 90, cy - 214, f=small, fill=BRASS)
        label('lenses', hx1 + 82, cy - 138, f=small, fill=BONE_DIM)
        label('your eyes', hx1 + 40, cy + 30, f=small, fill=BONE_DIM)
        # two pictures, each a little shifted
        for s, dx in ((-1, -14), (1, 14)):
            bx = cx + s * 200
            d.rounded_rectangle((bx - 130, cy + 140, bx + 130, cy + 290), 10, outline=BRASS_DIM, width=3)
            d.ellipse((bx - 30 + dx, cy + 185, bx + 30 + dx, cy + 245), fill=BRASS)
            d.rectangle((bx - 100, cy + 230, bx - 50, cy + 270), fill=BONE_DIM)
        label('left eye', cx - 200, cy + 300, f=small, fill=BONE_DIM)
        label('right eye', cx + 200, cy + 300, f=small, fill=BONE_DIM)
    elif name == 'dof':
        for i, (title, six) in enumerate((('3DoF', False), ('6DoF', True))):
            hx = cx - 260 + i * 520
            d.ellipse((hx - 70, cy - 120, hx + 70, cy + 20), outline=BONE, width=lw)        # a head
            d.rounded_rectangle((hx - 75, cy - 70, hx + 75, cy - 25), 14, fill=BRASS)        # its headset
            # the three turns: yaw, pitch, roll
            d.arc((hx - 140, cy - 190, hx + 140, cy + 90), 200, 340, fill=BRASS, width=4)
            d.arc((hx - 120, cy - 170, hx + 120, cy + 70), 20, 160, fill=BRASS_DIM, width=4)
            if six:
                # and moving: arrows along the three axes
                for (ax, ay) in ((1, 0), (-1, 0), (0, 1)):
                    sx, sy = hx + ax * 150, cy + 60 + ay * 120
                    d.line((hx + ax * 60, cy + 60 + ay * 30, sx, sy), fill=BONE, width=4)
                    d.polygon([(sx + ax * 18, sy + ay * 18), (sx - ay * 12 - ax * 4, sy + ax * 12 - ay * 4), (sx + ay * 12 - ax * 4, sy - ax * 12 - ay * 4)], fill=BONE)
            label(title, hx, cy + 200, f=font('title', 64), fill=BRASS)
            label('turn' if not six else 'turn + move', hx, cy + 275, f=small, fill=BONE_DIM)
    elif name == 'refresh':
        # frames per second: a strip of frames, denser for 120
        for row, (hz, n) in enumerate(((72, 6), (120, 10))):
            y = cy - 150 + row * 210
            label('%d Hz' % hz, x0 + 70, y + 30, f=font('title', 50), fill=BRASS)
            fx0 = x0 + 160
            step = (x1 - fx0 - 20) / n
            fw = step - 14
            for k in range(n):
                fx = fx0 + k * step
                d.rounded_rectangle((fx, y, fx + fw, y + 120), 8, outline=BONE_DIM, width=3, fill=PANEL)
                # the ball moves a little further in every frame: motion, one picture at a time
                dot = min(34, fw - 12)
                bx = fx + 6 + (fw - 12 - dot) * (k / max(1, n - 1))
                d.ellipse((bx, y + 60 - dot / 2, bx + dot, y + 60 + dot / 2), fill=BRASS)
        label('frames every second', cx + 60, cy + 270, f=small, fill=BONE_DIM)
    elif name == 'comfort':
        # a chair, a teleport arc and a break
        d.line((cx - 330, cy + 120, cx - 330, cy - 40), fill=BONE, width=lw)
        d.line((cx - 330, cy + 40, cx - 220, cy + 40), fill=BONE, width=lw)
        d.line((cx - 220, cy + 40, cx - 220, cy + 120), fill=BONE, width=lw)
        label('sit', cx - 280, cy + 150, f=lab)
        d.arc((cx - 120, cy - 120, cx + 120, cy + 120), 200, 340, fill=BRASS, width=lw)
        d.ellipse((cx + 95, cy - 10, cx + 135, cy + 30), outline=BRASS, width=lw)
        d.ellipse((cx - 135, cy - 10, cx - 95, cy + 30), fill=BRASS)
        label('teleport', cx, cy + 150, f=lab)
        d.rounded_rectangle((cx + 230, cy - 60, cx + 400, cy + 110), 20, outline=BONE, width=lw)
        d.line((cx + 270, cy - 20, cx + 270, cy + 70), fill=BRASS, width=10)
        d.line((cx + 360, cy - 20, cx + 360, cy + 70), fill=BRASS, width=10)
        label('take a break', cx + 315, cy + 150, f=lab)
    elif name == 'boundary':
        # a play space from above: the boundary, a person, a chair kept outside
        d.rounded_rectangle((cx - 280, cy - 220, cx + 280, cy + 200), 40, outline=BRASS, width=6)
        for k in range(0, 560, 40):
            d.line((cx - 280 + k, cy - 220, cx - 280 + k + 20, cy - 220), fill=INK, width=8)
        d.ellipse((cx - 40, cy - 40, cx + 40, cy + 40), outline=BONE, width=lw)
        d.rounded_rectangle((cx - 30, cy - 70, cx + 30, cy - 46), 8, fill=BRASS)
        d.rectangle((cx + 340, cy + 60, cx + 420, cy + 140), outline=BONE_DIM, width=4)
        label('chair: outside', cx + 380, cy + 160, f=small, fill=BONE_DIM)
        label('your boundary', cx, cy + 222, f=lab, fill=BRASS)


# ---------------------------------------------------------------- slides
VENUES = {'forecourt': 'The forecourt theatre', 'auditorium': 'The auditorium', 'classroom': 'Room 104 · XR Classroom'}


def monogram(client):
    first = client.split()[0] if client.split() else 'XR'
    if len(first) <= 3 and first.isupper():
        return first
    return ''.join(w[0] for w in client.split()[:2]).upper() or 'XR'


def draw_slide(talk, i, slide, n, campus, client=''):
    im = BG.copy()
    d = ImageDraw.Draw(im)
    layout = slide.get('layout', 'content')
    speaker = talk.get('speaker', {})
    # frame: a brass hairline inset, the footer rule
    d.rectangle((48, 48, W - 49, H - 49), outline=BRASS_DIM, width=2)
    d.line((96, H - 128, W - 96, H - 128), fill=BRASS_DIM, width=2)
    kicker(d, (100, H - 104), ('%s  ·  %s' % (client, campus)) if client else campus, size=22, fill=BRASS)
    ft = font('text', 24)
    mid = talk['title']
    d.text(((W - d.textlength(mid, font=ft)) / 2, H - 106), mid, font=ft, fill=BONE_DIM)
    page = '%d / %d' % (i + 1, n)
    d.text((W - 100 - d.textlength(page, font=ft), H - 106), page, font=ft, fill=BONE_DIM)

    if layout in ('title', 'end'):
        kind = WORDS.get('A class', 'A class') if talk.get('kind') == 'class' else WORDS.get('A talk', 'A talk')
        venue = VENUES.get(talk.get('venue'), talk.get('subtitle', ''))
        venue = WORDS.get(venue, venue)
        kicker(d, (140, 230), ('%s  ·  %s' % (kind, venue)) if layout == 'title' else talk['title'], size=28)
        tf = font('title', 124 if len(slide['title']) < 22 else 104)
        y = 290
        for line in wrap(d, slide['title'], tf, 1180):
            d.text((136, y), line, font=tf, fill=BONE)
            y += int(tf.size * 1.06)
        if layout == 'title':
            sub = talk.get('subtitle') or (slide.get('points') or [''])[0]
            if sub:
                d.text((140, y + 26), sub, font=font('text', 40), fill=BONE_DIM)
                y += 86
            d.line((140, y + 40, 560, y + 40), fill=BRASS, width=4)
            y += 86
            d.text((140, y), speaker.get('name', ''), font=font('italic', 58), fill=BONE)
            d.text((140, y + 76), speaker.get('role', ''), font=font('text', 34), fill=BONE_DIM)
        else:
            d.line((140, y + 34, 560, y + 34), fill=BRASS, width=4)
            y += 80
            pf = font('text', 40)
            for p in slide.get('points', []):
                d.ellipse((142, y + 18, 156, y + 32), fill=BRASS)
                d.text((180, y), p, font=pf, fill=BONE)
                y += 64
            d.text((140, y + 40), '%s  ·  %s' % (speaker.get('name', ''), speaker.get('role', '')), font=font('italic', 44), fill=BONE_DIM)
        # a brass seal on the right
        sx, sy, r = W - 400, 470, 190
        d.ellipse((sx - r, sy - r, sx + r, sy + r), outline=BRASS_DIM, width=3)
        d.ellipse((sx - r + 18, sy - r + 18, sx + r - 18, sy + r - 18), outline=BRASS, width=2)
        mono = monogram(client or campus)
        mf = font('title_b', 160)
        bb = d.textbbox((0, 0), mono, font=mf)
        d.text((sx - (bb[2] - bb[0]) / 2 - bb[0], sy - (bb[3] - bb[1]) / 2 - bb[1]), mono, font=mf, fill=BRASS)
        return im

    # a content slide: kicker, title, points on the left; the art or a drawing on the right
    kicker(d, (140, 150), '%s  ·  %d' % (talk['title'], i + 1), size=24, fill=BRASS)
    has_side = bool(slide.get('art') or slide.get('figure'))
    text_w = 920 if has_side else W - 320
    tf = font('title', 92)
    y = 205
    for line in wrap(d, slide['title'], tf, text_w):
        d.text((136, y), line, font=tf, fill=BONE)
        y += 100
    d.line((140, y + 26, 420, y + 26), fill=BRASS, width=4)
    y += 84
    pf = font('text', 42)
    for p in slide.get('points', []):
        lines = wrap(d, p, pf, text_w - 50)
        d.ellipse((142, y + 20, 158, y + 36), fill=BRASS)
        for ln in lines:
            d.text((184, y), ln, font=pf, fill=BONE)
            y += 58
        y += 28
    box = (1130, 170, W - 130, H - 190)
    if slide.get('art'):
        p = os.path.join(ART, slide['art'] + '.png')
        if os.path.exists(p):
            framed(im, p, box)
    elif slide.get('figure'):
        d.rounded_rectangle(box, 24, fill=PANEL, outline=BRASS_DIM, width=2)
        figure(slide['figure'], im, (box[0] + 40, box[1] + 40, box[2] - 40, box[3] - 40))
    return im


WORDS = {}


def main():
    global BG, WORDS
    with open(talks_file(), 'r', encoding='utf-8') as fh:
        talks = json.load(fh)['talks']
    lang = language()
    WORDS = builder_words(lang)
    changed = apply_language(talks, lang)
    if lang != 'en':
        print('language %s: %d talk fields from lang/%s/tables.json, %d builder words' % (lang, changed, lang, len(WORDS)), flush=True)
    campus = clientpack.get('campus', 'Walk the Archive')
    client = clientpack.get('client', '')
    BG = background()
    index = {}
    for talk in talks:
        folder = os.path.join(OUT, talk['id'])
        os.makedirs(folder, exist_ok=True)
        names = []
        n = len(talk['slides'])
        for i, slide in enumerate(talk['slides']):
            im = draw_slide(talk, i, slide, n, campus, client)
            name = '%02d.png' % (i + 1)
            im.resize(STORE, Image.LANCZOS).save(os.path.join(folder, name), optimize=True)
            if i == 0 or slide.get('figure') or i == n - 1:
                im.resize((960, 540), Image.LANCZOS).save(os.path.join(folder, 'preview_%02d.jpg' % (i + 1)), quality=86)
            names.append(name)
        index[talk['id']] = {'venue': talk['venue'], 'slides': names}
        print('slides', talk['id'], n, flush=True)
    with open(os.path.join(OUT, 'index.json'), 'w', encoding='utf-8') as fh:
        json.dump({'size': list(STORE), 'drawn_at': [W, H], 'talks': index}, fh, indent=1)


if __name__ == '__main__':
    main()
