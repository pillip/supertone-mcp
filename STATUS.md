# Project Status: Supertone TTS MCP Server

> Last updated: 2026-03-13

## Current Milestone

**M2: MCP Server Implementation** — Build the core MCP server with `text_to_speech` and `list_voices` tools.

## Issue Summary

| Metric | Count |
|--------|-------|
| Total issues | 11 |
| P0 (Critical) | 4 |
| P1 (Important) | 5 |
| P2 (Nice-to-have) | 2 |

### By Track

| Track | Count |
|-------|-------|
| Platform (scaffold, packaging, CI) | 4 |
| Product (tools, server, docs) | 7 |

### Status

| Status | Count |
|--------|-------|
| Backlog | 11 |
| In Progress | 0 |
| Done | 0 |

## Key Risks

| Risk | Impact | Status |
|------|--------|--------|
| R1: Supertone API docs incomplete (base URL, endpoints) | High | Open — needs M1 API spike |
| R2: Audio duration not in API response | Low | Open — mutagen fallback planned |
| R3: MCP SDK breaking changes | Medium | Mitigated — pin minor version |
| R4: Default voice_id unknown | Medium | Open — needs stakeholder input (A4) |
| R6: PyPI name availability | High | Open — check before dev starts |

## Next Issues to Implement

1. **ISSUE-001** (P0, 0.5d): Scaffold project with uv, pyproject.toml, and src layout
2. **ISSUE-002** (P0, 0.5d): Define domain types, constants, and exception hierarchy
3. **ISSUE-003** (P0, 1d): Implement SupertoneClient with synthesize and get_voices
4. **ISSUE-009** (P1, 0.5d): Set up GitHub Actions CI (can parallel with ISSUE-002+)

## Critical Path

```
001 → 002 → 003/004 (parallel) → 005/006 (parallel) → 007 → 008 → 011
```

**Estimated wall-clock time:** ~5 days with one developer (7.5d total effort).

## Documents

| Document | Status |
|----------|--------|
| `PRD.md` | Done |
| `docs/requirements.md` | Done |
| `docs/ux_spec.md` | Done |
| `docs/architecture.md` | Done |
| `docs/data_model.md` | Done |
| `docs/test_plan.md` | Done |
| `issues.md` | Done |
