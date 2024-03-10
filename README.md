# blender-intrinsic-lora
Use Stable Diffusion intrinsic lora to render texture maps (normal, albedo, shade, depth)

![intrinsic_lora](https://github.com/neph1/blender-intrinsic-lora/assets/7988802/0b63d94a-1e5d-4792-8893-b88e6e2cf496)


Blender implementation of 

https://intrinsic-lora.github.io/

Like with blender-stable-diffusion-render, this addon bakes the resulting texture back to you UV-mapped model.

Each texture generated will create a new node in the material. You're responsible for linking them.

Example video:

https://youtu.be/oTtM4-GYlXk


1. You need stable diffusion 1.5 in safetensors format. This for example: https://huggingface.co/runwayml/stable-diffusion-v1-5/

2. You need the loras. Download from here: https://huggingface.co/neph1/intrinsic_lora and place in intrinsic_lora_addon/pretrained_weights

3. Install the intrinsic_lora_addon in your addons folder

4. Config the path to the sd 1.5 checkpoint in the addon preferences. Config is optional, but required for running offline.
![Screenshot from 2024-03-10 20-34-13](https://github.com/neph1/blender-intrinsic-lora/assets/7988802/011c7c93-5c3f-431a-a05a-8d8911c47a8d)


6. The panel is in the render tab. Pick one (for now) and render it to the selected texture in the selected material.
![Screenshot from 2024-03-10 15-58-35](https://github.com/neph1/blender-intrinsic-lora/assets/7988802/4abf582b-72e2-462a-be2b-37fc9bb48604)

I think the model only supports 512x512 textures, but feel free to try larger sizes.

Please generate one texture at a time for now.
