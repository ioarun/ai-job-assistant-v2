# Phase 0 — Ideation & Planning

> Part of the [AI Job Assistant](README.md) phased build. Phase 0 produced the planning
> artifacts and a plan for every subsequent phase — **before** any code.

Produce the planning artifacts and a plan for every subsequent phase.

## The planning sequence (how we work through Phase 0)

We move from "outside & vague" to "inside & precise" — each step answers one
question before the next builds on it:

| Step | Question it answers | View |
|---|---|---|
| Ideation | What is this, roughly? | — |
| PRD | What & why? What's in scope? (ground truth for *what*) | — |
| ADRs | Which decisions did we make, and why? (ongoing — accrue as we decide) | — |
| Context diagram | Who/what does the system talk to in the world? (the boundary) | structural |
| Flow diagram | What happens, in what order, with which human approvals? | behavioral |
| Architecture diagram | What are the internal building blocks, and how do they wire up? | structural |
| Design Doc / RFC | How is it built? (ground truth for *how*) | — |
| Eval strategy | How do we measure whether the AI output is good? | — |
| Roadmap | What are the build phases (A–H), and in what order? | — |

Two **lenses** we keep separate: *structural* views show what **is** there (context,
architecture); *behavioral* views show what **happens** (flow). Two **authorities**
we keep separate: the **PRD owns _what & why_**, the **RFC owns _how_** — so scope
debates and design debates don't leak into each other.

**Exit criteria:** every row below is ✅.

| Artifact | Description | Location | Status |
|---|---|---|---|
| PRD | Product requirements (what & why), success + eval criteria | `docs/prd.md` | ✅ |
| ADRs | Decision records for stack & key choices (0001–0010) | `docs/adr/` | ✅ |
| Context diagram | System as a black box + external actors/systems (C4 L1) | `docs/diagrams/context.md` | ✅ |
| Flow diagram | Stages as input→output with HITL gates (MVP/Post-MVP/Future) | `docs/diagrams/flow.md` | ✅ |
| Architecture diagram | Internal containers and who calls whom (C4 L2) | `docs/diagrams/architecture.md` | ✅ |
| Design Doc / RFC | The technical *how*; ties diagrams + decisions + risks together | `docs/design.md` | ✅ |
| Eval strategy | How we measure LLM output quality (eval sets, rubrics, judge) | `docs/eval-strategy.md` | ✅ |
| Responsible-AI risk register | Domain risks + mitigations (hiring high-risk, ToS, no fabrication) | `docs/responsible-ai.md` | ✅ |
| Roadmap + per-phase plans | Phase A–H breakdown with goals/scope/exit criteria | `docs/roadmap.md` | ✅ |
| Project board | GitHub Projects board seeded from the roadmap | GitHub Projects | ✅ |

## Setting up the project board

A GitHub Projects (v2) board seeded from `docs/roadmap.md` (8 phases A–H + Phase A's 4 concrete steps) can be created with a helper script. **One-time setup:**

```bash
# Install dependencies (if not already present)
sudo apt install -y gh jq

# Authenticate with GitHub (opens browser)
gh auth login
gh auth refresh -s project,read:project

# Create the board
bash scripts/create-roadmap-board.sh
```

This creates a GitHub Projects board under your account, seeds it with issues for each phase/step, and opens the board in your browser. Subsequent phases are fleshed out just-in-time as you reach them (anti-waterfall).

Board statuses are kept in sync with development via `scripts/update-board-status.sh`.
