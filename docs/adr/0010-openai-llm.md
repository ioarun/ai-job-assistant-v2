# ADR-0010: Use OpenAI as the LLM (supersedes ADR-0004)

Status: Accepted (supersedes ADR-0004)
Date: 2026-06-29

## Context
ADR-0004 chose Anthropic Claude (`claude-opus-4-8`) as the LLM. For this **personal
learning project**, the builder already has an OpenAI account and prefers to use
OpenAI. The pipeline is model-agnostic: the orchestration (LangGraph), observability
(Langfuse), database, and API do not depend on which LLM vendor is used, so the
vendor can change without touching the rest of the stack.

## Decision
Use **OpenAI** as the LLM provider, via the official `openai` Python SDK. The
**specific model is TBD** (decided after the feasibility spike, using real
quality/cost numbers), defaulting toward the current flagship for parse quality and
the lowest fabrication risk. Pin the exact model ID and Structured Outputs / file-input
API specifics from OpenAI's official docs at build time, not from memory.

## Alternatives considered
- **Anthropic Claude (ADR-0004)** — top-tier capability, but the builder prefers
  OpenAI and already has access; vendor parity is close enough for this project's needs.
- **Local / open models** — fully local (better PII posture, lower marginal cost),
  but lower capability for this reasoning-heavy work; may be revisited for specific
  cheap subtasks.

## Consequences
- (+) Uses the vendor the builder already has access to and wants.
- (+) OpenAI provides **Structured Outputs** (Pydantic/JSON-schema) and **PDF file
  inputs**, which cover the MVP parse design (RFC §6).
- (+) No other ADRs change: LangGraph integrates via `langchain-openai`, and Langfuse
  has a first-class OpenAI integration — so observability/orchestration are unaffected.
- (−) Supersedes ADR-0004; the `claude-api` skill is no longer the implementation
  source of truth (use OpenAI's official SDK + docs instead).
- (−) Exact model ID and params remain TBD until the spike.
- (−) Requires **OpenAI API access** (an API key + pay-as-you-go billing) — this is
  separate from a ChatGPT subscription, which cannot be called from code.
- (−) **PII:** resume contents are sent to OpenAI (a third party), same as any hosted
  LLM. Self-hosted Langfuse keeps *traces* local, but prompts still leave the machine —
  factor this into the data-handling/retention policy (PRD §7, RFC §9).