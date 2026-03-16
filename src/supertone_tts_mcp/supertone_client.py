"""SDK wrapper for the Supertone TTS API."""

import base64
from collections.abc import AsyncIterator

import httpx
from supertone import Supertone, models
from supertone.errors.forbiddenerrorresponse import ForbiddenErrorResponse
from supertone.errors.internalservererrorresponse import InternalServerErrorResponse
from supertone.errors.no_response_error import NoResponseError
from supertone.errors.toomanyrequestserrorresponse import TooManyRequestsErrorResponse
from supertone.errors.unauthorizederrorresponse import UnauthorizedErrorResponse

from supertone_tts_mcp.exceptions import (
    SupertoneAuthError,
    SupertoneConnectionError,
    SupertoneRateLimitError,
    SupertoneServerError,
)
from supertone_tts_mcp.models import VoiceDict

# Map string language codes to SDK enum values
_LANGUAGE_MAP = {
    member.value: member
    for member in models.APIConvertTextToSpeechUsingCharacterRequestLanguage
}

# Map string model names to SDK enum values
_MODEL_MAP = {
    member.value: member
    for member in models.APIConvertTextToSpeechUsingCharacterRequestModel
}

# Map string format names to SDK enum values
_FORMAT_MAP = {
    member.value: member
    for member in models.APIConvertTextToSpeechUsingCharacterRequestOutputFormat
}


def _handle_sdk_errors(exc: Exception) -> None:
    """Map SDK exceptions to domain exceptions. Always raises."""
    if isinstance(exc, (UnauthorizedErrorResponse, ForbiddenErrorResponse)):
        raise SupertoneAuthError() from exc
    if isinstance(exc, TooManyRequestsErrorResponse):
        raise SupertoneRateLimitError() from exc
    if isinstance(exc, InternalServerErrorResponse):
        status = exc.raw_response.status_code if hasattr(exc, "raw_response") else 500
        raise SupertoneServerError(status) from exc
    if isinstance(exc, NoResponseError):
        raise SupertoneConnectionError(str(exc)) from exc
    if isinstance(exc, httpx.ConnectError):
        raise SupertoneConnectionError(str(exc)) from exc
    if isinstance(exc, httpx.TimeoutException):
        raise SupertoneConnectionError(str(exc)) from exc
    raise exc


class SupertoneClient:
    """Async client for the Supertone TTS API using the official SDK."""

    def __init__(self, api_key: str) -> None:
        self._sdk = Supertone(api_key=api_key)

    async def synthesize(
        self,
        voice_id: str,
        text: str,
        language: str,
        output_format: str,
        model: str,
        speed: float,
        pitch_shift: int,
        style: str | None = None,
    ) -> tuple[bytes, str, float | None]:
        """Synthesize speech using the Supertone SDK (batch mode).

        The SDK automatically splits text longer than 300 characters into chunks,
        processes them in parallel, and concatenates the audio.

        Returns a tuple of (audio_bytes, content_type, duration_seconds).
        """
        lang_enum = _LANGUAGE_MAP[language]
        model_enum = _MODEL_MAP[model]
        fmt_enum = _FORMAT_MAP[output_format]

        voice_settings = models.ConvertTextToSpeechParameters(
            speed=speed,
            pitch_shift=float(pitch_shift),
        )

        try:
            response = await self._sdk.text_to_speech.create_speech_async(
                voice_id=voice_id,
                text=text,
                language=lang_enum,
                model=model_enum,
                output_format=fmt_enum,
                voice_settings=voice_settings,
                style=style,
            )
        except (
            UnauthorizedErrorResponse,
            ForbiddenErrorResponse,
            TooManyRequestsErrorResponse,
            InternalServerErrorResponse,
            NoResponseError,
            httpx.ConnectError,
            httpx.TimeoutException,
        ) as exc:
            _handle_sdk_errors(exc)

        # Determine content type
        content_type = f"audio/{output_format}"

        # Extract audio bytes from response
        result = response.result
        if isinstance(result, httpx.Response):
            audio_bytes = result.content
            # Try to get duration from X-Audio-Length header
            duration: float | None = None
            audio_length = result.headers.get("x-audio-length")
            if audio_length:
                try:
                    duration = float(audio_length)
                except ValueError:
                    pass
            return audio_bytes, content_type, duration
        else:
            # CreateSpeechResponseBody with audio_base64
            audio_bytes = base64.b64decode(result.audio_base64)
            return audio_bytes, content_type, None

    async def synthesize_stream(
        self,
        voice_id: str,
        text: str,
        language: str,
        output_format: str,
        model: str,
        speed: float,
        pitch_shift: int,
        style: str | None = None,
    ) -> AsyncIterator[bytes]:
        """Synthesize speech using the Supertone SDK streaming API.

        Yields audio data chunks as they are received from the API.
        This reduces time-to-first-audio compared to the batch synthesize() method.
        """
        lang_enum = _LANGUAGE_MAP[language]
        model_enum = _MODEL_MAP[model]
        fmt_enum = _FORMAT_MAP[output_format]

        voice_settings = models.ConvertTextToSpeechParameters(
            speed=speed,
            pitch_shift=float(pitch_shift),
        )

        try:
            response = await self._sdk.text_to_speech.stream_speech_async(
                voice_id=voice_id,
                text=text,
                language=lang_enum,
                model=model_enum,
                output_format=fmt_enum,
                voice_settings=voice_settings,
                style=style,
            )
        except (
            UnauthorizedErrorResponse,
            ForbiddenErrorResponse,
            TooManyRequestsErrorResponse,
            InternalServerErrorResponse,
            NoResponseError,
            httpx.ConnectError,
            httpx.TimeoutException,
        ) as exc:
            _handle_sdk_errors(exc)

        result = response.result
        if hasattr(result, "aiter_bytes"):
            async for chunk in result.aiter_bytes():
                yield chunk
        elif isinstance(result, str):
            yield result.encode("utf-8")
        else:
            yield result

    async def get_voices(self) -> list[VoiceDict]:
        """Fetch all available voices from the Supertone API (handles pagination)."""
        all_voices: list[VoiceDict] = []
        next_page_token: str | None = None

        while True:
            try:
                response = await self._sdk.voices.list_voices_async(
                    page_size=100,
                    next_page_token=next_page_token,
                )
            except (
                UnauthorizedErrorResponse,
                ForbiddenErrorResponse,
                TooManyRequestsErrorResponse,
                InternalServerErrorResponse,
                NoResponseError,
                httpx.ConnectError,
                httpx.TimeoutException,
            ) as exc:
                _handle_sdk_errors(exc)

            for item in response.items:
                voice: VoiceDict = {
                    "voice_id": item.voice_id,
                    "name": item.name,
                    "supported_languages": item.language,
                    "supported_styles": item.styles,
                }
                all_voices.append(voice)

            next_page_token = response.next_page_token
            if not next_page_token:
                break

        return all_voices

    async def aclose(self) -> None:
        """Close the underlying SDK HTTP client."""
        # The SDK uses httpx internally; close its async client if available
        if hasattr(self._sdk, "_client"):
            await self._sdk._client.aclose()
