# Architecture Decision Records (ADRs)

Each ADR captures **one significant decision** and *why* we made it (including the
alternatives we rejected). ADRs are **numbered, dated, and immutable** — to change a
decision, add a new ADR that *supersedes* the old one rather than editing history.

Format: Michael Nygard's template (Status / Context / Decision / Alternatives /
Consequences).

| # | Decision | Status |
|---|---|---|
| [0001](0001-python-uv.md) | Python + uv for dependency & environment management | Accepted |
| [0002](0002-fastapi-backend.md) | FastAPI as the backend web framework | Accepted |
| [0003](0003-langgraph-orchestration.md) | LangGraph for agent/LLM orchestration | Accepted |
| [0004](0004-claude-llm.md) | Anthropic Claude (`claude-opus-4-8`) as the LLM | Accepted |
| [0005](0005-langfuse-observability.md) | Self-hosted Langfuse for observability/tracing | Accepted |
| [0006](0006-docker-compose.md) | Docker + docker-compose for local env & packaging | Accepted |
| [0007](0007-job-source-adzuna.md) | Adzuna API behind a `JobSource` interface | Accepted |