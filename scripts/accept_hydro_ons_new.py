"""Replay explicit ONS new-plant acceptance with catalogue-wide identity checks."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.hydro_catalogue.ons_new import accept_new


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    count = accept_new(Path("catalogues/hydro"), json.loads(args.batch.read_text()), args.output)
    print(f"Accepted {count} new CEG identities")


if __name__ == "__main__":
    main()
