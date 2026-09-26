#!/usr/bin/env bash
# Call with an explicit allowlist. No automatic merge/rebase or force push.
set -euo pipefail
git diff --cached --quiet || { echo 'Unexpected staged files'; exit 1; }
git add -- "$@"
if git diff --cached --quiet; then exit 0; fi
branch="${GITHUB_REF_NAME:?Run only on the default branch}"
base=$(git rev-parse HEAD)
git fetch origin "$branch"
if [ "$(git rev-parse FETCH_HEAD)" != "$base" ]; then
  echo 'Remote advanced; refusing to overwrite newer calendar/state. Rerun on latest revision.'
  exit 1
fi
git -c user.name=github-actions -c user.email=actions@github.com commit -m 'Update generated MarketTimeZen data'
git push origin "HEAD:$branch"
