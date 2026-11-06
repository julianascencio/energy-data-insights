"""Stage downloaded MaStR XML partitions for manual battery identity review."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_catalogue.mastr import stage_mastr_storage


def main() -> None:
    """Read local XML only; never download, import or merge automatically."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--units", type=Path, nargs="+", required=True)
    parser.add_argument("--storage", type=Path, nargs="+", required=True)
    parser.add_argument("--values", type=Path, required=True)
    parser.add_argument("--snapshot-date", required=True)
    parser.add_argument("--minimum-kw", type=float, default=1000)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = stage_mastr_storage(
        args.units,
        args.storage,
        args.values,
        snapshot_date=args.snapshot_date,
        minimum_kw=args.minimum_kw,
    )
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
