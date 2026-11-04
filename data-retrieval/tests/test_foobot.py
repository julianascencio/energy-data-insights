"""Synthetic parser contracts; network-independent."""

import json

import pytest

from energy_data_retrieval.foobot import parse_foobot


def payload():
    panels = []
    for test, offset in [("T1", 0), *[("T2", o) for o in (-60, -30, 0, 30, 60)]]:
        panels.append(
            dict(
                test=test,
                offset=offset,
                x=[-60, 0, 60],
                truth=[18, 20, 21],
                median=[18, 20, 21],
                lo=[17, 19, 20],
                hi=[19, 21, 22],
                setpoint=[18, 21, 21],
                cmd=[0, 1, 1],
            )
        )
    return [dict(date="2024-01-01", threshold=20.75, panels=panels)]


def encode(data):
    return "window.TIMESTRAL_EXPERIMENT = " + json.dumps(data) + ";"


def test_valid_and_no_execution():
    assert len(parse_foobot(encode(payload()))) == 6
    with pytest.raises(ValueError):
        parse_foobot(encode(payload()) + "alert(1)")
    with pytest.raises(ValueError):
        parse_foobot("arbitrary code")


@pytest.mark.parametrize("damage", ["duplicate", "missing", "setpoint", "nan", "quantile"])
def test_invalid(damage):
    data = payload()
    if damage == "duplicate":
        data *= 2
    elif damage == "missing":
        data[0]["panels"].pop()
    elif damage == "setpoint":
        data[0]["panels"][1]["setpoint"][0] = 19
    elif damage == "nan":
        data[0]["panels"][0]["truth"][0] = float("nan")
    else:
        data[0]["panels"][0]["lo"][0] = 50
    with pytest.raises(ValueError):
        parse_foobot(encode(data))
