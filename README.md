# vibe-plugin


https://github.com/user-attachments/assets/f7009c71-5870-4471-abb2-d94f4b38736d


A Godot 4 editor plugin for AI-assisted game development. Right-click assets and nodes in the editor to generate images, modify existing ones, or automate scene tree operations using natural language.

## Features

- **Generate Asset** -- right-click any folder in the FileSystem dock, describe what you want, get a PNG back
- **Modify Asset** -- right-click an existing image, describe the change, file gets updated in place
- **Automate** -- right-click any node in the SceneTree dock, describe what to do, LLM writes and executes the GDScript

## Setup

### 1. Install Godot

Download **Godot 4.3+** from [godotengine.org/download](https://godotengine.org/download/). The standard (non-Mono) build is all you need.

### 2. Start the backend

```bash
cd vibe_backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # then fill in your keys (see below)
uvicorn main:app --port 8765
```

Keys in `.env`:

| Variable | Required | Description |
|---|---|---|
| `PIXELLAB_API_KEY` | Yes | From [pixellab.ai](https://www.pixellab.ai/pixellab-api) |
| `OPENAI_API_KEY` | One of these | OpenAI |
| `MISTRAL_API_KEY` | One of these | Mistral |
| `GEMINI_API_KEY` | One of these | Google Gemini |
| `LLM_PROVIDER` | No | Force a provider: `openai`, `mistral`, or `gemini` (auto-detected otherwise) |
| `OPENAI_API_ENDPOINT` | No | Override the OpenAI endpoint URL for any OpenAI-compatible server (e.g. Ollama, LM Studio) |

### 3. Install the plugin

1. Copy `godot_addon/addons/vibe_plugin` into your Godot project at `addons/vibe_plugin`.
2. In Godot, open **Project > Project Settings > Plugins** and enable **Vibe Plugin**.

The backend must be running on `localhost:8765` before using any plugin features.

### Try it with the test project

`vibe_test_project/` is a minimal Godot 4.4 project with the plugin pre-enabled and an `assets/` folder ready for generated images. Open it in Godot to experiment without setting up your own project.

## Architecture

```
Godot Editor (GDScript plugin)
  -- HTTP POST --> FastAPI backend (localhost:8765)
                    -- PixelLab API  (generate/modify images)
                    -- LLM API       (generate GDScript for automation)
```

## Requirements

- Python 3.11+
- Godot 4.3+
- Pillow, httpx, fastapi, uvicorn
