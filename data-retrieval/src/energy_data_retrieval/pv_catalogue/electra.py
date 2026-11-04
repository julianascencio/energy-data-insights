"""Read a pinned, bounded Electra search export as candidates, never as projects.

The filtered CSV is only an index. INSTALACIONID is not established as a whole
plant identity; AUTOID is merely an export sequence. No capacity, lifecycle,
owner or technology is inferred from installation names.
"""

from __future__ import annotations

import csv
import io
import json
import re
from collections import Counter
from html.parser import HTMLParser
from typing import Any

from .odre import normal_name
from .sam import verify_sha256

COLUMNS = ["AUTOID", "INSTALACIONID", "REGIMEN", "INSTALACION", "AUTONOMIA"]
PREFIX = "ctl00_ContentPlaceHolder1_"


class _Scope(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.inputs: dict[str, list[str]] = {}
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if tag == "input" and data.get("id"):
            self.inputs.setdefault(str(data["id"]), []).append(data.get("value") or "")

    def handle_data(self, data: str) -> None:
        self.text.append(data)


def read_electra_csv(
    content: bytes,
    *,
    sha256: str,
    scope_page: bytes,
    scope_sha256: str,
    region: str,
    minimum_net_kw: int,
) -> list[dict[str, str]]:
    """Check both captures, echoed PV/region/filter, schema, count and identifiers.

    Reject an unfiltered or truncated export. The query's net-power threshold is
    retained only as selection provenance, never as a record's capacity value.
    Network access and canonical acceptance remain explicit separate operations.
    """
    verify_sha256(content, sha256)
    verify_sha256(scope_page, scope_sha256)
    if not region.strip() or type(minimum_net_kw) is not int or minimum_net_kw < 0:
        raise ValueError("Invalid bounded Electra scope")
    scope = _Scope()
    scope.feed(scope_page.decode("utf-8-sig"))
    expected = {
        "mChkDdlTipoTecnologia_mTxtCheckBoxListCombo": "Fotovoltaica",
        "mChkDdlAutonomia_mTxtCheckBoxListCombo": region,
        "mTxtPotenciaNetaMin": str(minimum_net_kw),
    }
    if any(scope.inputs.get(PREFIX + key) != [value] for key, value in expected.items()):
        raise ValueError("Electra echoed query scope differs; do not import")
    counts = re.findall(r"\d+\s*/\s*\d+\s*\((\d+)\)", " ".join(scope.text))
    if len(counts) != 1:
        raise ValueError("Electra result count missing or ambiguous")
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")), delimiter=";")
    if reader.fieldnames != COLUMNS:
        raise ValueError("Electra filtered-index schema changed; re-review")
    rows = list(reader)
    if len(rows) != int(counts[0]):
        raise ValueError("Electra CSV/result count mismatch")
    ids: set[str] = set()
    for index, row in enumerate(rows, start=1):
        identifier = row.get("INSTALACIONID", "")
        if (
            None in row
            or any(value is None for value in row.values())
            or row["AUTOID"] != str(index)
            or not re.fullmatch(r"[1-9]\d*", identifier)
            or identifier in ids
            or row["AUTONOMIA"] != region
            or row["REGIMEN"] not in {"ESPECIAL", "ORDINARIO"}
            or not row["INSTALACION"].strip()
        ):
            raise ValueError("Invalid, duplicate or out-of-scope Electra index row")
        ids.add(identifier)
    return rows


def screen_electra_candidates(
    rows: list[dict[str, str]], *, existing: list[dict[str, Any]]
) -> dict[str, list[str]]:
    """Return review reasons keyed by registry ID; never auto-merge names.

    All index rows require phase/privacy/freshness review. Exact normalized name
    equality only adds a conservative crosswalk flag, never proves identity.
    Return no installation names or holder/contact information in review output.
    """
    counts = Counter(normal_name(row["INSTALACION"]) for row in rows)
    names = {
        normal_name(name)
        for row in existing
        if row.get("country_code") == "ESP"
        for name in [row["name"], *row.get("aliases", [])]
    }
    registry_ids = {
        str(identifier)
        for row in existing
        if row.get("country_code") == "ESP"
        if (
            identifier := json.loads(row.get("external_ids_json", "{}")).get(
                "electra_installation_id"
            )
        )
        is not None
    }
    result = {}
    for row in rows:
        name = normal_name(row["INSTALACION"])
        reasons = ["index_only_requires_phase_privacy_freshness_and_power_evidence"]
        if counts[name] > 1:
            reasons.append("repeated_incoming_name_distinct_registry_ids")
        if name in names:
            reasons.append("existing_name_requires_reviewed_registry_crosswalk")
        if row["INSTALACIONID"] in registry_ids:
            reasons.append("existing_registry_id_requires_reviewed_phase_crosswalk")
        result[row["INSTALACIONID"]] = reasons
    return result
