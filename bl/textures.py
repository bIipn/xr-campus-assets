"""Tileable PBR textures for the photoreal rooms, generated here (no downloads): FFT-filtered noise is periodic by
construction, so every map tiles. Writes assets/tex/<name>_{col,rgh,nrm}.png (+ a few single-use images)."""
import os, math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'tex')
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)

def fnoise(n, beta=2.0, ax=1.0, ay=1.0, seed=None, low=1):
    """Periodic fractal noise, n x n, zero mean, unit-ish std. beta: spectral falloff; ax/ay stretch the spectrum."""
    r = np.random.default_rng(seed) if seed is not None else rng
    w = r.standard_normal((n, n))
    F = np.fft.fft2(w)
    fy = np.fft.fftfreq(n)[:, None] * n; fx = np.fft.fftfreq(n)[None, :] * n
    f = np.sqrt((fx * ax) ** 2 + (fy * ay) ** 2); f[0, 0] = 1
    filt = 1.0 / np.power(np.maximum(f, low), beta / 2); filt[0, 0] = 0
    out = np.real(np.fft.ifft2(F * filt))
    return out / (out.std() + 1e-9)

def norm01(a, lo=None, hi=None):
    lo = a.min() if lo is None else lo; hi = a.max() if hi is None else hi
    return np.clip((a - lo) / (hi - lo + 1e-9), 0, 1)

def srgb(lin):
    lin = np.clip(lin, 0, 1)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(lin, 1 / 2.4) - 0.055)

def save_rgb(name, arr):  # arr linear 0..1 (h, w, 3) -> sRGB png
    Image.fromarray((srgb(arr) * 255 + 0.5).astype(np.uint8), 'RGB').save(os.path.join(OUT, name), optimize=True)

def save_gray(name, arr):
    Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8), 'L').save(os.path.join(OUT, name), optimize=True)

