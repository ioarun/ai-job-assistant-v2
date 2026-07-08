# ADR-0014: Job matching & ranking via LLM reranking (retrieve → rerank)

Status: Accepted
Date: 2026-07-03

## Context
Phase D (roadmap) returns job candidates from **Adzuna** (ADR-0007) via keyword search,
then must **rank them by fit** to the applicant's parsed resume (`ParsedResume`, Phase B)
before the human picks (flow.md gate 2).

The roadmap sketched "first embeddings + vector store (pgvector) for semantic match" as the
ranking mechanism. But keyword/embedding similarity captures **topical closeness, not
nuanced job fit** — seniority, must-have vs. nice-to-have skills, transferable experience,
location. An LLM given the resume + the listings can judge fit *with reasoning*.

Adzuna returns a **small candidate set** per query (tens, not thousands), so the whole set
can often be ranked directly by an LLM without a pre-filter.

## Decision
Rank Adzuna results with an **LLM reranker**: a second, **Structured-Outputs** LLM call
takes the **structured `ParsedResume`** as context plus the candidate listings and returns
per-job fit scores + grounded reasons; we **sort by score in code**. The human still picks
(gate 2).

- **MVP: LLM-rank the Adzuna results directly** — no vector store yet — because the
  candidate set is small.
- **Scale path: retrieve → rerank.** When the candidate set or a persistent job store grows
  large, introduce **embeddings as a cheap first-stage recall/pre-rank**, and keep the LLM
  as the **reranker over the top-K**. The vector store (likely pgvector) is a *separate,
  later* decision, adopted only when scale requires it.
- Pass the **structured `ParsedResume`**, not raw text; use **Structured Outputs** for the
  scores; rank only a bounded **top-K**; the reranker **scores/orders only** — it must not
  fabricate job or resume facts, and reasons must be grounded in the description + resume.
- Validate ranking quality with **precision@10** (eval-strategy §6), later scaled with an
  LLM-judge calibrated to human labels.

## Alternatives considered
- **Embeddings / vector similarity as the *primary* ranker** (original roadmap sketch) —
  cheap and scalable, but misses nuanced fit and gives no explanation. **Kept as the
  first-stage recall for scale, not the final ranker.**
- **Keyword / Adzuna relevance only** — no personalization to the resume. Rejected.
- **LLM listwise ranking of the full (large) set** — context-window limited, position-biased,
  and costly. Avoided by ranking only a top-K (pointwise scoring or small listwise batches).

## Consequences
- (+) Nuanced, **explainable** ranking that actually uses the resume; **simpler MVP** (no
  vector store needed initially); reuses the Structured-Outputs + Langfuse tracing patterns
  already in the stack.
- (+) Clear **scale path** (retrieve → rerank) with no rework — the LLM reranker stays;
  embeddings slot in front of it later.
- (−) Per-query LLM **cost/latency** for ranking; the ranker can be **noisy/position-biased**
  (mitigated by pointwise scoring, a bounded top-K, and the precision@10 gate).
- (−) Slightly **reorders roadmap Phase D**: LLM-rank first; embeddings/pgvector deferred to
  a later, scale-driven ADR.

Builds on ADR-0007 (Adzuna job source) and the Phase B `ParsedResume`; **defers the
vector-store choice (pgvector) to a future ADR**; validated by the precision@10 eval
(eval-strategy §6).
