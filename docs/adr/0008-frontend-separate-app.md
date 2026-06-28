# ADR-0008: Build the front end as a separate app (not folded into the backend)

Status: Accepted
Date: 2026-06-29

## Context
The applicant needs a UI (upload resume, review the parse, and later pick jobs and
approve tailored docs). Two shapes: fold a minimal UI into the FastAPI backend
(server-rendered templates), or build a separate front-end application that talks to
the backend over HTTP/JSON. The product grows toward a richer multi-step,
human-in-the-loop UI, so the client/server split matters even at MVP.

## Decision
Build the front end as a **separate application** that consumes the backend API over
HTTP/JSON, starting from the MVP. The specific front-end framework is **not yet
decided** (a follow-up decision).

## Alternatives considered
- **Fold the UI into the backend** (server-rendered templates) — simpler short-term,
  but couples UI to the API, and the richer HITL UI later would force a rewrite.

## Consequences
- (+) Clean API-first separation; the front end can evolve independently; matches the
  context/architecture diagrams (UI is its own container).
- (−) More upfront setup (two apps, CORS, separate deploy); framework choice still
  pending.