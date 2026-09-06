#!/usr/bin/env bash
# Machine Made Worlds — Hostinger deploy via lftp/FTP/SFTP
# Syncs dist/ -> public_html on Hostinger. Board approval required before first live push.
# Usage:
#   HOSTINGER_FTP_HOST=ftp.example.com HOSTINGER_FTP_USER=u123 HOSTINGER_FTP_PASS=secret ./scripts/deploy.sh [--dry-run] [--yes]
# Env vars (HOSTINGER_FTP_* required, legacy HOSTINGER_* fallback for HOST):
#   HOSTINGER_FTP_HOST         e.g. 145.14.144.1 or ftp.machinemadeworlds.com
#   HOSTINGER_FTP_USER         Hostinger FTP username
#   HOSTINGER_FTP_PASS         Hostinger FTP password
#   HOSTINGER_FTP_PORT         default 21 (FTP) / 22 (SFTP) / 21 (FTPS)
#   HOSTINGER_FTP_PROTOCOL     ftp | sftp | ftps  (default ftp)
#   HOSTINGER_FTP_REMOTE_DIR   default public_html
#     NOTE (MAC-86, 2026-09-06, Hostinger account finding): on this account the
#     FTP login dir /public_html is NOT the live docroot (it contains a
#     DO_NOT_UPLOAD_HERE marker). The live docroot is
#     domains/machinemadeworlds.com/public_html (proven by probe-file test).
#     Set HOSTINGER_FTP_REMOTE_DIR=domains/machinemadeworlds.com/public_html
#     for this account. Default stays public_html for other accounts.
#   BOARD_APPROVED=1           bypass interactive approval check (required for CI/autonomous runs)
# Flags:
#   --dry-run  print what would be synced, do not push
#   --yes      confirm Board approval (same as BOARD_APPROVED=1)
#   --help     show help
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"
REMOTE_DEFAULT="public_html"

DRY_RUN=0
APPROVED=0

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --yes|--approved|--force) APPROVED=1 ;;
    --help|-h)
      echo "Usage: $0 [--dry-run] [--yes]"
      echo "Env: HOSTINGER_FTP_HOST, HOSTINGER_FTP_USER, HOSTINGER_FTP_PASS [+ PORT/PROTOCOL/REMOTE_DIR]"
      echo "REMOTE_DIR default: public_html"
      echo "NOTE (MAC-86): on this Hostinger account the live docroot is"
      echo "  domains/machinemadeworlds.com/public_html, not the FTP login dir"
      echo "  /public_html (DO_NOT_UPLOAD_HERE marker). Set:"
      echo "  HOSTINGER_FTP_REMOTE_DIR=domains/machinemadeworlds.com/public_html"
      exit 0
      ;;
    *) echo "Unknown arg: $arg (try --help)"; exit 1 ;;
  esac
done

if [[ "${BOARD_APPROVED:-0}" == "1" ]]; then APPROVED=1; fi

# Resolve env with legacy fallback
HOST="${HOSTINGER_FTP_HOST:-${HOSTINGER_HOST:-}}"
USER_VAL="${HOSTINGER_FTP_USER:-${HOSTINGER_USER:-}}"
PASS_VAL="${HOSTINGER_FTP_PASS:-${HOSTINGER_PASS:-}}"
PORT="${HOSTINGER_FTP_PORT:-${HOSTINGER_PORT:-}}"
PROTO="${HOSTINGER_FTP_PROTOCOL:-ftp}"
REMOTE="${HOSTINGER_FTP_REMOTE_DIR:-${HOSTINGER_REMOTE_DIR:-$REMOTE_DEFAULT}}"

# Default port by protocol
if [[ -z "$PORT" ]]; then
  case "$PROTO" in sftp) PORT=22 ;; ftps|ftp) PORT=21 ;; *) PORT=21 ;; esac
fi

# Validations
if [[ ! -d "$DIST_DIR" ]]; then
  echo "ERROR: dist/ not found at $DIST_DIR"
  echo "Build the site first so dist/ contains the deploy artifact."
  exit 1
fi
for f in index.html 404.html robots.txt sitemap.xml styles.css; do
  if [[ ! -f "$DIST_DIR/$f" ]]; then
    echo "WARN: dist/$f missing — dist may be incomplete"
  fi
