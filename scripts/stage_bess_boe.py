"""Stage BOE daily battery candidates from local original XML only."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_catalogue.boe import select_battery_notices

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path)
    p.add_argument("--date", required=True, help="Exact YYYYMMDD publication date")
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    a.output.write_text(
        json.dumps(
            select_battery_notices(a.input.read_bytes(), expected_date=a.date),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
