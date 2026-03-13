"""MCP tool handlers, input validation, and output formatting."""

import base64
import os
from pathlib import Path

from mcp.types import AudioContent, TextContent
from mutagen import File as MutagenFile

from supertone_tts_mcp.constants import (
    DEFAULT_FORMAT,
    DEFAULT_LANGUAGE,
    DEFAULT_MODEL,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_OUTPUT_MODE,
    DEFAULT_PITCH_SHIFT,
    DEFAULT_SPEED,
    DEFAULT_VOICE_ID,
    OUTPUT_MODE_BOTH,
    OUTPUT_MODE_FILES,
    OUTPUT_MODE_RESOURCES,
    PITCH_SHIFT_MAX,
    PITCH_SHIFT_MIN,
    SPEED_MAX,
    SPEED_MIN,
    SUPPORTED_FORMATS,
    SUPPORTED_LANGUAGES,
    SUPPORTED_MODELS,
    VALID_OUTPUT_MODES,
)
from supertone_tts_mcp.exceptions import (
    SupertoneAuthError,
    SupertoneConnectionError,
    SupertoneRateLimitError,
    SupertoneServerError,
)
from supertone_tts_mcp.models import TTSResponse, VoiceInfo, generate_output_path
from supertone_tts_mcp.supertone_client import SupertoneClient


# --- Input Validation ---


def validate_text(text: str) -> None:
    """Validate text input for TTS."""
    if not text:
        raise ValueError("Text must not be empty.")


def validate_language(language: str) -> None:
    """Validate language code."""
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f'Invalid language: "{language}". '
            f"Supported languages: {', '.join(SUPPORTED_LANGUAGES)}."
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


