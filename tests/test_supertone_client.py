"""Tests for SupertoneClient (ISSUE-003)."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from supertone_tts_mcp.exceptions import (
    SupertoneAuthError,
    SupertoneConnectionError,
    SupertoneRateLimitError,
    SupertoneServerError,
)
from supertone_tts_mcp.supertone_client import SupertoneClient


@pytest.fixture
def client():
    return SupertoneClient(api_key="test-key", base_url="https://api.test.com")


def _mock_response(status_code: int, content: bytes = b"", headers: dict | None = None, json_data=None):
    """Create a mock httpx.Response."""
    resp = httpx.Response(
        status_code=status_code,
        content=content,
        headers=headers or {},
        request=httpx.Request("GET", "https://api.test.com"),
    )
    if json_data is not None:
        # Override content with JSON
        import json as json_module
        resp = httpx.Response(
            status_code=status_code,
            content=json_module.dumps(json_data).encode(),
            headers={"content-type": "application/json", **(headers or {})},
            request=httpx.Request("GET", "https://api.test.com"),
        )
    return resp


class TestSynthesize:
    @pytest.mark.asyncio
    async def test_returns_bytes_on_200(self, client):
        audio_data = b"\xff\xfb\x90\x00" * 100
        mock_resp = _mock_response(200, content=audio_data, headers={"content-type": "audio/mpeg"})

        with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_resp):
            result_bytes, content_type = await client.synthesize(
                voice_id="v1", text="Hello", language="en",
                output_format="mp3", speed=1.0, pitch_shift=0,
            )

        assert result_bytes == audio_data
        assert content_type == "audio/mpeg"

    @pytest.mark.asyncio
    async def test_sends_correct_post_path(self, client):
        mock_resp = _mock_response(200, content=b"audio", headers={"content-type": "audio/mpeg"})

        with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_resp) as mock_post:
            await client.synthesize(
                voice_id="sujin-01", text="Hello", language="en",
                output_format="mp3", speed=1.0, pitch_shift=0,
            )

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "/v1/text-to-speech/sujin-01"

    @pytest.mark.asyncio
    async def test_sends_api_key_header(self, client):
        assert client._client.headers["x-sup-api-key"] == "test-key"

    @pytest.mark.asyncio
    async def test_omits_style_when_none(self, client):
        mock_resp = _mock_response(200, content=b"audio", headers={"content-type": "audio/mpeg"})

        with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_resp) as mock_post:
            await client.synthesize(
                voice_id="v1", text="Hello", language="en",
                output_format="mp3", speed=1.0, pitch_shift=0, style=None,
            )

        call_kwargs = mock_post.call_args[1]
        assert "style" not in call_kwargs["json"]

    @pytest.mark.asyncio
    async def test_includes_style_when_provided(self, client):
        mock_resp = _mock_response(200, content=b"audio", headers={"content-type": "audio/mpeg"})

        with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_resp) as mock_post:
            await client.synthesize(
                voice_id="v1", text="Hello", language="en",
                output_format="mp3", speed=1.0, pitch_shift=0, style="happy",
            )

        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["style"] == "happy"

    @pytest.mark.asyncio
    async def test_401_raises_auth_error(self, client):
        mock_resp = _mock_response(401)

        with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_resp):
            with pytest.raises(SupertoneAuthError):
                await client.synthesize(
                    voice_id="v1", text="Hello", language="en",
                    output_format="mp3", speed=1.0, pitch_shift=0,
                )

    @pytest.mark.asyncio
    async def test_403_raises_auth_error(self, client):
        mock_resp = _mock_response(403)

        with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_resp):
            with pytest.raises(SupertoneAuthError):
                await client.synthesize(
                    voice_id="v1", text="Hello", language="en",
                    output_format="mp3", speed=1.0, pitch_shift=0,
                )

    @pytest.mark.asyncio
    async def test_500_raises_server_error(self, client):
        mock_resp = _mock_response(500)

        with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_resp):
            with pytest.raises(SupertoneServerError) as exc_info:
                await client.synthesize(
                    voice_id="v1", text="Hello", language="en",
                    output_format="mp3", speed=1.0, pitch_shift=0,
                )
            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_503_raises_server_error(self, client):
        mock_resp = _mock_response(503)

        with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_resp):
            with pytest.raises(SupertoneServerError) as exc_info:
                await client.synthesize(
                    voice_id="v1", text="Hello", language="en",
                    output_format="mp3", speed=1.0, pitch_shift=0,
                )
            assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_connection_error_raises(self, client):
        with patch.object(client._client, "post", new_callable=AsyncMock, side_effect=httpx.ConnectError("Connection refused")):
            with pytest.raises(SupertoneConnectionError):
                await client.synthesize(
                    voice_id="v1", text="Hello", language="en",
                    output_format="mp3", speed=1.0, pitch_shift=0,
                )

    @pytest.mark.asyncio
    async def test_timeout_raises_connection_error(self, client):
        with patch.object(client._client, "post", new_callable=AsyncMock, side_effect=httpx.ReadTimeout("Timeout")):
            with pytest.raises(SupertoneConnectionError):
                await client.synthesize(
                    voice_id="v1", text="Hello", language="en",
                    output_format="mp3", speed=1.0, pitch_shift=0,
                )


class TestGetVoices:
    @pytest.mark.asyncio
    async def test_returns_parsed_list(self, client):
        voices = [
            {"voice_id": "v1", "name": "Voice1", "supported_languages": ["ko"], "supported_styles": ["neutral"]},
            {"voice_id": "v2", "name": "Voice2", "supported_languages": ["en"], "supported_styles": ["happy"]},
        ]
        mock_resp = _mock_response(200, json_data=voices)

        with patch.object(client._client, "get", new_callable=AsyncMock, return_value=mock_resp):
            result = await client.get_voices()

        assert len(result) == 2
        assert result[0]["voice_id"] == "v1"

    @pytest.mark.asyncio
    async def test_sends_get_to_voices(self, client):
        mock_resp = _mock_response(200, json_data=[])

        with patch.object(client._client, "get", new_callable=AsyncMock, return_value=mock_resp) as mock_get:
            await client.get_voices()

        mock_get.assert_called_once_with("/v1/voices")

    @pytest.mark.asyncio
    async def test_429_raises_rate_limit_error(self, client):
        mock_resp = _mock_response(429)

        with patch.object(client._client, "get", new_callable=AsyncMock, return_value=mock_resp):
            with pytest.raises(SupertoneRateLimitError):
                await client.get_voices()


class TestAclose:
    @pytest.mark.asyncio
    async def test_closes_client(self, client):
        with patch.object(client._client, "aclose", new_callable=AsyncMock) as mock_close:
            await client.aclose()
        mock_close.assert_called_once()
