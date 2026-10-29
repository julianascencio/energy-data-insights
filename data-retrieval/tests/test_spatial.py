"""Geographic boundary cases and source-preserving station candidate ranking."""

from __future__ import annotations

from copy import deepcopy
from math import pi

import numpy as np
import pandas as pd
import pytest

from energy_data_retrieval.spatial import (
    EARTH_MEAN_RADIUS_KM,
    MAX_DISTANCE_KM,
    haversine_distance_km,
    nearby_stations,
)


def catalogue() -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "station_id": ["far", "b", "a", "a", "missing", "invalid"],
            "source": ["noaa", "noaa", "noaa", "aemet", "aemet", "dwd"],
            "latitude": [0.0, 0.0, 0.0, 0.0, np.nan, 91.0],
            "longitude": [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "source:quality": ["raw", "good", "unknown", "unchecked", "", ""],
        },
        index=[9, 8, 8, 4, 3, 2],
    )
    frame.attrs = {"native_metadata": {"provider_note": ["preserve"]}}
    return frame


def test_distances_match_known_spherical_arcs_in_kilometres() -> None:
    distance = haversine_distance_km(0, 0, [0, 0, 90, 0], [0, 90, 123, 180])
    np.testing.assert_allclose(
        distance,
        [0, pi * EARTH_MEAN_RADIUS_KM / 2, pi * EARTH_MEAN_RADIUS_KM / 2, MAX_DISTANCE_KM],
        atol=1e-10,
    )


def test_antimeridian_uses_short_arc_and_equivalent_meridians_are_identical() -> None:
    distance = haversine_distance_km(0, 179.5, [0], [-179.5])
    assert distance[0] == pytest.approx(pi * EARTH_MEAN_RADIUS_KM / 180)
    assert haversine_distance_km(15, 180, [15], [-180])[0] == 0


def test_poles_do_not_depend_on_longitude_and_antipodes_are_finite() -> None:
    np.testing.assert_array_equal(haversine_distance_km(90, 0, [90, 90], [-180, 98]), [0, 0])
    np.testing.assert_allclose(
        haversine_distance_km(90, 42, [-90, -90], [0, 180]), [MAX_DISTANCE_KM] * 2
    )
    assert np.isfinite(haversine_distance_km(28.5, -16.5, [-28.5], [163.5])).all()


@pytest.mark.parametrize(
    ("latitude", "longitude"),
    [(91, 0), (-91, 0), (0, 181), (0, -181), (np.nan, 0), (0, np.inf), (True, 0)],
)
def test_invalid_query_coordinates_fail_even_with_empty_catalogue(
    latitude: float, longitude: float
) -> None:
    with pytest.raises(ValueError):
        haversine_distance_km(latitude, longitude, [], [])
    with pytest.raises(ValueError):
        nearby_stations(catalogue().iloc[:0], latitude, longitude)


@pytest.mark.parametrize(
    ("latitudes", "longitudes"),
    [([np.nan], [0]), ([0], [np.inf]), ([91], [0]), ([0], [181]), ([0], []), ([[0]], [[0]])],
)
def test_distance_arrays_require_finite_valid_aligned_vectors(
    latitudes: list, longitudes: list
) -> None:
    with pytest.raises(ValueError):
        haversine_distance_km(0, 0, latitudes, longitudes)


def test_ranking_preserves_native_fields_and_attributes_without_mutating_input() -> None:
    source = catalogue()
    original = source.copy(deep=True)
    attributes = deepcopy(source.attrs)
    result = nearby_stations(source, 0, 0, radius_km=200, limit=2)
    assert list(zip(result["source"], result["station_id"], strict=True)) == [
        ("aemet", "a"),
        ("noaa", "a"),
    ]
    assert result["rank"].tolist() == [1, 2]
    assert result["distance_km"].tolist() == [0, 0]
    assert result["source:quality"].tolist() == ["unchecked", "unknown"]
    assert result.attrs["native_metadata"] == attributes["native_metadata"]
    assert result.attrs["spatial_search"] == {
        "distance_method": "haversine_mean_radius_sphere",
        "earth_radius_km": EARTH_MEAN_RADIUS_KM,
        "latitude": 0.0,
        "longitude": 0.0,
        "radius_km": 200.0,
        "limit": 2,
        "input_station_count": 6,
        "invalid_coordinate_count": 2,
        "within_radius_count": 4,
        "returned_station_count": 2,
        "truncated": True,
    }
    result.attrs["native_metadata"]["provider_note"].append("only in result")
    pd.testing.assert_frame_equal(source, original)
    assert source.attrs == attributes


