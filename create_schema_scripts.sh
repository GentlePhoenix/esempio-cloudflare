#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# create_schema_scripts.sh
#
# Scans all JSON files in 04_batched_questions/ and generates one
# schema_XX.sql file per batch inside schemas/.
#
# The FIRST schema file (lowest numbered batch) includes:
#   DROP TABLE IF EXISTS questions;
#   CREATE TABLE questions ( ... );
#
# Every schema file contains INSERT statements for the rows in that batch.
#
# Usage:  ./create_schema_scripts.sh
# Requires: Python 3 (any version >= 3.6)
# ---------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec python3 "${SCRIPT_DIR}/_generate_schemas.py" "$@"
