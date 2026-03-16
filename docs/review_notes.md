# Review Notes: ISSUE-013 — Streaming TTS

> Reviewed: 2026-03-16
> PR: #9
> Branch: feat/streaming-tts-issue-013

## Code Review

### Findings

1. **Fixed (Medium): Inconsistent error handling in `get_voices()`**
   - `get_voices()` used inline exception handling while `synthesize()` and `synthesize_stream()` used the new `_handle_sdk_errors()` helper.
   - Refactored `get_voices()` to use `_handle_sdk_errors()` for consistency.

2. **Fixed (Low): Unnecessary file re-read in files mode**
   - In `files` mode, the entire audio file was read back into memory (`Path(file_path_str).read_bytes()`) after streaming to disk. This was unnecessary since `_autoplay()` uses `file_path` directly when available.
   - Removed the redundant read; `audio_bytes` is now only populated from `memory_buffer` when `collect_in_memory` is true.

3. **OK: Async generator typing** — `synthesize_stream` returns `AsyncIterator[bytes]` which is correct for async generators.

4. **OK: NDJSON fallback** — The `else` branch in `synthesize_stream` (line 187) handles non-httpx response types gracefully by encoding to bytes.

5. **OK: Partial file cleanup** — Error paths in `text_to_speech` properly clean up partial files on `SupertoneServerError` and `SupertoneConnectionError`.

### Changes Made

- `supertone_client.py`: Refactored `get_voices()` to use `_handle_sdk_errors()`.
- `tools.py`: Removed unnecessary file re-read in files mode; `audio_bytes` only populated from memory buffer when needed.

### Follow-ups

- None required.

## Security Findings

| Severity | Finding | Status |
|----------|---------|--------|
| None | No security issues found | Pass |

- API key handling unchanged — never logged or exposed.
- No new injection vectors introduced.
- `subprocess.Popen` usage in `_autoplay` uses controlled paths (no user input in shell commands for file mode).
- The `shell=True` path in `_autoplay` for resources mode uses `tmp.name` which is system-generated — acceptable risk.

## Test Coverage

- 155 tests passing (10 new streaming tests).
- Streaming happy path, error handling, partial file cleanup, all output modes covered.
- Test infrastructure uses proper async generator mocks.
