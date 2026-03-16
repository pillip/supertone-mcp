"""Tests for MCP server entry point and tool registration (ISSUE-007)."""

import pathlib

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
        desc = tool.description
        assert "speech" in desc
        assert "list_voices" in desc
        assert "23 languages" in desc

    def test_list_voices_description(self):
        tool = mcp._tool_manager._tools["list_voices"]
        desc = tool.description
        assert "voice" in desc.lower()
        assert "text_to_speech" in desc or "text-to-speech" in desc

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
        main_path = (
            pathlib.Path(__file__).parent.parent
            / "src"
            / "supertone_tts_mcp"
            / "__main__.py"
        )
        assert main_path.exists()

    def test_main_module_imports_main(self):
        source = (
            pathlib.Path(__file__).parent.parent
            / "src"
            / "supertone_tts_mcp"
            / "__main__.py"
        ).read_text()
        assert "from supertone_tts_mcp.server import main" in source
