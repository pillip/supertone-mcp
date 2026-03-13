# Architecture

## Overview

**Architecture style:** Single-process Python CLI application (monolith).

**Justification:** This is a thin wrapper around a third-party API, distributed as a PyPI package and executed as a subprocess by MCP clients. There is no database, no web server, no multi-user concurrency. The entire runtime is: receive a tool call over stdio, validate input, make one HTTP request, write a file, return a text response. A single Python module with three files is the correct architecture. Anything more is over-engineering.

**Key constraints driving the decision:**
- MCP servers communicate over stdio -- the process is spawned per-client session.
- No persistent state between tool calls (stateless by design).
- Single user, single API key per process.
- Must be installable and runnable with `uvx supertone-tts-mcp` (zero config beyond API key).

---

## Tech Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Language | Python 3.11+ | Team standard (claude.md), MCP SDK availability |
| MCP SDK | `mcp` (Python SDK) | Official SDK, required for protocol compliance (NFR-002) |
| HTTP client | `httpx` (async) | Async support required by NFR-008, modern Python HTTP library |
| Package manager | `uv` | Team standard (claude.md) |
| Test framework | `pytest` + `pytest-asyncio` | Team standard (claude.md), async test support |
| Audio metadata | `mutagen` (optional dep) | Duration calculation if API does not return it (Assumption A3) |
| Distribution | PyPI (`supertone-tts-mcp`) | NFR-001: single-command install |

**Version pinning rationale:** Pin `mcp` SDK to a specific minor version (e.g., `mcp>=1.0,<2.0`) because the MCP ecosystem is young and breaking changes are a known risk (R3). Pin `httpx>=0.27` for stable async client API. Do not pin patch versions -- let `uv.lock` handle reproducibility.

---

## Modules

### Module: `server` (`server.py`)

- **Responsibility:** MCP server entry point. Registers tools, configures stdio transport, starts the event loop.
- **Dependencies:** `tools` module, `mcp` SDK.
- **Key interfaces:**
  - `main()` -- entry point called by the console script. Creates the MCP `Server` instance, registers tool handlers from `tools.py`, and runs `server.run_stdio()`.
  - No public API beyond the entry point.

### Module: `tools` (`tools.py`)

- **Responsibility:** Implements the two MCP tool handlers (`text_to_speech`, `list_voices`). Handles all input validation and output formatting.
- **Dependencies:** `supertone_client` module.
- **Key interfaces:**
  - `async text_to_speech(text, voice_id?, language?, output_format?, speed?, pitch_shift?, style?) -> str` -- Validates inputs, calls client, saves file, returns formatted plain-text response.
  - `async list_voices(language?) -> str` -- Validates inputs, calls client, formats voice list as plain text.

### Module: `supertone_client` (`supertone_client.py`)

- **Responsibility:** Wraps all HTTP communication with the Supertone API. Translates HTTP errors into domain-specific exceptions.
- **Dependencies:** `httpx`.
- **Key interfaces:**
  - `class SupertoneClient`:
    - `__init__(api_key: str, base_url: str)` -- Configures the async HTTP client.
    - `async synthesize(voice_id: str, text: str, language: str, output_format: str, speed: float, pitch_shift: int, style: str | None) -> tuple[bytes, dict]` -- Calls `POST /v1/text-to-speech/{voice_id}`, returns raw audio bytes and response headers/metadata.
    - `async get_voices() -> list[dict]` -- Calls `GET /v1/voices`, returns parsed JSON list.
    - `async aclose()` -- Closes the underlying httpx client.

### Module: `__init__.py`

- **Responsibility:** Package metadata (`__version__`). Re-exports nothing -- keeps import surface minimal.

---

## Data Model

This system has no persistent data. All state is ephemeral within a single tool call.

### Entities (in-memory only)

