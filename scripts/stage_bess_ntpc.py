"""Stage local NTPC Lot-1/2 IFB tables for manual site/package review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_catalogue.ntpc import parse_ntpc_ifb


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", type=Path)
    parser.add_argument("--lot", type=int, choices=(1, 2), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = parse_ntpc_ifb(args.text.read_bytes(), lot=args.lot)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


if __name__ == "__main__":
    main()
