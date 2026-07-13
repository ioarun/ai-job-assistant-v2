# ADR-0017: Defer upskilling resource catalog out of project scope

Status: Accepted
Date: 2026-07-13

## Context
The roadmap's original Phase E scope included, alongside gap analysis, **upskilling
resource suggestions** — retrieving real courses/docs per missing skill from a curated
catalog, specifically to avoid hallucinated links. Designing this properly surfaced a
real fork: build a small static, hand-curated catalog (zero new infra, but needs a human
to source and vet real resources) versus a live external content API (scales better, but
needs the same kind of ToS/legal due-diligence ADR-0007 did for Adzuna — unstarted work).

Both paths are legitimate, but neither is core to the project's actual goal: taking a
resume from parse through to a tailored application for a specific job. Upskilling
suggestions are a nice-to-have adjacent feature, not part of that core path.

## Decision
**Remove the upskilling resource catalog from project scope entirely** (not merely
deferred to a later phase — parked, with no committed return date). Phase E narrows to
**gap analysis only**: `GapReport` (match score, matched skills, missing skills) via the
single Structured-Outputs call already built in `app/gap_analysis.py`.

The pipeline going forward is: resume upload → parse → HITL review → job search → LLM
rerank → pick → **gap analysis** → **tailored resume + cover letter (Phase F, next)**.

## Alternatives considered
- **Static curated catalog now** — rejected for now; would have required either the user
  personally sourcing real resources per skill, or Claude proposing candidates verified
  live via web search — real effort for a feature outside the core path.
- **Live external content API now** — rejected; needs unstarted ToS/legal research
  before it could even be evaluated, let alone built.
- **Keep it in Phase E scope but mark it `[OPEN]`/unscheduled** — rejected as
  half-committal; cleaner to record it as explicitly out of scope than let it linger as
  a perpetually-deferred item nobody revisits.

## Consequences
- (+) Phase E closes on just gap analysis, already built and tested — no new
  infrastructure, no unresolved external-dependency research blocking it.
- (+) The project stays focused on its core vertical: parse → search → gap → tailor,
  matching the thin-slice principle rather than growing breadth before that core path is
  proven end-to-end.
- (−) No upskilling suggestions feature exists or is planned. If revisited later, this
  ADR's alternatives (static catalog vs. live API) are the starting point, not a decision
  already made.

Narrows Phase E's scope from `docs/roadmap.md`; supersedes that document's "upskilling
suggestions" line for Phase E.
