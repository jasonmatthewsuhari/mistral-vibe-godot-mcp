import os
import warnings
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv(Path(__file__).parent / ".env")

from routes.generate_asset import router as generate_asset_router
from routes.modify_asset import router as modify_asset_router
from routes.automate import router as automate_router

app = FastAPI(title="Vibe Plugin Backend", version="0.1.0")

app.include_router(generate_asset_router)
app.include_router(modify_asset_router)
app.include_router(automate_router)


@app.on_event("startup")
async def _validate_env() -> None:
    has_pixellab = bool(os.getenv("PIXELLAB_API_KEY"))
    has_llm = any(os.getenv(k) for k in ("OPENAI_API_KEY", "MISTRAL_API_KEY", "GEMINI_API_KEY"))
    missing = []
    if not has_pixellab:
        missing.append("PIXELLAB_API_KEY")
    if not has_llm:
        missing.append("OPENAI_API_KEY / MISTRAL_API_KEY / GEMINI_API_KEY")
    if missing:
        warnings.warn(
            f"Vibe backend: missing env vars -- {', '.join(missing)}. "
            "Asset generation and automation will return 502 until keys are configured.",
            stacklevel=1,
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8765, reload=True)
