#!/usr/bin/env bash
# Bounded collection and strict local publication; no git push or deploy.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -f .cache/relationships/sec-contact.env ]]; then
  source .cache/relationships/sec-contact.env
fi
.venv/bin/python -m relationships_py collect-round "$@"
.venv/bin/python -m relationships_py auto-publish
