"""HTTP client wrapper for the Supertone TTS API."""

import httpx

from supertone_tts_mcp.constants import HTTP_TIMEOUT, SUPERTONE_BASE_URL
from supertone_tts_mcp.exceptions import (
    SupertoneAPIError,
    SupertoneAuthError,
    SupertoneConnectionError,
    SupertoneRateLimitError,
    SupertoneServerError,
)
from supertone_tts_mcp.models import SynthesizeRequestBody, VoiceDict


class SupertoneClient:
    """Async HTTP client for the Supertone TTS API."""

    def __init__(
        self, api_key: str, base_url: str = SUPERTONE_BASE_URL
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"x-sup-api-key": api_key},
            timeout=HTTP_TIMEOUT,
        )

    async def synthesize(
        self,
        voice_id: str,
        text: str,
        language: str,
        output_format: str,
        speed: float,
        pitch_shift: int,
        style: str | None = None,
    ) -> tuple[bytes, str]:
        """Call the Supertone TTS API to synthesize speech.

        Returns a tuple of (audio_bytes, content_type).
        """
        body: SynthesizeRequestBody = {
            "text": text,
            "language": language,
            "output_format": output_format,
            "speed": speed,
            "pitch_shift": pitch_shift,
        }
        if style is not None:
            body["style"] = style

        try:
            response = await self._client.post(
                f"/v1/text-to-speech/{voice_id}",
                json=body,
            )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise SupertoneConnectionError(str(exc)) from exc

        if response.status_code != 200:
            self._handle_error_response(response)

        content_type = response.headers.get("content-type", "audio/mpeg")
        return response.content, content_type

    async def get_voices(self) -> list[VoiceDict]:
        """Fetch the list of available voices from the Supertone API."""
        try:
            response = await self._client.get("/v1/voices")
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise SupertoneConnectionError(str(exc)) from exc

        if response.status_code != 200:
            self._handle_error_response(response)

        return response.json()

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Map HTTP error responses to domain exceptions."""
        status = response.status_code

        if status in (401, 403):
            raise SupertoneAuthError()
        elif status == 429:
            raise SupertoneRateLimitError()
        elif status >= 500:
            raise SupertoneServerError(status)
        else:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise SupertoneAPIError(status, str(detail))
