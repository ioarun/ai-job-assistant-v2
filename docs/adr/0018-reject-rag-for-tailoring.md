# ADR-0018: Reject RAG for Phase F tailored-generation grounding

Status: Accepted
Date: 2026-07-14

## Context
`docs/roadmap.md`'s Phase F section, written before this phase was detailed, committed
in writing to "RAG over the applicant's own corpus (past resumes/projects)" as the
grounding mechanism for tailored-resume and cover-letter generation, and
`docs/responsible-ai.md` similarly referenced "RAG corpus grounding" as something to
confirm works before Phase F ships.

When Phase F was actually detailed, two facts changed the picture:
1. The applicant's "corpus" in this product is currently **a single resume** — there is
   no multi-resume history, portfolio-document store, or any other second source to
   retrieve across. Retrieval only earns its complexity when there's a meaningful corpus
   to retrieve *from*; one document isn't that.
2. A single resume (~1-2 pages of extracted text) trivially fits in one LLM context
   window, the same situation ADR-0015 already reasoned through for Phase B's parsing
   stage.

## Decision
**Ground Phase F's tailored-resume and cover-letter generation directly on the
applicant's full raw resume text, passed straight into the prompt** — the same pattern
already used by `app/parse.py::parse_resume()` — rather than building a chunk + embed +
retrieve pipeline. No vector store is introduced for this phase.

## Alternatives considered
- **RAG over the applicant's corpus (chunk + embed + retrieve)** — the roadmap's original
  sketch. **Rejected**, generalizing ADR-0015's reasoning from extraction to generation:
  the source text already fits directly in the prompt, and there is only one document to
  retrieve over right now, so retrieval would add real infrastructure (pgvector or a
  dedicated vector store, chunking strategy, embedding calls) for no measurable grounding
  benefit over just using the full text. The no-fabrication requirement is enforced
  instead by a hard eval gate (`tests/eval/eval_tailor.py`) — a code-based skill-coverage
  check plus a narrowly-scoped coded LLM-judge comparing generated text against the
  source resume — not by the retrieval mechanism itself.

## Consequences
- (+) Phase F stays a thin vertical slice — no new infrastructure dependency.
- (+) Groundedness is enforced by prompt design + an eval hard gate, the same pattern
  already proven out in Phases B and E, rather than a new, unproven mechanism.
- (−) If a future phase introduces multiple resume versions, portfolio documents, or any
  other real multi-document corpus, retrieval will earn its complexity again — revisit
  with a new ADR at that point rather than reopening this one.
- `docs/roadmap.md` and `docs/responsible-ai.md`'s RAG references for Phase F are updated
  to match this decision.
