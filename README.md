# supertone-tts-mcp

MCP server for [Supertone](https://supertone.ai) TTS API. Convert text to speech with high-quality Korean, English, and Japanese voices directly from Claude Desktop, Cursor, or any MCP-compatible client.

## Features

- **text_to_speech** -- Convert text (up to 300 characters) to audio files (MP3/WAV)
- **list_voices** -- Browse available voices with language and style filtering
- Speed control (0.5x - 2.0x), pitch adjustment (-12 to +12 semitones), emotion styles
- Supports Korean, English, and Japanese

## Installation

```bash
# Using uvx (recommended)
uvx supertone-tts-mcp

# Using pip
pip install supertone-tts-mcp
```

## Configuration

### Claude Desktop

Add to your Claude Desktop configuration file (`claude_desktop_config.json`):

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

### Cursor

Add to your Cursor MCP settings:

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

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SUPERTONE_API_KEY` | Yes | -- | Your Supertone API key |
| `SUPERTONE_OUTPUT_DIR` | No | `~/supertone-tts-output/` | Directory where audio files are saved |

## Usage Examples

Once configured, you can use natural language in your MCP client:

**Generate speech:**
> "Read this aloud: Hello, how are you today?"

The server will generate an audio file and return:
```
Audio file saved: /Users/you/supertone-tts-output/2026-03-13_a1b2c3d4.mp3
Duration: 2.3 seconds
Voice: sujin-01
Language: en
Format: mp3
```

**List available voices:**
> "What Korean voices are available?"

**Adjust parameters:**
> "Say 'good morning' in Japanese, slower and with a happy tone"

## Parameters

### text_to_speech

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `text` | string | Yes | -- | Text to convert (max 300 characters) |
| `voice_id` | string | No | default voice | Voice identifier (use `list_voices` to browse) |
| `language` | string | No | `ko` | Language: `ko`, `en`, or `ja` |
| `output_format` | string | No | `mp3` | Format: `mp3` or `wav` |
| `speed` | float | No | `1.0` | Speed: 0.5 to 2.0 |
| `pitch_shift` | int | No | `0` | Pitch: -12 to +12 semitones |
| `style` | string | No | -- | Emotion style (e.g., `neutral`, `happy`) |

### list_voices

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `language` | string | No | -- | Filter by language: `ko`, `en`, or `ja` |

## Development

```bash
# Clone and install
git clone https://github.com/pillip/supertone-mcp.git
cd supertone-mcp
uv sync

# Run tests
uv run pytest -q

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing
```

## License

MIT
