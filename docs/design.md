<!--
First-draft Design Doc / RFC, AI-assisted. The RFC owns the HOW (the PRD owns the
what & why). This draft is MVP-deep and post-MVP-shallow on purpose: stage 1
(upload → parse → light review gate) is specified in buildable detail; later stages
are only sketched and will get their own RFCs. Assumptions are tagged [ASSUMPTION]
and open items [OPEN] — review/replace these. Decisions already recorded link to
their ADR rather than re-arguing them; genuinely new how-level questions are flagged
as candidate ADRs.
-->

# Design Doc / RFC — AI Job Assistant (MVP)

| Field | Value |
|---|---|
| Author | Arun |
| Date | 2026-06-29 |
| Status | Draft |
| Reviewers | Self / Claude (tutor) |
| Supersedes | — |
| Related | PRD (`prd.md`), diagrams (`diagrams/`), ADRs 0001–0010 (`adr/`) |

---

## 1. Summary (TL;DR)

Build the **thin vertical slice** the PRD §5 defines: an applicant uploads a PDF
resume, the backend parses it into structured data with one OpenAI call, and the
applicant reviews/approves the result behind a **light HITL gate**. The whole path
is **traced in Langfuse** and the parse quality is **measured by an offline eval
set**.

The MVP runs the pipeline as a **LangGraph** graph (one real LLM node + a human
interrupt) inside a **FastAPI** backend, persists to **Postgres**, and is driven by
a **separate minimal front end**. We deliberately stand up the *whole toolchain*
(orchestration, tracing, evals, DB, API, UI) around a single LLM call, so every
later stage plugs into an already-working, observable skeleton.

**This RFC covers the MVP only.** Search, gap analysis, tailoring, cover letters,
and auto-apply are out of scope here and get their own RFCs.

## 2. Context & scope

- **Problem & product goals:** see PRD §1–§2.
- **In scope (this RFC):** resume upload, parse, light review/approve gate; tracing;
  eval harness for parse quality; the minimal data model, API, and UI to support it.
- **Out of scope (future RFCs):** job search/matching, gap analysis, tailored resume
  + cover letter, agentic multi-stage orchestration, auto-apply, multi-user/auth.
  These are sketched in §11 only to confirm the MVP doesn't paint us into a corner.

### Design goals (how-level, distinct from product goals)
1. **Observable from the first call** — no LLM call ships without a trace.
2. **Reversible** — prompts and the model are versioned and swappable; the schema
   migrates forward; the `JobSource`-style seams exist before we need them.
3. **The skeleton is the point** — wire orchestration + tracing + evals + DB + API +
   UI end-to-end on a single stage, so stage 2+ is "add a node," not "add a system."
4. **No fabrication, even at MVP** — parsing must never invent fields not present in
   the source (this is an eval gate, not just a hope — see §8, PRD §6).

### Non-goals (of the design)
- Not optimizing cost/latency yet beyond a stated budget (§9).
- Not building the full field-by-field parse editor (light gate only; ADR-flow
  resolution — full editor deferred to Post-MVP).
- Not horizontal scaling / multi-tenant concerns.

## 3. Architecture recap

Containers and boundaries are already drawn — this RFC does not redraw them:
- **Context (C4 L1):** `diagrams/context.md`
- **Flow (behavioral):** `diagrams/flow.md` — the MVP is the `parse → reviewParse`
  subgraph.
- **Architecture (C4 L2):** `diagrams/architecture.md` — MVP containers are
  Front-end, Backend API, Postgres, Langfuse, + external OpenAI. (Vector store and
  Adzuna are dotted / Post-MVP.)

What this RFC adds is **C4 L3 — the components inside the Backend API** and how they
talk (below).

## 4. MVP pipeline — LangGraph design

The MVP is small enough that a plain function would work; we use LangGraph anyway
(ADR-0003) to **learn it and establish the orchestration seam** every later stage
needs. The graph stays tiny.

### Nodes (C4 L3 components inside the backend)
```
ingest ──▶ parse ──▶ [interrupt: human review] ──▶ persist_approved
   ▲                          │
   └──────── corrections ◀────┘   (loop back to parse on "Fix")
```

