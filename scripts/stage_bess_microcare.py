"""Stage reviewed Microcare manual text; original PDF and identity review required."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.microcare import parse_manual

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", type=Path)
    parser.add_argument("--series", choices=["1-5", "5-8", "10-15"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(
        json.dumps(parse_manual(args.text.read_text(), args.series), indent=2) + "\n"
    )
