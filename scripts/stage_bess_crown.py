"""Stage the reviewed Crown PDF table from local pdftotext -layout output."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.crown import SOURCE_URL, parse_crown_table


def main() -> None:
    """Write review candidates without modifying a catalogue."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = parse_crown_table(args.input.read_bytes(), source_url=SOURCE_URL)
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
