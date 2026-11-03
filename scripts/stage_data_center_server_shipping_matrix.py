#!/usr/bin/env python3
"""Stage an offline extracted server/accelerator shipping matrix."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.data_center_catalogue.inventories import (
    parse_server_accelerator_shipping_matrix,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--expected-count", required=True, type=int)
    args = parser.parse_args()
    result = parse_server_accelerator_shipping_matrix(
        args.path.read_bytes(),
        source_url=args.source_url,
        expected_count=args.expected_count,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
