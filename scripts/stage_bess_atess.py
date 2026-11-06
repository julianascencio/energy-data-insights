"""Stage reviewed local ATESS pdftotext-layout tables without catalogue mutation."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.atess import (
    MODELS,
    parse_enerstack314_clusters,
    parse_table,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--family", required=True, choices=[*MODELS, "EnerStack314"])
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    text = args.input.read_text()
    rows = (
        parse_enerstack314_clusters(text)
        if args.family == "EnerStack314"
        else parse_table(text, family=args.family)
    )
    with args.output.open("x") as output:
        json.dump(rows, output, indent=2)
        output.write("\n")


if __name__ == "__main__":
    main()