| Node | Responsibility | LLM? | Notes |
|---|---|---|---|
| `ingest` | Validate upload, extract/prepare the document for the model | No | PDF handling — see §6 |
| `parse` | One OpenAI call → structured resume (Pydantic schema) | **Yes** | The only LLM call in the MVP |
| *(interrupt)* | Pause the graph, surface the parse to the UI for the light gate | — | LangGraph `interrupt()` — see §4.1 |
| `persist_approved` | Write the approved structured resume to Postgres | No | Marks the run approved |

### 4.1 HITL gate via LangGraph interrupt
The light gate ("looks right? Yes / Fix") is implemented with LangGraph's
**`interrupt()`** primitive: the graph runs `ingest → parse`, then *interrupts*,
returning the parsed result to the API/UI and suspending. On **approve**, the run
resumes into `persist_approved`. On **Fix** (corrections), it resumes back into
`parse` with the user's corrections as additional context. [ASSUMPTION: corrections
are free-text hints in the MVP, not field-by-field edits — consistent with "light
gate."]

This requires the graph state to be **persisted across the interrupt** (the HTTP
request that triggers parse returns before the human responds). → see §4.2.

### 4.2 Graph state & checkpointing  → candidate ADR
LangGraph needs a **checkpointer** to survive the interrupt. Options:
- **Postgres checkpointer** (`langgraph-checkpoint-postgres`) — reuses our DB
  (ADR-0009), one fewer moving part, production-like. **Recommended.**
- In-memory — loses state on restart; only acceptable for a throwaway spike.

**[OPEN → candidate ADR-0011]** Confirm: LangGraph checkpoints live in the app
Postgres. (This was an open item on the architecture diagram.)

## 5. Data model (Postgres)

Minimal MVP schema. `jsonb` holds the variable-shape parsed resume (ADR-0009).

| Table | Key columns | Purpose |
|---|---|---|
| `resume` | `id`, `original_filename`, `mime_type`, `storage_ref`, `uploaded_at` | The uploaded source file (metadata + pointer to bytes) |
| `parse_run` | `id`, `resume_id` (fk), `status` (`pending`/`awaiting_review`/`approved`/`failed`), `model`, `prompt_version`, `trace_id`, `created_at` | One attempt to parse a resume; links to its Langfuse trace |
| `parsed_resume` | `id`, `resume_id` (fk), `parse_run_id` (fk), `data` (jsonb), `approved` (bool), `approved_at` | The structured output + approval state |

Notes / opens:
- **Where do the raw file bytes live?** Options: Postgres `bytea`, local filesystem,
  or object storage (MinIO already runs as part of the Langfuse stack — ADR-0005).
  **[OPEN]** Recommend local filesystem or `bytea` for the MVP (simplest);
  `storage_ref` abstracts it so we can move to MinIO/S3 later without schema change.
- **User identity:** v1 is single-user (PRD non-goal), so no `users` table yet; a
  nullable `user_id` stub can be added when multi-user lands. [ASSUMPTION]
- **Migrations:** use a migration tool (e.g. Alembic) from day one so the schema is
  reversible. [ASSUMPTION — confirm tool when we add the dependency]

## 6. Resume parsing — the one LLM call  → candidate ADR

Two how-questions: (a) how the PDF reaches the model, (b) how we get reliable
structured output.

### 6.1 PDF → model: native document vs. extract-then-prompt  → candidate ADR-0012
- **Native PDF to the model** (OpenAI supports PDF **file inputs**) — the model reads
  layout + text directly; less preprocessing; generally higher fidelity on
  real-world (multi-column, table-heavy) resumes. **Recommended.**
- **Extract text first**, then prompt with the extracted text — gives an inspectable
  intermediate (useful for debugging/evals) but adds a step that can mis-read layout
  before the model sees it. Naive extractors (`pypdf`/`pdfplumber`) struggle on
  multi-column resumes; a layout-aware loader like **`UnstructuredPDFLoader`**
  (`strategy="hi_res"`, which adds a layout model + OCR and heavier system deps —
  poppler/tesseract) is the stronger representative of this path.

