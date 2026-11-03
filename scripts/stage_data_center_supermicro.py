"""Stage the current official Supermicro B200/B300 system table offline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.data_center_catalogue.inventories import (
    parse_supermicro_nvidia_systems,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_html", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--expected-count", type=int, required=True)
    args = parser.parse_args()
    staged = parse_supermicro_nvidia_systems(
        args.source_html.read_bytes(),
        source_url="https://www.supermicro.com/en/accelerators/nvidia-certified-systems",
        expected_count=args.expected_count,
    )
    args.output.write_text(json.dumps(staged, indent=2, sort_keys=True) + "\n")
    print(f"Staged {len(staged['candidates'])} Supermicro system candidates")


if __name__ == "__main__":
    main()
