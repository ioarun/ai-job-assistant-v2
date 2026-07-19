<!--
First-draft Eval Strategy, AI-assisted. Evals are the "unit tests" for LLM output:
since you can't assert output == expected on a model, you curate datasets + rubrics,
score them, and gate changes on the scores. This doc owns the HOW of measurement;
the PRD §6 owns the target NUMBERS. MVP-deep (the parse eval is buildable),
later-shallow (other stages sketched so the harness extends). Assumptions tagged
[ASSUMPTION], open items [OPEN].
-->

# Eval Strategy — AI Job Assistant

| Field | Value |
|---|---|
| Author | Arun |
| Date | 2026-06-29 |
| Status | Draft |
| Reviewers | Self / Claude (tutor) |
| Related | PRD §6 (targets), RFC §8 (how evals hook in), ADR-0005 (Langfuse), ADR-0010 (OpenAI) |

---

## 1. Why this doc exists

You cannot write `assert output == expected` against an LLM — the output is
open-ended and non-deterministic. So LLM features are quality-controlled with
**evals**: curated inputs + rubrics, scored, with a **threshold that gates changes**
in CI. Evals are the new unit tests (CLAUDE.md). This doc defines *how* we measure;
the **PRD §6 owns the target numbers**, and this doc makes them enforceable.

Scope, mirroring the RFC: **MVP-deep** (the resume-parse eval, specified to build now)
and **later-shallow** (search / gap / tailor / cover-letter evals sketched so the
harness is designed to extend, not redesigned later).

## 2. Principles

1. **Cheapest grader that works.** Prefer deterministic code checks; use an
   LLM-as-judge only for genuinely subjective quality; use humans for ground-truth
   labels and spot-checks. (See §3.)
2. **Hard gates vs. soft thresholds.** Some criteria are tunable thresholds
   (accuracy ≥ X%); others are **binary hard gates** (zero fabrication — one failure
   fails the run). Keep them separate. (See §5.)
3. **Traces feed datasets.** Real Langfuse traces (RFC §8) become future eval cases —
   which is *why* observability is set up before evals.
4. **Hold out, don't peek.** Keep a holdout slice you never tune the prompt against,
   so scores reflect real quality, not prompt-overfitting to the dev set.
5. **Evals gate changes.** Any change to a prompt, model, or output schema must pass
   the eval bar in CI before it merges (evals-as-tests).
6. **Versioned together.** An eval result is meaningless without knowing the
   `model` + `prompt_version` + dataset version it ran against — record all three.

## 3. The three grader types (cheapest-first)

| Grader | What it is | Use it for | Cost / caveats |
|---|---|---|---|
| **Code-based (deterministic)** | Compare output to a labeled answer in code (exact / normalized / set overlap) | Structured fields: name, email, skills list, work-history entries | Cheap, fast, repeatable — **preferred**. Needs labeled data. |
| **LLM-as-judge** | A model scores output against a rubric | Subjective quality: tailoring fit, cover-letter tone/consistency, fuzzy field equivalence ("Sr SWE" ≈ "Senior Software Engineer") | Costs tokens; the judge can be biased/noisy — pin judge model+prompt, validate against human labels, prefer it to *grade* not *guess*. |
| **Human** | A person labels or reviews | Building ground-truth label sets; spot-checking; the precision@10 relevance judgement | Most expensive/slowest — reserve for labels + audits. |

**For resume parsing, most grading is code-based** (compare extracted JSON to a
labeled JSON). LLM-as-judge appears only for fuzzy-field equivalence, and is the
*primary* tool for the later tailoring/cover-letter stages.

## 4. MVP eval — resume parsing (specified to build)

### 4.1 What we're measuring (from PRD §6)
- **Field extraction accuracy ≥ 95%** on a labeled sample (name, contact, each
  work-history entry, skills, education).
- **Zero hallucinated entries** — nothing in the output that isn't supported by the
  source resume. **Hard gate.**

### 4.2 Dataset
- **Inputs → expected output:** each case is `(resume file, expected ParsedResume
  JSON)`. The expected JSON is hand-labeled (the ground truth).
- **Sources & composition** [ASSUMPTION — confirm sizes]:
  - ~20–30 curated resumes to start, spanning formats that stress the parser:
    single- vs multi-column, with/without tables, a scanned/image PDF, a sparse
    resume, a dense senior resume.
  - Grows over time from **anonymized real traces** (Langfuse) once we have them.
- **PII:** resumes are sensitive (PRD §7). Use **synthetic or anonymized** resumes in
  the committed dataset; never commit real personal data to git. [OPEN — where the
  dataset lives if it can't all be in-repo: a local/gitignored dir vs. Langfuse
  datasets.]
- **Versioning:** the dataset has a version id; eval results record which version they
  ran against (Principle 6).
- **Holdout:** reserve a slice (e.g. ~20%) never used while iterating the prompt.

### 4.3 How each field is scored
| Field | Match rule |
|---|---|
| name, email, phone | normalized exact match (trim/case/format-insensitive) |
| education entries | normalized match per entry; set-level precision/recall |
| skills | **set overlap** (precision/recall) with light normalization; LLM-judge only for ambiguous equivalence |
| work history | per-entry match on (title, company, dates); precision/recall over the set; titles may use fuzzy/LLM-judge equivalence |

**Accuracy metric:** field-level **precision & recall** aggregated across the set;
report overall accuracy against the ≥95% bar. (Per-field breakdown is what tells you
*where* it fails.)

