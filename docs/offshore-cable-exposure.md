# Offshore export-cable outage exposure: Norderney construction news

**Case date:** 6 November 2026 · **Technology:** Offshore wind transmission · **Evidence:** reported construction event + operator-reported planned aggregate connection capacity + industry cable-repair context + fully **synthetic** engineering scenarios.

## Evidence and why this study is relevant

On 4 November 2026, [Tagesschau reported](https://www.tagesschau.de/inland/regional/niedersachsen/pannen-bei-windkraft-anbindung-zwei-kabel-vor-norderney-beschaedigt,kabel-124.html) two cable damage incidents during installation near Norderney affecting the DolWin4 and BorWin4 grid connections. Repairs are planned for 2027. According to the report, **Amprion does not expect the incidents to delay the planned commissioning**. [Amprion's project page](https://www.amprion.net/Netzausbau/Unsere-Projekte/DolWin4-und-BorWin4/Projektfortschritt.html) states that the combined links will transport around **1.8 GW** of offshore wind from 2028. The supplied public information does **not** establish each affected cable's transfer limit or actual financial consequences. No actual generation was lost in 2026 because the connections were under construction.

For reliability context, [DNV](https://www.dnv.com/article/80-percent-of-insurance-claims-in-offshore-wind-are-related-to-subsea-cable-failures-how-can-the-industry-manage-these-risks/) reports industry loss-adjuster observations of an approximately 60-day average export-cable repair downtime. That industry number is **not** a probability, an estimate for DolWin4/BorWin4, or a guaranteed repair duration. See also [Gulski et al., *Renewable and Sustainable Energy Reviews* 151, 111580 (2021)](https://doi.org/10.1016/j.rser.2021.111580) for the role of cable topology, outages, repair delays and repair costs in offshore wind economics. Neither source supplies forecast failures at these German projects.

## Business question, method and outputs

If an offshore wind system hypothetically experienced a cable outage **after entering service**, how much energy could become non-exportable? What is the sensitivity to resource seasonality, outage duration and remaining transfer capacity? This informs contingency planning, redundancy discussions and inspection-value screening; it does **not** price an insurance policy or justify expected-annual-loss estimates without failure frequencies.

`energy_methods.offshore_cable_exposure.calculate_cable_exposure` takes one power series in MW averaged over a uniform time step, normal export capacity in MW and an explicitly bounded outage window with reduced capacity. For each interval:

```text
baseline_export_MW = min(available_wind_MW, normal_export_limit_MW)
outage_export_MW = min(available_wind_MW, outage_export_limit_MW)
additional_unexported_MWh = (baseline_export_MW - outage_export_MW) * dt_h
```

Only intervals inside the outage window use the reduced export limit. The method also reports available energy, baseline and outage exports, baseline and outage curtailment, and exact incremental lost export. Importantly, it reports **incremental** energy exposure, rather than mistakenly counting ordinary pre-existing curtailment as caused by the outage. Input validation rejects negative, infinite or NaN generation, invalid power limits and truncated outage windows. It works on hourly or subhourly uniformly spaced input.

## Runnable, reproducible gallery analysis

The [gallery source](../examples/analysis/plot_norderney_cable_exposure.py) runs offline with **no credentials** and uses a deterministic **synthetic** 400-day hourly wind waveform. A **hypothetical 900 MW** installed wind resource and **900 MW** normal export transfer represent an illustrative single system; the public 1.8 GW is the **combined planned capacity** and the study does not assert how it is split between cables. The illustrated energy realization value is **80 EUR/MWh assumed**, not a measured price or reported project revenue. Production is modeled before export; there are no wind speed measurements or turbine power curves.

From the repository root with its existing locked Python 3.13 workspace:

```bash
uv sync --locked --all-packages --group docs --python 3.13
uv run --no-sync pytest methods/tests/test_offshore_cable_exposure.py
MPLBACKEND=Agg uv run --no-sync python examples/analysis/plot_norderney_cable_exposure.py
uv run --no-sync sphinx-build -W --keep-going -b html docs docs/_build/html
```

Figures compare synthetic incremental energy not exported versus outage **starting day** for a 60-day event, and versus **duration** for a fixed start, each for 0% and 50% remaining transfer. Scenario ranges are **not** statistical uncertainty intervals and are not a Monte Carlo estimate of outage probabilities. With more defensible real input series, the method can be reused to quantify resource-timed exposure. The zero-outage baseline is an explicit check.

## Limitations / critical validation steps

- No 2026 operational outage or actual lost production is claimed. The damaged cables were being installed and the operator expects the projects' schedule to hold.
- The 900 MW example rating, waveform and €/MWh exposure conversion are **assumptions**; none are observed DolWin4/BorWin4 parameters.
- Repair time, probability of failure, insurance terms, compensation, prices and spare parts depend on the particular asset and are **not** inferred from the news report.
- This simple model treats export as a single equivalent limit. It omits AC/DC converter losses, N−1 topology, cable loading, offshore platform behavior, redispatch, congestion, alternate paths and capacity contracts. Partial export capacity is assumed, not proven available.
- Economic value is an **illustrative energy-price multiplication**; it is not contract revenue or expected loss. No project-cost or legal conclusions are supported.
- The waveform is deterministic and not an observation-based or stochastic weather forecast. Calibrate against metered generation with precise UTC timestamps and documented service/availability boundaries before site-level decision use.

**Potential follow-up:** connect a real hourly offshore wind production dataset, define independently sourced cable circuit configurations and contractual exposure, and integrate validated outage distributions only when enough operational evidence exists.
