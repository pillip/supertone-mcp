"""MCP server entry point for Supertone TTS."""

from mcp.server.fastmcp import FastMCP

from supertone_tts_mcp import tools

mcp = FastMCP("supertone-tts")


@mcp.tool(
    name="text_to_speech",
    description=(
        "Convert text to speech using Supertone TTS API. "
        "Saves the audio file locally and returns the file path and duration. "
        "Supports Korean, English, and Japanese. "
        "Maximum 300 characters per call."
    ),
)
async def text_to_speech(
    text: str,
    voice_id: str | None = None,
    language: str | None = None,
    output_format: str | None = None,
    speed: float | None = None,
    pitch_shift: int | None = None,
    style: str | None = None,
) -> str:
    """Convert text to speech using Supertone TTS API.

    Args:
        text: Text to convert to speech. Required. Maximum 300 characters.
        voice_id: Voice identifier. Use list_voices to see available options.
            If omitted, a default Korean voice is used.
        language: Language code: "ko" (Korean, default), "en" (English),
            or "ja" (Japanese).
        output_format: Audio format: "mp3" (default) or "wav".
        speed: Playback speed multiplier. Range: 0.5 to 2.0. Default: 1.0.
        pitch_shift: Pitch adjustment in semitones. Range: -12 to +12.
            Default: 0.
        style: Emotion style (e.g., "neutral", "happy"). Available styles
            vary by voice -- use list_voices to check.
    """
    return await tools.text_to_speech(
        text=text,
        voice_id=voice_id,
        language=language,
        output_format=output_format,
        speed=speed,
        pitch_shift=pitch_shift,
        style=style,
    )


@mcp.tool(
    name="list_voices",
    description=(
        "List available Supertone TTS voices. "
        "Returns voice ID, name, supported languages, and supported emotion "
        "styles for each voice. Optionally filter by language."
    ),
)
async def list_voices(language: str | None = None) -> str:
    """List available Supertone TTS voices.

    Args:
        language: Filter voices by language code: "ko", "en", or "ja".
            If omitted, all voices are returned.
    """
    return await tools.list_voices(language=language)


def main() -> None:
    """Start the Supertone TTS MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
