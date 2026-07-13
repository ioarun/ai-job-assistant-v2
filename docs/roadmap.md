<!--
First-draft Roadmap, AI-assisted. Turns the PRD §5 "Later" list and the RFC §13 MVP
milestones into a sequenced phase plan (A–H). Detail depth is deliberately LIGHT:
each phase has goal + scope + exit criteria; only the next phase (A) is fleshed into
concrete steps. Future phases are detailed just-in-time as we reach them
(anti-waterfall — a 2026-SDLC principle). Assumptions tagged [ASSUMPTION], open
items [OPEN].
-->

# Roadmap — AI Job Assistant

| Field | Value |
|---|---|
| Author | Arun |
| Date | 2026-06-29 |
| Status | Draft |
| Related | PRD §5 (scope), RFC §13 (milestones), flow.md (stages/gates), eval-strategy.md |

**Guiding principles** (from CLAUDE.md): **thin vertical slices** — ship one
capability end-to-end before building breadth; **everything reversible + observable**
— traced from day one, eval-gated where there's LLM output, with a **human gate
before any outward/irreversible action**. **The MVP is Phases A+B+C** (PRD stage 1),
not everything half-built.

## Phase summary

| Phase | Goal | Maps to | Tier |
|---|---|---|---|
| **A — Walking skeleton** | FastAPI + Postgres + Langfuse under Docker; one traced hello-OpenAI call; CI green | RFC milestone 1 | MVP |
| **B — Resume parse slice** | upload → OpenAI structured parse → persist, traced; + parse eval harness | PRD stage 1; RFC milestones 2,4 | MVP |
| **C — HITL review gate + minimal UI** | light review gate (LangGraph interrupt); separate front end → **MVP complete** | PRD stage 1; RFC milestones 3,5 | MVP |
| **D — Job search** | Adzuna behind `JobSource` + pick-job gate; first embeddings/vector store for semantic match | PRD stage 2 | Post-MVP |
| **E — Gap analysis** | per selected job: match score + gaps; upskilling resource suggestions | PRD stage 3 | Post-MVP |
| **F — Tailored resume + cover letter** | grounded generation (no fabrication); no-fabrication eval gate; approve gate | PRD stages 4,5 | Post-MVP |
| **G — Advanced techniques** | mature agentic/multi-agent orchestration; better RAG retrieval; MCP servers/tools | "intended techniques" | Post-MVP |
| **H — Auto-apply + productionization** | human-gated submission (ToS-aware); deploy dev→staging→prod; online evals; monitoring/SLOs | PRD stage 6 + deploy | Future |

> **MVP = A + B + C.** This restates the PRD §5 boundary so the roadmap and PRD agree.
> Nothing in D–H ships in the MVP. If the MVP boundary should move, change the PRD
> first, then this roadmap.

---

## Phase A — Walking skeleton  *(detailed — the next phase)*

**Goal:** prove the whole toolchain end-to-end on a trivial slice: the app runs under
Docker, makes **one OpenAI call**, and that call shows up as a **trace in Langfuse**,
with **CI green**. No resume logic yet — this is the rails everything else rides on.

**Concrete steps:**
- `uv init` the project (Python 3.12) + first dependency manifest; project layout
  (e.g. `app/`, `tests/`, `docker-compose.yml`, `.env.example`). *(scaffolders → Arun
  runs them; tutor rule.)*
- `docker-compose` bringing up **Postgres** (ADR-0009) and **self-hosted Langfuse**
  (ADR-0005), per ADR-0006.
- Minimal **FastAPI** app (ADR-0002) with a `/health` endpoint and **one traced
  hello-OpenAI call** (ADR-0010) wired through Langfuse's OpenAI integration.
- **CI** (GitHub Actions) [ASSUMPTION — provider] running lint + a smoke test;
  conventional commits, trunk-based dev.

**Scope — out:** no resume upload/parse, no LangGraph graph, no UI, no eval set.

**Exit criteria:**
- `docker compose up` yields a running API (`/health` OK).
- The hello-OpenAI call appears as a **trace in Langfuse**.
- **CI is green** on a PR.

**Eval / Responsible-AI note:** no LLM *output* to eval yet; this phase exists to make
tracing real so later phases' evals have data (eval-strategy §8). No PII handled yet.

---

## Phase B — Resume parse slice

**Goal:** the first real slice — upload a PDF, parse it into `ParsedResume` with one
OpenAI Structured-Outputs call, persist it; all traced. Stand up the **parse eval
harness** alongside.

**Scope — in:** upload endpoint; `ingest`→`parse` (RFC §4); native-PDF input
(candidate ADR-0012); Postgres persistence (RFC §5); the offline parse eval
(eval-strategy §4). **Out:** the HITL gate and UI (Phase C).

**Exit criteria:** a PDF in → persisted `ParsedResume` out, visible as a trace;
the parse eval runs and reports field accuracy + a fabrication count.