**[OPEN → candidate ADR-0012]** Recommend native PDF input to the model; keep a
text-extraction fallback (e.g. `UnstructuredPDFLoader` hi_res) behind the same
`ingest` node interface — built only if the spike shows native parsing struggling.

### 6.2 Structured output
Use OpenAI's **Structured Outputs** (the `openai` SDK's Pydantic `parse` helper, or
`response_format` with a JSON schema; model per ADR-0010) so the parse returns a
validated object, not free text we have to re-parse. The schema is the contract:

```python
# illustrative ONLY — example to learn from, not a file to apply
class WorkEntry(BaseModel):
    title: str
    company: str
    start: str | None
    end: str | None
    highlights: list[str] = []

class ParsedResume(BaseModel):
    name: str | None
    email: str | None
    phone: str | None
    skills: list[str] = []
    work_history: list[WorkEntry] = []
    education: list[str] = []
```

The model/params are governed by ADR-0010; pin the exact model ID and the Structured
Outputs / file-input API specifics from OpenAI's official docs when you write this,
not from memory.

### 6.3 Prompt versioning
The parse prompt is **versioned** (e.g. a string constant with a `prompt_version`
recorded on `parse_run`, or managed in Langfuse prompts). Rolling back a prompt must
be as easy as rolling back code (CLAUDE.md principle). **[OPEN]** code constant vs.
Langfuse-managed prompt — recommend a code constant for the MVP (simplest, in git),
revisit Langfuse-managed prompts when we have several.

### 6.4 No-fabrication guardrail
The prompt instructs the model to extract **only** what is present and leave unknown
fields null — never infer or invent. This is verified by the eval (§8), not trusted
blindly.

## 7. API surface (FastAPI)

Minimal REST for the MVP. JSON over HTTPS; the separate front end (ADR-0008) is the
only client.

| Method & path | Purpose | Returns |
|---|---|---|
| `POST /resumes` | Upload a PDF (multipart); creates a `resume`, kicks off a `parse_run` (graph runs to the interrupt) | `{ resume_id, parse_run_id, status }` |
| `GET /resumes/{id}/parse` | Poll the parse result / status | `{ status, parsed_resume? }` |
| `POST /resumes/{id}/parse/approve` | Light-gate **approve** → resumes graph into `persist_approved` | `{ status: "approved", parsed_resume }` |
| `POST /resumes/{id}/parse/corrections` | Light-gate **Fix** → resumes graph back into `parse` with hints | `{ status: "awaiting_review", parsed_resume }` |

Notes:
- **Sync vs. async:** parsing is one LLM call (seconds). MVP can run it inline and
  have the client poll `GET .../parse`. A background worker/queue is **not** needed
  yet. [ASSUMPTION — revisit when stages chain]
- **Approve/corrections map to the LangGraph resume** (§4.1): the API translates an
  HTTP call into resuming the suspended graph with the human's decision.

## 8. Observability & evals (the two practices we don't skip)

### 8.1 Tracing (Langfuse, ADR-0005)
- Every LLM call and every graph node is **traced** to self-hosted Langfuse
  (LangGraph has Langfuse integration; the OpenAI call is wrapped via Langfuse's
  OpenAI integration).
- `parse_run.trace_id` links a DB row to its trace, so any parse is inspectable
  end-to-end.
- Self-hosted so **resume PII stays local** (PRD §7 risk).

