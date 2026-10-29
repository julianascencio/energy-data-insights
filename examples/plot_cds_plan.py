"""Plan ERA5 requests without downloading
======================================

Build bounded monthly CDS selections for a broad Tenerife bounding box.
This only creates request objects: it makes no API calls, needs no credentials
and does not imply that a request has been accepted by the provider.
"""

from datetime import date

import matplotlib.pyplot as plt

from energy_data_retrieval.sources.cds.era5 import era5_requests

requests = era5_requests(
    date(2020, 1, 1),
    date(2020, 3, 31),
    variables=["2m_temperature", "surface_solar_radiation_downwards"],
    area=(29.0, -17.0, 28.0, -16.0),
)
labels = [request.selection["month"][0] for request in requests]
counts = [len(request.selection["day"]) * len(request.selection["time"]) for request in requests]
fig, ax = plt.subplots(figsize=(7, 4), layout="constrained")
bars = ax.bar(labels, counts, color="#096b76")
ax.bar_label(bars, padding=3)
ax.set(
    xlabel="Month in 2020",
    ylabel="UTC time labels per variable",
    title="Offline ERA5 request plan (leap year)",
    ylim=(0, 850),
)
plt.show()
print(f"Planned {len(requests)} requests; downloaded 0 files.")
