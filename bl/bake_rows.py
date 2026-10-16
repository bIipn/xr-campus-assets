"""The mezzanine shelf rows are 30 big flat strips: vertex lighting samples only their corners (which sit in the
darkest crevices), so they get their own lightmap instead. Loads bake_work.blend (after bake.py), gives the
'shelfrows' object lightmap UVs, bakes them into assets/lib/lightmap_rows.exr, drops their vertex colours,
re-exports lib_raw.gltf and records the extra lightmap in meta.json.
Usage: bl/bin/python bl/bake_rows.py [--samples 64] [--size 1024]"""
import bpy, os, sys, json, time, math
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(SP, 'assets', 'lib')
def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default
SAMPLES = arg('--samples', 64); SIZE = arg('--size', 1024)
WORK = os.path.join(OUT, 'bake_work.blend'); EXR = os.path.join(OUT, 'lightmap_rows.exr')

bpy.ops.wm.open_mainfile(filepath=WORK)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
o = sc.objects['shelfrows']
def select_only(sel):
    bpy.ops.object.select_all(action='DESELECT')
    for x in sel: x.select_set(True)
    bpy.context.view_layer.objects.active = sel[0]

# lightmap UVs laid out by hand: every strip is an axis-aligned quad, so each gets a rectangle at a fixed
# texel density, shelf-packed into a 1024 x H atlas (H a power of two)
if 'lm' not in o.data.uv_layers: o.data.uv_layers.new(name='lm')
uv = o.data.uv_layers['lm']
me = o.data
strips = []
for poly in me.polygons:
    pts = [me.vertices[me.loops[l].vertex_index].co.copy() for l in poly.loop_indices]
    zmin = min(p.z for p in pts); zmax = max(p.z for p in pts)
    flat = [p for p in pts if abs(p.z - zmin) < 1e-4]
    a, b = flat[0], flat[1]
    along = (b - a); L = along.length; along.normalize()
    strips.append(dict(poly=poly, origin=a, along=along, L=L, H=zmax - zmin, zmin=zmin))
PAD = 4
def layout(s, W, Hmax):
    rows = []; y = PAD
    order = sorted(strips, key=lambda st: -st['L'])
    for st in order:
        w = int(math.ceil(st['L'] * s)); h = int(math.ceil(st['H'] * s))
        if w > W - 2 * PAD: return None
        placed = False
        for r in rows:
            if r['h'] == h and r['x'] + w + PAD <= W:
                st['rect'] = (r['x'], r['y'], w, h); r['x'] += w + PAD; placed = True; break
        if not placed:
            if y + h + PAD > Hmax: return None
            rows.append(dict(x=PAD + w + PAD, y=y, h=h)); st['rect'] = (PAD, y, w, h); y += h + PAD
    return y + PAD
W = 1024
for Hatlas in (512, 1024):
    s = 60.0
    while s > 10 and layout(s, W, Hatlas) is None: s -= 1.0
    if s > 10: break
used = layout(s, W, Hatlas)
print('rows atlas', W, 'x', Hatlas, 'density %.0f texels/m' % s, 'rows used', used, flush=True)
for st in strips:
    x0, y0, w, h = st['rect']
    for l in st['poly'].loop_indices:
        p = me.vertices[me.loops[l].vertex_index].co
        u = (p - st['origin']).dot(st['along']) / st['L']; v = (p.z - st['zmin']) / st['H']
        uv.data[l].uv = ((x0 + u * w) / W, (y0 + v * h) / Hatlas)
o.data.uv_layers.active = uv
select_only([o])

img = bpy.data.images.new('lightmap_rows', W, Hatlas, float_buffer=True, alpha=False)
img.colorspace_settings.name = 'Non-Color'
m = o.data.materials[0]; nt = m.node_tree
n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; n.name = 'LM_BAKE'; n.location = (0, 500)
uvn = nt.nodes.new('ShaderNodeUVMap'); uvn.uv_map = 'lm'; uvn.location = (-200, 500)
nt.links.new(uvn.outputs['UV'], n.inputs['Vector']); nt.nodes.active = n

sc.cycles.samples = SAMPLES; sc.cycles.bake_type = 'DIFFUSE'
b = sc.render.bake
b.use_pass_direct = True; b.use_pass_indirect = True; b.use_pass_color = False
b.target = 'IMAGE_TEXTURES'; b.margin = 3; b.margin_type = 'EXTEND'; b.use_clear = True
t = time.time(); print('lightmap bake shelfrows', W, Hatlas, SAMPLES, flush=True)
bpy.ops.object.bake(type='DIFFUSE')
img.filepath_raw = EXR; img.file_format = 'OPEN_EXR'; img.save()
print('  done in %.0f s' % (time.time() - t), flush=True)
for x in [x for x in nt.nodes if x.name.startswith('LM_BAKE')]: nt.nodes.remove(x)
o.data.uv_layers.active = o.data.uv_layers['uv']

# it is lightmapped now, not vertex-lit
if 'light' in o.data.color_attributes: o.data.color_attributes.remove(o.data.color_attributes['light'])
o['lm'] = 1
if 'vc' in o: del o['vc']
bpy.ops.wm.save_as_mainfile(filepath=WORK)

sel = [x for x in sc.objects if x.type == 'MESH']
select_only(sel)
path = os.path.join(OUT, 'lib_raw.gltf')
bpy.ops.export_scene.gltf(filepath=path, export_format='GLTF_SEPARATE', use_selection=True, export_apply=True,
                          export_texcoords=True, export_normals=True, export_materials='EXPORT', export_image_format='AUTO',
                          export_vertex_color='ACTIVE', export_all_vertex_colors=False, export_active_vertex_color_when_no_material=False,
                          export_yup=True, export_extras=True, export_lights=False, export_cameras=False, export_animations=False)
meta = json.load(open(os.path.join(OUT, 'meta.json')))
meta['lm'] = sorted(set(meta['lm']) | {'shelfrows'}); meta['vc'] = [x for x in meta['vc'] if x != 'shelfrows']
meta['lmaps'] = { m.name:'lightmap_rows.png' }
json.dump(meta, open(os.path.join(OUT, 'meta.json'), 'w'))
print('exported', path, 'rows complete', flush=True)
