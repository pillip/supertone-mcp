# Issues: Supertone TTS MCP Server

> Generated: 2026-03-13
> Source: PRD, requirements.md, architecture.md, ux_spec.md, data_model.md

---

## Issue Index

| ID | Title | Priority | Estimate | Depends-On |
|----|-------|----------|----------|------------|
| ISSUE-001 | Scaffold project with uv, pyproject.toml, and src layout | P0 | 0.5d | none |
| ISSUE-002 | Define domain types, constants, and exception hierarchy | P0 | 0.5d | ISSUE-001 |
| ISSUE-003 | Implement SupertoneClient with synthesize and get_voices methods | P0 | 1d | ISSUE-002 |
| ISSUE-004 | Implement input validation and output formatting in tools module | P0 | 1d | ISSUE-002 |
| ISSUE-005 | Implement text_to_speech tool handler | P1 | 1d | ISSUE-003, ISSUE-004 |
| ISSUE-006 | Implement list_voices tool handler | P1 | 0.5d | ISSUE-003, ISSUE-004 |
| ISSUE-007 | Implement MCP server entry point and tool registration | P1 | 1d | ISSUE-005, ISSUE-006 |
| ISSUE-008 | Configure PyPI packaging and console entry point | P1 | 0.5d | ISSUE-007 |
| ISSUE-009 | Set up GitHub Actions CI pipeline | P1 | 0.5d | ISSUE-001 |
| ISSUE-010 | Write README and MCP client configuration docs | P2 | 0.5d | ISSUE-007 |
| ISSUE-011 | Create server.json and register on MCP Registry and PulseMCP | P2 | 0.5d | ISSUE-008 |

---

### ISSUE-001: Scaffold project with uv, pyproject.toml, and src layout
- Track: platform
- PRD-Ref: FR-009, FR-010
- Priority: P0
- Estimate: 0.5d
- Status: backlog
- Owner:
- Branch:
- GH-Issue:
- PR:
- Depends-On: none

#### Goal
The project has a working uv-managed Python project structure with all dependencies declared and the src layout created.

#### Scope (In/Out)
- In: `pyproject.toml` with metadata, dependencies (mcp, httpx, mutagen), dev dependencies (pytest, pytest-asyncio, pytest-cov), src/supertone_tts_mcp/ directory with `__init__.py`, tests/ directory with `__init__.py`, `.env.example`, `.gitignore`, console script entry point declaration
- Out: Implementation code, CI pipeline, README content

#### Acceptance Criteria (DoD)
- [ ] Given a fresh clone of the repo, when `uv sync` is run, then all dependencies install without error
- [ ] Given the project is initialized, when `uv run pytest -q` is run, then pytest executes successfully (0 tests collected, exit 0 or 5)
- [ ] Given `pyproject.toml` exists, when inspected, then it declares `name = "supertone-tts-mcp"`, `python >= 3.11`, dependencies `mcp`, `httpx`, `mutagen`, and dev dependencies `pytest`, `pytest-asyncio`, `pytest-cov`
- [ ] Given the src layout, when `src/supertone_tts_mcp/__init__.py` is inspected, then it contains `__version__ = "0.1.0"`
- [ ] Given `pyproject.toml`, when inspected, then a `[project.scripts]` entry maps `supertone-tts-mcp` to `supertone_tts_mcp.server:main`
- [ ] Given `.env.example` exists, when inspected, then it contains `SUPERTONE_API_KEY=your-api-key-here` and `SUPERTONE_OUTPUT_DIR=~/supertone-tts-output/` as placeholders only

#### Implementation Notes
- Use `uv init --python 3.11` then manually adjust pyproject.toml
- src layout: `src/supertone_tts_mcp/` per architecture.md
- Files to create: `pyproject.toml`, `src/supertone_tts_mcp/__init__.py`, `src/supertone_tts_mcp/server.py` (stub), `src/supertone_tts_mcp/tools.py` (stub), `src/supertone_tts_mcp/supertone_client.py` (stub), `tests/__init__.py`, `.env.example`, `.gitignore`
- Add `[tool.pytest.ini_options]` section per claude.md

#### Tests
- [ ] `uv sync` completes without error (manual verification)
- [ ] `uv run pytest -q` runs without import errors

#### Rollback
Delete generated files and revert pyproject.toml changes.

---

