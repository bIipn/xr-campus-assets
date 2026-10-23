"""Imports the Wax Hall motion capture and retargets it onto the MetaHuman body skeleton.

The clips come from Mixamo (Adobe, free with an Adobe account, royalty free), downloaded as FBX Binary at 30 fps:
one "With Skin" (the rigged figure the clips are authored on, _source_withskin.fbx) and one "Without Skin" per
action, named after the action id the scenes use (talk.fbx, sit_type.fbx, ...).

  run(clip_folder)
    1. imports _source_withskin.fbx, which brings in the Mixamo figure, its skeleton and its own animation;
    2. imports every other FBX as an animation on that skeleton (Mocap/Raw/<action>);
    3. builds an IK Rig for the Mixamo skeleton (UE recognises it, so the chains generate themselves) and an IK
       Retargeter from it to the MetaHuman IK Rig the MetaHumanCharacter plugin ships;
    4. batch retargets every raw clip onto the body mesh the wax figures use, leaving
       /Game/WTA/Characters/Common/Anims/Mocap/AS_WTA_<action>.

Run it from the editor's Python console:  import wta_mocap; wta_mocap.build.run()
"""

import os
import unreal

CLIP_FOLDER = r'C:\Users\lilbl\Desktop\Walk the Archive Files\Motion Clips'
SOURCE_FBX = '_source_withskin'

MOCAP_ROOT = '/Game/WTA/Characters/Common/Mocap'
SOURCE_PATH = MOCAP_ROOT + '/Source'
RAW_PATH = MOCAP_ROOT + '/Raw'
OUT_PATH = '/Game/WTA/Characters/Common/Anims/Mocap'
PREFIX = 'AS_WTA_'

# The MetaHumanCharacter plugin's rig for the MetaHuman body skeleton: chains, goals and a pelvis root already set.
MH_IK_RIG = '/MetaHumanCharacter/Animation/Retargeting/IK_MH_IKRig'
# Any wax figure's body mesh: they all share /Game/WTA/Characters/Common/.../metahuman_base_skel.
TARGET_BODY = '/Game/WTA/Characters/wax-2016-teen/Body/SKM_MHC_wax-2016-teen_BodyMesh'

MIXAMO_RIG = MOCAP_ROOT + '/IK_WTA_Mixamo'
RETARGETER = MOCAP_ROOT + '/RTG_WTA_Mixamo_to_MH'


def _log(message):
    unreal.log('[wta_mocap] ' + message)


def _warn(message):
    unreal.log_warning('[wta_mocap] ' + message)


def _skeletal_mesh_options():
    """Import the Mixamo figure itself: skeleton, mesh and the animation that came with it."""
    options = unreal.FbxImportUI()
    options.set_editor_property('import_mesh', True)
    options.set_editor_property('import_as_skeletal', True)
    options.set_editor_property('import_animations', True)
    options.set_editor_property('import_materials', False)
    options.set_editor_property('import_textures', False)
    options.set_editor_property('create_physics_asset', False)
    options.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    mesh_data = options.skeletal_mesh_import_data
    mesh_data.set_editor_property('import_morph_targets', False)
    mesh_data.set_editor_property('convert_scene', True)
    mesh_data.set_editor_property('force_front_x_axis', False)
    mesh_data.set_editor_property('convert_scene_unit', False)
    return options


