"""Synthetic layout fixtures; no OEM document redistribution."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.ingeteam import parse_converter_text


def m_fixture():
    table = """INGECON SUN STORAGE 4540TL
M600 M630 M660 M690
INPUT (DC) M3 M4 M3 M4 M3 M4 M3 M4
854 to 1,500 896 to 1,500 938 to 1,500 980 to 1,500
938 to 1,500 984 to 1,500 1,035 to 1,500 1,077 to 1,500
Nº DC inputs per module 5
Discharge/charge power (40 °C)[kVA] 2,961 3,948 3,111 4,148 3,258 4,344 3,405 4,540
Discharge/charge current (40 °C) [A] 2,850 3,800 2,850 3,800 2,850 3,800 2,850 3,800
AC output voltage 600 630 660 690
300002287_C"""
    return ("\f" * 3 + table).encode()


def c_fixture():
    table = """INGECON SUN STORAGE 3930TL HV
C600 C630 C660 C690 C720 C760 C840
INPUT (DC)
854 - 1,500 V 895 - 1,500 V 938 - 1,500 V 979 - 1,500 V 1,021 - 1,500 V 1,077 - 1,500 V
1,188 - 1,500 V
938 - 1,500 V 985 - 1,500 V 1,029 - 1,500 V 1,075 - 1,500 V 1,121 - 1,500 V 1,182 - 1,500 V
1,305 - 1,500 V
Maximum voltage 1500
Discharge power @1,500 Vdc (30 °C/ 50 °C)
2,806 kVA / 2,946 kVA / 3,087 kVA / 3,227 kVA / 3,367 kVA / 3,554 kVA / 3,928 kVA /
2,265 kVA 2,379 kVA 2,492 kVA 2,605 kVA 2,719 kVA 2,870 kVA 3,172 kVA
Discharge current @1,500 Vdc 2700 / 2180
Charge power @1,500 Vdc (30 °C/ 50 °C)
2,666 kVA / 2,799 kVA / 2,932 kVA / 3,066 kVA / 3,199 kVA / 3,377 kVA / 3,732 kVA /
2,152 kVA 2,260 kVA 2,368 kVA 2,475 kVA 2,583 kVA 2,726 kVA 3,013 kVA
Charge current @1,500 Vdc 2565 / 2071
300001994/F"""
    return ("\f" * 2 + table).encode()


def tl_fixture():
    pages = []
    for volts, mins, powers in [
        ([600, 615, 630, 645, 660], [933, 957, 980, 1003, 1027], [260, 266, 273, 279, 286]),
        (
            [675, 690, 710, 730, 750, 800],
            [1050, 1073, 1104, 1136, 1167, 1245],
            [292, 299, 307, 316, 325, 346],
        ),
    ]:
        pages.append(
            "INGECON SUN STORAGE 350TL\n"
            + " ".join(f"{x} V" for x in volts)
            + "\nINPUT (DC)\n"
            + " ".join(f"{x:,} - 1,500 V" for x in mins)
            + "\nMaximum voltage 1500\nCharge/Discharge power "
            + " ".join(f"{x} kVA" for x in powers)
            + "\nCharge/Discharge current 250\n300002273_A"
        )
    return ("\f\f" + "\f".join(pages)).encode()


def test_m_merged_voltage_columns_and_independent_module_identity():
    rows = parse_converter_text(m_fixture(), "M")
    assert len(rows) == 8
    assert rows[2]["configuration"] == "M630 M3"
    assert rows[3]["configuration"] == "M630 M4"
    assert rows[2]["grid_tied_dc_min_v"] == rows[3]["grid_tied_dc_min_v"] == 984
    assert rows[7]["charge_discharge_kva"] == 4540
    assert rows[7]["ac_current_a"] == 3800
    assert all("power_capacity_mw" not in r for r in rows)


def test_c_charge_discharge_and_temperature_rows_not_interleaved():
    rows = parse_converter_text(c_fixture(), "C")
    assert len(rows) == 7
    assert rows[0]["discharge_kva_30c"] == 2806
    assert rows[0]["discharge_kva_50c"] == 2265
    assert rows[-1]["charge_kva_30c"] == 3732
    assert rows[-1]["charge_kva_50c"] == 3013
    assert rows[-1]["grid_tied_dc_min_v"] == 1305


def test_tl_voltage_points_do_not_create_eleven_models():
    rows = parse_converter_text(tl_fixture(), "350")
    assert len(rows) == 1
    points = rows[0]["operating_points"]
    assert len(points) == 11
    assert points[4]["ac_voltage_v"] == 660
    assert points[5]["ac_voltage_v"] == 675
    assert points[-1]["charge_discharge_kva"] == 346
    assert points[-1]["dc_min_v"] == 1245


@pytest.mark.parametrize(
    ("factory", "series", "before", "after"),
    [
        (m_fixture, "M", b"300002287_C", b"300002287_D"),
        (m_fixture, "M", b"M600 M630", b"M630 M600"),
        (m_fixture, "M", b"M3 M4", b"M4 M3"),
        (m_fixture, "M", b"[kVA]", b"[kW]"),
        (m_fixture, "M", b"2,961 3,948", b"2,961"),
        (m_fixture, "M", b"4,540", b"0"),
        (c_fixture, "C", b"C600 C630", b"C630 C600"),
        (c_fixture, "C", b"kVA", b"kW"),
        (c_fixture, "C", b"30 \xc2\xb0C/ 50 \xc2\xb0C", b"25 C/ 45 C"),
        (tl_fixture, "350", b"675 V 690 V", b"690 V 675 V"),
        (tl_fixture, "350", b"kVA", b"kW"),
        (tl_fixture, "350", b"1,245 - 1,500 V", b"1,245 - 1,600 V"),
    ],
)
def test_changed_layouts_fail_closed(factory, series, before, after):
    with pytest.raises(ValueError):
        parse_converter_text(factory().replace(before, after), series)
