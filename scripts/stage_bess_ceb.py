"""Stage the local CEB 26 May 2022 table for project/phase identity review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_catalogue.ceb import parse_ceb_battery_table


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = parse_ceb_battery_table(args.text.read_bytes())
    args.output.write_text("".join(json.dumps(r) + "\n" for r in rows))


if __name__ == "__main__":
    main()
