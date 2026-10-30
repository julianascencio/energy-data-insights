"""Country topology, CRS, masking, resolution limits and clipped geometry."""

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest
import shapefile
import xarray as xr
from matplotlib.backends.backend_agg import FigureCanvasAgg
from pyproj import CRS, Transformer
from shapely import transform
from shapely.affinity import translate
from shapely.geometry import MultiPolygon, Polygon, box, mapping, shape

from energy_methods.country_boundaries import (
    CountryBoundary,
    CountrySelection,
    load_country_boundaries,
    write_country_boundaries,
)
from energy_methods.country_mapping import (
    clip_country_grid,
    country_grid,
    country_mask,
    plot_country_map,
    write_country_geojson,
)


def selection():
    mainland = Polygon([(0, 0), (4, 0), (4, 4), (0, 4)], holes=[[(1, 1), (1, 3), (3, 3), (3, 1)]])
    return CountrySelection(
        (
            CountryBoundary("AAA", "Alpha", MultiPolygon([mainland, box(6, 1, 7, 2)])),
            CountryBoundary("BBB", "Beta", box(8, 0, 10, 4)),
        )
    )


@pytest.mark.parametrize("suffix", [".shp", ".geojson"])
def test_boundary_roundtrip_islands_holes_selection_and_unknowns(tmp_path, suffix):
    original = selection()
    path = write_country_boundaries(original, tmp_path / f"countries{suffix}")
    selected = load_country_boundaries(path, ["alpha", "BBB", "AAA"])
    assert selected.codes == ("AAA", "BBB")  # Duplicate selectors do not duplicate area.
    assert selected.geometry.equals(original.geometry)
    assert len(selected.countries[0].geometry.geoms) == 2
    assert len(selected.countries[0].geometry.geoms[0].interiors) == 1
    assert load_country_boundaries(path, "Alpha").codes == ("AAA",)
    for query in ([], "Atlantis", [""]):
        with pytest.raises(ValueError):
            load_country_boundaries(path, query)
    if suffix == ".shp":
        assert all(path.with_suffix(s).exists() for s in (".shx", ".dbf", ".prj", ".cpg"))


def test_projected_shapefile_requires_crs_and_transforms_xy(tmp_path):
    polygon = box(-4, 40, -3, 41)
    projected = transform(
        polygon, Transformer.from_crs(4326, 3857, always_xy=True).transform, interleaved=False
    )
    path = tmp_path / "mercator.shp"
    with shapefile.Writer(str(path), shapeType=shapefile.POLYGON) as writer:
        writer.field("ADM0_A3", "C")
        writer.field("ADMIN", "C")
        writer.shape(mapping(projected))
        writer.record("AAA", "Alpha")
    with pytest.raises(ValueError, match="prj"):
        load_country_boundaries(path, "AAA")
    result = load_country_boundaries(path, "AAA", crs="EPSG:3857")
    np.testing.assert_allclose(result.geometry.bounds, polygon.bounds, atol=1e-10)
    path.with_suffix(".prj").write_text(CRS.from_epsg(3857).to_wkt())
    np.testing.assert_allclose(
        load_country_boundaries(path, "Alpha").geometry.bounds, polygon.bounds
    )


def test_aliases_and_ambiguous_names_fail(tmp_path):
    path = write_country_boundaries(selection(), tmp_path / "countries.geojson")
    data = json.loads(path.read_text())
    data["features"][0]["properties"]["ISO_A2"] = "AA"
    path.write_text(json.dumps(data))
    assert load_country_boundaries(path, "aa").codes == ("AAA",)
    data["features"][1]["properties"]["ADMIN"] = "Alpha"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="ambiguous"):
        load_country_boundaries(path, "Alpha")


def test_country_grid_masks_holes_islands_and_partial_cells():
    selected = selection()
    grid = country_grid(selected, resolution=0.5)
    centres = country_mask(grid.country_mask, selected, mode="center")
    assert centres.sel(lat=2.25, lon=2.25).item() is False  # Interior lake/hole.
    assert centres.sel(lat=1.25, lon=6.25).item() is True  # Detached island.
    assert centres.sel(lat=2.25, lon=5.25).item() is False
    # A cell can touch a country even when its centre is outside.
    assert grid.country_mask.sel(lat=0.25, lon=4.25).item() is True
    assert centres.sel(lat=0.25, lon=4.25).item() is False
    field = xr.full_like(grid.country_mask, 3, dtype=np.uint8).expand_dims(year=[2023])
    field.loc[{"lat": 0.25, "lon": 0.25}] = 0
    result = clip_country_grid(field, selected, nodata=0, mode="center")
    assert result.dtype == np.uint8 and result.sizes["year"] == 1
    assert result.sel(lat=0.25, lon=0.25).item() == 0
    assert result.sel(lat=2.25, lon=2.25).item() == 0
    # Zero-to-360 longitude grids normalize before matching countries.
    west = CountrySelection(
        tuple(
            CountryBoundary(c.code, c.name, translate(c.geometry, xoff=-10))
            for c in selected.countries
        )
    )
    field = field.assign_coords(lon=field.lon - 10)
    shifted = field.assign_coords(lon=field.lon % 360)
    xr.testing.assert_equal(country_mask(shifted, west), country_mask(field, west))


