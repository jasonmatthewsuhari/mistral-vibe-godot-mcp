import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from llm_client import generate_gdscript

router = APIRouter()

_FENCE_RE = re.compile(r"^```(?:gdscript)?\s*\n?(.*?)\n?```\s*$", re.DOTALL)


def _strip_fences(code: str) -> str:
    match = _FENCE_RE.match(code.strip())
    if match:
        return match.group(1)
    return code.strip()


class AutomateRequest(BaseModel):
    instruction: str
    node_info: str = ""


class AutomateResponse(BaseModel):
    ok: bool
    gdscript_code: str


@router.post("/automate", response_model=AutomateResponse)
async def automate(body: AutomateRequest) -> AutomateResponse:
    try:
        raw_code = await generate_gdscript(body.instruction, body.node_info)
    except EnvironmentError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM error: {exc}") from exc

    gdscript_code = _strip_fences(raw_code)
    return AutomateResponse(ok=True, gdscript_code=gdscript_code)
