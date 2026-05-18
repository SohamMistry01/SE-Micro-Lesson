import torch
from diffusers.pipelines.auto_pipeline import AutoPipelineForText2Image
from io import BytesIO


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
pipe = AutoPipelineForText2Image.from_pretrained(
    "stabilityai/sdxl-turbo",
    torch_dtype=torch.float32,
).to(DEVICE)


def make_generator(seed: int):
    return torch.Generator(device=DEVICE).manual_seed(seed)


def generate_image(prompt: str, seed: int = 42, steps: int = 1):
    image = pipe(
        prompt=prompt,
        num_inference_steps=steps,
        guidance_scale=0.0,
        generator=make_generator(seed),
    ).images[0]
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()
