# ADR-0006: Docker + docker-compose for local environment and packaging

Status: Accepted
Date: 2026-06-28

## Context
The system is multi-service from the start: the FastAPI app plus the self-hosted
Langfuse stack and its datastores (ADR-0005). We need a reproducible local
environment that runs them together, and a packaging path that carries forward to
deployment.

## Decision
**Containerize the app** (Dockerfile) and orchestrate the full local stack with
**docker-compose**. The compose file brings up the app alongside the Langfuse
services.

## Alternatives considered
- **Run services natively** on the host — fragile, prone to environment drift, hard
  to reproduce across machines.
- **Heavier orchestrators (e.g. Kubernetes)** — overkill for local development at
  this stage; revisit only for production scale.

## Consequences
- (+) Reproducible multi-service environment; the same images carry toward
  deployment; isolates the ~6-container Langfuse stack cleanly.
- (−) Build/run overhead and meaningful resource use on the dev machine.