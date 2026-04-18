import torch
from diffusers import StableDiffusionPipeline
from PIL import Image

class ImageGenerator:
    device: str
    model: StableDiffusionPipeline

    def __init__(self, model_id: str = 'stable-diffusion-v1-5/stable-diffusion-v1-5'):
        # init model, use 16-bit for memory optimization
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        dtype = torch.float16 if self.device == 'cuda' else torch.float32
        self.model = StableDiffusionPipeline.from_pretrained(
            model_id, 
            torch_dtype=dtype
        )
        self.model = self.model.to(self.device)
        
        sample_image = self.model("a cat", num_inference_steps=1).images[0]
        sample_image.save('sample_image.png')
        print("Dry run successful")

    def generate(self, 
                 prompt: str = "An astronaught riding a horse on the moon", 
                 negative_prompt: str = '',
                 steps: int = 50, 
                 cfg_scale: float = 7.0,
                 seed: int = 42,
                 save: bool = False,
                 save_path: str = './image.png') -> Image.Image:
        try:
            generator = torch.Generator(self.device).manual_seed(seed)
            image = self.model(
                prompt=prompt, 
                negative_prompt=negative_prompt, 
                num_inference_steps=steps, 
                guidance_scale=cfg_scale,
                generator=generator
            ).images[0]
            if save:
                image.save(save_path)
        except Exception as e:
            print(f"Error during image generation: {type(e).__name__} - {e}")
            return None
        return image