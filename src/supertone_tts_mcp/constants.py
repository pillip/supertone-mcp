"""Constants and literal types for the Supertone TTS MCP server."""

from typing import Literal

Language = Literal["ko", "en", "ja"]
OutputFormat = Literal["mp3", "wav"]

SUPPORTED_LANGUAGES: list[str] = ["ko", "en", "ja"]
SUPPORTED_FORMATS: list[str] = ["mp3", "wav"]

SPEED_MIN: float = 0.5
SPEED_MAX: float = 2.0
PITCH_SHIFT_MIN: int = -12
PITCH_SHIFT_MAX: int = 12
TEXT_MAX_LENGTH: int = 300

DEFAULT_LANGUAGE: str = "ko"
DEFAULT_FORMAT: str = "mp3"
DEFAULT_SPEED: float = 1.0
DEFAULT_PITCH_SHIFT: int = 0
DEFAULT_VOICE_ID: str = "TBD"

HTTP_TIMEOUT: float = 30.0
SUPERTONE_BASE_URL: str = "https://api.supertoneapi.com"
DEFAULT_OUTPUT_DIR: str = "~/supertone-tts-output/"
