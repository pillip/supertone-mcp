"""Tests for domain types, constants, and exceptions (ISSUE-002)."""

import dataclasses
import re

import pytest

from supertone_tts_mcp.constants import (
    DEFAULT_FORMAT,
    DEFAULT_LANGUAGE,
    DEFAULT_PITCH_SHIFT,
    DEFAULT_SPEED,
    DEFAULT_VOICE_ID,
    HTTP_TIMEOUT,
    PITCH_SHIFT_MAX,
    PITCH_SHIFT_MIN,
    SPEED_MAX,
    SPEED_MIN,
    SUPPORTED_FORMATS,
    SUPPORTED_LANGUAGES,
    SUPERTONE_BASE_URL,
    TEXT_MAX_LENGTH,
)
from supertone_tts_mcp.exceptions import (
    SupertoneAPIError,
    SupertoneAuthError,
    SupertoneConnectionError,
    SupertoneError,
    SupertoneRateLimitError,
    SupertoneServerError,
)
from supertone_tts_mcp.models import (
    TTSRequest,
    TTSResponse,
    VoiceInfo,
    generate_output_path,
)


class TestTTSRequest:
    def test_construction_with_valid_fields(self):
        req = TTSRequest(
            text="hi",
            voice_id="v1",
            language="ko",
            output_format="mp3",
            speed=1.0,
            pitch_shift=0,
            style=None,
        )
        assert req.text == "hi"
        assert req.voice_id == "v1"
        assert req.language == "ko"
        assert req.output_format == "mp3"
        assert req.speed == 1.0
        assert req.pitch_shift == 0
        assert req.style is None

    def test_frozen(self):
        req = TTSRequest(
            text="hi",
            voice_id="v1",
            language="ko",
            output_format="mp3",
            speed=1.0,
            pitch_shift=0,
            style=None,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            req.text = "changed"  # type: ignore[misc]

    def test_construction_with_style(self):
        req = TTSRequest(
            text="hello",
            voice_id="v1",
            language="en",
            output_format="wav",
            speed=1.5,
            pitch_shift=-3,
            style="happy",
        )
        assert req.style == "happy"


class TestTTSResponse:
    def test_construction(self):
        resp = TTSResponse(
            file_path="/tmp/test.mp3",
            duration_seconds=2.3,
            voice_id="v1",
            language="en",
            output_format="mp3",
        )
        assert resp.file_path == "/tmp/test.mp3"
        assert resp.duration_seconds == 2.3

    def test_frozen(self):
        resp = TTSResponse(
            file_path="/tmp/test.mp3",
            duration_seconds=2.3,
            voice_id="v1",
            language="en",
            output_format="mp3",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            resp.file_path = "/other"  # type: ignore[misc]


class TestVoiceInfo:
    def test_construction(self):
        voice = VoiceInfo(
            voice_id="sujin-01",
            name="Sujin",
            supported_languages=["ko", "en"],
            supported_styles=["neutral", "happy"],
        )
        assert voice.voice_id == "sujin-01"
        assert voice.name == "Sujin"
        assert voice.supported_languages == ["ko", "en"]
        assert voice.supported_styles == ["neutral", "happy"]


class TestConstants:
    def test_text_max_length(self):
        assert TEXT_MAX_LENGTH == 300

    def test_speed_range(self):
        assert SPEED_MIN == 0.5
        assert SPEED_MAX == 2.0

    def test_pitch_shift_range(self):
        assert PITCH_SHIFT_MIN == -12
        assert PITCH_SHIFT_MAX == 12

    def test_supported_languages(self):
        assert SUPPORTED_LANGUAGES == ["ko", "en", "ja"]

    def test_supported_formats(self):
        assert SUPPORTED_FORMATS == ["mp3", "wav"]

    def test_defaults(self):
        assert DEFAULT_LANGUAGE == "ko"
        assert DEFAULT_FORMAT == "mp3"
        assert DEFAULT_SPEED == 1.0
        assert DEFAULT_PITCH_SHIFT == 0
        assert DEFAULT_VOICE_ID == "TBD"

    def test_http_timeout(self):
        assert HTTP_TIMEOUT == 30.0

    def test_base_url(self):
        assert SUPERTONE_BASE_URL == "https://api.supertoneapi.com"


class TestGenerateOutputPath:
    def test_pattern(self):
        path = generate_output_path("/tmp/out", "mp3")
        # On macOS /tmp resolves to /private/tmp
        pattern = r".*/out/\d{4}-\d{2}-\d{2}_[0-9a-f]{8}\.mp3"
        assert re.match(pattern, str(path))

    def test_wav_format(self):
        path = generate_output_path("/tmp/out", "wav")
        assert str(path).endswith(".wav")

    def test_uniqueness(self):
        path1 = generate_output_path("/tmp/out", "mp3")
        path2 = generate_output_path("/tmp/out", "mp3")
        assert path1 != path2

    def test_expands_home(self):
        path = generate_output_path("~/output", "mp3")
        assert "~" not in str(path)
        assert path.is_absolute()


class TestExceptions:
    def test_server_error_stores_status_code(self):
        err = SupertoneServerError(502)
        assert err.status_code == 502
        assert "502" in str(err)

    def test_api_error_stores_status_code_and_message(self):
        err = SupertoneAPIError(400, "bad request")
        assert err.status_code == 400
        assert err.message == "bad request"
        assert "400" in str(err)
        assert "bad request" in str(err)

    def test_auth_error_is_supertone_error(self):
        assert isinstance(SupertoneAuthError(), SupertoneError)

    def test_rate_limit_error_is_supertone_error(self):
        assert isinstance(SupertoneRateLimitError(), SupertoneError)

    def test_server_error_is_supertone_error(self):
        assert isinstance(SupertoneServerError(500), SupertoneError)

    def test_api_error_is_supertone_error(self):
        assert isinstance(SupertoneAPIError(400, "test"), SupertoneError)

    def test_connection_error_is_supertone_error(self):
        assert isinstance(SupertoneConnectionError(), SupertoneError)
