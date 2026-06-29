#!/usr/bin/env bash
#
# Creates a GitHub Projects (v2) board for the AI Job Assistant roadmap.
# Cards = 8 phase issues (A-H) + Phase A's 4 concrete steps, all placed in "Todo".
# Source of truth: docs/roadmap.md
#
# PREREQS (run these once yourself):
#   1. Install gh:        https://github.com/cli/cli#installation
#                         (Ubuntu: see the apt instructions on that page)
#   2. Authenticate:      gh auth login
#   3. Add project scope: gh auth refresh -s project,read:project
#
# Then: bash scripts/create-roadmap-board.sh
#
set -euo pipefail

OWNER="ioarun"                       # personal account that owns the repo
REPO="ioarun/ai-job-assistant-v2"
TITLE="AI Job Assistant — Roadmap"

echo "==> Creating project '$TITLE' under @$OWNER ..."
PROJECT_NUMBER=$(gh project create --owner "$OWNER" --title "$TITLE" --format json | jq -r '.number')
PROJECT_ID=$(gh project view "$PROJECT_NUMBER" --owner "$OWNER" --format json | jq -r '.id')
echo "    project #$PROJECT_NUMBER ($PROJECT_ID)"

# Look up the default Status field + its "Todo" option id.
FIELDS_JSON=$(gh project field-list "$PROJECT_NUMBER" --owner "$OWNER" --format json)
STATUS_FIELD_ID=$(echo "$FIELDS_JSON" | jq -r '.fields[] | select(.name=="Status") | .id')
TODO_OPTION_ID=$(echo "$FIELDS_JSON" | jq -r '.fields[] | select(.name=="Status") | .options[] | select(.name=="Todo") | .id')

# Idempotent label creation (ignore "already exists" errors).
gh label create "roadmap"       --repo "$REPO" --color "0e8a16" --description "Roadmap phase/step"        2>/dev/null || true
gh label create "tier:mvp"      --repo "$REPO" --color "1d76db" --description "MVP (Phases A+B+C)"          2>/dev/null || true
gh label create "tier:post-mvp" --repo "$REPO" --color "fbca04" --description "Post-MVP (Phases D-G)"       2>/dev/null || true
gh label create "tier:future"   --repo "$REPO" --color "b60205" --description "Future (Phase H)"            2>/dev/null || true

# add_card <title> <labels-csv> <body>
add_card() {
  local title="$1" labels="$2" body="$3"
  echo "==> Issue: $title"
  local url item_id
  url=$(gh issue create --repo "$REPO" --title "$title" --label "$labels" --body "$body")
  item_id=$(gh project item-add "$PROJECT_NUMBER" --owner "$OWNER" --url "$url" --format json | jq -r '.id')
  gh project item-edit --id "$item_id" --project-id "$PROJECT_ID" \
    --field-id "$STATUS_FIELD_ID" --single-select-option-id "$TODO_OPTION_ID" >/dev/null
}

# ---- Phase cards (A-H) ----
add_card "Phase A — Walking skeleton" "roadmap,tier:mvp" \
"FastAPI + Postgres + Langfuse under Docker; one traced hello-OpenAI call; CI green. Maps to RFC milestone 1. See docs/roadmap.md Phase A."
add_card "Phase B — Resume parse slice" "roadmap,tier:mvp" \
"upload → OpenAI structured parse → persist, traced; + parse eval harness. PRD stage 1; RFC milestones 2,4. See docs/roadmap.md Phase B."
add_card "Phase C — HITL review gate + minimal UI (MVP complete)" "roadmap,tier:mvp" \
"Light LangGraph interrupt() review gate; separate front end. Closes the MVP loop (PRD stage 1). See docs/roadmap.md Phase C."
add_card "Phase D — Job search" "roadmap,tier:post-mvp" \
"Adzuna behind JobSource + pick-job gate; first embeddings/vector store for semantic match. PRD stage 2. See docs/roadmap.md Phase D."
add_card "Phase E — Gap analysis" "roadmap,tier:post-mvp" \
"Per selected job: match score + honest gaps; upskilling resource suggestions. PRD stage 3. See docs/roadmap.md Phase E."
add_card "Phase F — Tailored resume + cover letter" "roadmap,tier:post-mvp" \
"Grounded generation (no fabrication); no-fabrication eval gate; approve gate. PRD stages 4,5. See docs/roadmap.md Phase F."
add_card "Phase G — Advanced techniques" "roadmap,tier:post-mvp" \
"Mature agentic/multi-agent orchestration; better RAG retrieval; MCP servers/tools. See docs/roadmap.md Phase G."
add_card "Phase H — Auto-apply + productionization" "roadmap,tier:future" \
"Human-gated submission (ToS-aware); deploy dev→staging→prod; online evals; monitoring/SLOs. PRD stage 6 + deploy. See docs/roadmap.md Phase H."

# ---- Phase A concrete steps ----
add_card "A1 — uv init + project layout + dependency manifest" "roadmap,tier:mvp" \
"uv init (Python 3.12), first dependency manifest, project layout (app/, tests/, docker-compose.yml, .env.example). Tutor rule: Arun runs scaffolders. See docs/roadmap.md Phase A."
add_card "A2 — docker-compose: Postgres + self-hosted Langfuse" "roadmap,tier:mvp" \
"docker-compose bringing up Postgres (ADR-0009) and self-hosted Langfuse (ADR-0005), per ADR-0006. See docs/roadmap.md Phase A."
add_card "A3 — FastAPI app: /health + one traced hello-OpenAI call" "roadmap,tier:mvp" \
"Minimal FastAPI app (ADR-0002) with /health and one traced hello-OpenAI call (ADR-0010) via Langfuse's OpenAI integration. See docs/roadmap.md Phase A."
add_card "A4 — CI (GitHub Actions): lint + smoke test" "roadmap,tier:mvp" \
"GitHub Actions [ASSUMPTION] running lint + a smoke test; conventional commits, trunk-based dev. See docs/roadmap.md Phase A."

echo ""
echo "==> Done. Open the board:"
gh project view "$PROJECT_NUMBER" --owner "$OWNER" --web
