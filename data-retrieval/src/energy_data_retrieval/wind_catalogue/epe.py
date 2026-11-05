"""Checksum-pinned EPE-hosted SIGA observations, without lifecycle promotion."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from collections import defaultdict
from datetime import date
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

REFERENCE_IDS = (
    "epe_siga_bahia_20260113",
    "epe_siga_ceara_20260113",
    "epe_siga_rio_grande_do_norte_20260113",
    "wri_brazil_identity",
)
POWER_FIELDS = {
    "mdapotenciaoutorgadakw": "authorized_mw",
    "mdapotenciafiscalizadakw": "inspected_mw",
    "mdagarantiafisicakw": "physical_guarantee_mw",
}
DATE_FIELDS = (
    "datgeracaoconjuntodados",
    "datentradaoperacao",
    "datiniciovigencia",
    "datfimvigencia",
)


def ceg_key(value: str) -> tuple[str, int, int]:
    """Compare CEG suffix zero padding only; never collapse revisions or nuclei."""
    match = re.fullmatch(r"(EOL\.[A-Z]{2}\.[A-Z]{2}\.\d{6})-(\d)\.(\d{1,2})", value)
    if not match or int(match[1].rsplit(".", 1)[1]) == 0:
        raise ValueError("Invalid EPE wind CEG")
    return match[1], int(match[2]), int(match[3])


def parse_partition(
    pages: list[bytes],
    *,
    sha256: list[str],
    expected_ids: list[int],
    confirmed_ids: list[int],
    state: str,
    retrieved_at: str,
) -> list[dict[str, Any]]:
    """Validate complete ID-addressed pages and retain original SIGA quantities.

    The two independent ID queries must agree. The layer's dataset date is not
    retrieval time or an assertion of present operation. kW values are divided
    by 1000 separately; physical guarantee is not installed capacity. Coordinates
    returned by the service in EPSG:4326 are observations of unknown accuracy.
    """
    if (
        not pages
        or len(pages) != len(sha256)
        or not re.fullmatch(r"[A-Z]{2}", state)
        or not expected_ids
        or any(type(i) is not int for i in expected_ids + confirmed_ids)
        or len(set(expected_ids)) != len(expected_ids)
        or len(set(confirmed_ids)) != len(confirmed_ids)
        or set(expected_ids) != set(confirmed_ids)
    ):
        raise ValueError("Invalid or drifting EPE partition IDs")
    selected: list[dict[str, Any]] = []
    seen: set[int] = set()
    for data, digest in zip(pages, sha256, strict=True):
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError("EPE original checksum mismatch")
        doc = json.loads(data)
        if (
            "error" in doc
            or doc.get("exceededTransferLimit") is not False
            or doc.get("spatialReference", {}).get("wkid") != 4326
        ):
            raise ValueError("Incomplete EPE response or unexpected coordinate system")
        for feature in doc["features"]:
            raw = feature["attributes"]
            oid = raw["objectid"]
            if type(oid) is not int or oid in seen:
                raise ValueError("Duplicate or invalid EPE object ID")
            seen.add(oid)
            if raw["sigtipogeracao"] != "EOL" or raw["sigufprincipal"] != state:
                raise ValueError("EPE row outside selected partition")
            ceg = raw["codceg"]
            key = ceg_key(ceg)
            if key[0].split(".")[2] != state or not raw["nomempreendimento"]:
                raise ValueError("EPE identity/state disagreement")
            for field in DATE_FIELDS:
                value = raw[field]
                if value is not None:
                    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                        raise ValueError("Invalid EPE date precision")
                    date.fromisoformat(value)
            if raw["datgeracaoconjuntodados"] is None:
                raise ValueError("Missing EPE dataset date")
            normalized = {}
            for field, label in POWER_FIELDS.items():
                value = raw[field]
                if value is not None and (
                    type(value) not in (int, float) or not math.isfinite(value) or value < 0
                ):
                    raise ValueError("Invalid EPE kW quantity")
                normalized[label] = None if value is None else value / 1000
            geometry = feature.get("geometry")
            if geometry is not None:
                for field, bound in (("x", 180), ("y", 90)):
                    value = geometry[field]
                    if (
                        type(value) not in (int, float)
                        or not math.isfinite(value)
                        or abs(value) > bound
                    ):
                        raise ValueError("Invalid EPE coordinate")
            selected.append(
                dict(
                    ceg=ceg,
                    wri_gppd=f"BRA{int(key[0].rsplit('.', 1)[1]):07d}",
                    name=raw["nomempreendimento"],
                    object_id=oid,
                    original=copy.deepcopy(raw),
                    normalized_power=normalized,
                    normalization=(
                        "Original kW / 1000 to MW; separate reported categories; "
                        "gross/net unspecified"
                    ),
                    geometry=copy.deepcopy(geometry),
                    coordinate_reference="EPSG:4326 returned by service; native layer EPSG:4674",
                    positional_accuracy_m=None,
                    coordinate_semantics=(
                        "Registry point, not boundary or turbine location; "
                        "decimal precision is not accuracy"
                    ),
                    observation_date=raw["datgeracaoconjuntodados"],
                    retrieved_at=retrieved_at,
                    source_sha256=digest,
                    locator=f"Layer0 objectid={oid}; codceg={ceg}; original field names retained",
                    scope=(
                        "Dated SIGA registry observation; no current operating-census, "
                        "turbine completeness or aggregation eligibility inference"
                    ),
                )
            )
    if seen != set(expected_ids):
        raise ValueError("Missing or unexpected EPE partition rows")
    if len({c["observation_date"] for c in selected}) != 1:
        raise ValueError("Mixed EPE dataset dates")
    if len({c["ceg"] for c in selected}) != len(selected):
        raise ValueError("Duplicate EPE CEG")
    return sorted(selected, key=lambda c: c["ceg"])


def reconcile(
    candidates: list[dict[str, Any]],
    existing: list[dict[str, Any]],
    *,
    source_id: str,
    identity_source_id: str,
    now: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Attach unique WRI numeric-ID plus exact-name matches as dated observations.

    Neither name-only matches nor multiple CEG revisions are accepted. Existing
    CEGs are checked without changing their spelling. Replays are idempotent;
    changed observations under the same source ID are rejected.
    """
    if len({r["record_id"] for r in existing}) != len(existing):
        raise ValueError("Duplicate catalogue identity")
    if len({c["ceg"] for c in candidates}) != len(candidates):
        raise ValueError("Duplicate EPE candidate")
    by_wri: dict[str, list[dict[str, Any]]] = defaultdict(list)
    revisions: dict[str, list[str]] = defaultdict(list)
    for row in existing:
        if row["entity_type"] == "projects" and row.get("country_code") == "BRA":
            ids = json.loads(row.get("external_ids_json") or "{}")
            by_wri[ids.get("wri_gppd")].append(row)
    for item in candidates:
        revisions[item["wri_gppd"]].append(item["ceg"])
    enriched, ledger = [], []
    for item in candidates:
        matches = by_wri.get(item["wri_gppd"], [])
        reason = None
        if len(revisions[item["wri_gppd"]]) != 1:
            reason = "Multiple CEG versions; phase/repowering identity unresolved"
        elif len(matches) != 1:
            reason = "Missing or nonunique WRI identity; no new farm inferred"
        elif matches[0]["name"].strip().casefold() != item["name"].strip().casefold():
            reason = "Registry ID/name disagreement; no fuzzy match"
        elif (
            prior_ceg := json.loads(matches[0].get("external_ids_json") or "{}").get("aneel_ceg")
        ) and ceg_key(prior_ceg) != ceg_key(item["ceg"]):
            reason = "Existing CEG disagreement; no registry overwrite"
        elif any(
            ceg_key(observation["ceg"]) != ceg_key(item["ceg"])
            for observation in json.loads(matches[0].get("extensions_json") or "{}").get(
                "epe_siga_snapshots", []
            )
        ):
            reason = "Prior EPE CEG revision disagreement; phase/repowering crosswalk required"
        decision = dict(
            ceg=item["ceg"],
            wri_gppd=item["wri_gppd"],
            object_id=item["object_id"],
            name=item["name"],
            decision="deferred" if reason else "enriched",
            reason=reason,
        )
        ledger.append(decision)
        if reason:
            continue
        row = copy.deepcopy(matches[0])
        decision["record_id"] = row["record_id"]
        ext = json.loads(row.get("extensions_json") or "{}")
        history = ext.setdefault("epe_siga_snapshots", [])
        observation = {**copy.deepcopy(item), "source_id": source_id}
        previous = [o for o in history if o["source_id"] == source_id]
        if previous:
            if previous != [observation]:
                raise ValueError("Immutable EPE observation changed")
            enriched.append(row)
            continue
        if any(o["source_sha256"] == item["source_sha256"] for o in history):
            raise ValueError("Duplicate EPE snapshot under another source")
        history.append(observation)
        fs, ev = json.loads(row["field_sources_json"]), json.loads(row["evidence_json"])
        fs["extensions_json"] = sorted(
            set([*fs.get("extensions_json", []), source_id, identity_source_id])
        )
        ev["extensions_json"] = dict(
            prior_observation=ev.get("extensions_json"),
            source_id=source_id,
            locator=item["locator"],
            confidence="high",
            normalization=(
                "WRI numeric CEG identity plus exact name; "
                "original CEG suffix zero padding checked; scalars unchanged"
            ),
        )
        row.update(
            extensions_json=canonical_json(ext),
            field_sources_json=canonical_json(fs),
            evidence_json=canonical_json(ev),
            sources=sorted(set([*row["sources"], source_id, identity_source_id])),
            updated_at=now,
            last_verified_at=now,
        )
        enriched.append(row)
    return sorted(enriched, key=lambda r: r["record_id"]), ledger