**Eval / Responsible-AI note:** parse accuracy ≥95% target; **zero-fabrication hard
gate** is the first Responsible-AI guardrail (eval-strategy §4.4). PII begins here —
keep files local, traces self-hosted.

---

## Phase C — HITL review gate + minimal UI  → MVP COMPLETE

**Goal:** close the MVP loop — the applicant reviews the parse behind a **light gate**
("looks right? Yes / Fix") and approves; a minimal **separate front end** drives
upload → review → approve.

**Scope — in:** LangGraph `interrupt()` gate + checkpoint (candidate ADR-0011);
approve/corrections endpoints (RFC §7); minimal front end (ADR-0008). **Out:** the
full field-by-field editor (deferred Post-MVP per flow.md).

**Exit criteria:** an applicant can upload → see the parsed result → approve or send
corrections → get a stored, approved resume, through the UI. **This is the shippable
MVP (PRD stage 1).**

**Eval / Responsible-AI note:** first human-in-the-loop gate live (flow.md gate 1).

---

## Phase D — Job search

**Goal:** search jobs relevant to the parsed resume and let the applicant pick.

**Scope — in:** Adzuna behind the `JobSource` interface (ADR-0007); search +
pick-job HITL gate (flow.md gate 2); **first embeddings + vector store** for semantic
resume↔job matching (architecture.md marks this Post-MVP; pgvector candidate →
ADR around here). **Out:** gap analysis, tailoring.

**Exit criteria:** a query returns ranked, relevant listings; the applicant picks one;
relevance measured against precision@10 ≥70% (eval-strategy §6).

**Eval / Responsible-AI note:** respect Adzuna ToS; precision@10 eval introduced.

---

## Phase E — Gap analysis

**Goal:** for the selected job, compute a match score + honest skill gaps.

**Scope — in:** per-job gap analysis (flow.md stage 3) — a single Structured-Outputs
call returning `GapReport` (match score, matched skills, missing skills). **Out:**
tailoring (Phase F); upskilling resource suggestions (ADR-0017 — removed from project
scope entirely, not merely deferred to a later phase).

**Exit criteria:** gaps for a resume×job pair meet the precision/recall bar
([OPEN] — define, PRD §6).

**Eval / Responsible-AI note:** no automated decision *about the candidate* — gaps are
advisory (PRD §7).

---

## Phase F — Tailored resume + cover letter

**Goal:** generate a role-tailored resume and cover letter that improve fit **without
fabricating anything**.

**Scope — in:** grounded generation — **RAG over the applicant's own corpus** (past
resumes/projects) so output draws only on true facts; review/approve HITL gate
(flow.md gate 3); export format [OPEN — PRD §7]. **Out:** auto-apply.

**Exit criteria:** tailored resume covers ≥80% of *has*-skills with **zero
fabrication** (hard gate) and no contradiction with the source; cover letter
consistent (eval-strategy §6).

**Eval / Responsible-AI note:** the core "tailoring ≠ fabrication" constraint; RAG is
the *mechanism* enforcing it.

---

## Phase G — Advanced techniques

**Goal:** mature the AI architecture — the explicit learning goals of the project.

**Scope — in:** stronger agentic / multi-agent orchestration across stages; better
RAG (chunking, retrieval quality, reranking); **MCP** servers/tools to expose
sources/tools cleanly. **Out:** new product stages.

**Exit criteria:** [OPEN — define per technique as we reach it]; e.g. multi-agent
pipeline runs the full flow with gates; at least one MCP tool integrated.

**Eval / Responsible-AI note:** add a bias/fairness check as matching/tailoring mature
(eval-strategy §6; hiring is high-risk).

---

## Phase H — Auto-apply + productionization

**Goal:** the riskiest, last stage — submit applications (human-gated) and run the
system like a production service.

**Scope — in:** human-gated submission (flow.md gate 4; mechanism is [OPEN], PRD §7);
deploy dev→staging→prod with canary/progressive rollout; online evals; cost/latency
monitoring + SLOs; model/prompt rollback. **Out:** multi-user/accounts/billing unless
explicitly pulled in.

**Exit criteria:** a human-approved application can be submitted to a target; the
service is deployed with monitoring and a rollback path.

**Eval / Responsible-AI note:** highest-risk phase — respect job-board ToS, mandatory
human confirm before any submission, online evals + human review queue.

---

## Open items

- [OPEN] CI provider (assumed GitHub Actions).
- [OPEN] When exactly the vector store is introduced (Phase D) and which (pgvector vs.
  dedicated) → candidate ADR.
- [OPEN] Gap-analysis precision/recall bar (inherited from PRD §6 / eval-strategy).
- [OPEN] Tailored-resume export format (PRD §7).
- [OPEN] Auto-apply mechanism + deployment target (PRD §7).
- [OPEN] Per-technique exit criteria for Phase G.

_Detail for phases B–H is intentionally light and will be expanded just-in-time as
each phase begins._
