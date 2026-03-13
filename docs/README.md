# Supertone TTS MCP Server

A Model Context Protocol (MCP) server that wraps the Supertone TTS API, enabling high-quality text-to-speech conversion directly from MCP-compatible clients like Claude Desktop and Cursor.

## Prerequisites

- **Python 3.11+**
- **uv** package manager ([install guide](https://docs.astral.sh/uv/))
- **Supertone API Key** ([get one here](https://supertoneapi.com))

## Setup

### Install Dependencies

```bash
uv sync
```

### Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Set your Supertone API key:

```
SUPERTONE_API_KEY=your-api-key-here
SUPERTONE_OUTPUT_DIR=~/supertone-tts-output/   # optional
```

### Run the MCP Server

```bash
uv run supertone-tts-mcp
```

Or via PyPI (after publish):

```bash
uvx supertone-tts-mcp
pip install supertone-tts-mcp
```

### MCP Client Configuration

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "supertone-tts": {
      "command": "uvx",
      "args": ["supertone-tts-mcp"],
      "env": {
        "SUPERTONE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Test

```bash
uv run pytest -q
uv run pytest --cov=src --cov-report=term-missing
```

## Tools

| Tool | Description |
|------|-------------|
| `text_to_speech` | Convert text to speech (max 300 chars). Returns file path + duration. |
| `list_voices` | List available voices with optional language filter. |

### Supported Languages

`ko` (Korean, default), `en` (English), `ja` (Japanese)

### Parameters (text_to_speech)

| Parameter | Type | Default | Range |
|-----------|------|---------|-------|
| text | string | (required) | 1-300 chars |
| voice_id | string | default Korean voice | -- |
| language | string | "ko" | ko, en, ja |
| output_format | string | "mp3" | mp3, wav |
| speed | number | 1.0 | 0.5-2.0 |
| pitch_shift | number | 0 | -12 to +12 |
| style | string | voice default | varies by voice |

## Architecture

See `docs/architecture.md` for full architecture documentation.

**Tech Stack:** Python 3.11+, MCP Python SDK, httpx (async), mutagen, uv

**Modules:**
- `server.py` — MCP entry point, tool registration
- `tools.py` — Input validation, output formatting, tool handlers
- `supertone_client.py` — Supertone API HTTP wrapper
