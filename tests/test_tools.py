"""Tests for input validation, output formatting, and tool handlers."""

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from supertone_tts_mcp.exceptions import (
    SupertoneAuthError,
    SupertoneConnectionError,
    SupertoneRateLimitError,
    SupertoneServerError,
)
from supertone_tts_mcp.models import TTSResponse, VoiceInfo
from mcp.types import AudioContent, TextContent

from supertone_tts_mcp.tools import (
    calculate_duration,
    ensure_output_dir,
    format_tts_metadata,
    format_tts_response,
    format_voice_list,
    list_voices,
    resolve_api_key,
    resolve_output_dir,
    resolve_output_mode,
    text_to_speech,
    validate_language,
    validate_model,
    validate_output_format,
    validate_pitch_shift,
    validate_speed,
    validate_text,
)


class TestValidateText:
    def test_empty_string(self):
        with pytest.raises(ValueError, match="Text must not be empty."):
            validate_text("")

    def test_long_text_passes(self):
        """SDK handles chunking, so long text should pass validation."""
        validate_text("a" * 1000)

    def test_1_char_passes(self):
        validate_text("a")


class TestValidateLanguage:
    @pytest.mark.parametrize("lang", ["ko", "en", "ja", "de", "fr", "es"])
    def test_valid_languages(self, lang):
        validate_language(lang)

    def test_invalid_language(self):
        with pytest.raises(ValueError, match=r'Invalid language: "zz"'):
            validate_language("zz")


class TestValidateOutputFormat:
    @pytest.mark.parametrize("fmt", ["mp3", "wav"])
    def test_valid_formats(self, fmt):
        validate_output_format(fmt)

    def test_invalid_format(self):
        with pytest.raises(
            ValueError,
            match=r'Invalid output format: "ogg"\. Supported formats: mp3, wav\.',
        ):
            validate_output_format("ogg")


class TestValidateSpeed:
    @pytest.mark.parametrize("speed", [0.5, 1.0, 2.0])
    def test_valid_speeds(self, speed):
        validate_speed(speed)

    def test_too_low(self):
        with pytest.raises(
            ValueError,
            match=r"Speed must be between 0\.5 and 2\.0 \(received: 0\.4\)\.",
        ):
            validate_speed(0.4)

    def test_too_high(self):
        with pytest.raises(
            ValueError,
            match=r"Speed must be between 0\.5 and 2\.0 \(received: 2\.1\)\.",
        ):
            validate_speed(2.1)


class TestValidatePitchShift:
    @pytest.mark.parametrize("pitch", [-24, 0, 24])
    def test_valid_pitches(self, pitch):
        validate_pitch_shift(pitch)

    def test_too_low(self):
        with pytest.raises(
            ValueError,
            match=r"Pitch shift must be between -24 and \+24 semitones \(received: -25\)\.",
        ):
            validate_pitch_shift(-25)

    def test_too_high(self):
        with pytest.raises(
            ValueError,
            match=r"Pitch shift must be between -24 and \+24 semitones \(received: 25\)\.",
        ):
            validate_pitch_shift(25)


class TestValidateModel:
    @pytest.mark.parametrize("model", ["sona_speech_1", "sona_speech_2_flash"])
    def test_valid_models(self, model):
        validate_model(model)

    def test_invalid_model(self):
        with pytest.raises(ValueError, match=r'Invalid model: "bad_model"'):
            validate_model("bad_model")


class TestResolveApiKey:
    def test_returns_key_when_set(self):
        with patch.dict(os.environ, {"SUPERTONE_API_KEY": "test-key-123"}):
            assert resolve_api_key() == "test-key-123"

    def test_raises_when_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="SUPERTONE_API_KEY environment variable is not set"):
                resolve_api_key()

    def test_raises_when_empty(self):
        with patch.dict(os.environ, {"SUPERTONE_API_KEY": ""}):
            with pytest.raises(ValueError, match="SUPERTONE_API_KEY environment variable is not set"):
                resolve_api_key()


class TestResolveOutputDir:
    def test_returns_default_when_not_set(self):
        with patch.dict(os.environ, {}, clear=True):
            result = resolve_output_dir()
            assert "~" not in result
            assert os.path.isabs(result)
            assert "supertone-tts-output" in result

    def test_returns_custom_when_set(self):
        with patch.dict(os.environ, {"SUPERTONE_OUTPUT_DIR": "/custom/dir"}):
            result = resolve_output_dir()
            assert "custom" in result