### ISSUE-002: Define domain types, constants, and exception hierarchy
- Track: platform
- PRD-Ref: FR-005, FR-006, FR-007, FR-008
- Priority: P0
- Estimate: 0.5d
- Status: backlog
- Owner:
- Branch:
- GH-Issue:
- PR:
- Depends-On: ISSUE-001

#### Goal
All shared types (TTSRequest, TTSResponse, VoiceInfo, AppConfig), constants (validation ranges, defaults), and domain exceptions are defined and importable.

#### Scope (In/Out)
- In: Dataclasses (TTSRequest, TTSResponse, VoiceInfo, AppConfig), Literal types (Language, OutputFormat), constants (SPEED_MIN/MAX, PITCH_SHIFT_MIN/MAX, TEXT_MAX_LENGTH, SUPPORTED_LANGUAGES, SUPPORTED_FORMATS, DEFAULT_VOICE_ID, DEFAULT_LANGUAGE, DEFAULT_FORMAT, DEFAULT_SPEED, DEFAULT_PITCH_SHIFT, HTTP_TIMEOUT, SUPERTONE_BASE_URL), TypedDicts (SynthesizeRequestBody, VoiceDict), exception classes (SupertoneError hierarchy), `generate_output_path()` utility
- Out: Validation logic, HTTP calls, MCP integration

#### Acceptance Criteria (DoD)
- [ ] Given the module is imported, when `TTSRequest(text="hi", voice_id="v1", language="ko", output_format="mp3", speed=1.0, pitch_shift=0, style=None)` is constructed, then it creates a frozen dataclass instance with all fields accessible
- [ ] Given the constants module, when `TEXT_MAX_LENGTH` is accessed, then it equals 300
- [ ] Given the constants module, when `SPEED_MIN` and `SPEED_MAX` are accessed, then they equal 0.5 and 2.0 respectively
- [ ] Given `SupertoneServerError(502)` is raised, when caught, then `e.status_code` equals 502
- [ ] Given `generate_output_path("/tmp/out", "mp3")` is called, when the result is inspected, then the path matches pattern `/tmp/out/YYYY-MM-DD_XXXXXXXX.mp3` where X is hex chars

#### Implementation Notes
- Create `src/supertone_tts_mcp/models.py` for dataclasses and TypedDicts
- Create `src/supertone_tts_mcp/constants.py` for all constants and Literal types
- Create `src/supertone_tts_mcp/exceptions.py` for the exception hierarchy
- Add `generate_output_path()` to models.py or a separate utils.py
- Follow data_model.md exactly for field definitions
- DEFAULT_VOICE_ID is "TBD" pending API spike -- use a placeholder string

#### Tests
- [ ] Test TTSRequest construction with valid fields succeeds
- [ ] Test TTSRequest is frozen (assignment raises FrozenInstanceError)
- [ ] Test TTSResponse plain-text serialization matches UX spec format
- [ ] Test VoiceInfo plain-text serialization matches UX spec format
- [ ] Test generate_output_path returns correct pattern
- [ ] Test SupertoneServerError stores status_code
- [ ] Test SupertoneAPIError stores status_code and message
- [ ] Test all exception subclasses are instances of SupertoneError

#### Rollback
Remove models.py, constants.py, exceptions.py and their test files.

---

### ISSUE-003: Implement SupertoneClient with synthesize and get_voices methods
- Track: product
- PRD-Ref: FR-001, FR-002, FR-003, FR-007
- Priority: P0
- Estimate: 1d
- Status: backlog
- Owner:
- Branch:
- GH-Issue:
- PR:
- Depends-On: ISSUE-002

#### Goal
The SupertoneClient class wraps all Supertone API HTTP communication and translates HTTP errors into domain exceptions.

#### Scope (In/Out)
- In: `SupertoneClient.__init__(api_key, base_url)`, `async synthesize(voice_id, text, language, output_format, speed, pitch_shift, style) -> tuple[bytes, str]` (audio bytes + content_type), `async get_voices() -> list[VoiceDict]`, `async aclose()`, HTTP error-to-exception mapping (401/403 -> AuthError, 429 -> RateLimitError, 5xx -> ServerError, other 4xx -> APIError, connection/timeout -> ConnectionError)
- Out: Input validation (handled in tools.py), file saving, MCP registration

