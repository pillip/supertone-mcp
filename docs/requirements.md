# Requirements: Supertone TTS MCP Server

> Generated: 2026-03-13
> Source: PRD v0.1 (Draft, 2026-03-13)
> Analyst: requirements-analyst agent

---

## Goals (from PRD)

| ID | Goal | Measurement |
|----|------|-------------|
| G1 | Acquire MCP server development capability | A working server that conforms to the MCP standard |
| G2 | Bring Supertone TTS into the MCP ecosystem | Verified operation on Claude Desktop and Cursor |
| G3 | Publish as open-source to attract external users | Public GitHub repo + published on PyPI |

---

## Primary User

**MCP users (developers / creators)** who use MCP-compatible clients (Claude Desktop, Cursor, OpenClaw, etc.) and want to convert text to speech within their LLM workflow.

**Secondary:** Content creators who need high-quality Korean narration/dubbing and want to automate it inside an LLM pipeline.

---

## User Stories (prioritized)

### Must

#### US-001: Basic Text-to-Speech
**As an** MCP user, **I want** to input text and generate a speech audio file via Supertone TTS, **so that** I can listen to typed content as spoken audio.

**Acceptance Criteria:**
- [x] Given the MCP server is running and `SUPERTONE_API_KEY` is set, when the user calls `text_to_speech` with `text="Hello"`, then an audio file is saved to the output directory and the file path is returned.
- [x] Given valid input, when the tool completes, then the response includes the file path (absolute) and audio duration in seconds.
- [x] Given `text` is empty (zero-length string), when the tool is called, then an error message is returned indicating text must not be empty.
- [x] Given `text` exceeds 300 characters, when the tool is called, then an error is returned without automatic splitting, instructing the user to shorten the text.

#### US-002: List Available Voices
**As an** MCP user, **I want** to query the list of available voices, **so that** I can choose a voice for TTS.

**Acceptance Criteria:**
- [x] Given the server is running and API key is valid, when the user calls `list_voices` with no parameters, then a list of all voices is returned.
- [x] Each voice entry includes: `voice_id`, name, supported languages, and supported styles.
- [x] Given no voices match (e.g., API returns empty list), then an empty list is returned with no error.

#### US-003: Specify Language
**As an** MCP user, **I want** to specify the speech language (`ko`, `en`, `ja`), **so that** I can create multilingual content.

**Acceptance Criteria:**
- [x] Given `language="en"` is passed to `text_to_speech`, when the API is called, then the generated audio is in English.
- [x] Given no `language` parameter is provided, then `ko` is used as the default.
- [x] Given an unsupported language code (e.g., `language="zz"`), then an error is returned listing valid options (`ko`, `en`, `ja`).
- [x] Given `language="ja"` is passed to `list_voices`, then only Japanese-capable voices are returned.

### Should

#### US-004: Adjust Speed and Pitch
**As an** MCP user, **I want** to control speech speed and pitch, **so that** I can tailor the audio to my use case.

**Acceptance Criteria:**
- [x] Given `speed=1.5` is passed, then the generated audio plays at 1.5x speed.
- [x] Given `speed` is outside the range 0.5--2.0, then an error is returned stating the valid range.
- [x] Given `pitch_shift=3` is passed, then the audio pitch is shifted up by 3 semitones.
- [x] Given `pitch_shift` is outside the range -12 to +12, then an error is returned stating the valid range.
- [x] Given neither `speed` nor `pitch_shift` is provided, then defaults of `1.0` and `0` are used respectively.

#### US-005: Specify Emotion Style
**As an** MCP user, **I want** to set an emotion style (e.g., `neutral`, `happy`), **so that** I can create expressive speech.

**Acceptance Criteria:**
- [x] Given `style="happy"` is passed and the selected voice supports it, then the audio is generated with the happy style.
- [x] Given `style` is not provided, then the voice's default style is used.
- [x] Given an unsupported `style` value for the selected voice, then an error is returned indicating which styles are available for that voice.

