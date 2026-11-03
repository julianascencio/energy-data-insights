"""Build reviewed Huawei NetCol8000 and Delta precision-cooling records."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.inventories import (
    parse_precision_cooling_matrix,
)

RETRIEVED_AT = "2026-11-03T18:26:00Z"
AS_OF = "2026-11-03"

HUAWEI_A_URL = "https://info.support.huawei.com/Energy/info/en_US/dataCenter/docView/EDOC1100090384"
HUAWEI_C_URL = "https://info.support.huawei.com/Energy/info/en_US/dataCenter/docView/EDOC1100129236"
DELTA_ROW_URL = (
    "https://www.deltapowersolutions.com/en/mcis/data-center-rowcool-cw-cooling-specifications.php"
)
DELTA_80_URL = (
    "https://www.deltapowersolutions.com/en/mcis/"
    "liquid-to-air-coolant-distribution-unit-80kw-specifications.php"
)
DELTA_260_URL = (
    "https://www.deltapowersolutions.com/en/mcis/"
    "liquid-to-air-coolant-distribution-unit-260kw-specifications.php"
)
DELTA_3000_URL = (
    "https://www.deltapowersolutions.com/en/mcis/"
    "liquid-to-liquid-coolant-distribution-unit-3000kw--specifications.php"
)
DELTA_RACK_URL = (
    "https://www.delta-emea.com/en-GB/landing/Power-and-Cooling-Solutions-for-Data-Center"
)

SOURCES: dict[str, dict[str, str | None]] = {
    "huawei-netcol8000-a-issue17-20260730": {
        "url": HUAWEI_A_URL,
        "publication_date": "2026-07-30",
    },
    "huawei-netcol8000-c-issue16-20260920": {
        "url": HUAWEI_C_URL,
        "publication_date": "2026-09-20",
    },
    "delta-rowcool-cw-current-20261103": {"url": DELTA_ROW_URL, "publication_date": None},
    "delta-gocool-80-current-20261103": {"url": DELTA_80_URL, "publication_date": None},
    "delta-gocool-260-current-20261103": {"url": DELTA_260_URL, "publication_date": None},
    "delta-gocool-3000-current-20261103": {
        "url": DELTA_3000_URL,
        "publication_date": None,
    },
    "delta-inrack-l2l-current-20261103": {"url": DELTA_RACK_URL, "publication_date": None},
}

HUAWEI_A_CONDITIONS = (
    "Total and sensible capacity; 35 degC indoor dry bulb, 26% RH; 35 degC outdoor"
)
HUAWEI_C_CONDITIONS = (
    "7/12 degC inlet/outlet water; 24/17 degC return-air dry/wet bulb; 0 Pa static pressure"
)
DELTA_ROW_CONDITIONS = (
    "Total capacity at 40.6 degC dry bulb, 21.6 degC wet bulb, 17.8% RH and 7 degC inlet water"
)
DELTA_3000_CONDITIONS = (
    "4 degC approach; 3000 L/min primary and secondary flow; 1.5 L/min/kW; "
    "primary inlet 17 degC; primary water, secondary 25% PG"
)


def row(**values: Any) -> dict[str, Any]:
    return values


ROWS: tuple[dict[str, Any], ...] = (
    # Huawei Issue 17, tables 3-1 through 3-3. Current is the cooling-only
    # active-route maximum; optional heat/humidifier currents remain observations.
    row(
        source="huawei-netcol8000-a-issue17-20260730",
        manufacturer="Huawei Digital Power",
        model="NetCol8000-A045D",
        variant="downflow; air cooled",
        category="crac",
        cooling_capacity_kw=45,
        cooling_rating_conditions=HUAWEI_A_CONDITIONS,
        airflow_m3_h=11250,
        input_current_a=36,
        width_mm=900,
        height_mm=2000,
        depth_mm=1000,
        weight_kg=337,
        form_factor="floor-standing downflow air-cooled precision cooling unit",
        locator="Issue 17, table 3-1, NetCol8000-A045D",
        extras=[
            ("maximum_current_with_heat_humidifier", 40, "A"),
            ("fans", 1, None),
            ("optional_reheat", 6, "kW"),
            ("optional_humidification", 4.5, "kg/h"),
        ],
    ),
    row(
        source="huawei-netcol8000-a-issue17-20260730",
        manufacturer="Huawei Digital Power",
        model="NetCol8000-A045U",
        variant="upflow; air cooled",
        category="crac",
        cooling_capacity_kw=45,
        cooling_rating_conditions=HUAWEI_A_CONDITIONS,
        airflow_m3_h=11250,
        input_current_a=36,
        width_mm=900,
        height_mm=2000,
        depth_mm=1000,
        weight_kg=334.5,
        form_factor="floor-standing upflow air-cooled precision cooling unit",
        locator="Issue 17, table 3-1, NetCol8000-A045U",
        extras=[
            ("maximum_current_with_heat_humidifier", 40, "A"),
            ("fans", 1, None),
            ("optional_reheat", 6, "kW"),
            ("optional_humidification", 4.5, "kg/h"),
        ],
    ),
    row(
        source="huawei-netcol8000-a-issue17-20260730",
        manufacturer="Huawei Digital Power",
        model="NetCol8000-A090D",
        variant="downflow; air cooled",
        category="crac",
        cooling_capacity_kw=90,
        cooling_rating_conditions=HUAWEI_A_CONDITIONS,
        airflow_m3_h=22500,
        input_current_a=72,
        width_mm=1800,
        height_mm=2000,
        depth_mm=1000,
        weight_kg=643,
        form_factor="floor-standing downflow air-cooled precision cooling unit",
        locator="Issue 17, table 3-1, NetCol8000-A090D",
        extras=[
            ("maximum_current_with_heat_humidifier", 80, "A"),
            ("fans", 2, None),
            ("optional_reheat", 12, "kW"),
            ("optional_humidification", 10, "kg/h"),
        ],
    ),
    row(
        source="huawei-netcol8000-a-issue17-20260730",
        manufacturer="Huawei Digital Power",
        model="NetCol8000-A055D",
        variant="downflow; air cooled",
        category="crac",
        cooling_capacity_kw=55,
        cooling_rating_conditions=HUAWEI_A_CONDITIONS,
        airflow_m3_h=13000,
        input_current_a=41,
        width_mm=900,
        height_mm=2000,
        depth_mm=1000,
        weight_kg=354,
        form_factor="floor-standing downflow air-cooled precision cooling unit",
        locator="Issue 17, table 3-2, NetCol8000-A055D",
        extras=[
            ("maximum_current_with_heat_humidifier", 45, "A"),
            ("fans", 1, None),
            ("optional_reheat", 6, "kW"),
            ("optional_humidification", 6, "kg/h"),
        ],
    ),
    row(
        source="huawei-netcol8000-a-issue17-20260730",
        manufacturer="Huawei Digital Power",
        model="NetCol8000-A060D",
        variant="downflow; air cooled",
        category="crac",
        cooling_capacity_kw=60,
        cooling_rating_conditions=HUAWEI_A_CONDITIONS,
        airflow_m3_h=15000,
        input_current_a=41,
        width_mm=1100,
        height_mm=2000,
        depth_mm=1000,
        weight_kg=400,
        form_factor="floor-standing downflow air-cooled precision cooling unit",
        locator="Issue 17, table 3-3, NetCol8000-A060D",
        extras=[
            ("maximum_current_with_heat_humidifier", 45, "A"),
            ("fans", 1, None),
            ("optional_reheat", 6, "kW"),
            ("optional_humidification", 6, "kg/h"),
        ],
    ),
    row(
        source="huawei-netcol8000-a-issue17-20260730",
        manufacturer="Huawei Digital Power",
        model="NetCol8000-A060U",
        variant="upflow; air cooled",
        category="crac",
        cooling_capacity_kw=60,
        cooling_rating_conditions=HUAWEI_A_CONDITIONS,
        airflow_m3_h=14500,
        input_current_a=41,
        width_mm=1100,
        height_mm=2000,
        depth_mm=1000,
        weight_kg=416,
        form_factor="floor-standing upflow air-cooled precision cooling unit",
        locator="Issue 17, table 3-3, NetCol8000-A060U",
        extras=[
            ("maximum_current_with_heat_humidifier", 45, "A"),
            ("fans", 1, None),
            ("optional_reheat", 6, "kW"),
            ("optional_humidification", 6, "kg/h"),
        ],
    ),
    row(
        source="huawei-netcol8000-a-issue17-20260730",
        manufacturer="Huawei Digital Power",
        model="NetCol8000-A120D",
        variant="downflow; air cooled",
        category="crac",
        cooling_capacity_kw=120,
        cooling_rating_conditions=HUAWEI_A_CONDITIONS,
        airflow_m3_h=30000,
        input_current_a=82,
        width_mm=2200,
        height_mm=2000,
        depth_mm=1000,
        weight_kg=764,
        form_factor="floor-standing downflow air-cooled precision cooling unit",
        locator="Issue 17, table 3-3, NetCol8000-A120D",
        extras=[
            ("maximum_current_with_heat_humidifier", 90, "A"),
            ("fans", 2, None),
            ("optional_reheat", 12, "kW"),
            ("optional_humidification", 10, "kg/h"),
        ],
    ),
    # Huawei Issue 16, tables 2-1 and 2-2. Cooling-only current and weight are
    # normalized; full-configuration values are preserved separately.
    row(
        source="huawei-netcol8000-c-issue16-20260920",
        manufacturer="Huawei Digital Power",
        model="NetCol8000-C070D",
        variant="downflow; chilled water",
        category="crah",
        cooling_capacity_kw=60.1,
        cooling_rating_conditions=HUAWEI_C_CONDITIONS,
        airflow_m3_h=13200,
        input_current_a=7.3,
        width_mm=900,
        height_mm=2000,
        depth_mm=1000,
        weight_kg=300,
        form_factor="floor-standing downflow chilled-water air handler",
        locator="Issue 16, table 2-1, NetCol8000-C070D",
        extras=[
            ("maximum_current_full_configuration", 16.5, "A"),
            ("weight_full_configuration", 316, "kg"),
            ("fans", 1, None),
        ],
    ),
    row(
        source="huawei-netcol8000-c-issue16-20260920",
        manufacturer="Huawei Digital Power",
        model="NetCol8000-C130D",
        variant="downflow; chilled water",
        category="crah",
        cooling_capacity_kw=118.8,
        cooling_rating_conditions=HUAWEI_C_CONDITIONS,
        airflow_m3_h=24000,
        input_current_a=14,
        width_mm=1800,
        height_mm=2000,
        depth_mm=1000,
        weight_kg=500,
        form_factor="floor-standing downflow chilled-water air handler",
        locator="Issue 16, table 2-1, NetCol8000-C130D",
        extras=[
            ("maximum_current_full_configuration", 32.3, "A"),
            ("weight_full_configuration", 528, "kg"),
            ("fans", 2, None),
        ],
    ),
    row(
        source="huawei-netcol8000-c-issue16-20260920",
        manufacturer="Huawei Digital Power",
        model="NetCol8000-C190D",
        variant="downflow; chilled water",
        category="crah",
        cooling_capacity_kw=182.9,
        cooling_rating_conditions=HUAWEI_C_CONDITIONS,
        airflow_m3_h=36500,
        input_current_a=20.7,
        width_mm=2700,
        height_mm=2000,
        depth_mm=1000,
        weight_kg=690,
        form_factor="floor-standing downflow chilled-water air handler",
        locator="Issue 16, table 2-1, NetCol8000-C190D",
        extras=[
            ("maximum_current_full_configuration", 39, "A"),
            ("weight_full_configuration", 718, "kg"),
            ("fans", 3, None),
        ],
    ),
    row(
        source="huawei-netcol8000-c-issue16-20260920",
        manufacturer="Huawei Digital Power",
        model="NetCol8000-C070U",
        variant="upflow; chilled water",
        category="crah",
        cooling_capacity_kw=58.8,
        cooling_rating_conditions=HUAWEI_C_CONDITIONS,
        airflow_m3_h=12800,
        input_current_a=7.3,
        width_mm=900,
        height_mm=2000,
        depth_mm=1000,
        weight_kg=310,
        form_factor="floor-standing upflow chilled-water air handler",
        locator="Issue 16, table 2-2, NetCol8000-C070U",
        extras=[
            ("maximum_current_full_configuration", 16.5, "A"),
            ("weight_full_configuration", 326, "kg"),
            ("fans", 1, None),
        ],
    ),
    row(
        source="huawei-netcol8000-c-issue16-20260920",
        manufacturer="Huawei Digital Power",
        model="NetCol8000-C130U",
        variant="upflow; chilled water",
        category="crah",
        cooling_capacity_kw=117.7,
        cooling_rating_conditions=HUAWEI_C_CONDITIONS,
        airflow_m3_h=23500,
        input_current_a=14,
        width_mm=1800,
        height_mm=2000,
        depth_mm=1000,
        weight_kg=580,
        form_factor="floor-standing upflow chilled-water air handler",
        locator="Issue 16, table 2-2, NetCol8000-C130U",
        extras=[
            ("maximum_current_full_configuration", 32.3, "A"),
            ("weight_full_configuration", 608, "kg"),
            ("fans", 2, None),
        ],
    ),
    row(
        source="huawei-netcol8000-c-issue16-20260920",
        manufacturer="Huawei Digital Power",
        model="NetCol8000-C190U",
        variant="upflow; chilled water",
        category="crah",
        cooling_capacity_kw=175.7,
        cooling_rating_conditions=HUAWEI_C_CONDITIONS,
        airflow_m3_h=35400,
        input_current_a=20.7,
        width_mm=2700,
        height_mm=2000,
        depth_mm=1000,
        weight_kg=810,
        form_factor="floor-standing upflow chilled-water air handler",
        locator="Issue 16, table 2-2, NetCol8000-C190U",
        extras=[
            ("maximum_current_full_configuration", 39, "A"),
            ("weight_full_configuration", 838, "kg"),
            ("fans", 3, None),
        ],
    ),
    # Delta RowCool CW: condition (1) total capacity is normalized. Maximum and
    # high-temperature-water points remain separate observations.
    row(
        source="delta-rowcool-cw-current-20261103",
        manufacturer="Delta Electronics",
        model="CW-29",
        variant="RowCool chilled water",
        category="crah",
        cooling_capacity_kw=30.8,
        cooling_rating_conditions=DELTA_ROW_CONDITIONS,
        input_power_kw=1,
        width_mm=300,
        height_mm=2000,
        depth_mm=1090,
        weight_kg=185,
        form_factor="floor-standing in-row chilled-water cooling unit",
        locator="Technical Specifications, CW-29 column",
        extras=[
            ("sensible_cooling_capacity", 30.2, "kW"),
            ("maximum_total_capacity", 37.1, "kW"),
            ("high_temperature_water_capacity", 28.8, "kW"),
            ("chilled_water_flow", 68.3, "L/min"),
            ("airflow", 2902, "CFM"),
        ],
    ),
    row(
        source="delta-rowcool-cw-current-20261103",
        manufacturer="Delta Electronics",
        model="CW-43",
        variant="RowCool chilled water",
        category="crah",
        cooling_capacity_kw=43.4,
        cooling_rating_conditions=DELTA_ROW_CONDITIONS,
        input_power_kw=2.4,
        width_mm=300,
        height_mm=2000,
        depth_mm=1090,
        weight_kg=187,
        form_factor="floor-standing in-row chilled-water cooling unit",
        locator="Technical Specifications, CW-43 column",
        extras=[
            ("sensible_cooling_capacity", 43, "kW"),
            ("maximum_total_capacity", 50.4, "kW"),
            ("high_temperature_water_capacity", 36, "kW"),
            ("chilled_water_flow", 80, "L/min"),
            ("airflow", 4415, "CFM"),
        ],
    ),
    row(
        source="delta-rowcool-cw-current-20261103",
        manufacturer="Delta Electronics",
        model="CW-70",
        variant="RowCool chilled water; cooling-only base",
        category="crah",
        cooling_capacity_kw=69.3,
        cooling_rating_conditions=DELTA_ROW_CONDITIONS,
        input_power_kw=3,
        width_mm=600,
        height_mm=2000,
        depth_mm=1090,
        weight_kg=368,
        form_factor="floor-standing in-row chilled-water cooling unit",
        locator="Technical Specifications, CW-70 column",
        extras=[
            ("sensible_cooling_capacity", 69.3, "kW"),
            ("maximum_total_capacity", 83.1, "kW"),
            ("high_temperature_water_capacity", 57.4, "kW"),
            ("chilled_water_flow", 111.2, "L/min"),
            ("airflow", 6700, "CFM"),
            ("maximum_power_with_heater_humidifier", 10.8, "kW"),
            ("weight_with_heater_humidifier", 375, "kg"),
        ],
    ),
    row(
        source="delta-rowcool-cw-current-20261103",
        manufacturer="Delta Electronics",
        model="CW-95",
        variant="RowCool chilled water; cooling-only base",
        category="crah",
        cooling_capacity_kw=92.6,
        cooling_rating_conditions=DELTA_ROW_CONDITIONS,
        input_power_kw=4.8,
        width_mm=600,
        height_mm=2000,
        depth_mm=1090,
        weight_kg=415,
        form_factor="floor-standing in-row chilled-water cooling unit",
        locator="Technical Specifications, CW-95 column",
        extras=[
            ("sensible_cooling_capacity", 91.6, "kW"),
            ("maximum_total_capacity", 110.7, "kW"),
            ("high_temperature_water_capacity", 79.4, "kW"),
            ("chilled_water_flow", 120, "L/min"),
            ("airflow", 8200, "CFM"),
            ("maximum_power_with_heater_humidifier", 12.9, "kW"),
            ("weight_with_heater_humidifier", 422, "kg"),
        ],
    ),
    row(
        source="delta-gocool-80-current-20261103",
        manufacturer="Delta Electronics",
        model="GoCool-80",
        variant="liquid-to-air CDU",
        category="cdu",
        cooling_capacity_kw=80,
        cooling_rating_conditions="35 degC ambient, 45 degC coolant supply, 10 degC approach",
        input_power_kw=9.6,
        liquid_flow_l_min=120,
        width_mm=600,
        height_mm=2286,
        depth_mm=1068,
        weight_kg=625,
        form_factor="floor-standing liquid-to-air CDU",
        locator="Technical Specifications, GoCool-80",
        extras=[
            ("airflow", 10858, "CFM"),
            ("coolant_supply_pressure", 30, "psi"),
            ("protocol", "Modbus RTU", None),
        ],
    ),
    row(
        source="delta-gocool-260-current-20261103",
        manufacturer="Delta Electronics",
        model="GoCool-260",
        variant="liquid-to-air CDU",
        category="cdu",
        cooling_capacity_kw=260,
        cooling_rating_conditions="35 degC ambient, 45 degC coolant supply, 10 degC approach",
        input_power_kw=28.7,
        liquid_flow_l_min=286,
        width_mm=1200,
        height_mm=2331,
        depth_mm=1352,
        weight_kg=1320,
        form_factor="floor-standing liquid-to-air CDU",
        locator="Technical Specifications, GoCool-260",
        extras=[
            ("airflow", 25076, "CFM"),
            ("coolant_supply_pressure", 22.5, "psi"),
            ("protocol", "Modbus RTU", None),
        ],
    ),
    row(
        source="delta-gocool-3000-current-20261103",
        manufacturer="Delta Electronics",
        model="GoCool-3000",
        variant="liquid-to-liquid CDU; 4 degC approach point",
        category="cdu",
        cooling_capacity_kw=2000,
        cooling_rating_conditions=DELTA_3000_CONDITIONS,
        liquid_flow_l_min=3000,
        width_mm=1200,
        height_mm=2300,
        depth_mm=1500,
        weight_kg=2222,
        form_factor="floor-standing liquid-to-liquid CDU",
        locator="Technical Specifications, GoCool-3000, 4 degC approach row",
        extras=[
            ("cooling_capacity_5c_approach", 2500, "kW"),
            ("cooling_capacity_6c_approach", 3000, "kW"),
            ("weight_with_coolant", 2800, "kg"),
            ("protocols", ["SNMP", "Modbus RTU", "Modbus TCP/IP", "BACnet"], None),
        ],
    ),
    row(
        source="delta-inrack-l2l-current-20261103",
        manufacturer="Delta Electronics",
        model="19-inch 4U L2L 140kW CDU",
        variant="19-inch; 4U; liquid-to-liquid",
        category="cdu",
        cooling_capacity_kw=140,
        cooling_rating_conditions="4 degC approach; facility chilled water",
        form_factor="19-inch 4U in-rack liquid-to-liquid CDU",
        locator="In-Rack Solutions card, 19-inch 4U L2L 140kW CDU",
        extras=[
            ("pump_redundancy", "redundant", None),
            ("psu_redundancy", "redundant", None),
            ("remote_monitoring", "RJ45", None),
        ],
    ),
    row(
        source="delta-inrack-l2l-current-20261103",
        manufacturer="Delta Electronics",
        model="19-inch 6U L2L 250kW CDU",
        variant="19-inch; 6U; liquid-to-liquid",
        category="cdu",
        cooling_capacity_kw=250,
        cooling_rating_conditions="4 degC approach; facility chilled water",
        form_factor="19-inch 6U in-rack liquid-to-liquid CDU",
        locator="In-Rack Solutions card, 19-inch 6U L2L 250kW CDU",
        extras=[
            ("pump_redundancy", "redundant", None),
            ("psu_redundancy", "redundant", None),
            ("remote_monitoring", "RJ45", None),
        ],
    ),
    row(
        source="delta-inrack-l2l-current-20261103",
        manufacturer="Delta Electronics",
        model="21-inch 4U L2L 140kW CDU",
        variant="21-inch; 4U; liquid-to-liquid",
        category="cdu",
        cooling_capacity_kw=140,
        cooling_rating_conditions="4 degC approach; facility chilled water",
        form_factor="21-inch 4U in-rack liquid-to-liquid CDU",
        locator="OCP Rack card, 21-inch 4U L2L 140kW CDU",
        extras=[
            ("pump_redundancy", "redundant", None),
            ("psu_redundancy", "redundant", None),
            ("remote_monitoring", "RJ45", None),
        ],
    ),
)

CSV_FIELDS = [
    "manufacturer",
    "model",
    "variant",
    "category",
    "cooling_capacity_kw",
    "cooling_rating_conditions",
    "airflow_m3_h",
    "input_power_kw",
    "input_current_a",
    "liquid_flow_l_min",
    "width_mm",
    "height_mm",
    "depth_mm",
    "weight_kg",
    "locator",
]


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def extracted_csv(rows: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for item in rows:
        writer.writerow({field: item.get(field, "") for field in CSV_FIELDS})
    return stream.getvalue().encode()


def observation(
    item: dict[str, Any], field: str, value: object, unit: str | None
) -> dict[str, object]:
    return {
        "as_of": AS_OF,
        "boundary": f"Exact {item['model']} {item['variant']} configuration",
        "field": field,
        "kind": "reported",
        "locator": item["locator"],
        "source_id": item["source"],
        "unit": unit,
        "value": value,
    }


def build_record(item: dict[str, Any]) -> dict[str, object]:
    source_id = item["source"]
    source = SOURCES[source_id]
    normalized = [
        "airflow_m3_h",
        "cooling_capacity_kw",
        "depth_mm",
        "height_mm",
        "input_current_a",
        "input_power_kw",
        "liquid_flow_l_min",
        "weight_kg",
        "width_mm",
    ]
    fields = [
        "capacity_scope",
        "cooling_rating_conditions",
        "equipment_category",
        "form_factor",
        "manufacturer",
        "model",
        "name",
        "notes",
        "observations_json",
        "official_url",
        "record_scope",
        "variant",
    ] + [field for field in normalized if item.get(field) is not None]
    if item.get("input_power_kw") is not None:
        fields.extend(["power_conditions", "power_rating_kind"])
    units = {
        "airflow_m3_h": "m3/h",
        "cooling_capacity_kw": "kW",
        "depth_mm": "mm",
        "height_mm": "mm",
        "input_current_a": "A",
        "input_power_kw": "kW",
        "liquid_flow_l_min": "L/min",
        "weight_kg": "kg",
        "width_mm": "mm",
    }
    evidence: dict[str, dict[str, object]] = {}
    for field in fields:
        evidence[field] = {
            "confidence": "high",
            "locator": item["locator"],
            "source_publication_dates": {source_id: source["publication_date"]},
        }
        if field in units:
            evidence[field]["unit"] = units[field]
    observations = [
        observation(item, field, value, unit) for field, value, unit in item.get("extras", [])
    ]
    observations.extend(
        [
            observation(item, "nominal_power_supply", "380-415 V AC, 3-phase", "V")
            if source_id.startswith("huawei-")
            else observation(item, "voltage_choices", "See exact OEM page; multiple choices", "V"),
            observation(item, "frequency_choices", "50/60", "Hz"),
        ]
    )
    if source_id.startswith("huawei-"):
        notes = (
            "The generic table configuration is retained exactly; BOM suffixes are not "
            "expanded into undocumented combinations. Cooling-only current/weight is "
            "normalized where available; optional or full-configuration values remain observations."
        )
    else:
        notes = (
            "Alternate rating points and voltage choices remain observations. Optional "
            "heater/humidifier packages are not synthesized. OEM safety/conformance "
            "statements are not promoted to issuer-registry certifications."
        )
    record: dict[str, object] = {
        "capacity_scope": (
            f"Exact OEM {item['model']} {item['variant']} cooling configuration at the "
            "stated rating point"
        ),
        "cooling_rating_conditions": item["cooling_rating_conditions"],
        "created_at": RETRIEVED_AT,
        "entity_type": "equipment",
        "equipment_category": item["category"],
        "evidence_json": compact(evidence),
        "field_sources_json": compact({field: [source_id] for field in fields}),
        "form_factor": item["form_factor"],
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": item["manufacturer"],
        "model": item["model"],
        "name": f"{item['manufacturer']} {item['model']}",
        "notes": notes,
        "observations_json": compact(observations),
        "official_url": source["url"],
        "quality_status": "source_backed",
        "record_id": stable_id("equipment", item["manufacturer"], item["model"], item["variant"]),
        "record_scope": "configuration",
        "source_urls": [source["url"]],
        "sources": [source_id],
        "updated_at": RETRIEVED_AT,
        "variant": item["variant"],
    }
    if item.get("input_power_kw") is not None:
        record["power_conditions"] = (
            "OEM maximum equipment power consumption; cooling-only base value where "
            "heater/humidifier packages are separately reported"
        )
        record["power_rating_kind"] = "maximum equipment power consumption"
    for field in normalized:
        if item.get(field) is not None:
            record[field] = item[field]
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    staged: list[dict[str, Any]] = []
    for source_id, source in SOURCES.items():
        selected = [item for item in ROWS if item["source"] == source_id]
        result = parse_precision_cooling_matrix(
            extracted_csv(selected),
            source_url=str(source["url"]),
            expected_count=len(selected),
        )
        staged.extend(result["candidates"])
    if len(staged) != len(ROWS):
        raise ValueError("Staging lost precision-cooling rows")
    records = [build_record(item) for item in ROWS]
    if len(records) != 23 or len({record["record_id"] for record in records}) != 23:
        raise ValueError("Expected 23 unique Asian precision-cooling configurations")
    records.sort(key=lambda record: (record["manufacturer"], record["model"], record["variant"]))
    args.output.write_text("".join(f"{compact(record)}\n" for record in records), encoding="utf-8")
    print("Wrote 23 reviewed Huawei/Delta precision-cooling configurations")


if __name__ == "__main__":
    main()
