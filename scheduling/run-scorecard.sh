#!/usr/bin/env bash
# Agentic BI Team — unattended scorecard run (Linux / macOS, for cron).
#
#   ./scheduling/run-scorecard.sh weekly
#   ./scheduling/run-scorecard.sh monthly
#
# cron runs with a nearly empty environment and will not read your shell
# profile, so this sources .env from the repo root if it exists. Test the exact
# command by hand before trusting the schedule — almost every cron failure here
# is a missing variable or a relative path.
#
# See scheduling/SCHEDULING.md.

set -euo pipefail

PERIOD="${1:-weekly}"
if [[ "$PERIOD" != "weekly" && "$PERIOD" != "monthly" ]]; then
  echo "usage: $0 [weekly|monthly]" >&2
  exit 2
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Credentials: variable names live in .env.example, values in .env (gitignored).
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if ! command -v claude >/dev/null 2>&1; then
  echo "error: the 'claude' CLI is not on PATH." >&2
  echo "cron does not read your shell profile — use an absolute path here," >&2
  echo "or add the install dir to PATH at the top of this script." >&2
  exit 1
fi

echo "=== $(date -u +'%Y-%m-%dT%H:%M:%SZ') — /scorecard $PERIOD in $REPO_ROOT"
claude -p "/scorecard $PERIOD" --permission-mode acceptEdits

echo "=== $(date -u +'%Y-%m-%dT%H:%M:%SZ') — /health-check"
claude -p "/health-check" --permission-mode acceptEdits || \
  echo "warning: health check exited non-zero; see output above"

# The git history is the team's audit trail: each period's numbers, with a diff
# against the last. Commit locally; pushing is left to you deliberately.
if [[ -n "$(git status --porcelain scorecards/ knowledge/ 2>/dev/null)" ]]; then
  git add scorecards/ knowledge/
  git commit -m "chore: $PERIOD scorecard $(date -u +%Y-%m-%d)"
  echo "Committed. Push when you have reviewed it."
else
  echo "Nothing was written. That usually means the run failed rather than that"
  echo "there was no news — check the output above."
fi
