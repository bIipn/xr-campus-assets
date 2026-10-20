"""Materials for the Wax Hall hand props.

The props the reenactors hold are blocks (AWTAWaxStageActor::WaxPropKind) and a block with the engine's default
checker on it reads as a missing texture. These are three flat, cheap materials - a dark plastic, paper and
cardboard - matching the flat look the web campus has.

Run it from the editor's Python console:  import wta_mocap.props as p; p.run()
"""

import unreal

FOLDER = '/Game/WTA/Materials'
COLOURS = {
    'M_WTA_PropDark':  ((0.035, 0.038, 0.045), 0.38),
    'M_WTA_PropPaper': ((0.72, 0.68, 0.58), 0.80),
    'M_WTA_PropCard':  ((0.40, 0.27, 0.16), 0.85),
}


def make(name, colour, roughness):
    path = '%s/%s' % (FOLDER, name)
    existing = unreal.load_asset(path)
    if existing is not None:
        return existing
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    material = tools.create_asset(name, FOLDER, unreal.Material, unreal.MaterialFactoryNew())
    base = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionVectorParameter, -400, 0)
    base.set_editor_property('parameter_name', 'Colour')
    base.set_editor_property('default_value', unreal.LinearColor(colour[0], colour[1], colour[2], 1.0))
    rough = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionScalarParameter, -400, 200)
    rough.set_editor_property('parameter_name', 'Roughness')
    rough.set_editor_property('default_value', roughness)
    unreal.MaterialEditingLibrary.connect_material_property(base, '', unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.recompile_material(material)
    return material


def run():
    made = []
    for name, (colour, roughness) in COLOURS.items():
        material = make(name, colour, roughness)
        made.append(material.get_path_name() if material else '(failed) ' + name)
    unreal.EditorAssetLibrary.save_directory(FOLDER, False, True)
    for m in made:
        unreal.log('[wta_props] ' + m)
    return made
