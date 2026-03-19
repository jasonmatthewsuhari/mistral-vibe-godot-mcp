import base64
import re
from io import BytesIO
from typing import Tuple

import httpx
import PIL.Image

BASE_URL = "https://api.pixellab.ai/v1"
DEFAULT_SIZE = {"width": 256, "height": 256}

# Matches: 512x512, 512 x 512, 512×512, 512 by 512
_SIZE_RE = re.compile(r"\b(\d+)\s*(?:x|×|by)\s*(\d+)\b", re.IGNORECASE)


def _extract_size(prompt: str) -> Tuple[dict, str]:
    """Return (image_size dict, cleaned prompt). Falls back to DEFAULT_SIZE."""
    match = _SIZE_RE.search(prompt)
    if match:
        w, h = int(match.group(1)), int(match.group(2))
        cleaned = _SIZE_RE.sub("", prompt).strip(" ,.")
        return {"width": w, "height": h}, cleaned
    return DEFAULT_SIZE, prompt


async def generate_image(prompt: str, key: str) -> bytes:
    size, description = _extract_size(prompt)
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/generate-image-pixflux",
            headers={"Authorization": f"Bearer {key}"},
            json={"description": description, "image_size": size},
        )
        response.raise_for_status()
        return base64.b64decode(response.json()["image"]["base64"])


async def modify_image(prompt: str, image_b64: str, key: str) -> bytes:
    size, description = _extract_size(prompt)
    w, h = size["width"], size["height"]

    # Resize init_image to match requested output dimensions (PixelLab requires them to match)
    pil_img = PIL.Image.open(BytesIO(base64.b64decode(image_b64))).convert("RGBA")
    if pil_img.size != (w, h):
        pil_img = pil_img.resize((w, h), PIL.Image.LANCZOS)
    buf = BytesIO()
    pil_img.save(buf, format="PNG")
    resized_b64 = base64.b64encode(buf.getvalue()).decode()

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/generate-image-pixflux",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "description": description,
                "image_size": size,
                "init_image": {"type": "base64", "base64": resized_b64, "format": "png"},
                "init_image_strength": 200,
            },
        )
        response.raise_for_status()
        return base64.b64decode(response.json()["image"]["base64"])