#### US-006: Choose Output Format
**As an** MCP user, **I want** to select the output format (`wav` or `mp3`), **so that** I can get a file suitable for my purpose.

**Acceptance Criteria:**
- [x] Given `output_format="wav"` is passed, then the saved file has a `.wav` extension and contains valid WAV data.
- [x] Given `output_format` is not provided, then `mp3` is used as the default.
- [x] Given an invalid format (e.g., `output_format="ogg"`), then an error is returned listing valid options (`wav`, `mp3`).

### Could

#### US-007: Filter Voices by Language
**As an** MCP user, **I want** to filter the voice list by language, **so that** I only see voices relevant to my needs.

**Acceptance Criteria:**
- [x] Given `language="ko"` is passed to `list_voices`, then only voices supporting Korean are returned.
- [x] Given an unsupported language filter, then an error is returned listing valid language codes.

> Note: This is partially covered by US-003 AC for `list_voices`. Separated here for traceability.

---

## Functional Requirements

### Feature Area: TTS Core

#### FR-001: `text_to_speech` MCP Tool
- **Description:** Expose an MCP tool named `text_to_speech` that calls the Supertone API (`POST /v1/text-to-speech/{voice_id}`) and saves the resulting audio to a local file.
- **Priority:** Must
- **Parameters:** `text` (required), `voice_id`, `language`, `output_format`, `speed`, `pitch_shift`, `style` (all optional with defaults).
- **Acceptance Criteria:**
  - The tool is registered in the MCP server and discoverable by MCP clients.
  - The tool calls the Supertone API with correct headers (`x-sup-api-key`) and parameters.
  - The audio binary stream from the API is written to a file in the output directory.
  - The returned result is a text message containing the absolute file path and duration in seconds.
  - The file is named with a timestamp and unique identifier (e.g., `2026-03-13_abc123.mp3`).
- **Dependencies:** FR-003 (authentication).

#### FR-002: `list_voices` MCP Tool
- **Description:** Expose an MCP tool named `list_voices` that queries the Supertone API (`GET /v1/voices`) and returns voice metadata.
- **Priority:** Must
- **Parameters:** `language` (optional filter).
- **Acceptance Criteria:**
  - The tool is registered in the MCP server and discoverable by MCP clients.
  - Returns a structured list where each entry has: `voice_id`, `name`, `supported_languages`, `supported_styles`.
  - When `language` filter is provided, only matching voices are returned.
  - When no voices exist or API returns empty, the tool returns an empty list (not an error).
- **Dependencies:** FR-003 (authentication).

### Feature Area: Configuration and Authentication

#### FR-003: API Key Authentication
- **Description:** Authenticate with the Supertone API using an API key provided via the `SUPERTONE_API_KEY` environment variable.
- **Priority:** Must
- **Acceptance Criteria:**
  - On server startup, if `SUPERTONE_API_KEY` is not set or is empty, the server starts but each tool call returns a clear error: "SUPERTONE_API_KEY environment variable is not set. Please configure it in your MCP client settings."
  - The API key is sent as the `x-sup-api-key` HTTP header on every API request.
  - The API key is never logged or included in error messages returned to the user.
- **Dependencies:** None.

#### FR-004: Output Directory Configuration
- **Description:** Allow users to configure the output directory for saved audio files via the `SUPERTONE_OUTPUT_DIR` environment variable.
- **Priority:** Must
- **Acceptance Criteria:**
  - If `SUPERTONE_OUTPUT_DIR` is set, files are saved to that directory.
  - If `SUPERTONE_OUTPUT_DIR` is not set, files are saved to `~/supertone-tts-output/`.
  - If the output directory does not exist, it is created automatically (including intermediate directories).
  - If the directory cannot be created (permissions), a clear error is returned.
- **Dependencies:** None.

### Feature Area: Input Validation

