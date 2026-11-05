"""Bounded ONS wind unit observations; no farm capacity or lifecycle inference."""

from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import math
import re
from collections import defaultdict
from datetime import date
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

REFERENCE_IDS = ("ons_wind_units", "wri_brazil_identity")
COLUMNS = (
    "id_subsistema",
    "nom_subsistema",
    "id_estado",
    "nom_estado",
    "nom_modalidadeoperacao",
    "nom_agenteproprietario",
    "nom_agenteoperador",
    "nom_tipousina",
    "nom_usina",
    "ceg",
    "nom_unidadegeradora",
    "cod_equipamento",
    "num_unidadegeradora",
    "nom_combustivel",
    "dat_entradateste",
    "dat_entradaoperacao",
    "dat_desativacao",
    "val_potenciaefetiva",
)


def wri_id(ceg: str) -> str:
    """Apply the documented WRI Brazil importer mapping, never a name-derived ID."""
    match = re.fullmatch(r"EOL\.[A-Z]{2}\.[A-Z]{2}\.(\d{6})-\d\.\d{2}", ceg)
    if not match or int(match[1]) == 0:
        raise ValueError("Invalid wind CEG")
    return f"BRA{int(match[1]):07d}"


def parse_partition(
    data: bytes, *, sha256: str, offset: int, limit: int, retrieved_at: str
) -> dict[str, Any]:
    """Parse one sorted full-CEG partition of a pinned daily CSV.

    A unit can represent multiple turbines. Nominal MW follows the dictionary,
    despite the legacy column name ``val_potenciaefetiva``. Retrieval time is not
    an observation date; release-for-operation dates are not farm commissioning.
    """
    if hashlib.sha256(data).hexdigest() != sha256:
        raise ValueError("ONS original checksum mismatch")
    if type(offset) is not int or type(limit) is not int or offset < 0 or limit < 1:
        raise ValueError("Invalid bounded ONS partition")
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")), delimiter=";")
    headers = reader.fieldnames or []
    if any(headers.count(k) != 1 for k in COLUMNS) or len(set(headers)) != len(headers):
        raise ValueError("Missing or duplicate ONS columns")
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for line, native in enumerate(reader, 2):
        if None in native or any(v is None for v in native.values()):
            raise ValueError("Malformed ONS CSV row")
        if native["nom_tipousina"].strip() != "EOLIELÉTRICA":
            continue
        raw = {k: v.strip() or None for k, v in native.items()}
        ceg = str(raw["ceg"] or "")
        wri_id(ceg)
        groups[ceg].append({"original": raw, "locator": f"CSV line {line}; CEG {ceg}"})
    identities: dict[str, list[str]] = defaultdict(list)
    for ceg in groups:
        identities[wri_id(ceg)].append(ceg)
    selected = []
    for ceg in sorted(groups)[offset : offset + limit]:
        units = groups[ceg]
        seen = set()
        for unit in units:
            raw = unit["original"]
            code = raw["cod_equipamento"]
            if not code or code in seen:
                raise ValueError("Duplicate or missing ONS unit code within CEG")
            seen.add(code)
            value = raw["val_potenciaefetiva"]
            mw = None if value is None else float(value)
            if mw is not None and (not math.isfinite(mw) or mw < 0):
                raise ValueError("Invalid ONS nominal MW")
            for field in ("dat_entradateste", "dat_entradaoperacao", "dat_desativacao"):
                if raw[field] is not None:
                    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw[field]):
                        raise ValueError("Invalid ONS date precision")
                    date.fromisoformat(raw[field])
            unit.update(
                equipment_code=code,
                reported_nominal_mw=mw,
                unit="MW",
                gross_net_boundary="unspecified",
                normalization="Decimal MW unchanged; nominal per ONS dictionary",
                turbine_count=None,
            )
        names = sorted({u["original"]["nom_usina"] for u in units if u["original"]["nom_usina"]})
        selected.append(
            dict(
                ceg=ceg,
                wri_gppd=wri_id(ceg),
                names=names,
                competing_cegs=sorted(identities[wri_id(ceg)]),
                source_sha256=sha256,
                retrieved_at=retrieved_at,
                observation_date=None,
                units=units,
                locator=f"CSV all rows for CEG {ceg}",
                inventory_completeness=(
                    "All rows for this CEG in this daily ONS file; turbine inventory unknown"
                ),
                boundary=(
                    "ONS dispatched units, operation modalities I/II-A/II-B/II-C; "
                    "not a national operating census"
                ),
            )
        )
    return dict(
        total_wind_rows=sum(map(len, groups.values())),
        total_cegs=len(groups),
        offset=offset,
        limit=limit,
        candidates=selected,
        next_cegs=sorted(groups)[offset + limit : offset + limit + 20],
    )


