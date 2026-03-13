# PRD: Supertone TTS MCP Server

> Status: Draft
> Date: 2026-03-13
> Author: pillip

---

## 1. Background

MCP(Model Context Protocol)는 LLM 클라이언트(Claude Desktop, Cursor, OpenClaw 등)에서 외부 도구를 연동하는 표준 프로토콜로, 2024년 11월 출시 이후 폭발적으로 성장 중이다(10,000+ 서버, 5개월간 다운로드 80배 증가).

수퍼톤(Supertone)은 HYBE 자회사로 한국어 특화 고품질 TTS를 제공하며, API를 통해 23개 언어의 음성 합성을 지원한다. 현재 MCP 생태계에 TTS 서버는 5개 이상 존재하나, **수퍼톤 기반 MCP 서버는 없다.**

이 프로젝트는 수퍼톤 TTS API를 MCP 서버로 래핑하여 배포함으로써:
1. MCP 서버 개발 기술을 습득하고
2. 수퍼톤 API 사용량을 간접적으로 증가시키는 것을 목표로 한다.

---

## 2. Goals

| # | 목표 | 측정 기준 |
|---|------|----------|
| G1 | MCP 서버 개발 역량 확보 | MCP 표준을 준수하는 동작하는 서버 완성 |
| G2 | 수퍼톤 TTS를 MCP 생태계에 진입시킴 | Claude Desktop + Cursor에서 정상 동작 확인 |
| G3 | 오픈소스로 배포하여 외부 사용자 확보 | GitHub 공개 + PyPI 배포 |

---

## 3. Non-Goals (Out of Scope)

- STT(Speech-to-Text) 기능 — MCP의 구조(LLM이 tool 호출)와 맞지 않음
- 음성 대화 인터페이스 (STT→LLM→TTS) — 별도 프로젝트로 분리
- 음성 복제(voice clone) — v2에서 고려
- 배치 변환, 길이 예측 등 고급 기능 — v2에서 고려
- 웹 UI 또는 별도 클라이언트 앱
- 수퍼톤 외 다른 TTS 엔진 지원

---

## 4. Target Users

### Primary: MCP 사용자 (개발자/크리에이터)
- Claude Desktop, Cursor, OpenClaw 등 MCP 지원 클라이언트를 사용하는 사람
- LLM과 대화하면서 텍스트를 음성으로 변환하고 싶은 경우
- 예: "이 문장을 한국어 음성으로 만들어줘", "오늘 뉴스를 요약해서 음성 브리핑으로 만들어줘"

### Secondary: 콘텐츠 크리에이터
- 나레이션, 더빙 등을 LLM 워크플로우 안에서 자동화하고 싶은 사람
- 한국어 고품질 음성이 필요한 사람

---

## 5. User Stories

| # | 스토리 | 우선순위 |
|---|--------|---------|
| US1 | MCP 사용자로서, 텍스트를 입력하면 수퍼톤 TTS로 음성 파일을 생성하고 싶다. 그래야 타이핑한 내용을 음성으로 들을 수 있다. | Must |
| US2 | MCP 사용자로서, 사용 가능한 보이스 목록을 조회하고 싶다. 그래야 원하는 목소리를 골라서 TTS에 사용할 수 있다. | Must |
| US3 | MCP 사용자로서, 음성의 언어(한/영/일)를 지정하고 싶다. 그래야 다국어 콘텐츠를 만들 수 있다. | Must |
| US4 | MCP 사용자로서, 음성의 속도와 피치를 조절하고 싶다. 그래야 용도에 맞는 음성을 만들 수 있다. | Should |
| US5 | MCP 사용자로서, 감정 스타일(neutral, happy 등)을 지정하고 싶다. 그래야 표현력 있는 음성을 만들 수 있다. | Should |
| US6 | MCP 사용자로서, 출력 포맷(wav/mp3)을 선택하고 싶다. 그래야 용도에 맞는 파일을 받을 수 있다. | Should |

---

## 6. Functional Requirements

### FR1: `text_to_speech` Tool

수퍼톤 TTS API(`POST /v1/text-to-speech/{voice_id}`)를 호출하여 텍스트를 음성 파일로 변환한다.