#### FR-005: Text Length Validation
- **Description:** Validate that input text does not exceed 300 characters.
- **Priority:** Must
- **Acceptance Criteria:**
  - Given text with exactly 300 characters, the tool proceeds normally.
  - Given text with 301+ characters, the tool returns an error: "Text exceeds the maximum length of 300 characters (received: {N}). Please shorten or split the text manually."
  - Given an empty string, the tool returns an error: "Text must not be empty."
  - The system must NOT automatically split text that exceeds 300 characters.
- **Dependencies:** FR-001.

#### FR-006: Parameter Validation
- **Description:** Validate all optional parameters against their allowed values/ranges before making API calls.
- **Priority:** Must
- **Acceptance Criteria:**
  - `language` must be one of `ko`, `en`, `ja`. Invalid values return an error listing valid options.
  - `output_format` must be one of `wav`, `mp3`. Invalid values return an error listing valid options.
  - `speed` must be a number in range [0.5, 2.0]. Out-of-range values return an error stating the valid range.
  - `pitch_shift` must be a number in range [-12, +12]. Out-of-range values return an error stating the valid range.
  - All validation happens before any API call is made (fail-fast).
- **Dependencies:** FR-001.

### Feature Area: Error Handling

#### FR-007: API Error Propagation
- **Description:** Propagate Supertone API errors to the user with actionable information.
- **Priority:** Must
- **Acceptance Criteria:**
  - On HTTP 401/403, return: "Authentication failed. Please verify your SUPERTONE_API_KEY."
  - On HTTP 429, return: "Rate limit exceeded. Please wait and try again."
  - On HTTP 4xx (other), return the HTTP status code and the error message from the API response body.
  - On HTTP 5xx, return: "Supertone API server error ({status_code}). Please try again later."
  - On network timeout or connection error, return: "Failed to connect to Supertone API. Please check your network connection."
- **Dependencies:** FR-001, FR-002.

### Feature Area: Default Voice

#### FR-008: Default Voice Fallback
- **Description:** When `voice_id` is not provided to `text_to_speech`, use a default voice.
- **Priority:** Must
- **Acceptance Criteria:**
  - When `voice_id` is omitted, a pre-configured default voice ID is used.
  - The default voice supports at least the Korean language.
- **Dependencies:** FR-001.
- **Assumption:** PRD does not specify which voice ID is the default. This must be determined by inspecting the Supertone API documentation or selecting the first available Korean voice. **Verify with stakeholder.**

### Feature Area: Server Infrastructure

#### FR-009: MCP Server Entry Point
- **Description:** Implement an MCP server using the official MCP Python SDK that registers `text_to_speech` and `list_voices` as tools.
- **Priority:** Must
- **Acceptance Criteria:**
  - The server can be started via `uvx supertone-tts-mcp` or `python -m supertone_tts_mcp`.
  - The server communicates over stdio transport (standard for MCP CLI-based servers).
  - Both tools are listed when the client sends a `tools/list` request.
  - Tool schemas (parameter names, types, descriptions) are correctly exposed.
- **Dependencies:** None.

#### FR-010: PyPI Package
- **Description:** Package the server as `supertone-tts-mcp` on PyPI with a console entry point.
- **Priority:** Must
- **Acceptance Criteria:**
  - `pip install supertone-tts-mcp` installs the package and makes the `supertone-tts-mcp` command available.
  - `uvx supertone-tts-mcp` runs the server without prior installation.
  - The package has correct metadata (name, version, description, author, license).
- **Dependencies:** FR-009.

#### FR-011: MCP Registry Registration
- **Description:** Register the server on the official MCP Registry and PulseMCP.
- **Priority:** Should
- **Acceptance Criteria:**
  - A valid `server.json` file exists with correct schema, name (`io.github.pillip/supertone-tts`), description, and package reference.
  - The server is searchable on the official MCP Registry.
  - The server is listed on PulseMCP.
- **Dependencies:** FR-010.

---

## Non-functional Requirements

