"""Stage one downloaded Rolls flooded-battery page for human review."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.rolls import parse_rolls_flooded_html


def main() -> None:
    """Preserve exact model, source URL, revision and rate-dependent capacities."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    candidate = parse_rolls_flooded_html(
        args.input.read_bytes(), source_url=args.source_url, expected_model=args.model
    )
    args.output.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