#### Acceptance Criteria (DoD)
- [ ] Given a valid API key and mocked 200 response with audio bytes, when `synthesize()` is called, then it returns the audio bytes and content type
- [ ] Given a valid API key and mocked 200 response with JSON voice list, when `get_voices()` is called, then it returns a list of VoiceDict objects
- [ ] Given a mocked 401 response, when `synthesize()` is called, then `SupertoneAuthError` is raised
- [ ] Given a mocked 429 response, when `get_voices()` is called, then `SupertoneRateLimitError` is raised
- [ ] Given a mocked 503 response, when `synthesize()` is called, then `SupertoneServerError` is raised with status_code 503
- [ ] Given a mocked connection timeout, when `synthesize()` is called, then `SupertoneConnectionError` is raised
- [ ] Given the client is constructed, when the request headers are inspected, then `x-sup-api-key` is set and the API key value is never in any log output

#### Implementation Notes
- File: `src/supertone_tts_mcp/supertone_client.py`
- Use `httpx.AsyncClient` with `timeout=30.0` (HTTP_TIMEOUT constant)
- POST body uses SynthesizeRequestBody TypedDict; omit `style` key when None
- Catch `httpx.ConnectError`, `httpx.TimeoutException` -> SupertoneConnectionError
- Map response status codes in a private `_handle_error_response()` method
- Base URL from constant: `https://api.supertoneapi.com`
- Test file: `tests/test_supertone_client.py`
- All tests use `pytest-asyncio` and mock httpx responses (no real network calls)

#### Tests
- [ ] Test synthesize() returns bytes on 200 with audio/mpeg content-type
- [ ] Test synthesize() sends correct POST path `/v1/text-to-speech/{voice_id}`
- [ ] Test synthesize() sends `x-sup-api-key` header
- [ ] Test synthesize() omits `style` from body when style is None
- [ ] Test synthesize() includes `style` in body when style is provided
- [ ] Test get_voices() returns parsed list on 200
- [ ] Test get_voices() sends GET to `/v1/voices`
- [ ] Test 401 raises SupertoneAuthError
- [ ] Test 403 raises SupertoneAuthError
- [ ] Test 429 raises SupertoneRateLimitError
- [ ] Test 500 raises SupertoneServerError with status_code=500
- [ ] Test connection error raises SupertoneConnectionError
- [ ] Test timeout raises SupertoneConnectionError
- [ ] Test aclose() closes the underlying httpx client

#### Rollback
Revert `supertone_client.py` and `tests/test_supertone_client.py`.

---

### ISSUE-004: Implement input validation and output formatting in tools module
- Track: product
- PRD-Ref: FR-003, FR-004, FR-005, FR-006, FR-008
- Priority: P0
- Estimate: 1d
- Status: backlog
- Owner:
- Branch:
- GH-Issue:
- PR:
- Depends-On: ISSUE-002

#### Goal
All input validation functions and output formatting functions exist in tools.py (or a helpers module) and produce the exact error messages and output text specified in the UX spec.

#### Scope (In/Out)
- In: `validate_text(text)`, `validate_language(language)`, `validate_output_format(fmt)`, `validate_speed(speed)`, `validate_pitch_shift(pitch)`, `resolve_api_key()`, `resolve_output_dir()`, `ensure_output_dir(path)`, `format_tts_response(TTSResponse) -> str`, `format_voice_list(voices, language_filter) -> str`, `calculate_duration(file_path) -> float`
- Out: MCP tool handler glue, HTTP calls, server registration

#### Acceptance Criteria (DoD)
- [ ] Given text is empty string, when `validate_text("")` is called, then it raises ValueError with message "Text must not be empty."
- [ ] Given text has 301 characters, when `validate_text(text)` is called, then it raises ValueError with message "Text exceeds the maximum length of 300 characters (received: 301). Please shorten or split the text manually."
- [ ] Given text has exactly 300 characters, when `validate_text(text)` is called, then no error is raised
- [ ] Given language is "zz", when `validate_language("zz")` is called, then it raises ValueError with message `Invalid language: "zz". Supported languages: ko, en, ja.`
- [ ] Given speed is 5.0, when `validate_speed(5.0)` is called, then it raises ValueError with message "Speed must be between 0.5 and 2.0 (received: 5.0)."
- [ ] Given pitch_shift is 15, when `validate_pitch_shift(15)` is called, then it raises ValueError with message "Pitch shift must be between -12 and +12 semitones (received: 15)."
- [ ] Given output_format is "ogg", when `validate_output_format("ogg")` is called, then it raises ValueError with message `Invalid output format: "ogg". Supported formats: mp3, wav.`
- [ ] Given SUPERTONE_API_KEY env var is not set, when `resolve_api_key()` is called, then it raises ValueError with message "SUPERTONE_API_KEY environment variable is not set. Please configure it in your MCP client settings."
- [ ] Given SUPERTONE_OUTPUT_DIR is not set, when `resolve_output_dir()` is called, then it returns the expanded absolute path of `~/supertone-tts-output/`
- [ ] Given a TTSResponse object, when `format_tts_response()` is called, then it returns the exact plain-text format from UX spec section 4.1
- [ ] Given a list of VoiceInfo objects, when `format_voice_list()` is called, then it returns the numbered list format from UX spec section 4.2

