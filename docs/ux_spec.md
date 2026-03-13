# UX Specification: Supertone TTS MCP Server

> Generated: 2026-03-13
> Source: PRD v0.1, Requirements v0.1
> Author: ux-designer agent

---

## 1. Information Architecture

This MCP server exposes exactly two tools. The tool surface is intentionally minimal -- users interact through natural language in their MCP client (Claude Desktop, Cursor), and the LLM translates intent into tool calls.

### Tool Hierarchy

```
supertone-tts (MCP Server)
|
+-- text_to_speech    Primary action tool. Converts text to audio file.
|
+-- list_voices       Discovery tool. Queries available voices.
```

### Design Principles

1. **Discoverability through naming:** Tool names use snake_case and describe the action (`text_to_speech`) or the query (`list_voices`). No abbreviations, no brand prefixes on tool names.
2. **Progressive disclosure:** Only `text` is required for `text_to_speech`. All other parameters have sensible defaults. Users can start simple and add specificity as needed.
3. **Tool descriptions drive LLM behavior:** The MCP tool schema descriptions are the primary "UI" -- they tell the LLM when and how to invoke each tool. Descriptions must be precise and concise.

---

## 2. Tool Schema Descriptions (Copy Guidelines)

Tool descriptions are the most important UX surface. They are read by the LLM to decide when to call the tool and how to fill parameters. They must be:

- **Accurate:** Do not overstate capabilities.
- **Actionable:** Tell the LLM what the tool does and what it returns.
- **Concise:** LLM context is expensive. No filler words.

### 2.1 `text_to_speech`

**Tool description:**
```
Convert text to speech using Supertone TTS API. Saves the audio file locally and returns the file path and duration. Supports Korean, English, and Japanese. Maximum 300 characters per call.
```

**Parameter descriptions:**

| Parameter | Description |
|-----------|-------------|
| `text` | Text to convert to speech. Required. Maximum 300 characters. |
| `voice_id` | Voice identifier. Use list_voices to see available options. If omitted, a default Korean voice is used. |
| `language` | Language code: "ko" (Korean, default), "en" (English), or "ja" (Japanese). |
| `output_format` | Audio format: "mp3" (default) or "wav". |
| `speed` | Playback speed multiplier. Range: 0.5 to 2.0. Default: 1.0. |
| `pitch_shift` | Pitch adjustment in semitones. Range: -12 to +12. Default: 0. |
| `style` | Emotion style (e.g., "neutral", "happy"). Available styles vary by voice -- use list_voices to check. |

### 2.2 `list_voices`

**Tool description:**
```
List available Supertone TTS voices. Returns voice ID, name, supported languages, and supported emotion styles for each voice. Optionally filter by language.
```

**Parameter descriptions:**

| Parameter | Description |
|-----------|-------------|
| `language` | Filter voices by language code: "ko", "en", or "ja". If omitted, all voices are returned. |

---

## 3. Key Interaction Flows

### 3.1 Text-to-Speech Flow (Happy Path)

```
User (in Claude Desktop): "Read this sentence aloud: Hello, how are you?"
  |
  v
LLM decides to call text_to_speech(text="Hello, how are you?", language="en")
  |
  v
MCP Server:
  1. Validate parameters (text length, language code, ranges)
  2. Resolve voice_id (use default if not provided)
  3. Call Supertone API: POST /v1/text-to-speech/{voice_id}
  4. Save audio stream to file: ~/supertone-tts-output/2026-03-13_a1b2c3.mp3
  5. Return success response
  |
  v
LLM presents to user:
  "I've generated the audio file. It's saved at:
   ~/supertone-tts-output/2026-03-13_a1b2c3.mp3 (duration: 2.3 seconds)"
```

### 3.2 List Voices Flow (Happy Path)

```
User: "What voices are available for Japanese?"
  |
  v
LLM calls list_voices(language="ja")
  |
  v
MCP Server:
  1. Validate language parameter
  2. Call Supertone API: GET /v1/voices
  3. Filter results by language
  4. Return structured voice list
  |
  v
LLM presents to user:
  "Here are the available Japanese voices:
   - Yuki (voice_id: yuki-01) -- styles: neutral, happy, sad
   - Kenji (voice_id: kenji-01) -- styles: neutral, serious"
```

### 3.3 Error Paths

Each error path follows a consistent structure: **what went wrong** + **what to do about it**.

```
Error Flow: API Key Missing
  User calls any tool
    -> Server checks SUPERTONE_API_KEY env var
    -> Not set or empty
    -> Return error (no API call made)

Error Flow: Text Too Long
  User calls text_to_speech with 350 characters
    -> Server validates text length
    -> Exceeds 300 chars
    -> Return error (no API call made)

Error Flow: Invalid Parameter
  User calls text_to_speech(speed=5.0)
    -> Server validates speed range
    -> Out of range [0.5, 2.0]
    -> Return error (no API call made)

Error Flow: API Authentication Failure
  User calls tool with invalid API key
    -> Server calls Supertone API
    -> API returns HTTP 401/403
    -> Return error with auth guidance

Error Flow: API Rate Limit
  User calls tool too frequently
    -> API returns HTTP 429
    -> Return error with wait guidance

Error Flow: Network Failure
  User calls tool, network is down
    -> httpx raises connection error or timeout
    -> Return error with network guidance

Error Flow: File System Permission Error
  Server cannot write to output directory
    -> OS raises PermissionError
    -> Return error with directory guidance
```

