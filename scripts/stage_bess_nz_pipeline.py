"""Stage historical EA battery candidates; reviewed upserts remain separate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_catalogue.nz_pipeline import (
    parse_nz_pipeline,
    parse_transpower_pipeline,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--format", choices=["ea-2024", "transpower-2026"], default="ea-2024")
    args = parser.parse_args()
    parse = parse_nz_pipeline if args.format == "ea-2024" else parse_transpower_pipeline
    rows = parse(args.csv.read_bytes())
    args.output.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows)
    )


if __name__ == "__main__":
    main()