#### NFR-001: Installation Simplicity
- **Description:** The server must be installable with a single command.
- **Measurable Target:** `uvx supertone-tts-mcp` or `pip install supertone-tts-mcp` completes successfully in under 60 seconds on a standard broadband connection.
- **Priority:** Must

#### NFR-002: MCP Protocol Compliance
- **Description:** The server must conform to the MCP specification and work with major MCP clients.
- **Measurable Target:** Passes integration tests with Claude Desktop and Cursor (both tools callable and returning valid results).
- **Priority:** Must

#### NFR-003: Server-side Latency
- **Description:** The MCP server must introduce minimal overhead beyond the Supertone API response time.
- **Measurable Target:** Server-side processing overhead (excluding Supertone API call and file I/O) < 100ms at p95.
- **Priority:** Must

#### NFR-004: Error Message Quality
- **Description:** All error messages must be understandable by non-technical users and actionable.
- **Measurable Target:** Every error path returns a message that (a) states what went wrong, (b) suggests a fix or next step. No raw stack traces or internal error codes exposed to users.
- **Priority:** Must

#### NFR-005: Test Coverage
- **Description:** Automated tests must cover core functionality.
- **Measurable Target:**
  - pytest-based unit tests exist for all tools and the Supertone client wrapper.
  - All external API calls are mocked in tests (no real network calls in CI).
  - Test files: `tests/test_tools.py`, `tests/test_supertone_client.py`.
  - Minimum test count: at least 1 test per tool, 1 test per error path for FR-007.
- **Priority:** Must

#### NFR-006: Python Version Compatibility
- **Description:** The server must run on Python 3.11 and above.
- **Measurable Target:** CI passes on Python 3.11 and 3.12+.
- **Priority:** Must

#### NFR-007: Security -- API Key Handling
- **Description:** API keys must not be leaked.
- **Measurable Target:**
  - API key is read from environment variable only, never from config files committed to the repo.
  - API key is never printed in logs, error messages, or MCP tool responses.
  - `.env.example` contains only a placeholder value.
- **Priority:** Must

#### NFR-008: Async HTTP
- **Description:** HTTP calls to the Supertone API must be asynchronous.
- **Measurable Target:** Uses `httpx.AsyncClient` for all API calls. No blocking I/O on the event loop.
- **Priority:** Should

---

## Out of Scope

The following are explicitly excluded from this version (v1) per PRD Section 3:

1. **STT (Speech-to-Text)** -- incompatible with MCP's tool-calling architecture.
2. **Voice conversation interface** (STT -> LLM -> TTS pipeline) -- separate project.
3. **Voice cloning** (`clone_voice`) -- deferred to v2.
4. **Batch conversion** (`batch_tts`) -- deferred to v2.
5. **Duration prediction** (`predict_duration`) -- deferred to v2.
6. **Credit balance check** (`check_credits`) -- deferred to v2.
7. **Streaming TTS** -- deferred to v2.
8. **Automatic text splitting** for 300+ characters -- deferred to v2.
9. **Web UI or standalone client application**.
10. **Support for TTS engines other than Supertone**.
11. **Audio playback within the MCP response** -- MCP does not support binary streaming; file path is returned instead.
12. **Rate limiting or request queuing on the MCP server side** -- PRD does not mention this; users are subject to Supertone API rate limits directly.
13. **User authentication / multi-tenancy on the MCP server** -- single-user, single API key model.

---

## Assumptions

