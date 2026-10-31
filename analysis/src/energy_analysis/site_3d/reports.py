"""Static/interactive views and portable mesh exports with explicit model metadata."""

from __future__ import annotations

import html
import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from energy_methods.pv_site_3d import PVSiteScene

REFERENCE_IDS = ("plotly_mesh3d", "plotly_html_export")


def scene_metadata(scene: PVSiteScene) -> dict[str, Any]:
    """Separate measured/source geometry from explicit mounting scenarios."""
    clearance = np.concatenate(
        [m.vertices_m[:, 2] - m.terrain_at_vertices_m for m in scene.modules]
    )
    return {
        "schema_version": "1.0",
        "interpretation": "Scenario geometry, not a surveyed as-built model",
        "input_module_count": scene.input_module_count,
        "modelled_module_count": len(scene.modules),
        "modelled_table_count": len({m.table_id for m in scene.modules}),
        "rejected_modules": list(scene.rejected_modules),
        "frame": asdict(scene.frame),
        "horizontal_crs_wkt": scene.frame.crs.to_wkt(),
        "axes": "X east, Y north, Z up; metres relative to frame origin",
        "vertical_datum": scene.vertical_datum,
        "bounds_wgs84": scene.bounds_wgs84,
        "display_grid_shape": scene.display_grid_shape,
        "display_interpolation": "Bilinear; no new terrain information or nodata infill",
        "table_mounting": {k: asdict(v) for k, v in scene.table_mounting.items()},
        "vertex_clearance_range_m": [float(clearance.min()), float(clearance.max())],
        "evidence": {
            "horizontal_positions": "Input image candidates or supplied footprints",
            "terrain_heights": "Sampled elevation source; datum retained without conversion",
            "tilt_clearance": "Explicit scenario inputs, not inferred from RGB",
            "module_extent": (
                "Input horizontal projection retained; slant dimensions depend on tilt"
            ),
        },
        "limitations": [
            "No photogrammetric depth recovery",
            "No survey or structural validation",
            "No generation, occlusion or shading calculation",
            "Clearance checked at corners, edge midpoints and centres only",
        ],
    }


def _extents(scene: PVSiteScene) -> tuple[np.ndarray, np.ndarray]:
    xyz = np.vstack([scene.terrain.vertices_m, scene.module_mesh.vertices_m])
    return xyz.min(axis=0), xyz.max(axis=0)


def plot_site_scene(
    scene: PVSiteScene, *, title: str = "PV site scenario", attribution: str = ""
) -> Any:
    """Static metric 3D overview; elevation is not vertically exaggerated."""
    fig = plt.figure(figsize=(13, 7))
    ax = cast(Axes3D, fig.add_axes((0.04, 0.12, 0.92, 0.74), projection="3d"))
    xyz = scene.terrain.vertices_m
    terrain_faces = xyz[scene.terrain.triangles]
    z = terrain_faces[:, :, 2].mean(axis=1)
    colours = plt.colormaps["gist_earth"]((z - z.min()) / max(float(np.ptp(z)), 1) * 0.35 + 0.43)
    # One collection permits per-face depth sorting between terrain and modules.
    faces = [*terrain_faces, *(m.vertices_m for m in scene.modules)]
    module_colours = np.tile([0.06, 0.30, 0.43, 1], (len(scene.modules), 1))
    edges = np.vstack(
        [
            np.tile([0, 0, 0, 0], (len(terrain_faces), 1)),
            np.tile([0.65, 0.82, 0.88, 1], (len(scene.modules), 1)),
        ]
    )
    widths = np.r_[np.zeros(len(terrain_faces)), np.full(len(scene.modules), 0.18)]
    collection = Poly3DCollection(
        faces,
        facecolors=np.vstack([colours, module_colours]),
        edgecolors=edges,
        linewidths=widths,
        antialiased=False,
    )
    ax.add_collection3d(collection)
    low, high = _extents(scene)
    span = np.maximum(high - low, 0.1)
    ax.set(
        xlim=(low[0], high[0]),
        ylim=(low[1], high[1]),
        zlim=(low[2], high[2]),
        xlabel="East (m)",
        ylabel="North (m)",
        zlabel="Relative up (m)",
    )
    ax.zaxis.set_ticks([low[2], high[2]])
    ax.zaxis.set_ticklabels([f"{low[2]:.1f}", f"{high[2]:.1f}"])
    ax.set_box_aspect(span, zoom=1.22)
    ax.view_init(elev=30, azim=-115)
    fig.suptitle(title, fontsize=19, y=0.97)
    fig.text(
        0.5,
        0.91,
        f"True metric scale · Z origin {scene.frame.elevation_origin_m:g} m "
        f"{scene.vertical_datum} · assumed table planes",
        ha="center",
        fontsize=11,
    )
    fig.text(0.02, 0.02, attribution, fontsize=7, wrap=True)
    return fig