**입력 파라미터:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `text` | string | Yes | 변환할 텍스트 (최대 300자) |
| `voice_id` | string | No | 보이스 ID (미지정 시 기본 보이스 사용) |
| `language` | string | No | `ko`, `en`, `ja` 중 택 1 (기본값: `ko`) |
| `output_format` | string | No | `wav` 또는 `mp3` (기본값: `mp3`) |
| `speed` | number | No | 0.5~2.0 (기본값: 1.0) |
| `pitch_shift` | number | No | -12~+12 반음 (기본값: 0) |
| `style` | string | No | 감정 스타일 (예: `neutral`, `happy`) |

**출력:**
- 생성된 음성 파일을 로컬 디렉토리에 저장
- 파일 경로와 음성 길이(초)를 반환
- 저장 디렉토리는 환경변수(`SUPERTONE_OUTPUT_DIR`)로 설정 가능, 기본값은 `~/supertone-tts-output/`

**에러 처리:**
- API Key 미설정 시 명확한 안내 메시지
- 300자 초과 시 텍스트 자동 분할 없이 에러 반환 (사용자가 직접 분할)
- API 호출 실패 시 HTTP 상태 코드와 에러 메시지 전달

### FR2: `list_voices` Tool

수퍼톤 API에서 사용 가능한 보이스 목록을 조회한다.

**입력 파라미터:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `language` | string | No | 특정 언어의 보이스만 필터링 (`ko`, `en`, `ja`) |

**출력:**
- 보이스 목록 (voice_id, 이름, 지원 언어, 지원 스타일)

### FR3: 설정 및 인증

- 수퍼톤 API Key는 환경변수 `SUPERTONE_API_KEY`로 제공
- MCP 클라이언트의 서버 설정에서 환경변수로 주입하는 표준 방식 사용

---

## 7. Non-Functional Requirements

| # | 요구사항 | 기준 |
|---|---------|------|
| NFR1 | **설치 용이성** | `uvx supertone-tts-mcp` 또는 `pip install supertone-tts-mcp` 한 줄로 설치 가능 |
| NFR2 | **MCP 호환성** | MCP Python SDK 기반, Claude Desktop과 Cursor에서 정상 동작 |
| NFR3 | **응답 시간** | 수퍼톤 API 응답 시간에 의존 (MCP 서버 자체 오버헤드 < 100ms) |
| NFR4 | **에러 메시지** | API Key 누락, 잘못된 파라미터 등에 대해 사용자가 이해할 수 있는 메시지 제공 |
| NFR5 | **테스트** | pytest 기반 단위 테스트, API 호출은 mock 처리 |

---

## 8. Technical Notes

### 8.1 기술 스택

| 항목 | 선택 | 근거 |
|------|------|------|
| 언어 | **Python 3.11+** | claude.md 기본 언어, uv 워크플로우 활용 |
| MCP SDK | `mcp` (Python SDK) | 공식 SDK |
| HTTP 클라이언트 | `httpx` | async 지원, 현대적 Python HTTP 라이브러리 |
| 패키지 관리 | `uv` | claude.md 표준 |
| 테스트 | `pytest` + `pytest-asyncio` | claude.md 표준 |
| 배포 | PyPI (`supertone-tts-mcp`) | `uvx` 또는 `pip install`로 설치 |
| 레지스트리 | 공식 MCP Registry + PulseMCP | `mcp-publisher` CLI로 등록 |

### 8.2 수퍼톤 API 요약

- **Base URL**: `https://api.supertoneapi.com` (docs에서 확인 필요)
- **인증**: `x-sup-api-key` 헤더
- **TTS**: `POST /v1/text-to-speech/{voice_id}` → audio stream 반환
- **보이스 목록**: `GET /v1/voices` (추정, docs에서 확인 필요)
- **응답**: `audio/wav` 또는 `audio/mpeg` 바이너리 스트림
- **제한**: 텍스트 최대 300자, 요금제별 rate limit (20-60 req/min)

### 8.3 MCP 서버 구조