def test_duplicate_station_records_remain_distinct_in_stable_original_order() -> None:
    frame = pd.DataFrame(
        {"station_id": ["x", "x"], "latitude": [0, 0], "longitude": [0, 0], "record": [2, 1]}
    )
    result = nearby_stations(frame, 0, 0)
    assert result["record"].tolist() == [2, 1]
    assert result["rank"].tolist() == [1, 2]


def test_radius_is_inclusive_and_limit_applies_after_geographic_filter() -> None:
    frame = catalogue().iloc[:4]
    boundary = float(haversine_distance_km(0, 0, [0], [1])[0])
    inclusive = nearby_stations(frame, 0, 0, radius_km=boundary, limit=20)
    assert inclusive["station_id"].tolist() == ["a", "a", "b", "far"]
    outside = nearby_stations(frame, 0, 0, radius_km=boundary - 1e-6, limit=20)
    assert "far" not in outside["station_id"].tolist()
    assert outside.attrs["spatial_search"]["within_radius_count"] == 3
    assert not outside.attrs["spatial_search"]["truncated"]


def test_nearby_search_crosses_antimeridian() -> None:
    frame = pd.DataFrame(
        {"station_id": ["near", "far"], "latitude": [0, 0], "longitude": [-179.5, 170]}
    )
    result = nearby_stations(frame, 0, 179.5, radius_km=120)
    assert result["station_id"].tolist() == ["near"]


def test_unusable_catalogue_coordinates_are_counted_and_numeric_strings_are_preserved() -> None:
    frame = pd.DataFrame(
        {
            "station_id": list("abcdefgh"),
            "latitude": ["0.0", None, "missing", np.inf, 0, 0, True, 1 + 2j],
            "longitude": ["0.0", 0, 0, 0, 181, None, 0, 0],
        }
    )
    result = nearby_stations(frame, 0, 0)
    assert result["station_id"].tolist() == ["a"]
    assert result.loc[0, "latitude"] == "0.0"
    assert result.attrs["spatial_search"]["invalid_coordinate_count"] == 7


@pytest.mark.parametrize("empty", [True, False])
def test_empty_or_entirely_invalid_catalogue_returns_typed_empty_result(empty: bool) -> None:
    frame = catalogue().iloc[:0] if empty else catalogue().iloc[4:]
    result = nearby_stations(frame, 0, 0)
    assert result.empty
    assert result["distance_km"].dtype == np.float64
    assert result["rank"].dtype == np.int64
    assert result.attrs["spatial_search"]["within_radius_count"] == 0
    assert result.attrs["spatial_search"]["invalid_coordinate_count"] == len(frame)
    assert not result.attrs["spatial_search"]["truncated"]


@pytest.mark.parametrize("radius", [0, -1, np.nan, np.inf, MAX_DISTANCE_KM + 1, True])
def test_invalid_radius_is_rejected(radius: float) -> None:
    with pytest.raises(ValueError, match="radius_km"):
        nearby_stations(catalogue(), 0, 0, radius_km=radius)


@pytest.mark.parametrize("limit", [0, -1, 100_001, 2.0, True])
def test_invalid_limit_is_rejected(limit: int) -> None:
    with pytest.raises(ValueError, match="limit"):
        nearby_stations(catalogue(), 0, 0, limit=limit)


def test_missing_duplicate_and_reserved_columns_are_rejected() -> None:
    with pytest.raises(ValueError, match="longitude"):
        nearby_stations(catalogue().drop(columns="longitude"), 0, 0)
    with pytest.raises(ValueError, match="unique"):
        nearby_stations(pd.concat([catalogue(), catalogue()[["latitude"]]], axis=1), 0, 0)
    for name in ("distance_km", "rank"):
        with pytest.raises(ValueError, match="reserved"):
            nearby_stations(catalogue().assign(**{name: 7}), 0, 0)


def test_full_sphere_radius_includes_antipodal_station() -> None:
    frame = pd.DataFrame({"station_id": ["antipode"], "latitude": [0], "longitude": [180]})
    result = nearby_stations(frame, 0, 0, radius_km=MAX_DISTANCE_KM)
    assert result["station_id"].tolist() == ["antipode"]
    assert result.loc[0, "distance_km"] == MAX_DISTANCE_KM