### 8.2 Evals (parse quality)  → see eval-strategy.md
The eval harness is specified in `eval-strategy.md` (next artifact); this RFC states
how it hooks in:
- **Dataset:** a small set of labeled resumes (input PDF/text → expected structured
  fields). Traces feed future dataset growth (that's *why* tracing is set up first).
- **Metrics (PRD §6):** ≥95% field extraction accuracy; **zero hallucinated entries**
  (hard gate).
- **Where it runs:** offline, as a CI gate on changes to the parse prompt/schema/model
  (evals-as-tests). [ASSUMPTION — CI wiring lands with the build phase]

## 9. Cross-cutting concerns

- **Security / PII:** resumes are sensitive (PRD §7). Self-host Langfuse; keep files
  local; the Anthropic API key and DB creds come from env/secrets, never committed;
  define a retention policy. [OPEN — retention policy specifics]
- **Cost/latency budget:** MVP is one OpenAI call per resume; target < a few seconds
  and a few cents per parse. [ASSUMPTION — set real numbers from the feasibility
  spike.] Prompt caching considered later when prompts grow.
- **Error handling:** `parse_run.status = failed` on model/validation error; the UI
  offers retry; failures are traced. Malformed/oversized/non-PDF uploads rejected at
  `ingest` with a clear error.
- **Config:** 12-factor — all secrets/endpoints via environment; `.env` for local
  dev (gitignored), real secrets injected in deployed envs.

## 10. Alternatives considered

Most stack alternatives are already argued in the ADRs — not repeated here:
- Orchestration (LangGraph vs. plain code / other frameworks) → ADR-0003.
- LLM (OpenAI vs. Claude/others) → ADR-0010 (supersedes ADR-0004).
- Observability (Langfuse vs. LangSmith) → ADR-0005.
- DB (Postgres vs. SQLite/NoSQL) → ADR-0009.
- Front end (separate vs. folded) → ADR-0008.

New, RFC-level alternatives surfaced above (each a candidate ADR):
- LangGraph checkpoint location (§4.2) → candidate ADR-0011.
- PDF ingestion method (§6.1) → candidate ADR-0012.
- Prompt storage: code constant vs. Langfuse-managed (§6.3).
- Raw-file storage: filesystem/`bytea` vs. MinIO/S3 (§5).

## 11. Forward-compatibility (post-MVP, sketch only)

Confirming the MVP doesn't box us in — **not designing these now**:
- **Search / gap / tailor / cover letter** become **new LangGraph nodes** on the same
  graph; the `interrupt()` HITL pattern repeats at the pick-job and approve-docs
  gates (flow.md).
- **Job search** enters behind the `JobSource` interface (ADR-0007, Adzuna first).
- **RAG** adds a vector store (pgvector candidate, ADR-0009 note) + retrieval node;
  no change to the MVP containers.
- **Auto-apply** is last and human-gated (PRD non-goal / flow.md Future tier).

## 12. Risks (design-specific)

- **LangGraph interrupt/checkpoint is new to us** — small risk it's fiddly across an
  HTTP boundary. *Mitigation:* the feasibility spike exercises it on the real parse.
- **Native-PDF parsing quality unknown on messy resumes** — *Mitigation:* spike on
  real samples; text-extraction fallback behind the same node.
- **Over-engineering the skeleton** — using LangGraph/checkpointer for one call risks
  ceremony. *Accepted* deliberately: the learning + seam value justifies it; the
  graph stays tiny.

## 13. Milestones  → see roadmap.md

Sequenced delivery (goals/exit-criteria per phase live in `roadmap.md`):
1. **Walking skeleton** — FastAPI + Postgres + Langfuse up under Docker; one traced
   hello-LLM (OpenAI) call; CI runs.
2. **Parse slice** — `ingest → parse` with structured output, traced.
3. **HITL gate** — interrupt + approve/corrections + persist.
4. **Eval gate** — labeled set + scoring wired into CI.
5. **Minimal UI** — separate front end: upload → review → approve.

## 14. Open questions (consolidated)

- [OPEN → ADR-0011] LangGraph checkpoint location (recommend app Postgres).
- [OPEN → ADR-0012] PDF ingestion method (recommend native PDF to the model + fallback).
- [OPEN] Prompt storage: code constant (MVP) vs. Langfuse-managed (later).
- [OPEN] Raw-file storage: filesystem/`bytea` (MVP) vs. MinIO/S3 (later).
- [OPEN] Migration tool confirmation (Alembic assumed).
- [OPEN] Data retention policy specifics.
- [OPEN] Real cost/latency numbers — fill from the feasibility spike.