| Entity | Shape | Storage | Lifecycle |
|--------|-------|---------|-----------|
| TTS Request | Validated parameters (text, voice_id, language, etc.) | In-memory dict | Single tool call |
| Audio File | Binary audio data (WAV/MP3) | Local filesystem | Persisted to `SUPERTONE_OUTPUT_DIR` |
| Voice | `{voice_id, name, languages, styles}` | In-memory (from API response) | Single tool call |

### File Storage

- **Location:** `SUPERTONE_OUTPUT_DIR` env var, default `~/supertone-tts-output/`.
- **Naming:** `{YYYY-MM-DD}_{uuid4_short}.{format}` (e.g., `2026-03-13_a1b2c3d4.mp3`). The UUID component is the first 8 characters of a UUID4 to keep filenames short while preventing collisions.
- **Directory creation:** `os.makedirs(path, exist_ok=True)` on each tool call. Catches `PermissionError` and returns actionable message (FR-004).

### Migration Strategy

Not applicable. No database, no schema, no migrations.

---

## API Design

This server has no HTTP API. It communicates via MCP protocol over stdio. The "API" is the two MCP tools.

### Internal Tool Interfaces

#### `text_to_speech`

```
Method: MCP tool call
Parameters:
  text: str          (required, 1-300 chars)
  voice_id: str      (optional, default: pre-configured Korean voice)
  language: str      (optional, default: "ko", enum: ["ko", "en", "ja"])
  output_format: str (optional, default: "mp3", enum: ["mp3", "wav"])
  speed: float       (optional, default: 1.0, range: [0.5, 2.0])
  pitch_shift: int   (optional, default: 0, range: [-12, +12])
  style: str         (optional, default: voice default)

Success response (plain text):
  Audio file saved: /absolute/path/to/file.mp3
  Duration: 2.3 seconds
  Voice: yuki-01
  Language: en
  Format: mp3

Error response (plain text):
  "{What went wrong}. {What to do}."
```

#### `list_voices`

```
Method: MCP tool call
Parameters:
  language: str  (optional, enum: ["ko", "en", "ja"])

Success response (plain text):
  Found N voices [matching language: xx]:

  1. Name: ...
     Voice ID: ...
     Languages: ...
     Styles: ...

Error response (plain text):
  "{What went wrong}. {What to do}."
```

### Supertone API Integration

| Operation | Method | Path | Auth Header | Request Body | Response |
|-----------|--------|------|-------------|-------------|----------|
| Synthesize | POST | `/v1/text-to-speech/{voice_id}` | `x-sup-api-key: {key}` | JSON: `{text, language, output_format, speed, pitch_shift, style}` | Binary audio stream |
| List voices | GET | `/v1/voices` | `x-sup-api-key: {key}` | None | JSON array of voice objects |

### Authentication

- Single API key from `SUPERTONE_API_KEY` env var.
- Validated at tool-call time (not at server startup -- server starts successfully without it, per FR-003).
- Sent as `x-sup-api-key` header on every request.
- Never logged, never included in error messages (NFR-007).

### Rate Limiting / Pagination

- No rate limiting on the MCP server side (out of scope per requirements).
- Supertone API rate limits (20-60 req/min) are passed through as HTTP 429 errors with actionable messages.
- No pagination needed -- `list_voices` returns all voices in a single call (expected to be a small list).

---

## Background Jobs

None. The server is entirely request-response. Each tool call is a synchronous operation from the MCP client's perspective (async internally for HTTP, but the client waits for the response).

---

## Observability

### Logging Strategy

- **Library:** Python `logging` module (standard library, no extra dependency).
- **Format:** Structured key-value pairs: `level=INFO module=supertone_client action=synthesize voice_id=yuki-01 status=200 duration_ms=1234`.
- **Levels:**
  - `DEBUG`: Full request parameters (excluding API key), response headers.
  - `INFO`: Tool call start/complete, file saved path, Supertone API response time.
  - `WARNING`: Rate limit received, fallback to default voice.
  - `ERROR`: API errors, file system errors, validation failures.