class TestResolveOutputMode:
    def test_default_is_files(self):
        with patch.dict(os.environ, {}, clear=True):
            assert resolve_output_mode() == "files"

    @pytest.mark.parametrize("mode", ["files", "resources", "both"])
    def test_valid_modes(self, mode):
        with patch.dict(os.environ, {"SUPERTONE_MCP_OUTPUT_MODE": mode}):
            assert resolve_output_mode() == mode

    def test_case_insensitive(self):
        with patch.dict(os.environ, {"SUPERTONE_MCP_OUTPUT_MODE": "RESOURCES"}):
            assert resolve_output_mode() == "resources"

    def test_invalid_mode_raises(self):
        with patch.dict(os.environ, {"SUPERTONE_MCP_OUTPUT_MODE": "invalid"}):
            with pytest.raises(ValueError, match='Invalid output mode: "invalid"'):
                resolve_output_mode()


class TestFormatTtsMetadata:
    def test_without_file_path(self):
        result = format_tts_metadata(
            duration=2.3, voice_id="v1", language="ko", output_format="mp3"
        )
        assert result == "Duration: 2.3s | Voice: v1 | Language: ko | Format: mp3"

    def test_with_file_path(self):
        result = format_tts_metadata(
            duration=1.0, voice_id="v1", language="en", output_format="wav",
            file_path="/tmp/out.wav",
        )
        assert result == "Saved: /tmp/out.wav | Duration: 1.0s | Voice: v1 | Language: en | Format: wav"


class TestFormatTtsResponse:
    def test_produces_exact_format(self):
        resp = TTSResponse(
            file_path="/Users/test/output/2026-03-13_abc123.mp3",
            duration_seconds=2.3,
            voice_id="yuki-01",
            language="en",
            output_format="mp3",
        )
        result = format_tts_response(resp)
        expected = (
            "Audio file saved: /Users/test/output/2026-03-13_abc123.mp3\n"
            "Duration: 2.3 seconds\n"
            "Voice: yuki-01\n"
            "Language: en\n"
            "Format: mp3"
        )
        assert result == expected


class TestFormatVoiceList:
    def test_with_voices(self):
        voices = [
            VoiceInfo(voice_id="sujin-01", name="Sujin", supported_languages=["ko", "en"], supported_styles=["neutral", "happy"]),
            VoiceInfo(voice_id="minho-01", name="Minho", supported_languages=["ko"], supported_styles=["neutral"]),
        ]
        result = format_voice_list(voices)
        assert "Found 2 voices:" in result
        assert "1. Name: Sujin" in result
        assert "2. Name: Minho" in result
        assert "Voice ID: sujin-01" in result
        assert "Languages: ko, en" in result
        assert "Styles: neutral, happy" in result

    def test_empty_with_filter(self):
        result = format_voice_list([], language_filter="ja")
        assert result == "No voices found matching language: ja."

    def test_empty_no_filter(self):
        result = format_voice_list([])
        assert result == "No voices found."

    def test_with_language_filter(self):
        voices = [
            VoiceInfo(voice_id="v1", name="V1", supported_languages=["ko"], supported_styles=["neutral"]),
        ]
        result = format_voice_list(voices, language_filter="ko")
        assert "Found 1 voices matching language: ko" in result


class TestCalculateDuration:
    def test_returns_float_for_valid_file(self, tmp_path):
        mock_audio = MagicMock()
        mock_audio.info.length = 2.345

        with patch("supertone_tts_mcp.tools.MutagenFile", return_value=mock_audio):
            duration = calculate_duration("/tmp/test.mp3")

        assert duration == 2.3

    def test_returns_zero_for_unrecognized(self, tmp_path):
        with patch("supertone_tts_mcp.tools.MutagenFile", return_value=None):
            duration = calculate_duration("/tmp/test.mp3")
        assert duration == 0.0


# --- Tool Handler Tests ---


def _mock_synthesize():
    """Create a mock for SupertoneClient.synthesize that returns audio bytes."""
    return AsyncMock(return_value=(b"\xff\xfb\x90\x00" * 10, "audio/mpeg", 2.3))


