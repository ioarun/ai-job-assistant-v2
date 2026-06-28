<!--
Responsible-AI risk register. Promoted from PRD §7 into a first-class artifact
because hiring is a high-risk domain and the risks deserve to be citable + enforced,
not buried in the PRD. The PRD now points here as the source of truth for domain
risks. Likelihood/Impact are qualitative (Low/Med/High). "Where enforced" links each
mitigation to the artifact/phase that actually implements it — a mitigation with no
enforcement point is just a wish.
-->

# Responsible-AI Risk Register — AI Job Assistant

| Field | Value |
|---|---|
| Author | Arun |
| Date | 2026-06-29 |
| Status | Draft (living — reviewed each phase) |
| Related | PRD §7, eval-strategy.md, flow.md (HITL gates), RFC §9, ADR-0005/0007/0010, roadmap.md |

## Why this exists

Hiring/employment is a **high-stakes, regulated domain**. This register names the
domain risks up front, each with a mitigation **and the place that enforces it**, so
"responsible AI" is a set of wired-in controls rather than good intentions. It is a
**living document** — revisited as each phase lands, especially before Search (D),
Tailoring (F), and Auto-apply (H).

## Regulatory posture — the key nuance: applicant-side, not employer-side

The headline employment-AI laws regulate the **employer's** side of hiring:
- **EU AI Act** — AI used by employers to **screen/evaluate candidates** is
  **high-risk** (Annex III).
- **NYC Local Law 144** — regulates **Automated Employment Decision Tools (AEDTs)**
  used by **employers / employment agencies**, requiring bias audits.

**This tool sits on the _applicant's_ side**: it helps a person apply for jobs; it
makes **no automated decisions about other candidates**, and in v1 is single-user /
local-first. So the strict high-risk obligations (e.g. LL144 bias audits) **likely do
not apply to v1 as scoped**. [ASSUMPTION — not legal advice; confirm if productized.]

**But this is a deliberate boundary, not a free pass:** if the product ever moved
employer-side (screening candidates *for* a company), it would land squarely in
high-risk territory. We treat the responsible-AI controls below as in-scope anyway,
because they're good practice and keep that door open safely.

## Principles (the non-negotiables)

1. **Human gate before any outward/irreversible action** (e.g. submitting an
   application) — flow.md gates.
2. **No automated decisions _about candidates_** — gaps/matches are advisory to the
   applicant, never a screen.
3. **No fabrication** — tailoring/generation must never invent skills or experience.
4. **Privacy first** — resume PII minimized and kept local where possible.
5. **Transparency / observability** — every LLM step is traced and inspectable, not a
   black box.

## Risk register

| # | Risk | Likelihood | Impact | Mitigation | Where enforced |
|---|---|---|---|---|---|
| R1 | **Regulated-domain misuse** — drifting into automated decisions about candidates / employer-side use | Low (v1) | High | Applicant-side only; advisory outputs; no candidate screening; document posture; re-assess before any employer-side move | This register; flow.md (HITL); roadmap scope |
| R2 | **Fabrication / hallucination** — invented skills or experience in parse or tailoring | Med | High | **Zero-fabrication hard eval gate**; ground generation in source (parse) and the applicant's own corpus (tailoring, RAG); mandatory human review of tailored output | eval-strategy §4.4 & §6; RFC §6.4; flow.md gates 1 & 3; Phase F |
| R3 | **Auto-apply ToS / account risk** — automated submission violating job-board Terms of Service / risking bans | Med | High | Human confirm before every submission; prefer assisted over fully automated; respect each source's ToS; defer to the last phase | flow.md gate 4; roadmap Phase H; ADR-0007 |
| R4 | **PII / data privacy** — resumes are sensitive personal data; prompts go to a third-party LLM | High (exposure) | High | Self-hosted Langfuse (traces stay local); keep files local; minimize data sent to OpenAI; gitignore real data; define retention policy | ADR-0005; ADR-0010 (consequences); RFC §9; `.gitignore` (`data/`) |
| R5 | **Bias / fairness** — tailoring or matching varying on protected-characteristic proxies | Med | High | Advisory-only outputs; add a fairness eval check as matching/tailoring mature; human oversight | eval-strategy §6 (planned); roadmap Phase G |
| R6 | **Over-trust / automation bias** — user rubber-stamps outputs without real review | Med | Med | Light gates surface what changed; keep review meaningful; never auto-advance past a gate | flow.md gates; Phase C (HITL design) |

> **Note on cost/latency:** an operational risk, not a responsible-AI one — tracked in
> RFC §9 (cost/latency budget), not here.

## Review cadence

- **Each phase:** re-check this register against what's actually shipping.
- **Before Phase D (search):** confirm Adzuna ToS compliance.
- **Before Phase F (tailoring):** confirm the no-fabrication gate is wired and the RAG
  corpus grounding works.
- **Before Phase H (auto-apply):** the highest-risk review — submission mechanism,
  ToS, human-confirm gate, online monitoring.

## Open items

- [OPEN] Data retention policy specifics (how long resumes/traces are kept).
- [OPEN] Fairness/bias check definition (metric + dataset) for matching/tailoring.
- [OPEN] If ever productized/multi-user or employer-side: full EU AI Act / LL144
  compliance review (this register is not legal advice).
