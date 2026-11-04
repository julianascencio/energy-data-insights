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


def test_numeric_upper_bound_is_preserved():
    result = parse_panels(
        fixture("&lt;100ms"), expected_models=["TEST-A"], expected_fields={"Channel current"}
    )
    assert result[0]["fields"]["Channel current"] == "<100ms"


@pytest.mark.parametrize("value", ["<b>100</b>", "&lt;script&gt;bad&lt;/script&gt;", "<!--x-->"])
def test_markup_is_rejected(value):
    with pytest.raises(ValueError, match="markup"):
        parse_panels(
            fixture(value), expected_models=["TEST-A"], expected_fields={"Channel current"}
        )


def test_per_model_field_labels_require_exact_review():
    content = fixture().replace(b"</a></div>", b"</a><a>TEST-B</a></div>")
    content += (
        fixture()
        .split(b'<div class="info_list">', 1)[1]
        .join([b'<div class="info_list">', b""])
        .replace(b"Channel current", b"Channel current (B)")
    )
    labels = [{"Channel current"}, {"Channel current (B)"}]
    assert (
        len(parse_panels(content, expected_models=["TEST-A", "TEST-B"], expected_fields=labels))
        == 2
    )
    with pytest.raises(ValueError, match="field set"):
        parse_panels(content, expected_models=["TEST-A", "TEST-B"], expected_fields=labels[:1])
    with pytest.raises(ValueError, match="layout"):
        parse_panels(content, expected_models=["TEST-A", "TEST-B"], expected_fields=labels[::-1])