def _mock_get_voices(voices=None):
    """Create a mock for SupertoneClient.get_voices."""
    if voices is None:
        voices = [
            {"voice_id": "sujin-01", "name": "Sujin", "supported_languages": ["ko", "en"], "supported_styles": ["neutral", "happy"]},
            {"voice_id": "yuki-01", "name": "Yuki", "supported_languages": ["ja"], "supported_styles": ["neutral"]},
            {"voice_id": "minho-01", "name": "Minho", "supported_languages": ["ko"], "supported_styles": ["neutral", "sad"]},
        ]
    return AsyncMock(return_value=voices)


class TestTextToSpeechHandler:
    @pytest.mark.asyncio
    async def test_happy_path(self, tmp_path):
        with (
            patch.dict(os.environ, {"SUPERTONE_API_KEY": "test-key", "SUPERTONE_OUTPUT_DIR": str(tmp_path)}),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MockClient,
        ):
            instance = MockClient.return_value
            instance.synthesize = _mock_synthesize()
            instance.aclose = AsyncMock()

            result = await text_to_speech(text="Hello world")

        assert "Audio file saved:" in result
        assert "Duration: 2.3 seconds" in result
        assert str(tmp_path) in result

    @pytest.mark.asyncio
    async def test_uses_api_duration(self, tmp_path):
        """Duration from API header should be used instead of mutagen."""
        with (
            patch.dict(os.environ, {"SUPERTONE_API_KEY": "test-key", "SUPERTONE_OUTPUT_DIR": str(tmp_path)}),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MockClient,
        ):
            instance = MockClient.return_value
            instance.synthesize = AsyncMock(return_value=(b"\xff" * 10, "audio/mpeg", 5.7))
            instance.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        assert "Duration: 5.7 seconds" in result

    @pytest.mark.asyncio
    async def test_falls_back_to_mutagen_when_no_api_duration(self, tmp_path):
        mock_duration = MagicMock()
        mock_duration.info.length = 3.456

        with (
            patch.dict(os.environ, {"SUPERTONE_API_KEY": "test-key", "SUPERTONE_OUTPUT_DIR": str(tmp_path)}),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MockClient,
            patch("supertone_tts_mcp.tools.MutagenFile", return_value=mock_duration),
        ):
            instance = MockClient.return_value
            instance.synthesize = AsyncMock(return_value=(b"\xff" * 10, "audio/mpeg", None))
            instance.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        assert "Duration: 3.5 seconds" in result

    @pytest.mark.asyncio
    async def test_default_voice_id(self, tmp_path):
        with (
            patch.dict(os.environ, {"SUPERTONE_API_KEY": "test-key", "SUPERTONE_OUTPUT_DIR": str(tmp_path)}),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MockClient,
        ):
            instance = MockClient.return_value
            instance.synthesize = _mock_synthesize()
            instance.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        assert "Voice: 2d5a380030e78fcab0c82a" in result

    @pytest.mark.asyncio
    async def test_default_language(self, tmp_path):
        with (
            patch.dict(os.environ, {"SUPERTONE_API_KEY": "test-key", "SUPERTONE_OUTPUT_DIR": str(tmp_path)}),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MockClient,
        ):
            instance = MockClient.return_value
            instance.synthesize = _mock_synthesize()
            instance.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        assert "Language: ko" in result

    @pytest.mark.asyncio
    async def test_empty_text_returns_error(self):
        with patch.dict(os.environ, {"SUPERTONE_API_KEY": "test-key"}):
            result = await text_to_speech(text="")
        assert result == "Text must not be empty."

    @pytest.mark.asyncio
    async def test_invalid_language_returns_error(self):
        with patch.dict(os.environ, {"SUPERTONE_API_KEY": "test-key"}):
            result = await text_to_speech(text="Hello", language="zz")
        assert 'Invalid language: "zz"' in result

    @pytest.mark.asyncio
    async def test_auth_error_caught(self, tmp_path):
        with (
            patch.dict(os.environ, {"SUPERTONE_API_KEY": "bad-key", "SUPERTONE_OUTPUT_DIR": str(tmp_path)}),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MockClient,
        ):
            instance = MockClient.return_value
            instance.synthesize = AsyncMock(side_effect=SupertoneAuthError())
            instance.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        assert result == "Authentication failed. Please verify your SUPERTONE_API_KEY."

    @pytest.mark.asyncio
    async def test_rate_limit_error_caught(self, tmp_path):
        with (
            patch.dict(os.environ, {"SUPERTONE_API_KEY": "key", "SUPERTONE_OUTPUT_DIR": str(tmp_path)}),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MockClient,
        ):
            instance = MockClient.return_value
            instance.synthesize = AsyncMock(side_effect=SupertoneRateLimitError())
            instance.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        assert result == "Rate limit exceeded. Please wait and try again."

    @pytest.mark.asyncio
    async def test_server_error_caught(self, tmp_path):
        with (
            patch.dict(os.environ, {"SUPERTONE_API_KEY": "key", "SUPERTONE_OUTPUT_DIR": str(tmp_path)}),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MockClient,
        ):
            instance = MockClient.return_value
            instance.synthesize = AsyncMock(side_effect=SupertoneServerError(503))
            instance.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        assert result == "Supertone API server error (503). Please try again later."

    @pytest.mark.asyncio
    async def test_connection_error_caught(self, tmp_path):
        with (
            patch.dict(os.environ, {"SUPERTONE_API_KEY": "key", "SUPERTONE_OUTPUT_DIR": str(tmp_path)}),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MockClient,
        ):
            instance = MockClient.return_value
            instance.synthesize = AsyncMock(side_effect=SupertoneConnectionError())
            instance.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        assert result == "Failed to connect to Supertone API. Please check your network connection."

    @pytest.mark.asyncio
    async def test_file_written_with_correct_bytes(self, tmp_path):
        audio_data = b"\xff\xfb\x90\x00" * 10

        with (
            patch.dict(os.environ, {"SUPERTONE_API_KEY": "key", "SUPERTONE_OUTPUT_DIR": str(tmp_path)}),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MockClient,
        ):
            instance = MockClient.return_value
            instance.synthesize = AsyncMock(return_value=(audio_data, "audio/mpeg", 1.0))
            instance.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        file_path = result.split("Audio file saved: ")[1].split("\n")[0]
        assert Path(file_path).read_bytes() == audio_data

    @pytest.mark.asyncio
    async def test_api_key_missing_returns_error(self):
        with patch.dict(os.environ, {}, clear=True):
            result = await text_to_speech(text="Hello")
        assert "SUPERTONE_API_KEY environment variable is not set" in result

    @pytest.mark.asyncio
    async def test_resources_mode_returns_audio_content(self):
        audio_data = b"\xff\xfb\x90\x00" * 10
        with (
            patch.dict(os.environ, {
                "SUPERTONE_API_KEY": "key",
                "SUPERTONE_MCP_OUTPUT_MODE": "resources",
            }),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MockClient,
        ):
            instance = MockClient.return_value
            instance.synthesize = AsyncMock(return_value=(audio_data, "audio/mpeg", 2.3))
            instance.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        assert isinstance(result, list)
        assert len(result) == 2
        assert isinstance(result[0], AudioContent)
        assert result[0].mimeType == "audio/mpeg"
        assert isinstance(result[1], TextContent)
        assert "Duration: 2.3s" in result[1].text
        assert "Saved:" not in result[1].text

    @pytest.mark.asyncio
    async def test_resources_mode_no_file_written(self, tmp_path):
        audio_data = b"\xff\xfb\x90\x00" * 10
        with (
            patch.dict(os.environ, {
                "SUPERTONE_API_KEY": "key",
                "SUPERTONE_MCP_OUTPUT_MODE": "resources",
                "SUPERTONE_OUTPUT_DIR": str(tmp_path),
            }),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MockClient,
        ):
            instance = MockClient.return_value
            instance.synthesize = AsyncMock(return_value=(audio_data, "audio/mpeg", 1.0))
            instance.aclose = AsyncMock()

            await text_to_speech(text="Hello")

        assert list(tmp_path.iterdir()) == []

    @pytest.mark.asyncio
    async def test_both_mode_returns_audio_and_saves_file(self, tmp_path):
        audio_data = b"\xff\xfb\x90\x00" * 10
        with (
            patch.dict(os.environ, {
                "SUPERTONE_API_KEY": "key",
                "SUPERTONE_MCP_OUTPUT_MODE": "both",
                "SUPERTONE_OUTPUT_DIR": str(tmp_path),
            }),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MockClient,
        ):
            instance = MockClient.return_value
            instance.synthesize = AsyncMock(return_value=(audio_data, "audio/mpeg", 3.0))
            instance.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        assert isinstance(result, list)
        assert len(result) == 2
        assert isinstance(result[0], AudioContent)
        assert isinstance(result[1], TextContent)
        assert "Saved:" in result[1].text
        assert "Duration: 3.0s" in result[1].text
        # Verify file was written
        files = list(tmp_path.iterdir())
        assert len(files) == 1
        assert files[0].read_bytes() == audio_data

    @pytest.mark.asyncio
    async def test_resources_mode_wav_mime_type(self):
        audio_data = b"\x00" * 10
        with (
            patch.dict(os.environ, {
                "SUPERTONE_API_KEY": "key",
                "SUPERTONE_MCP_OUTPUT_MODE": "resources",
            }),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MockClient,
        ):
            instance = MockClient.return_value
            instance.synthesize = AsyncMock(return_value=(audio_data, "audio/wav", 1.0))
            instance.aclose = AsyncMock()

            result = await text_to_speech(text="Hello", output_format="wav")

        assert result[0].mimeType == "audio/wav"

    @pytest.mark.asyncio
    async def test_invalid_output_mode_returns_error(self):
        with patch.dict(os.environ, {
            "SUPERTONE_API_KEY": "key",
            "SUPERTONE_MCP_OUTPUT_MODE": "invalid",
        }):
            result = await text_to_speech(text="Hello")
        assert 'Invalid output mode: "invalid"' in result

    @pytest.mark.asyncio
    async def test_resources_mode_base64_encoding(self):
        import base64
        audio_data = b"\xff\xfb\x90\x00" * 5
        with (
            patch.dict(os.environ, {
                "SUPERTONE_API_KEY": "key",
                "SUPERTONE_MCP_OUTPUT_MODE": "resources",
            }),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MockClient,
        ):
            instance = MockClient.return_value
            instance.synthesize = AsyncMock(return_value=(audio_data, "audio/mpeg", 1.0))
            instance.aclose = AsyncMock()

            result = await text_to_speech(text="Hello")

        decoded = base64.b64decode(result[0].data)
        assert decoded == audio_data


