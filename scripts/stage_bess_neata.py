"""Stage an already-downloaded Neata table; never fetch or import records."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.neata import parse_neata_html

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path)
    p.add_argument("--series", choices=["lfp48", "ess"], required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.write_text(
        json.dumps(
            parse_neata_html(a.input.read_bytes(), series=a.series), ensure_ascii=False, indent=2
        )
        + "\n"
    )
