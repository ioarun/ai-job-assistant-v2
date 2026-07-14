# ADR-0011: LangGraph checkpointer — Postgres

Status: Accepted
Date: 2026-07-12

## Context
Phase C (roadmap) introduces the first real **LangGraph** graph (ADR-0003): `ingest →
parse → [interrupt: human review] → persist_approved`. The `interrupt()` pause means the
HTTP request that triggers `parse` returns to the client **before** the human responds —
the approve/corrections decision arrives later, via a separate HTTP request, possibly
minutes or hours afterward. For the graph to resume correctly at that point, its state
must be **persisted across the gap**, not held only in the process's memory. LangGraph
calls this a **checkpointer**, and the RFC (`docs/design.md` §4.2) flagged the choice as
an open item — "candidate ADR-0011."

## Decision
Use the official **Postgres checkpointer** (`langgraph-checkpoint-postgres`,
`AsyncPostgresSaver`), pointed at the **same app Postgres database** already used for
`resume`/`parse_run` (ADR-0009) — not a separate store.

- One `checkpointer.setup()` call (idempotent, run once at app startup) creates
  LangGraph's own internal checkpoint tables inside that same database. These tables are
  managed by LangGraph itself, **not** by our Alembic migrations — a second, separate
  schema-management mechanism living alongside our app schema, by design.
- The graph's compiled instance is built with this checkpointer attached, so a review
  left pending genuinely survives an app restart.

## Alternatives considered
- **In-memory checkpointer (`MemorySaver`)** — zero setup, but state is lost on process
  restart. A human may take arbitrarily long to review; losing an in-progress review on
  a routine restart violates "everything reversible and observable" and the whole point
  of the gate. **Rejected** beyond quick local experiments/tests.
- **SQLite checkpointer** — would introduce a second, different database technology
  purely for checkpoint state, when Postgres is already running and already the app's
  system of record. **Rejected** — unnecessary moving part.
- **A separate dedicated store (e.g. Redis)** — unnecessary infrastructure at MVP scale;
  consistent with ADR-0013's stance of minimizing local services. **Rejected for now**;
  revisit only if checkpoint volume/concurrency becomes a real bottleneck at production
  scale.

## Consequences
- (+) **One fewer moving part** — reuses the already-running, already-migrated app
  Postgres; no new local infrastructure.
- (+) **Production-like** — the same checkpointer works unchanged when deployed later.
- (+) Matches **"everything reversible and observable"** — a paused review is genuinely
  durable, not just apparently so.
- (−) LangGraph's checkpoint tables live in the same database but are **not** part of our
  Alembic-managed schema — remember to call `setup()` once at startup, not treat it as a
  migration.
- (−) Adds a new dependency (`langgraph-checkpoint-postgres`) alongside `langgraph`
  itself.

Builds on ADR-0003 (LangGraph orchestration) and ADR-0009 (Postgres as the app database);
feeds the Phase C review-gate graph.

## Addendum (2026-07-12) — the consequence above actually happened

While adding Phase D's `JobPick` model, `alembic revision --autogenerate` diffed the live
database against `app/models.py`, saw LangGraph's checkpoint tables (real, but never
declared in our SQLAlchemy models — exactly the gap flagged above), and concluded they
shouldn't exist. It generated `DROP TABLE` statements for all four, and `alembic upgrade
head` executed them — deleting the checkpoint state for every resume then sitting in
`awaiting_review`. The abstract warning in this ADR wasn't concrete enough to prevent it.

**Fix:** `migrations/env.py` now passes an `include_object` callback to
`context.configure()` that excludes `checkpoints`, `checkpoint_blobs`,
`checkpoint_writes`, and `checkpoint_migrations` from autogenerate diffing entirely.
Verified by generating a migration after the fix with the checkpoint tables present —
it correctly detected zero drift. Any future `alembic revision --autogenerate` is safe
by construction; this is not something to remember to check by hand anymore.
