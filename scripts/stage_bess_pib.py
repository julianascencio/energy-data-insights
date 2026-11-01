"""Stage a downloaded PIB BESS table for manual identity and scope review."""

import argparse
from pathlib import Path

from energy_data_retrieval.bess_catalogue.pib import parse_pib_bess_html
from energy_data_retrieval.pv_catalogue.catalogue import canonical_json


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    rows = parse_pib_bess_html(args.input.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.writelines(canonical_json(row) + "\n" for row in rows)
    print(f"Staged {len(rows)} candidates; no canonical records imported")


if __name__ == "__main__":
    main()
