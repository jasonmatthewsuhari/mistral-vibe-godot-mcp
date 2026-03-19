import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from pixellab_client import generate_image

router = APIRouter()


class GenerateAssetRequest(BaseModel):
    prompt: str
    folder_path: str


class GenerateAssetResponse(BaseModel):
    ok: bool
    file_path: str


@router.post("/generate-asset", response_model=GenerateAssetResponse)
async def generate_asset(body: GenerateAssetRequest) -> GenerateAssetResponse:
    api_key = os.getenv("PIXELLAB_API_KEY")
    if not api_key:
        raise HTTPException(status_code=502, detail="PIXELLAB_API_KEY not configured")

    try:
        image_bytes = await generate_image(body.prompt, api_key)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"PixelLab error: {exc}") from exc

    # Derive a filename from the prompt (slug first 30 chars)
    slug = "".join(c if c.isalnum() else "_" for c in body.prompt[:30]).strip("_")
    filename = f"{slug or 'generated'}.png"

    # folder_path may be a res:// path; strip prefix for filesystem writes
    folder = body.folder_path
    if folder.startswith("res://"):
        # Caller should pass an absolute path; if not, we can't resolve it here.
        raise HTTPException(
            status_code=400,
            detail="folder_path must be an absolute filesystem path, not a res:// path",
        )

    dest_dir = Path(folder)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / filename
    dest_file.write_bytes(image_bytes)

    return GenerateAssetResponse(ok=True, file_path=str(dest_file))
