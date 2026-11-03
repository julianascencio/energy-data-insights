"""Stage pinned Swiss PV discovery rows outside the accepted catalogue."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.pv_catalogue.swiss import stage_swiss_pv


def main() -> None:
    """Emit review-only metadata; no upsert or canonical identity assignment."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = stage_swiss_pv(args.input.read_bytes(), sha256=args.sha256)
    with args.output.open("x", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"Staged {len(rows)} review-only observations; zero accepted catalogue additions.")


if __name__ == "__main__":
    main()
