"""Stage battery service observations from local NGCP 2026-19 extracted text."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_catalogue.ngcp import (
    SEPTEMBER_URL,
    SOURCE_URL,
    parse_ngcp_batteries,
)


def main() -> None:
    """Write review candidates only; never infer operating status or capacity."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--september-2026", action="store_true")
    args = parser.parse_args()
    rows = parse_ngcp_batteries(
        args.input.read_bytes(),
        source_url=SEPTEMBER_URL if args.september_2026 else SOURCE_URL,
    )
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
