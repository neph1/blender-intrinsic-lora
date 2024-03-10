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
        #displacement_map = projector_material.node_tree.nodes.new(type='ShaderNodeDisplacement')
        #projector_material.node_tree.links.new(depth_map_node.outputs[0], displacement_map.inputs['Height'])
        projector_material.node_tree.links.new(depth_map_node.outputs[0], bdsf_node.inputs['Base Color'])
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
        projector_material.node_tree.links.new(shading_map_node.outputs[0], bdsf_node.inputs['Base Color'])
    
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
    material = obj.data.materials[obj.active_material_index]
    # Select the normal map texture
    normal_map_node = material.node_tree.nodes.active
    
    if not normal_map_node:
        return "No normal map found in material nodes."

        # Get the normal map image
    normal_map_texture = normal_map_node.image
    
    if not normal_map_texture:
        return "No normal map image found."
    # Get the tangent and bitangent from UV map
    mesh = obj.data
    #bm = bpy.data.meshes.new(obj.name + "_temp")
    #bm.from_mesh(mesh)
    #bm.calc_tangents()

    difference_values = []

    # Loop through each polygon and access its vertices and normals
    for polygon in mesh.polygons:
        # Access vertex indices and corresponding normals from the polygon
        vertex_indices = polygon.loop_indices-1
        vertex_normals = [mesh.vertices[index].normal for index in vertex_indices]

    # Process each vertex normal
    for vertex_normal in vertex_normals:
        # Get the corresponding pixel value from the normal map texture
        # This might require additional logic depending on UV mapping

        # Assuming UV coordinates are available in 'loop_data' for each vertex
        loop_data = mesh.loops[polygon.loop_indices[0]]
        uv_coord = loop_data.uv

        # Implement UV to pixel mapping logic here to get the corresponding pixel
        # This can involve texture coordinates and image dimensions
        # (Replace this with your UV mapping logic)
        map_pixel_index = calculate_pixel_index(uv_coord, normal_map_texture.width, normal_map_texture.height)
        map_normal_pixel = normal_map_texture.pixels[map_pixel_index][:3]

        # Calculate difference between vertex normal and map normal
        difference = [v - m for v, m in zip(vertex_normal, map_normal)]
        difference_values.append(difference)

    # Create a new image data block for the difference map
    difference_map = bpy.data.images.new("difference_normal_map", width=normal_map_texture.width, height=normal_map_texture.height)

    # Fill the pixels with the calculated difference values
    pixels = difference_map.pixels
    for i, difference in enumerate(difference_values):
        # Convert difference values back to (0, 255) range
        pixel_data = [(d * 127.5) + 127.5 for d in difference]
        pixels[i][:3] = pixel_data
        
    model_space_normal_map_node = obj.data.materials[0].node_tree.nodes.new(type='ShaderNodeTexImage')
    model_space_normal_map_node.image = difference_map


    return "Model space normal map created successfully."

