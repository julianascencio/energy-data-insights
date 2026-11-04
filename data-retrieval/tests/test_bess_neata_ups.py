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
