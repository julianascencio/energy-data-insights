"""Synthetic IFB layout boundary tests; not copies of tender documents."""

import pytest

from energy_data_retrieval.bess_catalogue.ntpc import parse_ntpc_ifb


def fixture(lot: int = 1) -> bytes:
    count, total, ident, date, letter = (
        (7, 2334, "100673", "30.09.2025", "A")
        if lot == 1
        else (9, 2670, "101702", "06.11.2025", "B")
    )
    text = f"2025_NTPC_{ident}_1 CS-0011-171{letter}-9 {date} (Lot-{lot})\n"
    text += f"Lot-{lot} comprises the following Stations/projects:\nBattery Capacity (MWh)\n"
    for i in range(1, count + 1):
        rating = total - (count - 1) * 100 if i == count else 100
        text += f" {i}. Synthetic Site {chr(64 + i)}\n     (Alias {chr(64 + i)})    {rating}\n"
    return (text + "2.0 BRIEF SCOPE\nContact data excluded").encode()


@pytest.mark.parametrize("lot,count", [(1, 7), (2, 9)])
def test_complete_table_and_boundaries(lot: int, count: int) -> None:
    rows = parse_ntpc_ifb(fixture(lot), lot=lot)
    assert len(rows) == count
    assert rows[0]["source_name"] == "Synthetic Site A (Alias A)"
    assert rows[0]["status"] == "announced"
    assert "power_mw" not in rows[0]
    assert "Contact" not in str(rows)


@pytest.mark.parametrize(
    "old,new",
    [
        (b"MWh", b"MW"),
        (b"30.09.2025", b"30.09.2026"),
        (b"7. Synthetic", b"8. Synthetic"),
        (b"1734", b"1735"),
        (b"100\n", b"0\n"),
        (b"Site B", b"Site A"),
    ],
)
def test_changed_table_fails(old: bytes, new: bytes) -> None:
    content = fixture().replace(old, new)
    if old == b"Site B":
        content = content.replace(b"Alias B", b"Alias A")
    with pytest.raises(ValueError):
        parse_ntpc_ifb(content, lot=1)


def test_same_site_across_lots_is_not_merged() -> None:
    first = parse_ntpc_ifb(fixture(1), lot=1)[0]
    second = parse_ntpc_ifb(fixture(2), lot=2)[0]
    assert first["source_name"] == second["source_name"]
    assert first["tender_id"] != second["tender_id"]


def test_unreviewed_lot() -> None:
    with pytest.raises(ValueError, match="lot"):
        parse_ntpc_ifb(fixture(), lot=3)


def test_wrapped_header_and_capacity_before_name_continuation() -> None:
    content = fixture().replace(b"Battery Capacity (MWh)", b"Battery\nCapacity\nStation Name (MWh)")
    content = content.replace(
        b"1. Synthetic Site A\n     (Alias A)    100", b"1. Synthetic Site    100\n     A (Alias A)"
    )
    rows = parse_ntpc_ifb(content, lot=1)
    assert rows[0]["source_name"] == "Synthetic Site A (Alias A)"
    assert rows[0]["tender_battery_energy_mwh"] == 100


def test_multiple_capacity_tokens_fail_instead_of_silent_selection() -> None:
    content = fixture().replace(b"(Alias A)    100", b"(Alias A)    100\n              200")
    with pytest.raises(ValueError, match="Ambiguous"):
        parse_ntpc_ifb(content, lot=1)