#### Implementation Notes
- File: `src/supertone_tts_mcp/tools.py` (validation and formatting functions)
- Error messages must match UX spec Section 4.1 error states exactly (copy-paste from spec)
- `resolve_output_dir()` uses `Path.expanduser().resolve()` to return absolute path
- `ensure_output_dir()` calls `os.makedirs(path, exist_ok=True)` and catches PermissionError
- `calculate_duration()` uses `mutagen` to parse audio file and return duration in seconds
- `format_tts_response()` produces multi-line plain text per UX spec
- `format_voice_list()` produces numbered list with blank-line separators per UX spec
- File paths in output must be absolute, no `~` (UX spec 6.2)
- Test file: `tests/test_tools.py`

#### Tests
- [ ] Test validate_text with empty string returns correct error message
- [ ] Test validate_text with 301 chars returns correct error message with count
- [ ] Test validate_text with 300 chars passes
- [ ] Test validate_text with 1 char passes
- [ ] Test validate_language with each valid value passes
- [ ] Test validate_language with invalid value returns correct error message
- [ ] Test validate_output_format with "mp3" and "wav" passes
- [ ] Test validate_output_format with "ogg" returns correct error message
- [ ] Test validate_speed at boundaries (0.5, 2.0) passes
- [ ] Test validate_speed out of range (0.4, 2.1) returns correct error messages
- [ ] Test validate_pitch_shift at boundaries (-12, 12) passes
- [ ] Test validate_pitch_shift out of range (-13, 13) returns correct error messages
- [ ] Test resolve_api_key returns key when env var is set
- [ ] Test resolve_api_key raises when env var is missing
- [ ] Test resolve_api_key raises when env var is empty string
- [ ] Test resolve_output_dir returns default when env var not set
- [ ] Test resolve_output_dir returns custom path when env var is set
- [ ] Test format_tts_response produces exact UX spec format
- [ ] Test format_voice_list with 2 voices produces numbered list
- [ ] Test format_voice_list with 0 voices and language filter produces "No voices found" message
- [ ] Test format_voice_list with 0 voices and no filter produces "No voices found" message
- [ ] Test calculate_duration returns float seconds for a valid audio file (use a tiny test fixture)

#### Rollback
Revert changes to `tools.py` and `tests/test_tools.py`.

---

### ISSUE-005: Implement text_to_speech tool handler
- Track: product
- PRD-Ref: FR-001, FR-005, FR-006, FR-007, FR-008, US-001, US-003, US-004, US-005, US-006
- Priority: P1
- Estimate: 1d
- Status: backlog
- Owner:
- Branch:
- GH-Issue:
- PR:
- Depends-On: ISSUE-003, ISSUE-004

#### Goal
The `text_to_speech` async function accepts parameters, validates them, calls SupertoneClient, saves the audio file, calculates duration, and returns a formatted plain-text response or error message.

#### Scope (In/Out)
- In: `async text_to_speech(text, voice_id?, language?, output_format?, speed?, pitch_shift?, style?) -> str` function that orchestrates validation, API call, file write, duration calculation, and response formatting. Error handling that catches all domain exceptions and returns UX-spec error messages.
- Out: MCP server registration (ISSUE-007), SupertoneClient implementation (ISSUE-003), validation functions (ISSUE-004)

#### Acceptance Criteria (DoD)
- [ ] Given valid parameters and a mocked API returning audio bytes, when `text_to_speech(text="Hello")` is called, then an audio file is written to the output directory and the response contains the absolute file path and duration in seconds
- [ ] Given voice_id is not provided, when `text_to_speech(text="Hello")` is called, then the default voice ID is used
- [ ] Given text exceeds 300 characters, when `text_to_speech(text=long_text)` is called, then the validation error message is returned without any API call being made
- [ ] Given the API returns 401, when `text_to_speech(text="Hello")` is called, then the response is "Authentication failed. Please verify your SUPERTONE_API_KEY."
- [ ] Given the API returns 429, when `text_to_speech(text="Hello")` is called, then the response is "Rate limit exceeded. Please wait and try again."
- [ ] Given a network error occurs, when `text_to_speech(text="Hello")` is called, then the response is "Failed to connect to Supertone API. Please check your network connection."
- [ ] Given the output directory cannot be created due to permissions, when `text_to_speech(text="Hello")` is called, then a clear permissions error is returned with the directory path
- [ ] Given the response, when the file path is inspected, then it is absolute (no `~`) and matches the naming pattern `{YYYY-MM-DD}_{uuid8hex}.{format}`

