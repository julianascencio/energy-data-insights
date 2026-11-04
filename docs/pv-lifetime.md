# PV reliability and lifetime over 30–50 years

This continuation adds six plots to the [2021 uncertainty study](degradation-uncertainty.md),
using **2025 field evidence** and **2026 modelling methods**. The
[runnable gallery](../auto_examples/analysis/plot_pv_lifetime_50_years.html)
shows measured module power, system loss rates, projections to year 50,
model-shape sensitivity, changing stress, and a 30–50-year threshold map.

## Newer research and what it supports

| Source | Contribution | Limit |
| --- | --- | --- |
| Özkalay et al. (2025), *Three decades, three climates: environmental and material impacts on the long-term reliability of photovoltaic modules*, EES Solar 1, 580–599. [DOI 10.1039/D4EL00040D](https://doi.org/10.1039/D4EL00040D), published online 30 May 2025. | Multi-decade Swiss system monitoring and laboratory measurements of aged modules; most modules in the paper retain over 80% nominal power after 30–35 years. | Selected older module designs and sites; no measured 50-year validation or universal warranty for modern technology. |
| Ravindrababu et al. (2026), *Development of a modular approach for photovoltaic module lifetime and reliability estimation*, Energy Reports 15, 109323. [DOI 10.1016/j.egyr.2026.109323](https://doi.org/10.1016/j.egyr.2026.109323), online 25 April 2026. [Institutional full text](https://publica-rest.fraunhofer.de/server/api/core/bitstreams/51732576-1c3a-4715-ba45-0c3e07e5e143/content). | MAPLE integrates empirical, mode-specific and multiscale models. We implement independent-mode multiplication, sigmoid retention and equivalent-time updates. | This implementation covers Eqs. 8, 10 and 13 only. Assumed parameters do not reproduce the full framework or establish a calibrated 50-year forecast. |
| Quest, Özkalay and Gassner (2024), shared data v1.0.0. [DOI 10.5281/zenodo.14524159](https://doi.org/10.5281/zenodo.14524159). | Source numerical cells for the 2025 study, independently downloadable and checksummed. | The archive predates the final paper and contains date, count and rate differences described below. |

## Source audit and measurement boundary

The packaged CSVs preserve all **32 module records** and **six system PLRs**
from the archive. Each value retains its source worksheet/cell address. We plot
22 rated field samples; six stored references are not field exposures, and four
Mont-Soleil samples lack numeric nameplate powers. Of those 22, fourteen have
at least 30 years of exposure according to the workbook dates. These form three
group-median anchors: Birg, Tiergarten SM55-HO and Möhlin.

Exposure is **dismantle year minus installation year**, in integer years. The
archive gives 16, 24, 25, 30, 31 and 37 years; we do not overwrite these with the
paper's summary of 30–35 years. It also has six Tiergarten SM55 and six HO
records, whereas paper section 3.2.1.1 describes five and seven. The archive
system PLRs differ slightly from the final text, for example −0.56 versus
−0.55%/year. No silent reassignment or correction is made. The unused EL sheet
contains cached `#REF!` entries; the extracted PM measurements are numeric.

Measured power is normalized to each workbook **nameplate**, not a measured
initial power. Nameplate tolerance, storage after removal, rounding of exposure
dates, selection of surviving modules and the unresolved archive differences
limit inference. The dataset supplies no complete failure/censoring histories.
Thus neither the sample fraction above 80% nor a power curve is a fleet survival
probability. System performance-ratio loss includes different effects from
module STC power loss; the two are plotted separately and never pooled.

The dataset is CC-BY-4.0 according to Zenodo metadata; the paper is separately
CC-BY-3.0. Attribution, original archive MD5/SHA256, workbook hashes, extracted
table hashes, access date and changes are retained in `data/provenance.json`.
The packaged CSVs are small attributed numerical extracts, not copies of the
workbooks or paper figures.

## Projection methods

For measured group median $p_a$ at exposure $a$, two explicitly assumed
continuations are plotted only from $a$ through year 50:

$$d=(1-p_a)/a,\qquad p_L(t)=p_a-d(t-a),$$

$$k=-\log(p_a)/a,\qquad p_E(t)=p_a\exp[-k(t-a)].$$

These are one-point, average-to-date scenarios. Neither estimates a measured
instantaneous degradation rate. No invented historical trace, confidence band
or age-30 value is supplied for a group measured only at a later age.

For the new mode-specific method, MAPLE Eq. 10 gives

$$p(D;B)=\frac{1+e^{-B}}{1+e^{D-B}},$$

where constant stress has $D=rt$. Its inverse is

$$D(p;B)=\log[1+e^B(1-p)]-\log p.$$

At each interval, the previous retained power is mapped to an equivalent
exposure under the **current** shape parameter, then $r_i\Delta t_i$ is added.
For constant $B$, this reduces to cumulative exposure $\sum_i r_i\Delta t_i$.
It does not substitute the newest rate into $r(t)t$, which can falsely restore
lost power after stress falls. Computation uses logarithms for numerical
stability; zero rate pauses damage. Eq. 8 combines independent mode power
fractions by multiplication. Dependence, interactions, stochastic failures,
repowering and replacements are not modelled.

The shape comparison assumes 90% power at year 30 and B=2, 4 or 8; it is not
calibrated to Swiss samples. The stress comparison multiplies sigmoid corrosion
(B=4) by background retention $e^{-0.001t}$, choosing the initial corrosion rate
to reach 90% combined power at year 30. Subsequent corrosion-rate multipliers
are 1 throughout, 1.5 after year 30, or 2 during years 30–40. These are stress
tests, not climate forecasts. The monthly time step is 1/12 year.

## What the 30–50-year plots show

| Hypothetical curve, all 90% at year 30 | Year 40 | Year 50 | 80% crossing within the horizon |
| --- | ---: | ---: | --- |
| Linear | 86.67% | 83.33% | Not reached by 50 |
| Exponential | 86.89% | 83.90% | Not reached by 50 |
| Sigmoid, B=2 | 85.64% | 80.77% | Not reached by 50 |
| Sigmoid, B=4 | 81.23% | 68.38% | 41.12 years |
| Sigmoid, B=8 | 56.45% | 15.76% | 34.18 years |

The 30-year anchor alone cannot identify the late-life shape. A linear model
requires loss no greater than **0.667%, 0.500% and 0.400% of original power per
year** to retain 80% at 30, 40 and 50 years respectively. This is an algebraic
condition, not evidence that a specific product will satisfy it.

Threshold crossing is linearly interpolated between monthly samples. A crossing
not reached by 50 is exported as a blank numeric value plus explicit status,
not infinity or a crossing at exactly 50. The 80% criterion describes retained
power; safety, economic retirement and system availability require other data.

## Run and reproduce

```bash
uv run python -m energy_analysis.pv_lifetime --output artifacts/pv-lifetime
```

The offline command writes **six PNGs, a six-page vector PDF, seven CSVs and a
manifest** containing input/code/output hashes and software versions. Run it
from the installed analysis package; no API keys or live network are required.

To regenerate packaged numerical extracts from the original archive:

```bash
python scripts/prepare_pv_lifetime_data.py --archive /path/to/Shared_data_results.zip
```

The script validates the published archive MD5 before extraction. A different
archive fails rather than silently replacing the reviewed source version.
Tests check source cells and exclusions, analytic inversion, changing-rate and
changing-shape updates, step subdivision, independent-mode multiplication,
horizon censoring and complete offline exports.

## Repairable plant operation over 30–50 years

The executable [operation scenario](https://julianascencio.github.io/energy-data-insights/auto_examples/analysis/plot_pv_operation_50_years.html)
extends degradation-only projections with independent annual component failures,
replacement downtime and constant-real replacement costs. Run it from the checkout
with `uv run python examples/analysis/plot_pv_operation_50_years.py`.

The reusable `energy_methods.pv_operation.simulate_operation` method accepts an
existing `ReliabilityCurve` and explicit `ComponentScenario` assumptions. The
example uses 2,000 seeded histories and reports years 30, 40 and 50 from the same
histories. It compares original-component survival with an analytical independent
Bernoulli calculation. Replacement restores service without resetting module age.
All failure probabilities, costs and outage durations are hypothetical. Percentile
bands reflect sampled failures conditional on those assumptions. Annual midpoint
retention approximates energy integration. Multiple failures of one component in
a year, repair queues, seasonal outages and parameter uncertainty are excluded.
The returned table can be exported directly to CSV using the example's export line.
