"""After the Blender bake: encode the lightmap for the web, shrink textures, write the reflection probe as .hdr.
Run with bl/bin/python (needs bpy for EXR reading)."""
import os, sys, json, numpy as np
from PIL import Image
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(SP, 'assets', 'lib')
LM_SCALE = 8.0      # lightmap png = sRGB(irradiance / LM_SCALE); three.js: lightMapIntensity = LM_SCALE * pi (see world.js)

def srgb(lin):
    lin = np.clip(lin, 0, 1)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(lin, 1 / 2.4) - 0.055)

def read_exr(path):
    import bpy
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    buf = np.empty(w * h * 4, np.float32); img.pixels.foreach_get(buf)
    a = buf.reshape(h, w, 4)[::-1, :, :3].copy()   # Blender stores bottom-up
    bpy.data.images.remove(img)
    return a

def dilate(rgb, mask, passes=6):
    """Push lit texels into the empty gutters so texture filtering never samples black."""
    out = rgb.copy(); m = mask.copy()
    for _ in range(passes):
        acc = np.zeros_like(out); cnt = np.zeros(out.shape[:2], np.float32)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            s = np.roll(np.roll(out, dy, 0), dx, 1); sm = np.roll(np.roll(m, dy, 0), dx, 1)
            acc += s * sm[..., None]; cnt += sm
        fill = (~m) & (cnt > 0)
        out[fill] = (acc[fill] / cnt[fill][:, None]); m = m | fill
    return out

def despeckle(rgb, k=3.0, r=2):
    """Leftover fireflies after denoising: a texel far brighter than its 5x5 median becomes the median."""
    stack = np.stack([np.roll(np.roll(rgb, dy, 0), dx, 1) for dy in range(-r, r + 1) for dx in range(-r, r + 1)], 0)
    med = np.median(stack, 0)
    hot = rgb.max(2) > k * med.max(2) + 0.02
    out = rgb.copy(); out[hot] = med[hot]
    print('  despeckled %d texels' % hot.sum())
    return out

def lightmap(stem='lightmap'):
    import subprocess
    src, dn = os.path.join(LIB, stem + '.exr'), os.path.join(LIB, stem + '_dn.exr')
    subprocess.run([sys.executable, os.path.join(SP, 'bl', 'denoise.py'), src, dn], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    lm = read_exr(dn)
    mask = lm.max(2) > 0
    lm = despeckle(lm)
    lm = dilate(lm, mask)
    enc = srgb(lm / LM_SCALE)
    Image.fromarray((enc * 255 + 0.5).astype(np.uint8), 'RGB').save(os.path.join(LIB, stem + '.png'), optimize=True)
    print(stem + '.png', lm.shape, 'coverage %.1f%%' % (100 * mask.mean()), 'p99 %.2f max %.2f' % (np.percentile(lm[mask].max(1), 99), lm.max()))

def rgbe(path_exr, path_hdr, size=(512, 256)):
    a = read_exr(path_exr)
    im = np.stack([np.array(Image.fromarray(a[:, :, c]).resize(size, Image.BOX)) for c in range(3)], -1).astype(np.float32)
    im = np.clip(im, 0, 1e4)
    h, w = im.shape[:2]
    mx = im.max(2)
    e = np.where(mx > 1e-32, np.floor(np.log2(np.maximum(mx, 1e-32))) + 1, 0)
    scale = np.where(mx > 1e-32, 256.0 / np.power(2.0, e), 0)
    rgb = np.clip(im * scale[..., None], 0, 255).astype(np.uint8)
    ee = np.where(mx > 1e-32, e + 128, 0).astype(np.uint8)
    data = np.concatenate([rgb, ee[..., None]], -1).astype(np.uint8)
    with open(path_hdr, 'wb') as f:
        f.write(b'#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n')
        f.write(('-Y %d +X %d\n' % (h, w)).encode())
        f.write(data.tobytes())   # flat (uncompressed) scanlines
    print('probe.hdr', w, h, 'max %.1f' % im.max())

def shrink():
    """Smaller web textures where the extra resolution buys nothing."""
    plan = { 'oak_floor_col.png':1024, 'oak_floor_nrm.png':1024, 'oak_floor_rgh.png':1024, 'rug_col.png':1024, 'rug_nrm.png':1024, 'rug_rgh.png':512,
             'walnut_col.png':1024, 'walnut_nrm.png':512, 'walnut_rgh.png':512, 'oak_col.png':1024, 'oak_nrm.png':512, 'oak_rgh.png':512,
             'plaster_col.png':512, 'plaster_nrm.png':512, 'plaster_rgh.png':512, 'green_col.png':512, 'green_nrm.png':512, 'green_rgh.png':512,
             'leather_col.png':512, 'leather_nrm.png':512, 'leather_rgh.png':512, 'brass_col.png':256, 'brass_rgh.png':256,
             'window_view.png':1024, 'books_rgh.png':256, 'shelfrow_col.png':2048 }
    for name, w in plan.items():
        fp = os.path.join(LIB, name)
        if not os.path.exists(fp): continue
        im = Image.open(fp)
        if im.width <= w: continue
        h = max(1, round(im.height * w / im.width))
        im.resize((w, h), Image.LANCZOS).save(fp, optimize=True)
        print('shrunk', name, '->', w, h)

if __name__ == '__main__':
    only = sys.argv[1:]
    if only:
        for stem in only: lightmap(stem)
        sys.exit(0)
    lightmap()
    if os.path.exists(os.path.join(LIB, 'lightmap_rows.exr')): lightmap('lightmap_rows')
    rgbe(os.path.join(LIB, 'probe.exr'), os.path.join(LIB, 'probe.hdr'))
    shrink()
    json.dump({ 'LM_SCALE':LM_SCALE }, open(os.path.join(LIB, 'post.json'), 'w'))