def _animation_options(skeleton):
    """Import one clip as an animation on the Mixamo skeleton, keeping its own sample rate."""
    options = unreal.FbxImportUI()
    options.set_editor_property('import_mesh', False)
    options.set_editor_property('import_as_skeletal', True)
    options.set_editor_property('import_animations', True)
    options.set_editor_property('import_materials', False)
    options.set_editor_property('import_textures', False)
    options.set_editor_property('create_physics_asset', False)
    options.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_ANIMATION)
    options.set_editor_property('skeleton', skeleton)
    anim_data = options.anim_sequence_import_data
    anim_data.set_editor_property('import_bone_tracks', True)
    anim_data.set_editor_property('remove_redundant_keys', False)
    anim_data.set_editor_property('convert_scene', True)
    anim_data.set_editor_property('force_front_x_axis', False)
    anim_data.set_editor_property('convert_scene_unit', False)
    anim_data.set_editor_property('animation_length', unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
    return options


def _import(filename, destination, asset_name, options):
    task = unreal.AssetImportTask()
    task.set_editor_property('filename', filename)
    task.set_editor_property('destination_path', destination)
    task.set_editor_property('destination_name', asset_name)
    task.set_editor_property('automated', True)
    task.set_editor_property('replace_existing', True)
    task.set_editor_property('save', False)
    task.set_editor_property('options', options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return [str(p) for p in task.get_editor_property('imported_object_paths')]


def _find(paths, cls):
    for path in paths:
        asset = unreal.load_asset(path.split('.')[0] + '.' + path.split('.')[-1]) if '.' in path else unreal.load_asset(path)
        if asset is None:
            asset = unreal.load_asset(path)
        if isinstance(asset, cls):
            return asset
    return None


def import_source(clip_folder):
    """Imports the Mixamo figure. Returns (skeletal_mesh, skeleton, its own animation)."""
    path = os.path.join(clip_folder, SOURCE_FBX + '.fbx')
    if not os.path.isfile(path):
        raise RuntimeError('no source clip at ' + path)
    made = _import(path, SOURCE_PATH, 'SK_WTA_Mixamo', _skeletal_mesh_options())
    _log('source: ' + ', '.join(made))
    mesh = _find(made, unreal.SkeletalMesh)
    anim = _find(made, unreal.AnimSequence)
    if mesh is None:
        raise RuntimeError('the source FBX did not import a skeletal mesh')
    skeleton = mesh.get_editor_property('skeleton')
    return mesh, skeleton, anim


def import_clips(clip_folder, skeleton):
    """Imports every clip FBX as an animation named after its file. Returns {action: AnimSequence}."""
    options = _animation_options(skeleton)
    clips = {}
    for name in sorted(os.listdir(clip_folder)):
        if not name.lower().endswith('.fbx') or name.startswith('_'):
            continue
        action = os.path.splitext(name)[0]
        made = _import(os.path.join(clip_folder, name), RAW_PATH, action, options)
        anim = _find(made, unreal.AnimSequence)
        if anim is None:
            _warn('%s: no animation imported' % action)
            continue
        clips[action] = anim
    _log('imported %d clips' % len(clips))
    return clips


def build_rigs(mixamo_mesh):
    """The Mixamo IK Rig (chains generated from the skeleton) and the retargeter onto the MetaHuman rig."""
    tools = unreal.AssetToolsHelpers.get_asset_tools()

    rig = unreal.load_asset(MIXAMO_RIG)
    if rig is None:
        rig = tools.create_asset('IK_WTA_Mixamo', MOCAP_ROOT, unreal.IKRigDefinition, unreal.IKRigDefinitionFactory())
    rig_controller = unreal.IKRigController.get_controller(rig)
    if not rig_controller.set_skeletal_mesh(mixamo_mesh):
        raise RuntimeError('the Mixamo mesh is not compatible with the IK rig')
    # Mixamo is one of the skeletons Unreal knows, so its chains and pelvis come out of the template.
    if not rig_controller.apply_auto_generated_retarget_definition():
        _warn('Unreal did not recognise the Mixamo skeleton; the chains are being set by hand')
        _chains_by_hand(rig_controller)
    chains = rig_controller.get_retarget_chains()
    _log('Mixamo rig: root %s, %d chains' % (rig_controller.get_retarget_root(), len(chains)))

    target_rig = unreal.load_asset(MH_IK_RIG)
    if target_rig is None:
        raise RuntimeError('no MetaHuman IK rig at ' + MH_IK_RIG)

    retargeter = unreal.load_asset(RETARGETER)
    if retargeter is None:
        retargeter = tools.create_asset('RTG_WTA_Mixamo_to_MH', MOCAP_ROOT, unreal.IKRetargeter, unreal.IKRetargetFactory())
    controller = unreal.IKRetargeterController.get_controller(retargeter)
    controller.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, rig)
    controller.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, target_rig)
    controller.add_default_ops()
    controller.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
    # Mixamo stands in a T pose and a MetaHuman in an A pose: line the two up limb by limb, or every clip comes
    # out with the arms too high.
    controller.auto_align_all_bones(unreal.RetargetSourceOrTarget.SOURCE, unreal.RetargetAutoAlignMethod.CHAIN_TO_CHAIN)
    controller.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET, unreal.RetargetAutoAlignMethod.CHAIN_TO_CHAIN)
    return rig, retargeter


