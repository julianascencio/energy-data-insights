"""Stage the CNE Chile Capacidad Instalada de Gx CSV for identity review.

The CSV mixes plant and unit observations. Preserve the source grain, and keep
net and gross MW separate. This reader never accepts a canonical identity.
"""

import csv
import hashlib
import io
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

HEADERS: tuple[str, ...] = (
    "sistema",
    "subsistema",
    "propietario",
    "razon_social",
    "rut",
    "central",
    "estado",
    "fecha_puesta_servicio_central",
    "anio_servicio_central",
    "region_nombre",
    "comuna_nombre",
    "cod_unidad",
    "tipo_unidad",
    "fecha_servicio_unidad",
    "unidades",
    "marca_modelo",
    "clasificacion",
    "tipo_de_energia",
    "potencia_bruta_mw",
    "potencia_neta_mw",
    "ley_ernc",
    "medio_generacion",
    "distribuidora",
    "punto_conexion",
    "combustible_1",
    "consumo_1",
    "unidad_1",
    "combustible_2",
    "consumo_2",
    "unidad_2",
    "combustible_3",
    "consumo_3",
    "unidad_3",
    "tipo_turbina_hidraulica",
    "gasto_m3_por_s",
    "caida_m",
    "coord_este_utm",
    "coord_norte_utm",
    "huso_utm",
    "tipo_final",
    "orden",
    "fecha_act",
)
SITE_FIELDS = ("sistema", "subsistema", "central", "region_nombre", "comuna_nombre")


@dataclass(frozen=True, slots=True)
class CnePvObservation:
    """Safe, source-qualified candidate without owner, tax or coordinate fields."""

    row_number: int
    site_key: tuple[str, ...]
    site_rows: int
    unit_label: str | None
    technology: str
    gross_mw: float | None
    net_mw: float | None
    native_status: str | None
    update_date: str
    reported_plant_service_date: str | None
    review_flags: tuple[str, ...]


def _mw(raw: str) -> float | None:
    if not raw:
        return None
    if not re.fullmatch(r"[0-9]+(?:,[0-9]+)?", raw):
        raise ValueError("CNE malformed MW value")
    value = float(raw.replace(",", "."))
    if not 0 <= value < 1e6:
        raise ValueError("CNE MW value outside allowed range")
    return value


def read_cne_csv(path: Path, *, sha256: str) -> list[CnePvObservation]:
    """Read an exact source revision, staging only explicit photovoltaic rows.

    The native final technology field distinguishes PV from generic solar or
    CSP. Conflicting classifications, repeated site keys and inconsistent
    capacity bases stay visible as review flags. No rows are aggregated.
    """
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != sha256:
        raise ValueError("CNE checksum mismatch")
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig"), newline=""), strict=True)
    if tuple(reader.fieldnames or ()) != HEADERS:
        raise ValueError("CNE CSV header drift")
    sites: Counter[tuple[str, ...]] = Counter()
    candidates = []
    for row_number, row in enumerate(reader, 2):
        if None in row or any(value is None for value in row.values()):
            raise ValueError("CNE CSV row width")
        site = tuple(row[key].strip() for key in SITE_FIELDS)
        sites[tuple(value.casefold() for value in site)] += 1
        if row["tipo_final"].strip().casefold() == "solar fotovoltaica":
            candidates.append((row_number, row, site))

    result = []
    for row_number, row, site in candidates:
        site_rows = sites[tuple(value.casefold() for value in site)]
        gross = _mw(row["potencia_bruta_mw"].strip())
        net = _mw(row["potencia_neta_mw"].strip())
        native_date = row["fecha_act"].strip()
        update_date = date.fromisoformat(native_date).isoformat()
        if update_date != native_date:
            raise ValueError("CNE noncanonical update date")
        service = row["fecha_puesta_servicio_central"].strip()
        service_date = (
            datetime.strptime(service, "%d/%m/%Y").date().isoformat() if service else None
        )
        flags = []
        if not all(site[i] for i in (0, 2, 3, 4)):
            flags.append("incomplete_site_key")
        if site_rows != 1:
            flags.append("multiple_native_rows_for_site")
        if row["tipo_de_energia"].strip().casefold() not in {"", "solar", "solar fotovoltaica"}:
            flags.append("conflicting_technology")
        fuels = {row[f"combustible_{i}"].strip().casefold() for i in range(1, 4)}
        if fuels - {"", "solar"}:
            flags.append("conflicting_fuel_label")
        if re.match(r"(?:pmgd\s+ter|pe)\s+", site[2], re.IGNORECASE):
            flags.append("potential_non_pv_plant_label")
        if gross is not None and net is not None and net > gross:
            flags.append("net_exceeds_gross")
        result.append(
            CnePvObservation(
                row_number=row_number,
                site_key=site,
                site_rows=site_rows,
                unit_label=row["cod_unidad"].strip() or None,
                technology=row["tipo_final"].strip(),
                gross_mw=gross,
                net_mw=net,
                native_status=row["estado"].strip() or None,
                update_date=update_date,
                reported_plant_service_date=service_date,
                review_flags=tuple(flags),
            )
        )
    return result
