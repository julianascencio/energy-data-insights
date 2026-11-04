"""Synthetic changed-layout and identity guards; no copyrighted fixtures."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.kehua_panels import parse_panels


def fixture(value="240A*2"):
    return (
        '<div class="xx_xh"><a>TEST-A</a></div><div class="info_list">'
        '<div class="attr_item"><p>Channel current</p><p>' + value + "</p></div>"
        '<div class="g-btn-red">'
    ).encode()


def test_channel_current_is_not_summed():
    assert parse_panels(fixture(), expected_models=["TEST-A"], expected_fields={"Channel current"})[
        0
    ]["fields"] == {"Channel current": "240A*2"}


@pytest.mark.parametrize(
    "mutation",
    [
        lambda x: x.replace(b"TEST-A", b"TEST-B"),
        lambda x: x.replace(b"Channel current", b"Maximum current"),
        lambda x: x.replace(b'<div class="g-btn-red">', b""),
        lambda x: x.replace(b"240A*2", b""),
        lambda x: x.replace(
            b'<div class="g-btn-red">',
            b'<div class="attr_item"><p>Channel current</p><p>999A</p></div>'
            b'<div class="g-btn-red">',
        ),
    ],
)
def test_unreviewed_panel_rejected(mutation):
    with pytest.raises(ValueError):
        parse_panels(
            mutation(fixture()), expected_models=["TEST-A"], expected_fields={"Channel current"}
        )
