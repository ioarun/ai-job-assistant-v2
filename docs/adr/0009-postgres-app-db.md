# ADR-0009: Use PostgreSQL as the application database

Status: Accepted
Date: 2026-06-29

## Context
We need to persist uploaded resumes, parsed/structured data, jobs, and run/approval
state. The data is partly relational and partly semi-structured (parsed resume
fields vary). We also anticipate a future RAG vector store, and want a mature,
production-like store that runs cleanly under Docker.

## Decision
Use **PostgreSQL** as the primary application database.

## Alternatives considered
- **SQLite** — simplest for local dev, but weaker concurrency and less
  production-like; we'd likely migrate later.
- **A NoSQL/document store** — poorer fit for the relational run/approval state.

## Consequences
- (+) Mature and relational, with `jsonb` for the semi-structured resume data.
- (+) The **pgvector** extension means the future vector store could reuse Postgres
  (one fewer moving part) — candidate, deferred to a Post-MVP ADR.
- (+) Aligns with Langfuse's own Postgres usage (ADR-0005).
- (−) Heavier than SQLite for local dev (mitigated by Docker, ADR-0006).