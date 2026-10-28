#!/usr/bin/env bash
# Creates the working branches locally from the current branch. Does NOT push.
# Run from the repo root: bash scripts/setup_branches.sh
set -euo pipefail

BRANCHES=(
  a/bedrock-live
  a/prompts
  a/evaluation
  b/pricing
  b/diagram
  b/security
  b/ui
  shared/scenarios
)

for b in "${BRANCHES[@]}"; do
  if git show-ref --verify --quiet "refs/heads/$b"; then
    echo "exists: $b"
  else
    git branch "$b"
    echo "created: $b"
  fi
done
