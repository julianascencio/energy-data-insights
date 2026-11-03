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
    args = parser.parse_args()
    row = parse_rolls_agm_text(
        args.input.read_bytes(), source_url=args.url, expected_model=args.model
    )
    args.output.write_text(json.dumps(row, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
