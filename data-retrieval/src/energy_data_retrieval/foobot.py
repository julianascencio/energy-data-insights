"""Read published Foobot simulation outputs; never execute the JavaScript wrapper."""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.request import urlopen

import numpy as np

SOURCE_URL = "https://techblog.foobot.io/assets/timestral-counterfactual/data.js"
ARTICLE_URL = "https://techblog.foobot.io/ai/hvac/control/tsfm-counterfactual-thermal-dynamics.html"


@dataclass(frozen=True)
class ThermalPanel:
    """Published temperatures (degrees C) and minutes relative to baseline start.

    Dates are simulation dates, not observations. Time zone is not published;
    relative minutes deliberately avoid inventing UTC timestamps.
    """

    date: str
    test: str
    offset: int
    threshold: float
    minutes: tuple[float, ...]
    truth: tuple[float, ...]
    median: tuple[float, ...]
    lo: tuple[float, ...]
    hi: tuple[float, ...]
    setpoint: tuple[float, ...]
    command: tuple[float, ...]


def parse_foobot(text: str) -> tuple[ThermalPanel, ...]:
    """Validate the fixed assignment wrapper and decode JSON without eval.

    Reject duplicate panels, incomplete schedules, nonfinite or unordered data,
    and inconsistent T2 issue times/setpoints. No missing trajectories are filled.
    """
    prefix = "window.TIMESTRAL_EXPERIMENT = "
    if not text.startswith(prefix):
        raise ValueError("Unexpected Foobot data wrapper")
    try:
        records = json.loads(text[len(prefix) :].strip().removesuffix(";"))
        if not isinstance(records, list) or not records:
            raise ValueError("Expected nonempty morning records")
        panels = []
        seen = set()
        for day in records:
            if day["date"] in seen:
                raise ValueError("Duplicate morning")
            seen.add(day["date"])
            daily = []
            for p in day["panels"]:
                panel = ThermalPanel(
                    str(day["date"]),
                    str(p["test"]),
                    int(p["offset"]),
                    float(day["threshold"]),
                    *(
                        tuple(float(v) for v in p[k])
                        for k in ("x", "truth", "median", "lo", "hi", "setpoint", "cmd")
                    ),
                )
                arrays = np.asarray(
                    [
                        panel.minutes,
                        panel.truth,
                        panel.median,
                        panel.lo,
                        panel.hi,
                        panel.setpoint,
                        panel.command,
                    ]
                )
                if (
                    arrays.ndim != 2
                    or arrays.shape[1] < 2
                    or not np.isfinite(arrays).all()
                    or not np.isfinite(panel.threshold)
                    or not np.all(np.diff(arrays[0]) > 0)
                    or not np.all(arrays[3] <= arrays[2])
                    or not np.all(arrays[2] <= arrays[4])
                    or not np.isin(arrays[6], [0, 1]).all()
                ):
                    raise ValueError("Invalid thermal trajectory")
                if p["offset"] != panel.offset:
                    raise ValueError("Offset must be an integer")
                daily.append(panel)
            expected = {("T1", 0), *(("T2", n) for n in (-60, -30, 0, 30, 60))}
            if len(daily) != 6 or {(p.test, p.offset) for p in daily} != expected:
                raise ValueError("Each morning requires T1 and five paired T2 schedules")
            t2 = [p for p in daily if p.test == "T2"]
            if any(p.minutes != t2[0].minutes or p.setpoint != t2[0].setpoint for p in t2):
                raise ValueError("T2 schedules need identical issue grid and setpoints")
            panels.extend(daily)
        return tuple(panels)
    except (KeyError, TypeError, OverflowError) as exc:
        raise ValueError("Malformed Foobot experiment") from exc


def fetch_foobot() -> str:
    """Fetch the public numerical asset with a timeout and 5 MB size bound.

    The returned source text is intended for local audit, not redistribution of
    the publisher's scripts or artwork. Public access does not imply a licence.
    """
    with urlopen(SOURCE_URL, timeout=30) as response:
        payload = response.read(5_000_001)
    if len(payload) > 5_000_000:
        raise ValueError("Foobot asset exceeds size limit")
    text = payload.decode("utf-8")
    parse_foobot(text)
    return text