def validate_model(model: str) -> None:
    """Validate model parameter."""
    if model not in SUPPORTED_MODELS:
        raise ValueError(
            f'Invalid model: "{model}". '
            f"Supported models: {', '.join(SUPPORTED_MODELS)}."
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


def resolve_output_mode() -> str:
    """Resolve the output mode from environment or default.

    Valid modes: "files", "resources", "both".
    """
    mode = os.environ.get("SUPERTONE_MCP_OUTPUT_MODE", DEFAULT_OUTPUT_MODE).lower()
    if mode not in VALID_OUTPUT_MODES:
        raise ValueError(
            f'Invalid output mode: "{mode}". '
            f"Valid modes: {', '.join(VALID_OUTPUT_MODES)}."
        )
    return mode


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


def format_tts_metadata(
    duration: float,
    voice_id: str,
    language: str,
    output_format: str,
    file_path: str | None = None,
) -> str:
    """Format TTS metadata as concise text for resources/both modes."""
    parts = [
        f"Duration: {duration}s",
        f"Voice: {voice_id}",
        f"Language: {language}",
        f"Format: {output_format}",
    ]
    if file_path:
        parts.insert(0, f"Saved: {file_path}")
    return " | ".join(parts)


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


# --- Tool Handlers ---


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

    Returns a plain-text response string or a list of Content objects
    depending on the output mode (SUPERTONE_MCP_OUTPUT_MODE env var).
    """
    # Apply defaults
    voice_id = voice_id or DEFAULT_VOICE_ID
    language = language or DEFAULT_LANGUAGE
    output_format = output_format or DEFAULT_FORMAT
    model = model or DEFAULT_MODEL
    speed = speed if speed is not None else DEFAULT_SPEED
    pitch_shift = pitch_shift if pitch_shift is not None else DEFAULT_PITCH_SHIFT

    # Validate inputs
    try:
        api_key = resolve_api_key()
        output_mode = resolve_output_mode()
        validate_text(text)
        validate_language(language)
        validate_output_format(output_format)
        validate_model(model)
        validate_speed(speed)
        validate_pitch_shift(pitch_shift)
    except ValueError as e:
        return str(e)

    # Resolve output directory (only needed for files/both modes)
    needs_file = output_mode in (OUTPUT_MODE_FILES, OUTPUT_MODE_BOTH)
    if needs_file:
        try:
            output_dir = resolve_output_dir()
            ensure_output_dir(output_dir)
        except ValueError as e:
            return str(e)

    # Call API
    client = SupertoneClient(api_key=api_key)
    try:
        audio_bytes, _content_type, api_duration = await client.synthesize(
            voice_id=voice_id,
            text=text,
            language=language,
            output_format=output_format,
            model=model,
            speed=speed,
            pitch_shift=pitch_shift,
            style=style,
        )
    except SupertoneAuthError:
        return "Authentication failed. Please verify your SUPERTONE_API_KEY."
    except SupertoneRateLimitError:
        return "Rate limit exceeded. Please wait and try again."
    except SupertoneServerError as e:
        return f"Supertone API server error ({e.status_code}). Please try again later."
    except SupertoneConnectionError:
        return "Failed to connect to Supertone API. Please check your network connection."
    finally:
        await client.aclose()

    # Save file (files/both modes only)
    file_path_str: str | None = None
    if needs_file:
        output_path = generate_output_path(output_dir, output_format)
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(audio_bytes)
        except PermissionError:
            return (
                f"Cannot write to output directory: {output_path.parent}. "
                "Please check directory permissions or set SUPERTONE_OUTPUT_DIR "
                "to a writable location."
            )
        except OSError:
            return "Cannot write audio file. Please check available disk space."
        file_path_str = str(output_path)

    # Get duration: prefer API header, fall back to mutagen
    if api_duration is not None:
        duration = round(api_duration, 1)
    elif file_path_str:
        duration = calculate_duration(file_path_str)
    else:
        duration = 0.0

    # Format response based on output mode
    if output_mode == OUTPUT_MODE_FILES:
        response = TTSResponse(
            file_path=file_path_str,
            duration_seconds=duration,
            voice_id=voice_id,
            language=language,
            output_format=output_format,
        )
        return format_tts_response(response)

    # resources or both mode: return AudioContent + TextContent
    mime_type = "audio/mpeg" if output_format == "mp3" else "audio/wav"
    audio_base64 = base64.b64encode(audio_bytes).decode()
    meta_text = format_tts_metadata(
        duration=duration,
        voice_id=voice_id,
        language=language,
        output_format=output_format,
        file_path=file_path_str,
    )
    return [
        AudioContent(type="audio", data=audio_base64, mimeType=mime_type),
        TextContent(type="text", text=meta_text),
    ]


async def list_voices(language: str | None = None) -> str:
    """List available Supertone TTS voices.

    Returns a plain-text response string (never raises to the caller).
    """
    # Validate language filter
    if language is not None:
        try:
            validate_language(language)
        except ValueError as e:
            return str(e)

    # Resolve API key
    try:
        api_key = resolve_api_key()
    except ValueError as e:
        return str(e)

    # Call API
    client = SupertoneClient(api_key=api_key)
    try:
        voice_dicts = await client.get_voices()
    except SupertoneAuthError:
        return "Authentication failed. Please verify your SUPERTONE_API_KEY."
    except SupertoneRateLimitError:
        return "Rate limit exceeded. Please wait and try again."
    except SupertoneServerError as e:
        return f"Supertone API server error ({e.status_code}). Please try again later."
    except SupertoneConnectionError:
        return "Failed to connect to Supertone API. Please check your network connection."
    finally:
        await client.aclose()

    # Convert to VoiceInfo objects
    voices = [
        VoiceInfo(
            voice_id=v["voice_id"],
            name=v["name"],
            supported_languages=v["supported_languages"],
            supported_styles=v["supported_styles"],
        )
        for v in voice_dicts
    ]

    # Filter by language
    if language is not None:
        voices = [v for v in voices if language in v.supported_languages]

    return format_voice_list(voices, language_filter=language)
