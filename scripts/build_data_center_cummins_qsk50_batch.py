"""Build reviewed Cummins QSK50 Data Center Continuous configurations."""

from __future__ import annotations

import argparse
from pathlib import Path

from build_data_center_cummins_batch import build_record, compact

from energy_data_retrieval.data_center_catalogue.portfolios import (
    parse_cummins_generator_table,
)

RETRIEVED_AT = "2026-11-05T22:22:01Z"
AS_OF = "2026-11-05"
SOURCE_ID = "cummins-qsk50-dcc-current-20261105"
SOURCE_URL = (
    "https://www.cummins.com/en-na/generators/products/qsk50?application=Data%20Centers&v=3021"
)
EXPECTED_COUNT = 8


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    staged = parse_cummins_generator_table(
        args.capture.read_bytes(),
        source_url=SOURCE_URL,
        expected_count=EXPECTED_COUNT,
    )
    rows = [
        build_record(
            candidate,
            SOURCE_ID,
            SOURCE_URL,
            retrieved_at=RETRIEVED_AT,
            as_of=AS_OF,
        )
        for candidate in staged["candidates"]
    ]
    rows.sort(key=lambda row: (row["model"], row["frequency_hz"]))
    args.output.write_text("".join(f"{compact(row)}\n" for row in rows), encoding="utf-8")
    print(f"Wrote {len(rows)} reviewed Cummins QSK50 DCC configurations to {args.output}")


if __name__ == "__main__":
    main()
