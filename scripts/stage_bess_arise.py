"""Stage local ARISE screening text; no network calls or automatic identity import."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_catalogue.arise import parse_arise_screening


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", type=Path, help="Local pdftotext -layout output")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = parse_arise_screening(args.text.read_text())
    args.output.write_text("".join(json.dumps(r) + "\n" for r in rows))


if __name__ == "__main__":
    main()
