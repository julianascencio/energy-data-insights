"""Stage one reviewed exact LEOCH OPzV sheet from local layout text."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.leoch import parse_opzv


def main() -> None:
    """Write candidates only; manual identity and evidence review precedes upsert."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(
        json.dumps(parse_opzv(args.text.read_text(), args.model), indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
