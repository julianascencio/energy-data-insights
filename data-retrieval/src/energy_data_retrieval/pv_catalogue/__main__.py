"""Offline CLI: python -m energy_data_retrieval.pv_catalogue."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .catalogue import (
    build_parquet,
    load_records,
    upsert_records,
    validate_catalogue,
    validate_record,
    write_records,
)
from .sam import parse_sam_csv, verify_sha256


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate", "build", "import-sam", "upsert"])
    parser.add_argument("--root", type=Path, default=Path("catalogues/pv"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--source-id")
    parser.add_argument("--entity-type", choices=["modules", "inverters"])
    parser.add_argument("--now", help="UTC ISO timestamp for an observed update")
    args = parser.parse_args()
    registry = json.loads((args.root / "sources.json").read_text())
    if args.command == "build":
        if args.output is None:
            parser.error("build requires --output (a new directory)")
        result = build_parquet(args.root, args.output)
        print(json.dumps({k: v["rows"] for k, v in result["tables"].items()}, indent=2))
    elif args.command in {"import-sam", "upsert"}:
        if args.input is None or args.now is None or args.output is None:
            parser.error("imports require --input, --now and --output for quarantine JSON")
        rejected = []
        if args.command == "import-sam":
            if not args.source_id or not args.entity_type:
                parser.error("import-sam requires --source-id and --entity-type")
            content = args.input.read_bytes()
            verify_sha256(content, registry[args.source_id]["sha256"])
            incoming, rejected = parse_sam_csv(
                content.decode("utf-8-sig"),
                entity_type=args.entity_type,
                source_id=args.source_id,
                retrieved_at=args.now,
            )
        else:
            incoming = [json.loads(line) for line in args.input.read_text().splitlines() if line]
        for row in incoming:
            validate_record(row, registry)
        records, conflicts = upsert_records(load_records(args.root), incoming, now=args.now)
        write_records(args.root, records)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps([*rejected, *conflicts], indent=2) + "\n")
        print(f"Processed {len(incoming)} records; quarantined {len(rejected) + len(conflicts)}")
    else:
        records = load_records(args.root)
        validate_catalogue(records, registry)
        print(f"Validated {len(records)} unique records; schema and field evidence present")


if __name__ == "__main__":
    main()
