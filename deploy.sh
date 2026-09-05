#!/usr/bin/env bash
# Wrapper for convenience — delegates to scripts/deploy.sh
set -euo pipefail
exec "$(dirname "$0")/scripts/deploy.sh" "$@"