#### Implementation Notes
- File: `src/supertone_tts_mcp/tools.py` (add the `text_to_speech` handler function)
- Orchestration flow per data_model.md "Pattern: text_to_speech"
- Catch ValueError from validation, SupertoneError subclasses from client, OSError from file writes
- All error paths return a string (not raise) -- MCP tools return text responses
- Use `generate_output_path()` from ISSUE-002
- Use `calculate_duration()` from ISSUE-004
- Use `format_tts_response()` from ISSUE-004
- Test file: `tests/test_tools.py` (extend)

#### Tests
- [ ] Test happy path: valid input -> file saved, response contains path and duration
- [ ] Test default voice_id is applied when omitted
- [ ] Test default language "ko" is applied when omitted
- [ ] Test default output_format "mp3" is applied when omitted
- [ ] Test default speed 1.0 and pitch_shift 0 are applied when omitted
- [ ] Test validation error for empty text returns error string (not exception)
- [ ] Test validation error for invalid language returns error string
- [ ] Test SupertoneAuthError is caught and formatted correctly
- [ ] Test SupertoneRateLimitError is caught and formatted correctly
- [ ] Test SupertoneServerError is caught and formatted with status code
- [ ] Test SupertoneConnectionError is caught and formatted correctly
- [ ] Test PermissionError on output dir is caught and formatted correctly
- [ ] Test file is written with correct bytes from API response

#### Rollback
Revert text_to_speech handler code and related tests.

---

### ISSUE-006: Implement list_voices tool handler
- Track: product
- PRD-Ref: FR-002, FR-007, US-002, US-003, US-007
- Priority: P1
- Estimate: 0.5d
- Status: backlog
- Owner:
- Branch:
- GH-Issue:
- PR:
- Depends-On: ISSUE-003, ISSUE-004

#### Goal
The `list_voices` async function accepts an optional language filter, calls SupertoneClient, filters results, and returns a formatted plain-text voice list or error message.

#### Scope (In/Out)
- In: `async list_voices(language?) -> str` function that validates language filter, calls `get_voices()`, filters by language, and formats the result using `format_voice_list()`. Error handling for domain exceptions.
- Out: MCP server registration (ISSUE-007)

#### Acceptance Criteria (DoD)
- [ ] Given a mocked API returning 3 voices, when `list_voices()` is called with no filter, then the response contains all 3 voices in numbered list format
- [ ] Given a mocked API returning 3 voices (2 Korean, 1 Japanese), when `list_voices(language="ko")` is called, then only the 2 Korean voices are returned
- [ ] Given a mocked API returning 0 voices, when `list_voices()` is called, then the response is "No voices found." (not an error)
- [ ] Given language filter is "zz", when `list_voices(language="zz")` is called, then the validation error message is returned
- [ ] Given the API returns 401, when `list_voices()` is called, then the response is "Authentication failed. Please verify your SUPERTONE_API_KEY."

#### Implementation Notes
- File: `src/supertone_tts_mcp/tools.py` (add the `list_voices` handler function)
- Filtering: iterate voices, check if `language` is in `voice.supported_languages`
- Use `format_voice_list()` from ISSUE-004
- Catch ValueError from validation, SupertoneError subclasses from client
- Test file: `tests/test_tools.py` (extend)

#### Tests
- [ ] Test happy path: no filter returns all voices formatted
- [ ] Test language filter returns only matching voices
- [ ] Test empty result returns "No voices found" message
- [ ] Test invalid language filter returns error string
- [ ] Test SupertoneAuthError is caught and formatted correctly
- [ ] Test SupertoneConnectionError is caught and formatted correctly

#### Rollback
Revert list_voices handler code and related tests.

---

### ISSUE-007: Implement MCP server entry point and tool registration
- Track: product
- PRD-Ref: FR-009, NFR-002
- Priority: P1
- Estimate: 1d
- Status: backlog
- Owner:
- Branch:
- GH-Issue:
- PR:
- Depends-On: ISSUE-005, ISSUE-006

