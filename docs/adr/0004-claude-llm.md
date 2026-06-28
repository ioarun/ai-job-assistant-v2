# ADR-0004: Anthropic Claude (`claude-opus-4-8`) as the LLM

Status: Superseded by [ADR-0010](0010-openai-llm.md)
Date: 2026-06-28

## Context
The pipeline needs a capable LLM for resume parsing, job matching, gap analysis,
and resume/cover-letter tailoring. We want the latest, most capable model, with
strong tool-use and structured-output support, integrating with LangGraph (via
`langchain-anthropic`).

## Decision
Use **Anthropic Claude**, defaulting to **`claude-opus-4-8`**. Treat the
`claude-api` skill (model IDs, parameters, SDK usage) as the source of truth rather
than memory; revisit the model choice per task as cost/quality data accrues.

## Alternatives considered
- **OpenAI GPT models** — capable, but the project standardizes on Claude.
- **Local/open models** — lower cost and fully local, but lower capability for this
  reasoning-heavy work; may be revisited for specific cheap subtasks.

## Consequences
- (+) Top-tier capability, adaptive thinking, tool use, structured outputs.
- (−) External dependency and per-token cost; the model ID will evolve over time
  (mitigated by centralizing model selection in one place).