def _interactive_figure(scene: PVSiteScene, title: str) -> go.Figure:
    ground = scene.terrain
    fig = go.Figure(
        go.Mesh3d(
            x=ground.vertices_m[:, 0],
            y=ground.vertices_m[:, 1],
            z=ground.vertices_m[:, 2],
            i=ground.triangles[:, 0],
            j=ground.triangles[:, 1],
            k=ground.triangles[:, 2],
            intensity=ground.vertices_m[:, 2] + scene.frame.elevation_origin_m,
            colorscale=[[0, "#b3bb8b"], [0.5, "#8b956a"], [1, "#b6a18c"]],
            showscale=False,
            name="Elevation surface",
            showlegend=True,
            hovertemplate=(
                "Elevation surface<br>East %{x:.1f} m<br>North %{y:.1f} m"
                "<br>Relative up %{z:.2f} m<extra></extra>"
            ),
            lighting={"ambient": 0.65, "diffuse": 0.7, "specular": 0.05, "roughness": 1},
        )
    )
    mesh = scene.module_mesh
    labels = [
        f"{html.escape(m.id)} · table {html.escape(m.table_id)}"
        for m in scene.modules
        for _ in range(4)
    ]
    fig.add_trace(
        go.Mesh3d(
            x=mesh.vertices_m[:, 0],
            y=mesh.vertices_m[:, 1],
            z=mesh.vertices_m[:, 2],
            i=mesh.triangles[:, 0],
            j=mesh.triangles[:, 1],
            k=mesh.triangles[:, 2],
            color="#125c86",
            flatshading=True,
            name="Candidate module surfaces",
            showlegend=True,
            text=labels,
            hovertemplate=(
                "%{text}<br>East %{x:.2f} m<br>North %{y:.2f} m"
                "<br>Modelled up %{z:.2f} m<extra></extra>"
            ),
            lighting={"ambient": 0.55, "diffuse": 0.8, "specular": 0.25, "roughness": 0.6},
        )
    )
    outlines = np.concatenate(
        [np.vstack([m.vertices_m, m.vertices_m[0], [np.nan] * 3]) for m in scene.modules]
    )
    fig.add_trace(
        go.Scatter3d(
            x=outlines[:, 0],
            y=outlines[:, 1],
            z=outlines[:, 2],
            mode="lines",
            line={"color": "#abd3e1", "width": 1},
            name="Module edges",
            showlegend=True,
            hoverinfo="skip",
        )
    )
    low, high = _extents(scene)
    span = np.maximum(high - low, 0.1)
    ratios = 1.8 * span / span.max()

    def aspect(factor: float) -> dict[str, float]:
        return {"x": float(ratios[0]), "y": float(ratios[1]), "z": float(ratios[2] * factor)}

    cameras = [
        ("Oblique", {"x": 1.2, "y": -1.5, "z": 1.0}),
        ("Top", {"x": 0, "y": -0.01, "z": 2.3}),
        ("Low angle", {"x": 0.5, "y": -2, "z": 0.25}),
    ]
    fig.update_layout(
        title={"text": html.escape(title), "font": {"size": 18}},
        margin={"l": 0, "r": 0, "b": 0, "t": 100},
        paper_bgcolor="#f4f7f9",
        font={"family": "Arial, sans-serif", "color": "#173042"},
        scene={
            "aspectmode": "manual",
            "aspectratio": aspect(1),
            "camera": {"eye": cameras[0][1]},
            "xaxis": {"title": "East (m)"},
            "yaxis": {"title": "North (m)"},
            "zaxis": {
                "title": "Relative up (m)",
                "tickvals": [float(low[2]), float(high[2])],
                "tickformat": ".1f",
            },
        },
        legend={"orientation": "h", "y": -0.02, "x": 0.01},
        updatemenus=[
            {
                "type": "buttons",
                "direction": "right",
                "x": 0,
                "y": 1.08,
                "buttons": [
                    {"label": label, "method": "relayout", "args": [{"scene.camera.eye": eye}]}
                    for label, eye in cameras
                ],
            },
            {
                "type": "dropdown",
                "x": 1,
                "xanchor": "right",
                "y": 1.08,
                "buttons": [
                    {
                        "label": f"Vertical display x{factor}",
                        "method": "relayout",
                        "args": [{"scene.aspectratio": aspect(factor)}],
                    }
                    for factor in (1, 3, 5)
                ],
            },
        ],
        uirevision="pv-site-scene",
    )
    return fig


