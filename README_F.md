# Phase F — Tailored Resume + Cover Letter

> Part of the [AI Job Assistant](README.md) phased build. Phase F builds on the picked
> job from [Phase D](README_D.md) and the gap analysis from [Phase E](README_E.md).

## Goal

For the applicant's picked job, generate a role-tailored resume and cover letter that
improve fit **without fabricating anything**, behind a human review/approve gate. PRD
stages 4–5.

## What was built

| Piece | Where | Notes |
|---|---|---|
| `Resume.raw_text` | `app/models.py` | New column — raw resume text wasn't persisted anywhere before this phase; only the structured `ParsedResume` JSON survived |
| `TailorRun` DB model + migration | `app/models.py`, `migrations/` | Mirrors `ParseRun`'s shape (status/model/prompt_version + content), FK to `JobPick` — mutates in place per revise cycle, same as `ParseRun` |
| `TailoredResume`/`CoverLetter`/`TailorResult` schemas | `app/schemas.py` | Free-text `content` (Markdown) + a closed-vocabulary `emphasized_skills` sidecar copied verbatim from the parsed resume's skills |
| `app/tailor.py` | New module | `tailor_resume()` + `write_cover_letter()` (sequential — the letter is grounded on the *actual* tailored resume output) + `generate_tailored_docs()` combining both |
| `app/tailor_graph.py` | New LangGraph subgraph | A second `interrupt()`-based approve gate, same pattern as Phase C's review graph, on its own checkpointer thread namespace (`tailor:{job_pick_id}`) |
| Endpoints | `app/main.py` `POST/GET .../tailor`, `POST .../tailor/approve`, `POST .../tailor/corrections` | Mirrors the resume-parse endpoint group exactly |
| Frontend | `frontend/index.html` | "Generate Tailored Docs" button, a review view with approve/corrections controls identical in structure to the resume-review flow |
| Eval | `tests/eval/eval_tailor.py` | Code-based skill-coverage check (bar ≥80%) + a narrowly-scoped coded LLM-judge for the zero-fabrication hard gate |
| ADR-0018 | `docs/adr/0018-reject-rag-for-tailoring.md` | Rejects RAG/vector-store grounding for this phase |

## Key decisions

- **No RAG, no vector store.** Generation grounds directly on the applicant's full raw
  resume text in the prompt — same pattern as `app/parse.py::parse_resume()`. A single
  resume trivially fits in one context window, and there's currently only *one* resume
  as "corpus" anyway (no multi-resume history exists yet). This generalizes ADR-0015's
  rejection of RAG for Phase B parsing to Phase F's generation task — see ADR-0018.
- **Export format: plain text/Markdown**, not PDF. Closes PRD §7's long-standing
  `[OPEN]` item — PDF templating is explicitly deferred, not decided against forever.
- **Resume and cover letter built together**, sharing one grounding source, one
  no-fabrication hard gate, one approve gate — they're generated *sequentially*
  (resume first, then the letter conditioned on the actual tailored resume output) so
  the two documents don't independently invent inconsistent framing.
- **Raw resume text now persisted on `Resume`, not `ParseRun`** — it's a property of
  the upload itself and doesn't change across correction/revise cycles, unlike
  `ParseRun.parsed`. Written once in `parse_node` (which already has a DB session open
  and the extracted text in scope), idempotently overwritten on each revise loop.
- **A second LangGraph subgraph, not a new node bolted onto the existing one.** The
  tailor flow has a genuine pause-for-human-review need, just like Phase C — unlike
  Phase D/E, which stayed as plain endpoints because nothing paused mid-computation
  there. Kept as its own graph (rather than extending `app/graph.py`) because it has a
  different trigger (`job_pick_id`, not a resume upload) and a different lifecycle.
- **Thread-id collision, caught before it could bite**: `job_pick_id` and `resume_id`
  are both independent autoincrement PKs starting at 1 — sharing the same
  `AsyncPostgresSaver` checkpointer with the existing graph's bare `str(resume_id)`
  thread-id scheme would have silently collided the first time both hit the same
  integer. Fixed by namespacing the new graph's threads as `f"tailor:{job_pick_id}"`;
  the shipped Phase C code was left untouched.
