# Phase C — HITL Review Gate + Minimal UI

> Part of the [AI Job Assistant](README.md) phased build. Phase C closes the MVP loop —
> see [Phase B](README_B.md) for the resume-parse slice it builds on.

## Goal

An applicant uploads a resume, reviews the parsed result behind a light gate
("looks right? Yes / Fix"), and approves or corrects it — entirely through a browser.
**This is the shippable MVP** (PRD stage 1; roadmap Phases A + B + C).

## What was built

| Piece | Where | Notes |
|---|---|---|
| Review-gate graph | `app/graph.py` | LangGraph `StateGraph`: `ingest → parse → [interrupt: review] → persist_approved`, with a `revise` loop back to `parse` |
| Checkpointer | `app/main.py` `lifespan` | `AsyncPostgresSaver`, built once at startup (ADR-0011); reuses the app Postgres, own tables via `.setup()` |
| Upload endpoint | `app/main.py` `POST /resumes` | Creates `Resume` + initial `ParseRun` rows, runs the graph to the interrupt, returns whatever it paused with |
| Poll endpoint | `app/main.py` `GET /resumes/{id}/parse` | Deliberately bypasses the graph — a plain DB read (not currently called by the frontend; there for reloading a stale page) |
| Review endpoints | `app/main.py` `POST .../approve`, `POST .../corrections` | Resume the paused graph via `Command(resume=...)`, keyed by `thread_id = str(resume_id)` |
| CORS | `app/main.py` | `CORSMiddleware`, wildcard origin — the frontend is a genuinely separate origin (ADR-0008) |
| `ProjectEntry` | `app/schemas.py` | Distinguishes personal/side projects from paid `work_history`; prompt bumped to `parse-v2` |
| Eval coverage | `tests/eval/` | All 3 fixtures score `projects` alongside work/education |
| Frontend | `frontend/index.html`, `style.css` | Plain HTML/JS (ADR-0008): upload → review parsed fields (incl. projects) → Approve or send free-text Corrections; loading states on every async action |
| Code walkthrough | `docs/walkthroughs/phase-c-review-gate.html` | Interactive blueprint-style diagram — frontend → API → graph, click any box for its real source (gitignored, WIP) |

## Key decisions

- **ADR-0011 — Postgres checkpointer.** Reuses the app database rather than a separate
  store; `AsyncPostgresSaver.setup()` creates its own tables alongside the Alembic-managed
  schema, not through it.
- **The re-execution rule shaped `review_node`.** LangGraph reruns an interrupted node
  *from its first line* on resume — so `review_node` does nothing but call `interrupt()`
  and branch on the result; all real persistence lives in separate nodes that only run
  once.
- **`ProjectEntry` fixed a real misclassification** — your own resume's "Independent GenAI
  Portfolio" entry had been forced into `work_history` with a location standing in for a
  company name. A dedicated `projects` field, plus a one-line prompt distinction, resolved
  it cleanly.
- **ADR-0015 — rejected RAG-augmented parsing.** The originally-floated "B2" extension
  (Chroma dual-purpose chunking) was designed, then explicitly turned down — strict
  string-matching plus `temperature=0` was already accurate and deterministic.
- **ADR-0016 — resume identity/dedup deferred.** Every upload reparses unconditionally,
  even an identical re-upload. Recorded as a proposed-but-undecided future ADR rather than
  an untracked gap.

## In depth

### Two `graph.ainvoke()` calls, one HTTP request apart

The hardest thing to internalize about this phase: `POST /resumes` and
`POST .../approve` are **two separate calls to the same compiled graph**, sharing state
only because the Postgres checkpointer remembers exactly where `review_node` paused. There
is no in-memory link between them — if the server restarted in between, the review would
still resume correctly, because the checkpoint lives in the database, not in a process.

### The eval caught real bugs again, same as Phase B

Adding LangGraph surfaced a fresh lesson: `chat.completions.parse()`'s `temperature`
default had already been pinned in Phase B, so this phase's surprises were structural
instead — the first version of `POST /resumes` mirrored the RFC's synchronous design
faithfully, but the temptation to add a database write *before* `interrupt()` inside
`review_node` would have silently double-executed it on every resume. Understanding
*why* (the re-execution rule) came before writing the node, not after debugging it.

### Why the frontend is deliberately plain

ADR-0008 committed to a separate frontend without picking a framework. For Phase C, plain
HTML + vanilla `fetch()` was chosen over React or Streamlit: zero build tooling, and the
whole review-gate story (three endpoints, three button handlers) fits in one legible file.
A richer framework is a reasonable choice later, once the UI needs more than "upload,
review, approve" — not before.

## Running it locally

Prereqs: same as Phase B, plus the new dependencies.

```bash
# 1. App database + migrations (if not already done)
docker compose up -d
uv run alembic upgrade head

# 2. Backend
uv run uvicorn app.main:app --env-file .env --reload

# 3. Frontend (separate terminal, from the project root)
python3 -m http.server 5500 --directory frontend
```

Open `http://localhost:5500` — upload a resume PDF, review the parsed fields, then either
**Approve**, or type a correction and **Send Corrections** to watch it loop back through
the gate.

Lint + test:

```bash
uv run ruff check .
uv run pytest tests/
```

Run the parse eval (real OpenAI calls, not part of CI):

```bash
uv run --env-file .env python -m tests.eval.eval_parse
```

## Exit criteria

| Criterion | Status |
|---|---|
| Upload → see the parsed result, through the UI | ✅ |
| Approve or send corrections → stored, approved resume | ✅ |
| Corrections loop back through the review gate | ✅ |
| CI green (`ruff check .` on the whole repo) | ✅ |
| **MVP complete (A + B + C)** | ✅ |

## Notes

- Model is still **`gpt-4o-mini`** as a placeholder — pinning after a feasibility spike
  remains open, non-blocking.
- `GET /resumes/{id}/parse` exists but isn't called by the frontend yet — a capability
  ahead of its use.
- The code walkthrough is gitignored (`/docs/walkthroughs/`) — a working resource, not yet
  committed, meant to grow into a project doc site across future phases.
- GitHub issue #6 closed 2026-07-12.

## What comes next — Phase D

Job search: Adzuna behind a `JobSource` interface, plus a pick-job HITL gate. ADR-0014
already settled the ranking approach (LLM reranker over Adzuna's candidate set, embeddings
deferred until scale demands them) — Phase D is where that gets built.

Full phase plan: [docs/roadmap.md](docs/roadmap.md).