def write_scene_html(
    scene: PVSiteScene,
    path: str | Path,
    *,
    title: str = "PV site scenario",
    attribution: str = "",
    evidence_note: str = "",
) -> Path:
    """Write a self-contained offline Plotly viewer; no imagery or CDN calls required.

    Display exaggeration affects the camera aspect only. Exported coordinates
    retain metric Z. All externally supplied text is escaped before embedding.
    """
    path = Path(path)
    if path.exists():
        raise FileExistsError(path)
    figure = _interactive_figure(scene, title)
    plot = figure.to_html(
        full_html=False,
        include_plotlyjs=True,
        div_id="pv-site-scene",
        default_height="72vh",
        config={"responsive": True, "displaylogo": False, "scrollZoom": True},
    )
    assumptions = "; ".join(
        sorted(
            {
                f"{p.tilt_degrees:g}° tilt, {p.azimuth_degrees:g}° facing azimuth, "
                f"{p.minimum_clearance_m:g} m minimum sampled clearance"
                for p in scene.table_mounting.values()
            }
        )
    )
    page = (
        """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>"""
        + html.escape(title)
        + """</title><style>
body{margin:0;background:#f4f7f9;color:#173042;font:15px/1.5 Arial,sans-serif}
header,footer{padding:18px 28px;max-width:1300px;margin:auto}h1{font-size:26px;margin:0 0 8px}
p{margin:6px 0}.tag{font-size:12px;color:#5a6d79;text-transform:uppercase;letter-spacing:.08em}
small{color:#536673}main{padding:0 12px}footer{border-top:1px solid #dce4e9}
</style></head><body><header><div class="tag">Reproducible PV scene · scenario geometry</div><h1>"""
        + html.escape(title)
        + """</h1><p>"""
        + str(len(scene.modules))
        + """ candidate module surfaces · """
        + str(len({m.table_id for m in scene.modules}))
        + """ tables</p><p>Assumed mounting: """
        + html.escape(assumptions)
        + """</p><small>Drag to orbit; scroll to zoom. Toggle layers in the legend.
Default vertical display is x1.</small></header><main>"""
        + plot
        + """</main><footer><p>"""
        + html.escape(evidence_note)
        + """</p><p>Height reference: """
        + html.escape(scene.vertical_datum)
        + f"; local Z origin {scene.frame.elevation_origin_m:g} m"
        + """. Interpolated terrain adds no source resolution.
This is not a surveyed as-built model.</p><small>"""
        + html.escape(attribution)
        + """</small></footer></body></html>"""
    )
    path.write_text(page, encoding="utf-8")
    return path


