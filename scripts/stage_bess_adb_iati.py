"""Stage ADB battery financing activities for manual physical-project review."""

import argparse
from pathlib import Path

from energy_data_retrieval.bess_catalogue.adb_iati import stage_adb_battery_activities
from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("input", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()
rows = stage_adb_battery_activities(args.input.read_bytes())
with args.output.open("x", encoding="utf-8") as stream:
    stream.writelines(canonical_json(row) + "\n" for row in rows)
print(f"Staged {len(rows)} financing activities; no canonical import")
