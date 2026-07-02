#!/usr/bin/env bash
#
# Updates the status of cards on the GitHub Projects (v2) roadmap board to match
# real development progress. Companion to create-roadmap-board.sh (which creates
# the board). Source of truth for progress: git history + docs/roadmap.md.
#
# Idempotent: setting a card to a status it already has is a no-op, so re-running
# is safe. Edit the "DESIRED STATE" block below as work moves, then re-run.
#
# PREREQS (same as create-roadmap-board.sh):
#   1. Install gh + jq
#   2. Authenticate:      gh auth login
#   3. Add project scope: gh auth refresh -s project,read:project
#
# Then: bash scripts/update-board-status.sh
#
set -euo pipefail

OWNER="ioarun"                       # personal account that owns the project
PROJECT_NUMBER=2                     # "AI Job Assistant — Roadmap"

# --- Resolve the project id, Status field id, and its option ids dynamically ---
# (IDs are stable, but resolving them keeps this script robust to board rebuilds.)
echo "==> Resolving project '$PROJECT_NUMBER' under @$OWNER ..."
PROJECT_ID=$(gh project view "$PROJECT_NUMBER" --owner "$OWNER" --format json | jq -r '.id')

FIELDS_JSON=$(gh project field-list "$PROJECT_NUMBER" --owner "$OWNER" --format json)
STATUS_FIELD_ID=$(echo "$FIELDS_JSON" | jq -r '.fields[] | select(.name=="Status") | .id')

# Map each Status option name -> its option id (Todo / In Progress / Done).
declare -A OPTION_ID
while IFS=$'\t' read -r name id; do
  OPTION_ID["$name"]="$id"
done < <(echo "$FIELDS_JSON" \
  | jq -r '.fields[] | select(.name=="Status") | .options[] | "\(.name)\t\(.id)"')

# Snapshot all items once (title -> item id) to avoid a lookup per card.
ITEMS_JSON=$(gh project item-list "$PROJECT_NUMBER" --owner "$OWNER" --format json)

# set_status "<exact card title>" "<Todo|In Progress|Done>"
set_status() {
  local title="$1" status="$2" item_id option_id
  item_id=$(echo "$ITEMS_JSON" | jq -r --arg t "$title" \
    '.items[] | select(.content.title==$t) | .id')
  option_id="${OPTION_ID[$status]:-}"

  if [ -z "$item_id" ]; then
    echo "  !! card not found (check the title): $title" >&2
    return 1
  fi
  if [ -z "$option_id" ]; then
    echo "  !! unknown status '$status' (want: Todo | In Progress | Done)" >&2
    return 1
  fi

  gh project item-edit --id "$item_id" --project-id "$PROJECT_ID" \
    --field-id "$STATUS_FIELD_ID" --single-select-option-id "$option_id" >/dev/null
  echo "  $title -> $status"
}

# ======================= DESIRED STATE (edit as progress moves) =======================
# Cadence: a step card -> "In Progress" when you start it, "Done" when its commit lands.
# The Phase card -> "In Progress" at its first step, "Done" only when its exit criteria
# are met (docs/roadmap.md). Cards left unlisted keep their current status.

echo "==> Applying statuses ..."
set_status "Phase A — Walking skeleton"                            "In Progress"
set_status "A1 — uv init + project layout + dependency manifest"   "Done"
set_status "A2 — docker-compose: Postgres + self-hosted Langfuse"  "Done"
# A3 — FastAPI /health + traced hello call : Todo  (next up — flip to In Progress on step 6)
# A4 — CI: lint + smoke test               : Todo
# Phases B–H                               : Todo
# ======================================================================================

echo ""
echo "==> Done. Open the board:"
gh project view "$PROJECT_NUMBER" --owner "$OWNER" --web