"""Stage final Portuguese grant IDs from local layout text.

Rights and identities require review; no canonical writes.
"""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_catalogue.portugal_grants import (
    parse_2026_grants,
    parse_final_grants,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--final-2026", action="store_true", help="Reviewed 45-row C21-i18/2026 final table"
    )
    args = parser.parse_args()
    parse = parse_2026_grants if args.final_2026 else parse_final_grants
    rows = parse(args.input.read_bytes())
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
