"""Stage local PGE notice 719197-2026 XML without fetching or importing identities."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_catalogue.ted_pge import parse_pge_notice


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xml", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = parse_pge_notice(args.xml.read_bytes())
    args.output.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


if __name__ == "__main__":
    main()
