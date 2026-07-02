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
| [0004](0004-claude-llm.md) | Anthropic Claude (`claude-opus-4-8`) as the LLM | Superseded by [0010](0010-openai-llm.md) |
| [0005](0005-langfuse-observability.md) | Self-hosted Langfuse for observability/tracing | Accepted |
| [0006](0006-docker-compose.md) | Docker + docker-compose for local env & packaging | Accepted |
| [0007](0007-job-source-adzuna.md) | Adzuna API behind a `JobSource` interface | Accepted |
| [0008](0008-frontend-separate-app.md) | Front end as a separate app (not folded into backend) | Accepted |
| [0009](0009-postgres-app-db.md) | PostgreSQL as the application database | Accepted |
| [0010](0010-openai-llm.md) | OpenAI as the LLM (supersedes ADR-0004) | Accepted |
| [0013](0013-separate-compose-stacks.md) | Separate compose stacks for app and Langfuse; app on host (refines ADR-0006) | Accepted |