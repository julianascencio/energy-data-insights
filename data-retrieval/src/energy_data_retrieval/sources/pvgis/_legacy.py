"""PVGIS 5 documented endpoint parameters, with explicit physical input checks."""

from __future__ import annotations

import math
from typing import Any

from ._validation import validate

_COMMON = "lat lon usehorizon userhorizon raddatabase outputformat browser"
_GEOMETRY = "angle aspect"
_PV = "peakpower loss pvtechchoice mountingplace optimalinclination optimalangles"
_PARAMETERS = {
    "PVcalc": f"{_COMMON} {_GEOMETRY} {_PV} fixed inclined_axis inclined_optimum "
    "inclinedaxisangle vertical_axis vertical_optimum verticalaxisangle twoaxis "
    "pvprice systemcost interest lifetime",
    "SHScalc": f"{_COMMON} {_GEOMETRY} peakpower batterysize cutoff consumptionday hourconsumption",
    "MRcalc": f"{_COMMON} startyear endyear horirrad optrad selectrad angle mr_dni d2g avtemp",
    "DRcalc": f"{_COMMON} {_GEOMETRY} month global glob_2axis clearsky clearsky_2axis "
    "showtemperatures localtime",
    "seriescalc": f"{_COMMON} {_GEOMETRY} {_PV} startyear endyear "
    "pvcalculation trackingtype components",
    "tmy": "lat lon usehorizon userhorizon startyear endyear outputformat browser",
    "printhorizon": "lat lon userhorizon outputformat browser",
}
_FLAGS = set(
    [
        "usehorizon",
        "browser",
        "fixed",
        "optimalinclination",
        "optimalangles",
        "inclined_axis",
        "inclined_optimum",
        "vertical_axis",
        "vertical_optimum",
        "twoaxis",
        "pvprice",
        "horirrad",
        "optrad",
        "selectrad",
        "mr_dni",
        "d2g",
        "avtemp",
        "global",
        "glob_2axis",
        "clearsky",
        "clearsky_2axis",
        "showtemperatures",
        "localtime",
        "pvcalculation",
        "components",
    ]
)
_RANGES = {
    "lat": (-90, 90),
    "lon": (-180, 180),
    "angle": (0, 90),
    "aspect": (-180, 180),
    "inclinedaxisangle": (0, 90),
    "verticalaxisangle": (0, 90),
    "loss": (0, 100),
    "cutoff": (0, 100),
    "month": (0, 12),
    "trackingtype": (0, 5),
    "startyear": (1900, 2200),
    "endyear": (1900, 2200),
    "lifetime": (1, 200),
}
_REQUIRED = {
    "PVcalc": ["peakpower", "loss"],
    "SHScalc": ["peakpower", "batterysize", "cutoff", "consumptionday"],
    "DRcalc": ["month"],
}


def contract(endpoint: str) -> dict[str, Any]:
    if endpoint not in _PARAMETERS:
        raise ValueError(f"Unknown PVGIS 5 endpoint: {endpoint}")
    schemas = {}
    for name in _PARAMETERS[endpoint].split():
        schema: dict[str, Any] = {"type": "number"}
        if name in _FLAGS:
            schema = {"type": "integer", "enum": [0, 1]}
        elif name in {"startyear", "endyear", "lifetime", "month", "trackingtype"}:
            schema = {"type": "integer"}
        elif name in {"raddatabase", "pvtechchoice", "mountingplace", "outputformat"}:
            schema = {"type": "string"}
        elif name in {"userhorizon", "hourconsumption"}:
            schema = {
                "type": "array",
                "items": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 90 if name == "userhorizon" else 1,
                },
            }
            if name == "hourconsumption":
                schema.update(minItems=24, maxItems=24)
            else:
                schema.update(minItems=4)
        if name in _RANGES:
            schema.update(minimum=_RANGES[name][0], maximum=_RANGES[name][1])
        if name in {"peakpower", "batterysize", "consumptionday"}:
            schema["exclusiveMinimum"] = 0
        if name in {"systemcost", "interest"}:
            schema["minimum"] = 0
        if name == "outputformat":
            schema["enum"] = ["json", "csv", "basic"] + (["epw"] if endpoint == "tmy" else [])
        if name == "mountingplace":
            schema["enum"] = ["free", "building"]
        if name == "pvtechchoice":
            schema["enum"] = ["crystSi", "crystSi2025", "CIS", "CdTe", "Unknown"]
        schemas[name] = schema
    return {"parameters": schemas, "required": ["lat", "lon", *_REQUIRED.get(endpoint, [])]}


def prepare(endpoint: str, values: dict[str, Any]) -> dict[str, str]:
    definition = contract(endpoint)
    values = {k: v for k, v in values.items() if v is not None}
    values.setdefault("outputformat", "json")
    unknown = values.keys() - definition["parameters"].keys()
    if unknown:
        raise ValueError(f"Unsupported {endpoint} parameters: {sorted(unknown)}")
    required = set(definition["required"])
    if values.get("pvcalculation") == 1:
        required.update(["peakpower", "loss"])
    if values.get("pvprice") == 1:
        required.update(["systemcost", "interest"])
    missing = required - values.keys()
    if missing:
        raise ValueError(f"Missing {endpoint} parameters: {sorted(missing)}")
    for name, value in values.items():
        if name in _FLAGS and isinstance(value, bool):
            values[name] = value = int(value)
        if name in {"hourconsumption", "userhorizon"} and isinstance(value, str):
            try:
                values[name] = value = [float(item) for item in value.split(",")]
            except ValueError:
                raise ValueError(f"{name} must contain comma-separated numbers") from None
        validate(value, definition["parameters"][name], name)
    if "hourconsumption" in values and not math.isclose(
        sum(values["hourconsumption"]), 1, rel_tol=0, abs_tol=1e-6
    ):
        raise ValueError("hourconsumption must contain 24 fractions summing to 1")
    if "startyear" in values and "endyear" in values:
        if values["startyear"] > values["endyear"]:
            raise ValueError("startyear must not follow endyear")
        if endpoint == "tmy" and values["endyear"] - values["startyear"] + 1 < 10:
            raise ValueError("TMY requires at least ten source years")
    options = {
        "MRcalc": ("horirrad", "optrad", "selectrad", "mr_dni", "d2g", "avtemp"),
        "DRcalc": ("global", "glob_2axis", "clearsky", "clearsky_2axis", "showtemperatures"),
    }
    if endpoint in options and not any(values.get(k) == 1 for k in options[endpoint]):
        raise ValueError(f"Select at least one output for {endpoint}")
    return {
        k: ",".join(map(str, v)) if isinstance(v, (list, tuple)) else str(v)
        for k, v in values.items()
    }
