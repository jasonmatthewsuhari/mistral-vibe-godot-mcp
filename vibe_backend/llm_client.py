import os
import httpx

SYSTEM_PROMPT = """You are a Godot 4 editor automation assistant. Write GDScript that runs in the editor.
Rules:
1. Produce a single class extending EditorScript
2. Must have: func run() -> void
3. Access editor via get_editor_interface()
4. Get scene root: get_editor_interface().get_edited_scene_root()
5. After adding nodes: set node.owner = scene_root
6. After file changes: get_editor_interface().get_resource_filesystem().scan()
7. Save scene: get_editor_interface().save_scene()
8. Output ONLY raw GDScript -- no markdown fences, no explanation"""

# OpenAI-compatible providers
_OPENAI_COMPAT = {
    "openai":  ("https://api.openai.com/v1/chat/completions",  "OPENAI_API_KEY",  "gpt-4o"),
    "mistral": ("https://api.mistral.ai/v1/chat/completions",  "MISTRAL_API_KEY", "mistral-large-latest"),
}

_GEMINI_URL_TMPL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)
_GEMINI_MODEL = "gemini-2.0-flash"


def _detect_provider() -> str:
    preferred = os.getenv("LLM_PROVIDER", "").lower()
    if preferred in (*_OPENAI_COMPAT, "gemini"):
        return preferred
    # Auto-detect: first key found wins
    for name, (_, env_var, _) in _OPENAI_COMPAT.items():
        if os.getenv(env_var):
            return name
    if os.getenv("GEMINI_API_KEY"):
        return "gemini"
    raise EnvironmentError(
        "No LLM API key found. Set one of: OPENAI_API_KEY, MISTRAL_API_KEY, GEMINI_API_KEY. "
        "Or set LLM_PROVIDER explicitly."
    )


async def _call_openai_compat(provider: str, user_message: str) -> str:
    url, env_var, model = _OPENAI_COMPAT[provider]
    api_key = os.getenv(env_var)
    if not api_key:
        raise EnvironmentError(f"{env_var} is not set")
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
            },
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


async def _call_gemini(user_message: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY is not set")
    url = _GEMINI_URL_TMPL.format(model=_GEMINI_MODEL)
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            url,
            params={"key": api_key},
            json={
                "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": [{"role": "user", "parts": [{"text": user_message}]}],
            },
        )
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]


async def generate_gdscript(user_instruction: str, node_info: str) -> str:
    user_message = user_instruction
    if node_info:
        user_message = f"Node context:\n{node_info}\n\nInstruction: {user_instruction}"

    provider = _detect_provider()

    if provider in _OPENAI_COMPAT:
        return await _call_openai_compat(provider, user_message)
    if provider == "gemini":
        return await _call_gemini(user_message)

    raise EnvironmentError(f"Unknown LLM provider: {provider!r}")
