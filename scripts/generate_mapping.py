"""
Generate mapping JSON files from source CSV data.

Each mapping lives under mapping/<name>/ as one or more CSV files.  All
``*.csv`` files in the directory are read (sorted by filename) and
concatenated into a single key list.  The generated JSON is written to
mapping/<name>.json.

CSV format:
    - The first column MUST be ``key``.
    - A ``comment`` column, if present, is for human documentation only
      and is stripped from the output.
    - All other columns (e.g. ``displayName``) are carried through into
      the generated JSON entries as-is.

ID assignment is append-only: existing entries in the JSON keep their
IDs and order; new keys found in the CSV are appended at the end with
the next available ID.
Removing or reordering existing keys is treated as an error.
"""

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
MAPPING_DIR = REPO_ROOT / "mapping"

# Each entry: (source_directory, output_json, schema_ref)
MAPPINGS: list[tuple[Path, Path, str]] = [
    (
        MAPPING_DIR / "identification",
        MAPPING_DIR / "identification.json",
        "./identification.schema.json",
    ),
    (
        MAPPING_DIR / "shiny",
        MAPPING_DIR / "shiny.json",
        "./shiny.schema.json",
    ),
]

# Columns that are never included in the generated JSON output.
IGNORED_COLUMNS: set[str] = {"comment"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def read_existing_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, obj: dict) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def read_csv_entries(source_dir: Path) -> list[dict[str, str]]:
    """
    Read all ``*.csv`` files in *source_dir* and return a combined entry list.
    """
    csv_files = sorted(source_dir.glob("*.csv"))
    if not csv_files:
        print(f"ERROR: no CSV files found in {source_dir}", file=sys.stderr)
        sys.exit(1)

    entries: list[dict[str, str]] = []
    seen_keys: set[str] = set()

    for csv_file in csv_files:
        with open(csv_file, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None or "key" not in reader.fieldnames:
                print(
                    f"ERROR: {csv_file.name} is missing the required 'key' column header",
                    file=sys.stderr,
                )
                sys.exit(1)

            # Determine which columns to keep (all except ignored ones)
            output_fields = [
                col for col in reader.fieldnames if col.strip() not in IGNORED_COLUMNS
            ]

            for row in reader:
                key = row["key"].strip()
                if not key:
                    continue
                if key in seen_keys:
                    print(
                        f"ERROR: duplicate key '{key}' found in {csv_file.name}",
                        file=sys.stderr,
                    )
                    sys.exit(1)
                seen_keys.add(key)
                entry = {col.strip(): row[col].strip() for col in output_fields}
                entries.append(entry)

    return entries


def validate_append_only(
    existing_keys: list[str], new_keys: list[str], name: str
) -> None:
    """Ensure `new_keys` is a superset of `existing_keys` with identical ordering prefix.

    Rules:
      - Every key in `existing_keys` must still be present in `new_keys`.
      - The first `len(existing_keys)` entries in `new_keys` must match exactly.
      - New keys may only appear after all existing keys.
    """
    missing = set(existing_keys) - set(new_keys)
    if missing:
        print(
            f"ERROR ({name}): the following keys were removed from the source CSV "
            f"but still exist in the JSON — removal is not allowed: {sorted(missing)}",
            file=sys.stderr,
        )
        sys.exit(1)

    prefix = new_keys[: len(existing_keys)]
    if prefix != existing_keys:
        print(
            f"ERROR ({name}): the order of existing keys in the source CSV has changed — "
            f"reordering is not allowed.  Expected the first {len(existing_keys)} keys "
            f"to match the current JSON.",
            file=sys.stderr,
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def generate_mapping(source_dir: Path, output_path: Path, schema_ref: str) -> None:
    name = source_dir.name

    entries = read_csv_entries(source_dir)
    if not entries:
        print(f"ERROR ({name}): source CSV files contain no entries", file=sys.stderr)
        sys.exit(1)

    keys = [e["key"] for e in entries]

    # Validate append-only against existing JSON
    existing = read_existing_json(output_path)
    if existing is not None:
        existing_keys = [entry["key"] for entry in existing["data"]]
        validate_append_only(existing_keys, keys, name)

    # Build data array: id + all CSV columns (except comment)
    new_data = [{"id": i, **entry} for i, entry in enumerate(entries)]

    # Idempotency check
    if existing is not None and existing.get("data") == new_data:
        print(f"{name}: no changes, skipping write")
        return

    obj = {
        "$schema": schema_ref,
        "lastUpdated": now_iso(),
        "data": new_data,
    }
    write_json(output_path, obj)
    print(f"{name}: wrote {len(new_data)} entries -> {output_path.name}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    for source_dir, output_path, schema_ref in MAPPINGS:
        generate_mapping(source_dir, output_path, schema_ref)


if __name__ == "__main__":
    main()