- **A narrowly-scoped coded LLM-judge for the fabrication hard gate** — a deliberate
  exception to the "defer coded LLM-judges" precedent from Phase D. That precedent was
  about a *subjective relevance score* with no ground truth to calibrate against; this
  judge does a binary "is this claim grounded in the source text, yes/no" check, closer
  in kind to Phase B/E's deterministic fabrication checks, just needing semantic (not
  substring) matching because tailored output is paraphrased prose.

## In depth

### Why raw text needed a new column

Tracing the existing pipeline: `ingest_node` extracts text, `parse_node` sends it to
OpenAI and persists only the *structured* result (`ParseRun.parsed`) — the raw text
itself was discarded after use, existing only transiently in LangGraph's own checkpoint
state (no app-owned column, no defined read API). Since Phase F's whole grounding
strategy depends on the model seeing the original phrasing (not a re-serialized JSON
version of it), this had to become a first-class, durably persisted field before any
generation code could be written.

### The eval needed a different fabrication-check mechanism than Phase B/E

Phase B and E's fabrication checks are simple substring checks — they work because the
model's output there is short, atomic strings (skills) that either verbatim-match the
source or don't. Phase F's output is free-form, deliberately *paraphrased* prose — the
entire point of tailoring is to rewrite phrasing, so a substring check would flag almost
every sentence as "fabricated" even when it's a faithful rewrite. This forced a genuinely
different grader: a coded LLM-judge that reads the source resume and the generated text
and lists any claim not grounded in the source, explicitly told that paraphrasing is not
fabrication. Both fixtures passed cleanly (0 fabricated claims) on the first real run,
and a manual read of the generated output confirmed the content was genuinely grounded —
including one borderline case (an expressed interest in "healthcare data" in a cover
letter) that the judge correctly did not flag, since expressing enthusiasm for a domain
isn't a factual claim about past experience.

## Running it locally

Prereqs: same as Phase E.

```bash
docker compose up -d
uv run alembic upgrade head
uv run uvicorn app.main:app --env-file .env --reload
python3 -m http.server 5500 --directory frontend   # separate terminal
```

Open `http://localhost:5500` — upload → approve → search → pick → **Generate Tailored
Docs** → review → approve (or send corrections to trigger a full regeneration loop).

Run the eval (real OpenAI calls, static fixtures — not part of `pytest`/CI):

```bash
uv run --env-file .env python -m tests.eval.eval_tailor
```

Lint + test:

```bash
uv run ruff check .
uv run pytest tests/
```

## Exit criteria

| Criterion | Status |
|---|---|
| Tailored resume + cover letter generated for a resume×job pair, grounded on raw resume text | ✅ |
| Skill coverage ≥80%, zero fabrication (eval-strategy §6) | ✅ both fixtures pass; `tests/eval/eval_tailor.py` |
| Review/approve HITL gate, including the corrections/revise loop | ✅ verified end-to-end in browser 2026-07-15 |
| CI green (`ruff check .` on the whole repo) | ✅ verified 2026-07-15 |

## Notes

- Model is still **`gpt-4o-mini`** as a placeholder throughout (generation and the
  eval's judge) — pinning remains open, non-blocking.
- GitHub issue #9 closed 2026-07-15, with no open exit-criteria items this time — full
  local verification (lint, eval, and browser walkthrough) completed in one session.
- PDF export/templating stays explicitly deferred — Markdown/plain text is the shipped
  format for this phase.

## What comes next — Phase G

Advanced techniques: this is where the deliberately-deferred agent+tools architecture
(declined for Phases D–F) and genuine RAG (which ADR-0018 rejected here for lack of a
real multi-document corpus) finally earn their complexity — e.g. once multiple resume
versions or portfolio documents exist to retrieve across. Also: MCP servers/tools.

Full phase plan: [docs/roadmap.md](docs/roadmap.md).
