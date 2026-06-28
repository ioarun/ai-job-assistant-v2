# AI Job Assistant

The assistant is designed to help users find AI job opportunities, identify gaps in their knowledge, and assist in the application process by tailoring resumes and cover letters to specific job descriptions.

## How does it work?

1. Let's users type in the description of the job they are interested in and upload their resume. 
2. The assistant searches for relevant job opportunities based on the provided description.
3. It then let's users pick from the list of the jobs returned and generates a tailored resume and cover letter for the selected job.
4. Additionally, it finds gaps in the user's knowledge based on the job description and provides resources/projects suggestion to help fill those gaps.

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
