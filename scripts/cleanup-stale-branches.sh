#!/bin/bash
# Cleanup stale branches that have been merged into main
# Usage: bash scripts/cleanup-stale-branches.sh [--dry-run]
#
# This script lists and optionally deletes branches from merged PRs.
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
OPEN_PR_BRANCHES=$(gh pr list --state open --json headRefName --jq '.[].headRefName' 2>/dev/null || echo "")

echo "Open PR branches (protected):"
echo "$OPEN_PR_BRANCHES" | sed 's/^/  - /'
echo ""

DELETED=0
SKIPPED=0

for branch in $REMOTE_BRANCHES; do
  # Skip protected branches
  if printf '%s\n' "${PROTECTED[@]}" | grep -qx "$branch"; then
    echo "⏭️  PROTECTED: $branch"
    continue
  fi

  # Skip branches with open PRs
  if echo "$OPEN_PR_BRANCHES" | grep -qx "$branch"; then
    echo "⏭️  OPEN PR: $branch"
    continue
  fi

  # Check if branch has been merged
  if git branch -r --merged origin/main | grep -q "origin/$branch"; then
    if [ "$DRY_RUN" = false ]; then
      echo "🗑️  Deleting: $branch"
      git push origin --delete "$branch"
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
