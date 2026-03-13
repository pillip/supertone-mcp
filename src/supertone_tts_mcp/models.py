"""Domain types and data models for the Supertone TTS MCP server."""

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import NotRequired, TypedDict
from uuid import uuid4


@dataclass(frozen=True)
class TTSRequest:
    """Validated TTS request parameters. Immutable after construction."""

    text: str
    voice_id: str
    language: str
    output_format: str
    model: str
    speed: float
    pitch_shift: int
    style: str | None


@dataclass(frozen=True)
class TTSResponse:
    """Result of a successful TTS synthesis."""

    file_path: str
    duration_seconds: float
    voice_id: str
    language: str
    output_format: str


@dataclass(frozen=True)
class VoiceInfo:
    """A single voice from the Supertone voice catalog."""

    voice_id: str
    name: str
    supported_languages: list[str]
    supported_styles: list[str]


@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration resolved from environment."""

    api_key: str
    output_dir: str
    base_url: str


class VoiceSettingsBody(TypedDict, total=False):
    """voice_settings object nested in the synthesize request."""

    pitch_shift: int
    speed: float


class SynthesizeRequestBody(TypedDict, total=False):
    """Request body for the Supertone synthesize API."""

    text: str
    language: str
    output_format: str
    model: str
    style: str
    voice_settings: VoiceSettingsBody


class VoiceDict(TypedDict):
    """Voice entry from the Supertone API response (mapped from raw API)."""

    voice_id: str
    name: str
    supported_languages: list[str]
    supported_styles: list[str]


def generate_output_path(output_dir: str, output_format: str) -> Path:
    """Generate a unique output file path for an audio file.

    Returns a Path like: /absolute/path/2026-03-13_a1b2c3d4.mp3
    """
    today = date.today().isoformat()
    unique_id = uuid4().hex[:8]
    filename = f"{today}_{unique_id}.{output_format}"
    return Path(output_dir).expanduser().resolve() / filename