#### Goal
The MCP server starts via `supertone-tts-mcp` command, registers both tools with correct schemas, and handles tool calls over stdio transport.

#### Scope (In/Out)
- In: `server.py` with `main()` function that creates MCP Server instance, registers `text_to_speech` and `list_voices` as tools with parameter schemas and descriptions matching UX spec, runs stdio transport. Tool descriptions and parameter descriptions must match UX spec Section 2.1 and 2.2 exactly.
- Out: PyPI publishing, CI pipeline

#### Acceptance Criteria (DoD)
- [ ] Given the package is installed, when `supertone-tts-mcp` command is run, then the MCP server starts and listens on stdio
- [ ] Given the server is running, when a `tools/list` request is sent, then both `text_to_speech` and `list_voices` are returned with correct schemas
- [ ] Given the server is running, when the `text_to_speech` tool schema is inspected, then the description matches UX spec: "Convert text to speech using Supertone TTS API. Saves the audio file locally and returns the file path and duration. Supports Korean, English, and Japanese. Maximum 300 characters per call."
- [ ] Given the server is running, when the `list_voices` tool schema is inspected, then the description matches UX spec: "List available Supertone TTS voices. Returns voice ID, name, supported languages, and supported emotion styles for each voice. Optionally filter by language."
- [ ] Given a `text_to_speech` tool call with `{"text": "Hello"}`, when processed, then the `text_to_speech` handler from tools.py is invoked and the result is returned
- [ ] Given the server, when `python -m supertone_tts_mcp` is run, then the server also starts (alternative entry point)

#### Implementation Notes
- File: `src/supertone_tts_mcp/server.py`
- Use MCP Python SDK: `from mcp.server import Server` and `server.run_stdio()`
- Register tools using `@server.tool()` decorator or `server.add_tool()` method
- Parameter schemas must include types, descriptions, required fields, enums, and ranges
- `text` parameter is required; all others are optional with defaults
- Add `__main__.py` for `python -m` support
- Logging to stderr (stdout reserved for MCP protocol)
- Test file: `tests/test_server.py`
- Integration test: can use MCP SDK test client or mock stdio

#### Tests
- [ ] Test server registers exactly 2 tools
- [ ] Test text_to_speech tool schema has correct parameter names and types
- [ ] Test text_to_speech tool has `text` marked as required
- [ ] Test list_voices tool schema has `language` as optional parameter
- [ ] Test tool descriptions match UX spec exactly
- [ ] Test main() function is callable without error (with mocked stdio)
- [ ] Test __main__.py module exists and calls main()

#### Rollback
Revert `server.py`, `__main__.py`, and `tests/test_server.py`.

---

### ISSUE-008: Configure PyPI packaging and console entry point
- Track: platform
- PRD-Ref: FR-010, NFR-001
- Priority: P1
- Estimate: 0.5d
- Status: backlog
- Owner:
- Branch:
- GH-Issue:
- PR:
- Depends-On: ISSUE-007

#### Goal
The package builds successfully with `uv build` and the resulting distribution installs with `pip install` and makes the `supertone-tts-mcp` command available.

#### Scope (In/Out)
- In: Complete pyproject.toml metadata (name, version, description, author, license, URLs, classifiers, python-requires), verify `[project.scripts]` entry, `uv build` produces working sdist and wheel, verify `pip install dist/*.whl` makes `supertone-tts-mcp` command available
- Out: Actual PyPI publishing (manual step), CI publish workflow (ISSUE-009)

#### Acceptance Criteria (DoD)
- [ ] Given the project, when `uv build` is run, then a `.whl` and `.tar.gz` are created in `dist/`
- [ ] Given the built wheel, when installed with `pip install dist/*.whl` in a fresh venv, then `supertone-tts-mcp` command is available and starts the server
- [ ] Given pyproject.toml, when inspected, then it contains: description, author, license (MIT), python_requires >= 3.11, project URLs (repository, homepage)
- [ ] Given pyproject.toml, when inspected, then classifiers include Python 3.11, 3.12, 3.13

#### Implementation Notes
- Update pyproject.toml with full metadata
- Verify console_scripts entry works end-to-end
- Test with `uv build` then local install
- Add `long_description` pointing to README.md with content-type text/markdown

#### Tests
- [ ] `uv build` succeeds without error (manual verification)
- [ ] Local wheel install creates working `supertone-tts-mcp` command (manual verification)

