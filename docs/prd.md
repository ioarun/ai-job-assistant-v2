<!--
First-draft PRD, AI-assisted. Content reflects reasonable assumptions based on the
project vision and decisions so far. Assumptions are tagged [ASSUMPTION] and open
items [OPEN] — review/replace these. A PRD states WHAT & WHY, not HOW (the "how"
lives in the Design Doc / RFC).
-->

# Product Requirements Document (PRD) — AI Job Assistant

| Field | Value |
|---|---|
| Author | Arun |
| Date | 2026-06-28 |
| Status | Draft |
| Reviewers | Self / Claude (tutor) |

---

## 1. Problem & context

Job seekers spend an enormous amount of manual effort to land a role: searching
fragmented job boards, judging which postings actually fit their experience,
figuring out what skills they're missing, rewriting their resume for each role,
and filling out repetitive applications. The work is slow, tedious, and
error-prone — and because tailoring by hand is so costly, most applicants submit
generic resumes that poorly match each role's requirements, which lowers their
callback rate.

There is no single assistant that takes a person from **resume → matched jobs →
honest gap analysis → role-tailored resume → application**, while keeping the
applicant in control of every meaningful decision.

## Prior art & differentiation (future — NOT a v1 goal)

Comparable tools already exist — **AIApply**, **Jobright**, **LoopCV**, **Simplify**,
**Resumly/Massive** — and the match → tailor → (auto-)apply loop is a mature
category; per-application tailoring is the recognized quality differentiator within
it. So this project is **not novel as a product**, and that is fine:

> **Primary goal: learning.** This project exists to learn RAG, agentic AI, MCP, and
> the modern (2026) software/AI engineering lifecycle — not to out-compete those
> tools. Rebuilding a known product is a deliberate learning choice. **Product
> novelty is explicitly out of scope for v1.**

**Potential differentiators — deferred, do NOT build for v1.** If we ever choose to
make this app genuinely distinct, the defensible angles (most competitors are cloud
SaaS that ingest your data and spray applications) would be:
- **Privacy / local-first** — self-hosted, PII stays on the user's machine, BYO API key.
- **Honesty as a hard constraint** — never fabricate skills/experience.
- **Transparency / observability** — inspectable traces, not a black box.
- **Open & MCP-extensible** — pluggable job sources/tools.
- **Human-gated, quality-over-quantity** — deliberately not reckless spray-and-pray auto-apply.

These are aspirational and revisited only post-learning; none are required for the
MVP or near-term phases.

## 2. Goals

If this works, an applicant can:

- Upload a resume once and have it parsed into structured data.
- Discover jobs genuinely matched to their actual background, without trawling
  multiple sites.
- See concrete, honest skill gaps between their resume and the roles they want.
- Get a role-tailored resume that improves fit **without fabricating anything**.
- Have the assistant generate a tailored cover letter (optional) that is consistent with the resume and role.
- Have applications submitted on their behalf — saving the repetitive
  busywork — while approving each step.
- Stay in control: review and approve at every key decision point.

## 3. Non-goals (v1)

- **Not** building large-scale job-scraping/crawling infrastructure — v1 uses an
  existing job source via the Adzuna API behind a pluggable `JobSource` interface
  (see ADR-0007).
- **Not** fully autonomous auto-apply — every submission passes a human gate.
- **Not** a multi-user SaaS with accounts, auth, or billing — v1 is single-user /
  local-first. [ASSUMPTION]
- **Not** interview prep, or salary negotiation.
- **Not** multi-language — English resumes only in v1. [ASSUMPTION]
- **Not** direct ATS-account integrations.
- v1 supports a limited set of resume input formats (PDF, possibly DOCX).
  [ASSUMPTION]

## 4. Users & key use cases

**Primary persona:** an active job seeker (e.g., a software engineer) applying to
many roles who wants to spend their time on quality applications, not on search
and copy-paste busywork. [ASSUMPTION]

User stories:

- As an applicant, I upload my resume so that the assistant understands my
  experience without me re-entering it.
- As an applicant, I see a shortlist of relevant jobs so that I don't have to
  search multiple boards myself.
- As an applicant, I review the skill gaps for a target role so that I know how
  well I fit and what to emphasize.
