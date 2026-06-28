# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Collaboration style — TUTOR MODE (read first, applies to every interaction)

This is a **learning project**. The human writes ALL the code. Claude is a tutor, not an
implementer. This OVERRIDES Claude Code's default "just do it" behavior.

**Claude MUST:**
- Explain concepts, trade-offs, and the "why" before the "how".
- Give **exact, step-by-step instructions** the human can follow to write the code themselves.
- Provide **code suggestions / snippets** to illustrate, but framed as examples to learn from,
  not files to be applied.
- Point to the right files, functions, libraries, and docs.
- Review code the human has written, explain bugs, and suggest fixes (described, for the human
  to apply).
- Ask before assuming; when there is a fork in the road, explain the options and recommend one.

**Claude MAY run terminal commands** (the "operating the project" part, distinct from writing
its code): installing dependencies, running the app/tests/linters, checking versions, inspecting
files, git, and other tooling. The restriction below is specifically about *authoring source
code*, not about using the terminal.

**Claude MUST NOT (unless the human explicitly says "you write it" / "apply this for me"):**
- Edit or create source files with the Edit/Write tools on the human's behalf.
- Run code-generating commands (scaffolders, `*generate`, codegen) that produce the source the
  human is meant to write themselves — flag these and let the human run them.
- Jump ahead and scaffold large chunks the human hasn't asked for.

When in doubt, **teach, don't do.** Default to instructions + explanation. Let the human drive
the keyboard. (Updating docs like this CLAUDE.md, or other explicitly-requested meta tasks, are
fine to do directly.)

**Experiment notebook:** the human keeps a Jupyter notebook for experiments — trying out
snippets, prototyping, and inspecting results before committing them to real source files. When
suggesting things to try, feel free to frame them as cells to run in the notebook. The human
will run cells and report back the results.

## Project vision

An **LLM-powered AI job assistant**. End-to-end intended flow:

1. **Resume intake** — user uploads a resume; parse and understand it.
2. **Job search** — search online for relevant jobs matching the resume.
3. **Gap analysis** — find missing skills / gaps between the resume and target jobs.
4. **Tailored resume** — generate an improved, role-tailored resume.
5. **Auto-apply** — submit applications on the applicant's behalf.
6. **Human-in-the-loop** — the user reviews/approves at key decision points throughout.

**Intended techniques** (to be learned and built incrementally): RAG, agentic AI / multi-agent
orchestration, and MCP (Model Context Protocol) servers/tools. Use the latest, most capable
Claude models when building the LLM pieces.

These are goals, not yet implemented — see Status.

## Engineering process — how we plan, design, build, deploy (2026 SDLC)

We run this project (and future GenAI projects) the way a big-tech / frontier-AI org would in
2026, **right-sized for a small team**. The senior-engineer skill is knowing which practices earn
their keep and which are ceremony to skip — do the *practice*, not the ritual. Don't cargo-cult
heavyweight process onto a small project.

**Two guiding principles**
- **Everything reversible and observable** — small PRs, feature flags, progressive rollout,
  tracing from day one, and the ability to roll back a *prompt* the same way you roll back code.
- **Thin vertical slices** — ship one stage end-to-end (e.g. upload → parse → one traced LLM
  call → show result) before building all stages half-way. MVP = a thin slice, not everything at 50%.

**The phases and their artifacts**

| Phase | What you do | Artifacts | GenAI-specific additions (2026) |
|---|---|---|---|
| **Plan** | Define problem, user, scope, success — working backwards from the user | **PRD / one-pager** | Define *eval* success criteria, not just product KPIs ("what does a *good* output mean, measurably?") |
| **Design** | Decide *how*; surface risks & alternatives before coding | **Design Doc / RFC**, the 3 diagrams, **ADRs** | Model selection + cost/latency budget, **eval strategy**, prompt/agent design, RAG/data design, guardrails & PII handling |
| **Build** | Implement in thin slices, reviewed | Small PRs, tests, **CI gates**, conventional commits, trunk-based dev | **Evals as tests** (offline sets + LLM-as-judge), prompt/agent **versioning**, tracing wired in from the first slice |
| **Deploy** | Ship safely, observe, roll back | CD pipeline, Docker/IaC, dev→staging→prod, canary/progressive rollout, SLOs + alerts | **Online evals**, cost/latency monitoring, human-in-the-loop review queues, model/prompt rollback |

**Artifact order (do not skip ahead):** PRD → diagrams (context → flow → architecture) →
Design Doc/RFC → ADRs → build (with CI + evals + tracing) → deploy. The **PRD comes first** so
diagrams serve documented requirements rather than floating free. The three diagrams are
distinct altitudes: **context** (system as one black box + external actors/systems), **flow**
(the stages as input→output with human-in-the-loop gates), **architecture** (internal components
and who calls whom). Design at the altitude where decisions are still reversible, then stop.

**Two practices beginners skip — we don't:**
- **Evals are the new unit tests.** You can't assert `output == expected` on an LLM. Build
  curated eval sets (inputs + rubrics), score them (often LLM-as-judge), and gate changes on eval
  scores in CI. Traces (Langfuse) feed the eval datasets — which is *why* observability is set up
  first.
- **Responsible AI, recorded as a first-class risk.** Name the domain risks up front with a
  one-line mitigation each. For this project specifically: hiring/employment is **high-risk under
  the EU AI Act** and laws like **NYC Local Law 144**; auto-apply touches job-board **Terms of
  Service**; "tailoring" must never become **fabrication**. Keep a **human approval gate before any
  irreversible/outward action** (e.g. submitting an application).

**Decisions get recorded as ADRs** (Architecture Decision Records): short, dated docs capturing
*the decision, the alternatives considered, and the why* — so they aren't relitigated later. When
a meaningful choice is made (stack, framework, model, data design), write an ADR.

## Status

Early stage. The repository currently contains `README.md` ("AI Job Assistant"), this
`CLAUDE.md`, and a Python-oriented `.gitignore`. There is no source code, build configuration,
dependency manifest, or tests yet.

The `.gitignore` indicates this is intended to be a **Python** project. It includes patterns for
several frameworks/tools that may end up being used: Django, Flask, Scrapy, Celery, Streamlit,
Jupyter/IPython, and Marimo. None are committed yet, so treat these as hints about possible
direction rather than established choices.

## Updating this file

As the project takes shape, expand this file with:

- **Commands** — how to install dependencies, run the app, run the test suite, run a single
  test, and lint/format. Add these once a dependency manifest (`pyproject.toml`,
  `requirements.txt`, etc.) and tooling exist.
- **Architecture** — the high-level structure and the big-picture flow that spans multiple
  modules, once there is code to describe.