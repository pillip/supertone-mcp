"""MCP server entry point for Supertone TTS."""

from mcp.server.fastmcp import FastMCP

from supertone_tts_mcp import tools

mcp = FastMCP("supertone-tts")


@mcp.tool(
    name="text_to_speech",
    description=(
        "Generate natural-sounding speech audio from text. "
        "Use this when the user wants to: "
        "hear text read aloud, create narration or voiceover, "
        "generate voice audio, preview how text sounds when spoken, "
        "or convert any writing into spoken audio. "
        "Supports 23 languages including Korean, English, and Japanese. "
        "Audio is automatically played back on macOS. "
        "A default voice is already configured -- just call this tool directly. "
        "Only call list_voices if the user explicitly asks to change or browse voices."
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
    """Generate natural-sounding speech audio from text.

    Args:
        text: The text to speak aloud. Required.
            Can be a sentence, paragraph, or any text content.
            Long text is automatically split and processed.
        voice_id: Voice to use (e.g., "sujin-01", "minho-01").
            Run list_voices to browse available voices.
            If omitted, a default Korean voice is used.
        language: Language code for the speech output.
            "ko" (Korean, default), "en" (English), "ja" (Japanese),
            and 20+ more. Must match the text language for best results.
        output_format: Audio file format: "mp3" (default) or "wav".
            Use "wav" for higher quality, "mp3" for smaller files.
        model: TTS model: "sona_speech_1" (default, streaming),
            "sona_speech_2", "sona_speech_2_flash" (fastest),
            "sona_speech_2t", "supertonic_api_1".
        speed: Speech speed. 0.5 (slow) to 2.0 (fast). Default: 1.0.
        pitch_shift: Voice pitch adjustment in semitones.
            -24 (deeper) to +24 (higher). Default: 0.
        style: Emotion or tone of the voice (e.g., "neutral", "happy",
            "sad", "angry"). Available styles vary by voice --
            call list_voices to see what each voice supports.
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
        "Browse available voices for text-to-speech. "
        "Use this before text_to_speech to find the right voice. "
        "Shows each voice's name, ID, supported languages, and emotion styles "
        "(e.g., neutral, happy, sad, angry). "
        "Use this when the user asks: what voices are available, "
        "find a voice for a specific language, or pick a voice with a certain style."
    ),
)
async def list_voices(language: str | None = None) -> str:
    """Browse available voices for text-to-speech.

    Args:
        language: Filter by language code to narrow results
            (e.g., "ko" for Korean voices, "en" for English, "ja" for Japanese).
            If omitted, all voices across all languages are returned.
    """
    return await tools.list_voices(language=language)


def main() -> None:
    """Start the Supertone TTS MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
