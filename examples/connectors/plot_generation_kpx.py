"""South Korea: plan and retrieve hourly regional solar generation
==================================================================

Prepare bounded requests to Korea Power Exchange's official regional solar
generation API. The default example is an **offline request plan**, not measured
or simulated Korean power. It downloads no observations and needs no key.

For actual observations, apply for the `official data.go.kr service
<https://www.data.go.kr/data/15103243/openapi.do>`_, set the decoded service key in
``KPX_API_KEY`` locally, and run this script with ``ENERGY_DATA_INSIGHTS_LIVE=1``.

The data covers market-participating solar generators, not all Korean PV.
It reports hourly **MWh**, and can include coupled ESS output. Trading hours
01-24 label hour ends in Korea. Settlement revisions can change prior values.
"""

import os
from datetime import date

import matplotlib.pyplot as plt

from energy_data_retrieval.sources.kpx import KPX_HOSTS, KPXClient, solar_requests
from energy_data_retrieval.transport import HTTPClient

# %%
# 1. Inspect a credential-free bounded request plan
# -------------------------------------------------
start, end = date(2024, 9, 1), date(2024, 9, 7)
plans = solar_requests(start, end)
print("First-page plan:", plans[0])
print("Initial daily requests:", len(plans))
print("Further pages, when needed, count against the client's total request limit.")

# %%
# 2. Fetch only when live access is explicitly enabled
# ----------------------------------------------------
# Keys are passed through the transport's secret mapping. The returned request
# records contain public parameters, retrieval timestamps and response hashes.
if os.environ.get("ENERGY_DATA_INSIGHTS_LIVE") == "1":
    with HTTPClient(KPX_HOSTS) as http:
        result = KPXClient.from_environment(http).solar_generation(start, end)
    observations = result.frame
    if observations.empty:
        raise ValueError("KPX returned no observations for this interval")
    pivot = observations.pivot(index="timestamp", columns="area", values="value")
    pivot.plot(
        figsize=(10, 5),
        ylabel="Hourly solar generation (MWh)",
        xlabel="Interval start (UTC)",
        title="Actual market-participating Korean regional solar",
    )
    plt.tight_layout()
    plt.show()
else:
    fig, ax = plt.subplots(figsize=(8, 4), layout="constrained")
    labels = [plan["tradeYmd"][-4:] for plan in plans]
    ax.bar(labels, [1] * len(plans), color="#4b779c")
    ax.set(
        xlabel="Korean trading date (MMDD)",
        ylabel="Initial API requests",
        title="Offline KPX plan: zero observations downloaded",
        ylim=(0, 1.4),
    )
    ax.set_yticks([0, 1])
    plt.show()

# %%
# 3. Interpret the retrieved interval labels
# ------------------------------------------
# Hour 01 on 1 September means 00:00-01:00 Asia/Seoul, represented by the UTC
# interval start 31 August 15:00 and end 16:00. Hour 24 ends at the next midnight.
# A nighttime value is not automatically erroneous: the source can include ESS.
# Missing regions/hours remain absent rather than becoming zero generation.
