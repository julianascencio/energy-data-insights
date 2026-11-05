"""Synthetic BOE boundary tests; notice title is never a project import."""

import hashlib

import pytest

from energy_data_retrieval.bess_catalogue.boe import inspect_notice, select_battery_notices


def index(title="baterías sintéticas", ident="BOE-A-2026-1"):
    return f"<response><status><code>200</code></status><data><sumario><metadatos><fecha_publicacion>20261030</fecha_publicacion></metadatos><diario><item><identificador>{ident}</identificador><titulo>{title}</titulo><url_xml>https://www.boe.es/diario_boe/xml.php?id={ident}</url_xml></item></diario></sumario></data></response>".encode()


def test_select_not_infer():
    a = select_battery_notices(index(), expected_date="20261030")
    assert len(a) == 1
    assert "power_capacity_mw" not in a[0]
    assert select_battery_notices(index("parque eólico"), expected_date="20261030") == []


@pytest.mark.parametrize(
    "content,date",
    [
        (index(), "20261029"),
        (index().replace(b"<code>200", b"<code>404"), "20261030"),
        (index(ident="BAD"), "20261030"),
        (b"<!DOCTYPE x>" + index(), "20261030"),
    ],
)
def test_bad_index(content, date):
    with pytest.raises(ValueError):
        select_battery_notices(content, expected_date=date)


def test_notice_hash_identity_and_paragraphs():
    b = (
        b"<documento><metadatos><identificador>BOE-A-2026-1</identificador>"
        b"</metadatos><texto><p>Battery <b>planned</b>.</p></texto></documento>"
    )
    h = hashlib.sha256(b).hexdigest()
    assert inspect_notice(b, expected_id="BOE-A-2026-1", sha256=h)["paragraphs"] == [
        "Battery planned."
    ]
    with pytest.raises(ValueError):
        inspect_notice(b, expected_id="BOE-A-2026-2", sha256=h)
    with pytest.raises(ValueError):
        inspect_notice(b, expected_id="BOE-A-2026-1", sha256="0" * 64)