done
if [[ ! -f "$DIST_DIR/about/index.html" ]]; then echo "WARN: dist/about/index.html missing"; fi
if [[ ! -f "$DIST_DIR/blog/index.html" ]]; then echo "WARN: dist/blog/index.html missing"; fi
if [[ -z "$HOST" ]]; then echo "ERROR: Set HOSTINGER_FTP_HOST (or legacy HOSTINGER_HOST)"; exit 1; fi
if [[ -z "$USER_VAL" ]]; then echo "ERROR: Set HOSTINGER_FTP_USER"; exit 1; fi
if [[ -z "$PASS_VAL" ]]; then echo "ERROR: Set HOSTINGER_FTP_PASS"; exit 1; fi

# Board approval gate
if [[ $APPROVED -eq 0 && $DRY_RUN -eq 0 ]]; then
  echo "Board approval required before first live push."
  echo "  This gate protects machinemadeworlds.com from unapproved publishes."
  echo "  After the Board approves in Paperclip, re-run with --yes or BOARD_APPROVED=1"
  echo ""
  echo "  Example: BOARD_APPROVED=1 ./scripts/deploy.sh"
  echo "  Dry-run (no approval needed): ./scripts/deploy.sh --dry-run"
  exit 3
fi

echo "=== Machine Made Worlds deploy ==="
echo "Source : $DIST_DIR/"
echo "Target : $USER_VAL@$HOST:$REMOTE (proto=$PROTO port=$PORT)"
echo "Files  : $(find "$DIST_DIR" -type f | wc -l | tr -d ' ') files, $(du -sh "$DIST_DIR" | cut -f1) total"
if [[ $DRY_RUN -eq 1 ]]; then
  echo "[dry-run] Would mirror dist/ -> $REMOTE via $PROTO"
fi
echo ""

if [[ $DRY_RUN -eq 1 ]]; then
  echo "--- dist contents (top) ---"
  find "$DIST_DIR" -type f | sort | head -n 50 | sed "s|$ROOT_DIR/||"
  if command -v lftp >/dev/null 2>&1; then
    echo ""
    echo "[dry-run] lftp found — preview command:"
    echo "  lftp -u \"$USER_VAL,***\" -p $PORT $HOST -e \"mirror -R -e --delete --verbose dist/ /$REMOTE/; quit\""
  else
    echo ""
    echo "lftp not installed — install it for real deploys:"
    echo "  macOS: brew install lftp"
    echo "  Debian/Ubuntu: sudo apt-get install lftp"
    echo "  Windows: use scripts/deploy.ps1 with WinSCP"
  fi
  echo ""
  echo "[dry-run] Done — no files pushed."
  exit 0
fi

# Real push — requires lftp
if ! command -v lftp >/dev/null 2>&1; then
  echo "ERROR: lftp not found. Install lftp or run scripts/deploy.ps1 on Windows (WinSCP)."
  echo "  macOS: brew install lftp"
  echo "  Debian/Ubuntu: sudo apt-get install lftp"
  exit 2
fi

echo "Pushing with lftp mirror -R --delete ..."
# Build lftp URL based on protocol
case "$PROTO" in
  sftp)
    LFTP_HOST="sftp://$HOST"
    ;;
  ftps)
    # lftp FTP over TLS — explicit
    LFTP_HOST="$HOST"
    SET_SSL="set ftp:ssl-force true; set ssl:verify-certificate no;"
    ;;
  ftp|*)
    LFTP_HOST="$HOST"
    SET_SSL=""
    ;;
esac

lftp -u "$USER_VAL,$PASS_VAL" -p "$PORT" "$LFTP_HOST" <<LFTP_EOF
${SET_SSL:-}
set cmd:fail-exit true
mirror --reverse --delete --verbose --parallel=3 \
  --exclude-glob .git/* \
  --exclude-glob .DS_Store \
  --exclude-glob Thumbs.db \
  --exclude .paperclip* \
  --exclude-glob posts/_template/* \
  --exclude posts/_template/ \
  "$DIST_DIR/" "/$REMOTE/"
bye
LFTP_EOF

echo ""
echo "Deploy finished. Verifying https://machinemadeworlds.com ..."
if command -v curl >/dev/null 2>&1; then
  curl -sS -o /dev/null -w "HTTP %{http_code} %{url_effective}\n" https://machinemadeworlds.com/ || echo "curl check failed — site may still be propagating"
  curl -sS -o /dev/null -w "sitemap HTTP %{http_code}\n" https://machinemadeworlds.com/sitemap.xml || true
else
  echo "(curl not found — open https://machinemadeworlds.com manually to verify)"
fi
