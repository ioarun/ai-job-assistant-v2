# Phase E — Gap Analysis

> Part of the [AI Job Assistant](README.md) phased build. Phase E builds on the
> picked job from [Phase D](README_D.md).

## Goal

For the applicant's picked job, compute a match score and honest skill gaps. PRD
stage 3.

## What was built

| Piece | Where | Notes |
|---|---|---|
| `GapReport` schema | `app/schemas.py` | `match_score` (0-100), `matched_skills`, `missing_skills` |
| `analyze_gap()` | `app/gap_analysis.py` | Single OpenAI Structured-Outputs call, `temperature=0`, `PROMPT_VERSION = "gap-v1"` — not hand-rolled skill diffing |
| Endpoint | `app/main.py` `POST /jobs/{job_pick_id}/gap-analysis` | Plain FastAPI — looks up the `JobPick`, finds the resume's latest approved `ParseRun`, calls `analyze_gap` |
| Frontend | `frontend/index.html` | "Run Gap Analysis" button on the picked-job view, `renderGapReport()` |
| Eval | `tests/eval/eval_gap_analysis.py` | Code-based precision/recall on matched + missing skills (eval-strategy §6, bar ≥80%), hard zero-fabrication gate |
| Fixtures | `tests/eval/fixtures/gap_1_*`, `gap_2_*` | Fresh, dedicated synthetic resume×job pairs — not reused from Phase B's `sample_resume_*` |

## Key decisions

- **No agent, no LangGraph for this phase either.** Same reasoning as Phase D: the
  process (fetch approved resume → one Structured-Outputs call → return) is fixed and
  known, and nothing pauses mid-computation waiting on a human — the endpoint completes
  and returns in one shot. The only LLM involvement is content judgment (scoring fit and
  identifying gaps), not autonomous multi-step reasoning.
- **Upskilling resource suggestions removed from project scope entirely** (ADR-0017) —
  not deferred to a later phase, genuinely out of scope with no committed return date.
  Phase E is gap analysis only.
- **Eval grader scores `matched_skills`/`missing_skills`, not `match_score`.** There's no
  principled way to hand-author a single "correct" 0-100 number for a synthetic fixture;
  set precision/recall on the two skill lists is deterministic and matches
  eval-strategy §3's preferred "code-based" grader.
- **Bar set at ≥80%**, closing the `[OPEN]` item that had sat unresolved across
  `eval-strategy.md`, `prd.md`, and `roadmap.md` since Phase 0. Reasoning: between
  Phase B's 95% (objective field extraction) and Phase D's 70% (subjective, live
  relevance judgment); gap analysis is grounded/checkable like Phase B but involves the
  model's implicit judgment about what "satisfies" a requirement. 80% also matches an
  existing precedent already in `eval-strategy.md` §6 for tailored-resume coverage, so
  it's not an arbitrary new number.
- **Fresh fixtures, not reused from Phase B.** Coupling `gap_analysis` fixtures to the
  parse eval's `sample_resume_*` files would mean a Phase B fixture edit could silently
  break Phase E's eval.

## In depth

### A phrasing bug the eval caught, that manual reading missed

The first real eval run failed the 80% bar badly (60.42% mean accuracy) — but
`matched_skills` scored a perfect 100%/100% on both fixtures. All the damage was in
`missing_skills` (0%/0% on one fixture). A quick manual read of the gap report looked
fine — the *identified* gaps were genuinely correct. The eval's exact-string set matching
surfaced something manual inspection didn't: the model was returning `missing_skills` as
full sentences (`"Experience with Kubernetes"`) while `matched_skills` stayed terse
(`"Kubernetes"`) — a real format inconsistency in the artifact, not just an eval
nuisance. Downstream (rendering as tags in the UI, or feeding Phase F's tailoring), that
inconsistency would have been a product bug too. Fixed at the root — `SYSTEM_PROMPT` in
`app/gap_analysis.py` now explicitly requires both lists to be short skill/technology
names — rather than loosening the grader to tolerate paraphrasing. Both gates passed on
the next run.

## Running it locally

Prereqs: same as Phase D (Postgres, Langfuse, Adzuna credentials in `.env`).

```bash
docker compose up -d
uv run alembic upgrade head
uv run uvicorn app.main:app --env-file .env --reload
python3 -m http.server 5500 --directory frontend   # separate terminal
```

Open `http://localhost:5500` — upload → approve → search → pick → **Run Gap Analysis**.

Run the eval (real OpenAI calls, static fixtures — not part of `pytest`/CI):

```bash
uv run --env-file .env python -m tests.eval.eval_gap_analysis
```

Lint + test:

```bash
uv run ruff check .
uv run pytest tests/
```

## Exit criteria

| Criterion | Status |
|---|---|
| Gap report (`match_score`/`matched_skills`/`missing_skills`) returned for a resume×job pair | ✅ |
| Precision/recall ≥80% on matched + missing skills, zero fabrication (eval-strategy §6) | ✅ both fixtures pass; `tests/eval/eval_gap_analysis.py` |
| Frontend visually verified in a browser | ✅ verified end-to-end 2026-07-14 |
| CI green (`ruff check .` on the whole repo) | ✅ confirmed 2026-07-15 |

## Notes

- Model is still **`gpt-4o-mini`** as a placeholder throughout — pinning remains open,
  non-blocking.
- GitHub issue #8 closed 2026-07-14. Its one open exit-criteria item (whole-repo lint
  check) was confirmed passing 2026-07-15.
- `pytest tests/` confirmed the eval scripts (all three now) are not collected —
  `tests/eval/` stays outside default test discovery by convention, matching Phase B/D.

## What comes next — Phase F

Tailored resume + cover letter for the picked job: grounded generation over the
applicant's own corpus (raw resume text, chunked — not the structured `ParsedResume`),
with a zero-fabrication hard gate and a HITL approve gate before anything is finalized.

Full phase plan: [docs/roadmap.md](docs/roadmap.md).
