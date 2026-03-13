"""MCP tool handlers, input validation, and output formatting."""

import os
from pathlib import Path

from mutagen import File as MutagenFile

from supertone_tts_mcp.constants import (
    DEFAULT_OUTPUT_DIR,
    PITCH_SHIFT_MAX,
    PITCH_SHIFT_MIN,
    SPEED_MAX,
    SPEED_MIN,
    SUPPORTED_FORMATS,
    SUPPORTED_LANGUAGES,
    TEXT_MAX_LENGTH,
)
from supertone_tts_mcp.models import TTSResponse, VoiceInfo


# --- Input Validation ---


def validate_text(text: str) -> None:
    """Validate text input for TTS."""
    if not text:
        raise ValueError("Text must not be empty.")
    if len(text) > TEXT_MAX_LENGTH:
        raise ValueError(
            f"Text exceeds the maximum length of {TEXT_MAX_LENGTH} characters "
            f"(received: {len(text)}). Please shorten or split the text manually."
        )


def validate_language(language: str) -> None:
    """Validate language code."""
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f'Invalid language: "{language}". Supported languages: ko, en, ja.'
        )


def validate_output_format(fmt: str) -> None:
    """Validate output format."""
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(
            f'Invalid output format: "{fmt}". Supported formats: mp3, wav.'
        )


def validate_speed(speed: float) -> None:
    """Validate speed parameter."""
    if speed < SPEED_MIN or speed > SPEED_MAX:
        raise ValueError(
            f"Speed must be between {SPEED_MIN} and {SPEED_MAX} (received: {speed})."
        )


def validate_pitch_shift(pitch_shift: int) -> None:
    """Validate pitch shift parameter."""
    if pitch_shift < PITCH_SHIFT_MIN or pitch_shift > PITCH_SHIFT_MAX:
        raise ValueError(
            f"Pitch shift must be between {PITCH_SHIFT_MIN} and +{PITCH_SHIFT_MAX} "
            f"semitones (received: {pitch_shift})."
        )


# --- Configuration Resolution ---


def resolve_api_key() -> str:
    """Resolve the Supertone API key from environment."""
    key = os.environ.get("SUPERTONE_API_KEY", "")
    if not key:
        raise ValueError(
            "SUPERTONE_API_KEY environment variable is not set. "
            "Please configure it in your MCP client settings."
        )
    return key


def resolve_output_dir() -> str:
    """Resolve the output directory from environment or default."""
    output_dir = os.environ.get("SUPERTONE_OUTPUT_DIR", DEFAULT_OUTPUT_DIR)
    return str(Path(output_dir).expanduser().resolve())


def ensure_output_dir(path: str) -> None:
    """Create the output directory if it does not exist."""
    try:
        os.makedirs(path, exist_ok=True)
    except PermissionError:
        raise ValueError(
            f"Cannot write to output directory: {path}. "
            "Please check directory permissions or set SUPERTONE_OUTPUT_DIR "
            "to a writable location."
        )


# --- Output Formatting ---


def format_tts_response(response: TTSResponse) -> str:
    """Format a TTSResponse as plain text per UX spec."""
    return (
        f"Audio file saved: {response.file_path}\n"
        f"Duration: {response.duration_seconds} seconds\n"
        f"Voice: {response.voice_id}\n"
        f"Language: {response.language}\n"
        f"Format: {response.output_format}"
    )


def format_voice_list(
    voices: list[VoiceInfo], language_filter: str | None = None
) -> str:
    """Format a list of VoiceInfo as plain text per UX spec."""
    if not voices:
        if language_filter:
            return f"No voices found matching language: {language_filter}."
        return "No voices found."

    if language_filter:
        header = f"Found {len(voices)} voices matching language: {language_filter}"
    else:
        header = f"Found {len(voices)} voices:"

    entries = []
    for i, voice in enumerate(voices, 1):
        entry = (
            f"{i}. Name: {voice.name}\n"
            f"   Voice ID: {voice.voice_id}\n"
            f"   Languages: {', '.join(voice.supported_languages)}\n"
            f"   Styles: {', '.join(voice.supported_styles)}"
        )
        entries.append(entry)

    return header + "\n\n" + "\n\n".join(entries)


def calculate_duration(file_path: str) -> float:
    """Calculate the duration of an audio file in seconds using mutagen."""
    audio = MutagenFile(file_path)
    if audio is not None and audio.info is not None:
        return round(audio.info.length, 1)
    return 0.0
