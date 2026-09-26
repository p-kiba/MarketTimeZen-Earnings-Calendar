#!/usr/bin/env bash
# Actual bounded collection only; no approval, public export, git push or deploy.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -f .cache/relationships/sec-contact.env ]]; then
  source .cache/relationships/sec-contact.env
fi
exec .venv/bin/python -m relationships_py collect-round "$@"