### 4.4 The no-fabrication (grounding) check — hard gate
Separate from accuracy. For **every** value in the output, verify it is **grounded**
in the source resume text (present or directly supported). Any ungrounded value =
**fabrication = the run fails**, regardless of accuracy score.
- MVP implementation: programmatic grounding check (does the value appear in / derive
  from the extracted source text?), with an LLM-judge backstop for paraphrased cases.
  [OPEN — exact grounding method; validate on the curated set.]
- This is simultaneously the **Responsible-AI guardrail** for parsing (PRD §7:
  "tailoring must never become fabrication" starts here, at parse).

### 4.5 Where it runs
- **Offline, in CI**, as a gate on any change to the parse prompt / schema / model
  (evals-as-tests, RFC §8.2).
- **Tooling** [OPEN → recommendation]: start simple — **`pytest` reading committed
  JSON fixtures** + deterministic comparisons; record runs to **Langfuse
  datasets/experiments** as the set grows and traces accumulate. Rationale: don't
  stand up heavy eval infra for 20 cases; graduate to Langfuse-managed datasets when
  trace volume justifies it.
- **Pass criteria to merge:** accuracy ≥ 95% on the (non-holdout) set **AND** zero
  fabrications. Periodically re-check the holdout to detect overfitting.

## 5. Hard gates vs. soft thresholds (summary)

| Criterion | Type | Bar |
|---|---|---|
| Parse field accuracy | soft threshold | ≥ 95% |
| Parse fabrication | **hard gate** | exactly 0 |
| Tailored-resume skill coverage (later) | soft threshold | ≥ 80% |
| Tailored-resume / cover-letter fabrication (later) | **hard gate** | exactly 0 |

A hard gate failing **fails the whole eval** even if every soft threshold passes.

## 6. Later-stage evals (sketch — designed to extend, not built now)

These reuse the same harness (dataset → grader → CI gate); numbers from PRD §6.

| Stage | Primary grader | Metric / bar | Notes |
|---|---|---|---|
| **Job relevance** | human (+ LLM-judge to scale) | **precision@10 ≥ 70%** | needs a human-rated relevance set; LLM-judge calibrated to human labels; **query-dependent — see note below** |
| **Gap analysis** | code vs. labeled gap set | precision/recall **≥ 80%** (matched + missing skills, unweighted mean) | label the true gaps for a resume×job pair; hard zero-fabrication gate (`tests/eval/eval_gap_analysis.py`) |
| **Tailored resume** | LLM-judge + code | **≥ 80%** coverage of *has*-skills; **zero fabrication** (hard); no contradiction with source | grounded against the source resume |
| **Cover letter** | LLM-judge | consistent with resume+job; **zero fabrication** (hard) | tone/consistency rubric |

**Job relevance is inherently query-dependent** — a real gap surfaced and resolved
2026-07-15. A niche query (e.g. "computer vision engineer") returned only 18 Adzuna
candidates with just ~6 genuinely strong matches; no reranker can fill 10 good slots
from a pool that thin, so precision@10 was structurally capped around 60% regardless
of reranker quality. A broader, more commonly-searched query (e.g. "machine learning
engineer", 50 candidates) hit 100% with the same reranker. Separately, the reranker's
`SYSTEM_PROMPT` (`app/rank.py`) was missing seniority/scope weighting — it would flag
a mismatch ("may require more leadership than the candidate has") in its own reasoning
but not discount the score for it. Fixed by explicitly instructing the model to score
down clear seniority/ownership overreach (e.g. "Staff", "Principal", "lead the
architecture end-to-end") even when the technical domain matches well — verified this
does shift scores appropriately (a "Senior Staff Engineer" posting dropped from 75 to
50). When re-testing this bar, prefer a reasonably broad/common query — a niche query
can legitimately fail on retrieval breadth alone, not reranker quality.

**Tailored-resume/cover-letter mechanism** (`tests/eval/eval_tailor.py`): coverage is a
code-based check — a `has`-skill counts as covered if it's in the model's
`emphasized_skills` sidecar (a closed-vocabulary list copied verbatim from the parsed
resume's skills) or appears as a normalized substring in the generated text. Fabrication
and source-contradiction are both caught by a single, narrowly-scoped coded LLM-judge
(`judge_fabrication`) that lists any claim in the generated text not grounded in the
source resume — explicitly instructed that paraphrasing/reordering/summarizing real
content is not fabrication. No RAG/vector store is used for grounding (ADR-0018);
generation is grounded directly on the full raw resume text in the prompt.

**Bias / fairness (hiring is high-risk — PRD §7):** as matching/tailoring land, add a
fairness check that outputs don't vary on protected-characteristic proxies. [OPEN —
define the check; not needed for the parse-only MVP but flagged early.]

## 7. Online / production evals (post-deploy, future)

Once deployed (roadmap later phases): sample production traces, run the same graders
online, watch for quality/cost/latency drift, and route low-confidence or
hard-gate-failing outputs to a **human review queue** (which also produces new labels).
Out of scope for the MVP; listed so the tracing/dataset design anticipates it.

## 8. Open questions

- [OPEN] Curated dataset size & exact composition (assumed ~20–30 to start).
- [OPEN] Dataset storage if not fully in-repo (gitignored local dir vs. Langfuse
  datasets) — driven by the PII constraint.
- [RESOLVED for tailoring] Grounding/no-fabrication check method: code-based skill
  coverage + a coded LLM-judge (`tests/eval/eval_tailor.py`). Still open for any stage
  not yet built.
- [OPEN] Eval tooling graduation point (pytest+fixtures → Langfuse datasets).
- [OPEN] Judge model + cost budget for LLM-as-judge in later stages.
- [OPEN] Fairness/bias check definition for the matching/tailoring stages.