def test_boundary_points_limits_bounds_and_small_islands():
    selected = CountrySelection((CountryBoundary("AAA", "Alpha", box(0, 0, 0.1, 0.1)),))
    grid = country_grid(selected, resolution=0.5)
    assert min(grid.sizes.values()) == 2
    clipped = clip_country_grid(grid.country_mask, selected, nodata=0)
    assert min(clipped.sizes.values()) == 2  # Remains plottable/exportable after crop.
    points = xr.DataArray([[1]], dims=("lat", "lon"), coords={"lat": [0], "lon": [0]})
    assert country_mask(points, selected, mode="center").item()
    for spacing in (0, -1, np.nan, np.inf, 0.7, True, 1e-100):
        with pytest.raises(ValueError, match="resolution"):
            country_grid(selected, resolution=spacing)
    with pytest.raises(ValueError, match="maximum_cells"):
        country_grid(selection(), resolution=0.001, maximum_cells=100)
    with pytest.raises(ValueError, match="intersect"):
        country_grid(selected, bounds=(10, 10, 11, 11))
    with pytest.raises(ValueError, match="bounds"):
        country_grid(selected, bounds=(10, 10, 0, 11))


def test_split_antimeridian_supported_unsplit_invalid_geometries_rejected():
    split = CountrySelection(
        (
            CountryBoundary(
                "DAT", "Dateline", MultiPolygon([box(179, -2, 180, 0), box(-180, -2, -179, 0)])
            ),
        )
    )
    grid = country_grid(split, resolution=1)
    assert grid.country_mask.sel(lon=-179.5).any()
    assert grid.country_mask.sel(lon=179.5).any()
    assert not grid.country_mask.sel(lon=0.5).any()
    with pytest.raises(ValueError, match="antimeridian"):
        CountrySelection((CountryBoundary("DAT", "Dateline", box(-179, -2, 179, 0)),))
    with pytest.raises(ValueError, match="valid"):
        CountrySelection(
            (CountryBoundary("BAD", "Bad", Polygon([(0, 0), (1, 1), (1, 0), (0, 1)])),)
        )


def test_geojson_clips_partial_cells_and_preserves_missing_values(tmp_path):
    selected = CountrySelection(
        (CountryBoundary("TRI", "Triangle", Polygon([(0, 0), (2, 0), (0, 2)])),)
    )
    field = xr.DataArray(
        [[2.0, 3.0], [4.0, np.nan]],
        dims=("lat", "lon"),
        coords={"lat": [0.5, 1.5], "lon": [0.5, 1.5]},
    )
    path = write_country_geojson(
        field, selected, tmp_path / "risk.geojson", labels={2: "Low", 3: "Medium", 4: "High"}
    )
    features = json.loads(path.read_text())["features"]
    assert len(features) == 3
    assert sum(shape(f["geometry"]).area for f in features) == pytest.approx(2)
    assert all(selected.geometry.covers(shape(f["geometry"])) for f in features)
    assert [f["properties"]["label"] for f in features] == ["Low", "Medium", "High"]
    with pytest.raises(ValueError, match="maximum_features"):
        write_country_geojson(field, selected, tmp_path / "too-many.json", maximum_features=2)
    # Plot uses a polygon clip, not a rectangular extent or interpolated contours.
    fig, ax = plt.subplots()
    mesh = plot_country_map(field, selected, ax=ax)
    assert mesh.get_clip_path() is not None
    fig.canvas.draw()
    plt.close(fig)


def test_plot_leaves_country_holes_unpainted():
    from matplotlib.colors import ListedColormap

    selected = selection()
    grid = country_grid(selected, resolution=0.5)
    field = xr.ones_like(grid.country_mask, dtype=float)
    fig, ax = plt.subplots(figsize=(7, 4), dpi=100)
    plot_country_map(field, selected, ax=ax, cmap=ListedColormap(["#ff0000"]))
    ax.grid(False)
    fig.canvas.draw()
    assert isinstance(fig.canvas, FigureCanvasAgg)
    pixels = np.asarray(fig.canvas.buffer_rgba())

    def color(x, y):
        col, row = ax.transData.transform((x, y)).astype(int)
        return pixels[pixels.shape[0] - 1 - row, col, :3]

    assert (color(2.25, 2.25) > 240).all()  # Hole stays background, not raster/fill.
    assert color(0.75, 0.75).tolist() == [255, 0, 0]
    assert color(6.25, 1.25).tolist() == [255, 0, 0]  # Detached island is painted.
    plt.close(fig)
