# ADR-0005: Self-hosted Langfuse for LLM observability and tracing

Status: Accepted
Date: 2026-06-28

## Context
We want tracing of LLM calls (inputs, outputs, token counts, cost, latency, nested
agent steps) wired in from day one — both for debugging and to feed eval datasets.
Resumes are PII, so trace data should stay local. We also want a framework-agnostic,
open-source tool with native LangChain/LangGraph integration.

## Decision
**Self-host Langfuse** via docker-compose and wire its LangChain callback handler
into the LangGraph runs.

## Alternatives considered
- **LangSmith** — excellent, but proprietary and cloud-first; sends PII off-machine
  by default and leans toward the LangChain ecosystem.
- **No tracing** — rejected; observability is a Phase-A foundation, not an add-on.

## Consequences
- (+) PII stays local; open source; framework-agnostic; native LangGraph
  integration; traces feed the eval datasets.
- (−) Heavier infrastructure — the v3 stack is ~6 containers (postgres, clickhouse,
  redis, minio, langfuse-web, langfuse-worker) on top of the app.