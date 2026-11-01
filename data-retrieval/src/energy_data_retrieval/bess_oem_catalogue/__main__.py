"""Offline BESS OEM validation and Parquet export."""

import argparse
import json
from pathlib import Path

from .catalogue import build_parquet, load_records, validate_catalogue


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate", "build"])
    parser.add_argument("--root", type=Path, default=Path("catalogues/bess_oem"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "build":
        if args.output is None:
            parser.error("build requires --output (a new directory)")
        print(json.dumps(build_parquet(args.root, args.output)["tables"], indent=2))
    else:
        rows = load_records(args.root)
        validate_catalogue(rows, json.loads((args.root / "sources.json").read_text()))
        manufacturers = len({r["manufacturer"] for r in rows})
        print(
            f"Validated {len(rows)} BESS OEM configurations/families "
            f"from {manufacturers} manufacturers"
        )


if __name__ == "__main__":
    main()