---

## 4. Tool States (Input/Output Specification)

### 4.1 `text_to_speech`

#### Success State

**Input example:**
```json
{
  "text": "Hello, this is a test.",
  "language": "en",
  "output_format": "mp3",
  "speed": 1.0
}
```

**Output format:**
```
Audio file saved: /Users/username/supertone-tts-output/2026-03-13_a1b2c3.mp3
Duration: 2.3 seconds
Voice: yuki-01
Language: en
Format: mp3
```

The output is plain text, not JSON. MCP tool responses are consumed by the LLM, which will reformat for the user. Structured but human-readable text is the optimal format -- it is easy for the LLM to parse and present.

#### Error States

| Error Condition | Output Message |
|----------------|----------------|
| API key not set | `SUPERTONE_API_KEY environment variable is not set. Please configure it in your MCP client settings.` |
| Empty text | `Text must not be empty.` |
| Text too long | `Text exceeds the maximum length of 300 characters (received: {N}). Please shorten or split the text manually.` |
| Invalid language | `Invalid language: "{value}". Supported languages: ko, en, ja.` |
| Invalid output_format | `Invalid output format: "{value}". Supported formats: mp3, wav.` |
| Speed out of range | `Speed must be between 0.5 and 2.0 (received: {value}).` |
| Pitch out of range | `Pitch shift must be between -12 and +12 semitones (received: {value}).` |
| Invalid style | `Style "{value}" is not supported by voice "{voice_id}". Available styles: {list}.` |
| API auth failure (401/403) | `Authentication failed. Please verify your SUPERTONE_API_KEY.` |
| Rate limit (429) | `Rate limit exceeded. Please wait and try again.` |
| API server error (5xx) | `Supertone API server error ({status_code}). Please try again later.` |
| Network/connection error | `Failed to connect to Supertone API. Please check your network connection.` |
| Output dir permission error | `Cannot write to output directory: {path}. Please check directory permissions or set SUPERTONE_OUTPUT_DIR to a writable location.` |

#### Edge Cases

| Case | Behavior |
|------|----------|
| Exactly 300 characters | Accepted. Proceeds normally. |
| 301 characters | Rejected with text-too-long error. |
| Unicode text (e.g., Korean, emoji) | Character count uses Python `len()` (counts Unicode codepoints, not bytes). |
| `voice_id` not provided | Default voice is used. Success message includes the default voice_id for transparency. |
| `style` not provided | Voice's default style is used. Not mentioned in output unless explicitly set. |
| Output directory does not exist | Created automatically (including intermediate directories). |
| File name collision | Unique ID component prevents collisions. File naming: `{YYYY-MM-DD}_{uuid_short}.{format}`. |

### 4.2 `list_voices`

#### Success State (with results)

**Input example:**
```json
{
  "language": "ko"
}
```

**Output format:**
```
Found 3 voices matching language: ko

1. Name: Sujin
   Voice ID: sujin-01
   Languages: ko, en
   Styles: neutral, happy, sad, angry

2. Name: Minho
   Voice ID: minho-01
   Languages: ko
   Styles: neutral, serious

3. Name: Yuna
   Voice ID: yuna-01
   Languages: ko, ja
   Styles: neutral, happy
```

Output uses a numbered list format. Each voice entry is separated by a blank line for readability. Fields are labeled clearly so the LLM can extract and present them in any format (table, list, prose).

#### Success State (empty results)

**Input example:**
```json
{
  "language": "ja"
}
```

**Output (when no Japanese voices exist):**
```
No voices found matching language: ja.
```

This is a success state, not an error. The query succeeded but returned no results.

#### Success State (no filter)

**Input example:**
```json
{}
```

**Output:**
```
Found 5 voices:

1. Name: Sujin
   ...
```

#### Error States

| Error Condition | Output Message |
|----------------|----------------|
| API key not set | `SUPERTONE_API_KEY environment variable is not set. Please configure it in your MCP client settings.` |
| Invalid language filter | `Invalid language filter: "{value}". Supported languages: ko, en, ja.` |
| API auth failure (401/403) | `Authentication failed. Please verify your SUPERTONE_API_KEY.` |
| Rate limit (429) | `Rate limit exceeded. Please wait and try again.` |
| API server error (5xx) | `Supertone API server error ({status_code}). Please try again later.` |
| Network/connection error | `Failed to connect to Supertone API. Please check your network connection.` |

---

## 5. Error Message Copy Guidelines

### 5.1 Structure

Every error message must follow this template:

```
{What went wrong}. {What the user should do}.
```

