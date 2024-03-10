

bl_info = {
    "name": "Intrinsic LoRA",
    "author": "Rickard Edén",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "Render > Intrinsic LoRA Render",
    "description": "Render textures using Stable Diffusion Intrinsic LoRA",
    "warning": "",
    "doc_url": "https://github.com/neph1/blender-intrinsic-lora",
    "category": "Render",
}

if "bpy" in locals():
    import importlib
    importlib.reload(base64)
    importlib.reload(numpy)
    importlib.reload(image_utils)
    importlib.reload(camera_utils)
else:
    import base64
    import numpy

import bpy

from . import generate_texture

from bpy.props import (PointerProperty)

from bpy.types import (Panel,
                       PropertyGroup,
                       )

class ModelSelector(bpy.types.AddonPreferences):
    bl_idname = __name__

    model: bpy.props.StringProperty(
        name="Model",
        description="The path to the model to use for rendering (sd 1.5)",
        default="",
    )

    config: bpy.props.StringProperty(
        name="Config",
        description="Config for the model. Required for offline.",
        default="",
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "model")
        layout.prop(self, "config")

class IntrinsicLoRAProperties(PropertyGroup):

    normal_map: bpy.props.BoolProperty(
        name="Normal Map",
        description="Render normal map",
        default=False,
    )

    depth_map: bpy.props.BoolProperty(
        name="Depth Map",
        description="Render depth map",
        default=False,
    )

    albedo_map: bpy.props.BoolProperty(
        name="Albedo Map",
        description="Render albedo map",
        default=False,
    )

    shading_map: bpy.props.BoolProperty(
        name="Shading Map",
        description="Render shading map",
        default=False,
    )

    size: bpy.props.IntProperty(
        name="Size",
        description="Size of the rendered image",
        default=512,
    )

    delete_projector: bpy.props.BoolProperty(
        name="Delete Projector",
        description="Delete projector after rendering",
        default=True,
    )

    model: bpy.props.StringProperty(
        name="Model",
        description="The path to the model to use for rendering (sd 1.5)",
        default="",
    )


class IntrinsicLoRASettings(Panel):

    bl_idname = "RENDER_PT_intrinsic_lora_settings"
    bl_label = "Intrinsic LoRA Settings"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        intrinsic_lora_properties = scene.intrinsic_lora_properties

        layout.prop(intrinsic_lora_properties, "normal_map")
        layout.prop(intrinsic_lora_properties, "depth_map")
        layout.prop(intrinsic_lora_properties, "albedo_map")
        layout.prop(intrinsic_lora_properties, "shading_map")

        layout.prop(intrinsic_lora_properties, "size")
        layout.separator()
        layout.prop(intrinsic_lora_properties, "delete_projector")

        col = self.layout.column(align=True)
        col.operator(RenderButton_operator.bl_idname, text="Render")
        #col.operator(ConvertNormalMapButton_operator.bl_idname, text="Convert Normal Map")

class RenderButton_operator(bpy.types.Operator):
    bl_idname = "intrinsic_lora.render_button"
    bl_label = "Render"

    def execute(self, context):
        result = generate_texture.execute()
        if result:
            self.report({'ERROR'}, result)
        return {'FINISHED'}
    
class ConvertNormalMapButton_operator(bpy.types.Operator):
    bl_idname = "intrinsic_lora.convert_normal_map_button"
    bl_label = "Convert Normal Map"

    def execute(self, context):
        result = generate_texture.convert_normal_map()
        if result:
            self.report({'ERROR'}, result)
        return {'FINISHED'}
    
def register():
    bpy.utils.register_class(ModelSelector)
    prefs = bpy.context.preferences.addons[__name__].preferences

    bpy.utils.register_class(RenderButton_operator)
    #bpy.utils.register_class(ConvertNormalMapButton_operator)
    bpy.utils.register_class(IntrinsicLoRAProperties)
    bpy.types.Scene.intrinsic_lora_properties = PointerProperty(type=IntrinsicLoRAProperties)
    bpy.utils.register_class(IntrinsicLoRASettings)

def unregister():
    bpy.utils.unregister_class(RenderButton_operator)
    #bpy.utils.unregister_class(ConvertNormalMapButton_operator)
    bpy.utils.unregister_class(ModelSelector)

    bpy.utils.unregister_class(IntrinsicLoRAProperties)
    bpy.utils.unregister_class(IntrinsicLoRASettings)

if __name__ == "__main__":
    register()