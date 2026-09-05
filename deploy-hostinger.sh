#!/usr/bin/env bash
# DEPRECATED — use ./deploy.sh or ./scripts/deploy.sh (same HOSTINGER_FTP_* env vars)
# Kept for backward compat, delegates to scripts/deploy.sh and maps legacy HOSTINGER_* vars.
echo "WARN: deploy-hostinger.sh is deprecated — use ./deploy.sh or ./scripts/deploy.sh" >&2
echo "Mapping legacy HOSTINGER_HOST/USER/PASS -> HOSTINGER_FTP_HOST/USER/PASS ..." >&2
export HOSTINGER_FTP_HOST="${HOSTINGER_FTP_HOST:-${HOSTINGER_HOST:-}}"
export HOSTINGER_FTP_USER="${HOSTINGER_FTP_USER:-${HOSTINGER_USER:-}}"
export HOSTINGER_FTP_PASS="${HOSTINGER_FTP_PASS:-${HOSTINGER_PASS:-}}"
export HOSTINGER_FTP_PORT="${HOSTINGER_FTP_PORT:-${HOSTINGER_PORT:-}}"
export HOSTINGER_FTP_REMOTE_DIR="${HOSTINGER_FTP_REMOTE_DIR:-${HOSTINGER_REMOTE_DIR:-public_html}}"
exec "$(dirname "$0")/scripts/deploy.sh" "$@"
