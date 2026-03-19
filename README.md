# vibe-plugin

A Godot 4 editor plugin for AI-assisted game development. Right-click assets and nodes in the editor to generate images, modify existing ones, or automate scene tree operations using natural language.

## Features

- **Generate Asset** -- right-click any folder in the FileSystem dock, describe what you want, get a PNG back
- **Modify Asset** -- right-click an existing image, describe the change, file gets updated in place
- **Automate** -- right-click any node in the SceneTree dock, describe what to do, LLM writes and executes the GDScript

## Setup

### Backend

```bash
cd vibe_backend
pip install -r requirements.txt
cp .env.example .env  # fill in your API keys
uvicorn main:app --port 8765
```

Keys needed in `.env`:
- `PIXELLAB_API_KEY` -- from [pixellab.ai](https://www.pixellab.ai/pixellab-api)
- One of: `OPENAI_API_KEY`, `MISTRAL_API_KEY`, or `GEMINI_API_KEY`

Set `LLM_PROVIDER` to override auto-detection (`openai`, `mistral`, or `gemini`).

### Plugin

Copy `godot_addon/addons/vibe_plugin` into your Godot project under `addons/`, then enable it in **Project > Project Settings > Plugins**.

The backend needs to be running on `localhost:8765` before using any of the plugin features.

## Test Project

`vibe_test_project/` is a minimal Godot 4.4 project with the plugin pre-enabled and an `assets/` folder ready for generated images. Open it in Godot to try things out.

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
