"""Synthetic NEA schema/classification/identity tests; no government document fixture."""

import hashlib
import io
import zipfile

import pytest

from energy_data_retrieval.pv_catalogue.nea import HEADERS, read_nea_pv_registrations


def document(
    *, heading="二、集中式光伏发电\uff081个\uff09", codes=None, headers=None, power="5.12"
):
    codes = ["PPC25013411030011"] if codes is None else codes
    cells = [HEADERS if headers is None else headers] + [
        [str(i), code, "Synthetic PV", power, "Synthetic locality"]
        for i, code in enumerate(codes, start=1)
    ]
    table = "".join(
        "<w:tr>"
        + "".join(f"<w:tc><w:p><w:r><w:t>{v}</w:t></w:r></w:p></w:tc>" for v in row)
        + "</w:tr>"
        for row in cells
    )
    xml = (
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body><w:p><w:r><w:t>{heading}</w:t></w:r></w:p><w:tbl>{table}</w:tbl>"
        "</w:body></w:document>"
    )
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("word/document.xml", xml)
    return stream.getvalue()


def read(content):
    return read_nea_pv_registrations(content, sha256=hashlib.sha256(content).hexdigest())


def test_registration_stays_candidate():
    row = read(document())[0]
    assert row["registered_capacity_mw"] == 5.12
    assert "record_id" not in row and "status" not in row and "commissioning_date" not in row
    assert "AC/DC unspecified" in row["capacity_basis"]


@pytest.mark.parametrize(
    "options",
    [
        {"heading": "一、风电\uff081个\uff09"},
        {"heading": "二、集中式光伏发电\uff082个\uff09"},
        {"codes": ["PWC25013411030011"]},
        {"codes": ["PPC25013411030011"] * 2, "heading": "二、集中式光伏发电\uff082个\uff09"},
        {"headers": [*HEADERS, "Private contact"]},
        {"power": "5,12"},
    ],
)
def test_unreviewed_schema_identity_or_power_rejected(options):
    with pytest.raises(ValueError):
        read(document(**options))


def test_checksum_before_parsing():
    with pytest.raises(ValueError, match="checksum"):
        read_nea_pv_registrations(b"invalid", sha256="0" * 64)