class TestListVoicesHandler:
    @pytest.mark.asyncio
    async def test_no_filter_returns_all(self):
        with (
            patch.dict(os.environ, {"SUPERTONE_API_KEY": "key"}),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MockClient,
        ):
            instance = MockClient.return_value
            instance.get_voices = _mock_get_voices()
            instance.aclose = AsyncMock()

            result = await list_voices()

        assert "Found 3 voices:" in result
        assert "Sujin" in result
        assert "Yuki" in result
        assert "Minho" in result

    @pytest.mark.asyncio
    async def test_language_filter(self):
        with (
            patch.dict(os.environ, {"SUPERTONE_API_KEY": "key"}),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MockClient,
        ):
            instance = MockClient.return_value
            instance.get_voices = _mock_get_voices()
            instance.aclose = AsyncMock()

            result = await list_voices(language="ko")

        assert "Found 2 voices matching language: ko" in result
        assert "Sujin" in result
        assert "Minho" in result
        assert "Yuki" not in result

    @pytest.mark.asyncio
    async def test_empty_result(self):
        with (
            patch.dict(os.environ, {"SUPERTONE_API_KEY": "key"}),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MockClient,
        ):
            instance = MockClient.return_value
            instance.get_voices = _mock_get_voices(voices=[])
            instance.aclose = AsyncMock()

            result = await list_voices()

        assert result == "No voices found."

    @pytest.mark.asyncio
    async def test_invalid_language_filter(self):
        with patch.dict(os.environ, {"SUPERTONE_API_KEY": "key"}):
            result = await list_voices(language="zz")
        assert 'Invalid language: "zz"' in result

    @pytest.mark.asyncio
    async def test_auth_error_caught(self):
        with (
            patch.dict(os.environ, {"SUPERTONE_API_KEY": "key"}),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MockClient,
        ):
            instance = MockClient.return_value
            instance.get_voices = AsyncMock(side_effect=SupertoneAuthError())
            instance.aclose = AsyncMock()

            result = await list_voices()

        assert result == "Authentication failed. Please verify your SUPERTONE_API_KEY."

    @pytest.mark.asyncio
    async def test_connection_error_caught(self):
        with (
            patch.dict(os.environ, {"SUPERTONE_API_KEY": "key"}),
            patch("supertone_tts_mcp.tools.SupertoneClient") as MockClient,
        ):
            instance = MockClient.return_value
            instance.get_voices = AsyncMock(side_effect=SupertoneConnectionError())
            instance.aclose = AsyncMock()

            result = await list_voices()

        assert result == "Failed to connect to Supertone API. Please check your network connection."
