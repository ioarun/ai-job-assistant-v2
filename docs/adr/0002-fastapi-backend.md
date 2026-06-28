# ADR-0002: FastAPI as the backend web framework

Status: Accepted
Date: 2026-06-28

## Context
The assistant needs an HTTP API to drive the pipeline and expose endpoints (resume
upload, results, approvals). LLM and external-API calls are I/O-bound, so async
support matters. We want a "production-shaped" backend rather than a UI-only
prototype.

## Decision
Use **FastAPI** (ASGI, async, Pydantic-based) as the backend framework, served by
Uvicorn.

## Alternatives considered
- **Streamlit** — fastest path to a UI with approval buttons, but it's a UI tool,
  not a real API; harder to grow into a production service.
- **Flask** — synchronous and less modern; weaker async story.
- **Django** — heavier than needed for an API-first service.

## Consequences
- (+) Async-friendly, typed, automatic OpenAPI/Swagger docs, Pydantic validation.
- (−) The human-in-the-loop UI must be built separately (no built-in frontend).