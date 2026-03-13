"""Tests for MCP server entry point and tool registration (ISSUE-007)."""

import pathlib

import pytest

from supertone_tts_mcp.server import mcp


class TestToolRegistration:
    def test_registers_exactly_two_tools(self):
        tool_manager = mcp._tool_manager
        tools = tool_manager._tools
        assert len(tools) == 2

    def test_text_to_speech_tool_exists(self):
        tools = mcp._tool_manager._tools
        assert "text_to_speech" in tools

    def test_list_voices_tool_exists(self):
        tools = mcp._tool_manager._tools
        assert "list_voices" in tools

    def test_text_to_speech_description(self):
        tool = mcp._tool_manager._tools["text_to_speech"]
        expected = (
            "Convert text to speech using Supertone TTS API. "
            "Supports 23 languages including Korean, English, and Japanese. "
            "Long text is automatically split into chunks and processed. "
            "Output mode is controlled by SUPERTONE_MCP_OUTPUT_MODE env var: "
            '"files" (default) saves to disk and returns file path, '
            '"resources" returns audio data directly (no disk write), '
            '"both" saves to disk and returns audio data with file path. '
            "Set SUPERTONE_MCP_AUTOPLAY=false to disable auto-play. "
            "Set SUPERTONE_MCP_VOICE_ID to use a default voice without calling list_voices."
        )
        assert tool.description == expected

    def test_list_voices_description(self):
        tool = mcp._tool_manager._tools["list_voices"]
        expected = (
            "List available Supertone TTS voices. "
            "Returns voice ID, name, supported languages, and supported emotion "
            "styles for each voice. Optionally filter by language."
        )
        assert tool.description == expected

    def test_text_to_speech_has_text_parameter(self):
        tool = mcp._tool_manager._tools["text_to_speech"]
        schema = tool.parameters
        assert "text" in schema["properties"]

    def test_text_to_speech_text_is_required(self):
        tool = mcp._tool_manager._tools["text_to_speech"]
        schema = tool.parameters
        assert "text" in schema.get("required", [])

    def test_text_to_speech_has_model_parameter(self):
        tool = mcp._tool_manager._tools["text_to_speech"]
        schema = tool.parameters
        assert "model" in schema["properties"]

    def test_list_voices_language_is_optional(self):
        tool = mcp._tool_manager._tools["list_voices"]
        schema = tool.parameters
        required = schema.get("required", [])
        assert "language" not in required


class TestMainFunction:
    def test_main_is_callable(self):
        from supertone_tts_mcp.server import main
        assert callable(main)


class TestMainModule:
    def test_main_module_exists(self):
        main_path = pathlib.Path(__file__).parent.parent / "src" / "supertone_tts_mcp" / "__main__.py"
        assert main_path.exists()

    def test_main_module_imports_main(self):
        source = (
            pathlib.Path(__file__).parent.parent
            / "src" / "supertone_tts_mcp" / "__main__.py"
        ).read_text()
        assert "from supertone_tts_mcp.server import main" in source
