#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# run_schema_scripts.sh
#
# Executes every *.sql file found in schemas/ against the D1 database
# using wrangler, in sorted order so schema_00.sql (with CREATE TABLE)
# runs first.
#
# Usage:  ./run_schema_scripts.sh
# ---------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCHEMAS_DIR="${SCRIPT_DIR}/schemas"

for sql_file in $(ls "${SCHEMAS_DIR}"/*.sql | sort); do
  filename="$(basename "$sql_file")"
  echo ">>> Executing ${filename} ..."
  npx wrangler d1 execute quiz-app-db --remote --file="./schemas/${filename}"
  echo "    Done."
done

echo ""
echo "All schema scripts executed successfully."
