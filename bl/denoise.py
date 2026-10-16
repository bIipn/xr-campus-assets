"""Denoise a baked EXR with Blender's compositor (Intel Open Image Denoise): bl/bin/python bl/denoise.py in.exr out.exr"""
import bpy, sys, os
src, dst = [os.path.abspath(a) for a in sys.argv[1:3]]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
img = bpy.data.images.load(src)
w, h = img.size
sc.render.resolution_x = w; sc.render.resolution_y = h; sc.render.resolution_percentage = 100
sc.render.engine = 'BLENDER_WORKBENCH'
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
for vl in sc.view_layers: vl.use = False          # compositing only, no scene render
nt = bpy.data.node_groups.new('comp', 'CompositorNodeTree')
sc.compositing_node_group = nt
im = nt.nodes.new('CompositorNodeImage'); im.image = img
dn = nt.nodes.new('CompositorNodeDenoise'); dn.inputs['HDR'].default_value = True
try: dn.inputs['Quality'].default_value = 'HIGH'
except Exception as e: print('quality', e)
out = nt.nodes.new('NodeGroupOutput'); nt.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
nt.links.new(im.outputs['Image'], dn.inputs['Image']); nt.links.new(dn.outputs['Image'], out.inputs['Image'])
sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '32'; sc.render.image_settings.exr_codec = 'ZIP'
sc.view_settings.view_transform = 'Standard'; sc.render.dither_intensity = 0
sc.render.filepath = dst
bpy.ops.render.render(write_still=True)
print('denoised', src, '->', dst, w, h)