def reconcile(
    candidates: list[dict[str, Any]],
    existing: list[dict[str, Any]],
    *,
    source_id: str,
    identity_source_id: str,
    now: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Enrich unique registry-ID plus exact-name matches; preserve all scalar facts.

    New/ambiguous identities remain in the ledger. Case and surrounding whitespace
    are normalized, but accents, words and phase suffixes are not approximated.
    Replaying the same source is idempotent; changed source content is rejected.
    """
    by_wri: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if len({r["record_id"] for r in existing}) != len(existing):
        raise ValueError("Duplicate catalogue record ID")
    if len({c["ceg"] for c in candidates}) != len(candidates):
        raise ValueError("Duplicate candidate CEG")
    for record in existing:
        if record["entity_type"] == "projects" and record.get("country_code") == "BRA":
            by_wri[json.loads(record.get("external_ids_json") or "{}").get("wri_gppd")].append(
                record
            )
    enriched, ledger = [], []
    for item in candidates:
        matches = by_wri.get(item["wri_gppd"], [])
        reason = None
        if len(item["competing_cegs"]) != 1:
            reason = (
                "Multiple CEG versions map to this historical ID; phase/repowering review required"
            )
        elif len(matches) != 1:
            reason = "Missing or nonunique historical WRI identity; no new farm inferred"
        elif {n.strip().casefold() for n in item["names"]} != {
            matches[0]["name"].strip().casefold()
        }:
            reason = "Registry ID/name disagreement; no fuzzy-name acceptance"
        decision = dict(
            ceg=item["ceg"],
            wri_gppd=item["wri_gppd"],
            names=item["names"],
            locator=item["locator"],
            unit_rows=len(item["units"]),
            decision="deferred" if reason else "enriched",
            reason=reason,
        )
        ledger.append(decision)
        if reason:
            continue
        row = copy.deepcopy(matches[0])
        ids = json.loads(row["external_ids_json"])
        if ids.get("aneel_ceg", item["ceg"]) != item["ceg"]:
            raise ValueError("Conflicting existing CEG")
        ext = json.loads(row.get("extensions_json") or "{}")
        history = ext.setdefault("ons_wind_unit_snapshots", [])
        observation = {**copy.deepcopy(item), "source_id": source_id}
        prior = [o for o in history if o["source_id"] == source_id]
        decision["record_id"] = row["record_id"]
        if prior:
            if prior != [observation]:
                raise ValueError("Immutable ONS observation changed")
            enriched.append(row)
            continue
        if any(o.get("source_sha256") == item["source_sha256"] for o in history):
            raise ValueError("Overlapping ONS snapshot from another source")
        history.append(observation)
        ids["aneel_ceg"] = item["ceg"]
        fs, ev = json.loads(row["field_sources_json"]), json.loads(row["evidence_json"])
        for field, value in (("external_ids_json", ids), ("extensions_json", ext)):
            row[field] = canonical_json(value)
            fs[field] = sorted(set([*fs.get(field, []), source_id, identity_source_id]))
            ev[field] = dict(
                prior_observation=ev.get(field),
                source_id=source_id,
                locator=item["locator"] + "; embedded unit line locators",
                confidence="high",
                normalization="WRI encoded CEG numeric ID and exact name; dated unit scope only",
            )
        row.update(
            field_sources_json=canonical_json(fs),
            evidence_json=canonical_json(ev),
            sources=sorted(set([*row["sources"], source_id, identity_source_id])),
            updated_at=now,
            last_verified_at=now,
        )
        enriched.append(row)
    return sorted(enriched, key=lambda r: r["record_id"]), ledger
