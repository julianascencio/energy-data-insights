import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from energy_data_retrieval.pv_catalogue.nve import read_nve_solar_cases


def _case(**updates: Any) -> dict[str, Any]:
    return {
        "objekttype": "Solkraftverk",
        "anleggsnr": 44,
        "saksid": 71,
        "anleggnavn": "Example solkraftverk ",
        "kommune": "Example",
        "fylkenavn": "Example county",
        "sakslenke": "https://www.nve.no/konsesjon/konsesjonssaker/konsesjonssak?type=A-6&id=71",
        "stadium": "Konsesjon gitt",
        "status": "U",
        "effekt_mw": 5.6,
        "effekt_mw_idrift": None,
        "forventetproduksjon_gwh": 7.5,
        "datafangstdato": 1704429010000,
        "eier": "private field",
        **updates,
    }


def _write(path: Path, *rows: dict[str, Any]) -> str:
    raw = json.dumps(
        {
            "exceededTransferLimit": True,
            "features": [{"attributes": x, "geometry": {"x": 1, "y": 2}} for x in rows],
        }
    ).encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def test_nve_stages_native_bases_and_excludes_other_objects(tmp_path: Path) -> None:
    path = tmp_path / "cases.json"
    result = read_nve_solar_cases(
        path, sha256=_write(path, _case(), _case(objekttype="Transformatorstasjon"))
    )
    (row,) = result.cases
    assert result.exceeded_transfer_limit and result.excluded_non_solar == 1
    assert row.name == "Example solkraftverk"
    assert row.proposed_mw == 5.6 and row.in_service_mw is None
    assert row.forecast_gwh == 7.5 and row.stage == "Konsesjon gitt"
    assert row.first_service_timestamp is None
    assert row.data_capture_timestamp == "2024-01-05T04:30:10+00:00"
    assert not hasattr(row, "eier") and not hasattr(row, "geometry")


def test_nve_keeps_repeated_ids_for_review(tmp_path: Path) -> None:
    path = tmp_path / "cases.json"
    result = read_nve_solar_cases(
        path, sha256=_write(path, _case(), _case(anleggnavn="Possible phase"))
    )
    assert len(result.cases) == 2
    assert all(
        row.review_flags == ("repeated_plant_number", "repeated_case_id") for row in result.cases
    )


@pytest.mark.parametrize(
    ("updates", "message"),
    [
        ({"anleggsnr": True}, "identifier"),
        (
            {
                "sakslenke": "https://www.nve.no/konsesjon/konsesjonssaker/konsesjonssak?type=A-6&id=72"
            },
            "URL",
        ),
        ({"effekt_mw": -1}, "quantity"),
        ({"datafangstdato": "2026-10-01"}, "epoch"),
    ],
)
def test_nve_rejects_invalid_source_values(
    tmp_path: Path, updates: dict[str, Any], message: str
) -> None:
    path = tmp_path / "cases.json"
    with pytest.raises(ValueError, match=message):
        read_nve_solar_cases(path, sha256=_write(path, _case(**updates)))


def test_nve_rejects_changed_file(tmp_path: Path) -> None:
    path = tmp_path / "cases.json"
    checksum = _write(path, _case())
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="checksum"):
        read_nve_solar_cases(path, sha256=checksum)
