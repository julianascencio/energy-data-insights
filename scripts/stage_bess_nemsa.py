"""Stage one downloaded NEMSA application for manual identity and unit review."""

import argparse
from pathlib import Path

from energy_data_retrieval.bess_catalogue.nemsa import parse_nemsa_minigrid_html
from energy_data_retrieval.pv_catalogue.catalogue import canonical_json


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    row = parse_nemsa_minigrid_html(args.input.read_bytes(), source_url=args.source_url)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(canonical_json(row) + "\n")
    print("Staged one applicant declaration; manual review required, no import")


if __name__ == "__main__":
    main()
