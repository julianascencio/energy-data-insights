import pandas as pd
import pytest

from energy_data_retrieval.pvdeg import to_pvdeg_weather


def test_weather_adapter():
    frame = pd.DataFrame(
        {
            "temp_air": [20],
            "relative_humidity": [60],
            "wind_speed": [2],
            "ghi": [500],
            "dni": [600],
            "dhi": [100],
        },
        index=pd.date_range("2020-01-01", periods=1, tz="Atlantic/Canary"),
    )
    result = to_pvdeg_weather(frame)
    assert isinstance(result.index, pd.DatetimeIndex)
    assert str(result.index.tz) == "UTC"
    result.iloc[0, 0] = 30
    assert frame.iloc[0, 0] == 20
    with pytest.raises(ValueError, match="Missing"):
        to_pvdeg_weather(frame.drop(columns="ghi"))
    frame["relative_humidity"] = 101
    with pytest.raises(ValueError, match="bounds"):
        to_pvdeg_weather(frame)
