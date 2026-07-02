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
- The app is **not** containerized yet (runs on host); a Dockerfile/app service is future
  work (Phase H), as recorded in ADR-0013.

Full phase plan: [docs/roadmap.md](docs/roadmap.md).
