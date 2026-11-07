"""Stage checksum-pinned NVE solar concession candidates for identity review."""

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit


@dataclass(frozen=True, slots=True)
class NveSolarCase:
    """One source observation, without personal details or geometries."""

    feature_number: int
    plant_number: int
    case_id: int
    name: str
    municipality: str
    county: str
    case_url: str
    stage: str
    status_code: str
    proposed_mw: float | None
    in_service_mw: float | None
    forecast_gwh: float | None
    stage_timestamp: str | None
    first_service_timestamp: str | None
    data_capture_timestamp: str | None
    review_flags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class NveSolarPartition:
    """Candidate page; a transfer limit marks the page as incomplete."""

    cases: tuple[NveSolarCase, ...]
    exceeded_transfer_limit: bool
    excluded_non_solar: int


def _identifier(value: object) -> int:
    if type(value) is not int or not 0 < value < 2**31:
        raise ValueError("NVE invalid native identifier")
    return value


def _label(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("NVE missing source label")
    return value.strip()


def _quantity(value: object) -> float | None:
    if value is None:
        return None
    if not isinstance(value, (float, int)) or isinstance(value, bool) or not 0 <= value < 1e6:
        raise ValueError("NVE invalid native quantity")
    return float(value)


def _timestamp(value: object) -> str | None:
    if value is None:
        return None
    if type(value) is not int or not 0 < value < 4_102_444_800_000:
        raise ValueError("NVE invalid epoch milliseconds")
    return datetime.fromtimestamp(value / 1000, tz=UTC).isoformat()


def _case_url(value: object, case_id: int) -> str:
    url = _label(value)
    parts = urlsplit(url)
    if (
        parts.scheme != "https"
        or parts.netloc != "www.nve.no"
        or parts.path != "/konsesjon/konsesjonssaker/konsesjonssak"
        or parse_qs(parts.query) != {"type": ["A-6"], "id": [str(case_id)]}
        or parts.fragment
    ):
        raise ValueError("NVE case URL does not match native case identifier")
    return url


def read_nve_solar_cases(path: Path, *, sha256: str) -> NveSolarPartition:
    """Read a pinned ArcGIS layer-2 response without inferring AC/DC or operation.

    Only the explicit Solkraftverk object type is staged. Repeated case/plant IDs
    remain visible as holds. The caller must check the catalogue and the exact
    phase/site scope before upserting. Native MW and GWh are not recast as AC,
    DC, measured generation, or a canonical lifecycle state.
    """
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != sha256:
        raise ValueError("NVE checksum mismatch")
    document = json.loads(data)
    if not isinstance(document, dict) or not isinstance(document.get("features"), list):
        raise ValueError("NVE expected ArcGIS feature collection")
    exceeded = document.get("exceededTransferLimit", False)
    if type(exceeded) is not bool:
        raise ValueError("NVE invalid transfer limit flag")

    entries: list[tuple[int, int, int, dict[str, Any]]] = []
    excluded = 0
    for number, feature in enumerate(document["features"], start=1):
        if not isinstance(feature, dict) or not isinstance(feature.get("attributes"), dict):
            raise ValueError("NVE malformed feature attributes")
        attrs = feature["attributes"]
        if _label(attrs.get("objekttype")) != "Solkraftverk":
            excluded += 1
            continue
        entries.append(
            (number, _identifier(attrs.get("anleggsnr")), _identifier(attrs.get("saksid")), attrs)
        )

    plants = Counter(plant for _, plant, _, _ in entries)
    cases = Counter(case for _, _, case, _ in entries)
    out = []
    for number, plant, case, attrs in entries:
        flags = []
        if plants[plant] != 1:
            flags.append("repeated_plant_number")
        if cases[case] != 1:
            flags.append("repeated_case_id")
        out.append(
            NveSolarCase(
                feature_number=number,
                plant_number=plant,
                case_id=case,
                name=_label(attrs.get("anleggnavn")),
                municipality=_label(attrs.get("kommune")),
                county=_label(attrs.get("fylkenavn")),
                case_url=_case_url(attrs.get("sakslenke"), case),
                stage=_label(attrs.get("stadium")),
                status_code=_label(attrs.get("status")),
                proposed_mw=_quantity(attrs.get("effekt_mw")),
                in_service_mw=_quantity(attrs.get("effekt_mw_idrift")),
                forecast_gwh=_quantity(attrs.get("forventetproduksjon_gwh")),
                stage_timestamp=_timestamp(attrs.get("stadiumdato")),
                first_service_timestamp=_timestamp(attrs.get("forsteidriftdato")),
                data_capture_timestamp=_timestamp(attrs.get("datafangstdato")),
                review_flags=tuple(flags),
            )
        )
    return NveSolarPartition(tuple(out), exceeded, excluded)
