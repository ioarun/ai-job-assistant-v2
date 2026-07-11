# Phase A — Walking Skeleton

> Part of the [AI Job Assistant](README.md) phased build. Phase A is the first
> implementation slice — see [Phase 0](README_0.md) for the planning that preceded it.

## Goal

Prove the whole toolchain works end-to-end on a trivial payload **before** any resume
logic exists: the app runs, makes **one OpenAI call**, and that call shows up as a
**trace in Langfuse**, with **CI green**. These are the rails every later phase rides on.

## What was built

| Piece | Where | Notes |
|---|---|---|
| FastAPI app | `app/main.py` | `GET /health` (200, no external calls) + `GET /hello` (one traced OpenAI call) |
| Config | `app/config.py` | lazy, validated `pydantic-settings`; no secrets touched at import |
| Local DB | `docker-compose.yml` | app Postgres on host port **5433** |
| Smoke test | `tests/test_health.py` | in-process `TestClient` on `/health` (no Docker/keys needed) |
| CI | `.github/workflows/ci.yml` | `uv sync → ruff check → pytest` on PRs to `master` |
| Lint | `pyproject.toml` `[tool.ruff]` | E / F / I rule families |

**Observability:** `/hello` uses the `langfuse.openai` drop-in, so every OpenAI call is
auto-traced in the self-hosted Langfuse (ADR-0005).

## Key decision — ADR-0013 (separate compose stacks)

Langfuse self-hosted is a 6-service stack that ships its own Postgres on `5432`. Rather
than vendor/maintain that, our `docker-compose.yml` runs only the app db (on **5433**), and
Langfuse is consumed from its upstream compose. The app runs on the **host** during Phase
A, so plain `localhost` reaches both — no container networking. See
[docs/adr/0013-separate-compose-stacks.md](docs/adr/0013-separate-compose-stacks.md).

## In depth

### Why a walking skeleton

A walking skeleton is a **thin vertical slice that touches every layer but does almost
nothing**: the app runs → makes **one OpenAI call** → that call shows up as a **trace in
Langfuse** → **CI is green**. That's the entire scope. Why bother before any resume logic?

- **Everything reversible and observable** is a founding principle. Wire up tracing, CI,
  and config *on day one, on a trivial payload*, so every later phase rides on rails that
  are already proven.
- Debugging plumbing *while also* debugging AI logic is the trap — separate them. Prove
  the plumbing first, then build the intelligence on top.
- The beginner move is to start coding resume parsing immediately. The senior move is to
  prove the plumbing first. **MVP = a thin slice, not everything at 50%.**

### The decisions worth understanding

1. **`uv` for everything** (ADR-0001) — one tool replacing pip + venv + pip-tools +
   lockfiles. The modern 2026 default for Python dependency/env/lockfile management.
2. **Drop-in tracing** (ADR-0005) — one import line does the work:
   ```python
   from langfuse.openai import openai   # same OpenAI API, auto-traced
   ```
   **Zero call-site changes.** Normal OpenAI code, and every call automatically appears as
   a trace in the self-hosted Langfuse.
3. **Lazy singleton config** — `@lru_cache def get_settings()` builds settings on *first
   call*, never at import time. The payoff: **CI can import the app without any secrets
   present.** `.env.example` is committed (blank); `.env` is gitignored (real values).
4. **A credential-wiring gotcha** — the OpenAI and Langfuse SDKs read raw `os.environ`,
   **not** the Pydantic `Settings` object. The bridge is `uvicorn --env-file .env`, which
   loads `.env` into the process environment for the SDKs. (An accepted alternative is to
   assign credentials manually from `get_settings()`; the env-file approach is the default.)
5. **Separate Docker stacks** (ADR-0013) — the key architectural decision, detailed above.
6. **`flush()` is demo-only** — Langfuse batches traces in the background, so
   `get_client().flush()` forces the trace out *before the response returns* for immediate
   visibility. This would **not** be done per-request in production.

### The engineering-process throughline

Phase A is run the way a 2026 frontier-AI org would, right-sized for a solo project:

- **Phase 0 came first** — PRD → three diagrams (context / flow / architecture) → RFC →
  ADRs → eval strategy → responsible-AI risk register → roadmap. *Artifacts before code.*
- **ADRs** record every real decision (the decision + alternatives + the *why*) so they
  are never re-litigated later.
- **Evals are the new unit tests** — you can't assert `output == expected` on an LLM. This
  practice is set up now and pays off in Phase B.
- **Responsible AI as a first-class risk** — hiring is *high-risk* under the EU AI Act and
  NYC Local Law 144; "tailoring" must never become **fabrication**; a human gate sits
  before any outward/irreversible action.

## Running it locally

Prereqs: [`uv`](https://docs.astral.sh/uv/), Docker, an OpenAI API key, and a self-hosted
Langfuse instance.

```bash
# 1. Config — copy the template and fill in real values (never commit .env)
cp .env.example .env
#    set OPENAI_API_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY

# 2. App database
docker compose up -d

# 3. Langfuse (self-hosted, per ADR-0013) — start it from its upstream compose,
#    create a project, and copy that project's public/secret keys into .env
#    https://langfuse.com/self-hosting/docker-compose

# 4. Run the app (loads .env into the process env for the SDKs)
uv run uvicorn app.main:app --env-file .env --reload
```

Verify:

```bash
curl localhost:8000/health     # -> {"status":"ok"}
curl localhost:8000/hello      # -> a sentence from OpenAI
# Langfuse UI (http://localhost:3000) -> Traces -> the `hello-phase-a` trace appears
```

Lint + test:

```bash
uv run ruff check .
uv run pytest
```

## Exit criteria

| Criterion | Status |
|---|---|
| App runs; `/health` returns 200 | ✅ |
| `/hello` → OpenAI response **and** a `hello-phase-a` trace in Langfuse | ✅ |
| CI green on a PR to `master` | ⬜ (runs on push/PR) |

## Notes

- `model="gpt-4o-mini"` in `/hello` is a **placeholder** — the real model is pinned after a
  short feasibility spike, before Phase B.
- The project uses **OpenAI** as the LLM (ADR-0010 supersedes the earlier ADR-0004 "Claude"
  decision) — stated here so the older ADR doesn't cause confusion.
- The app is **not** containerized yet (runs on host); a Dockerfile/app service is future
  work (Phase H), as recorded in ADR-0013.

## What comes next — Phase B

With the rails proven, Phase B is the first *real* AI slice: upload a resume → structured
parse → persist, fully traced, with a parse-quality **eval harness**. That is where the
LLM-specific engineering (structured outputs, fabrication guardrails, RAG-augmented
extraction, and dual-mode accuracy evaluation) begins.

Full phase plan: [docs/roadmap.md](docs/roadmap.md).
