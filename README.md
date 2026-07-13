# AI Job Assistant

The assistant is designed to help users find AI job opportunities, identify gaps in their knowledge, and assist in the application process by tailoring resumes and cover letters to specific job descriptions.

## How does it work?

1. Let's users type in the description of the job they are interested in and upload their resume. 
2. The assistant searches for relevant job opportunities based on the provided description.
3. It then let's users pick from the list of the jobs returned and generates a tailored resume and cover letter for the selected job.
4. Additionally, it finds gaps in the user's knowledge based on the job description and provides resources/projects suggestion to help fill those gaps.

## Development phases

The project is built in phases following a modern (2026) software/AI engineering
lifecycle. Each phase gets its own README as it completes; the full plan lives in
[docs/roadmap.md](docs/roadmap.md).

**Legend:** ✅ Done · 🟡 In progress / partial · ⬜ Not started

| Phase | Focus | Details | Status |
|---|---|---|---|
| **0 — Ideation & Planning** | PRD, ADRs, diagrams, RFC, eval strategy, roadmap | [README_0.md](README_0.md) | ✅ |
| **A — Walking skeleton** | FastAPI + traced OpenAI + Langfuse + CI (the rails) | [README_A.md](README_A.md) | ✅ |
| **B — Resume parse slice** | upload → structured parse → persist, traced; parse eval | [README_B.md](README_B.md) | ✅ |
| **C — HITL review + minimal UI** | review gate + UI → **MVP complete** | [README_C.md](README_C.md) | ✅ |
| **D — Job search** | Adzuna behind `JobSource` + LLM reranker | [README_D.md](README_D.md) | 🟡 |
| **E — Gap analysis** | match score + honest gaps + upskilling resources | [roadmap](docs/roadmap.md) | ⬜ |
| **F — Tailored resume + cover letter** | grounded generation (no fabrication) | [roadmap](docs/roadmap.md) | ⬜ |
| **G — Advanced techniques** | multi-agent orchestration, better RAG, MCP | [roadmap](docs/roadmap.md) | ⬜ |
| **H — Auto-apply + productionization** | human-gated submit + deploy/monitoring | [roadmap](docs/roadmap.md) | ⬜ |

> **MVP = A + B + C.**

## Glossary

Shorthand used across the docs (`docs/`) and in discussion.

### Process & documents
| Term | Meaning |
|---|---|
| **PRD** | Product Requirements Document — *what & why* we're building (not *how*). See `docs/prd.md`. |
| **RFC / Design Doc** | Request for Comments — the technical *how*: architecture, components, data, trade-offs. |
| **ADR** | Architecture Decision Record — one decision + the alternatives + the *why*; numbered, dated, immutable. See `docs/adr/`. |
| **SDLC** | Software Development Life Cycle — plan → design → build → deploy. |
| **MVP** | Minimum Viable Product — the smallest valuable, shippable slice. |
| **HITL** | Human-in-the-loop — a human reviews/approves at key decision points. |
| **Eval** | Evaluation — measuring the quality of LLM output (the "tests" for AI features). |
| **CI/CD** | Continuous Integration / Continuous Delivery — automated test & release pipelines. |
| **SLO** | Service Level Objective — a target for reliability/latency. |
| **ToS** | Terms of Service — a third-party site/API's usage rules. |
| **PII** | Personally Identifiable Information — sensitive personal data (e.g. resumes). |

### Diagrams
| Term | Meaning |
|---|---|
| **Context diagram** | The system as one black box + external actors/systems (the boundary). |
| **Flow diagram** | The stages as input → output, with the HITL gates marked. |
| **Architecture diagram** ("arc") | Internal components and who calls whom. |

### AI / technical
| Term | Meaning |
|---|---|
| **LLM** | Large Language Model. |
| **RAG** | Retrieval-Augmented Generation — grounding the model in retrieved data. |
| **MCP** | Model Context Protocol — a standard for exposing tools/data to the model. |
| **Agent / agentic** | An LLM that plans and uses tools in a loop to accomplish a task. |
