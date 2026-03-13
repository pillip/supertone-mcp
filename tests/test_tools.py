"""Tests for input validation and output formatting (ISSUE-004)."""

import os
from unittest.mock import MagicMock, patch

import pytest

from supertone_tts_mcp.models import TTSResponse, VoiceInfo
from supertone_tts_mcp.tools import (
    calculate_duration,
    ensure_output_dir,
    format_tts_response,
    format_voice_list,
    resolve_api_key,
    resolve_output_dir,
    validate_language,
    validate_output_format,
    validate_pitch_shift,
    validate_speed,
    validate_text,
)


class TestValidateText:
    def test_empty_string(self):
        with pytest.raises(ValueError, match="Text must not be empty."):
            validate_text("")

    def test_301_chars(self):
        text = "a" * 301
        with pytest.raises(
            ValueError,
            match=r"Text exceeds the maximum length of 300 characters \(received: 301\)",
        ):
            validate_text(text)

    def test_300_chars_passes(self):
        validate_text("a" * 300)

    def test_1_char_passes(self):
        validate_text("a")


class TestValidateLanguage:
    @pytest.mark.parametrize("lang", ["ko", "en", "ja"])
    def test_valid_languages(self, lang):
        validate_language(lang)

    def test_invalid_language(self):
        with pytest.raises(
            ValueError,
            match=r'Invalid language: "zz"\. Supported languages: ko, en, ja\.',
        ):
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
    @pytest.mark.parametrize("pitch", [-12, 0, 12])
    def test_valid_pitches(self, pitch):
        validate_pitch_shift(pitch)

    def test_too_low(self):
        with pytest.raises(
            ValueError,
            match=r"Pitch shift must be between -12 and \+12 semitones \(received: -13\)\.",
        ):
            validate_pitch_shift(-13)

    def test_too_high(self):
        with pytest.raises(
            ValueError,
            match=r"Pitch shift must be between -12 and \+12 semitones \(received: 13\)\.",
        ):
            validate_pitch_shift(13)


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
        # Create a minimal valid MP3 file is complex, so we mock mutagen
        mock_audio = MagicMock()
        mock_audio.info.length = 2.345

        with patch("supertone_tts_mcp.tools.MutagenFile", return_value=mock_audio):
            duration = calculate_duration("/tmp/test.mp3")

        assert duration == 2.3

    def test_returns_zero_for_unrecognized(self, tmp_path):
        with patch("supertone_tts_mcp.tools.MutagenFile", return_value=None):
            duration = calculate_duration("/tmp/test.mp3")
        assert duration == 0.0
