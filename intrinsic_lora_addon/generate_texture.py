import bpy
import logging
from intrinsic_lora_addon.camera_utils import project_uvs, render_viewport
from intrinsic_lora_addon.intrinsic_lora import IntrinsicLoRAImageGenerator

from intrinsic_lora_addon.image_utils import bake_from_active, create_projector_object, set_projector_position_and_orientation, setup_projector_material, assign_material_to_projector, remove_projector, transform_normal_map

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

def generate(obj) -> str:
    props = bpy.context.scene.intrinsic_lora_properties
    output_folder = bpy.context.scene.render.filepath
    size = props.size
    rendered_image = render_viewport(size, size, output_folder)
    print("Output folder:", output_folder)
    model = bpy.context.preferences.addons['intrinsic_lora_addon'].preferences.model
    print("Model:", model)
    generator = IntrinsicLoRAImageGenerator(pretrained_model_name_or_path=model)
    depth_map = None
    normal_map = None
    albedo_map = None
    shade_map = None
    image_path = f"{output_folder}/intrinsic_render.png"
    if props.depth_map:
        generator.generate_image(image_path, output_folder, task='depth')
        depth_map = bpy.data.images.load(f"{output_folder}/intrinsic_render_depth.png")
    if props.normal_map:
        generator.generate_image(image_path, output_folder, task='normal')
        normal_map = bpy.data.images.load(f"{output_folder}/intrinsic_render_normal.png")
    if props.albedo_map:
        generator.generate_image(image_path, output_folder, task='albedo')
        albedo_map = bpy.data.images.load(f"{output_folder}/intrinsic_render_albedo.png")
    if props.shading_map:
        generator.generate_image(image_path, output_folder, task='shading')
        shade_map = bpy.data.images.load(f"{output_folder}/intrinsic_render_shading.png")

    target_object = obj
    
    bpy.context.active_object.select_set(False)
    
    projector = create_projector_object(target_object)
    bpy.context.view_layer.objects.active = projector
    set_projector_position_and_orientation(projector, target_object)
    projector_material = setup_projector_material(depth_map, normal_map, albedo_map, shade_map)
    assign_material_to_projector(projector, projector_material)
    bpy.ops.object.mode_set(mode = 'OBJECT')
    project_uvs(projector)
    
    bake_from_active(projector, target_object, depth_map, normal_map, albedo_map, shade_map, size)

    if props.delete_projector:
        remove_projector(projector)
        
    generator.close()

def convert_normal_map():
    if len(bpy.context.selected_objects) > 0:
        obj = bpy.context.selected_objects[0]
        transform_normal_map(obj)
    else:
        return "No object selected. Please select an object."
 
def execute():
    if len(bpy.context.selected_objects) > 0:
        obj = bpy.context.selected_objects[0]
        if obj.type == 'CAMERA':
            return "Cannot generate texture for camera. Please select an object."
        return generate(obj)
    else:
        return "No object selected. Please select an object."