import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from pixellab_client import modify_image

router = APIRouter()


class ModifyAssetRequest(BaseModel):
    prompt: str
    file_path: str
    image_base64: str


class ModifyAssetResponse(BaseModel):
    ok: bool
    file_path: str


@router.post("/modify-asset", response_model=ModifyAssetResponse)
async def modify_asset(body: ModifyAssetRequest) -> ModifyAssetResponse:
    api_key = os.getenv("PIXELLAB_API_KEY")
    if not api_key:
        raise HTTPException(status_code=502, detail="PIXELLAB_API_KEY not configured")

    if body.file_path.startswith("res://"):
        raise HTTPException(
            status_code=400,
            detail="file_path must be an absolute filesystem path, not a res:// path",
        )

    dest = Path(body.file_path)
    if not dest.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {body.file_path}")

    try:
        image_bytes = await modify_image(body.prompt, body.image_base64, api_key)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"PixelLab error: {exc}") from exc

    dest.write_bytes(image_bytes)

    return ModifyAssetResponse(ok=True, file_path=str(dest))
