# ADR-0007: Source job listings via the Adzuna API behind a `JobSource` interface

Status: Accepted
Date: 2026-06-28

## Context
We need structured job listings for Australia. The top consumer boards (SEEK,
Indeed, LinkedIn) offer no public job-*search* API and prohibit scraping in their
Terms of Service, so they are not viable, legal sources. We need a legal, reliable,
structured source — and we don't want to couple the system to any single provider.

## Decision
Use the **Adzuna API** (free developer tier, Australia coverage, JSON responses) as
the v1 job source, accessed through a **pluggable `JobSource` interface**
(e.g. `search(query, location) -> list[JobPosting]`). Adzuna is the first
implementation of that interface.

## Alternatives considered
- **Scraping SEEK / Indeed / LinkedIn** — rejected: ToS violation, active blocking,
  and legal risk.
- **Jooble / JSearch / LoopCV** — viable developer APIs; deferred as future
  `JobSource` adapters.
- **Adzuna MCP server** — a future adapter that also advances the project's MCP
  learning goal.
- **Claude web-search tool** — returns unstructured pages and inherits the
  underlying sites' ToS ambiguity; not reliable for structured listings.

## Consequences
- (+) Legal, structured data quickly; ToS risk retired by design.
- (+) The interface lets us add/swap sources (incl. MCP) without a rewrite.
- (−) v1 coverage is limited to Adzuna's index.
- (−) Adds an external dependency and an API key to manage.