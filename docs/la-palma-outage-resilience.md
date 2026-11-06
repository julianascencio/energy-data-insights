# La Palma outage: critical-load BESS energy-adequacy screen

**Dated event:** 2 November 2026; **source:** Red Electrica,
[Electricity supply restored in La Palma](https://www.ree.es/en/news/press-release/2026/11/electricity-supply-restored-in-la-palma).
The operator reports an island-system blackout beginning at **06:38** and
restoration of *all* supply by **10:26** local Canary Islands time. The
**228-minute restoration interval** is not a verified per-customer interruption
duration or a sampled power series. The operator states that causes were still
under investigation at publication. No power, energy-not-served, or wind/PV
generation measurements were taken from this news item.

## Business case

Screen the **usable energy capacity (MWh)** of a correctly designed,
grid-independent, islandable BESS serving a hypothetical critical facility during
an outage as long as the observed restoration interval. Compare no local
generation (conservative) with an explicitly **synthetic** conditional
solar-and-wind scenario, and use a zero-storage baseline.

## Inputs and reproducibility

- **Observed:** 2026-11-02 local start/end times only, from the Red Electrica
  primary press release. Access checked 2026-11-06; time difference 228 minutes.
- **Modeled, not observed:** constant 0.50 MW critical load, 0.65 MW discharge
  rating, 80% starting SOC, 90.25% round-trip efficiency (95% each direction),
  3-minute resolution, assumed conditional PV/wind output.
- **Method:** `energy_methods.outage_resilience.minimum_islanded_capacity`
  reuses `simulate_hybrid`, including inverter power, state-of-charge,
  charging/discharging efficiency, and direct renewable supply. A bounded
  bisection finds the least modeled usable battery capacity meeting all
  energy demand within 1e-9 MWh. It raises an error if inverter power or the
  imposed capacity bound makes full service impossible.
- **Baseline:** no solar, no wind, no storage. The conservative no-generation
  required energy is calculated independently as
  `0.50 MW * (228 / 60) hours / (0.80 * 0.95) = 2.50 usable MWh`.
- **Outputs:** comparison plot of critical-load energy served versus battery
  usable energy capacity, plus calculated capacity thresholds.

Run from an installed repository checkout (no credentials or live requests):

```bash
uv sync --locked --all-packages
uv run --no-sync python examples/analysis/plot_la_palma_outage_resilience.py
uv run --no-sync pytest methods/tests/test_outage_resilience.py
```

## Physical, scientific and business limitations

This is **energy-only, deterministic, synthetic screening**, not a design
certification, a grid restoration simulation, or an estimate of avoided customer
outages on La Palma. Grid-following solar or wind plants do not automatically
operate in an outage. Achieving the displayed coverage requires independent
islanding/transfer equipment, suitable grid-forming and black-start capability,
protection coordination, inverter surge performance, load prioritization,
availability and operating reserve. None is validated by this code.
The assumed 80% SOC is not a guaranteed pre-outage reserve. The modeled capacity
is usable DC-equivalent energy, not battery nameplate, lifetime or warranted
discharge energy. Weather during the storm, renewable resource correlation,
degradation, minimum SOC, cycling limits, capex and downtime economics remain
unmodeled. The published timeline is a restoration interval, **not** measured
energy not supplied. Do not use this as an asset investment or safety decision
without site measurements and qualified engineering design.

**Next step:** connect licensed per-facility critical-load data and outage
telemetry, calibrated PV/wind observations with storm derating, and formal
island-mode feasibility and reliability risk models.