- **Destination:** stderr (stdout is reserved for MCP protocol messages over stdio).
- **What NOT to log:** API key values, raw audio data.

### Metrics

Not applicable for v1. This is a CLI tool, not a long-running service. If needed in v2, instrument with OpenTelemetry.

### Alerting

Not applicable. No long-running process to alert on.

---

## Security

### Auth Scheme

- No user authentication on the MCP server itself. The MCP client spawns the server as a subprocess and trusts it.
- Supertone API authentication via `x-sup-api-key` header, sourced from environment variable.

### Input Validation Strategy

All validation happens in `tools.py` before any API call (fail-fast):

1. **Text:** Non-empty, max 300 chars (Python `len()` for Unicode codepoint count).
2. **Language:** Enum check against `["ko", "en", "ja"]`.
3. **Output format:** Enum check against `["mp3", "wav"]`.
4. **Speed:** Range check `[0.5, 2.0]`.
5. **Pitch shift:** Range check `[-12, +12]`.
6. **Style:** Pass-through to API (validated by API since available styles are per-voice and may change).

### Secrets Management

- API key read from `SUPERTONE_API_KEY` env var only.
- Never written to disk, logs, or tool responses.
- `.env.example` contains placeholder only.
- No config files store secrets.

### OWASP Top 10 Mitigations

| Risk | Applicability | Mitigation |
|------|--------------|------------|
| Injection | Low -- no SQL, no shell commands | Input is validated and passed as typed parameters to httpx (no string interpolation into URLs/queries) |
| Broken Auth | Medium | API key from env var, never logged |
| Sensitive Data Exposure | Medium | API key never in logs or responses; audio files stored locally with user's filesystem permissions |
| SSRF | Low | Base URL is hardcoded (`https://api.supertoneapi.com`), not user-configurable |
| Path Traversal | Low | Output directory is resolved via `Path.expanduser().resolve()` and files are named with server-generated UUIDs (no user-controlled path components) |

---

## Deployment & Rollback

### Deployment Target

PyPI package, run as a subprocess by MCP clients. No containers, no servers, no cloud infrastructure.

### Build & Publish Pipeline

```
1. Version bump in pyproject.toml
2. Run tests: uv run pytest -q
3. Build: uv build
4. Publish: uv publish (or twine upload)
5. Verify: uvx supertone-tts-mcp --help
6. Tag git release: git tag v0.1.0
```

### CI/CD Pipeline Outline

```yaml
# GitHub Actions
on: [push, pull_request]
jobs:
  test:
    strategy:
      matrix:
        python: ["3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run pytest -q --cov=src --cov-report=term-missing

  publish:
    if: startsWith(github.ref, 'refs/tags/v')
    needs: test
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv build
      - run: uv publish
        env:
          UV_PUBLISH_TOKEN: ${{ secrets.PYPI_TOKEN }}
```

### Rollback Procedure

- **Code rollback:** `pip install supertone-tts-mcp==<previous-version>` or `uvx supertone-tts-mcp@<previous-version>`. PyPI retains all published versions.
- **No database migrations** to roll back.
- **No infrastructure** to roll back.
- If a broken version is published, yank it on PyPI: `uv publish --yank <version>`.

---

## Failure Mode Analysis

| Component | Failure | Impact | Handling |
|-----------|---------|--------|----------|
| `SUPERTONE_API_KEY` missing | Every tool call fails | Total (for that tool) | Server starts fine; each tool call returns clear error with setup instructions |
| Supertone API down (5xx) | TTS and voice listing fail | Total | Return "Supertone API server error ({code}). Please try again later." |
| Supertone API timeout | Tool call hangs | Partial | httpx timeout set to 30s; on timeout return "Failed to connect to Supertone API. Please check your network connection." |
| Network unreachable | All API calls fail | Total | Catch `httpx.ConnectError`, return network error message |
| Output directory not writable | File save fails (TTS only) | Partial (list_voices still works) | Catch `PermissionError`/`OSError`, return actionable message with directory path |
| Disk full | File save fails | Partial | Catch `OSError`, return "Cannot write audio file. Please check available disk space." |
| Invalid API key | 401 from API | Total | Return "Authentication failed. Please verify your SUPERTONE_API_KEY." |
| Rate limited | 429 from API | Temporary | Return rate limit message; user retries manually |
| MCP SDK bug | Server crash | Total | Pinned SDK version mitigates; user can downgrade package version |