#### Rollback
Revert pyproject.toml metadata changes.

---

### ISSUE-009: Set up GitHub Actions CI pipeline
- Track: platform
- PRD-Ref: NFR-005, NFR-006
- Priority: P1
- Estimate: 0.5d
- Status: backlog
- Owner:
- Branch:
- GH-Issue:
- PR:
- Depends-On: ISSUE-001

#### Goal
A GitHub Actions workflow runs tests on push and PR across Python 3.11, 3.12, and 3.13, and a publish job triggers on version tags.

#### Scope (In/Out)
- In: `.github/workflows/ci.yml` with test matrix (3.11, 3.12, 3.13), `uv sync` + `uv run pytest -q --cov=src --cov-report=term-missing`, publish job on `v*` tags using `uv build` + `uv publish`
- Out: Actual PyPI token setup (manual), MCP registry steps

#### Acceptance Criteria (DoD)
- [ ] Given a push to any branch, when GitHub Actions runs, then the test job executes on Python 3.11, 3.12, and 3.13
- [ ] Given the CI workflow, when the test step is inspected, then it runs `uv sync` followed by `uv run pytest -q --cov=src --cov-report=term-missing`
- [ ] Given a tag matching `v*` is pushed, when GitHub Actions runs, then the publish job builds and publishes to PyPI using `UV_PUBLISH_TOKEN` secret
- [ ] Given the publish job, when inspected, then it depends on the test job passing (needs: test)

#### Implementation Notes
- File: `.github/workflows/ci.yml`
- Use `actions/checkout@v4` and `astral-sh/setup-uv@v4`
- Per architecture.md CI/CD Pipeline Outline
- Publish step uses `UV_PUBLISH_TOKEN` from repository secrets

#### Tests
- [ ] CI YAML is valid (use actionlint or manual review)
- [ ] Workflow triggers on push and pull_request events

#### Rollback
Delete `.github/workflows/ci.yml`.

---

### ISSUE-010: Write README and MCP client configuration docs
- Track: product
- PRD-Ref: FR-009, NFR-001, NFR-002
- Priority: P2
- Estimate: 0.5d
- Status: backlog
- Owner:
- Branch:
- GH-Issue:
- PR:
- Depends-On: ISSUE-007

#### Goal
The README.md contains installation instructions, Claude Desktop and Cursor configuration examples, usage examples, and environment variable documentation.

#### Scope (In/Out)
- In: README.md with: project description, features list, installation (`uvx supertone-tts-mcp`, `pip install supertone-tts-mcp`), Claude Desktop config JSON example (from PRD 8.4), Cursor config example, environment variables table (SUPERTONE_API_KEY, SUPERTONE_OUTPUT_DIR), usage examples, license
- Out: MCP registry registration (ISSUE-011)

#### Acceptance Criteria (DoD)
- [ ] Given the README, when inspected, then it contains a working Claude Desktop configuration JSON with `"command": "uvx"` and `"args": ["supertone-tts-mcp"]`
- [ ] Given the README, when inspected, then it documents both environment variables with their defaults and descriptions
- [ ] Given the README, when inspected, then it includes at least one usage example showing a natural language prompt and expected output
- [ ] Given the README, when inspected, then it lists supported languages (ko, en, ja) and parameter ranges

#### Implementation Notes
- Include the `mcp-name: io.github.pillip/supertone-tts` metadata line for MCP Registry
- Reference PRD Section 8.4 for Claude Desktop config format
- Keep it concise -- developers are the audience

#### Tests
- [ ] README renders correctly on GitHub (manual verification)
- [ ] All code blocks in README use correct syntax highlighting tags

#### Rollback
Revert README.md changes.

---

### ISSUE-011: Create server.json and register on MCP Registry and PulseMCP
- Track: product
- PRD-Ref: FR-011
- Priority: P2
- Estimate: 0.5d
- Status: backlog
- Owner:
- Branch:
- GH-Issue:
- PR:
- Depends-On: ISSUE-008

#### Goal
The server is registered and searchable on the official MCP Registry and listed on PulseMCP.

#### Scope (In/Out)
- In: `server.json` file with correct schema, name (`io.github.pillip/supertone-tts`), description, version, and PyPI package reference. Registration on MCP Registry via `mcp-publisher publish`. Self-registration on PulseMCP.
- Out: Ongoing maintenance of registry listings

