#!/bin/bash
# Cleanup stale branches that have been merged into main
# Usage: bash scripts/cleanup-stale-branches.sh [--no-dry-run]
#
# Default mode is dry-run (no changes made, just listing).
# Pass --no-dry-run to actually delete merged stale branches.
#
# Protected branches (main, and branches with open PRs) are kept.

set -euo pipefail

DRY_RUN=true
if [[ "${1:-}" == "--no-dry-run" ]]; then
  DRY_RUN=false
fi

PROTECTED=("main")

echo "=== Stale Branch Cleanup ==="
if [ "$DRY_RUN" = true ]; then
  echo "🔍 DRY RUN mode — no branches will be deleted"
  echo "   Run with --no-dry-run to actually delete"
fi
echo ""

# Fetch latest from origin
git fetch --prune origin

# Get all remote branches
REMOTE_BRANCHES=$(git branch -r | sed 's|origin/||' | grep -v 'HEAD' | sort)

# Get branches with open PRs (protect these)
if command -v gh &>/dev/null; then
  OPEN_PR_BRANCHES=$(gh pr list --state open --json headRefName --jq '.[].headRefName' 2>/dev/null || echo "")
else
  echo "⚠️  WARNING: gh CLI not found — cannot detect open PR branches"
  echo "   Branches with open PRs will NOT be protected!"
  echo ""
  OPEN_PR_BRANCHES=""
fi

echo "Open PR branches (protected):"
if [ -n "$OPEN_PR_BRANCHES" ]; then
  echo "$OPEN_PR_BRANCHES" | sed 's/^/  - /'
else
  echo "  (none detected)"
fi
echo ""

# Confirmation step for non-dry-run
if [ "$DRY_RUN" = false ]; then
  echo "⚠️  About to delete all merged stale branches (excluding protected ones)."
  echo "   Type 'yes' to continue, anything else to abort:"
  read -r CONFIRM
  if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 1
  fi
fi

DELETED=0
SKIPPED=0

for branch in $REMOTE_BRANCHES; do
  # Skip protected branches
  if printf '%s\n' "${PROTECTED[@]}" | grep -Fqx "$branch"; then
    echo "⏭️  PROTECTED: $branch"
    continue
  fi

  # Skip branches with open PRs
  if [ -n "$OPEN_PR_BRANCHES" ] && echo "$OPEN_PR_BRANCHES" | grep -Fqx "$branch"; then
    echo "⏭️  OPEN PR: $branch"
    continue
  fi

  # Check if branch has been merged
  if git branch -r --merged origin/main | grep -Fq "origin/$branch"; then
    if [ "$DRY_RUN" = false ]; then
      echo "🗑️  Deleting: $branch"
      if ! git push origin --delete "$branch"; then
        echo "⚠️  Failed to delete: $branch"
      fi
    else
      echo "❌ Would delete: $branch (merged)"
    fi
    DELETED=$((DELETED + 1))
  else
    echo "⏭️  Not merged: $branch"
    SKIPPED=$((SKIPPED + 1))
  fi
done

echo ""
echo "=== Summary ==="
echo "Deleted: $DELETED"
echo "Skipped: $SKIPPED"
if [ "$DRY_RUN" = true ]; then
  echo ""
  echo "🔍 Run with --no-dry-run to perform actual deletion"
fi
