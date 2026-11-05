"""Offline validation and deterministic snapshot generation."""

import argparse
import json
from pathlib import Path

from . import build_parquet, load_records, validate_catalogue


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate", "build"])
    parser.add_argument("--root", type=Path, default=Path("catalogues/hydro"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "build":
        if args.output is None:
            parser.error("--output is required for build")
        print(json.dumps(build_parquet(args.root, args.output), indent=2))
    else:
        rows = load_records(args.root)
        validate_catalogue(
            rows,
            json.loads((args.root / "sources.json").read_text()),
        )
        print(f"Validated {len(rows)} hydropower records")


if __name__ == "__main__":
    main()
