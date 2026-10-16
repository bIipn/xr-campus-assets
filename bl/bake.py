"""Resumable bake for a room built by library.py: loads assets/<room>/library.blend (geometry, materials, lightmap UVs),
bakes the lightmap one object at a time into a shared atlas (saved after every object), then vertex colours per object
(saved into the .blend after each), then the reflection probe, then exports. Re-running continues where it stopped.
Usage: bl/bin/python bl/bake.py [--lm 128] [--vc 96] [--size 2048]"""
import bpy, os, sys, json, time, math
import numpy as np
from mathutils import Vector
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(SP, 'assets', 'lib')
def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default
SAMPLES_LM = arg('--lm', 128); SAMPLES_VC = arg('--vc', 96); LM_SIZE = arg('--size', 2048)
VC_SCALE = 4.0
BLEND = os.path.join(OUT, 'library.blend'); WORK = os.path.join(OUT, 'bake_work.blend')
PROG = os.path.join(OUT, 'bake_progress.json'); EXR = os.path.join(OUT, 'lightmap.exr')
prog = json.load(open(PROG)) if os.path.exists(PROG) else { 'lm':[], 'vc':[], 'probe':False, 'export':False, 'size':LM_SIZE }
if prog.get('size') != LM_SIZE: prog = { 'lm':[], 'vc':[], 'probe':False, 'export':False, 'size':LM_SIZE }
def save_prog(): json.dump(prog, open(PROG, 'w'))

bpy.ops.wm.open_mainfile(filepath=WORK if os.path.exists(WORK) and (prog['lm'] or prog['vc']) else BLEND)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
obs = [o for o in sc.objects if o.type == 'MESH']
lm = [o for o in obs if o.get('lm')]; vc = [o for o in obs if o.get('vc')]
print('loaded', 'lightmapped', [o.name for o in lm], 'vertex-lit', len(vc), 'progress', prog, flush=True)

def select_only(sel):
    bpy.ops.object.select_all(action='DESELECT')
    for o in sel: o.select_set(True)
    bpy.context.view_layer.objects.active = sel[0]

# ---------------- lightmap, one object at a time into the shared atlas
todo = [o for o in lm if o.name not in prog['lm']]
if todo:
    if os.path.exists(EXR) and prog['lm']:
        img = bpy.data.images.load(EXR); img.name = 'lightmap'
    else:
        img = bpy.data.images.new('lightmap', LM_SIZE, LM_SIZE, float_buffer=True, alpha=False)
        img.filepath_raw = EXR; img.file_format = 'OPEN_EXR'
    img.colorspace_settings.name = 'Non-Color'
    for m in {o.data.materials[0] for o in lm}:
        nt = m.node_tree
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; n.name = 'LM_BAKE'; n.location = (0, 500)
        uvn = nt.nodes.new('ShaderNodeUVMap'); uvn.uv_map = 'lm'; uvn.location = (-200, 500)
        nt.links.new(uvn.outputs['UV'], n.inputs['Vector']); nt.nodes.active = n
    for o in lm: o.data.uv_layers.active = o.data.uv_layers['lm']
    sc.cycles.samples = SAMPLES_LM; sc.cycles.bake_type = 'DIFFUSE'
    b = sc.render.bake
    b.use_pass_direct = True; b.use_pass_indirect = True; b.use_pass_color = False
    b.target = 'IMAGE_TEXTURES'; b.margin = 16 if LM_SIZE > 1024 else 10; b.margin_type = 'EXTEND'; b.use_clear = False
    for o in todo:
        select_only([o])
        t = time.time(); print('lightmap bake', o.name, LM_SIZE, SAMPLES_LM, flush=True)
        bpy.ops.object.bake(type='DIFFUSE')
        img.filepath_raw = EXR; img.file_format = 'OPEN_EXR'; img.save()
        prog['lm'].append(o.name); save_prog()
        print('  done in %.0f s' % (time.time() - t), flush=True)
    for o in lm: o.data.uv_layers.active = o.data.uv_layers['uv']
    for m in {o.data.materials[0] for o in lm}:
        nt = m.node_tree
        for n in [n for n in nt.nodes if n.name.startswith('LM_BAKE')]: nt.nodes.remove(n)
    bpy.ops.wm.save_as_mainfile(filepath=WORK)

# ---------------- vertex colours, one object at a time
todo = [o for o in vc if o.name not in prog['vc']]
if todo:
    sc.cycles.samples = SAMPLES_VC; sc.cycles.bake_type = 'DIFFUSE'
    b = sc.render.bake
    b.use_pass_direct = True; b.use_pass_indirect = True; b.use_pass_color = False
    b.target = 'VERTEX_COLORS'
    for o in todo:
        o.data.color_attributes.active_color = o.data.color_attributes['light']
        select_only([o])
        t = time.time(); print('vertex bake', o.name, len(o.data.loops), 'corners', flush=True)
        bpy.ops.object.bake(type='DIFFUSE')
        ca = o.data.color_attributes['light']
        n = len(ca.data); buf = np.empty(n * 4, np.float32); ca.data.foreach_get('color', buf)
        buf = buf.reshape(-1, 4); buf[:, :3] = np.clip(buf[:, :3] / VC_SCALE, 0, 1); buf[:, 3] = 1
        ca.data.foreach_set('color', buf.ravel())
        prog['vc'].append(o.name); save_prog()
        bpy.ops.wm.save_as_mainfile(filepath=WORK)
        print('  done in %.0f s' % (time.time() - t), flush=True)

# ---------------- reflection probe
if not prog['probe']:
    cam = bpy.data.cameras.new('Probe'); cam.type = 'PANO'; cam.panorama_type = 'EQUIRECTANGULAR'
    co = bpy.data.objects.new('Probe', cam); sc.collection.objects.link(co)
    co.location = Vector((-22.0, 3.0, 1.6)); co.rotation_euler = (math.radians(90), 0, math.radians(-90))
    sc.camera = co
    sc.render.resolution_x = 1024; sc.render.resolution_y = 512; sc.render.resolution_percentage = 100
    sc.cycles.samples = 96; sc.cycles.use_denoising = True
    sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '16'
    sc.view_settings.view_transform = 'Standard'
    sc.render.filepath = os.path.join(OUT, 'probe.exr')
    t = time.time(); bpy.ops.render.render(write_still=True); print('probe rendered in %.0f s' % (time.time() - t), flush=True)
    sc.view_settings.view_transform = 'AgX'
    sc.collection.objects.unlink(co)
    prog['probe'] = True; save_prog()

# ---------------- export
if not prog['export']:
    sel = [o for o in sc.objects if o.type == 'MESH']
    select_only(sel)
    path = os.path.join(OUT, 'lib_raw.gltf')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLTF_SEPARATE', use_selection=True, export_apply=True,
                              export_texcoords=True, export_normals=True, export_materials='EXPORT', export_image_format='AUTO',
                              export_vertex_color='ACTIVE', export_all_vertex_colors=False, export_active_vertex_color_when_no_material=False,
                              export_yup=True, export_extras=True, export_lights=False, export_cameras=False, export_animations=False)
    json.dump(dict(VC_SCALE=VC_SCALE, LM_SIZE=LM_SIZE, lm=[o.name for o in lm], vc=[o.name for o in vc]), open(os.path.join(OUT, 'meta.json'), 'w'))
    prog['export'] = True; save_prog()
    print('exported', path, flush=True)
print('bake complete', flush=True)