```
supertone-tts-mcp/
├── pyproject.toml
├── src/
│   └── supertone_tts_mcp/
│       ├── __init__.py
│       ├── server.py          # MCP 서버 진입점
│       ├── tools.py           # text_to_speech, list_voices 구현
│       └── supertone_client.py # 수퍼톤 API 래핑
├── tests/
│   ├── test_tools.py
│   └── test_supertone_client.py
├── server.json             # MCP Registry 등록용 메타데이터
└── README.md
```

### 8.4 MCP 클라이언트 설정 예시 (Claude Desktop)

```json
{
  "mcpServers": {
    "supertone-tts": {
      "command": "uvx",
      "args": ["supertone-tts-mcp"],
      "env": {
        "SUPERTONE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### 8.5 MCP Registry 배포

PyPI 배포 후 공식 MCP Registry에 등록하여 검색/설치 가능하게 한다.

**등록 절차:**
```bash
# 1. CLI 설치
brew install mcp-publisher

# 2. 설정 파일 생성 (server.json)
mcp-publisher init

# 3. GitHub 인증
mcp-publisher login github

# 4. 등록
mcp-publisher publish
```

**server.json 예시:**
```json
{
  "$schema": "https://static.modelcontextprotocol.io/schemas/2025-07-09/server.schema.json",
  "name": "io.github.pillip/supertone-tts",
  "description": "High-quality TTS powered by Supertone API — best Korean voice synthesis with emotion control and voice cloning",
  "version": "0.1.0",
  "packages": [
    {
      "registry_type": "pypi",
      "identifier": "supertone-tts-mcp",
      "version": "0.1.0"
    }
  ]
}
```

**추가 등록 대상:**
- [공식 MCP Registry](https://registry.modelcontextprotocol.io/) — `mcp-publisher`로 등록
- [PulseMCP](https://pulsemcp.com/) — 셀프 등록 (5,500+ 서버 등록된 커뮤니티 디렉토리)
- [GitHub MCP Registry](https://github.blog/ai-and-ml/github-copilot/meet-the-github-mcp-registry-the-fastest-way-to-discover-mcp-servers/) — GitHub 릴리스 기반

PyPI README에 아래 메타데이터 포함 필수:
```
mcp-name: io.github.pillip/supertone-tts
```

### 8.6 음성 파일 전달 방식

MCP에서 바이너리 파일 전달은 제한적이므로:
1. 수퍼톤 API에서 받은 오디오 스트림을 **로컬 파일로 저장**
2. **파일 경로**를 텍스트로 반환 (예: `~/supertone-tts-output/2026-03-13_abc123.mp3`)
3. 사용자가 해당 경로의 파일을 재생

---

## 9. Success Metrics

| # | 지표 | 목표 (출시 후 3개월) |
|---|------|-------------------|
| SM1 | GitHub stars | 50+ |
| SM2 | PyPI 다운로드 수 | 200+ |
| SM3 | 공식 MCP Registry 등록 | 등록 완료 + 검색 가능 확인 |
| SM4 | Claude Desktop + Cursor에서 정상 동작 | 2개 클라이언트 모두 확인 |
| SM5 | MCP 학습 목표 달성 | MCP 서버 개발 프로세스 숙달 (주관적) |

---

## 10. Milestones

| 단계 | 내용 | 예상 기간 |
|------|------|----------|
| M1 | 수퍼톤 API 연동 확인 (단독 스크립트) | 1일 |
| M2 | MCP 서버 구현 (`text_to_speech` + `list_voices`) | 2-3일 |
| M3 | 테스트 작성 + Claude Desktop에서 동작 확인 | 1-2일 |
| M4 | README 작성 + PyPI 배포 | 1일 |
| M5 | GitHub 공개 + 공식 MCP Registry 등록 + PulseMCP 등록 | 1일 |

**총 예상 기간**: 1-2주

---

## 11. Future Considerations (v2+)

- 음성 복제 (`clone_voice` tool) — 10초 음성으로 커스텀 보이스 생성
- 배치 변환 (`batch_tts`) — 여러 문장을 한번에 변환
- 길이 예측 (`predict_duration`) — 크레딧 소비 전 예상 시간 확인
- 크레딧 잔액 조회 (`check_credits`)
- 스트리밍 TTS 지원
- 300자 초과 텍스트 자동 분할 및 연결
