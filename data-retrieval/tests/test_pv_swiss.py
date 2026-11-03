"""Source contracts for Swiss PV staging."""

import hashlib
import io
import zipfile

import pytest

from energy_data_retrieval.pv_catalogue.swiss import stage_swiss_pv


def _archive(details: str, pv_code: str = "Photovoltaic") -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as archive:
        archive.writestr("SubCategoryCatalogue.csv", f"Catalogue_id,en\nsubcat_2,{pv_code}\n")
        archive.writestr(
            "ElectricityProductionPlant.csv",
            "xtf_id,SubCategory,InitialPower,TotalPower,BeginningOfOperation,EGID,Address\n"
            "1,subcat_2,1000,1200,2020-01-01,123,private address\n"
            "2,subcat_2,4,4,2020-01-01,123,private address\n"
            "3,subcat_1,9999,9999,2020-01-01,,hydro\n",
        )
        archive.writestr(
            "PlantDetail.csv", "xtf_id,ElectricityProductionPlantR,Power,Date\n" + details
        )
    return out.getvalue()


def test_parent_scope_and_optional_details() -> None:
    raw = _archive("01,1,200,2021-01-01\n02,1,,\n")
    (row,) = stage_swiss_pv(raw, sha256=hashlib.sha256(raw).hexdigest())
    assert row["source_parent_id"] == "1"
    assert row["total_power_kw"] == "1200"
    assert row["power_basis"] == "unspecified_ac_dc"
    assert row["linked_detail_count"] == 2
    assert row["linked_detail_power_kw"] is None
    assert row["shared_building_review"]
    assert "private" not in str(row) and "123" not in str(row)
    assert row["disposition"] == "review_only"


@pytest.mark.parametrize(
    ("details", "code", "message"),
    [
        ("01,404,200,2021-01-01\n", "Photovoltaic", "Orphan"),
        ("01,1,200,2021-01-01\n01,2,4,2021-01-01\n", "Photovoltaic", "duplicate"),
        ("", "Solar", "PV code"),
        ("01,1,NaN,2021-01-01\n", "Photovoltaic", "native kW"),
    ],
)
def test_invalid_source_is_rejected(details: str, code: str, message: str) -> None:
    raw = _archive(details, code)
    with pytest.raises(ValueError, match=message):
        stage_swiss_pv(raw, sha256=hashlib.sha256(raw).hexdigest())


def test_checksum_pins_revision() -> None:
    with pytest.raises(ValueError, match="checksum"):
        stage_swiss_pv(_archive(""), sha256="0" * 64)
