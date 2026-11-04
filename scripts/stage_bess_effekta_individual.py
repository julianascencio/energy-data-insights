"""Stage an exact EFFEKTA English datasheet; no download or automatic import."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.effekta_individual import (
    SOURCE_URLS,
    parse_individual_sheet,
)


def main() -> None:
    """Require a reviewed printed identity and archive URL."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--source-url", choices=sorted(SOURCE_URLS), required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    row = parse_individual_sheet(
        args.input.read_bytes(), source_url=args.source_url, expected_model=args.model
    )
    args.output.write_text(json.dumps(row, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
