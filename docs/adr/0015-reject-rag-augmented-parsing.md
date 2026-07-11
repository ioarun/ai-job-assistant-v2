# ADR-0015: Reject RAG-augmented parsing for Phase B fabrication detection

Status: Accepted
Date: 2026-07-11

## Context
During a design discussion prior to Phase B implementation (recorded in
`claude.ai/03_07_phase_bcd_discussion_summary.md`), a "B2" extension was floated: chunk +
embed resume text into a vector store (Chroma), and use it for two purposes — (1)
retrieval-augmented context at extraction time, and (2) semantic (cosine-similarity)
fabrication-checking, as an alternative/supplement to strict string matching. This would
also have required semantic chunking (over fixed-size) to avoid blending unrelated
concepts into one embedding.

Phase B was then built as a **base slice only**: `pypdf` extraction (ADR-0012) → OpenAI
Structured Outputs parse (`temperature=0`, deterministic) → Postgres persistence
(`Resume`/`ParseRun`) → Langfuse tracing → a strict-string-match eval harness (3 synthetic
fixture pairs), which passed both the ≥95% accuracy bar and the zero-fabrication gate
cleanly and consistently.

## Decision
**Do not build the RAG-augmented/semantic parsing approach (the informally-named "B2")
for Phase B.** The base-slice strict string-matching approach is the final design for
Phase B's extraction context and fabrication detection.

## Alternatives considered
- **RAG-augmented parsing (Chroma dual-purpose chunking)** — chunk+embed resume text; use
  retrieved chunks as extraction context, and use the same collection for semantic
  (cosine-similarity) fabrication checking. **Rejected.** Adds a vector-store dependency,
  semantic-chunking complexity, and a second eval pathway (semantic vs. strict) for a
  single-resume, single-call extraction task where the whole source text already fits
  directly in the prompt. The presumed benefit (catching paraphrase-style non-fabrications,
  e.g. "Docker" vs. "containerization") was judged not to justify the added architecture
  for this phase.
- **Semantic (embedding-based) fabrication eval alongside strict string-match** — same
  rejection rationale; strict string-matching alone, on `temperature=0`, has proven
  accurate and deterministic across all 3 eval fixtures.

## Consequences
- (+) Phase B stays a genuinely thin vertical slice; no new infrastructure (vector store)
  introduced for the parse step.
- (+) The eval harness stays simple: one scoring method, one fixture format, easy to
  extend with more fixtures later if needed.
- (−) Paraphrase-style extractions (a candidate's skill phrased differently than the
  resume's exact wording) will register as **fabrication** under strict string matching —
  a known false-positive mode. If real-world resumes hit this often enough to matter,
  revisit with a new ADR rather than reopening this one.
- Phase B is considered **done** (GitHub issue #5 closed 2026-07-11); no further
  parsing-architecture work is planned for this phase.

Supersedes the informally-flagged "RAG-augmented parsing" and "semantic chunking" ADR
placeholders noted in `claude.ai/03_07_phase_bcd_discussion_summary.md` — those are not
being written, as the underlying approach was rejected.
