"""
One site: climate metadata and practical next steps
===================================================

Look up KGPV, JRC, ML21 and PVCZ context for a coordinate near **Rengo, Chile**.
This is an illustrative coordinate, not a surveyed PV plant. The offline bundle
keeps **all native columns** for nearby source rows, rather than only map labels.

Download the :download:`runnable site bundle <site_climate_examples.zip>` and
read :doc:`the site lookup guide </_generated/guides/site-climate>` for full
catalogue use, units, source access, tie handling and operational interpretation.
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from energy_analysis.climate_comparison.site import load_site_example, site_climate_profile

# %%
# One call returns four schemes and their metadata
# ------------------------------------------------
# The 50 km threshold is an explicit search limit, not a claim of scientific
# representativeness. The query never selects a farther complete row to hide
# missing data, and it reports ambiguous labels at equally nearest source points.

catalogues, manifest, model = load_site_example(Path("."))
latitude, longitude = manifest["site"]["latitude"], manifest["site"]["longitude"]
profile = site_climate_profile(
    latitude,
    longitude,
    catalogues=catalogues,
    source_metadata=manifest["sources"],
    jrc_model=model,
    radius_km=50,
)
rows = []
for scheme, result in profile["classifications"].items():
    rows.append(
        {
            "scheme": scheme,
            "status": result["status"],
            "code": result["code"],
            "distance_km": result["distance_km"],
            "period": result["source"]["period"],
            "resolution": result["source"]["resolution"],
        }
    )
print(pd.DataFrame(rows).to_string(index=False))

# %%
# Inspect where the metadata comes from
# -------------------------------------
# KGPV and ML21 share the same reference workbook here, so their source markers
# overlap. PVCZ can contain several records at the same rounded coordinates;
# the returned candidates preserve all such rows. No marker is moved to the site.

fig, ax = plt.subplots(figsize=(9, 6), layout="constrained")
ax.scatter(longitude, latitude, marker="*", s=220, c="#111827", label="Requested site", zorder=5)
colors = {"JRC": "#d97706", "KGPV": "#15803d", "ML21": "#2563eb", "PVCZ": "#9333ea"}
for index, (scheme, result) in enumerate(profile["classifications"].items()):
    for candidate in result["candidates"]:
        ax.scatter(
            candidate["lon"],
            candidate["lat"],
            s=70 + index * 25,
            facecolors="none",
            edgecolors=colors[scheme],
            linewidths=2,
        )
        ax.plot(
            [longitude, candidate["lon"]],
            [latitude, candidate["lat"]],
            color=colors[scheme],
            alpha=0.5,
            linewidth=0.8,
        )
    if result["candidates"]:
        candidate = result["candidates"][0]
        ax.annotate(
            f"{scheme}: {result['code']} ({result['distance_km']:.1f} km)",
            (candidate["lon"], candidate["lat"]),
            xytext=(10, 12 + index * 16),
            textcoords="offset points",
            color=colors[scheme],
            fontsize=9,
        )
ax.set(
    xlabel="Longitude (°)",
    ylabel="Latitude (°)",
    title=(
        "Rengo site and nearest source coordinates\n"
        "Point distances do not establish local representativeness"
    ),
)
ax.margins(0.4)
ax.grid(alpha=0.2)
ax.legend(loc="lower left")
plt.show()

# %%
# Inspect the complete fields and provenance
# ------------------------------------------
# Each entry contains its label, all source-row fields, units, source URL/hash,
# period, native resolution and interpretation. The JRC entry also records the
# frozen model, centroid meaning and whether inputs exceed its training range.
# Missing numerical values serialize as JSON null, never invented zeros.

for scheme, result in profile["classifications"].items():
    print(f"\n{scheme}: {result['label']}")
    print("Source:", json.dumps(result["source"], ensure_ascii=False, indent=2))
    for candidate in result["candidates"]:
        details = [
            {"field": name, "value": value, "units": result["field_metadata"][name]["units"]}
            for name, value in candidate.items()
        ]
        print(pd.DataFrame(details).to_string(index=False))

# Save the complete record when running locally:
# Path("my_site_climate.json").write_text(json.dumps(profile, indent=2, allow_nan=False))

# %%
# Use the metadata: screen mounting-related thermal stress
# --------------------------------------------------------
# PVCZ supplies modelled temperatures for both open-rack and close-roof mounting
# at several activation energies. Compare the two source values at 1.1 eV to
# decide whether mounting deserves a dedicated thermal study. This is a source
# model comparison at the selected grid point, not a measured temperature change
# or a degradation-rate prediction for this site.

pvcz_context = profile["classifications"]["PVCZ"]
if pvcz_context["status"] == "matched" and len(pvcz_context["candidates"]) == 1:
    native = pvcz_context["candidates"][0]
    rack = native["T_equiv_rack_1p1eV"]
    roof = native["T_equiv_roof_1p1eV"]
    if rack is not None and roof is not None:
        fig, ax = plt.subplots(figsize=(7, 4), layout="constrained")
        bars = ax.bar(["Open rack", "Close roof"], [rack, roof], color=["#2563eb", "#d97706"])
        ax.bar_label(bars, fmt="%.1f °C", padding=4)
        ax.set(
            ylabel="Arrhenius-equivalent module temperature (°C)",
            ylim=(0, max(rack, roof) * 1.2),
            title="Use the source metadata: mounting stress comparison\n"
            "PVCZ modelled source point, 2010-2018, activation energy 1.1 eV",
        )
        plt.show()
        print(f"Source-model close-roof minus open-rack temperature: {roof - rack:.1f} °C")
        print("Next: model the actual mounting and ventilation with local weather.")

# %%
# What to do with these results
# -----------------------------
# * **KGPV:** group sites into climate peers before a fleet performance comparison.
# * **JRC:** examine irradiation and module-temperature conditions, then use local
#   weather and the real tilt/mounting for a yield or thermal-loss model.
# * **ML21:** stratify benchmarking by PV-climate family; keep technology, design
#   and data-quality differences under control.
# * **PVCZ:** use thermal/humidity stress as input to a qualification or inspection
#   plan, then confirm mechanisms with module and field evidence.
# * **Degradation rate:** supply module calibration and hourly temperature/RH/UV
#   stresses to the separate degradation model. A class is not a %/year rate.
#
# Inspect sources before acting. These products use different periods and model
# assumptions; their IDs have no cross-scheme numeric equivalence. If any entry
# is missing, outside the radius or ambiguous, resolve it with appropriate local
# data instead of widening the search just to obtain a label.

for scheme, result in profile["classifications"].items():
    print(f"{scheme}: {result['use']} {result['limitation']}")
for step in profile["next_steps"]:
    print("Next:", step)

# %%
# Query a different site
# ----------------------
# The included files are a bounded Rengo subset, so arbitrary sites require full
# source catalogues. ``site_climate_profile`` accepts the existing JRC/ML21/PVCZ
# reader outputs; the guide shows the download/read calls and exact metadata.
# The same query with radius_km=0.1 shows an honest no-nearby-source result.

strict = site_climate_profile(
    latitude,
    longitude,
    catalogues=catalogues,
    source_metadata=manifest["sources"],
    jrc_model=model,
    radius_km=0.1,
)
print({name: entry["status"] for name, entry in strict["classifications"].items()})
