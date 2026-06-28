# ADR-0001: Python + uv for dependency and environment management

Status: Accepted
Date: 2026-06-28

## Context
This is a Python GenAI project that needs reproducible dependencies and a managed
interpreter. The system Python is 3.8 (too old for FastAPI/LangGraph/Langfuse,
which want 3.10+). We also want reproducible installs so Docker images build
identically every time, and a single fast tool rather than stitching together
several.

## Decision
Use **uv** to manage the Python version (3.12), the virtual environment,
dependencies, and the lockfile (`uv.lock`). Add dependencies with `uv add`; run
project commands with `uv run`.

## Alternatives considered
- **pip + venv** — simplest, but manual and weakest reproducibility (no first-class
  lockfile).
- **Poetry** — mature and lockfile-based, but slower and heavier than uv.

## Consequences
- (+) One fast tool for env + deps + lockfile; downloads its own Python so the old
  system 3.8 is irrelevant.
- (+) `uv.lock` gives reproducible Docker builds.
- (−) A newer tool the developer must install; less ubiquitous than pip.