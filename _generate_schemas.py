#!/usr/bin/env python3
"""
_generate_schemas.py

Reads every batch_XX.json in 04_batched_questions/ and writes one
schema_XX.sql in schemas/ for each batch.

The first .sql file (lowest XX) contains:
  - DROP TABLE IF EXISTS questions;
  - CREATE TABLE questions ( ... );

All .sql files contain INSERT statements for their rows, with a batch_id
column derived from the numeric suffix of the input filename.

The script is resilient to missing fields — any field not present in a
particular JSON object is inserted as NULL.
"""

import json
import os
import re
import sys
import glob as globmod
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_DIR = SCRIPT_DIR / "04_batched_questions"
OUTPUT_DIR = SCRIPT_DIR / "schemas"

# ---------------------------------------------------------------------------
# SQL helpers
# ---------------------------------------------------------------------------


def sql_escape(value):
    """Escape a Python value for SQLite literal insertion."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    # Convert anything else to string and escape single quotes
    s = str(value).replace("'", "''")
    return f"'{s}'"


def to_json_text(value):
    """Serialize a Python value to a JSON string for storage in a TEXT column."""
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Flatten one question object into a flat dict ready for INSERT
# ---------------------------------------------------------------------------

# Some batches have cognitive_level / question_type at the top level;
# others have them only inside metadata.  We normalise to top-level.


def flatten_question(obj, batch_id):
    """Return an OrderedDict-like dict with all columns for one row."""
    meta = obj.get("metadata") or {}

    row = {}

    # -- identifiers --------------------------------------------------------
    row["batch_id"] = batch_id
    row["id"] = obj.get("id")
    row["curriculum_area"] = obj.get("curriculum_area")
    row["lecturer"] = obj.get("lecturer")
    row["topic"] = obj.get("topic")
    row["clusters"] = to_json_text(obj.get("clusters"))

    # cognitive_level & question_type: top-level wins, fall back to metadata
    row["cognitive_level"] = obj.get("cognitive_level") or meta.get("cognitive_level")
    row["question_type"] = obj.get("question_type") or meta.get("question_type")
    row["distractor_strategy"] = obj.get("distractor_strategy")

    # -- metadata -----------------------------------------------------------
    row["difficulty"] = meta.get("difficulty")
    row["source_file"] = meta.get("source_file")
    row["source_file_page_number"] = meta.get("source_file_page_number")
    row["topics"] = to_json_text(meta.get("topics"))

    # -- question -----------------------------------------------------------
    row["question_prompt"] = obj.get("question_prompt")

    # -- choices (stored as JSON array) -------------------------------------
    row["choices"] = to_json_text(obj.get("choices"))

    # -- explanation (stored as JSON object) ---------------------------------
    row["explanation"] = to_json_text(obj.get("explanation"))

    # -- related questions (stored as JSON array) ----------------------------
    row["related_questions"] = to_json_text(obj.get("related_questions"))

    return row


# ---------------------------------------------------------------------------
# Column definitions for the CREATE TABLE
# ---------------------------------------------------------------------------

COLUMNS = [
    ("batch_id", "INTEGER NOT NULL"),
    ("id", "TEXT"),
    ("curriculum_area", "TEXT"),
    ("lecturer", "TEXT"),
    ("topic", "TEXT"),
    ("clusters", "TEXT"),  # JSON array
    ("cognitive_level", "TEXT"),
    ("question_type", "TEXT"),
    ("distractor_strategy", "TEXT"),
    ("difficulty", "TEXT"),
    ("source_file", "TEXT"),
    ("source_file_page_number", "INTEGER"),
    ("topics", "TEXT"),  # JSON array
    ("question_prompt", "TEXT"),
    ("choices", "TEXT"),  # JSON array
    ("explanation", "TEXT"),  # JSON object
    ("related_questions", "TEXT"),  # JSON array
]

COLUMN_NAMES = [c[0] for c in COLUMNS]

# ---------------------------------------------------------------------------
# Build the CREATE TABLE statement
# ---------------------------------------------------------------------------


def create_table_sql():
    lines = ["DROP TABLE IF EXISTS questions;", ""]
    lines.append("CREATE TABLE questions (")
    col_lines = []
    for name, typedef in COLUMNS:
        col_lines.append(f"  {name} {typedef}")
    lines.append(",\n".join(col_lines))
    lines.append(");")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Build INSERT statements for a list of row dicts
# ---------------------------------------------------------------------------


def insert_sql(rows):
    if not rows:
        return ""
    parts = []
    for row in rows:
        values = ", ".join(sql_escape(row.get(col)) for col in COLUMN_NAMES)
        parts.append(
            f"INSERT INTO questions ({', '.join(COLUMN_NAMES)}) VALUES ({values});"
        )
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    # Discover batch files, sorted by suffix
    pattern = str(INPUT_DIR / "batch_*.json")
    batch_files = sorted(globmod.glob(pattern))

    if not batch_files:
        print(f"No batch files found in {INPUT_DIR}", file=sys.stderr)
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for idx, filepath in enumerate(batch_files):
        filename = os.path.basename(filepath)
        # Extract numeric suffix: batch_00.json -> 0
        match = re.search(r"batch_(\d+)\.json$", filename)
        if not match:
            print(f"Skipping {filename}: cannot parse batch number", file=sys.stderr)
            continue
        batch_id = int(match.group(1))
        suffix = match.group(1)  # e.g. "00"

        # Read JSON
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            print(
                f"Skipping {filename}: top-level JSON is not an array", file=sys.stderr
            )
            continue

        rows = [flatten_question(obj, batch_id) for obj in data]

        # Build SQL
        sql_parts = []
        if idx == 0:
            sql_parts.append(create_table_sql())
            sql_parts.append("")
        sql_parts.append(f"-- Data from {filename} (batch_id = {batch_id})")
        sql_parts.append(insert_sql(rows))
        sql_parts.append("")  # trailing newline

        out_path = OUTPUT_DIR / f"schema_{suffix}.sql"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(sql_parts))

        print(f"  {out_path.name}  ({len(rows)} rows)")

    print(f"\nDone. Generated {len(batch_files)} schema files in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
