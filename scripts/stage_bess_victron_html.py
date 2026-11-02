"""Stage a reviewed Victron HTML manual table for manual model and unit review."""

import argparse
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.victron_html import parse_victron_manual_html
from energy_data_retrieval.pv_catalogue.catalogue import canonical_json


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    rows = parse_victron_manual_html(args.input.read_bytes(), source_url=args.source_url)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.writelines(canonical_json(row) + "\n" for row in rows)
    print(f"Staged {len(rows)} model columns; manual review required, no import")


if __name__ == "__main__":
    main()