#### Acceptance Criteria (DoD)
- [ ] Given `server.json`, when validated against the MCP server schema, then it passes validation
- [ ] Given `server.json`, when inspected, then the name is `io.github.pillip/supertone-tts` and the package identifier is `supertone-tts-mcp` with registry_type `pypi`
- [ ] Given `mcp-publisher publish` is run, when the MCP Registry is searched for "supertone", then the server appears in results
- [ ] Given PulseMCP self-registration is completed, when the PulseMCP directory is searched, then the server is listed

#### Implementation Notes
- File: `server.json` in project root
- Follow PRD Section 8.5 for server.json format
- Use `mcp-publisher` CLI for MCP Registry
- PulseMCP registration is manual via their web form at pulsemcp.com
- This issue is blocked until PyPI publishing (ISSUE-008) is complete

#### Tests
- [ ] server.json is valid JSON matching the schema (manual or automated validation)
- [ ] Server is searchable on MCP Registry (manual verification post-publish)

#### Rollback
Remove server.json, contact MCP Registry to delist if needed.

---

## Dependency Graph

```
ISSUE-001 (Scaffold)
  |
  +-- ISSUE-002 (Types/Constants/Exceptions)
  |     |
  |     +-- ISSUE-003 (SupertoneClient)  [can parallel with ISSUE-004]
  |     |     |
  |     +-- ISSUE-004 (Validation/Formatting)  [can parallel with ISSUE-003]
  |           |
  |           +-- ISSUE-005 (text_to_speech handler)  [needs 003 + 004]
  |           |     |
  |           +-- ISSUE-006 (list_voices handler)  [needs 003 + 004, can parallel with 005]
  |                 |
  |                 +-- ISSUE-007 (MCP Server)  [needs 005 + 006]
  |                       |
  |                       +-- ISSUE-008 (PyPI Packaging)
  |                       |     |
  |                       |     +-- ISSUE-011 (Registry)
  |                       |
  |                       +-- ISSUE-010 (README)
  |
  +-- ISSUE-009 (CI)  [only needs 001, can parallel with everything]
```

**Critical path:** 001 -> 002 -> 003/004 (parallel) -> 005/006 (parallel) -> 007 -> 008 -> 011

**Maximum parallelism:**
- After ISSUE-001: ISSUE-002 and ISSUE-009 can run in parallel
- After ISSUE-002: ISSUE-003 and ISSUE-004 can run in parallel
- After ISSUE-003+004: ISSUE-005 and ISSUE-006 can run in parallel
- After ISSUE-007: ISSUE-008, ISSUE-010 can run in parallel

---

## Requirement Coverage Check

| Requirement | Covered by |
|-------------|-----------|
| FR-001 | ISSUE-003, ISSUE-005 |
| FR-002 | ISSUE-003, ISSUE-006 |
| FR-003 | ISSUE-003, ISSUE-004 |
| FR-004 | ISSUE-004, ISSUE-005 |
| FR-005 | ISSUE-004, ISSUE-005 |
| FR-006 | ISSUE-004, ISSUE-005 |
| FR-007 | ISSUE-003, ISSUE-005, ISSUE-006 |
| FR-008 | ISSUE-002, ISSUE-005 |
| FR-009 | ISSUE-001, ISSUE-007 |
| FR-010 | ISSUE-008 |
| FR-011 | ISSUE-011 |
| US-001 | ISSUE-005 |
| US-002 | ISSUE-006 |
| US-003 | ISSUE-004, ISSUE-005, ISSUE-006 |
| US-004 | ISSUE-004, ISSUE-005 |
| US-005 | ISSUE-005 |
| US-006 | ISSUE-004, ISSUE-005 |
| US-007 | ISSUE-006 |
| NFR-001 | ISSUE-008 |
| NFR-002 | ISSUE-007 |
| NFR-003 | ISSUE-005, ISSUE-006 |
| NFR-004 | ISSUE-004, ISSUE-005, ISSUE-006 |
| NFR-005 | All issues include tests |
| NFR-006 | ISSUE-009 |
| NFR-007 | ISSUE-003, ISSUE-004 |
| NFR-008 | ISSUE-003 |

**Orphaned requirements:** None. All FRs, user stories, and NFRs are covered.

---

## Confidence Rating

**High.** The project scope is small and well-defined (2 tools, 3 modules, no database). Architecture and data model documents are detailed with exact type definitions and error messages. The only uncertainties are Supertone API specifics (Assumptions A1-A6), which affect implementation details within ISSUE-003 but not the issue decomposition or dependencies.
