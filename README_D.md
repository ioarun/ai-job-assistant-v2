# Phase D — Job Search

> Part of the [AI Job Assistant](README.md) phased build. Phase D is the first
> Post-MVP slice — see [Phase C](README_C.md) for the MVP it builds on.

## Goal

Given an approved resume, search for relevant jobs and let the applicant pick one.
PRD stage 2.

## What was built

| Piece | Where | Notes |
|---|---|---|
| Adzuna credentials | `app/config.py`, `.env.example` | `ADZUNA_APP_ID`, `ADZUNA_API_KEY`, `ADZUNA_COUNTRY` |
| `JobPosting` schema | `app/schemas.py` | title, company, location, description, url, salary range |
| `JobSource` interface + `AdzunaJobSource` | `app/job_source.py` | ADR-0007's pluggable interface — a `Protocol`, not inheritance; real Adzuna response fields verified against their docs |
| LLM reranker | `app/rank.py` | ADR-0014: Structured-Outputs call scores each job against the structured `ParsedResume`; sorted by score **in code**, not trusted from the model |
| `JobPick` DB model + migration | `app/models.py`, `migrations/` | Snapshots the picked job's full data (title, description, score, reason) rather than a bare reference — Adzuna listings can change or expire |
| Endpoints | `app/main.py` `POST /jobs/search`, `POST /jobs/pick` | Plain FastAPI, no LangGraph — explained below |
| Frontend | `frontend/index.html` | Search (keywords + optional location) → ranked results with fit score + grounded reason → pick, or search again |
| Eval | `tests/eval/eval_job_search.py` | Interactive precision@10 (eval-strategy §6, bar ≥70%) |

## Key decisions

- **No agent, no LangGraph for this phase.** Two architecture pivots were floated and
  both declined on reflection: (1) reframing the whole job-search flow as an
  agent-with-tools, and (2) modeling the pick gate as a LangGraph `interrupt()` node like
  Phase C's review gate. Neither earns its complexity here — the process (fetch → rank →
  pick) is fixed and known upfront, and unlike the review gate, nothing pauses
  mid-computation waiting on a human: `/jobs/search` completes and returns a full ranked
  list in one shot, and picking is a separate, independent, stateless call. The "search
  again with different keywords" case that *sounds* like Phase C's `revise` loop turns
  out not to need one either — it's just calling `/jobs/search` again.
- **ADR-0014 (already accepted before this phase) governs ranking** — LLM reranker over
  Adzuna's candidate set, not embeddings/vector similarity. The original roadmap sketch
  ("first embeddings + vector store") is stale; ADR-0014 explicitly deferred that to a
  future, scale-driven decision.
- **`JobPick` snapshots full job data**, not just a foreign reference, since Adzuna
  listings aren't stable over time — the record of what the applicant actually saw and
  chose has to be self-contained.
- **LLM-as-judge doesn't require new code.** Demonstrated directly in-conversation:
  reading real job descriptions against the real resume and giving genuine relevance
  verdicts is exactly what an LLM-judge is — no separate OpenAI call needed to *do* it.
  A **coded, automated** judge (for unattended/repeated runs) is deliberately deferred
  until real human-labeled data exists to calibrate it against — building one now would
  produce confident-looking numbers with no evidence they track real judgment.

## In depth

### A real Alembic bug, found and fixed mid-phase

Adding the `JobPick` model triggered `alembic revision --autogenerate`, which diffed the
live database against `app/models.py` — and found LangGraph's checkpoint tables (real,
but deliberately not declared in our models; ADR-0011's own caveat). Alembic concluded
they shouldn't exist and generated `DROP TABLE` for all four; applying it destroyed the
paused state of every resume then sitting in `awaiting_review`. The fix:
`migrations/env.py` now excludes those tables from autogenerate diffing entirely via an
`include_object` callback — verified by generating a fresh migration afterward and
confirming it detected zero drift. Full writeup in ADR-0011's addendum.

### Two architecture questions, resolved by asking "does this actually need to pause?"

Both the agent-with-tools pivot and the graph-based pick gate are *possible* — LangGraph
could model either. The deciding question wasn't capability, it was necessity: is there
a computation that genuinely needs to pause and resume across an unpredictable gap? Phase
C's review gate has one (a human may take hours reviewing a parse). Phase D's search and
pick don't — search runs to completion synchronously, and picking is stateless. Building
graph machinery for a process with no pause to model would be complexity without a job
to do.

### The eval needed a fundamentally different grader than Phase B's

Phase B's eval has objective ground truth — a synthetic resume with a hand-authored
expected `ParsedResume`. Job relevance has no such ground truth; it's a judgment call,
and real Adzuna results aren't static like the Phase B fixtures. `eval_job_search.py`
reuses the *exact* production search+rank pipeline and asks a human to label the top 10 —
matching eval-strategy's "human (+ LLM-judge to scale)" grader for this stage exactly.

## Running it locally

Prereqs: same as Phase C, plus Adzuna credentials (`developer.adzuna.com`) in `.env`.

```bash
docker compose up -d
uv run alembic upgrade head
uv run uvicorn app.main:app --env-file .env --reload
python3 -m http.server 5500 --directory frontend   # separate terminal
```

Open `http://localhost:5500` — upload → approve → **Search for Jobs** → pick.

Run the precision@10 eval (interactive, real OpenAI + Adzuna calls):

```bash
uv run --env-file .env python -m tests.eval.eval_job_search <resume_id> "<keywords>" [location]
```

Lint + test:

```bash
uv run ruff check .
uv run pytest tests/
```

## Exit criteria

| Criterion | Status |
|---|---|
| A query returns ranked, relevant listings | ✅ verified — real Adzuna + reranker, grounded reasoning |
| The applicant picks one | ✅ `POST /jobs/pick`, persisted and confirmed in the DB |
| Relevance ≥ precision@10 70% (eval-strategy §6) | ⬜ **open** — one ad-hoc judged run scored 60% (FAIL); needs a proper recorded run, and likely reranker-prompt iteration |
| Frontend visually verified in a browser | ⬜ **open** — API-level verified only; pending manual check |
| CI green (`ruff check .` on the whole repo) | ✅ |

## Notes

- Model is still **`gpt-4o-mini`** as a placeholder throughout (parse, rerank) — pinning
  remains open, non-blocking.
- GitHub issue #7 closed 2026-07-13, with the two open exit-criteria items called out
  explicitly in the closing comment — "closed" here means code-complete, not
  fully-verified.
- A coded LLM-judge for the precision@10 eval is deliberately deferred (see memory
  `llm-judge-deferred` / this README's Key Decisions) until real human-labeled rounds
  accumulate.

## What comes next — Phase E

Gap analysis: for the picked job, a single OpenAI Structured-Outputs call returning a
`GapReport` (match score, matched skills, missing skills) — not hand-rolled skill
diffing, per the earlier design session's redesign. Upskilling resource suggestions must
be retrieved from a curated catalog, never generated, to avoid hallucinated links.

Full phase plan: [docs/roadmap.md](docs/roadmap.md).
