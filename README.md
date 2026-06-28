# AI Job Assistant

The assistant is designed to help users find AI job opportunities, identify gaps in their knowledge, and assist in the application process by tailoring resumes and cover letters to specific job descriptions.

## How does it work?

1. Let's users type in the description of the job they are interested in and upload their resume. 
2. The assistant searches for relevant job opportunities based on the provided description.
3. It then let's users pick from the list of the jobs returned and generates a tailored resume and cover letter for the selected job.
4. Additionally, it finds gaps in the user's knowledge based on the job description and provides resources/projects suggestion to help fill those gaps.

## Development phases

The project is built in phases following a modern (2026) software/AI engineering
lifecycle. This section is appended as each phase completes.

**Legend:** ✅ Done · 🟡 In progress / partial · ⬜ Not started

### Phase 0 — Ideation & Planning

Produce the planning artifacts and a plan for every subsequent phase.

#### The planning sequence (how we work through Phase 0)

We move from "outside & vague" to "inside & precise" — each step answers one
question before the next builds on it:

| Step | Question it answers | View |
|---|---|---|
| Ideation | What is this, roughly? | — |
| PRD | What & why? What's in scope? (ground truth for *what*) | — |
| ADRs | Which decisions did we make, and why? (ongoing — accrue as we decide) | — |
| Context diagram | Who/what does the system talk to in the world? (the boundary) | structural |
| Flow diagram | What happens, in what order, with which human approvals? | behavioral |
| Architecture diagram | What are the internal building blocks, and how do they wire up? | structural |
| Design Doc / RFC | How is it built? (ground truth for *how*) | — |
| Eval strategy | How do we measure whether the AI output is good? | — |
| Roadmap | What are the build phases (A–H), and in what order? | — |

Two **lenses** we keep separate: *structural* views show what **is** there (context,
architecture); *behavioral* views show what **happens** (flow). Two **authorities**
we keep separate: the **PRD owns _what & why_**, the **RFC owns _how_** — so scope
debates and design debates don't leak into each other.

**Exit criteria:** every row below is ✅.

| Artifact | Description | Location | Status |
|---|---|---|---|
| PRD | Product requirements (what & why), success + eval criteria | `docs/prd.md` | ✅ |
| ADRs | Decision records for stack & key choices (0001–0010) | `docs/adr/` | ✅ |
| Context diagram | System as a black box + external actors/systems (C4 L1) | `docs/diagrams/context.md` | ✅ |
| Flow diagram | Stages as input→output with HITL gates (MVP/Post-MVP/Future) | `docs/diagrams/flow.md` | ✅ |
| Architecture diagram | Internal containers and who calls whom (C4 L2) | `docs/diagrams/architecture.md` | ✅ |
| Design Doc / RFC | The technical *how*; ties diagrams + decisions + risks together | `docs/design.md` | ✅ |
| Eval strategy | How we measure LLM output quality (eval sets, rubrics, judge) | `docs/eval-strategy.md` | ✅ |
| Responsible-AI risk register | Domain risks + mitigations (hiring high-risk, ToS, no fabrication) | `docs/prd.md` §7 | 🟡 |
| Roadmap + per-phase plans | Phase A–H breakdown with goals/scope/exit criteria | `docs/roadmap.md` | ⬜ |
| Project board | GitHub Projects board seeded from the roadmap | GitHub Projects | ⬜ |

_Subsequent phases (A — Walking skeleton, B — Resume intake, …) will be appended here as we reach them._

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
