"""Synthetic identity and unit tests, without publisher data fixtures."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.neata_ups import HEADER, MODELS, parse_sc_partitions


def sample():
    rows = [HEADER, ["(V)", "W", "(V)", "usually", "Max", "L", "W", "H", "(kg)"]]
    rows += [
        [
            m,
            "48V30Ah",
            "48",
            "27",
            "1000",
            "50~55(60)",
            "10",
            "20",
            "1000W(2000W/60S)",
            "100",
            "200",
            "300",
            "12.5",
        ]
        for m in MODELS
    ]
    return (
        "<table>"
        + "".join("<tr>" + "".join("<td>" + v + "</td>" for v in r) + "</tr>" for r in rows)
        + "</table>"
    ).encode()


def test_conflicting_label_preserved():
    r = parse_sc_partitions(sample())
    assert len(r) == 21
    assert r[0]["pack_ah"] == "27"
    assert r[0]["battery_type_label"] == "48V30Ah"
    assert "energy_capacity_mwh" not in r[0]


@pytest.mark.parametrize(
    "a,b",
    [
        (b"SC48-20", b"SC48-27"),
        (b"1000W(", b"1000VA("),
        (b"60S", b"30S"),
        (b"50~55(60)", b"50-55"),
        (b"(kg)", b"(lb)"),
        (b"</table>", b""),
    ],
)
def test_changed_source_fails(a, b):
    with pytest.raises(ValueError):
        parse_sc_partitions(sample().replace(a, b, 1))


def high_sample():
    from energy_data_retrieval.bess_oem_catalogue.neata_ups import HIGH_MODELS

    row = (
        "<tr>"
        + "".join(
            "<td>" + v + "</td>"
            for v in [
                "MODEL",
                "96V30Ah",
                "102.4",
                "27",
                "4000",
                "108.8~110.4(115.2)",
                "15",
                "27",
                "4000W(5000W/60S)",
                "600",
                "442",
                "86",
                "36.5",
            ]
        )
        + "</tr>"
    )
    return sample().replace(
        b"</table>", ("".join(row.replace("MODEL", m) for m in HIGH_MODELS) + "</table>").encode()
    )


def test_high_conflicts_preserved():
    from energy_data_retrieval.bess_oem_catalogue.neata_ups import parse_high_sc

    rows = parse_high_sc(high_sample())
    assert len(rows) == 13
    assert rows[0]["voltage_v"] == "102.4"
    assert rows[0]["battery_type_label"] == "96V30Ah"


@pytest.mark.parametrize(
    "a,b",
    [
        (b"SC102-20", b"SC102-27"),
        (b"4000W(5000W/60S)", b"4000VA"),
        (b"102.4", b"102.4V"),
        (b"108.8~110.4(115.2)", b"108-115"),
    ],
)
def test_high_mutations_fail(a, b):
    from energy_data_retrieval.bess_oem_catalogue.neata_ups import parse_high_sc

    with pytest.raises(ValueError):
        parse_high_sc(high_sample().replace(a, b, 1))


def cabinet_sample():
    from energy_data_retrieval.bess_oem_catalogue.neata_ups import CABINET_MODELS

    row = (
        "<tr>"
        + "".join(
            "<td>" + v + "</td>"
            for v in [
                "MODEL",
                "204.8V50Ah",
                "204.8",
                "50",
                "max. 48.64KW",
                "217.6~220.8(230.4)",
                "25",
                "50",
                "39.68KW/15min",
                "800",
                "600",
                "1165",
                "215",
            ]
        )
        + "</tr>"
    )
    return high_sample().replace(
        b"</table>",
        ("".join(row.replace("MODEL", m) for m in CABINET_MODELS) + "</table>").encode(),
    )


def test_cabinets_preserve_distinct_power_observations():
    from energy_data_retrieval.bess_oem_catalogue.neata_ups import parse_low_voltage_cabinets

    rows = parse_low_voltage_cabinets(cabinet_sample())
    assert len(rows) == 12
    assert rows[0]["power_w"] == "max. 48.64KW"
    assert rows[0]["discharge_power_native"] == "39.68KW/15min"


@pytest.mark.parametrize(
    "a,b",
    [
        (b"TC40</td>", b"NC16</td>"),
        (b"max. 48.64KW", b"48.64KVA"),
        (b"39.68KW/15min", b"39.68KW/15h"),
        (b"204.8</td>", b"512</td>"),
    ],
)
def test_cabinet_mutations_fail(a, b):
    from energy_data_retrieval.bess_oem_catalogue.neata_ups import parse_low_voltage_cabinets

    with pytest.raises(ValueError):
        parse_low_voltage_cabinets(cabinet_sample().replace(a, b, 1))


def middle_sample():
    from energy_data_retrieval.bess_oem_catalogue.neata_ups import MID_CABINET_MODELS

    row = (
        "<tr>"
        + "".join(
            "<td>" + v + "</td>"
            for v in [
                "MODEL",
                "384V30Ah",
                "384",
                "27",
                "max.44.8KW",
                "408~414(432)",
                "15",
                "27",
                "41.6KW/10min",
                "800",
                "600",
                "1165",
                "257",
            ]
        )
        + "</tr>"
    )
    return cabinet_sample().replace(
        b"</table>",
        ("".join(row.replace("MODEL", m) for m in MID_CABINET_MODELS) + "</table>").encode(),
    )


def test_middle_native_conflict_retained():
    from energy_data_retrieval.bess_oem_catalogue.neata_ups import parse_mid_voltage_cabinets

    rows = parse_mid_voltage_cabinets(middle_sample())
    assert len(rows) == 14
    assert rows[0]["battery_type_label"] == "384V30Ah"
    assert rows[0]["pack_ah"] == "27"


@pytest.mark.parametrize(
    "a,b",
    [
        (b"NC24Y</td>", b"TC48Y</td>"),
        (b"max.44.8KW", b"max.44.8KVA"),
        (b"41.6KW/10min", b"41.6KW/10h"),
        (b"384</td>", b"768</td>"),
    ],
)
def test_middle_mutations_fail(a, b):
    from energy_data_retrieval.bess_oem_catalogue.neata_ups import parse_mid_voltage_cabinets

    with pytest.raises(ValueError):
        parse_mid_voltage_cabinets(middle_sample().replace(a, b, 1))


def upper_sample():
    from energy_data_retrieval.bess_oem_catalogue.neata_ups import UPPER_CABINET_MODELS

    row = (
        "<tr>"
        + "".join(
            "<td>" + v + "</td>"
            for v in [
                "MODEL",
                "480V30Ah",
                "480",
                "27",
                "max.44.8KW",
                "510~517.5(540)",
                "15",
                "27",
                "41.6KW/10min",
                "800",
                "600",
                "1165",
                "257",
            ]
        )
        + "</tr>"
    )
    return middle_sample().replace(
        b"</table>",
        ("".join(row.replace("MODEL", m) for m in UPPER_CABINET_MODELS) + "</table>").encode(),
    )


def test_upper_native_conflict_retained():
    from energy_data_retrieval.bess_oem_catalogue.neata_ups import parse_upper_voltage_cabinets

    rows = parse_upper_voltage_cabinets(upper_sample())
    assert len(rows) == 13
    assert rows[0]["battery_type_label"] == "480V30Ah"
    assert rows[0]["pack_ah"] == "27"


@pytest.mark.parametrize(
    "a,b",
    [
        (b"NC30Y</td>", b"TC60Y</td>"),
        (b"max.44.8KW", b"max.44.8KVA"),
        (b"41.6KW/10min", b"41.6KW/10h"),
        (b"480</td>", b"768</td>"),
    ],
)
def test_upper_mutations_fail(a, b):
    from energy_data_retrieval.bess_oem_catalogue.neata_ups import parse_upper_voltage_cabinets

    with pytest.raises(ValueError):
        parse_upper_voltage_cabinets(upper_sample().replace(a, b, 1))


def final_sample():
    from energy_data_retrieval.bess_oem_catalogue.neata_ups import FINAL_CABINET_MODELS

    row = (
        "<tr>"
        + "".join(
            "<td>" + v + "</td>"
            for v in [
                "MODEL",
                "614.4V30Ah",
                "614.4",
                "27",
                "max.44.8KW",
                "510~517.5(540)",
                "15",
                "27",
                "41.6KW/10min",
                "800",
                "600",
                "1165",
                "257",
            ]
        )
        + "</tr>"
    )
    return upper_sample().replace(
        b"</table>",
        ("".join(row.replace("MODEL", m) for m in FINAL_CABINET_MODELS) + "</table>").encode(),
    )


def test_final_native_conflict_retained():
    from energy_data_retrieval.bess_oem_catalogue.neata_ups import parse_final_voltage_cabinets

    rows = parse_final_voltage_cabinets(final_sample())
    assert len(rows) == 23
    assert rows[0]["battery_type_label"] == "614.4V30Ah"
    assert rows[0]["pack_ah"] == "27"


@pytest.mark.parametrize(
    "a,b",
    [
        (b"NC36</td>", b"TC72</td>"),
        (b"max.44.8KW", b"max.44.8KVA"),
        (b"41.6KW/10min", b"41.6KW/10h"),
        (b"614.4</td>", b"1024</td>"),
    ],
)
def test_final_mutations_fail(a, b):
    from energy_data_retrieval.bess_oem_catalogue.neata_ups import parse_final_voltage_cabinets

    with pytest.raises(ValueError):
        parse_final_voltage_cabinets(final_sample().replace(a, b, 1))


def test_final_missing_power_suffix_is_native_only_for_reviewed_models():
    from energy_data_retrieval.bess_oem_catalogue.neata_ups import parse_final_voltage_cabinets

    raw = final_sample().replace(
        b"NC42</td><td>614.4V30Ah</td><td>614.4</td><td>27</td><td>max.44.8KW",
        b"NC42</td><td>614.4V30Ah</td><td>614.4</td><td>27</td><td>max.44.8",
    )
    row = next(r for r in parse_final_voltage_cabinets(raw) if r["model"] == "NC42")
    assert row["power_w"] == "max.44.8"
    with pytest.raises(ValueError):
        parse_final_voltage_cabinets(raw.replace(b"max.44.8KW", b"max.44.8", 1))
