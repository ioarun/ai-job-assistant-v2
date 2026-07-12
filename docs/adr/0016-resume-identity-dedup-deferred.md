# ADR-0016: Resume identity & deduplication — deferred

Status: Proposed (deferred — no decision made yet)
Date: 2026-07-12

## Context
`POST /resumes` creates a **brand-new `Resume` row with a new auto-incrementing `id`**
on every call — regardless of whether the exact same PDF (by content) was already
uploaded, parsed, and approved earlier. There is no content hash, no lookup, no concept
of "have I seen this file before."

Concretely, uploading the same resume twice produces:
- Two separate `resume` rows with unrelated IDs
- Two separate `parse_run` rows, each starting fresh at `status="pending"`
- **Two independent OpenAI calls** — the second upload re-parses from scratch, with zero
  awareness of the first upload's result or approval
- Two separate LangGraph `thread_id`s, so the two runs don't interfere with each other,
  but also share nothing

This was a reasonable non-goal for Phases B/C — the RFC's MVP scope is explicitly
single-user with no `users` table (`docs/design.md` §5), and a thin-slice review gate
doesn't need resume history. But it will likely need addressing as the project grows:
a user re-uploading a lightly-edited resume, wanting to avoid needless re-parse cost, or
later multi-user phases needing real applicant identity anyway.

## Decision
**Not yet decided.** This ADR exists to record the problem and the candidate approaches
for a future phase to pick up deliberately, rather than leaving it as an untracked,
implicit gap.

## Candidate approaches (none chosen)
- **Content-hash dedup** — hash the uploaded PDF bytes (e.g. SHA-256); if a `Resume` with
  the same hash already exists, skip re-parsing and either reuse the existing approved
  result or prompt the user ("this resume was already uploaded on [date] — reuse it?").
- **User/session identity** — introduce a lightweight applicant/user concept so resumes
  group and version per person, rather than remaining anonymous, disconnected rows. Likely
  needed anyway once the project is no longer single-user.
- **Explicit versioning** — let a resume be explicitly linked as "a new version of resume
  #6" rather than auto-detecting duplicates by hash; puts the decision in the user's
  hands instead of inferring it.
- **Do nothing (status quo)** — accept that re-parsing is cheap and fast enough at
  current scale (one Structured-Outputs call) to not be worth the added complexity yet.

## Consequences (of remaining undecided)
- Every upload costs a real OpenAI call, even for an identical re-upload.
- No way to see a given applicant's resume history/versions over time.
- Acceptable for MVP/demo purposes; revisit if real usage shows this matters — e.g. cost
  at scale, or the multi-user work in Phase D+ requiring real identity regardless.