| ID | Assumption | Risk if Wrong |
|----|-----------|---------------|
| A1 | The Supertone API base URL is `https://api.supertoneapi.com`. PRD states "docs에서 확인 필요" (needs verification from docs). **Verify with stakeholder.** | API calls fail; requires code change to fix URL. |
| A2 | The voice listing endpoint is `GET /v1/voices`. PRD states this is an estimate ("추정"). **Verify with stakeholder.** | `list_voices` tool will not work. |
| A3 | The Supertone API returns audio duration in its response headers or metadata. PRD requires returning duration but does not specify how it is obtained. **Verify with stakeholder.** If the API does not return duration, it must be calculated from the audio file (e.g., parsing WAV headers or using a library). | Additional dependency required (e.g., `mutagen` or `pydub`) if duration must be computed locally. |
| A4 | A sensible default `voice_id` exists and can be hardcoded or fetched at startup. PRD says "미지정 시 기본 보이스 사용" but does not specify which voice. **Verify with stakeholder.** | If no default is provided, the tool may fail when `voice_id` is omitted. |
| A5 | The `style` parameter values (e.g., `neutral`, `happy`) are per-voice and can be discovered from the `list_voices` response. | If the API does not expose available styles per voice, validation of the `style` parameter is not possible and must be passed through as-is. |
| A6 | The Supertone API supports `speed` and `pitch_shift` parameters as described. PRD lists them but they may not map directly to API parameters. **Verify against actual API documentation.** | Parameters silently ignored or cause API errors. |
| A7 | MCP stdio transport is sufficient for Claude Desktop and Cursor integration. No SSE or HTTP transport is needed for v1. | Would need to implement additional transport layer. |
| A8 | The file naming pattern `{date}_{unique_id}.{format}` is acceptable. PRD shows `2026-03-13_abc123.mp3` as an example but does not formalize the pattern. | No user impact; cosmetic only. |

---

## Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|-----------|--------|------------|
| R1 | Supertone API documentation is incomplete or inaccurate (base URL, endpoints, parameters). | High | High | Perform M1 (API spike) first. Validate all endpoints with real API calls before building the MCP wrapper. |
| R2 | Supertone API does not return audio duration, requiring local computation. | Medium | Low | Add `mutagen` or equivalent as optional dependency; compute duration from file if API does not provide it. |
| R3 | MCP SDK introduces breaking changes (ecosystem is young and fast-moving). | Medium | Medium | Pin `mcp` SDK version in `pyproject.toml`. Monitor SDK changelog. |
| R4 | Rate limits (20-60 req/min) may frustrate users generating multiple audio files. | Medium | Medium | Out of scope for v1 but document the limitation clearly in README. Consider queuing in v2. |
| R5 | The `style` parameter may not be supported by all voices, leading to confusing errors. | Medium | Low | Validate `style` against `list_voices` data when possible; return clear error otherwise. |
| R6 | PyPI package name `supertone-tts-mcp` may already be taken. | Low | High | Check name availability before development. Have fallback names ready. |
| R7 | File system permissions prevent writing to the output directory on some OS configurations. | Low | Medium | Catch permission errors explicitly and return actionable error message (FR-004). |

---

## Success Metrics (quantitative, measurable)

| ID | Metric | Target | Timeframe |
|----|--------|--------|-----------|
| SM-001 | GitHub stars | >= 50 | 3 months post-launch |
| SM-002 | PyPI downloads | >= 200 | 3 months post-launch |
| SM-003 | MCP Registry listing | Registered and searchable | At launch |
| SM-004 | Client compatibility | Verified on Claude Desktop AND Cursor | At launch |
| SM-005 | Unit test count | >= 10 tests covering tools, client, and error paths | At launch |
| SM-006 | Test pass rate | 100% in CI | Continuous |

---

## Traceability Matrix

| User Story | Functional Requirements | NFRs |
|-----------|------------------------|------|
| US-001 | FR-001, FR-003, FR-004, FR-005, FR-007, FR-008 | NFR-003, NFR-004, NFR-008 |
| US-002 | FR-002, FR-003, FR-007 | NFR-004 |
| US-003 | FR-001, FR-002, FR-006 | NFR-004 |
| US-004 | FR-001, FR-006 | NFR-004 |
| US-005 | FR-001, FR-006 | NFR-004 |
| US-006 | FR-001, FR-006 | NFR-004 |
| US-007 | FR-002 | NFR-004 |
| -- | FR-009, FR-010, FR-011 | NFR-001, NFR-002, NFR-005, NFR-006, NFR-007 |
