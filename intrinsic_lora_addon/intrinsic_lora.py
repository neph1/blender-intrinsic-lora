from collections import defaultdict
import gc
import os
import torch
import numpy as np
from PIL import Image
from pathlib import Path
from torchvision import transforms
from torchvision.transforms.functional import pil_to_tensor, to_pil_image
from diffusers import StableDiffusionPipeline
from diffusers.loaders import LoraLoaderMixin

class IntrinsicLoRAImageGenerator:
    def __init__(self, pretrained_model_name_or_path, config=None):
        self.pretrained_model_name_or_path = pretrained_model_name_or_path
        self.config = config
        self.unet = None
        self.tokenizer = None
        self.text_encoder = None
        self.vae = None
        self.scheduler = None
        self.max_timestep = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.task = None
        self.load_model()

    def load_model(self):

        self.pipeline = StableDiffusionPipeline.from_single_file(self.pretrained_model_name_or_path, original_config_file=self.config, local_files_only=True if self.config else False, load_safety_checker=False)
        self.pipeline.to(self.device)
        self.unet = self.pipeline.unet
        self.text_encoder = self.pipeline.text_encoder
        self.tokenizer = self.pipeline.tokenizer
        self.pipeline.text_encoder = self.text_encoder
        self.vae = self.pipeline.vae
        self.scheduler = self.pipeline.scheduler
        self.max_timestep = self.pipeline.scheduler.config.num_train_timesteps
        

    def generate_image(self, input_image_path, output_dir, task: str = None) -> Image.Image:
        if not task:
            print('Task not specified')
            return None
        
        if task != self.task:
            self.pipeline.unload_lora_weights()
            model_path = self.get_lora_path(task)
            self.unet, self.text_encoder = load_lora_weights(self.pipeline.unet, self.pipeline.text_encoder, os.path.join(os.path.dirname(__file__), model_path), self.device)
            self.pipeline.unet = self.unet
            self.pipeline.text_encoder = self.text_encoder

        self.task = task

        image_transforms = transforms.Compose([
            transforms.Resize(512, interpolation=transforms.InterpolationMode.BILINEAR),
            transforms.CenterCrop(512),
            transforms.ToTensor(),
            transforms.Normalize([0.5], [0.5]),
        ])
        with torch.inference_mode():
            with Image.open(input_image_path) as orig_img:
                orig_img = orig_img.convert("RGB")
                orig_img_tensor = image_transforms(orig_img).unsqueeze(0).to(self.device)

                timesteps = torch.randint(self.max_timestep - 1, self.max_timestep, (1,), device=self.device).long()
                original_image_embeds = self.vae.encode(orig_img_tensor).latent_dist.mode()
                original_image_embeds = original_image_embeds * self.vae.config.scaling_factor

                prompt = self.get_prompt(self.task)
                text_inputs = tokenize_prompt(self.tokenizer, prompt).input_ids.to(self.device)
                encoder_hidden_states = self.text_encoder(text_inputs)[0]

                model_pred = self.unet(original_image_embeds, timesteps, encoder_hidden_states).sample
                image = self.vae.decode(model_pred / self.vae.config.scaling_factor, return_dict=False)[0]

                if self.task == 'depth':
                    imax = image.max()
                    imin = image.min()
                    image = (image-imin)/(imax-imin)
                    image = image.squeeze().mean(0)
                    image = image.cpu().numpy() * 255.
                    val_image = Image.fromarray(image.astype(np.uint8))
                elif self.task == 'normal':
                    image = tensor2np(image.clamp(-1.,1.).squeeze())
                    val_image = Image.fromarray((255 - image).astype(np.uint8))
                else:
                    image = tensor2np(image.clamp(-1., 1.).squeeze())
                    val_image = Image.fromarray(image)
                if output_dir:
                    pred_path = f'{output_dir}/{Path(input_image_path).stem}_{self.task}.png'
                    val_image.save(pred_path)
                return val_image

    def get_prompt(self, task: str):
        if task == 'normal':
            return 'surface normal'
        elif task == 'depth':
            return 'depth map'
        elif task == 'albedo':
            return 'albedo'
        elif task == 'shading':
            return 'shading'
        else:
            raise NotImplementedError('Not implemented')
        
    def get_lora_path(self, task: str):
        if task == 'normal':
            return "pretrained_weights/intrinsic_lora_normal.safetensors"
        elif task == 'depth':
            return "pretrained_weights/intrinsic_lora_depth.safetensors"
        elif task == 'albedo':
            return "pretrained_weights/intrinsic_lora_albedo.safetensors"
        elif task == 'shading':
            return "pretrained_weights/intrinsic_lora_shading.safetensors"
        else:
            raise NotImplementedError('Not implemented')
        
    def close(self):
        self.pipeline.unload_lora_weights()
        self.pipeline.maybe_free_model_hooks()
        del self.pipeline
        gc.collect()
        if self.device == 'cuda':
            torch.cuda.empty_cache()
        
def tokenize_prompt(tokenizer, prompt, tokenizer_max_length=None):
    if tokenizer_max_length is not None:
        max_length = tokenizer_max_length
    else:
        max_length = tokenizer.model_max_length

    text_inputs = tokenizer(
        prompt,
        truncation=True,
        padding="max_length",
        max_length=max_length,
        return_tensors="pt",
    )
    return text_inputs

def tensor2np(tensor):
    return (255*(tensor.cpu().permute(1,2,0).numpy()*0.5+0.5)).astype(np.uint8)

def load_lora_weights(unet, text_encoder, input_dir, device):
    lora_state_dict, network_alphas = LoraLoaderMixin.lora_state_dict(input_dir)

    LoraLoaderMixin.load_lora_into_unet(
        lora_state_dict, network_alphas=network_alphas, unet=unet
    )
    LoraLoaderMixin.load_lora_into_text_encoder(
        lora_state_dict, network_alphas=network_alphas, text_encoder=text_encoder
    )
    unet.to(device)
    text_encoder.to(device)
    return unet, text_encoder