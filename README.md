# blender-intrinsic-lora
Use Stable Diffusion intrinsic lora to render texture maps (normal, albedo, shade, depth)

Blender implementation of 

https://intrinsic-lora.github.io/


Example video:

https://youtu.be/oTtM4-GYlXk


1. You need stable diffusion 1.5 in safetensors format. This for example: https://huggingface.co/runwayml/stable-diffusion-v1-5/

2. You need the loras. Download from here: https://huggingface.co/neph1/intrinsic_lora and place in intrinsic_lora_addon/pretrained_weights

3. Install the intrinsic_lora_addon in your addons folder

4. Config the path to the sd 1.5 checkpoint in the addon preferences.

5. The panel is in the render tab. Pick one (for now) and render it to the selected texture in the selected material.
