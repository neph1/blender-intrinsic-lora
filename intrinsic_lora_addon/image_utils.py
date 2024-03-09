import bpy
import numpy as np

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
    output_node = projector_material.node_tree.nodes.new('ShaderNodeOutputMaterial')
    if depth_map:
        depth_map_node = projector_material.node_tree.nodes.new('ShaderNodeTexImage')
        depth_map_node.image = depth_map
        displacement_map = projector_material.node_tree.nodes.new(type='ShaderNodeDisplacement')
        projector_material.node_tree.links.new(depth_map_node.outputs[0], displacement_map.inputs['Height'])
        projector_material.node_tree.links.new(displacement_map.outputs[0], output_node.inputs['Displacement'])
    if normal_map:
        normal_map_node = projector_material.node_tree.nodes.new('ShaderNodeTexImage')
        normal_map_node.image = normal_map
        normal_map = projector_material.node_tree.nodes.new(type='ShaderNodeNormalMap')
        projector_material.node_tree.links.new(normal_map_node.outputs[0], normal_map.inputs[1])
        projector_material.node_tree.links.new(normal_map.outputs[0], bdsf_node.inputs['Normal'])
    if albedo_map:
        albedo_map_node = projector_material.node_tree.nodes.new('ShaderNodeTexImage')
        albedo_map_node.image = albedo_map
        projector_material.node_tree.links.new(albedo_map_node.outputs[0], bdsf_node.inputs['Base Color'])
    if shading_map:
        shading_map_node = projector_material.node_tree.nodes.new('ShaderNodeTexImage')
        shading_map_node.image = shading_map
        projector_material.node_tree.links.new(shading_map_node.outputs[0], bdsf_node.inputs[3])
    
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

def bake_from_active(projector, target_object, depth: bool, normal: bool, albedo: bool, shading: bool, size: int):
    bpy.context.active_object.select_set(False)
    projector.select_set(True)
    #bpy.context.view_layer.objects.active = target_object
    bpy.context.view_layer.objects.active = target_object
    target_object.select_set(True)
    bpy.context.scene.render.bake.use_selected_to_active = True
    types = []
    if depth:
        types.append('DIFFUSE')
    if normal:
        types.append('NORMAL')
    if albedo:
        types.append('DIFFUSE')
    if shading:
        types.append('DIFFUSE')

    for type in types:
        create_texture_node(target_object, type, size, size)
        bpy.ops.object.bake(type=type, use_clear=True, cage_extrusion=0.1)

def create_texture_node(obj, texture_name, image_width, image_height):
    """Create a texture node for baking"""
    material = obj.data.materials[obj.active_material_index]
    image = bpy.data.images.new(name=texture_name, width=image_width, height=image_height)
    texture_node_image = material.node_tree.nodes.new('ShaderNodeTexImage')
    texture_node_image.image = image
    material.node_tree.nodes.active = texture_node_image
    return texture_node_image

    
def remove_projector(projector):
    bpy.data.materials.remove(projector.data.materials[0])
    bpy.data.objects.remove(projector)

def world_to_model_normal(world_normal, tangent, bitangent):
    tangent = np.array(tangent)
    bitangent = np.array(bitangent)
    normal = np.array(world_normal)

    TBN = np.column_stack((tangent, bitangent, normal)).T
    model_normal = np.linalg.inv(TBN) @ normal

    return model_normal

def transform_normal_map(obj):
    bpy.context.view_layer.objects.active = obj
    
    # Ensure the object has a UV map
    if not obj.data.uv_layers:
        return "Object has no UV map."

    # Select the normal map texture
    normal_map_node = None
    for mat_slot in obj.material_slots:
        if mat_slot.material:
            for node in mat_slot.material.node_tree.nodes:
                if node.type == 'NORMAL_MAP':
                    normal_map_node = node
                    break

    if not normal_map_node:
        return "No normal map found in material nodes."

    # Get the tangent and bitangent from UV map
    mesh = obj.data
    bm = bpy.data.meshes.new(obj.name + "_temp")
    bm.from_mesh(mesh)
    bm.calc_tangents()

    for face in bm.faces:
        for loop_index, loop in enumerate(face.loops):
            tangent = loop.tangent
            bitangent = loop.bitangent
            break

    bm.free()

    # Get the normal map image
    normal_map_texture = None
    for slot in obj.material_slots:
        if slot.material:
            for texture_slot in slot.material.texture_slots:
                if texture_slot and texture_slot.texture.type == 'IMAGE':
                    normal_map_texture = texture_slot.texture.image
                    break

    if not normal_map_texture:
        return "No normal map image found."

    # Create a new image for the model space normal map
    model_space_normal_map = bpy.data.images.new(obj.name + "_model_space_normal_map", width=normal_map_texture.size[0], height=normal_map_texture.size[1])

    # Transform each pixel in the normal map
    world_normals = np.array(normal_map_texture.pixels[:]).reshape(normal_map_texture.size[1], normal_map_texture.size[0], 4)

    for y in range(normal_map_texture.size[1]):
        for x in range(normal_map_texture.size[0]):
            world_normal = world_normals[y, x, :3]
            model_normal = world_to_model_normal(world_normal, tangent, bitangent)
            model_space_normal_map.pixels[(y * normal_map_texture.size[0] + x) * 4:(y * normal_map_texture.size[0] + x + 1) * 4] = [*model_normal, 1.0]

    # Assign the model space normal map to the material
    model_space_normal_map.pack()
    normal_map_texture.user_clear()
    normal_map_texture.user_of_texture_clear()
    normal_map_texture.user_of_image_clear()
    obj.data.materials[0].node_tree.nodes.remove(normal_map_node)
    model_space_normal_map_node = obj.data.materials[0].node_tree.nodes.new(type='ShaderNodeTexImage')
    model_space_normal_map_node.image = model_space_normal_map
    obj.data.materials[0].node_tree.links.new(normal_map_node.outputs[0], model_space_normal_map_node.inputs[0])

    return "Model space normal map created successfully."