def _chains_by_hand(controller):
    """Mixamo's own bone names, in case the template ever stops matching."""
    controller.set_retarget_root('mixamorig:Hips')
    for chain, start, end, goal in [
        ('Root', 'mixamorig:Hips', 'mixamorig:Hips', ''),
        ('Spine', 'mixamorig:Spine', 'mixamorig:Spine2', ''),
        ('Neck', 'mixamorig:Neck', 'mixamorig:Neck', ''),
        ('Head', 'mixamorig:Head', 'mixamorig:Head', ''),
        ('LeftClavicle', 'mixamorig:LeftShoulder', 'mixamorig:LeftShoulder', ''),
        ('LeftArm', 'mixamorig:LeftArm', 'mixamorig:LeftHand', ''),
        ('RightClavicle', 'mixamorig:RightShoulder', 'mixamorig:RightShoulder', ''),
        ('RightArm', 'mixamorig:RightArm', 'mixamorig:RightHand', ''),
        ('LeftLeg', 'mixamorig:LeftUpLeg', 'mixamorig:LeftToeBase', ''),
        ('RightLeg', 'mixamorig:RightUpLeg', 'mixamorig:RightToeBase', ''),
        ('LeftThumb', 'mixamorig:LeftHandThumb1', 'mixamorig:LeftHandThumb3', ''),
        ('LeftIndex', 'mixamorig:LeftHandIndex1', 'mixamorig:LeftHandIndex3', ''),
        ('LeftMiddle', 'mixamorig:LeftHandMiddle1', 'mixamorig:LeftHandMiddle3', ''),
        ('LeftRing', 'mixamorig:LeftHandRing1', 'mixamorig:LeftHandRing3', ''),
        ('LeftPinky', 'mixamorig:LeftHandPinky1', 'mixamorig:LeftHandPinky3', ''),
        ('RightThumb', 'mixamorig:RightHandThumb1', 'mixamorig:RightHandThumb3', ''),
        ('RightIndex', 'mixamorig:RightHandIndex1', 'mixamorig:RightHandIndex3', ''),
        ('RightMiddle', 'mixamorig:RightHandMiddle1', 'mixamorig:RightHandMiddle3', ''),
        ('RightRing', 'mixamorig:RightHandRing1', 'mixamorig:RightHandRing3', ''),
        ('RightPinky', 'mixamorig:RightHandPinky1', 'mixamorig:RightHandPinky3', ''),
    ]:
        controller.add_retarget_chain(chain, start, end, goal)


def retarget(clips, mixamo_mesh, retargeter):
    """Retargets every raw clip onto the wax figures' body mesh."""
    target = unreal.load_asset(TARGET_BODY)
    if target is None:
        raise RuntimeError('no target body mesh at ' + TARGET_BODY)
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    by_name = {str(d.asset_name): d for d in registry.get_assets_by_path(RAW_PATH, recursive=False)}
    assets = [by_name[action] for action in sorted(clips) if action in by_name]
    missing = [action for action in sorted(clips) if action not in by_name]
    if missing:
        _warn('not in %s: %s' % (RAW_PATH, ', '.join(missing)))
    inputs = unreal.IKRetargetBatchOperationInputs()
    inputs.set_editor_property('assets_to_retarget', assets)
    inputs.set_editor_property('source_mesh', mixamo_mesh)
    inputs.set_editor_property('target_mesh', target)
    inputs.set_editor_property('ik_retarget_asset', retargeter)
    inputs.set_editor_property('prefix', PREFIX)
    inputs.set_editor_property('target_path', OUT_PATH)
    inputs.set_editor_property('use_source_path', False)
    inputs.set_editor_property('include_referenced_assets', False)
    inputs.set_editor_property('overwrite_existing_files', True)
    made = unreal.IKRetargetBatchOperation.run_batch_retarget(inputs)
    _log('retargeted %d of %d clips' % (len(made), len(assets)))
    return [str(a.package_name) for a in made]


def run(clip_folder=CLIP_FOLDER):
    mesh, skeleton, source_anim = import_source(clip_folder)
    clips = import_clips(clip_folder, skeleton)
    # The figure's own clip is the neutral idle every scene falls back to.
    if source_anim is not None and 'idle' not in clips:
        renamed = unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset('idle', RAW_PATH, source_anim)
        if renamed is not None:
            clips['idle'] = renamed
    rig, retargeter = build_rigs(mesh)
    made = retarget(clips, mesh, retargeter)
    unreal.EditorAssetLibrary.save_directory(MOCAP_ROOT, False, True)
    unreal.EditorAssetLibrary.save_directory(OUT_PATH, False, True)
    # the retarget points the standing clips' feet straight down: turn them back (fix_feet.py); it also keys the
    # pelvis 17 cm above the hips: bring it down to them (fix_hips.py)
    from . import fix_feet, fix_hips
    fix_feet.run()
    fix_hips.run()
    _log('done: %d clips at %s' % (len(made), OUT_PATH))
    return made
