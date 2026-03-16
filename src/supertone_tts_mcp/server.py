"""MCP server entry point for Supertone TTS."""

from mcp.server.fastmcp import FastMCP

from supertone_tts_mcp import tools

mcp = FastMCP("supertone-tts")


@mcp.tool(
    name="text_to_speech",
    description=(
        "Convert text to speech using Supertone TTS API. "
        "Supports 23 languages including Korean, English, and Japanese. "
        "Long text is automatically split into chunks and processed. "
        "Output mode is controlled by SUPERTONE_MCP_OUTPUT_MODE env var: "
        '"files" (default) saves to disk and returns file path, '
        '"resources" returns audio data directly (no disk write), '
        '"both" saves to disk and returns audio data with file path. '
        "Set SUPERTONE_MCP_AUTOPLAY=false to disable auto-play. "
        "Set SUPERTONE_MCP_VOICE_ID to use a default voice without calling list_voices."
    ),
)
async def text_to_speech(
    text: str,
    voice_id: str | None = None,
    language: str | None = None,
    output_format: str | None = None,
    model: str | None = None,
    speed: float | None = None,
    pitch_shift: int | None = None,
    style: str | None = None,
) -> str | list:
    """Convert text to speech using Supertone TTS API.

    Args:
        text: Text to convert to speech. Required.
            Long text is automatically split into chunks.
        voice_id: Voice identifier. Use list_voices to see available options.
            If omitted, a default Korean voice is used.
        language: Language code: "ko" (Korean, default), "en" (English),
            "ja" (Japanese), and 20+ more languages.
        output_format: Audio format: "mp3" (default) or "wav".
        model: TTS model: "sona_speech_1" (default),
            "sona_speech_2", "sona_speech_2_flash",
            "sona_speech_2t", "supertonic_api_1".
        speed: Playback speed multiplier. Range: 0.5 to 2.0. Default: 1.0.
        pitch_shift: Pitch adjustment in semitones. Range: -24 to +24.
            Default: 0.
        style: Emotion style (e.g., "neutral", "happy"). Available styles
            vary by voice -- use list_voices to check.
    """
    return await tools.text_to_speech(
        text=text,
        voice_id=voice_id,
        language=language,
        output_format=output_format,
        model=model,
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
        language: Filter voices by language code (e.g., "ko", "en", "ja").
            If omitted, all voices are returned.
    """
    return await tools.list_voices(language=language)


def main() -> None:
    """Start the Supertone TTS MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
