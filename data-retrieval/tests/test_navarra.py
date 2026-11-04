"""Synthetic DBF tests for layout, privacy and reviewed permit identities."""

import hashlib
import io
import struct
import zipfile

import pytest

from energy_data_retrieval.pv_catalogue.navarra import (
    COLUMNS,
    read_navarra_archive,
    reviewed_navarra_project,
)


def archive(
    *, cases=("123-CE",), power="1.2500", licence="CC BY 4.0", deleted=False, layer="operating"
):
    columns = (
        COLUMNS
        if layer == "operating"
        else [k for k in COLUMNS if k not in {"PUESTSERV", "RAIPEE"}]
    )
    suffix = "" if layer == "operating" else "Tra"
    title = "servicio" if layer == "operating" else "tramitación"
    widths = [max(32, len(k)) for k in columns]
    header = 33 + 32 * len(columns)
    size = 1 + sum(widths)
    data = bytearray(header + size * len(cases) + 1)
    data[0] = 3
    data[4:12] = struct.pack("<IHH", len(cases), header, size)
    for i, (key, width) in enumerate(zip(columns, widths, strict=True)):
        p = 32 + i * 32
        data[p : p + len(key)] = key.encode()
        data[p + 11] = ord("C")
        data[p + 16] = width
    data[header - 1] = 13
    for i, case in enumerate(cases):
        values = dict.fromkeys(columns, "")
        values.update(
            FEATURE="8200011",
            NOMBRE="Synthetic plant",
            PROMOTOR="PRIVATE PERSON",
            POT_MW=power,
            EXPEDIENTE=case,
            PUESTSERV="2026",
            BEGINLIFE="19/05/2026",
        )
        p = header + i * size
        data[p] = 42 if deleted else 32
        p += 1
        for key, width in zip(columns, widths, strict=True):
            data[p : p + width] = values[key].encode().ljust(width)
            p += width
    data[-1] = 26
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("ENERGI_Pol_PSolar" + suffix + ".dbf", data)
        z.writestr(
            "spaSITNAENERGI_Pol_PSolar" + suffix + ".xml",
            licence
            + " suma de las potencias de los paneles Plantas solares fotovoltaicas en "
            + title,
        )
    return out.getvalue()


def read(data):
    return read_navarra_archive(data, sha256=hashlib.sha256(data).hexdigest())


def test_privacy_units_and_no_invented_status_or_point():
    rows = read(archive())
    assert "PROMOTOR" not in rows[0] and "PRIVATE PERSON" not in str(rows)
    row = reviewed_navarra_project(
        rows[0], rows=rows, approved_case="123-CE", source_id="test", now="2026-11-04T11:00:00Z"
    )
    assert row["capacity_dc_mw"] == 1.25
    assert not {"status", "latitude", "commissioning_year", "owners"} & row.keys()
    assert "8200011" not in row["external_ids_json"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"licence": "restricted"},
        {"power": "NaN"},
        {"power": "0"},
        {"deleted": True},
    ],
)
def test_reject_changed_rights_nonfinite_power_and_deleted_rows(kwargs):
    with pytest.raises(ValueError):
        read(archive(**kwargs))


@pytest.mark.parametrize(
    "cases,approved",
    [
        (("123-CE", "123-CE"), "123-CE"),
        (("123-456-CE",), "123-456-CE"),
        (("123-CE",), "456-CE"),
    ],
)
def test_repeated_aggregate_and_unreviewed_cases_cannot_be_accepted(cases, approved):
    rows = read(archive(cases=cases))
    with pytest.raises(ValueError):
        reviewed_navarra_project(
            rows[0], rows=rows, approved_case=approved, source_id="test", now="2026-11-04T11:00:00Z"
        )


def test_checksum_and_truncation():
    data = archive()
    with pytest.raises(ValueError, match="checksum"):
        read_navarra_archive(data, sha256="0" * 64)
    z = zipfile.ZipFile(io.BytesIO(data))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as target:
        target.writestr("ENERGI_Pol_PSolar.dbf", z.read("ENERGI_Pol_PSolar.dbf")[:-4])
        target.writestr("spaSITNAENERGI_Pol_PSolar.xml", z.read("spaSITNAENERGI_Pol_PSolar.xml"))
    with pytest.raises(ValueError, match="Truncated"):
        read(out.getvalue())


def test_permitting_is_separate_and_never_operating():
    data = archive(layer="permitting")
    rows = read_navarra_archive(data, sha256=hashlib.sha256(data).hexdigest(), layer="permitting")
    assert "tramitación" in rows[0]["source_layer"]
    assert "PUESTSERV" not in rows[0]
    with pytest.raises(KeyError):
        read(data)
    with pytest.raises(ValueError, match="Unknown"):
        read_navarra_archive(data, sha256=hashlib.sha256(data).hexdigest(), layer="other")