Examples:
- "Text exceeds the maximum length of 300 characters (received: 412). Please shorten or split the text manually."
- "Authentication failed. Please verify your SUPERTONE_API_KEY."

### 5.2 Rules

1. **No stack traces.** Never expose Python tracebacks, internal module names, or line numbers in tool responses.
2. **No API key echo.** Never include the API key value (even partially) in any output.
3. **Specific over generic.** "Speed must be between 0.5 and 2.0 (received: 5.0)" is better than "Invalid parameter."
4. **Include received values.** When a user provides an invalid value, echo it back so they can see the mistake. Exception: never echo the API key.
5. **Suggest the fix.** Every error message ends with guidance. If the fix requires configuration, name the specific environment variable or setting.
6. **Use plain English.** Avoid jargon like "HTTP 401" in user-facing messages. Map status codes to human-readable descriptions. Exception: 5xx errors include the status code because it aids debugging with Supertone support.
7. **Consistent tone.** Neutral and direct. No apologies ("Sorry, ..."), no exclamation marks, no emoji.
8. **Period-terminated.** Every message ends with a period.

### 5.3 Language

All error messages and tool descriptions are in **English**. The tool converts text in multiple languages but its own interface is English-only. This is consistent with MCP ecosystem conventions and the target audience (developers).

---

## 6. Output Formatting and Accessibility

### 6.1 Plain Text Output

All tool responses use plain text, not JSON or Markdown. Rationale:
- MCP tool responses are consumed by the LLM, which reformats for presentation.
- Plain text is universally parseable by any LLM.
- Structured text (labeled fields, numbered lists) gives the LLM enough structure to present well.

### 6.2 File Paths

- Always return **absolute paths** (e.g., `/Users/username/supertone-tts-output/...`), not relative paths or paths with `~`.
- Expand `~` to the full home directory path before returning.
- Use forward slashes on all platforms for consistency in the returned message.

### 6.3 Numbers

- Duration: always include unit ("2.3 seconds", not "2.3s" or "2.3").
- Speed/pitch: include the unit or context in error messages ("0.5 to 2.0", "-12 to +12 semitones").

### 6.4 Lists

- Use numbered lists for voice listings (aids reference: "use voice number 2").
- Use labeled fields within each list item (not positional).
- Separate list items with blank lines for readability.

### 6.5 Consistency

- Field labels use Title Case followed by a colon: "Voice ID:", "Languages:", "Styles:".
- Enum values (language codes, format names) are always lowercase in output: `ko`, `mp3`.
- Voice names use their original casing from the API.

---

## 7. Interaction Edge Cases and Guidance

### 7.1 LLM-Mediated Interactions

Users do not call MCP tools directly -- the LLM decides when and how to invoke them. This means:

- **The LLM may call `list_voices` before `text_to_speech`** to help the user choose a voice. The tool descriptions should encourage this pattern (the `voice_id` description says "Use list_voices to see available options").
- **The LLM may adjust parameters** based on user intent. For example, if a user says "make it faster," the LLM may call `text_to_speech` with `speed=1.5`.
- **The LLM will present errors** in natural language. Error messages should be written so they can be relayed directly to the user without reformulation.

### 7.2 Multi-Turn Patterns

Common multi-turn flows the tool descriptions should support:

1. **Explore then generate:** User asks "what voices do you have?" -> LLM calls `list_voices` -> User picks one -> LLM calls `text_to_speech` with that `voice_id`.
2. **Iterate on parameters:** User says "make it slower" -> LLM calls `text_to_speech` again with lower `speed`, keeping other params.
3. **Language switch:** User says "now say the same thing in Japanese" -> LLM calls `text_to_speech` with `language="ja"` and the same text.

The tool itself is stateless -- it does not remember previous calls. The LLM maintains conversational context.

### 7.3 What the Server Does NOT Do

- **No audio playback.** The server saves a file and returns the path. Playing the audio is outside scope.
- **No text splitting.** If text exceeds 300 characters, the user (or LLM) must split it manually.
- **No voice recommendation.** The server does not suggest voices. The LLM can use `list_voices` output to make suggestions.
- **No progress indication.** MCP tool calls are synchronous from the client's perspective. There is no streaming progress update. The Supertone API response time (typically 1-5 seconds) is the dominant wait.

---

## 8. Traceability

| UX Element | Requirement |
|-----------|-------------|
| `text_to_speech` tool description | FR-001, US-001 |
| `list_voices` tool description | FR-002, US-002 |
| Language parameter copy | US-003, FR-006 |
| Speed/pitch parameter copy | US-004, FR-006 |
| Style parameter copy | US-005, FR-006 |
| Output format parameter copy | US-006, FR-006 |
| Language filter in list_voices | US-007 |
| API key error message | FR-003, NFR-004, NFR-007 |
| Text length error message | FR-005, NFR-004 |
| Parameter validation errors | FR-006, NFR-004 |
| API error messages (401, 429, 5xx, network) | FR-007, NFR-004 |
| Output directory error message | FR-004, NFR-004 |
| Absolute file path in output | FR-001 |
| Plain text output format | NFR-004 (clarity) |
