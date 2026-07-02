# ADR-0013: Separate compose stacks for app and Langfuse (local dev)

Status: Accepted
Date: 2026-07-01

## Context
Self-hosted Langfuse (ADR-0005) is not one container — it is a ~6-service stack
(`langfuse-web`, `langfuse-worker`, `postgres`, `clickhouse`, `redis`, `minio`)
shipped as an upstream docker-compose file, with several `# CHANGEME` secrets.
ADR-0006 chose docker-compose for local orchestration and assumed a single compose
file brings up the app *alongside* the Langfuse services, with the app containerized.

Phase A (walking skeleton) needs a trace target and an app Postgres, but the app does
no database work yet, and the priority is a light, reproducible dev loop. Folding
everything into one hand-maintained compose would mean owning Langfuse's 6 services
plus its secrets, and resolving a Postgres port collision — both the app db and
Langfuse's own Postgres default to `5432`.

## Decision
Keep **two separate compose stacks** for local development:
- **This repo's `docker-compose.yml` runs only the app's Postgres** (`postgres:16`),
  published on host port **5433** to avoid colliding with Langfuse's `5432`.
- **Langfuse runs from its official upstream compose**, cloned outside this repo and
  consumed as-is (not vendored or hand-merged).

Run the **FastAPI app on the host** (`uv run uvicorn`) during Phase A rather than in a
container, so `localhost` resolves directly to both stacks with no container-network
rewiring. This **refines ADR-0006**'s "containerize the app" for the early phases;
containerizing the app is deferred until a deploy path needs it.

## Alternatives considered
- **Single combined compose** (vendor Langfuse's services, or use Compose `include:`)
  — gives one `docker compose up`, but you then maintain/version Langfuse's full stack
  and secrets and pay a heavier boot every cycle. Rejected for the walking skeleton;
  revisit if a one-command full-stack boot becomes worth the weight.
- **Defer the app DB entirely to Phase B** — thinnest possible slice, but diverges
  from the roadmap's "bring up Postgres in Phase A"; we want the rails proven now.

## Consequences
- (+) `docker-compose.yml` stays one service we fully own; Langfuse stays
  upstream-maintained (upgrade by pulling the clone, not diffing interleaved YAML).
- (+) Light dev loop: leave Langfuse running, restart only the small app db.
- (+) No port collision; app-on-host means plain `localhost` works for both
  `DATABASE_URL` (`5433`) and `LANGFUSE_HOST` (`3000`) — no container networking.
- (−) Two `docker compose up` commands; the Langfuse clone lives outside the repo, so
  the full local stack is not reproducible from this repo alone (one-time setup).
- (−) The app is not containerized yet — a Dockerfile/app service is future work
  (refines ADR-0006), to be added when deployment (Phase H) needs it.

Refines ADR-0006 (local orchestration); builds on ADR-0005 (Langfuse) and
ADR-0009 (Postgres).