---

## What Changes at 10x Scale

This section is included because the PRD mentions future features (v2) that could change the architecture.

| Scale trigger | Current design | What changes |
|--------------|----------------|-------------|
| Batch TTS (v2) | Single synchronous call | May need background job queue or chunked responses. Consider MCP progress notifications. |
| Streaming TTS (v2) | Full file download then save | Would need streaming write + MCP streaming support (if available). |
| Voice cloning (v2) | No upload capability | Requires file upload tool or resource, possible multipart HTTP. |
| Multiple TTS engines | Hardcoded Supertone client | Abstract client interface, factory pattern. Not needed now. |
| High request volume | Single process, no queue | Not relevant -- each MCP client spawns its own server process. Scale is inherently per-user. |

---

## Tradeoffs

| Decision | Chosen | Rejected | Rationale |
|----------|--------|----------|-----------|
| Architecture | Single-process CLI | Microservices, long-running server | MCP servers are spawned as subprocesses by clients. There is no need for a long-running process, shared state, or multi-tenancy. A single Python process is the simplest correct solution. |
| HTTP client | httpx (async) | requests (sync), aiohttp | NFR-008 requires async. httpx has the cleanest async API and is well-maintained. aiohttp would also work but httpx is simpler for this use case (no websocket needs). |
| Audio duration | `mutagen` library | Manual WAV header parsing, `pydub` | `mutagen` is lightweight, handles both WAV and MP3, has no binary dependencies (unlike `pydub` which needs ffmpeg). Manual parsing is fragile and only works for WAV. If the Supertone API returns duration in headers/metadata, `mutagen` becomes unnecessary and should be removed. |
| Output format | Plain text responses | JSON responses | UX spec mandates plain text. LLMs parse plain text well. JSON adds structure the LLM does not need and makes messages less natural when relayed to users. |
| Validation location | Client-side (in tools.py) | Server-side (in Supertone API) | Fail-fast reduces unnecessary API calls and provides consistent, user-friendly error messages. API-side validation is a backup, not the primary gate. |
| State management | Stateless (no memory between calls) | Cache voice list, session state | Stateless is simpler, matches MCP tool semantics. Voice list caching could save API calls but adds complexity (cache invalidation, memory management). Not justified for v1 where list_voices is called infrequently. |
| Default voice | Hardcoded voice ID constant | Fetch first voice at startup | Hardcoded is simpler and does not require an API call at startup. Downside: if the voice ID changes or is removed, it breaks. Mitigated by clear error message. Needs stakeholder input to determine the ID (Assumption A4). |
| Logging destination | stderr | File logging, structured JSON to file | MCP uses stdout for protocol messages. stderr is the only safe destination. File logging adds configuration complexity unnecessary for a CLI tool. |
| SDK version pinning | Pin minor version (`>=1.0,<2.0`) | Pin exact version, unpinned | Exact pin breaks on patch updates; unpinned risks breaking changes. Minor-version range balances stability with patch fixes. |

---

## Confidence Rating

**High.** The architecture is a direct reflection of the constraints: MCP servers are subprocesses, the scope is two tools wrapping two API endpoints, and there is no persistent state. The only uncertainties are in the Supertone API details (Assumptions A1-A6), which affect implementation but not architecture. The module structure is the simplest that satisfies the requirements, and every module can be tested independently with mocks.
