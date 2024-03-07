import bpy

def create_projector_object(obj):
    """Create a projector object"""
    obj_data = obj.data.copy()
    projector = bpy.data.objects.new(name="TextureProjector", object_data=obj_data)
    projector.data.uv_layers.remove(projector.data.uv_layers[0])
    projector.data.uv_layers.new(name="bake")
    bpy.context.collection.objects.link(projector)
    return projector

def setup_projector_material(depth_map = None, normal_map = None, albedo_map = None, shading_map = None):
    """Set up projector material with the rendered image"""
    projector_material = bpy.data.materials.new(name="TextureProjectorMaterial")
    projector_material.use_nodes = True
    projector_material.node_tree.nodes.clear()
    bdsf_node = projector_material.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    if depth_map:
        depth_map_node = projector_material.node_tree.nodes.new('ShaderNodeTexImage')
        depth_map_node.image = depth_map
        projector_material.node_tree.links.new(depth_map_node.outputs[0], bdsf_node.inputs[0])
    if normal_map:
        normal_map_node = projector_material.node_tree.nodes.new('ShaderNodeTexImage')
        normal_map_node.image = normal_map
        projector_material.node_tree.links.new(normal_map_node.outputs[0], bdsf_node.inputs[18])
    if albedo_map:
        albedo_map_node = projector_material.node_tree.nodes.new('ShaderNodeTexImage')
        albedo_map_node.image = albedo_map
        projector_material.node_tree.links.new(albedo_map_node.outputs[0], bdsf_node.inputs[3])
    if shading_map:
        shading_map_node = projector_material.node_tree.nodes.new('ShaderNodeTexImage')
        shading_map_node.image = shading_map
        projector_material.node_tree.links.new(shading_map_node.outputs[0], bdsf_node.inputs[17])
    
    output_node = projector_material.node_tree.nodes.new('ShaderNodeOutputMaterial')
    projector_material.node_tree.links.new(bdsf_node.outputs[0], output_node.inputs[0])
    return projector_material

def assign_material_to_projector(projector, projector_material):
    """Assign projector material to projector object"""
    if not projector.data.materials:
        projector.data.materials.append(projector_material)
    else:
        projector.data.materials[0] = projector_material

def set_projector_position_and_orientation(projector, target_object):
    """Set projector position and orientation"""
    projector.location = target_object.location
    projector.rotation_euler = target_object.rotation_euler

def bake_from_active(projector, target_object, depth, normal, albedo, shading):
    bpy.context.active_object.select_set(False)
    projector.select_set(True)
    #bpy.context.view_layer.objects.active = target_object
    bpy.context.view_layer.objects.active = target_object
    target_object.select_set(True)
    bpy.context.scene.render.bake.use_selected_to_active = True
    if depth:
        type = 'DISPLACEMENT'
    if normal:
        type = 'NORMAL'
        #bpy.context.scene.render.bake.normal_space = 'TANGENT'
        #bpy.context.scene.render.bake.normal_r = 0.5
        #bpy.context.scene.render.bake.normal_g = 0.5
        #bpy.context.scene.render.bake.normal_b = 1.0
    if albedo:
        type = 'DIFFUSE'
    if shading:
        type = 'AO'
    
    bpy.ops.object.bake(type=type, use_clear=True, cage_extrusion=0.1)
    
def remove_projector(projector):
    bpy.data.materials.remove(projector.data.materials[0])
    bpy.data.objects.remove(projector)
