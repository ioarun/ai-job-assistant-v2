# ADR-0003: LangGraph for agent/LLM orchestration

Status: Accepted
Date: 2026-06-28

## Context
The product is a multi-step, stateful, **human-in-the-loop** agentic pipeline
(parse → search → gap analysis → tailor → apply) with branching and approval
gates. We need orchestration that models state, conditional flow, and pausing for
human input — and the project's learning goals include agentic AI and MCP.

## Decision
Use **LangGraph** to orchestrate the multi-step / multi-agent workflow, including
human-in-the-loop interrupts.

## Alternatives considered
- **Raw Anthropic SDK + a custom loop** — maximizes learning of agent fundamentals
  and avoids a framework, but is more to build and maintain for branching + HITL.
- **Other agent frameworks** — not chosen; LangGraph's graph/state model fits the
  staged pipeline well and pairs cleanly with Langfuse tracing (ADR-0005).

## Consequences
- (+) Graph + state model fits multi-step flow and HITL gates; native interrupts;
  good observability integration.
- (−) Adds a framework abstraction over the fundamentals; learning curve; couples
  to the LangChain ecosystem.