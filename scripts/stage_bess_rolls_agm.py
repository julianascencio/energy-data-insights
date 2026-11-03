"""Stage one reviewed Rolls AGM-S reader-text table, without catalogue writes."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.rolls_agm import parse_rolls_agm_text


def main() -> None:
    """Write reviewable candidates from local, unnumbered extracted text."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--reviewed-r2", action="store_true", help="Explicitly reviewed R2 single-cell table"
    )
    args = parser.parse_args()
    row = parse_rolls_agm_text(
        args.input.read_bytes(),
        source_url=args.url,
        expected_model=args.model,
        reviewed_r2=args.reviewed_r2,
    )
    args.output.write_text(json.dumps(row, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
