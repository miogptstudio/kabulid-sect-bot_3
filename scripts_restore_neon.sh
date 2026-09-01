#!/usr/bin/env bash
# ریستور بک‌آپ PostgreSQL روی Neon
# Usage:
#   export DATABASE_URL='postgresql://neondb_owner:PASS@ep-xxx.aws.neon.tech/neondb?sslmode=require'
#   bash scripts_restore_neon.sh /path/to/2026-08-30T21:26Z/kabulid_sect

set -euo pipefail

DUMP_DIR="${1:-}"
if [[ -z "$DUMP_DIR" || ! -d "$DUMP_DIR" ]]; then
  echo "Usage: $0 /path/to/directory-format-dump"
  echo "Example: $0 ./2026-08-30T21:26Z/kabulid_sect"
  exit 1
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: set DATABASE_URL first"
  exit 1
fi

if ! command -v pg_restore >/dev/null 2>&1; then
  echo "ERROR: pg_restore not found. Install postgresql-client."
  exit 1
fi

# strip channel_binding if present
URL="${DATABASE_URL//&channel_binding=require/}"
URL="${URL//channel_binding=require&/}"
URL="${URL//\?channel_binding=require/}"

echo "Restoring from: $DUMP_DIR"
echo "Target: ${URL%%@*}@***"

pg_restore --verbose --clean --if-exists --no-owner --no-acl \
  -d "$URL" \
  "$DUMP_DIR"

echo "Done. Restart the bot so migrate_schema / load_from_db run."