def export_site_scene(
    scene: PVSiteScene,
    directory: str | Path,
    *,
    title: str = "PV site scenario",
    provenance: dict[str, Any] | None = None,
    attribution: str = "",
    evidence_note: str = "",
) -> Path:
    """Export open OBJ/MTL, complete local-coordinate JSON and an offline viewer.

    OBJ coordinates use metres, Z-up. Neither OBJ nor JSON converts orthometric
    heights to WGS84 ellipsoidal heights. JSON retains the georeference and IDs.
    """
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=False)
    metadata = scene_metadata(scene)
    document = {
        **metadata,
        "provenance": provenance or {},
        "attribution": attribution,
        "terrain": {
            "vertices_m": scene.terrain.vertices_m.tolist(),
            "triangles": scene.terrain.triangles.tolist(),
        },
        "modules": [
            {
                "id": m.id,
                "table_id": m.table_id,
                "vertices_m": m.vertices_m.tolist(),
                "terrain_at_vertices_m": m.terrain_at_vertices_m.tolist(),
            }
            for m in scene.modules
        ],
    }
    (destination / "scene.json").write_text(json.dumps(document, allow_nan=False) + "\n")
    (destination / "summary.json").write_text(
        json.dumps({**metadata, "provenance": provenance or {}}, indent=2, allow_nan=False) + "\n"
    )
    lines = [
        "# PV scenario mesh; metres; X east, Y north, Z up",
        f"# Relative Z origin: {scene.frame.elevation_origin_m} m; datum {scene.vertical_datum}",
        "# See scene.json for georeference, assumptions, evidence and source attribution",
        "mtllib site.mtl",
        "o terrain",
        "usemtl terrain",
    ]
    for v in scene.terrain.vertices_m:
        lines.append("v " + " ".join(f"{x:.8f}" for x in v))
    for face in scene.terrain.triangles:
        lines.append("f " + " ".join(str(int(i) + 1) for i in face))
    offset = len(scene.terrain.vertices_m)
    for index, module in enumerate(scene.modules):
        safe = re.sub(r"[^A-Za-z0-9_-]", "_", module.id)
        lines.extend([f"o module_{index:06d}_{safe}", "usemtl module"])
        lines.extend("v " + " ".join(f"{x:.8f}" for x in v) for v in module.vertices_m)
        lines.extend(
            ["f " + " ".join(str(offset + i + 1) for i in face) for face in ((0, 1, 2), (0, 2, 3))]
        )
        offset += 4
    (destination / "site.obj").write_text("\n".join(lines) + "\n")
    (destination / "site.mtl").write_text(
        "newmtl terrain\nKd 0.58 0.62 0.44\n\nnewmtl module\n"
        "Kd 0.07 0.36 0.53\nKs 0.25 0.25 0.25\nNs 32\n"
    )
    write_scene_html(
        scene,
        destination / "viewer.html",
        title=title,
        attribution=attribution,
        evidence_note=evidence_note,
    )
    (destination / "README.txt").write_text(
        "Open viewer.html in a WebGL-capable browser; no server/network is required.\n"
        "OBJ/MTL: import site.obj with Z-up and metre units, keeping site.mtl beside it.\n"
        "Meshes are surfaces, not solid modules or engineering structures.\n"
        "scene.json retains all vertices, triangles, IDs, local CRS and vertical reference.\n"
        "summary.json records assumptions and rejected footprints. "
        "No vertical datum conversion occurs.\n"
        "Changing the viewer vertical display does not alter exported heights.\n"
        + attribution
        + "\n"
    )
    return destination