def normal_from_height(h, strength=1.0, wrap=True):
    """Tangent-space normal map (OpenGL/glTF convention, +Y = up in texture space) from a periodic height field."""
    dx = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) * 0.5
    dy = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) * 0.5
    nx = -dx * strength; ny = dy * strength; nz = np.ones_like(h)
    l = np.sqrt(nx * nx + ny * ny + nz * nz)
    n = np.stack([nx / l, ny / l, nz / l], -1)
    img = ((n * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8)
    return Image.fromarray(img, 'RGB')

def lerp3(a, b, t):
    t = t[..., None]
    return np.asarray(a)[None, None, :] * (1 - t) + np.asarray(b)[None, None, :] * t

def wood(n, base, dark, ring_freq, grain=(1.0, 14.0), seed=1, along='x', rings=0.5, knots=False):
    """Wood grain: stretched periodic noise along the grain plus ring bands. Returns (albedo lin, height)."""
    ax, ay = (grain[::-1] if along == 'x' else grain)  # attenuate the along-grain axis so streaks run along it
    g = fnoise(n, 1.6, ax, ay, seed=seed)            # long streaks
    f = fnoise(n, 1.2, ax * 0.5, ay * 0.5, seed=seed + 1)  # finer streaks
    warp = fnoise(n, 2.2, 1, 1, seed=seed + 2) * 0.9
    yy, xx = np.mgrid[0:n, 0:n] / n
    coord = (xx if along == 'x' else yy)
    across = (yy if along == 'x' else xx)
    band = np.sin(2 * math.pi * (ring_freq * across + warp * 0.35 + g * 0.08))
    band = 0.5 + 0.5 * np.sign(band) * np.power(np.abs(band), 0.6)
    t = np.clip(0.5 + 0.28 * g + 0.14 * f + rings * (band - 0.5), 0, 1)
    col = lerp3(base, dark, t)
    col *= (1 + 0.06 * fnoise(n, 2.5, 1, 1, seed=seed + 3))[..., None]
    h = 0.5 + 0.35 * (t - 0.5) + 0.08 * f
    return np.clip(col, 0, 1), h

def planks(n, nx, ny, base, dark, seed=5, gap=3, bevel=5):
    """Floor boards: nx boards across, ny rows (staggered), each with its own grain and tint, periodic."""
    col = np.zeros((n, n, 3)); hgt = np.zeros((n, n)); rgh = np.zeros((n, n))
    bw = n // nx; bh = n // ny
    k = 0
    for j in range(ny):
        off = (j % 2) * (bw // 2) + (j // 2) * (bw // 3)
        for i in range(-1, nx + 1):
            x0 = i * bw + off; k += 1
            c, h = wood(bw, base, dark, 1.2 + 0.6 * (k % 4), grain=(1.0, 12.0), seed=seed + k, along='x', rings=0.45)
            tint = 1 + 0.18 * (np.random.default_rng(seed + k).random() - 0.5)
            c = np.clip(c * tint, 0, 1)
            # resample the square wood into the plank cell, then place it with wrap-around
            cell_c = np.array(Image.fromarray((np.clip(c, 0, 1) * 255).astype(np.uint8)).resize((bw, bh), Image.BILINEAR)) / 255.0
            cell_h = np.array(Image.fromarray((np.clip(h, 0, 1) * 255).astype(np.uint8)).resize((bw, bh), Image.BILINEAR)) / 255.0
            # plank edge bevel + dark gap
            yy, xx = np.mgrid[0:bh, 0:bw]
            ex = np.minimum(xx, bw - 1 - xx); ey = np.minimum(yy, bh - 1 - yy); e = np.minimum(ex, ey)
            bev = np.clip((e - gap) / bevel, 0, 1)
            cell_h = cell_h * (0.6 + 0.4 * bev) * (e >= gap) + 0.15 * (e < gap)
            cell_c = cell_c * (0.55 + 0.45 * bev)[..., None]
            for yy_ in range(bh):
                ys = (j * bh + yy_) % n
                xs = (np.arange(bw) + x0) % n
                col[ys, xs] = cell_c[yy_]; hgt[ys, xs] = cell_h[yy_]
                rgh[ys, xs] = 0.42 + 0.12 * (1 - bev[yy_]) + 0.08 * (0.5 - cell_h[yy_])
    return col, hgt, np.clip(rgh, 0, 1)

def make_oak_floor():
    n = 2048
    col, h, r = planks(n, 2, 14, base=[0.60, 0.42, 0.24], dark=[0.33, 0.20, 0.10], seed=11)
    col = np.clip(col * (1 + 0.05 * fnoise(n, 2.8, 1, 1, seed=99))[..., None], 0, 1)
    save_rgb('oak_floor_col.png', col); save_gray('oak_floor_rgh.png', r + 0.04 * fnoise(n, 2, 1, 1, seed=98))
    normal_from_height(h, 2.4).save(os.path.join(OUT, 'oak_floor_nrm.png'), optimize=True)

def make_walnut():
    n = 1024
    col, h = wood(n, base=[0.30, 0.17, 0.09], dark=[0.13, 0.07, 0.035], ring_freq=7, grain=(1.0, 16.0), seed=21, along='x', rings=0.55)
    save_rgb('walnut_col.png', col); save_gray('walnut_rgh.png', 0.38 + 0.12 * (h - 0.5) + 0.04 * fnoise(n, 2, 1, 1, seed=22))
    normal_from_height(h, 0.9).save(os.path.join(OUT, 'walnut_nrm.png'), optimize=True)

def make_oak_light():  # shelves / tables top: lighter honey oak
    n = 1024
    col, h = wood(n, base=[0.64, 0.45, 0.25], dark=[0.40, 0.25, 0.12], ring_freq=5, grain=(1.0, 14.0), seed=31, along='x', rings=0.5)
    save_rgb('oak_col.png', col); save_gray('oak_rgh.png', 0.40 + 0.10 * (h - 0.5) + 0.04 * fnoise(n, 2, 1, 1, seed=32))
    normal_from_height(h, 1.0).save(os.path.join(OUT, 'oak_nrm.png'), optimize=True)

def make_plaster():
    n = 1024
    f = fnoise(n, 2.4, 1, 1, seed=41); g = fnoise(n, 1.2, 1, 1, seed=42)
    base = np.array([0.80, 0.74, 0.62])
    col = base[None, None, :] * (1 + 0.035 * f + 0.02 * g)[..., None]
    stains = np.clip(fnoise(n, 3.0, 1, 1, seed=43), 0, 3) * 0.02
    col = np.clip(col * (1 - stains)[..., None], 0, 1)
    save_rgb('plaster_col.png', col); save_gray('plaster_rgh.png', 0.9 + 0.05 * g)
    normal_from_height(0.5 + 0.12 * f + 0.06 * g, 0.5).save(os.path.join(OUT, 'plaster_nrm.png'), optimize=True)

def make_plaster_green():  # the library's deep green upper walls
    n = 1024
    f = fnoise(n, 2.4, 1, 1, seed=51); g = fnoise(n, 1.2, 1, 1, seed=52)
    base = np.array([0.075, 0.135, 0.105])
    col = np.clip(base[None, None, :] * (1 + 0.06 * f + 0.03 * g)[..., None], 0, 1)
    save_rgb('green_col.png', col); save_gray('green_rgh.png', 0.82 + 0.05 * g)
    normal_from_height(0.5 + 0.12 * f + 0.06 * g, 0.5).save(os.path.join(OUT, 'green_nrm.png'), optimize=True)

def make_leather():
    n = 1024
    f = fnoise(n, 1.0, 1, 1, seed=61); g = fnoise(n, 2.0, 1, 1, seed=62)
    cells = np.clip(np.abs(f), 0, 2) / 2
    base = np.array([0.08, 0.16, 0.10])
    col = np.clip(base[None, None, :] * (1 + 0.25 * (cells - 0.5) + 0.08 * g)[..., None], 0, 1)
    save_rgb('leather_col.png', col); save_gray('leather_rgh.png', 0.55 + 0.15 * cells)
    normal_from_height(0.5 + 0.25 * cells + 0.05 * g, 1.6).save(os.path.join(OUT, 'leather_nrm.png'), optimize=True)

def make_rug():
    """A bordered geometric wool rug (not tiled: used once, aspect 2:1)."""
    W, H = 2048, 1024
    img = Image.new('RGB', (W, H), (122, 34, 30))
    d = ImageDraw.Draw(img)
    cream, navy, gold, red, green = (214, 193, 150), (28, 42, 74), (186, 140, 62), (140, 38, 34), (46, 82, 62)
    d.rectangle([0, 0, W - 1, H - 1], outline=cream, width=28)
    d.rectangle([60, 60, W - 61, H - 61], outline=navy, width=44)
    d.rectangle([130, 130, W - 131, H - 131], outline=gold, width=10)
    d.rectangle([160, 160, W - 161, H - 161], fill=(150, 42, 36))
    # border motif: diamonds along the navy band
    for x in range(100, W - 100, 96):
        for y in (82, H - 82):
            d.polygon([(x, y - 18), (x + 18, y), (x, y + 18), (x - 18, y)], fill=cream)
            d.polygon([(x, y - 8), (x + 8, y), (x, y + 8), (x - 8, y)], fill=red)
    for y in range(100, H - 100, 96):
        for x in (82, W - 82):
            d.polygon([(x, y - 18), (x + 18, y), (x, y + 18), (x - 18, y)], fill=cream)
    # field: lattice of medallions
    cx, cy = W // 2, H // 2
    for i in range(-3, 4):
        for j in range(-1, 2):
            x, y = cx + i * 240, cy + j * 240
            if abs(i) == 3 and j != 0: continue
            d.polygon([(x, y - 80), (x + 80, y), (x, y + 80), (x - 80, y)], fill=navy, outline=gold, width=4)
            d.polygon([(x, y - 46), (x + 46, y), (x, y + 46), (x - 46, y)], fill=green, outline=cream, width=3)
            d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=gold)
    d.ellipse([cx - 150, cy - 150, cx + 150, cy + 150], fill=navy, outline=gold, width=8)
    d.polygon([(cx, cy - 110), (cx + 110, cy), (cx, cy + 110), (cx - 110, cy)], fill=red, outline=cream, width=5)
    d.ellipse([cx - 40, cy - 40, cx + 40, cy + 40], fill=gold)
    a = np.array(img).astype(np.float32) / 255.0
    lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    fib = fnoise(1024, 0.6, 1, 1, seed=71); fib = np.concatenate([fib, fib], axis=1)
    lin = np.clip(lin * (1 + 0.10 * fib)[..., None] * 0.9, 0, 1)
    save_rgb('rug_col.png', lin); save_gray('rug_rgh.png', np.full((H, W), 0.95))
    normal_from_height(0.5 + 0.2 * fib, 0.8).save(os.path.join(OUT, 'rug_nrm.png'), optimize=True)

def make_books():
    """Spine/cover atlas: 16 x 4 cells of 128 x 448 (spine 64 px wide on the left, cover on the right),
    and a paper band (pages) at the bottom 256 px."""
    W, H = 2048, 2048
    img = Image.new('RGB', (W, H), (235, 226, 205))
    d = ImageDraw.Draw(img)
    r = np.random.default_rng(81)
    palette = [(122, 42, 34), (94, 31, 28), (47, 74, 51), (77, 90, 46), (36, 50, 79), (42, 85, 85), (90, 59, 34), (165, 138, 92),
               (211, 196, 162), (30, 27, 24), (160, 122, 42), (74, 43, 61), (139, 74, 43), (60, 79, 99), (120, 90, 120), (30, 60, 90)]
    golds = [(214, 178, 94), (240, 224, 180), (200, 170, 110)]
    for row in range(4):
        for colm in range(16):
            x0, y0 = colm * 128, row * 448
            base = palette[(colm + row * 5) % len(palette)]
            k = 1 + 0.18 * (r.random() - 0.5)
            base = tuple(int(min(255, max(0, c * k))) for c in base)
            d.rectangle([x0, y0, x0 + 127, y0 + 447], fill=base)
            # cloth texture lines
            shade = tuple(int(c * 0.9) for c in base)
            for y in range(y0, y0 + 448, 3): d.line([(x0, y), (x0 + 127, y)], fill=shade, width=1)
            gold = golds[r.integers(0, 3)]
            style = r.integers(0, 5)
            sx0, sx1 = x0 + 4, x0 + 60
            if style == 0:   # bands top and bottom with a label box
                for yy in (y0 + 30, y0 + 44, y0 + 400, y0 + 414): d.line([(sx0 + 4, yy), (sx1 - 4, yy)], fill=gold, width=2)
                d.rectangle([sx0 + 8, y0 + 120, sx1 - 8, y0 + 300], fill=tuple(int(c * 0.75) for c in base), outline=gold)
                for yy in range(y0 + 150, y0 + 280, 22): d.line([(sx0 + 16, yy), (sx1 - 16, yy)], fill=gold, width=3)
            elif style == 1:  # raised bands (leather look)
                for yy in range(y0 + 60, y0 + 420, 72):
                    d.rectangle([sx0, yy, sx1, yy + 10], fill=tuple(int(c * 0.7) for c in base))
                    d.line([(sx0, yy + 1), (sx1, yy + 1)], fill=gold, width=1)
                for yy in range(y0 + 200, y0 + 260, 14): d.line([(sx0 + 12, yy), (sx1 - 12, yy)], fill=gold, width=2)
            elif style == 2:  # plain with title lines
                for yy in range(y0 + 70, y0 + 150, 16): d.line([(sx0 + 10, yy), (sx1 - 10, yy)], fill=(245, 240, 230), width=3)
                d.line([(sx0 + 10, y0 + 380), (sx1 - 10, y0 + 380)], fill=gold, width=2)
            elif style == 3:  # label at the top, decorative stripe
                d.rectangle([sx0 + 6, y0 + 40, sx1 - 6, y0 + 120], fill=(236, 226, 200))
                for yy in range(y0 + 56, y0 + 110, 14): d.line([(sx0 + 12, yy), (sx1 - 12, yy)], fill=(60, 50, 40), width=2)
                for yy in range(y0 + 300, y0 + 420, 18): d.line([(sx0 + 6, yy), (sx1 - 6, yy)], fill=gold, width=1)
            else:             # two-tone spine
                d.rectangle([sx0, y0 + 160, sx1, y0 + 290], fill=tuple(int(c * 0.6) for c in base))
                for yy in range(y0 + 190, y0 + 260, 16): d.line([(sx0 + 10, yy), (sx1 - 10, yy)], fill=gold, width=3)
            # spine/cover seam and cover emboss
            d.line([(x0 + 64, y0), (x0 + 64, y0 + 447)], fill=tuple(int(c * 0.6) for c in base), width=2)
            d.rectangle([x0 + 76, y0 + 40, x0 + 118, y0 + 400], outline=tuple(int(min(255, c * 1.15)) for c in base), width=2)
    # pages band
    y0 = 1792
    d.rectangle([0, y0, W - 1, H - 1], fill=(232, 222, 198))
    pr = np.random.default_rng(82)
    for y in range(y0, H, 2):
        c = int(190 + 40 * pr.random())
        d.line([(0, y), (W - 1, y)], fill=(c, c - 8, c - 30), width=1)
    img.save(os.path.join(OUT, 'books_col.png'), optimize=True)
    rough = np.full((H, W), 0.75, np.float32); rough[y0:, :] = 0.9
    save_gray('books_rgh.png', rough)

def make_brass():
    n = 512
    f = fnoise(n, 2.0, 1, 1, seed=91)
    col = np.clip(np.array([0.78, 0.60, 0.30])[None, None, :] * (1 + 0.05 * f)[..., None], 0, 1)
    save_rgb('brass_col.png', col); save_gray('brass_rgh.png', 0.32 + 0.06 * f)

def make_marble():
    n = 1024
    v = fnoise(n, 1.8, 1, 1, seed=101); w = fnoise(n, 3.0, 1, 1, seed=102)
    veins = np.abs(np.sin(5.0 * (v + 0.5 * w)))
    veins = np.power(np.clip(veins, 0, 1), 14)
    veins = np.clip(veins * 1.6 + 0.4 * np.clip(fnoise(n, 1.4, 1, 1, seed=103), -1, 1) * 0.25, 0, 1)
    base = np.array([0.74, 0.72, 0.68]); dark = np.array([0.42, 0.40, 0.38])
    col = lerp3(base, dark, 1 - veins) * (1 + 0.03 * w)[..., None]
    save_rgb('marble_col.png', np.clip(col, 0, 1)); save_gray('marble_rgh.png', 0.22 + 0.05 * np.abs(w))
    normal_from_height(0.5 + 0.03 * w, 0.4).save(os.path.join(OUT, 'marble_nrm.png'), optimize=True)

def make_window_view():
    """What you see through the arched window: late-afternoon sky, soft sun glow, far hills and trees (emissive backdrop)."""
    W, H = 2048, 2048
    yy, xx = np.mgrid[0:H, 0:W] / H
    top = np.array([0.20, 0.42, 0.78]); horizon = np.array([0.86, 0.80, 0.66])
    t = np.clip((yy - 0.22) / 0.55, 0, 1) ** 1.6
    sky = lerp3(top, horizon, t)
    sunx, suny = 0.70, 0.52
    dist = np.sqrt(((xx - sunx) * 1.0) ** 2 + (yy - suny) ** 2)
    glow = np.exp(-dist * 6) * 2.2 + np.exp(-dist * 1.4) * 0.5
    sky = sky + glow[..., None] * np.array([1.0, 0.86, 0.62])[None, None, :]
    img = Image.fromarray((srgb(np.clip(sky, 0, 1)) * 255).astype(np.uint8), 'RGB')
    d = ImageDraw.Draw(img)
    r = np.random.default_rng(111)
    # hills
    for k, (c, yb, amp) in enumerate([((126, 150, 128), 0.66, 0.05), ((86, 112, 92), 0.73, 0.06), ((54, 78, 62), 0.82, 0.07)]):
        pts = [(0, H)]
        for i in range(0, W + 64, 64):
            pts.append((i, int(H * (yb + amp * math.sin(i / 300.0 + k) * 0.5 + amp * 0.3 * math.sin(i / 90.0 + k * 2)))))
        pts.append((W, H)); d.polygon(pts, fill=c)
    # trees
    for i in range(120):
        x = int(r.random() * W); base = int(H * (0.76 + 0.16 * r.random())); h = int(40 + 110 * r.random()); w = int(h * (0.35 + 0.3 * r.random()))
        g = int(40 + 40 * r.random()); col = (g // 2, g + 10, g // 2 + 5)
        d.ellipse([x - w, base - h, x + w, base], fill=col)
        d.rectangle([x - 4, base - 10, x + 4, base + 20], fill=(50, 36, 24))
    img = img.filter(ImageFilter.GaussianBlur(1.5))
    img.save(os.path.join(OUT, 'window_view.png'), optimize=True)

def make_shelfrow():
    """One shelf row of books as a flat strip (4096 x 512, tiles horizontally): used for the far-away upper tiers."""
    atlas = Image.open(os.path.join(OUT, 'books_col.png')).convert('RGB')
    W, H = 4096, 512
    img = Image.new('RGB', (W, H), (40, 28, 18))
    d = ImageDraw.Draw(img)
    r = np.random.default_rng(121)
    x = -20
    while x < W + 40:
        if r.random() < 0.04: x += int(20 + 60 * r.random()); continue
        w = int(22 + 34 * r.random()); h = int(H * (0.62 + 0.3 * r.random()))
        cell = int(r.integers(0, 64)); cx, cy = (cell % 16) * 128, (cell // 16) * 448
        spine = atlas.crop((cx, cy, cx + 64, cy + 448)).resize((w, h), Image.LANCZOS)
        img.paste(spine, (x, H - h))
        if x + w > W: img.paste(spine, (x - W, H - h))   # wrap
        x += w + 1
    # shelf shadow from the board above and the board itself at the bottom
    a = np.array(img).astype(np.float32) / 255.0
    yy = np.arange(H)[:, None] / H
    shade = np.clip(0.35 + 0.65 * np.clip((yy - 0.05) / 0.35, 0, 1), 0, 1)
    a = a * shade[..., None]
    Image.fromarray((a * 255).astype(np.uint8), 'RGB').save(os.path.join(OUT, 'shelfrow_col.png'), optimize=True)


if __name__ == '__main__':
    import sys
    which = sys.argv[1:] or ['all']
    jobs = { 'oak_floor':make_oak_floor, 'walnut':make_walnut, 'oak':make_oak_light, 'plaster':make_plaster, 'green':make_plaster_green,
             'leather':make_leather, 'rug':make_rug, 'books':make_books, 'brass':make_brass, 'marble':make_marble, 'window':make_window_view, 'shelfrow':make_shelfrow }
    for k, fn in jobs.items():
        if 'all' in which or k in which:
            fn(); print('made', k, flush=True)