- As an applicant, I get a tailored version of my resume for a specific job so
  that it matches the role — and I can trust it contains nothing false.
- As an applicant, I get a tailored cover letter for a specific job so that it
  is consistent with my resume and the role.
- As an applicant, I approve each application before it's submitted so that I stay
  in control of what goes out under my name.

## 5. Requirements (prioritized)

### MVP — first shippable slice (thin vertical slice)
The smallest end-to-end, observable, valuable capability:

- Upload a resume (PDF). [ASSUMPTION on format]
- Parse it into structured data (contact info, work history, skills, education).
- Present the structured understanding back to the user for review/correction.
- The full path is **traced/observable** and the parse quality is **measured by an
  eval set** (see §6).

> Rationale: proving resume intake end-to-end — with tracing and evals — exercises
> the whole toolchain on real value before adding more stages.

### Later (post-MVP, roughly in order)
- Job search / matching against the parsed resume.
- Gap analysis between resume and a target job.
- Tailored-resume generation (with the no-fabrication guarantee).
- Tailored-cover-letter generation (with the no-fabrication guarantee).
- Agentic orchestration tying the stages together with human-in-the-loop gates.
- Auto-apply (gated, ToS-aware) — highest risk, last.
- Multi-user, accounts, deployment to a shared environment.
- A fully functional frontend UI (beyond the MVP's minimal proof-of-concept).

## 6. Success metrics — product AND eval criteria

**Product metrics**
- Reduction in time from "have a resume" to "submitted a tailored application."
- Number of tailored applications produced/submitted per session.
- User-reported usefulness (qualitative for v1). [ASSUMPTION]
- (Longer-term, hard to attribute) interview/callback rate.

**Eval criteria — what "good" means per stage (measurable)**
- **Resume parsing:** ≥95% of fields (name, contact, each work-history entry,
  skills, education) correctly extracted on a labeled sample; **zero hallucinated
  entries** (info not present in the source). [ASSUMPTION on threshold]
- **Job relevance:** ≥70% of the top-10 returned jobs rated "relevant" by a human
  reviewer (precision@10). [ASSUMPTION on threshold]
- **Gap analysis:** identified gaps match a human-labeled gap set with **≥80%
  precision/recall** (matched + missing skills, unweighted mean); zero fabrication
  (hard gate).
- **Tailored resume:** covers ≥80% of the target job's required skills that the
  applicant *actually has*; **exactly zero fabricated skills/experience** (hard
  constraint — a single fabrication fails the eval); no factual contradictions
  with the source resume.
- **Tailored cover letter:** consistent with the tailored resume and target job;
  no fabricated skills/experience; no factual contradictions with the source
  resume.

## 7. Risks, assumptions & open questions

**Risks & mitigations**

Domain (responsible-AI) risks now live in their own first-class register —
**`docs/responsible-ai.md`** — which is the source of truth: each risk has a
likelihood/impact, a mitigation, and the artifact/phase that *enforces* it. In brief,
the headline risks are: regulated-domain misuse, fabrication/hallucination, auto-apply
ToS/account risk, PII/privacy, and bias/fairness. (Operational cost/latency is tracked
separately in RFC §9.)

**Assumptions**
- Single-user / local-first for v1; no auth/billing.
- English-language, PDF resumes for v1.
- The user has the right to apply to the roles surfaced.

**Resolved**
- ✅ **Job listing source** — Adzuna API (free dev tier, AU coverage) behind a
  pluggable `JobSource` interface; Jooble / JSearch / MCP-based sources are future
  adapters. See ADR-0007.

**Open questions**
- [OPEN] **Auto-apply mechanism** — email, portal form-fill, or a browser agent?
  Legality and feasibility need investigation before committing.
- [RESOLVED] **Tailored-resume export** — plain text/Markdown, returned as a string
  field via the API and rendered as text in the frontend (Phase F). PDF templating
  deferred to a later pass.
- [OPEN] **Deployment target** for the eventual hosted version.

## 8. Out of scope / future

- Suggest resources/courses for upskilling, Interview preparation, salary negotiation.
- Multi-user SaaS, authentication, billing.
- Mobile app.
- Recruiter-/employer-side features.
- Non-English resumes.