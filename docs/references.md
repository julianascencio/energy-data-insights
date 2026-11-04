# Scientific references and attribution

## Project inspiration and early foundations

Energy Data Insights was inspired by the following doctoral thesis, and its
first studies and methods build on that research. The repository has since
expanded with new methods, connectors, databases and applications beyond the
thesis. Each component's sources and implementation boundaries are identified
separately.

**Julián Andrés Ascencio Vásquez (2021). _Modelling and worldwide assessment
of performance and aging of photovoltaic modules and systems_. Doctoral
dissertation, University of Ljubljana, Faculty of Electrical Engineering.**
[Permanent national-library record](https://www.dlib.si/details/URN:NBN:SI:DOC-TMG3QFI9).

The root `CITATION.cff` describes the software; the thesis is retained among its
references and appears first in analysis report bibliographies as project
context. Its institutional catalogue identifier
is **COBISS 77808131**. The university records the defense on **21 September 2021**:
[LPVO thesis catalogue](https://lpvo.fe.uni-lj.si/en/education/final-theses/completed/)
and [defense announcement](https://lpvo.fe.uni-lj.si/en/2021/).
The later national-library upload date is not the thesis publication year.
Marko Topič is the advisor, not a thesis coauthor. No thesis DOI is asserted.

## How to cite work using this repository

1. Cite the repository URL and exact Git commit for the software used.
2. Cite the individual algorithm papers, software and data sources actually used
   by your analysis, including the thesis for methods or studies derived from it.
   Later additions have their own sources; a thesis citation does not replace them.
3. Retain the input hashes,
   parameters, software versions and source-access timestamps in your manifest.

Use descriptive method names such as **acceptance band** and **typical daily
profiles** in prose, headings and labels. Preserve author names in citations and
attribution, rather than adding them as method-name prefixes.

The catalogue is scoped to the methods, sources and documentation used or
discussed in this repository. It is not the thesis's complete bibliography.
`implemented` identifies method lineage; it does not claim identical reproduction
of published author software. `background` is explanatory context. A `data`
entry documents an available source and does not prove that a particular run
downloaded it. Use the run's acquisition provenance for that determination.

| Component | Attribution and implementation boundary |
| --- | --- |
| Typical Daily Profiles | Ascencio-Vásquez et al. (2021); project qualification/pooling rules. |
| CCYA | Thesis (2021), sections 7.5.1-7.5.3; adaptations documented in docs/ccya.md. |
| Acceptance bands | Ascencio-Vásquez et al. (2020); documented roughness/distance interpretation. |
| Effective POA | Reda-Andreas, Erbs, Hay-Davies, Spencer and pvlib. |
| Single-axis geometry | Anderson-Mikofski and Lorenzo et al. through pvlib; inferred geometry. |
| LightGBM | Ke et al. and LightGBM documentation; project chronology and monotonic settings. |
| Physical response | Stark-Parker BVLS through SciPy; repository-specific PV basis. |
| Operational screening | IEC TS 63019 context; no conformity or certified availability claim. |
| Generation and weather | Worldwide providers and measured PV; see run provenance. |

Subhourly irradiance redistribution and geometry/lag search are project choices.
The shape-constrained physical basis is not attributed to the solver authors.
Screening thresholds cannot establish verified operating causes.

## Maintaining the bibliography

The single metadata source is
`methods/src/energy_methods/references.json`, packaged with `energy_methods`.
The immutable Python API is `energy_methods.references`. This page,
`references.bib` and `CITATION.cff` are generated together. The CFF file uses
JSON syntax, which is valid YAML, so its consistency can be checked without a
runtime YAML dependency. Its schema version is CFF 1.2.0.

```bash
uv run python scripts/check_citations.py --write
uv run python scripts/check_citations.py
```

Add a verified entry and connect it to the relevant implementation when a new
method or source is introduced. Do not invent a DOI, assume a publication year
from a web-page upload date, imply unimplemented algorithms are available, or
substitute a metadata-verification date for the actual data-access date.
No license is inferred from bibliographic metadata.

## Complete catalogue

### ascencio_vasquez_2021_thesis

Ascencio Vásquez, Julián Andrés (2021). **Modelling and worldwide assessment of performance and aging of photovoltaic modules and systems**. University of Ljubljana, Faculty of Electrical Engineering. [Source](https://www.dlib.si/details/URN:NBN:SI:DOC-TMG3QFI9)

**Role:** foundational. Project inspiration and scientific foundation for the early studies and methods. Later additions include independent methods, connectors, databases and applications with their own sources; this thesis is not the source of every repository component. University of Ljubljana catalogue: COBISS 77808131; national-library URN:NBN:SI:DOC-TMG3QFI9. Defended 21 September 2021. Marko Topič is the advisor, not a coauthor. No thesis DOI has been verified. Citation does not claim that every thesis chapter is implemented. CCYA implementation follows sections 7.5.1–7.5.3 (pp. 150–164), with equations 3.6/3.8 for thermal context. The institutional full text is https://repozitorij.uni-lj.si/Dokument.php?id=148326&lang=eng. Explicit choices for monthly centroid scaling, incremental temperature normalization, nonexceedance quantiles and cumulative ratio versus signed gain are documented in docs/ccya.md; no numerical reproduction of Bolzano is claimed. Soiling and snow indicators follow Eqs. 3.2–3.4 (pp. 49–51) and Tables 6.6–6.7 (pp. 135–136), with explicit equality/low-domain conventions and alternative example data documented in docs/soiling-snow.md.

**Used by:** `README.md`, `methods/README.md`, `analysis/README.md`, `methods/src/energy_methods/degradation.py`, `docs/degradation.md`, `methods/src/energy_methods/ccya.py`, `docs/ccya.md`, `analysis/examples/ccya/README.md`, `analysis/src/energy_analysis/ccya_case/pipeline.py`, `examples/analysis/plot_kgpv_worldwide.py`, `docs/kgpv.md`, `methods/src/energy_methods/weather_risk.py`, `methods/src/energy_methods/weather_risk_mapping.py`, `docs/soiling-snow.md`, `examples/analysis/plot_soiling_snow_risk.py`, `examples/analysis/plot_country_risk.py`, `examples/connectors/plot_generation_coverage.py`, `docs/worldwide-generation.md`, `scripts/prepare_connector_station_coverage.py`, `examples/connectors/data/generation_coverage_stations.csv`, `examples/connectors/data/generation_coverage_stations_provenance.json`, `analysis/src/energy_analysis/canary_kgpv/pipeline.py`, `examples/analysis/plot_kgpv_canary.py`, `docs/kgpv-canary.md`, `analysis/src/energy_analysis/chile_kgpv/pipeline.py`, `examples/analysis/plot_kgpv_chile.py`, `docs/kgpv-chile.md`, `methods/src/energy_methods/climate_zones.py`, `methods/src/energy_methods/jrc_climate.py`, `methods/src/energy_methods/ml21.py`, `methods/src/energy_methods/pvcz.py`, `docs/climate-comparison.md`.

### ascencio_vasquez_2021_tdp

Ascencio-Vásquez, Julián; Osorio-Aravena, Juan Carlos; Brecl, Kristijan; Muñoz-Cerón, Emilio; Topič, Marko (2021). **Typical Daily Profiles, a novel approach for photovoltaics performance assessment: Case study on large-scale systems in Chile**. Solar Energy, 225, 357-374. [DOI: 10.1016/j.solener.2021.07.007](https://doi.org/10.1016/j.solener.2021.07.007)

**Role:** implemented. Source of the Typical Daily Profiles approach and original Chile fleet case study. Project qualification rules, missing-data handling, fixed-clock pooling and unavailable historical capacity gates are documented adaptations, not a claim of byte-identical author software.

**Used by:** `methods/src/energy_methods/tdp.py`.

### ascencio_vasquez_2020_modelling

Ascencio-Vásquez, Julián; Bevc, Jakob; Reba, Kristjan; Brecl, Kristijan; Jankovec, Marko; Topič, Marko (2020). **Advanced PV Performance Modelling Based on Different Levels of Irradiance Data Accuracy**. Energies, 13(9), 2166. [DOI: 10.3390/en13092166](https://doi.org/10.3390/en13092166)

**Role:** implemented. Source of the two-stage irradiance/power acceptance band and low/medium/high irradiance evidence levels. The repository states its interpretation of inconsistent printed roughness/distance expressions. Chronological validation and monotonic LightGBM settings are project adaptations. The solar/wind forecasting benchmark uses this paper as methodological inspiration for resource-quality disclosure and empirical/ML comparison, not numerical reproduction. Rolling forecasts, XGBoost, Timestral and wind are project extensions; its acceptance-band algorithm and test-outlier removal are not applied in this benchmark.

**Used by:** `methods/src/energy_methods/acceptance_band.py`, `methods/src/energy_methods/lightgbm.py`, `analysis/src/energy_analysis/forecast_benchmark.py`, `examples/analysis/plot_forecast_model_benchmark.py`, `docs/forecast-benchmark.md`.

### erbs_1982_diffuse

Erbs, D.G.; Klein, S.A.; Duffie, J.A. (1982). **Estimation of the diffuse radiation fraction for hourly, daily and monthly-average global radiation**. Solar Energy, 28(4), 293-302. [DOI: 10.1016/0038-092X(82)90302-4](https://doi.org/10.1016/0038-092X%2882%2990302-4)

**Role:** implemented. Erbs decomposition through pvlib. Applying the hourly model at synthetic solar-position substeps is a declared integration approximation.

**Used by:** `methods/src/energy_methods/poa.py`.

### hay_davies_1980_transposition

Hay, J. E.; Davies, J. A. (1980). **Calculations of the solar radiation incident on an inclined surface**. Proceedings of the First Canadian Solar Radiation Data Workshop, 59. [Source](https://pvlib-python.readthedocs.io/en/stable/reference/generated/pvlib.irradiance.haydavies.html)

**Role:** implemented. Hay-Davies sky-diffuse transposition through pvlib. Metadata checked against pvlib documentation; no DOI is asserted. Ground reflection is handled separately by pvlib.

**Used by:** `methods/src/energy_methods/poa.py`.

### reda_andreas_2004_solar_position

Reda, Ibrahim; Andreas, Afshin (2004). **Solar position algorithm for solar radiation applications**. Solar Energy, 76(5), 577-589. [DOI: 10.1016/j.solener.2003.12.003](https://doi.org/10.1016/j.solener.2003.12.003)

**Role:** implemented. Solar position algorithm used through pvlib nrel_numpy. The twelve-substep integration and effective geometry selection are repository choices.

**Used by:** `methods/src/energy_methods/poa.py`.

### spencer_1971_solar_fourier

Spencer, J. W. (1971). **Fourier series representation of the position of the sun**. Search, 2(5), 172. [Source](https://pvlib-python.readthedocs.io/en/stable/reference/generated/pvlib.solarposition.equation_of_time_spencer71.html)

**Role:** implemented. Source of the Spencer Fourier approximation used by pvlib get_extra_radiation (its default method). The solar-position calculation itself uses the separate Reda-Andreas algorithm. Metadata checked against pvlib; no DOI is asserted.

**Used by:** `methods/src/energy_methods/poa.py`.

### anderson_mikofski_2020_backtracking

Anderson, Kevin; Mikofski, Mark (2020). **Slope-Aware Backtracking for Single-Axis Trackers**. NREL/TP-5K00-76626. National Renewable Energy Laboratory. [DOI: 10.2172/1660126](https://doi.org/10.2172/1660126)

**Role:** implemented. Single-axis tracking/backtracking equations used through pvlib. The current geometry bank uses level cross-axis terrain; citing the general method does not assert surveyed slope or tracker configuration.

**Used by:** `methods/src/energy_methods/poa.py`.

### lorenzo_2011_backtracking

Lorenzo, E.; Narvarte, L.; Muñoz, J. (2011). **Tracking and back-tracking**. Progress in Photovoltaics: Research and Applications, 19(6), 747-753. [DOI: 10.1002/pip.1085](https://doi.org/10.1002/pip.1085)

**Role:** implemented. Tracking/backtracking source cited by pvlib singleaxis, the implementation used by the geometry bank.

**Used by:** `methods/src/energy_methods/poa.py`.

### anderson_2023_pvlib

Anderson, Kevin S.; Hansen, Clifford W.; Holmgren, William F.; Jensen, Adam R.; Mikofski, Mark A.; Driesse, Anton (2023). **pvlib python: 2023 project update**. Journal of Open Source Software, 8(92), 5994. [DOI: 10.21105/joss.05994](https://doi.org/10.21105/joss.05994)

**Role:** software. Current project-level citation recommended by pvlib. Exact installed software versions are recorded in analysis manifests and the workspace lockfile.

**Used by:** `methods/src/energy_methods/poa.py`.

### pvlib_interval_transposition

pvlib python contributors (n.d.). **Modeling with interval averages**. [Source](https://pvlib-python.readthedocs.io/en/stable/gallery/irradiance-transposition/plot_interval_transposition_error.html)

**Role:** background. Documentation motivating explicit interval alignment. The repository cosine-disaggregation scheme is its own approximation; this example is not a validation of that scheme.

**Used by:** `methods/README.md`.

### ke_2017_lightgbm

Ke, Guolin; Meng, Qi; Finley, Thomas; Wang, Taifeng; Chen, Wei; Ma, Weidong; Ye, Qiwei; Liu, Tie-Yan (2017). **LightGBM: A Highly Efficient Gradient Boosting Decision Tree**. Advances in Neural Information Processing Systems, 30. [Source](https://proceedings.neurips.cc/paper_files/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html)

**Role:** implemented. Original LightGBM algorithm reference. The optional model uses the LightGBM library; monotonic settings do not guarantee concavity or any minimum prediction score.

**Used by:** `methods/src/energy_methods/lightgbm.py`, `analysis/src/energy_analysis/forecast_benchmark.py`, `examples/analysis/plot_forecast_model_benchmark.py`, `docs/forecast-benchmark.md`.

### lightgbm_parameters

LightGBM contributors (n.d.). **LightGBM parameters**. [Source](https://lightgbm.readthedocs.io/en/stable/Parameters.html)

**Role:** software. Reference for deterministic CPU execution, objective compatibility, bounded thread counts and feature monotonicity. Version-specific behavior is tied to the lockfile.

**Used by:** `methods/src/energy_methods/lightgbm.py`, `methods/README.md`.

### stark_parker_1995_bvls

Stark, P. B.; Parker, R. L. (1995). **Bounded-variable least-squares: an algorithm and applications**. Computational Statistics, 10, 129-141. [Source](https://www.stat.berkeley.edu/~stark/Preprints/bvls.pdf)

**Role:** implemented. Bounded-variable least-squares algorithm selected explicitly as scipy.optimize.lsq_linear(method="bvls"). The nonnegative transformed PV basis and shape constraints are repository-specific. Author spelling verified against the author bibliography, correcting the typo in some SciPy documentation.

**Used by:** `methods/src/energy_methods/physics.py`.

### virtanen_2020_scipy

Virtanen, Pauli; Gommers, Ralf; Oliphant, Travis E.; Haberland, Matt; Reddy, Tyler; Cournapeau, David; Burovski, Evgeni; Peterson, Pearu; Weckesser, Warren; Bright, Jonathan; van der Walt, Stéfan J.; Brett, Matthew; Wilson, Joshua; Millman, K. Jarrod; Mayorov, Nikolay; Nelson, Andrew R. J.; Jones, Eric; Kern, Robert; Larson, Eric; Carey, C J; Polat, İlhan; Feng, Yu; Moore, Eric W.; VanderPlas, Jake; Laxalde, Denis; Perktold, Josef; Cimrman, Robert; Henriksen, Ian; Quintero, E. A.; Harris, Charles R.; Archibald, Anne M.; Ribeiro, Antônio H.; Pedregosa, Fabian; van Mulbregt, Paul; SciPy 1.0 Contributors; Vijaykumar, Aditya; Bardelli, Alessandro Pietro; Rothberg, Alex; Hilboll, Andreas; Kloeckner, Andreas; Scopatz, Anthony; Lee, Antony; Rokem, Ariel; Woods, C. Nathan; Fulton, Chad; Masson, Charles; Häggström, Christian; Fitzgerald, Clark; Nicholson, David A.; Hagen, David R.; Pasechnik, Dmitrii V.; Olivetti, Emanuele; Martin, Eric; Wieser, Eric; Silva, Fabrice; Lenders, Felix; Wilhelm, Florian; Young, G.; Price, Gavin A.; Ingold, Gert-Ludwig; Allen, Gregory E.; Lee, Gregory R.; Audren, Hervé; Probst, Irvin; Dietrich, Jörg P.; Silterra, Jacob; Webber, James T; Slavič, Janko; Nothman, Joel; Buchner, Johannes; Kulick, Johannes; Schönberger, Johannes L.; de Miranda Cardoso, José Vinícius; Reimer, Joscha; Harrington, Joseph; Rodríguez, Juan Luis Cano; Nunez-Iglesias, Juan; Kuczynski, Justin; Tritz, Kevin; Thoma, Martin; Newville, Matthew; Kümmerer, Matthias; Bolingbroke, Maximilian; Tartre, Michael; Pak, Mikhail; Smith, Nathaniel J.; Nowaczyk, Nikolai; Shebanov, Nikolay; Pavlyk, Oleksandr; Brodtkorb, Per A.; Lee, Perry; McGibbon, Robert T.; Feldbauer, Roman; Lewis, Sam; Tygier, Sam; Sievert, Scott; Vigna, Sebastiano; Peterson, Stefan; More, Surhud; Pudlik, Tadeusz; Oshima, Takuya; Pingel, Thomas J.; Robitaille, Thomas P.; Spura, Thomas; Jones, Thouis R.; Cera, Tim; Leslie, Tim; Zito, Tiziano; Krauss, Tom; Upadhyay, Utkarsh; Halchenko, Yaroslav O.; Vázquez-Baeza, Yoshiki (2020). **SciPy 1.0: fundamental algorithms for scientific computing in Python**. Nature Methods, 17(3), 261-272. [DOI: 10.1038/s41592-019-0686-2](https://doi.org/10.1038/s41592-019-0686-2)

**Role:** software. SciPy provides the bounded least-squares numerical solver; see Stark and Parker for the chosen BVLS algorithm. This is not attribution of the repository-specific PV parameterization to SciPy.

**Used by:** `methods/src/energy_methods/physics.py`.

### iec_2019_availability

International Electrotechnical Commission (2019). **IEC TS 63019:2019: Photovoltaic power systems (PVPS) - Information model for availability**. [Source](https://webstore.iec.ch/en/publication/27253)

**Role:** standard. Information-model context only. The ten observable states and numeric thresholds are project screening rules, not normative IEC categories or a conformity claim. Causes remain unconfirmed and the workflow does not compute certified availability.

**Used by:** `methods/src/energy_methods/status.py`, `analysis/README.md`.

### cen_generation_api

Coordinador Eléctrico Nacional (n.d.). **Generación real: API de datos abiertos**. [Source](https://sipub.api.coordinador.cl/generacion-real/v3/findByDate)

**Role:** data. Actual-generation API source. Use the exact request interval, access time, response provenance and effective unit roster recorded by the acquisition; catalogue inclusion is not evidence of live authorization or complete national coverage.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/cen`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### cen_infotecnica_registry

Coordinador Eléctrico Nacional (n.d.). **Infotécnica: registro público de centrales**. [Source](https://api-infotecnica.coordinador.cl/v1/centrales-sin-filtrar/extended/)

**Role:** data. Public plant registry source. Reported maximum power is retained without silently treating it as verified AC or DC nameplate capacity.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/cen`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`, `docs/chile-module-counting.md`, `examples/analysis/plot_chile_largest_module_counting.py`, `examples/analysis/plot_chile_smallest_module_counting.py`, `docs/rengo-module-counting.md`, `examples/analysis/data/rengo_modules/rengo_study.json`.

### cen_historical_reports

Coordinador Eléctrico Nacional (n.d.). **Reportes y estadísticas: generación del Sistema Eléctrico Nacional**. [Source](https://www.coordinador.cl/reportes-y-estadisticas/)

**Role:** data. Provider catalogue for historical generation and Qlik exports. Every imported export requires its specific source URL/file, timestamp conventions and hash; this general catalogue does not certify the completeness of a supplied export.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/cen`, `data-retrieval/README.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### cen_qlik_generation

Coordinador Eléctrico Nacional (n.d.). **Generación real descargable (Qlik)**. [Source](https://qap-prd.coordinador.cl/ext/extensions/mashup_Generacion_Real_Descargable/mashup_Generacion_Real_Descargable.html)

**Role:** data. Source interface for preserved generation exports. The adapter imports user-supplied CSV/XLSX/ZIP exports with an explicit contract; citation does not imply anonymous live access, successful authorization or an implemented Qlik session client.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/cen/history.py`, `data-retrieval/README.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### hersbach_2020_era5

Hersbach, Hans; Bell, Bill; Berrisford, Paul; Hirahara, Shoji; Horányi, András; Muñoz‐Sabater, Joaquín; Nicolas, Julien; Peubey, Carole; Radu, Raluca; Schepers, Dinand; Simmons, Adrian; Soci, Cornel; Abdalla, Saleh; Abellan, Xavier; Balsamo, Gianpaolo; Bechtold, Peter; Biavati, Gionata; Bidlot, Jean; Bonavita, Massimo; De Chiara, Giovanna; Dahlgren, Per; Dee, Dick; Diamantakis, Michail; Dragani, Rossana; Flemming, Johannes; Forbes, Richard; Fuentes, Manuel; Geer, Alan; Haimberger, Leo; Healy, Sean; Hogan, Robin J.; Hólm, Elías; Janisková, Marta; Keeley, Sarah; Laloyaux, Patrick; Lopez, Philippe; Lupu, Cristina; Radnoti, Gabor; de Rosnay, Patricia; Rozum, Iryna; Vamborg, Freja; Villaume, Sebastien; Thépaut, Jean‐Noël (2020). **The ERA5 global reanalysis**. Quarterly Journal of the Royal Meteorological Society, 146(730), 1999-2049. [DOI: 10.1002/qj.3803](https://doi.org/10.1002/qj.3803)

**Role:** data. Scientific description of ERA5 reanalysis. Reanalysis is modelled weather and cannot be relabelled as a measured station. Cite the actual dataset and acquisition wrapper separately.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/open_meteo`, `data-retrieval/src/energy_data_retrieval/sources/earthmover_era5`, `data-retrieval/src/energy_data_retrieval/grid_discovery.py`, `docs/location-discovery.md`, `data-retrieval/src/energy_data_retrieval/sources/cds`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### era5_single_levels

Copernicus Climate Change Service (C3S) Climate Data Store (CDS) (2023). **ERA5 hourly data on single levels from 1940 to present**. [DOI: 10.24381/cds.adbb2d47](https://doi.org/10.24381/cds.adbb2d47)

**Role:** data. Single-level dataset citation as recommended by the Earthmover source catalogue. Record the actual retrieval date and selected data vintage; do not use the metadata-verification date as a data-access date.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/open_meteo`, `data-retrieval/src/energy_data_retrieval/sources/earthmover_era5`, `data-retrieval/src/energy_data_retrieval/grid_discovery.py`, `docs/location-discovery.md`, `data-retrieval/src/energy_data_retrieval/sources/cds`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### earthmover_icechunk_era5

Earthmover (n.d.). **Icechunk ERA5**. [Source](https://registry.opendata.aws/earthmover-era5/)

**Role:** data. Optional native ERA5 source. Cite Earthmover, the C3S single-level dataset, and underlying ERA5 research; acquisition must retain the pinned snapshot and actual access date. Catalogue metadata verification does not establish current snapshot coverage or a new data acquisition.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/earthmover_era5`, `data-retrieval/src/energy_data_retrieval/grid_discovery.py`, `docs/location-discovery.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### open_meteo_historical_weather

Open-Meteo (n.d.). **Historical Weather API**. [Source](https://open-meteo.com/en/docs/historical-weather-api)

**Role:** data. Optional ERA5 weather wrapper. Cite the underlying ERA5 dataset/paper and retain the explicitly requested product, grid cell and interval semantics; this is not measured irradiance. The snow example separately selects ERA5-Land physical ground snow_depth, credits Open-Meteo (CC BY 4.0), and retains the provider warning about snow-depth overestimation.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/open_meteo`, `data-retrieval/src/energy_data_retrieval/grid_discovery.py`, `docs/location-discovery.md`, `scripts/prepare_weather_risk_example.py`, `examples/analysis/plot_soiling_snow_risk.py`, `docs/soiling-snow.md`, `examples/analysis/plot_country_risk.py`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### open_meteo_historical_forecast

Open-Meteo (n.d.). **Historical Forecast API**. [Source](https://open-meteo.com/en/docs/historical-forecast-api)

**Role:** data. Optional archive of numerical forecasts. The adapter explicitly selects ECMWF IFS; do not describe these records as ERA5 or observations. Record model, vintage and interval semantics from provenance.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/open_meteo`, `data-retrieval/src/energy_data_retrieval/grid_discovery.py`, `docs/location-discovery.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### open_meteo_variable_definitions

Open-Meteo (n.d.). **Weather Forecast API: hourly variable definitions**. [Source](https://open-meteo.com/en/docs)

**Role:** data. Provider definitions for preceding-hour radiation/gust variables and instantaneous temperature/wind. Archive-specific variable definitions take priority where products differ.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/open_meteo`, `data-retrieval/README.md`, `data-retrieval/src/energy_data_retrieval/grid_discovery.py`, `docs/location-discovery.md`.

### eyring_2016_cmip6

Eyring, V.; Bony, S.; Meehl, G. A.; Senior, C. A.; Stevens, B.; Stouffer, R. J.; Taylor, K. E. (2016). **Overview of the Coupled Model Intercomparison Project Phase 6 (CMIP6) experimental design and organization**. Geoscientific Model Development, 9, 1937-1958. [DOI: 10.5194/gmd-9-1937-2016](https://doi.org/10.5194/gmd-9-1937-2016)

**Role:** data. Scientific design of the CMIP6 archive accessed by the retrieval provider. The repository retrieves published climate-model output; it does not implement or run the contributing climate models. Cite each selected model/experiment dataset and its version separately using the preserved provider citation links.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/cmip6`, `data-retrieval/README.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### oneill_2016_scenariomip

O'Neill, B. C.; Tebaldi, C.; van Vuuren, D. P.; Eyring, V.; Friedlingstein, P.; Hurtt, G.; Knutti, R.; Kriegler, E.; Lamarque, J.-F.; Lowe, J.; Meehl, G. A.; Moss, R.; Riahi, K.; Sanderson, B. M. (2016). **The Scenario Model Intercomparison Project (ScenarioMIP) for CMIP6**. Geoscientific Model Development, 9, 3461-3482. [DOI: 10.5194/gmd-9-3461-2016](https://doi.org/10.5194/gmd-9-3461-2016)

**Role:** data. Scientific description of the SSP scenario experiments selectable by the CMIP6 retrieval provider. Scenario simulations are conditional climate projections, not observations or deterministic weather forecasts. Their availability and coverage are established by each saved catalogue result, not by this paper citation.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/cmip6`, `data-retrieval/README.md`.

### esgf_stac_access

Earth System Grid Federation (ESGF) contributors (n.d.). **ESGF PyClient documentation: STAC migration and data-access services**. [Source](https://esgf-pyclient.readthedocs.io/en/latest/)

**Role:** data. Official access guidance identifies the east and west ESGF STAC discovery services and deprecates the legacy Solr search interface. This provider uses direct HTTP requests; this reference does not mean esgf-pyclient is a runtime dependency. Preserve the actual endpoint, search criteria, resolved dataset version, asset URLs and access time in acquisition provenance.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/cmip6`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### intake_esgf_cmip6_catalogue_guidance

ESGF2-US intake-esgf contributors (n.d.). **intake-esgf documentation: CMIP6 catalogue migration guidance**. [Source](https://intake-esgf.readthedocs.io/en/latest/)

**Role:** background. Upstream operational guidance documents CMIP6 republishing and inconsistent member identifiers in some STAC records. The retrieval implementation must preserve and validate identifiers instead of silently substituting another ensemble member. This reference is documentation, not a dependency or a claim of complete catalogue coverage.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/cmip6`.

### stac_file_info

STAC File Info extension contributors (n.d.). **STAC File Info Extension Specification, version 2.1.0**. [Source](https://github.com/stac-extensions/file/tree/v2.1.0)

**Role:** standard. Defines byte sizes, relative local paths and hexadecimal multihash checksums carried by ESGF NetCDF assets. Checksums establish file integrity against the published asset metadata; they do not establish scientific accuracy or data completeness.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/cmip6`.

### cmip6_data_user_guide

Program for Climate Model Diagnosis and Intercomparison (PCMDI) (2022). **CMIP6 Guidance for Data Users**. [Source](https://pcmdi.llnl.gov/CMIP6/Guide/dataUsers.html)

**Role:** data. Document version 19 October 2022. Source of the data-citation and provenance guidance: retain official model and institution names, experimental identifiers, dataset versions and the original citation/further-information links. A general CMIP6 paper citation does not replace dataset-specific author and DOI attribution. Use the current STAC access documentation for endpoints because this older guide includes legacy interfaces.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/cmip6`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### cmip6_terms_of_use

Program for Climate Model Diagnosis and Intercomparison (PCMDI) (2022). **CMIP6: Terms of Use, version 6.2**. [Source](https://pcmdi.llnl.gov/CMIP6/TermsOfUse/TermsOfUse6-2.html)

**Role:** data. Document version 12 October 2022. Defines acknowledgement and data-citation requirements and directs users to the official per-model license inventory, which supersedes older file-header restrictions. Preserve source metadata and consult that inventory for data reuse; a catalogue-record license alone does not establish the license of the underlying model output or of this repository.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/cmip6`.

### driemel_2018_bsrn

Driemel, Amelie; Augustine, John; Behrens, Klaus; Colle, Sergio; Cox, Christopher; Cuevas-Agulló, Emilio; Denn, Fred M.; Duprat, Thierry; Fukuda, Masato; Grobe, Hannes; Haeffelin, Martial; Hodges, Gary; Hyett, Nicole; Ijima, Osamu; Kallis, Ain; Knap, Wouter; Kustov, Vasilii; Long, Charles N.; Longenecker, David; Lupi, Angelo; Maturilli, Marion; Mimouni, Mohamed; Ntsangwane, Lucky; Ogihara, Hiroyuki; Olano, Xabier; Olefs, Marc; Omori, Masao; Passamani, Lance; Pereira, Enio Bueno; Schmithüsen, Holger; Schumacher, Stefanie; Sieger, Rainer; Tamlyn, Jonathan; Vogt, Roland; Vuilleumier, Laurent; Xia, Xiangao; Ohmura, Atsumu; König-Langlo, Gert (2018). **Baseline Surface Radiation Network (BSRN): structure and data description (1992–2017)**. Earth System Science Data, 10(3), 1491-1501. [DOI: 10.5194/essd-10-1491-2018](https://doi.org/10.5194/essd-10-1491-2018)

**Role:** data. Canonical scientific description of the BSRN radiation archive. The provider retrieves station observations through PANGAEA and preserves their published identity and provenance. Cite the actual station collection and monthly dataset DOIs in addition to this network paper. Archive checks do not establish that a downloaded value passed every subsequent scientific quality check or represents a particular PV site.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/bsrn`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`, `scripts/prepare_connector_station_coverage.py`, `examples/connectors/data/generation_coverage_stations.csv`, `examples/connectors/data/generation_coverage_stations_provenance.json`.

### bsrn_pangaea_access

World Radiation Monitoring Center, Alfred Wegener Institute (n.d.). **Baseline Surface Radiation Network: Data retrieval via PANGAEA**. [Source](https://bsrn.awi.de/data/data-retrieval-via-pangaea/)

**Role:** data. Official source guidance for UTC timestamps, station/month datasets and logical records. The adapter targets basic radiation records; other record types require their own explicit contract. AWI states that resulting detailed BSRN quality-check flags are not archived. PANGAEA value annotations, when present, are preserved separately and do not establish completed scientific quality control. Preserve each dataset's citation, station metadata and BSRN data-release conditions.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/bsrn`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`, `scripts/prepare_connector_station_coverage.py`, `examples/connectors/data/generation_coverage_stations.csv`, `examples/connectors/data/generation_coverage_stations_provenance.json`.

### pangaea_data_access

PANGAEA Data Publisher for Earth & Environmental Science (n.d.). **PANGAEA Data Access and Reuse**. [Source](https://wiki.pangaea.de/wiki/Data_Access_and_Reuse)

**Role:** data. Documents DOI-based programmatic access, tab-delimited exports, structured metadata and citation links. PANGAEA describes these as standard HTTP access rather than a separate proprietary data API. The adapter retains the original citation/license text and source hashes; a DOI identifies the selected dataset and does not imply unrestricted access or a license for all PANGAEA holdings.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/bsrn`, `examples/connectors/plot_generation_coverage.py`, `docs/worldwide-generation.md`, `scripts/prepare_connector_station_coverage.py`, `examples/connectors/data/generation_coverage_stations.csv`, `examples/connectors/data/generation_coverage_stations_provenance.json`.

### menne_2023_ghcnh

Menne, Matthew J.; Noone, Simon; Casey, Nancy W.; Dunn, Robert H.; McNeill, Shelley; Kantor, Diana; Thorne, Peter W.; Orcutt, Karen; Cunningham, Sam; Risavi, Nicholas (2023). **Global Historical Climatology Network-Hourly (GHCNh)**. NOAA National Centers for Environmental Information. [DOI: 10.25921/jp3d-3v19](https://doi.org/10.25921/jp3d-3v19)

**Role:** data. Official NOAA dataset citation, including all ten credited authors. Identify the actual station/year subset, product version and access date when citing an acquisition. The adapter retrieves GHCNh station reports and retains measurement, quality, source and report codes; the word hourly does not convert every reported value into a one-hour mean or supply missing irradiance observations.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/noaa`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`, `scripts/prepare_connector_station_coverage.py`, `examples/connectors/data/generation_coverage_stations.csv`, `examples/connectors/data/generation_coverage_stations_provenance.json`.

### noaa_ghcnh_documentation

NOAA National Centers for Environmental Information (2026). **Global Historical Climatology Network hourly (GHCNh): Documentation, version 1.1.0**. [Source](https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly/doc/ghcnh_DOCUMENTATION.pdf)

**Role:** data. Official documentation updated 10 March 2026. Defines native station/year PSV access, station identifiers, units and measurement/quality/report/source codes. GHCNh version 1.1.0 supersedes previous versions and replaces the legacy ISD product. Preserve source fields and actual report timestamps; transformations into analysis intervals require a separately stated aggregation policy.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/noaa`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`, `scripts/prepare_connector_station_coverage.py`, `examples/connectors/data/generation_coverage_stations.csv`, `examples/connectors/data/generation_coverage_stations_provenance.json`.

### noaa_isd_service_transition

NOAA National Centers for Environmental Information (2026). **Service Location Change for Integrated Surface Data (Global Hourly)**. [Source](https://www.nesdis.noaa.gov/news/service-location-change-integrated-surface-data-global-hourly)

**Role:** background. Official notice dated 23 June 2026 explains why new acquisition uses GHCNh. It records that legacy ISD updates stopped after 24 August 2025 and announces retirement of NCEI's ISD FTP/HTTPS distribution, while legacy files remain available through NODD. This repository's NOAA provider does not implement a legacy ISD fallback.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/noaa`, `examples/connectors/plot_generation_coverage.py`, `docs/worldwide-generation.md`, `scripts/prepare_connector_station_coverage.py`, `examples/connectors/data/generation_coverage_stations.csv`, `examples/connectors/data/generation_coverage_stations_provenance.json`.

### pangaea_quality_flags

PANGAEA Data Publisher for Earth & Environmental Science (n.d.). **PANGAEA Quality flag definitions**. [Source](https://wiki.pangaea.de/wiki/Quality_flag)

**Role:** data. Defines numeric-value annotations for questionable, invalid, unknown, individually defined and inequality-qualified observations. The BSRN parser preserves the annotation and original field rather than silently treating an annotated value as unqualified. PANGAEA syntax alone does not certify detailed BSRN scientific quality control.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/bsrn`, `examples/connectors/plot_generation_coverage.py`, `docs/worldwide-generation.md`, `scripts/prepare_connector_station_coverage.py`, `examples/connectors/data/generation_coverage_stations.csv`, `examples/connectors/data/generation_coverage_stations_provenance.json`.

### knap_2009_bsrn_cabauw

Knap, Wouter (2009). **Basic measurements of radiation at station Cabauw (2009-06)**. PANGAEA. Koninklijk Nederlands Meteorologisch Instituut, De Bilt. [DOI: 10.1594/PANGAEA.725795](https://doi.org/10.1594/PANGAEA.725795)

**Role:** data. The explicit Cabauw June 2009 dataset used by the BSRN retrieval example. It is not a default station selection or an input to every analysis. Retain the retrieved dataset metadata, source hash and BSRN release conditions, and cite the associated station collection as well as this monthly dataset when using its measurements.

**Used by:** `data-retrieval/README.md`.

### knap_2022_bsrn_cabauw_collection

Knap, Wouter (2022). **Basic and other measurements of radiation at station Cabauw (2005-02 et seq)**. PANGAEA. Koninklijk Nederlands Meteorologisch Instituut, De Bilt. [DOI: 10.1594/PANGAEA.940531](https://doi.org/10.1594/PANGAEA.940531)

**Role:** data. Station-level publication series containing the monthly Cabauw dataset in the retrieval example. The collection is updated over time; its citation does not assert that the entire collection was downloaded. Identify the exact monthly DOI and acquisition snapshot used, and preserve their associated station and instrument metadata.

**Used by:** `data-retrieval/README.md`.

### aemet_opendata_specification

Agencia Estatal de Meteorología (AEMET) (n.d.). **AEMET OpenData API specification, version 2.0**. [Source](https://opendata.aemet.es/AEMET_OpenData_specification.json)

**Role:** data. Current official OpenAPI 3.0.1 document, service version 2.0. Defines header api_key authentication, daily-climate inventory and date-range endpoints, and recent conventional station observations described as the latest 12 hours. The recent endpoint does not accept a historical date range. Exact per-field units and observation periods are preserved from each retrieved metadata document.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/aemet/client.py`, `data-retrieval/README.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### aemet_opendata_access

Agencia Estatal de Meteorología (AEMET) (n.d.). **AEMET OpenData: Frequently asked questions and two-stage data access**. [Source](https://opendata.aemet.es/centrodedescargas/faqs)

**Role:** data. Official documentation of API estado responses and temporary datos/metadatos links, which expire after about five minutes. Field metadata contains source units, definitions, attribution and usage conditions. Canonical JSON snapshots retain data values and metadata; they do not claim to preserve exact HTTP encoding. Key expiry follows the newer published access notices rather than older FAQ PDF statements.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/aemet/client.py`, `data-retrieval/README.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### aemet_observation_guidance

Agencia Estatal de Meteorología (AEMET) (n.d.). **Interpretación: Hoy y últimos días**. [Source](https://www.aemet.es/es/eltiempo/observacion/ultimosdatos/ayuda)

**Role:** data. Official interpretation guidance distinguishing instantaneous temperature, wind averaging intervals, gusts and accumulated precipitation. The public website and API may display different units; this implementation checks returned API field metadata before assigning physical-unit columns. Native reporting dates and variable-specific aggregation periods are retained without inferring a uniform hourly observation contract.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/aemet/client.py`, `data-retrieval/README.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### aemet_opendata_key_policy

Agencia Estatal de Meteorología (AEMET) (2026). **AEMET OpenData: API access and key-expiration notices**. [Source](https://opendata.aemet.es/centrodedescargas/novedades)

**Role:** background. Current 2026 notices describe retirement of keys issued without expiration and three-month validity for newly issued keys. The source reads AEMET_API_KEY from the environment, sends it through the documented private HTTP header and excludes credentials from output, provenance and public caches.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/aemet/client.py`, `data-retrieval/README.md`.

### dwd_2024_hourly_solar

Deutscher Wetterdienst (2024). **Hourly station observations of solar incoming (total/diffuse) and longwave downward radiation for Germany**. [Source](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/solar/)

**Role:** data. DWD CDC dataset version v24.03; published 29 March 2024. Dataset identifier urn:x-wmo:md:de.dwd.cdc::obsgermany-climate-hourly-solar. CC BY 4.0. Native hourly radiation energy remains in J/cm², and acquisition hashes record the separately changing station-archive vintage.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/dwd/client.py`, `data-retrieval/README.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`, `scripts/prepare_connector_station_coverage.py`, `examples/connectors/data/generation_coverage_stations.csv`, `examples/connectors/data/generation_coverage_stations_provenance.json`.

### dwd_hourly_solar_documentation

Deutscher Wetterdienst (2024). **DWD CDC dataset description: Hourly station observations of solar incoming (total/diffuse) and longwave downward radiation for Germany**. [Source](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/solar/DESCRIPTION_obsgermany_climate_hourly_solar_en.pdf)

**Role:** data. Official version v24.03, published 29 March 2024 and last edited 6 May 2024. Defines native fields, hourly energy sums, missing sentinel -999, QN quality-procedure codes, true-solar-time labels, station metadata and CC BY 4.0. The adapter also verifies per-archive parameter metadata specifying UTC and WOZ; interval boundaries and irradiance flux are not inferred.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/dwd/client.py`, `data-retrieval/README.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`, `scripts/prepare_connector_station_coverage.py`, `examples/connectors/data/generation_coverage_stations.csv`, `examples/connectors/data/generation_coverage_stations_provenance.json`.

### augustine_2000_surfrad

Augustine, John A.; DeLuisi, John J.; Long, Charles N. (2000). **SURFRAD—A National Surface Radiation Budget Network for Atmospheric Research**. Bulletin of the American Meteorological Society, 81(10), 2341-2357. [DOI: 10.1175/1520-0477(2000)081<2341:sansrb>2.3.co;2](https://doi.org/10.1175/1520-0477%282000%29081%3C2341%3Asansrb%3E2.3.co%3B2)

**Role:** data. Scientific network reference explicitly requested by NOAA in README_SURFRAD for publications using SURFRAD data. Author names and bibliographic fields verified against publisher-deposited Crossref metadata. Cite the actual station/day subset and access date as well. Page range follows Crossref and the NOAA README (2341–2357); the current AMS web display ends at 2358.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/surfrad/client.py`, `data-retrieval/README.md`, `examples/connectors/plot_generation_coverage.py`, `docs/worldwide-generation.md`, `scripts/prepare_connector_station_coverage.py`, `examples/connectors/data/generation_coverage_stations.csv`, `examples/connectors/data/generation_coverage_stations_provenance.json`.

### augustine_2005_surfrad

Augustine, John A.; Hodges, Gary B.; Cornwall, Christopher R.; Michalsky, Joseph J.; Medina, Carlos I. (2005). **An Update on SURFRAD—The GCOS Surface Radiation Budget Network for the Continental United States**. Journal of Atmospheric and Oceanic Technology, 22(10), 1460-1472. [DOI: 10.1175/jtech1806.1](https://doi.org/10.1175/jtech1806.1)

**Role:** data. Scientific network reference explicitly requested by NOAA in README_SURFRAD for publications using SURFRAD data. Author names and bibliographic fields verified against publisher-deposited Crossref metadata. Cite the actual station/day subset and access date as well. Describes the seven-station network and its BSRN affiliation; this affiliation creates potential overlap between archive routes.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/surfrad/client.py`, `data-retrieval/README.md`, `examples/connectors/plot_generation_coverage.py`, `docs/worldwide-generation.md`, `scripts/prepare_connector_station_coverage.py`, `examples/connectors/data/generation_coverage_stations.csv`, `examples/connectors/data/generation_coverage_stations_provenance.json`.

### noaa_surfrad_documentation

NOAA Global Monitoring Laboratory (n.d.). **Description of SURFRAD Daily Data Files**. [Source](https://gml.noaa.gov/aftp/data/radiation/surfrad/bon/README_SURFRAD.txt)

**Role:** data. Official 48-field native daily format, station filename aliases, UTC interval-end labels, three-minute averages before 1 January 2009 and one-minute averages thereafter. Defines missing sentinel -9999.9, native quality codes, physical units including UVB in mW/m² and instrument temperatures in Kelvin, and CC0-1.0 licensing. The provider preserves original flags and source values without additional filtering or correction.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/surfrad/client.py`, `data-retrieval/README.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`, `scripts/prepare_connector_station_coverage.py`, `examples/connectors/data/generation_coverage_stations.csv`, `examples/connectors/data/generation_coverage_stations_provenance.json`.

### noaa_surfrad_stations

NOAA Global Monitoring Laboratory (n.d.). **SURFRAD Site Information**. [Source](https://gml.noaa.gov/grad/surfrad/sitepage.html)

**Role:** data. Official current station catalogue. The seven SURFRAD archive aliases are bon, tbl, dra, fpk, gwn, psu and sxf; Bondville has site code BND but file prefix bon. The separately linked ARM Southern Great Plains site is outside this provider. Current catalogue positions do not override historical file-header coordinates or elevations.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/surfrad/client.py`, `data-retrieval/README.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`, `scripts/prepare_connector_station_coverage.py`, `examples/connectors/data/generation_coverage_stations.csv`, `examples/connectors/data/generation_coverage_stations_provenance.json`.

### noaa_surfrad_overview

NOAA Global Monitoring Laboratory (n.d.). **SURFRAD Overview: Surface Radiation Budget Monitoring**. [Source](https://gml.noaa.gov/grad/surfrad/overview.html)

**Role:** data. Official network scope, radiation and meteorological instrumentation, calibration context and BSRN participation. SURFRAD and BSRN archive acquisitions must not be treated as independent observations without checking station/time/variable/vintage overlap.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/surfrad/client.py`, `data-retrieval/README.md`, `examples/connectors/plot_generation_coverage.py`, `docs/worldwide-generation.md`, `scripts/prepare_connector_station_coverage.py`, `examples/connectors/data/generation_coverage_stations.csv`, `examples/connectors/data/generation_coverage_stations_provenance.json`.

### noaa_surfrad_archive

NOAA Global Monitoring Laboratory (n.d.). **NOAA GML SURFRAD daily radiation and meteorological observations**. [Source](https://gml.noaa.gov/aftp/data/radiation/surfrad/)

**Role:** data. Public GML station/year daily text archive actually used by this provider. Cite the selected station, UTC days and acquisition date; preserve its native files, quality flags and hashes. CC0-1.0 with NOAA attribution and fair-use guidance. This is not a claim to retrieve the separately published NCEI NetCDF, QCRAD, or realtime products.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/surfrad/client.py`, `data-retrieval/README.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`, `scripts/prepare_connector_station_coverage.py`, `examples/connectors/data/generation_coverage_stations.csv`, `examples/connectors/data/generation_coverage_stations_provenance.json`.

### bsrn_station_catalogue

PANGAEA; Alfred Wegener Institute (n.d.). **BSRN Stations: PANGAEA station event catalogue**. [Source](https://dataportals.pangaea.de/bsrn/stations)

**Role:** data. Official BSRN station inventory linked from the Alfred Wegener Institute station overview. Its bounded tab-delimited export preserves event codes, names, location, elevation, event dates, comments and source URIs. Event date extents do not establish monthly observation availability or continuous measurements; geographic proximity does not establish site representativeness. The selected catalogue and retrieval timestamp identify the acquisition vintage.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/bsrn/stations.py`, `data-retrieval/src/energy_data_retrieval/station_discovery.py`, `docs/location-discovery.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`, `scripts/prepare_connector_station_coverage.py`, `examples/connectors/data/generation_coverage_stations.csv`, `examples/connectors/data/generation_coverage_stations_provenance.json`.

### ascencio_vasquez_2019_kgpv

Ascencio-Vásquez, Julián; Brecl, Kristijan; Topič, Marko (2019). **Methodology of Köppen-Geiger-Photovoltaic climate classification and implications to worldwide mapping of PV system performance**. Solar Energy, 191, 672-685. [DOI: 10.1016/j.solener.2019.08.072](https://doi.org/10.1016/j.solener.2019.08.072)

**Role:** implemented. Fig. A1 classification precedence and fixed irradiation thresholds; Table 4 merges 24 raw combinations into 12 zones. Verified against the open-access institutional full text. Uses updated GPCC/CRU releases and caller-selected baseline rather than reproducing the original 1990-2016 map. Exact 18 C is assigned tropical, irradiation upper edges are inclusive, and aridity reductions use a machine-roundoff tolerance; these numerical conventions are explicit. No PV yield simulation is claimed.

**Used by:** `methods/src/energy_methods/kgpv.py`, `methods/src/energy_methods/climatology.py`, `methods/src/energy_methods/mapping.py`, `docs/kgpv.md`, `examples/analysis/plot_kgpv_worldwide.py`, `analysis/src/energy_analysis/canary_kgpv/pipeline.py`, `examples/analysis/plot_kgpv_canary.py`, `docs/kgpv-canary.md`, `analysis/src/energy_analysis/chile_kgpv/pipeline.py`, `examples/analysis/plot_kgpv_chile.py`, `docs/kgpv-chile.md`.

### kottek_2006_kg

Kottek, Markus; Grieser, Jürgen; Beck, Christoph; Rudolf, Bruno; Rubel, Franz (2006). **World Map of the Köppen-Geiger climate classification updated**. Meteorologische Zeitschrift, 15(3), 259-263. [DOI: 10.1127/0941-2948/2006/0130](https://doi.org/10.1127/0941-2948/2006/0130)

**Role:** implemented. Eq. 2.1 seasonal dryness threshold uses at least two thirds of annual precipitation in winter or summer. The KGPV paper cites this work with year 2007, but the verified publication is 2006. KGPV Fig. A1 supplies the relabelling and polar/steppe equality rules.

**Used by:** `methods/src/energy_methods/kgpv.py`, `docs/kgpv.md`.

### gpcc_monthly_v2025

Rustemeier, Elke; Finger, Peter; Schirmeister, Zora; Ziese, Markus (2025). **GPCC Precipitation Analysis Monthly Version 2025**. Deutscher Wetterdienst, Global Precipitation Climatology Centre. [Source](https://opendata.dwd.de/climate_environment/GPCC/html/gpcc_precipitation_analysis_monthly_v2025_doi_download.html)

**Role:** data. Four resolutions: 0.25, 0.5, 1.0 and 2.5 degrees. Cite the selected product DOI 10.5676/DWD_GPCC/MONTHLY_V2025_025, _050, _100 or _250 respectively; the request and retrieval manifest expose the exact DOI. Monthly totals; precip_infill is opt-in. Five-year blocks through 2020, 2021-2024 block, monthly files from 2025. Retain native gauge/error fields in raw archives. Follow DWD terms of use.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/gpcc/client.py`, `docs/kgpv.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### harris_2020_cru_ts

Harris, Ian; Osborn, Timothy J.; Jones, Phil; Lister, David (2020). **Version 4 of the CRU TS monthly high-resolution gridded multivariate climate dataset**. Scientific Data, 7, 109. [DOI: 10.1038/s41597-020-0453-3](https://doi.org/10.1038/s41597-020-0453-3)

**Role:** data. Method reference requested by the CRU TS provider. Data version is cited separately; use of this adapter does not imply that any particular analysis consumed CRU data.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/cru_ts/client.py`, `docs/kgpv.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### cru_ts_410

Climatic Research Unit, University of East Anglia (2026). **CRU-TS Version 4.10**. [Source](https://crudata.uea.ac.uk/cru/data/hrg/cru_ts_4.10/)

**Role:** data. Pinned release cruts.2604091129.v4.10, monthly 1901-2025 at 0.5 degrees over land excluding Antarctica. No version DOI was provided on the verified release page. Provider asks users to prefer CEDA and use UEA if CEDA is unavailable or the release has not yet been published there. ODbL with Database Contents License, attribution and share-alike. TMP is monthly mean temperature; PRE is monthly total; PET remains mm/day.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/cru_ts/client.py`, `docs/kgpv.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### xarray_documentation

Xarray developers (n.d.). **Xarray documentation: labelled arrays, CF decoding and interpolation**. [Source](https://docs.xarray.dev/en/stable/)

**Role:** software. Software used for labelled climate grids, CF NetCDF masking/scaling, explicit coordinate alignment, interpolation and NetCDF serialization. The algorithms and scientific threshold choices remain attributed to their individual method papers.

**Used by:** `methods/src/energy_methods/mapping.py`, `data-retrieval/src/energy_data_retrieval/climate_grid.py`.

### ascencio_vasquez_2019_degradation_mapping

Ascencio-Vásquez, Julián; Kaaya, Ismail; Brecl, Kristijan; Weiss, Karl-Anders; Topič, Marko (2019). **Global Climate Data Processing and Mapping of Degradation Mechanisms and Degradation Rates of PV Modules**. Energies, 12(24), 4749. [DOI: 10.3390/en12244749](https://doi.org/10.3390/en12244749)

**Role:** implemented. Source of climate-driven mechanism mapping and 0.2 percent/year categories, also presented in thesis Section 6.4. This implementation requires explicit module calibration and stress conventions. Mean daily extrema and arithmetic ambient humidity in the optional hourly processor are declared adaptations; the published global rasters and their calibration are not claimed reproduced.

**Used by:** `methods/src/energy_methods/degradation.py`, `methods/src/energy_methods/degradation_mapping.py`, `docs/degradation.md`.

### kaaya_2019_degradation

Kaaya, Ismail; Koehl, Michael; Mehilli, Amantin Panos; de Cardona Mariano, Sidrach; Weiss, Karl Anders (2019). **Modeling Outdoor Service Lifetime Prediction of PV Modules: Effects of Combined Climatic Stressors on PV Module Power Degradation**. IEEE Journal of Photovoltaics, 9(4), 1105-1112. [DOI: 10.1109/JPHOTOV.2019.2916197](https://doi.org/10.1109/JPHOTOV.2019.2916197)

**Role:** implemented. Original hydrolysis, photodegradation, thermomechanical and multiplicative combined-rate equations (3)-(7), reproduced in thesis equations 3.14-3.17. Publication Boltzmann constant and normalization placement retained. Calibration and climatic aggregation must be supplied explicitly; no universal module coefficients, power-loss trajectory or service-lifetime predictor are implied.

**Used by:** `methods/src/energy_methods/degradation.py`, `methods/src/energy_methods/degradation_mapping.py`, `docs/degradation.md`.

### skoplaki_palyvos_2009_temperature

Skoplaki, E.; Palyvos, J.A. (2009). **Operating temperature of photovoltaic modules: A survey of pertinent correlations**. Renewable Energy, 34(1), 23-29. [DOI: 10.1016/j.renene.2008.04.009](https://doi.org/10.1016/j.renene.2008.04.009)

**Role:** implemented. Thesis reference [154] for module-temperature correlations, including the Ross relation in thesis equation 3.8. CCYA uses monthly site-adapted GHI and ambient temperature, with the thesis case-study Ross coefficient 0.03 degrees C m2/W. This is a coarse monthly thermal approximation, not hourly irradiance-weighted module temperature. Metadata verified against publisher-deposited Crossref record.

**Used by:** `methods/src/energy_methods/ccya.py`, `docs/ccya.md`.

### polo_2020_site_adaptation

Polo, Jesus; Fernández-Peruchena, Carlos; Salamalikis, Vasileios; Mazorra-Aguiar, Luis; Turpin, Mathieu; Martín-Pomares, Luis; Kazantzidis, Andreas; Blanc, Philippe; Remund, Jan (2020). **Benchmarking on improvement and site-adaptation techniques for modeled solar radiation datasets**. Solar Energy, 201, 469-479. [DOI: 10.1016/j.solener.2020.03.040](https://doi.org/10.1016/j.solener.2020.03.040)

**Role:** background. Thesis reference [287], cited as background for site adaptation in section 7.5.1. CCYA implements the thesis simple monthly linear regression; it does not implement or reproduce the entire benchmark or all correction techniques in this paper. Metadata verified against publisher-deposited Crossref record.

**Used by:** `methods/src/energy_methods/ccya.py`, `docs/ccya.md`.

### hunter_2007_matplotlib

Hunter, John D. (2007). **Matplotlib: A 2D Graphics Environment**. Computing in Science & Engineering, 9(3), 90-95. [DOI: 10.1109/MCSE.2007.55](https://doi.org/10.1109/MCSE.2007.55)

**Role:** software. Matplotlib generates the CCYA analysis figures. Bibliographic details verified against the official Matplotlib citing page; the run manifest records the installed software version.

**Used by:** `analysis/src/energy_analysis/ccya_case/reports/generator.py`.

### eurac_abd_data_access

Eurac Research (n.d.). **Solar energy production data from the PV-ABD plant**. [Source](https://www.eurac.edu/en/institutes-centers/institute-for-renewable-energy/tools-services/photovoltaiksysteme/solar-energy-production-data-from-the-pv-abd-plant)

**Role:** background. Official access description for the Bolzano plant production and meteorological database. Access is restricted. No original plant data were retrieved or redistributed by this example; the bundled generator creates synthetic inputs. This citation documents access limitations, not a data acquisition.

**Used by:** `analysis/examples/ccya/README.md`, `analysis/src/energy_analysis/ccya_case/reports/generator.py`.

### faiman_2008_temperature

Faiman, David (2008). **Assessing the outdoor operating temperature of photovoltaic modules**. Progress in Photovoltaics: Research and Applications, 16(4), 307-315. [DOI: 10.1002/pip.813](https://doi.org/10.1002/pip.813)

**Role:** implemented. Faiman heat-loss temperature model. This implementation follows the 2019 global mapping paper's GHI approximation; it is not a plane-of-array irradiance model.

**Used by:** `methods/src/energy_methods/degradation_weather.py`.

### huld_amillo_2015_performance

Huld, Thomas; Gracia Amillo, Ana M. (2015). **Estimating PV Module Performance over Large Geographical Regions: The Role of Irradiance, Air Temperature, Wind Speed and Solar Spectrum**. Energies, 8(6), 5159-5181. [DOI: 10.3390/en8065159](https://doi.org/10.3390/en8065159)

**Role:** implemented. Source cited by the 2019 mapping study for open-rack crystalline-silicon Faiman coefficients u0=26.9 and u1=6.2 and wind-height scaling exponent 0.2.

**Used by:** `methods/src/energy_methods/degradation_weather.py`.

### wald_2018_spectral

Wald, Lucien (2018). **A simple algorithm for the computation of the spectral distribution of the solar irradiance at surface**. MINES ParisTech. [Source](https://hal.science/hal-01693473)

**Role:** implemented. UVA/UVB clearness-index regressions, as reproduced in the 2019 degradation mapping paper equations 5–8. The implementation clamps kt to 0.1–0.7 and documents missing/zero-TOA handling.

**Used by:** `methods/src/energy_methods/degradation_weather.py`.

### kaaya_2020_thesis

Kaaya, Ismail (2020). **Photovoltaic Lifetime Forecast: Models for long-term photovoltaic degradation prediction and forecast**. University of Málaga, School of Industrial Engineering. [Source](https://www.uma.es/media/tinyimages/file/Ismail__Thesis2.pdf)

**Role:** implemented. Author-accessible verification of the 2019 Kaaya model coefficients: Table 4.3, printed p.45 / PDF p.55. Gran Canaria mono-Si calibration: Ah=4.91e7, Eh=0.74, n=1.90; Ap=71.83, Ep=0.45, x=0.63; Atm=2.04, Etm=0.43, theta=2.24. A_N=1 and the applied analysis aggregation/cycling conventions are explicit study choices, not newly fitted coefficients.

**Used by:** `analysis/src/energy_analysis/degradation/pipeline.py`, `analysis/examples/degradation/kaaya_2019_scenario.json`.

### copernicus_cds_api

European Centre for Medium-Range Weather Forecasts (ECMWF) (n.d.). **Climate Data Store: CDSAPI setup**. [Source](https://cds.climate.copernicus.eu/how-to-api)

**Role:** software. Official CDS API setup and access guidance. The connector uses optional cdsapi, personal access tokens and manually accepted dataset terms. Cite the selected dataset separately; native downloads are not normalized observations. SDK version and artifact/request hashes are recorded per acquisition.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/cds`, `data-retrieval/src/energy_data_retrieval/grid_discovery.py`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### era5_single_levels_monthly

Copernicus Climate Change Service (C3S) Climate Data Store (CDS) (2019). **ERA5 monthly averaged data on single levels from 1940 to present**. [DOI: 10.24381/cds.f17050d7](https://doi.org/10.24381/cds.f17050d7)

**Role:** data. Official CDS catalogue publication date 18 April 2019 and dataset DOI verified. Monthly averaged reanalysis retains native units and accumulation semantics; it is not an hourly station observation. Record the actual retrieval date, selection and downloaded artifact hash because upstream ERA5T can be revised.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/cds`, `data-retrieval/src/energy_data_retrieval/grid_discovery.py`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### noaa_psl_ncep_ncar_reanalysis_1

NOAA Physical Sciences Laboratory (n.d.). **NCEP-NCAR Reanalysis 1**. [Source](https://psl.noaa.gov/data/gridded/data.ncep.reanalysis.html)

**Role:** data. Source of the 1991–2020 air temperature, precipitation-rate and downward surface solar-flux climatologies and Gaussian land mask used in the worldwide KGPV gallery fixture. The 5-degree CSV is a derived illustration, not an official NOAA product or reproduction of the published KGPV map. Exact source URLs, retrieval timestamps, checksums, unit conversions, coverage and clipping policy are recorded in examples/analysis/kgpv_worldwide_provenance.json. NOAA lists no usage restrictions and requests attribution to NOAA PSL, Boulder, Colorado, USA; see https://psl.noaa.gov/data/help/. The soiling/snow example reuses the reviewed KGPV fixture's coarse land mask.

**Used by:** `examples/analysis/plot_kgpv_worldwide.py`, `scripts/prepare_kgpv_worldwide.py`, `docs/kgpv.md`, `scripts/prepare_weather_risk_example.py`, `examples/analysis/plot_soiling_snow_risk.py`, `docs/soiling-snow.md`.

### kalnay_1996_ncep_ncar

Kalnay, E.; Kanamitsu, M.; Kistler, R.; Collins, W.; Deaven, D.; Gandin, L.; Iredell, M.; Saha, S.; White, G.; Woollen, J.; Zhu, Y.; Chelliah, M.; Ebisuzaki, W.; Higgins, W.; Janowiak, J.; Mo, K. C.; Ropelewski, C.; Wang, J.; Leetmaa, A.; Reynolds, R.; Jenne, R.; Joseph, D. (1996). **The NCEP/NCAR 40-Year Reanalysis Project**. Bulletin of the American Meteorological Society, 77(3), 437-470. [DOI: 10.1175/1520-0477(1996)077<0437:TNYRP>2.0.CO;2](https://doi.org/10.1175/1520-0477%281996%29077%3C0437%3ATNYRP%3E2.0.CO%3B2)

**Role:** background. Methodological reference requested by NOAA PSL for NCEP/NCAR Reanalysis 1. Bibliographic metadata verified against NOAA NCEI study 10873 and the publisher; the separately identified PSL files, not the paleo study subset, supply this example.

**Used by:** `examples/analysis/plot_kgpv_worldwide.py`, `scripts/prepare_kgpv_worldwide.py`, `docs/kgpv.md`.

### cordero_2018_soiling

Cordero, R. R.; Damiani, A.; Laroze, D.; MacDonell, S.; Jorquera, J.; Sepúlveda, E.; Feron, S.; Llanillo, P.; Labbe, F.; Carrasco, J.; Ferrer, J.; Torres, G. (2018). **Effects of soiling on photovoltaic (PV) modules in the Atacama Desert**. Scientific Reports, 8, 13943. [DOI: 10.1038/s41598-018-32291-8](https://doi.org/10.1038/s41598-018-32291-8)

**Role:** implemented. Underlying annual-average AOD/soiling correlation from Chilean sites; implemented as the piecewise thesis Eq. 3.2, with explicit boundary conventions. This is a daily-rate indicator, not a cleaning-aware annual loss model or a globally validated dust-event model.

**Used by:** `methods/src/energy_methods/weather_risk.py`, `methods/src/energy_methods/weather_risk_mapping.py`, `docs/soiling-snow.md`, `examples/analysis/plot_soiling_snow_risk.py`.

### ryberg_freeman_2017_snow

Ryberg, David Severin; Freeman, Janine (2017). **Integration, Validation, and Application of a PV Snow Coverage Model in SAM**. NREL/TP-6A20-68705. National Renewable Energy Laboratory. [DOI: 10.2172/1374128](https://doi.org/10.2172/1374128)

**Role:** background. Underlying snow-model report cited by the thesis. The repository implements the thesis's logarithmic annual snow-depth fit for fixed latitude-tilt modules, not the full SAM snow-coverage model. Centimetre units come from thesis Figure 3.4; low-domain and exact-boundary extensions are explicit.

**Used by:** `methods/src/energy_methods/weather_risk.py`, `methods/src/energy_methods/weather_risk_mapping.py`, `docs/soiling-snow.md`, `examples/analysis/plot_soiling_snow_risk.py`.

### nasa_power_aerosols

NASA POWER Project (n.d.). **NASA POWER: Cloud and Aerosol Sources**. [Source](https://power.larc.nasa.gov/docs/methodology/data/sources_clds_aerosols/)

**Role:** data. Source documentation for total dimensionless AOD at 550 nm from CERES SYN1deg/MATCH. The example explicitly requests unadjusted AOD_55 and UTC dates, averages daily values annually, and credits NASA POWER/CERES. This replaces the thesis ECMWF aerosol source; modelled AOD is not observed surface deposition.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/nasa_power`, `scripts/prepare_weather_risk_example.py`, `examples/analysis/plot_soiling_snow_risk.py`, `docs/soiling-snow.md`, `examples/analysis/plot_country_risk.py`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### munoz_sabater_2021_era5_land

Muñoz-Sabater, Joaquín; Dutra, Emanuel; Agustí-Panareda, Anna; Albergel, Clément; Arduini, Gabriele; Balsamo, Gianpaolo; Boussetta, Souhail; Choulga, Margarita; Harrigan, Shaun; Hersbach, Hans; Martens, Brecht; Miralles, Diego G.; Piles, María; Rodríguez-Fernández, Nemesio J.; Zsoter, Ervin; Buontempo, Carlo; Thépaut, Jean-Noël (2021). **ERA5-Land: a state-of-the-art global reanalysis dataset for land applications**. Earth System Science Data, 13, 4349-4383. [DOI: 10.5194/essd-13-4349-2021](https://doi.org/10.5194/essd-13-4349-2021)

**Role:** data. Underlying ERA5-Land reanalysis for the example snow inputs, explicitly selected through Open-Meteo. The wrapper returns physical ground snow depth in metres; native ERA5 water-equivalent sd is not substituted. Credit Copernicus/ERA5-Land and the wrapper. Source snow biases remain; this is an alternative dataset to the thesis ERA5 inputs.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/open_meteo/snow.py`, `scripts/prepare_weather_risk_example.py`, `examples/analysis/plot_soiling_snow_risk.py`, `docs/soiling-snow.md`, `examples/analysis/plot_country_risk.py`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### aemo_dispatch_scada

Australian Energy Market Operator (n.d.). **MMS Data Model: DISPATCH_UNIT_SCADA**. [Source](https://visualisations.aemo.com.au/aemo/nemweb/MMSDataModelReport/Electricity/MMS%20Data%20Model%20Report_files/MMS_123.htm)

**Role:** data. Official schema for public DUID-level instantaneous SCADA MW at the start of each dispatch interval. SETTLEMENTDATE remains the published label; readings are not interval means or settlement energy. Scheduled, semi-scheduled and selected non-scheduled units are included where SCADA is available. Technology and generator/load class require a verified roster.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/aemo/client.py`, `examples/connectors/plot_generation_aemo.py`, `docs/generation-connectors.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### aemo_nemweb

Australian Energy Market Operator (n.d.). **NEMWeb: public Dispatch SCADA archives**. [Source](https://nemweb.com.au/Reports/ARCHIVE/Dispatch_SCADA/)

**Role:** data. Official daily archive listing. The connector discovers current or archived files and verifies bounded nested ZIP/CSV contents. The gallery retains 864 original rows from three DUIDs on 27 October 2026, with source URL, retrieval time, full-archive and subset hashes. Archive retention and publication coverage are finite.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/aemo/client.py`, `examples/connectors/plot_generation_aemo.py`, `docs/generation-connectors.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### aemo_market_time

Australian Energy Market Operator (n.d.). **AEMO Markets Portal glossary: AEST and market time**. [Source](https://markets-portal-help.docs.public.aemo.com.au/Content/TOC_common-topics-DOnotChange/Glossary.htm)

**Role:** data. Official market-time convention: fixed Australian Eastern Standard Time, UTC+10, without daylight-saving changes. The connector preserves the published dispatch label and converts that label to UTC.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/aemo/client.py`, `examples/connectors/plot_generation_aemo.py`, `docs/generation-connectors.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### eia_api_v2

U.S. Energy Information Administration (n.d.). **EIA API Technical Documentation, API v2**. [Source](https://www.eia.gov/opendata/documentation.php)

**Role:** data. Official API routes, data/facet parameters, registered-key access and maximum JSON page size. The connector uses stable sorting and bounded offset pagination for hourly fuel-type generation and monthly facility-fuel net generation. Credentialed routes were contract-tested without asserting authenticated live validation.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/eia/client.py`, `examples/connectors/plot_generation_eia.py`, `docs/generation-connectors.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### eia_930

U.S. Energy Information Administration (n.d.). **Hourly Electric Grid Monitor: data coverage, quality and time reporting**. [Source](https://www.eia.gov/electricity/930-content/about.html)

**Role:** data. Official EIA-930 scope and hour-ending conventions. Hourly energy uses explicit UTC interval bounds; public balance-file hourly average MW is multiplied by one hour to obtain MWh. No imputed/adjusted values substitute for missing reported data. Regional aggregates overlap individual balancing authorities; distributed-generation coverage is incomplete.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/eia/client.py`, `examples/connectors/plot_generation_eia.py`, `docs/generation-connectors.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### eia_930_source_codes

U.S. Energy Information Administration (n.d.). **EIA-930 Reference Tables: energy source codes**. [Source](https://www.eia.gov/electricity/930-content/EIA930_Reference_Tables.xlsx)

**Role:** data. Official code workbook used to verify fuel and storage/hybrid codes, including the expanded 2025 taxonomy. Unknown columns or unavailable requested fuels fail explicitly; aggregate/detail categories are not silently summed.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/eia/client.py`, `examples/connectors/plot_generation_eia.py`, `docs/generation-connectors.md`.

### eia_930_instructions

U.S. Energy Information Administration (n.d.). **Form EIA-930 Instructions**. [Source](https://www.eia.gov/survey/form/eia_930/instructions.pdf)

**Role:** data. Official reporting instructions for hourly integrated generation and the updated storage/hybrid energy-source categories. A schema/code reference, not independent evidence that all requested observations exist.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/eia/client.py`, `examples/connectors/plot_generation_eia.py`, `docs/generation-connectors.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### ree_redata_api

Red Eléctrica de España (n.d.). **REData API: request parameters, geographic scopes and JSON responses**. [Source](https://www.ree.es/en/datos/apidata)

**Role:** data. Official public generation-structure endpoint and complete geographic filter contract. Dates are inclusive source calendar dates; returned UTC offsets and last-update metadata remain. The connector bounds calendar-year chunks and supports daily/monthly/yearly full-period generation.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/ree/client.py`, `examples/connectors/plot_generation_ree.py`, `docs/generation-connectors.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### ree_generation_structure

Red Eléctrica de España (n.d.). **Generation structure by technology**. [Source](https://www.ree.es/es/datos/generacion/estructura-generacion)

**Role:** data. System-level generation by technology. API values are MWh even when the website scales charts to GWh; the scale was cross-checked against the official 2024 report (https://www.sistemaelectrico-ree.es/es/2024/informe-del-sistema-electrico/generacion/generacion-de-energia-electrica/generacion-total-de-energia-electrica). Totals remain separate to prevent double counting. The gallery preserves a complete June 2024 daily response, with checksums and update metadata. This product is not plant telemetry or total estimated self-consumption. Provider terms apply.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/ree/client.py`, `examples/connectors/plot_generation_ree.py`, `docs/generation-connectors.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### entsoe_transparency_api

European Network of Transmission System Operators for Electricity (n.d.). **ENTSO-E Transparency Platform REST API parameters**. [Source](https://transparencyplatform.zendesk.com/hc/en-us/articles/15696716612372-Request-Parameters)

**Role:** data. Official actual-generation requests A75/A16 by production type and A73/A16 by published unit, EIC domains, UTC bounds and security token. Current production endpoint is https://web-api.tp.entsoe.eu/api. Credentials are environment-only and redacted. Authenticated live retrieval was not performed; no-data HTTP 200 acknowledgements and other responses follow the official Query-Response guidance.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/entsoe/client.py`, `examples/connectors/plot_generation_entsoe.py`, `docs/generation-connectors.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### entsoe_generation_data_descriptions

European Network of Transmission System Operators for Electricity (n.d.). **ENTSO-E Transparency Platform Detailed Data Descriptions, version 2 release 5**. [Source](https://www.entsoe.eu/fileadmin/user_upload/_library/resources/Transparency/02_MoP%20Ref02%20-%20DDD_V2R5.pdf)

**Role:** data. Official generation definitions, interval-average net power and publication scope. A73 does not enumerate every small plant; aggregate actual generation can contain submitted estimates. Generation and consumption remain separate flows; unit EICs, production type, document revisions and native intervals are preserved.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/entsoe/client.py`, `examples/connectors/plot_generation_entsoe.py`, `docs/generation-connectors.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### entsoe_curve_types

European Network of Transmission System Operators for Electricity (n.d.). **CurveType A01 versus CurveType A03**. [Source](https://transparencyplatform.zendesk.com/hc/en-us/articles/30262342482961-CurveType-A01-vs-CurveType-A03)

**Role:** data. Official fixed- and variable-block XML semantics. A03 is expanded within each Period at the published resolution, including explicit missing blocks; A01 absent positions remain missing. No value is carried across Period boundaries. Official public XML examples validate schema compatibility but are not claimed to be operational measurements.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/entsoe/client.py`, `examples/connectors/plot_generation_entsoe.py`, `docs/generation-connectors.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### natural_earth_countries

Natural Earth contributors (n.d.). **Natural Earth: Admin 0 - Countries**. [Source](https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-0-countries/)

**Role:** data. Public-domain country polygons at 1:10, 1:50 and 1:110 million map scales; default de facto boundaries. Country membership follows the source administrative units. The checked-in country example preserves unsimplified Austria/Slovenia contours from version 5.1.1, with the archive and subset checksums recorded. The worldwide connector coverage fixture retains 176 unchanged 1:110 million country geometries from the same version; Antarctica is explicitly excluded because its original unsplit world-spanning ring fails the country-map antimeridian contract. Its provenance records the source archive, derived GeoJSON checksum and exclusion. Country shapes supply geographic context rather than electrical service territories or evidence of observation availability. Map scale is not metre accuracy; no scientific climate resolution is inferred from boundary detail.

**Used by:** `methods/src/energy_methods/country_boundaries.py`, `methods/src/energy_methods/country_mapping.py`, `docs/country-mapping.md`, `examples/analysis/plot_country_risk.py`, `data-retrieval/src/energy_data_retrieval/sources/natural_earth`, `scripts/prepare_weather_risk_example.py`, `analysis/src/energy_analysis/chile_kgpv/pipeline.py`, `examples/analysis/plot_kgpv_chile.py`, `docs/kgpv-chile.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`, `scripts/prepare_connector_coverage.py`, `examples/connectors/data/generation_coverage_world.geojson`, `examples/connectors/data/generation_coverage_provenance.json`, `examples/connectors/plot_candelaria_solar_farm.py`, `examples/connectors/data/candelaria_site.json`, `scripts/prepare_candelaria_imagery.py`.

### shapely_documentation

Shapely contributors (n.d.). **Shapely documentation**. [Source](https://shapely.readthedocs.io/en/stable/)

**Role:** software. Polygon topology, point/cell intersection masks, transformations and exact country-cell footprint clipping. Operations are planar longitude/latitude; country areas require geodesic or equal-area calculations. Invalid geometries and unsplit antimeridian rings are rejected explicitly.

**Used by:** `methods/src/energy_methods/country_boundaries.py`, `methods/src/energy_methods/country_mapping.py`, `docs/country-mapping.md`, `examples/analysis/plot_country_risk.py`.

### pyproj_documentation

PyProj contributors (n.d.). **PyProj documentation: Transformer**. [Source](https://pyproj4.github.io/pyproj/stable/api/transformer.html)

**Role:** software. Reads declared shapefile CRS and transforms selected boundaries to EPSG:4326 using always_xy=True. Missing shapefile CRS requires explicit caller input; no coordinate system is guessed from coordinate magnitudes.

**Used by:** `methods/src/energy_methods/country_boundaries.py`, `docs/country-mapping.md`.

### pyshp_documentation

PyShp contributors (n.d.). **PyShp: Python Shapefile Library**. [Source](https://github.com/GeospatialPython/pyshp)

**Role:** software. Reads and writes ESRI shapefile geometry/attributes and companion files. Selected exports retain polygon holes and islands with ESRI ring orientation; the PRJ and CPG files declare WGS84 and UTF-8.

**Used by:** `methods/src/energy_methods/country_boundaries.py`, `docs/country-mapping.md`.

### ons_hourly_generation

Operador Nacional do Sistema Elétrico (n.d.). **Geração por Usina em Base Horária**. [Source](https://dados.ons.org.br/dataset/geracao-usina-2)

**Role:** data. Verified plant/group average MW (MWmed); Type III and MMGD estimate/forecast categories are excluded by default. Native labels and an explicit source-clock interpretation are retained. Public Parquet resources are discovered through the CKAN catalogue.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/ons/client.py`, `data-retrieval/src/energy_data_retrieval/sources/ons/README.md`, `examples/connectors/plot_generation_ons.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### ons_pv_curtailment

Operador Nacional do Sistema Elétrico (n.d.). **Restrições de operação por constrained-off: usinas fotovoltaicas, detalhamento**. [Source](https://dados.ons.org.br/dataset/restricao_coff_fotovoltaica_detail)

**Role:** data. Separate half-hour photovoltaic detail from April 2024. Verified output, estimated/reference values, irradiance flags and restrictions remain distinct; the adapter does not infer curtailment energy from an estimated/actual difference.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/ons/client.py`, `data-retrieval/src/energy_data_retrieval/sources/ons/README.md`, `examples/connectors/plot_generation_ons.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `scripts/prepare_forecast_benchmark.py`, `analysis/src/energy_analysis/forecast_benchmark.py`, `examples/analysis/plot_forecast_model_benchmark.py`, `docs/forecast-benchmark.md`.

### ieso_generator_output

Independent Electricity System Operator (n.d.). **Generator Output and Capability report: format and definitions**. [Source](https://reports-public.ieso.ca/docrefs/helpfile/GenOutputCapability_h4.pdf)

**Role:** data. Ontario published generator output MW, hourly hour-ending labels in fixed Eastern Standard Time. Capability is not generation. The public recent XML archive is not a promise of complete historical or distributed-generation coverage.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/ieso/client.py`, `data-retrieval/src/energy_data_retrieval/sources/ieso/README.md`, `examples/connectors/plot_generation_ieso.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### ieso_report_directory

Independent Electricity System Operator (n.d.). **IESO power data directory**. [Source](https://www.ieso.ca/en/power-data/data-directory)

**Role:** data. Official report discovery and publication scope. Gallery observations are captured from native public generator-output XML and retain a source/selection/checksum manifest.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/ieso/client.py`, `data-retrieval/src/energy_data_retrieval/sources/ieso/README.md`, `examples/connectors/plot_generation_ieso.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### xm_simem_actual_generation

XM (n.d.). **SIMEM: generación real horaria por recurso, dataset 055A4D**. [Source](https://www.simem.co/datadetail/055a4d5f-3616-45e3-9bcd-1d3e3a4a47bd)

**Role:** data. Actual hourly generation-boundary records, distinct from estimated daily SCADA dataset E17D25. Native kWh is retained beside normalized MWh; an explicit settlement revision defaults to TXF without fallback. Source FechaHora is interpreted as Colombia UTC-05 without shifting its label.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/xm/client.py`, `data-retrieval/src/energy_data_retrieval/sources/xm/README.md`, `examples/connectors/plot_generation_xm.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### xm_api_documentation

XM analytics team (n.d.). **Official SIMEM API client and query semantics**. [Source](https://github.com/EquipoAnaliticaXM/API_XM/blob/master/pydataxm/pydatasimem.py)

**Role:** data. Provider-maintained query documentation supports public dataset/date and settlement-version filtering. The adapter validates metadata, bounds request/row counts and preserves native resource/agent identifiers and revision.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/xm/client.py`, `data-retrieval/src/energy_data_retrieval/sources/xm/README.md`, `examples/connectors/plot_generation_xm.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### aeso_historical_generation

Alberta Electric System Operator (n.d.). **AESO historical generation data**. [Source](https://www.aeso.ca/market/market-and-system-reporting/data-requests/historical-generation-data/)

**Role:** data. Public CSD Generation five-minute/hourly archive exports. Volume is interval-average MW, not MWh; explicit Date (MST) is fixed UTC-07 and Date (MPT) is retained. Local import follows user download/extraction, preserves the exact file hash and performs no historical API call.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/aeso/client.py`, `data-retrieval/src/energy_data_retrieval/sources/aeso/README.md`, `examples/connectors/plot_generation_aeso.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### aeso_current_generation_api

Alberta Electric System Operator (n.d.). **Current Supply Demand API v1: generation by asset**. [Source](https://developer-apim.aeso.ca/api-details#api=currentsupplydemand-api-v1&operation=getCSDReportByAsset)

**Role:** data. Current operational net_generation MW with explicit UTC timestamp, distinct capacity/reserve fields and an API-KEY header. Official documented schema was verified and mocked; no authenticated live response is claimed. Scope is published reporting assets over 5 MW.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/aeso/client.py`, `data-retrieval/src/energy_data_retrieval/sources/aeso/README.md`, `examples/connectors/plot_generation_aeso.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### adme_open_data

Administración del Mercado Eléctrico (n.d.). **ADME datos abiertos**. [Source](https://www.adme.com.uy/datosabiertos.html)

**Role:** data. Official Uruguayan market/open-data entry point. The implementation uses the available public native SCADA archive rather than the legacy CSV endpoint that returned PHP warnings during verification.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/adme/client.py`, `data-retrieval/src/energy_data_retrieval/sources/adme/README.md`, `examples/connectors/plot_generation_adme.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### adme_scada_archive

Administración del Mercado Eléctrico (n.d.). **ADME native plant SCADA SAS archive**. [Source](https://pronos.adme.com.uy/svg/pronos/cache_series_scada/)

**Role:** data. Public archive discovery and bounded six-header-line SAS parsing. Actual GETOTMEDP.AV MW is distinguished from dispatch limits and forecasts, the declared sample period is retained, and missing sentinels remain missing. The source labels have no offset; the explicit default interpretation is America/Montevideo.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/adme/client.py`, `data-retrieval/src/energy_data_retrieval/sources/adme/README.md`, `examples/connectors/plot_generation_adme.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### elexon_insights_api

Elexon (n.d.). **Elexon Insights API documentation**. [Source](https://developer.data.elexon.co.uk/)

**Role:** data. Public B1610 metered-volume acquisition with bounded response/pagination checks, UTC half-hour-end labels validated against Great Britain settlement dates and periods, and request provenance.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/elexon/client.py`, `data-retrieval/src/energy_data_retrieval/sources/elexon/README.md`, `examples/connectors/plot_generation_elexon.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### elexon_b1610_metered_volumes

Elexon (n.d.). **How to get more detailed metered volume data from Insights Solution**. [Source](https://www.elexon.co.uk/bsc/article/bsc-insight-how-to-get-more-detailed-metered-volume-data-from-our-insights-solution/)

**Role:** data. BM-unit signed half-hour metered MWh. A BM unit is not automatically an individual PV plant, negative values can represent import, and published records can be revised.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/elexon/client.py`, `data-retrieval/src/energy_data_retrieval/sources/elexon/README.md`, `examples/connectors/plot_generation_elexon.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### rte_eco2mix_consolidated

Réseau de Transport d’Électricité (n.d.). **éCO2mix national: consolidated and definitive data**. [Source](https://odre.opendatasoft.com/explore/dataset/eco2mix-national-cons-def/)

**Role:** data. National consolidated actual technology generation in MW at half-hour resolution. Quarter-hour rows containing forecasts only are excluded; missing values at actual half-hour labels remain missing. Pumping, totals and overlapping technology subcategories are kept outside the selected disjoint generation series.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/rte/client.py`, `data-retrieval/src/energy_data_retrieval/sources/rte/README.md`, `examples/connectors/plot_generation_rte.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### rte_eco2mix_api

Réseau de Transport d’Électricité (n.d.). **ODRÉ Explore API for consolidated éCO2mix national data**. [Source](https://odre.opendatasoft.com/explore/dataset/eco2mix-national-cons-def/api/)

**Role:** data. Public offset-aware queries and explicit pagination with total-count, duplicate-page and row/request bounds. This connector does not claim the separate live or regional products.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/rte/client.py`, `data-retrieval/src/energy_data_retrieval/sources/rte/README.md`, `examples/connectors/plot_generation_rte.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### caiso_todays_outlook_supply

California Independent System Operator (n.d.). **CAISO Today’s Outlook: supply and fuel mix**. [Source](https://www.caiso.com/todays-outlook/supply)

**Role:** data. Operational five-minute fuel-mix MW from public daily CSV files. Imports, storage and mixed Other supply (including proxy demand response) remain distinct flows. Source Pacific local labels on DST clock-change days may be ambiguous or nonexistent; the adapter fails rather than fabricate a UTC timeline. These data are not settlement meter records.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/caiso/client.py`, `data-retrieval/src/energy_data_retrieval/sources/caiso/README.md`, `examples/connectors/plot_generation_caiso.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### smard_generation_user_guide

Bundesnetzagentur (n.d.). **SMARD user guide: market data and electricity generation**. [Source](https://www.smard.de/resource/blob/205652/63fcff2c9813096fa2229d769da164ef/smard-user-guide-09-2021-data.pdf)

**Role:** data. Verified public German solar, onshore-wind and offshore-wind generation series at quarter-hour resolution in MWh. Weekly data are located through source index JSON and filtered by German civil dates; no additional country or unverified technology identifiers are implied.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/smard/client.py`, `data-retrieval/src/energy_data_retrieval/sources/smard/README.md`, `examples/connectors/plot_generation_smard.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### smard_data_use

Bundesnetzagentur (n.d.). **SMARD data use**. [Source](https://www.smard.de/en/datennutzung)

**Role:** data. Provider reuse and attribution guidance for SMARD public data. Gallery captures preserve original series responses, exact source requests and checksums; applicable source terms remain authoritative.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/smard/client.py`, `data-retrieval/src/energy_data_retrieval/sources/smard/README.md`, `examples/connectors/plot_generation_smard.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### nz_emi_generation

Electricity Authority New Zealand (n.d.). **Generation output: plant/connection metered generation**. [Source](https://www.ea.govt.nz/data-and-insights/datasets/wholesale/generation/generation-output/)

**Role:** data. Metered injection in kWh by plant/connection and half-hour trading period. Pacific/Auckland civil days have 46, 48 or 50 intervals; the adapter validates the native trading-period layout and preserves source identities and missing values.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/emi/client.py`, `data-retrieval/src/energy_data_retrieval/sources/emi/README.md`, `examples/connectors/plot_generation_emi.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### nz_emi_license

Electricity Authority New Zealand (n.d.). **EMI legal information**. [Source](https://www.emi.ea.govt.nz/LegalInformation)

**Role:** data. Provider reuse terms generally use Creative Commons Attribution 4.0 with stated exceptions. The gallery preserves attributed source selections and does not extend those terms to unrelated third-party data.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/emi/client.py`, `data-retrieval/src/energy_data_retrieval/sources/emi/README.md`, `examples/connectors/plot_generation_emi.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### tepco_generation

TEPCO Power Grid (n.d.). **Tokyo-area electricity supply and demand data**. [Source](https://www.tepco.co.jp/forecast/html/area_jukyu-j.html)

**Role:** data. Monthly native CP932 CSV, current _03 schema from February 2024. The unit row specifies average MW or ten-thousand kW, which is converted explicitly. Half-hour technology generation is separate from demand, total, storage, imports and curtailment.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/tepco/client.py`, `data-retrieval/src/energy_data_retrieval/sources/tepco/README.md`, `examples/connectors/plot_generation_tepco.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### tepco_generation_definitions

TEPCO Power Grid (n.d.). **Tokyo-area supply/demand data definitions and use conditions**. [Source](https://www.tepco.co.jp/forecast/html/area_data-j.html)

**Role:** data. Provider definitions, estimation/revision caveats and Tokyo-area scope. Source labels use Japan UTC+09. The gallery records the exact raw CP932 hash and its documented UTF-8 subset transformation.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/tepco/client.py`, `data-retrieval/src/energy_data_retrieval/sources/tepco/README.md`, `examples/connectors/plot_generation_tepco.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### taipower_live_generation

Taiwan Power Company (n.d.). **Taipower real-time generation by unit**. [Source](https://data.gov.tw/en/datasets/8931)

**Role:** data. Public current MW snapshot, not a ten-minute average. Published assets, groups, subtotals and storage load are distinguished; aggregate and load rows are excluded by default. Source time is UTC+08.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/taipower/client.py`, `data-retrieval/src/energy_data_retrieval/sources/taipower/README.md`, `examples/connectors/plot_generation_taipower.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### taipower_generation_history

Taiwan Power Company (n.d.). **Taipower historical generating-unit power output**. [Source](https://data.gov.tw/en/datasets/37331)

**Role:** data. Documents the separate delayed historical product. The implemented connector is bounded current-snapshot retrieval and does not claim automatic ingestion of the much larger historical download. Taiwan Open Government Data License terms apply to the provider dataset.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/taipower/client.py`, `data-retrieval/src/energy_data_retrieval/sources/taipower/README.md`, `examples/connectors/plot_generation_taipower.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### kpx_regional_solar

Korea Power Exchange (n.d.). **Korea Power Exchange: regional hourly solar generation**. [Source](https://www.data.go.kr/data/15103243/openapi.do)

**Role:** data. Approved-key API for net market-traded regional solar energy in MWh. It does not cover all national rooftop PV; ESS operation can produce nighttime output. The endpoint and native schema were verified from official Swagger, with mocked retrieval tests and no authenticated live-data claim.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/kpx/client.py`, `data-retrieval/src/energy_data_retrieval/sources/kpx/README.md`, `examples/connectors/plot_generation_kpx.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### kpx_trading_periods

Korea Power Exchange (n.d.). **Korean electricity market trading-period definitions**. [Source](https://marketrule.kpx.or.kr/lmxsrv/law/joHistoryContent.do?DATE_END=20231230&DATE_START=20210501&SEQ=2&SEQ_CONTENTS=7335)

**Role:** data. Native tradeNo values 01..24 are hour-ending market periods; 01 maps to 00:00–01:00 KST. The adapter retains interval boundaries and UTC+09 source semantics.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/kpx/client.py`, `data-retrieval/src/energy_data_retrieval/sources/kpx/README.md`, `examples/connectors/plot_generation_kpx.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### kpx_data_guide

Korea Power Exchange (n.d.). **KPX public data usage guide**. [Source](https://new.kpx.or.kr/boardDownload.es?bid=0045&list_no=71003&seq=2)

**Role:** data. Provider field definitions, access requirements and product scope. The serviceKey is read from KPX_API_KEY, sent only as a secret parameter and excluded from caches, logs and provenance.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/kpx/client.py`, `data-retrieval/src/energy_data_retrieval/sources/kpx/README.md`, `examples/connectors/plot_generation_kpx.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### eskom_hourly_renewables

Eskom (n.d.). **Hourly renewable generation**. [Source](https://www.eskom.co.za/dataportal/renewables-performance/hourly-renewable-generation/)

**Role:** data. Eskom-owned/contracted renewable wind, PV, CSP and other output, excluding embedded generation. Current exact Hourly_Generation CSV URLs are discovered through the public media catalogue because the chart page can retain a stale upload link.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/eskom/client.py`, `data-retrieval/src/energy_data_retrieval/sources/eskom/README.md`, `examples/connectors/plot_generation_eskom.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### eskom_generation_statistics

Eskom (n.d.). **Weekly system status report: renewable generation contribution**. [Source](https://www.eskom.co.za/wp-content/uploads/2024/04/Weekly_System_Status_Report_2024_w16.pdf)

**Role:** data. Supports the MW contribution convention used for Eskom renewable statistics. The hourly CSV uses hour-beginning labels in South African UTC+02; the adapter calls it reported hourly power without inferring a finer sampling definition or independently metered MWh.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/eskom/client.py`, `data-retrieval/src/energy_data_retrieval/sources/eskom/README.md`, `examples/connectors/plot_generation_eskom.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### pvdaq_public_archive

U.S. Department of Energy, Open Energy Data Initiative (n.d.). **PVDAQ public photovoltaic performance data archive**. [Source](https://data.openei.org/submissions/4568)

**Role:** data. Public anonymous OEDI daily PV system measurements and channel metadata. The adapter selects a bounded system/date range; it preserves native columns and requires explicit power units and source clock. Missing archive files fail instead of generating observations.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/pvdaq/client.py`, `data-retrieval/src/energy_data_retrieval/sources/pvdaq/README.md`, `examples/connectors/plot_generation_pvdaq.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### pvdaq_data_dictionary

Open Energy Data Initiative (n.d.). **PVDAQ data dictionary and public archive schema**. [Source](https://github.com/openEDI/documentation/blob/main/pvdaq.md)

**Role:** data. Defines system/site metadata, measured_on and UTC fields, and channel units/scaling/aggregation. The real system 4 example uses metric315 AC power in W, scale1/offset0, and an explicit winter UTC-07 clock. Parquet channel metadata is kept alongside the captured native CSV.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/pvdaq/client.py`, `data-retrieval/src/energy_data_retrieval/sources/pvdaq/README.md`, `examples/connectors/plot_generation_pvdaq.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### nist_pv_testbeds

National Institute of Standards and Technology (n.d.). **NIST photovoltaic testbeds and data portal**. [Source](https://www.nist.gov/el/beed/heat-transfer-alternative-energy-systems/photovoltaic-testbeds)

**Role:** data. Instrumented Ground, Roof and Canopy photovoltaic arrays in Gaithersburg. The connector imports user-downloaded native CSV/TOA5 exports; no portal-token handling or unattended bulk-download claim. No real NIST capture is bundled.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/nist/client.py`, `data-retrieval/src/energy_data_retrieval/sources/nist/README.md`, `examples/connectors/plot_generation_nist.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### nist_pv_dictionary

National Institute of Standards and Technology (n.d.). **NIST photovoltaic testbed and weather station data dictionary**. [Source](https://www.nist.gov/document/datadictionarysupplementalcontentpdf)

**Role:** data. Native TIMESTAMP is local standard time. InvPAC_kW and PwrMtrP_kW are AC real-power kW channels; one-minute average suffixes and instantaneous channels remain distinct from accumulated kWh registers.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/nist/client.py`, `data-retrieval/src/energy_data_retrieval/sources/nist/README.md`, `examples/connectors/plot_generation_nist.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### nist_pv_measurements_paper

Boyd, Matthew (2017). **Performance Data from the NIST Photovoltaic Arrays and Weather Station**. Journal of Research of the National Institute of Standards and Technology, 122, 40. [DOI: 10.6028/jres.122.040](https://doi.org/10.6028/jres.122.040)

**Role:** data. Verifies fixed Eastern Standard Time with no daylight saving, one-minute aggregate suffixes, one-second instantaneous channels and missing NAN readings. The importer preserves signed and missing observations and does not infer interval-edge alignment.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/nist/client.py`, `data-retrieval/src/energy_data_retrieval/sources/nist/README.md`, `examples/connectors/plot_generation_nist.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### dkasc_download

Desert Knowledge Australia (n.d.). **Desert Knowledge Australia Solar Centre data downloads**. [Source](https://dkasolarcentre.com.au/download?location=alice-springs)

**Role:** data. Measured PV array exports are obtained through the provider form. The adapter imports a user-downloaded native CSV with exact selected columns/date format and records its hash; it does not submit personal details or accept provider terms for the user.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/dkasc/client.py`, `data-retrieval/src/energy_data_retrieval/sources/dkasc/README.md`, `examples/connectors/plot_generation_dkasc.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### dkasc_data_parameters

Desert Knowledge Australia (n.d.). **DKASC glossary: measured solar generation data parameters**. [Source](https://dkasolarcentre.com.au/glossary)

**Role:** data. Five-minute average AC power in kW is distinct from cumulative kWh registers. Total and phase channels remain separate. Alice Springs source labels are normalized using Australia/Darwin UTC+09:30 and retain native values.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/dkasc/client.py`, `data-retrieval/src/energy_data_retrieval/sources/dkasc/README.md`, `examples/connectors/plot_generation_dkasc.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### dkasc_data_terms

Desert Knowledge Australia (n.d.). **DKASC data terms and conditions**. [Source](https://dkasolarcentre.com.au/download/terms-conditions)

**Role:** data. Provider terms distinguish limited unaltered excerpts up to 5000 data cells with attribution/disclaimer from larger redistribution requiring permission. No DKASC observations are bundled; the gallery is an import workflow until a real export is supplied.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/dkasc/client.py`, `data-retrieval/src/energy_data_retrieval/sources/dkasc/README.md`, `examples/connectors/plot_generation_dkasc.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

### canaryclim_2025_data

Karger, D. N.; Collart, F.; Vanderpoorten, A.; Martin-Esquivel, J. L.; Naranjo-Cigala, A.; Mirolo, S.; Patiño, J. (2025). **CHELSACanaryClim-climatologies**. [DOI: 10.16904/envidat.692](https://doi.org/10.16904/envidat.692)

**Role:** data. CC0 v1.0 COG release, monthly 1979–2013 temperature and precipitation. The acquired files have approximately 5 m pixel spacing; this is not validated 5 m climate accuracy. Encoded nodata is masked before scale/offset conversion. Source checksums, grid, dates and original license are retained in the Canary Islands example provenance.

**Used by:** `analysis/src/energy_analysis/canary_kgpv/pipeline.py`, `examples/analysis/plot_kgpv_canary.py`, `docs/kgpv-canary.md`, `data-retrieval/src/energy_data_retrieval/sources/canary_clim`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### patino_2023_canaryclim

Patiño, J.; Collart, F.; Vanderpoorten, A.; Martin-Esquivel, J. L.; Naranjo-Cigala, A.; Mirolo, S.; Karger, D. N. (2023). **Spatial resolution impacts projected plant responses to climate change on topographically complex islands**. Diversity and Distributions, 29(10), 1245-1262. [DOI: 10.1111/ddi.13757](https://doi.org/10.1111/ddi.13757)

**Role:** data. Scientific description and 100 m model-resolution benchmark for CanaryClim. Citation does not validate the current approximately 5 m COG spacing or this derived KGPV application at five metres.

**Used by:** `analysis/src/energy_analysis/canary_kgpv/pipeline.py`, `examples/analysis/plot_kgpv_canary.py`, `docs/kgpv-canary.md`, `data-retrieval/src/energy_data_retrieval/sources/canary_clim`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### global_solar_atlas_2019

World Bank Group; ESMAP; Solargis (2019). **Global Solar Atlas 2.0: Spain solar resource GIS data**. [Source](https://globalsolaratlas.info/download/spain)

**Role:** data. Pinned 2019 Spain archive, annual GHI at 9 arcseconds (nominally 250 m), 1994–2018 according to its XML metadata. Values are already annual kWh/m². Nearest-cell sampling adds no finer solar information. Developed and operated by Solargis s.r.o. on behalf of the World Bank Group using Solargis data with ESMAP funding. CC BY 4.0 with additional mediation/arbitration terms, preserved in the example manifest. Regional extraction and KGPV derivation are modifications; no provider endorsement is implied.

**Used by:** `analysis/src/energy_analysis/canary_kgpv/pipeline.py`, `examples/analysis/plot_kgpv_canary.py`, `docs/kgpv-canary.md`, `data-retrieval/src/energy_data_retrieval/sources/global_solar_atlas`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### rasterio_documentation

Rasterio contributors (n.d.). **Rasterio documentation: windowed reading, writing and reprojection**. [Source](https://rasterio.readthedocs.io/en/stable/)

**Role:** software. Bounded raster-window processing, nearest-neighbour GHI sampling and categorical overviews. Native climate pixel centres and missing values remain explicit; display reduction does not change downloadable native rasters.

**Used by:** `analysis/src/energy_analysis/canary_kgpv/pipeline.py`, `examples/analysis/plot_kgpv_canary.py`, `docs/kgpv-canary.md`, `analysis/src/energy_analysis/canary_kgpv/plotting.py`, `analysis/src/energy_analysis/chile_kgpv/pipeline.py`, `examples/analysis/plot_kgpv_chile.py`, `docs/kgpv-chile.md`, `data-retrieval/src/energy_data_retrieval/sources/chelsa`.

### chelsa_2021_climatologies

Karger, D. N.; Conrad, O.; Böhner, J.; Kawohl, T.; Kreft, H.; Soria-Auza, R. W.; Zimmermann, N. E.; Linder, H. P.; Kessler, M. (2021). **Climatologies at high resolution for the earth’s land surface areas, Version 2.1**. [DOI: 10.16904/envidat.228](https://doi.org/10.16904/envidat.228)

**Role:** data. CC0 v2.1 climatologies, 1981–2010 monthly temperature and precipitation, 30 arcseconds. Regional windows retain source pixels, CF units, scale/offset and masks. Strong source ETags and crop-pixel SHA-256 pins are recorded; ETags are not SHA-256 hashes. Current files are served from the provider’s chelsa02 container on os.unil.cloud.switch.ch.

**Used by:** `analysis/src/energy_analysis/chile_kgpv/pipeline.py`, `examples/analysis/plot_kgpv_chile.py`, `docs/kgpv-chile.md`, `data-retrieval/src/energy_data_retrieval/sources/chelsa`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### karger_2017_chelsa

Karger, D. N.; Conrad, O.; Böhner, J.; Kawohl, T.; Kreft, H.; Soria-Auza, R. W.; Zimmermann, N. E.; Linder, H. P.; Kessler, M. (2017). **Climatologies at high resolution for the earth’s land surface areas**. Scientific Data, 4, 170122. [DOI: 10.1038/sdata.2017.122](https://doi.org/10.1038/sdata.2017.122)

**Role:** data. Scientific description of CHELSA; use the versioned dataset record for the exact v2.1 baseline, storage encoding and release. Does not independently validate the derived Chile KGPV classifications.

**Used by:** `analysis/src/energy_analysis/chile_kgpv/pipeline.py`, `examples/analysis/plot_kgpv_chile.py`, `docs/kgpv-chile.md`, `data-retrieval/src/energy_data_retrieval/sources/chelsa`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### global_solar_atlas_chile_2019

World Bank Group; ESMAP; Solargis (2019). **Global Solar Atlas 2.0: Chile solar resource GIS data**. [Source](https://globalsolaratlas.info/download/chile)

**Role:** data. Pinned 2019 Chile archive. XML identifies 1999–2018 annual GHI, kWh/m²; 9 arcseconds, nominal 250 m. Usable values stop at 45°S, though the file rectangle extends to 46°S; southern mainland Patagonia is unclassified. CC BY 4.0 plus additional mediation/arbitration terms retained in the provenance. World Bank/ESMAP/Solargis attribution; derived KGPV does not imply endorsement.

**Used by:** `analysis/src/energy_analysis/chile_kgpv/pipeline.py`, `examples/analysis/plot_kgpv_chile.py`, `docs/kgpv-chile.md`, `data-retrieval/src/energy_data_retrieval/sources/global_solar_atlas`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`, `docs/worldwide-generation.md`.

### medina_2026_pv_climates

Medina, Ismael; Martínez, Ana M.; Dunlop, Ewan (2026). **Parametric and distribution-based definition of climatic zones for photovoltaics**. Solar Energy, 306, 114295. [DOI: 10.1016/j.solener.2025.114295](https://doi.org/10.1016/j.solener.2025.114295)

**Role:** implemented. Parametric two-feature workflow only; independent implementation using sklearn with documented convergence and empty-cluster adaptations. JRC labels are a saved refit, not a claim of identical published raster reconstruction. The distribution/optimal-transport method is not implemented. Online publication 2025; journal issue 2026.

**Used by:** `methods/src/energy_methods/jrc_climate.py`, `docs/climate-comparison.md`.

### jrc_2025_climate_dataset

Medina, Ismael; Martinez, Ana (2025). **High-resolution global and European climatic dataset for the definition of climatic zones for Photovoltaics**. [DOI: 10.2905/JRC.R1B5FSR](https://doi.org/10.2905/JRC.R1B5FSR)

**Role:** data. Global means at 0.1 degree for 2005-2023; G is annual in-plane irradiation and Tw is irradiance-weighted module temperature. E and eff are modeled PVGIS outputs. European Commission reuse notice applies; original download hash retained. Source description: https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/PVGIS/climatic-zones-pv/dataset_description.md.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/jrc_climate/client.py`, `examples/analysis/climate_provenance.json`.

### triana_2026_ml_climates

Triana de las Heras, Francisco Javier; Isabella, Olindo; Vogt, Malte Ruben (2026). **A machine learning approach to PV-climate classification**. Renewable Energy, 256, 123685. [DOI: 10.1016/j.renene.2025.123685](https://doi.org/10.1016/j.renene.2025.123685)

**Role:** implemented. Original published labels imported from the 55,418-row supplementary workbook. New seven-feature regression-weighted fits have their own MLxx IDs and frozen training state; no exact reproduction of published centroids or performance improvement is claimed. Radiation statistics retain native workbook conventions. Article CC BY; online 2025, journal volume 2026.

**Used by:** `methods/src/energy_methods/ml21.py`, `data-retrieval/src/energy_data_retrieval/sources/ml21/client.py`, `docs/climate-comparison.md`.

### karin_2019_pvcz

Karin, Todd; Jones, C. Birk; Jain, Anubhav (2019). **Photovoltaic Degradation Climate Zones**. IEEE Photovoltaic Specialists Conference. [Source](https://github.com/toddkarin/pvcz)

**Role:** implemented. IEEE PVSC paper supplied in the author repository. Table I thermal/specific-humidity boundaries and Arrhenius equivalent temperature at 1.1 eV. Equality enters the warmer/wetter class; missing ID zero shifts upstream IDs by one. Stress classes do not predict a degradation rate or lifetime.

**Used by:** `methods/src/energy_methods/pvcz.py`, `docs/climate-comparison.md`.

### karin_pvcz_software

Karin, Todd (2019). **Photovoltaic Climate Zones and Stressors (PVCZ)**. [Source](https://github.com/toddkarin/pvcz/tree/aa89fab8d1d66f46f4ea8575e2452aa75a927535)

**Role:** software. Pinned public CSV from the MIT-licensed author repository, based on GLDAS 2010-2018 at 0.25 degree. Original labels retained despite rounded coordinates/stresses; no pickle loaded. MIT copyright and permission notice included with extracts.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/pvcz/client.py`, `examples/analysis/climate_PVCZ_LICENSE.txt`.

### pvgis_5_api

European Commission Joint Research Centre (n.d.). **PVGIS 5 API non-interactive service**. [Source](https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis/using-pvgis-5/api-non-interactive-service_en)

**Role:** data. Seven public calculation/data tools; v5.3 and explicit v5.2 routing. Provider model and data reuse conditions apply. No field-measurement or accuracy claim.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/pvgis`, `docs/pvgis.md`.

### pvgis_6_api

European Commission Joint Research Centre (n.d.). **PVGIS 6 Web API**. [Source](https://photovoltaic-geographic-information-system.ec.europa.eu/api/v6/docs)

**Role:** data. Version 6 OpenAPI contract reviewed 2026-10-31; 20 paths and 27 GET/POST operations. Native parameters, conventions and outputs retained. Active service development may change the contract. Software licensing does not by itself establish data reuse terms.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/pvgis`, `docs/pvgis.md`.

### nasa_srtmgl1

USGS and NASA (n.d.). **SRTM 1 Arc-Second Global**. [DOI: 10.5066/F7PR7TFT](https://doi.org/10.5066/F7PR7TFT)

**Role:** data. Finest publicly distributed SRTM grid: 1 arcsecond, approximately 30 m; 60 N to 56 S; February 2000 radar acquisition; EGM96 orthometric heights. SRTMGL1 void-filled HGT posts are retained without vertical conversion.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/srtm/client.py`, `docs/terrain.md`, `examples/connectors/plot_terrain_sources.py`, `examples/connectors/data/terrain_provenance.json`, `scripts/prepare_terrain_samples.py`.

### esa_srtm_mirror

European Space Agency (n.d.). **ESA SNAP SRTMGL1 auxiliary data mirror**. [Source](https://step.esa.int/auxdata/dem/SRTMGL1/)

**Role:** data. Anonymous official ESA distribution of NASA SRTMGL1 HGT ZIP tiles. Downloaded N28W017 and validated one 3601 by 3601 big-endian int16 member; no SNAP ellipsoid correction applied.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/srtm/client.py`, `docs/terrain.md`, `examples/connectors/plot_terrain_sources.py`, `examples/connectors/data/terrain_provenance.json`, `scripts/prepare_terrain_samples.py`.

### copernicus_dem

European Space Agency and European Union (n.d.). **Copernicus DEM: Global and European Digital Elevation Model**. [DOI: 10.5270/ESA-c5d3d65](https://doi.org/10.5270/ESA-c5d3d65)

**Role:** data. GLO-30 DSM, primarily TanDEM-X acquisition 2011-2015 with other products for gap filling; EGM2008 heights. Licence attribution is retained in the sample manifest, gallery and guide. Public GLO-30 does not grant EEA-10 access.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/copernicus_dem/client.py`, `docs/terrain.md`, `examples/connectors/plot_terrain_sources.py`, `examples/connectors/data/terrain_provenance.json`, `scripts/prepare_terrain_samples.py`, `methods/src/energy_methods/pv_site_3d.py`, `examples/analysis/plot_rengo_site_3d.py`, `examples/analysis/data/rengo_3d/terrain_provenance.json`, `docs/pv-site-3d.md`.

### copernicus_dem_aws

Sinergise and AWS Open Data (n.d.). **Copernicus DEM GLO-30 Public: AWS COG layout**. [Source](https://copernicus-dem-30m.s3.amazonaws.com/readme.html)

**Role:** data. Public mirror has unavailable/restricted tiles and absent ocean tiles. COG removes duplicate southern/eastern posts, retains 3600 rows and latitude-dependent longitudinal spacing; 10 in the path means 1.0 arcsecond, not 10 m.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/copernicus_dem/client.py`, `docs/terrain.md`, `examples/connectors/plot_terrain_sources.py`, `examples/connectors/data/terrain_provenance.json`, `scripts/prepare_terrain_samples.py`, `scripts/prepare_rengo_3d.py`, `docs/pv-site-3d.md`.

### ign_mdt

Instituto Geográfico Nacional de España (n.d.). **CNIG digital terrain models from PNOA lidar**. [Source](https://centrodedescargas.cnig.es/CentroDescargas/modelos-digitales-elevaciones)

**Role:** data. Bare-earth terrain products include 5 m, 2 m and 0.5 m coverages. This connector explicitly retrieves the 5 m WCS layer, not the finer standalone downloads. Spanish official height references vary between mainland and islands; confirm project metadata.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/ign_terrain/client.py`, `docs/terrain.md`, `examples/connectors/plot_terrain_sources.py`, `examples/connectors/data/terrain_provenance.json`, `scripts/prepare_terrain_samples.py`.

### ign_terrain_wcs

Instituto Geográfico Nacional de España (n.d.). **IGN INSPIRE WCS terrain service**. [Source](https://servicios.idee.es/wcs-inspire/mdt?SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCapabilities)

**Role:** data. WCS 2.0.1 numeric elevation, with live DescribeCoverage and native-aligned subsets of Elevacion4083_5 and Elevacion25830_5 supported. Live Canary TIFF is 5 m int16 with no nodata declared. DescribeCoverage has generic radiance units; original XML retained and elevations interpreted from official MDT documentation as metres.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/ign_terrain/client.py`, `docs/terrain.md`, `examples/connectors/plot_terrain_sources.py`, `examples/connectors/data/terrain_provenance.json`, `scripts/prepare_terrain_samples.py`.

### usgs_3dep

U.S. Geological Survey (n.d.). **3DEP elevation products and services**. [Source](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services)

**Role:** data. Project-based 1 m bare-earth DEMs derive from lidar; no complete national or global 1 m coverage implied. CONUS uses projected metre coordinates and NAVD88 heights. Separate seamless 1 m products are not selected by this connector.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/usgs_3dep/client.py`, `docs/terrain.md`, `examples/connectors/plot_terrain_sources.py`, `examples/connectors/data/terrain_provenance.json`, `scripts/prepare_terrain_samples.py`.

### usgs_tnm_api

U.S. Geological Survey (n.d.). **The National Map GIS data downloads and API**. [Source](https://www.usgs.gov/the-national-map-data-delivery/gis-data-download)

**Role:** data. TNM products API returns metadata, project extents and official GeoTIFF download URLs. Search pagination and byte budgets are bounded. A project bounding box is not a valid-data mask; overlapping tiles require explicit project selection.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/usgs_3dep/client.py`, `docs/terrain.md`, `examples/connectors/plot_terrain_sources.py`, `examples/connectors/data/terrain_provenance.json`, `scripts/prepare_terrain_samples.py`.

### orbitalpv_imagery

Julián Ascencio Vásquez (n.d.). **Orbital PV: ground satellite imagery connectors and native raster persistence**. [Source](https://github.com/julianascencio/orbital-pv/tree/498c47e182f9f0e1b0f0d40bc3125ef7c2110a05)

**Role:** implemented. Actual dependency, pinned to commit 498c47e182f9f0e1b0f0d40bc3125ef7c2110a05. Uses Sentinel2GroundConnector, read_ground_image, GroundImage.save_geotiff and load_ground_image. Python 3.13+ optional workspace dependency group; Git pin remains outside published package metadata. Earlier PyPI 0.7.0 lacks these ground APIs.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/orbitalpv_imagery/client.py`, `docs/satellite-imagery.md`, `examples/connectors/plot_satellite_imagery.py`, `examples/connectors/data/imagery_provenance.json`, `scripts/prepare_satellite_imagery_samples.py`, `examples/connectors/plot_candelaria_solar_farm.py`, `examples/connectors/data/candelaria_site.json`, `scripts/prepare_candelaria_imagery.py`.

### earth_search_c1

Element 84 (n.d.). **Earth Search: Sentinel-2 Collection 1 Level-2A STAC and cloud-optimized GeoTIFFs**. [Source](https://github.com/Element84/earth-search)

**Role:** data. Public Earth Search v1, sentinel-2-c1-l2a. Asset-level GSD, projection, scale, offset and nodata retained; scene-wide cloud cover is not a local mask.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/orbitalpv_imagery/client.py`, `docs/satellite-imagery.md`, `examples/connectors/plot_satellite_imagery.py`, `examples/connectors/data/imagery_provenance.json`, `scripts/prepare_satellite_imagery_samples.py`, `examples/connectors/plot_candelaria_solar_farm.py`, `examples/connectors/data/candelaria_site.json`, `scripts/prepare_candelaria_imagery.py`.

### sentinel2_imagery

European Space Agency; European Union (n.d.). **Copernicus Sentinel-2 mission and imagery documentation**. [Source](https://documentation.dataspace.copernicus.eu/Data/SentinelMissions/Sentinel2.html)

**Role:** data. Native 10 m visible/NIR, 20 m and 60 m bands. Examples retain native grid and SCL quality classes; RGB display is not reflectance. Contains modified Copernicus Sentinel data (2026).

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/orbitalpv_imagery/client.py`, `docs/satellite-imagery.md`, `examples/connectors/plot_satellite_imagery.py`, `examples/connectors/data/imagery_provenance.json`, `scripts/prepare_satellite_imagery_samples.py`, `examples/connectors/plot_candelaria_solar_farm.py`, `examples/connectors/data/candelaria_site.json`, `scripts/prepare_candelaria_imagery.py`.

### maxar_open_data

Maxar Technologies (n.d.). **Maxar / Vantor Open Data Program: event imagery and public STAC archive**. [Source](https://xpress-docs.maxar.com/OpenData/OpenData_intro.htm)

**Role:** data. Event-limited disaster imagery, program/event CC BY-NC 4.0. Archive https://maxar-opendata.s3.amazonaws.com/events/catalog.json. Original acquisition collection proprietary declaration is also retained. Finest selection compares native GSD and asset grid, never a sharpened preview. Actual WorldView-3 sample has 0.33 m declared GSD; approximately 0.305 m visual display spacing is not new sensor detail.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/orbitalpv_imagery/client.py`, `docs/satellite-imagery.md`, `examples/connectors/plot_satellite_imagery.py`, `examples/connectors/data/imagery_provenance.json`, `scripts/prepare_satellite_imagery_samples.py`.

### tenerife_iter_pv_catalogue

Cabildo Insular de Tenerife; Instituto Tecnológico y de Energías Renovables (n.d.). **Infraestructuras de generación de energía en Tenerife**. [Source](https://datos.canarias.es/catalogos/general/dataset/infraestructuras-de-generacion-de-energia-en-tenerife)

**Role:** data. CC BY. Official catalogue feature 6 identifies Planta Icor at longitude -16.442229, latitude 28.194341 with 2,000 kW listed power; AC/DC basis unspecified. Full canonical GeoJSON and request hash retained. OSM point-in-polygon association is not a surveyed boundary.

**Used by:** `examples/connectors/plot_candelaria_solar_farm.py`, `examples/connectors/data/candelaria_site.json`, `scripts/prepare_candelaria_imagery.py`, `docs/satellite-imagery.md`, `examples/connectors/data/candelaria_README.txt`, `docs/pv-module-counting.md`, `examples/analysis/plot_candelaria_module_counting.py`.

### osm_solar_footprints

OpenStreetMap contributors (n.d.). **OpenStreetMap solar-energy features and copyright**. [Source](https://www.openstreetmap.org/copyright)

**Role:** data. ODbL-1.0. Original query-bound Tenerife capture from Orbital PV commit 498c47e182f9f0e1b0f0d40bc3125ef7c2110a05, examples/ground_imagery/_data/tenerife-osm.json, retrieved 2026-10-30; original sidecar and checksum retained. Way 430266023 contains the official Icor point. Mapping does not establish ownership, full installation extent or capacity.

**Used by:** `examples/connectors/plot_candelaria_solar_farm.py`, `examples/connectors/data/candelaria_site.json`, `scripts/prepare_candelaria_imagery.py`, `docs/satellite-imagery.md`, `examples/connectors/data/candelaria_README.txt`, `docs/pv-module-counting.md`, `examples/analysis/plot_candelaria_module_counting.py`.

### ign_pnoa_imagery

Instituto Geográfico Nacional; Plan Nacional de Ortofotografía Aérea (n.d.). **PNOA Imagen: visualizadores y servicios web**. [Source](https://pnoa.ign.es/web/portal/pnoa-imagen/visualizadores-y-servicios-web)

**Role:** data. PNOA/IGN rendered aerial orthophoto via https://www.ign.es/wms-inspire/pnoa-ma, OI.OrthoimageCoverage, WMS 1.1.1. IGN attribution/licence terms apply. The Icor view is aerial, not satellite or calibrated reflectance; acquisition date and native GSD remain unknown. Render width does not establish native detail. Original query and SHA-256 retained.

**Used by:** `examples/connectors/plot_candelaria_solar_farm.py`, `examples/connectors/data/candelaria_site.json`, `scripts/prepare_candelaria_imagery.py`, `docs/satellite-imagery.md`, `examples/connectors/data/candelaria_README.txt`, `docs/pv-module-counting.md`, `examples/analysis/plot_candelaria_module_counting.py`.

### grimaccia_2017_pv_mapping

Grimaccia, Francesco; Leva, Sonia; Niccolai, Alessandro (2017). **PV plant digital mapping for modules’ defects detection by unmanned aerial vehicles**. IET Renewable Power Generation, 11(10), 1221-1228. [DOI: 10.1049/iet-rpg.2016.1041](https://doi.org/10.1049/iet-rpg.2016.1041)

**Role:** background. Background for colour-based PV module recognition and mapping from aerial imagery. The repository uses its own experimental RGB thresholding, morphology, robust table-edge fitting and brightness-profile grid counter; it does not reproduce the paper’s HSV/UAV workflow or its validation. Candidate counts require independent annotations or an as-built inventory.

**Used by:** `methods/src/energy_methods/pv_module_counting.py`, `docs/pv-module-counting.md`, `examples/analysis/plot_candelaria_module_counting.py`.

### scipy_find_peaks

SciPy contributors (n.d.). **SciPy signal.find_peaks reference**. [Source](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html)

**Role:** implemented. Peak detection on detrended table brightness profiles. Prominence, distance and height conditions are explicit image-space screening parameters, not calibrated detection probabilities. Morphological operations and interpolation also use SciPy.

**Used by:** `methods/src/energy_methods/pv_module_counting.py`, `docs/pv-module-counting.md`, `examples/analysis/plot_candelaria_module_counting.py`, `methods/src/energy_methods/pv_lattice_counting.py`.

### esri_world_imagery_static

Esri (n.d.). **World Imagery static map exports and source metadata**. [Source](https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer)

**Role:** data. Attributed research-report static maps for the Chile audits and El Mirlo pilot. Source resolution and rendered service sampling differ. Map copyrights remain with Esri and licensors; static-map terms https://doc.arcgis.com/en/arcgis-online/reference/static-maps.htm. No open imagery-data license asserted.

**Used by:** `docs/chile-module-counting.md`, `examples/analysis/plot_chile_largest_module_counting.py`, `examples/analysis/plot_chile_smallest_module_counting.py`, `docs/rengo-module-counting.md`, `examples/analysis/data/rengo_modules/rengo_study.json`.

### ceme1_engineering_inventory

Estudios Eléctricos (n.d.). **Parque Fotovoltaico CEME1: Informe de Potencia Máxima, EE-EN-2024-0488-R1**. [Source](https://www.coordinador.cl/wp-content/uploads/2025/12/EE-EN-2024-0488-R1_Potencia_Maxima_PFV_CEME1.pdf)

**Role:** data. Section 3.2, Figure 3.4 and Table 3.1, pages 15–16. 882,720 modules and 480.19 MWDC. This is a reported inventory, never an automatic image count. Upload date is not asserted as report publication date.

**Used by:** `docs/chile-module-counting.md`, `examples/analysis/plot_chile_largest_module_counting.py`, `examples/analysis/plot_chile_smallest_module_counting.py`.

### sunbelt_concon_project

Sunbelt (n.d.). **Planta de gas, Concón**. [Source](https://sunbelt.cl/proyectos/planta-de-gas-concon/)

**Role:** data. Installer confirms photovoltaic technology, PMGD use and 118 kWp DC. No verified module count supplied; photographs do not provide an unobscured complete inventory.

**Used by:** `docs/chile-module-counting.md`, `examples/analysis/plot_chile_largest_module_counting.py`, `examples/analysis/plot_chile_smallest_module_counting.py`.

### cardoso_2024_pv_modules

Cardoso, Andressa; Jurado-Rodríguez, David; López, Alfonso; Ramos, M. Isabel; Jurado, Juan Manuel (2024). **Automated detection and tracking of photovoltaic modules from 3D remote sensing data**. Applied Energy, 367, 123242. [DOI: 10.1016/j.apenergy.2024.123242](https://doi.org/10.1016/j.apenergy.2024.123242)

**Role:** background. Background on geometric individual-module detection from high-resolution UAV RGB/thermal and 3D data. The PCA/autocorrelation method here is a separate experimental implementation, not a reproduction; published accuracy does not transfer to the El Mirlo basemap pilot. No known-count gap filling is implemented.

**Used by:** `methods/src/energy_methods/pv_lattice_counting.py`, `docs/rengo-module-counting.md`.

### el_mirlo_project

oEnergy / PFV El Mirlo SpA (n.d.). **Parque Fotovoltaico El Mirlo**. [Source](https://mirlo.centralpmgd.cl/)

**Role:** data. Developer project page confirms identity and Malloa location. Design power is not substituted for the dated CEN power field. No project-design module count is used in image detection.

**Used by:** `docs/rengo-module-counting.md`, `examples/analysis/data/rengo_modules/rengo_study.json`.

### sam_cec_pv_catalogue_2026

National Laboratory of the Rockies (2026). **SAM CEC module and inverter libraries, pinned revision 784177b**. [Source](https://github.com/NatLabRockies/SAM/tree/784177b634fa1475fda6672b70595e087a238aea/deploy/libraries)

**Role:** data. Pinned source snapshot with SHA-256 hashes and BSD notice in catalogues/pv. Fitted reference parameters, not proof of current availability/certification. Duplicate exact module names are quarantined.

**Used by:** `data-retrieval/src/energy_data_retrieval/pv_catalogue/sam.py`, `docs/pv-catalogue.md`.

### eia860_pv_catalogue_2025

U.S. Energy Information Administration (2025). **Form EIA-860 detailed data: report year 2025**. [Source](https://www.eia.gov/electricity/data/eia860/)

**Role:** data. Year denotes reporting period, not access year. Downloaded 31 October 2026. Plant and solar workbooks; only OP/PV generators. One row per plant; source fields and generator-level attributes preserved; source dates and capacities not promoted beyond their documented scope.

**Used by:** `data-retrieval/src/energy_data_retrieval/pv_catalogue/eia860.py`, `docs/pv-catalogue.md`.

### proj_aeqd

PROJ contributors (n.d.). **Azimuthal Equidistant — PROJ documentation**. [Source](https://proj.org/en/stable/operations/projections/aeqd.html)

**Role:** software. Local WGS84 azimuthal-equidistant projection for metre-based PV scenes. The local radius guard and table-plane lifting rule are repository choices, not a PROJ photogrammetry algorithm.

**Used by:** `methods/src/energy_methods/pv_site_3d.py`, `docs/pv-site-3d.md`.

### plotly_mesh3d

Plotly Technologies Inc. (n.d.). **3D Mesh Plots in Python**. [Source](https://plotly.com/python/3d-mesh/)

**Role:** software. Rendering indexed terrain and candidate module surfaces. Visual output does not validate geometry or recover depth.

**Used by:** `analysis/src/energy_analysis/site_3d/reports.py`, `docs/pv-site-3d.md`.

### plotly_html_export

Plotly Technologies Inc. (n.d.). **Interactive HTML Export in Python**. [Source](https://plotly.com/python/interactive-html-export/)

**Role:** software. Self-contained offline HTML export with embedded Plotly.js. No CDN or live map tiles are required.

**Used by:** `analysis/src/energy_analysis/site_3d/reports.py`, `docs/pv-site-3d.md`.

### bess_neoen_au_2024

Neoen (2024). **Collie Battery Stage 1 begins operating and delivering grid reliability services**. [Source](https://neoen.com/en/news/2024/neoens-collie-battery-stage-1-begins-operating-and-delivering-grid-reliability-services-in-western-australia/)

**Role:** data. Lists operating Hornsdale at 150 MW / 193.5 MWh and Victorian Big Battery at 300 MW / 450 MWh. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_nzea_collie

Net Zero Economy Authority (n.d.). **Neoen Collie Battery**. [Source](https://www.nzea.gov.au/neoen-collie-battery)

**Role:** data. Two operating stages: 219 MW / 877 MWh from October 2024, and 341 MW / 1363 MWh from July 2025. Total computed as the sum of these non-overlapping stages. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_engie_hazelwood

ENGIE Australia (n.d.). **Hazelwood Battery**. [Source](https://engie.com.au/about-us/our-generation-activities/battery-storage/hazelwood-battery)

**Role:** data. Original HBESS operational from 2023, 150 MW / 150 MWh; separate HBESS2 expansion of 150 MW / 600 MWh under construction. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_mortenson_edwards

Mortenson (n.d.). **Edwards & Sanborn Solar + Storage Project Complete**. [Source](https://www.mortenson.com/news-insights/edwards-sanborn-solar-storage-completion)

**Role:** data. Completed project: 3287 MWh BESS, 1300 MW site interconnection and 875 MWdc solar. Interconnection is not BESS output; no battery MW inferred. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_aecon_oneida

Aecon (2025). **Oneida Energy Storage Project Commences Commercial Operations**. [Source](https://www.aecon.com/press-room/news/2025/05/07/oneida-commences-commercial-operations)

**Role:** data. 250 MW / 1000 MWh at Haldimand County; lithium-ion units; Northland oversees operations. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_engie_coya_2024

ENGIE Chile (2024). **Inicia su operación comercial el sistema de almacenamiento más grande de América Latina**. [Source](https://www.engie.cl/inicia-su-operacion-comercial-el-sistema-de-almacenamiento-mas-grande-de-america-latina/)

**Role:** data. Coya at María Elena: 139 MW / 638 MWh, lithium batteries; operation authorized by CEN. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_engie_storage

ENGIE Chile (n.d.). **Almacenamiento BESS**. [Source](https://www.engie.digital/almacenamiento-bess/)

**Role:** data. Operating Tamaya: 68 MW / 418 MWh, Tocopilla, 2025. Coya listed at 139 MW / 638 MWh. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_engie_financial_2025

ENGIE Chile / Comisión para el Mercado Financiero (n.d.). **ENGIE Energia Chile financial disclosure, 2025**. [Source](https://www.cmfchile.cl/institucional/inc/inf_financiera/ifrs/safec_ifrs_verarchivo.php?auth=YTkzMzg5N2Q1NzVhYjg0YmQxNGVkZDQ1ZDY1YjU5MmI%3D&send=aTLbRr%2F7WtG0t9iSEYFzO7yoE2%2FVR6LkV0F57PF3dpY8m4jmpYcoaGZpfwneYsXRwIlXZjuYRoRicccbOcDrZ0gHG6YUSV2RxGE71hXYJrKSw7IXoi1yVuWH7hiH5GAZhoC6eH+HvxGZ7yP10tgDpCUpJvbQPBAl2L8V56+AXzTHOAQ%3D)

**Role:** data. Financial report lists Coya at 140.97 MW and Tamaya at 76 MW. Basis discrepancy with public project descriptions is unresolved. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_isa_registro

ISA Energia Brasil (2025). **ISA Energia Brasil receives MME, EPE and ONS at its battery storage facility**. [Source](https://www.isaenergiabrasil.com.br/centro-de-midia/noticias/isa-energia-brasil-recebe-mme-epe-e-ons-para-visita-ao-primeiro-sistema-de-armazenamento-de-energia-em-larga-escala-da-transmissao-nacional/)

**Role:** data. Registro substation battery system: 30 MW / 60 MWh and two-hour peak support. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_sse_ferrybridge

SSE (2026). **Ferrybridge Battery Storage System enters full operation**. [Source](https://www.sse.com/news-and-views/2026/03/sse-s-ferrybridge-battery-storage-system-enters-full-operation/)

**Role:** data. Ferrybridge 150/300 operating; Salisbury 50/100 operating; Monk Fryston 320/640 and Fiddlers Ferry 150/300 under construction. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_iberdrola_aranuelo

Iberdrola (2021). **Iberdrola commissions Arañuelo III, the first photovoltaic plant in Spain with a storage battery**. [Source](https://www.iberdrola.com/press-room/news/detail/aranuelo-iii-first-photovoltaic-plant-spain-storage-battery)

**Role:** data. 3 MW / 9 MWh battery with Arañuelo III solar plant; commissioned announcement. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_galp_alcoutim

Galp (2024). **Galp and Powin to build large-scale energy storage system in Portugal**. [Source](https://www.galp.com/corp/en/media/press-releases/press-release/id/1515/galp-and-powin-to-build-large-scale-energy-storage-system-in-portugal)

**Role:** data. 5 MW / 20 MWh BESS near Alcoutim, integrated by Powin with solar. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_galp_alcoutim_2025

Galp (2025). **Galp instala 74 MW de baterias para armazenar energia solar em Portugal e Espanha**. [Source](https://www.galp.com/corp/Portals/0/Comunicados_Media/2025/07-Jul/Galp-instala-74-MW-de-baterias-para-armazenar-energia-solar-em-Portugal-e-Espanha.pdf)

**Role:** data. Original Alcoutim 5 MW / 20 MWh system operating since early 2025; additional four-system 60.5 MW / 120.4 MWh expansion distinct. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_total_dunkirk

TotalEnergies (2021). **TotalEnergies Launches the Largest Battery-Based Energy Storage Site in France**. [Source](https://totalenergies.com/newsroom/totalenergies-launches-largest-battery-based-energy-storage-site-france/?lang=eng)

**Role:** data. Completed Dunkirk facility: 61 MW and 61 MWh; Saft containers. Initial 25 MW unit included, not additive. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_rwe_hamm_neurath

RWE (2025). **220 megawatts of power to stabilise the grid: RWE commissions Hamm and Neurath battery storage systems**. [Source](https://www.rwe.com/en/press/rwe-generation/2025-02-14-220-megawatts-of-power-to-stabilise-the-grid-new-battery-storage-systems/)

**Role:** data. Separate sites: Hamm 140 MW / 151 MWh and Neurath 80 MW / 84 MWh; exclude 220 MW portfolio total. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_neoen_storen

Neoen (2024). **Sveriges största batteri tas i bruk**. [Source](https://sweden.neoen.com/sv/okategoriserad/2024/sveriges-storsta-batteri-tas-i-bruk/)

**Role:** data. Storen in Ragunda: 52 MW / 52 MWh; inaugurated and operating. Isbillen is a different project. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_neoen_yllikkala

Neoen (2025). **Neoen ottaa käyttöön toisen suuren akkuvarastonsa Suomessa**. [Source](https://finland.neoen.com/fi/okategoriserad/2025/neoen-ottaa-kayttoon-toisen-suuren-akkuvarastonsa-suomessa/)

**Role:** data. Two distinct installations ~100 metres apart: original 30 MW / 30 MWh; new Two project 56.4 MW / 112.9 MWh, Nidec and Destia. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_energy_cells

Energy Cells (n.d.). **About the project: Lithuanian battery parks**. [Source](https://energy-cells.eu/about-project/)

**Role:** data. Four separate 50 MW / 50 MWh parks at Vilnius, Šiauliai, Alytus, Utena; operational reserve service in 2023; Siemens Energy/Fluence consortium. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_giga_buffalo

GIGA Storage (n.d.). **Buffalo NL**. [Source](https://giga-storage.com/en/projects/buffalo/)

**Role:** data. Lelystad: 25 MW / 48 MWh, lithium LFP, supplier Wärtsilä, delivered 2022; connected to Windnet smart grid. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_eskom_hex

Eskom (2023). **Eskom unveils a first of its kind largest battery storage project in the African continent**. [Source](https://www.eskom.co.za/eskom-unveils-a-first-of-its-kind-largest-battery-storage-project-in-the-african-continent/)

**Role:** data. Hex opened in Worcester; 100 MWh storage. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_eskom_rollout

Eskom (n.d.). **Battery Energy Storage System - Distribution**. [Source](https://www.eskom.co.za/distribution/battery-energy-storage-system/)

**Role:** data. Site-level table lists Hex at 20 MW / 100 MWh. Rollout totals are not separate projects. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_seci_rajnandgaon

Solar Energy Corporation of India (n.d.). **Own projects: commissioned Rajnandgaon solar and BESS**. [Source](https://seci.co.in/own-projects)

**Role:** data. Commissioned Rajnandgaon: 40 MW / 120 MWh lithium-ion storage paired with 100 MW solar PV. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_dicp_dalian

Dalian Institute of Chemical Physics, Chinese Academy of Sciences (2022). **百兆瓦级大连液流电池储能调峰电站并网发电**. [Source](https://dicp.cas.cn/xwdt/kyjz/202210/t20221031_6541871.html)

**Role:** data. Grid-connected first phase: 100 MW / 400 MWh vanadium flow battery. Planned 200 MW / 800 MWh total is excluded. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_sembcorp_ess

Sembcorp (n.d.). **Energy Storage Systems**. [Source](https://www.sembcorp.com/en/driving-energy-transition/our-businesses/renewable-energy/energy-storage-systems/)

**Role:** data. Current owner page reports operating Jurong Island ESS with 326 MWh; no battery MW stated. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_ema_sembcorp_2023

Energy Market Authority (2023). **Southeast Asia’s largest energy storage system officially opens**. [Source](https://www.ema.gov.sg/news-events/news/media-releases/2023/southeast-asias-largest-energy-storage-system-officially-opens)

**Role:** data. Jurong Island Banyan and Sakra project: 285 MWh at opening, operations began December 2022. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_sumitomo_hayakita

Sumitomo Electric (2026). **Sumitomo Electric’s Vanadium Redox Flow Battery Selected by Hokkaido Electric Power Network for the Third Time**. [Source](https://sumitomoelectric.com/press/2026/04/prs015)

**Role:** data. Original 15 MW / 60 MWh demonstration battery remains commercially operational; separate 17/51 project and future 11/33 project excluded. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_fluence_kabankalan

Fluence (2022). **SMCGPH and Fluence’s First Battery Project of 470 MW Portfolio Begins Commercial Operation in the Philippines**. [Source](https://blog.fluenceenergy.com/smcgph-and-fluences-first-battery-energy-storage-project-of-470-mw-portfolio-begins-commercial-operation-in-the-philippines)

**Role:** data. Kabankalan 20 MW / 20 MWh enters commercial operation; not the complete 470 MW portfolio. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_huawei_redsea

Huawei (n.d.). **City of Tomorrow: Huawei FusionSolar contributes to the first city powered by clean energy**. [Source](https://digitalpower.huawei.com/en/cases/fusionsolar/first-fity-powered-by-clean-energy)

**Role:** data. Red Sea hotels and airport operating; project package includes 400 MW PV and 1.3 GWh ESS. No BESS power rating stated. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_nrec_bisha

NR Electric (n.d.). **Saudi Arabia achieves black start of 500MW energy storage station for the first time**. [Source](https://www.nrec.com/en/index.php/about/newsInfo/203.html)

**Role:** data. Black-start test dated February 9, 2026 for 500 MW / 2 GWh Bisha project; NR supplies AC-side PCS/PMS/EMS. Commercial status not established by this test. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_ea_nz_batteries

Electricity Authority New Zealand (n.d.). **Eye on electricity: Battery performance in New Zealand**. [Source](https://www.ea.govt.nz/news/eye-on-electricity/eye-on-electricity-battery-performance-in-new-zealand/)

**Role:** data. Operating grid batteries listed: Rotohiko 35 MW / 35 MWh, Ruakākā 100 MW / 200 MWh and Glenbrook-Ohurua 100 MW / 200 MWh. Factual metadata only; no open data license asserted.

**Used by:** `catalogues/bess/sources.json`, `docs/bess-catalogue.md`, `examples/database/plot_bess_projects.py`.

### bess_eia860_2025_bess

U.S. Energy Information Administration (n.d.). **Form EIA-860 detailed data, report year 2025: battery storage**. [Source](https://www.eia.gov/electricity/data/eia860/xls/eia8602025.zip)

**Role:** data. Operating battery units aggregated by Plant Code. Nameplate power AC; stored energy nameplate; December 31 reporting-year status per archive instructions. Electrochemical capacitors excluded.

**Used by:** `catalogues/bess/sources.json`, `catalogues/bess/research/2026-11-01_expansion.md`.

### bess_repd_2026_q2_bess

Department for Energy Security and Net Zero (2026). **Renewable Energy Planning Database, July 2026 (Q2) battery records**. [Source](https://assets.publishing.service.gov.uk/media/6a6cbdc00c36759b5ccaa305/REPD_Publication_Q2_2026.csv)

**Role:** data. CP1252 CSV; operational Battery records only. Planning records require phase and alias reconciliation; MWh unreported; native applicant/operator and projected coordinates retained without role or datum inference.

**Used by:** `catalogues/bess/sources.json`, `catalogues/bess/research/2026-11-01_expansion.md`.

### bess_neoen_blyth_2025

Neoen (2025). **Blyth Battery is now operating**. [Source](https://blythbattery.com.au/2025/04/10/blyth-battery-is-now-operating/)

**Role:** data. 238.5 MW / 477 MWh operating; South Australia; release date not asserted as COD.

**Used by:** `catalogues/bess/sources.json`, `catalogues/bess/research/2026-11-01_expansion.md`.

### bess_neoen_western_downs_2025

Neoen (2025). **Multiple milestones reached on Western Downs Battery**. [Source](https://westerndownsgreenpowerhub.com.au/2025/12/15/multiple-milestones-reached-on-western-downs-battery/)

**Role:** data. Stages 1 and 2 operating at combined 540 MW / 1080 MWh. Stage 3 is 305 MW / 1220 MWh under construction, expected summer 2027/28 and excluded from current totals.

**Used by:** `catalogues/bess/sources.json`, `catalogues/bess/research/2026-11-01_expansion.md`.

### bess_amea_abydos_2025

AMEA Power (2025). **Successful commissioning of Egypt battery energy storage system**. [Source](https://www.ameapower.com/amea-power-successfully-commissions-landmark-battery-energy-storage-system-in-egypt-following-successful-financial-close/)

**Role:** data. 300 MWh BESS at 500 MW solar plant in Aswan; commissioning complete ahead of scheduled COD; exact commercial operation unconfirmed.

**Used by:** `catalogues/bess/sources.json`, `catalogues/bess/research/2026-11-01_expansion.md`.

### bess_ifc_abydos_bess

International Finance Corporation (2025). **Abydos I BESS investment disclosure 50576**. [Source](https://disclosures.ifc.org/project-detail/SII/50576/abydos-i-bess)

**Role:** data. Named Abydos I BESS: 300 MWh integrated with existing 500 MWac PV in Aswan. The November 2024 commissioning date refers to solar, not BESS.

**Used by:** `catalogues/bess/sources.json`, `catalogues/bess/research/2026-11-01_expansion.md`.

### bess_acwa_riverside_cod

ACWA Power, issuer announcement via Euroland IR (n.d.). **Riverside BESS full commercial-operation notice**. [Source](https://ksatools.eurolandir.com/tools/Pressreleases/GetPressRelease/?ID=7901635&companycode=sa-acwa&lang=en-GB&v=ticker)

**Role:** data. Company received notice on 11 February 2026 that full COD had been achieved. 334 MW / 501 MWh Plant 2, 200 MW PV Plant 1, Tashkent region. Notice receipt is not necessarily the exact COD.

**Used by:** `catalogues/bess/sources.json`, `catalogues/bess/research/2026-11-01_expansion.md`.

### bess_esb_aghada_2024

ESB (2024). **Aghada second battery facility opens**. [Source](https://esb.ie/news---insights/press-releases/article/2024/11/15/esb-officially-opens-its-latest-battery-storage-project-in-co-cork-as-part-of--300m-investment)

**Role:** data. Second Aghada battery 150 MW / 300 MWh, following first 19 MW / 38 MWh in 2022. Poolbeg 75 MW /150 MWh. Aghada combined arithmetic total is 169 MW /338 MWh; no duplicate phase rows.

**Used by:** `catalogues/bess/sources.json`, `catalogues/bess/research/2026-11-01_expansion.md`.

### bess_esb_poolbeg

ESB (n.d.). **Poolbeg Energy Hub**. [Source](https://esb.ie/what-we-do/generation-and-trading/poolbeg-energy-hub)

**Role:** data. 75 MW /150 MWh operational since late November 2023. Owner reports coordinates 53.340380,-6.189385. February 2024 opening is not COD.

**Used by:** `catalogues/bess/sources.json`, `catalogues/bess/research/2026-11-01_expansion.md`.

### bess_met_dunamenti_2025

MET Group (2025). **Dunamenti battery energy storage facility enters operation**. [Source](https://met.com/en/media/press-releases/met-group-inaugurates-hungary-s-largest-battery-energy-storage-facility/)

**Role:** data. New facility 40 MW /80 MWh enters operation in Szazhalombatta. Huawei equipment, Forest-Vill main contractor. Separate 2022 Tesla demonstrator 4 MW /8 MWh excluded from new-facility ratings.

**Used by:** `catalogues/bess/sources.json`, `catalogues/bess/research/2026-11-01_expansion.md`.

### bess_baltic_storage_platform

Baltic Storage Platform (n.d.). **Kiisa and Arukula battery parks**. [Source](https://balticstorageplatform.ee/)

**Role:** data. Two independent 100 MW /200 MWh parks. Kiisa operating for grid services Q4 2025. Arukula construction completed in 2026; both regulate grid frequency. No exact COD inferred. Joint venture Evecon, Corsica Sole and Mirova.

**Used by:** `catalogues/bess/sources.json`, `catalogues/bess/research/2026-11-01_expansion.md`.

### bess_aemo_nem_oct2026_bess

Australian Energy Market Operator (2026). **NEM Generation Information, October 2026: battery unit inventory**. [Source](https://www.aemo.com.au/-/media/files/electricity/nem/planning_and_forecasting/generation_information/2026/nem-generation-information-oct-2026.xlsx?rev=e4625386b864409786cd79986dd0ac04&sc_lang=en)

**Role:** data. Primary-source BESS factual metadata; see catalogue for access method and rating/scope qualifications.

**Used by:** `catalogues/bess/sources.json`, `catalogues/bess/research/2026-11-01_australia_chile.md`.

### bess_cne_oct2026_bess

Comisión Nacional de Energía de Chile (2026). **Tablas de declaración en construcción, octubre 2026: BESS**. [Source](https://www.cne.cl/wp-content/uploads/2026/10/Tablas-Declaracion-Construccion-octubre-2026.xlsx)

**Role:** data. Primary-source BESS factual metadata; see catalogue for access method and rating/scope qualifications.

**Used by:** `catalogues/bess/sources.json`, `catalogues/bess/research/2026-11-01_australia_chile.md`.

### bess_cne_resolution_603_2026

Comisión Nacional de Energía de Chile (2026). **Resolución Exenta 603/2026: actualización de instalaciones en construcción**. [Source](https://www.cne.cl/wp-content/uploads/2026/10/Resolucion-Exenta-603-2026.pdf)

**Role:** data. Primary-source BESS factual metadata; see catalogue for access method and rating/scope qualifications.

**Used by:** `catalogues/bess/sources.json`, `catalogues/bess/research/2026-11-01_australia_chile.md`.

### bess_sec_mreh_project

State Electricity Commission of Victoria (n.d.). **Melbourne Renewable Energy Hub**. [Source](https://www.secvictoria.com.au/investments/melbourne-renewable-energy-hub)

**Role:** data. Primary-source BESS factual metadata; see catalogue for access method and rating/scope qualifications.

**Used by:** `catalogues/bess/sources.json`, `catalogues/bess/research/2026-11-01_australia_chile.md`.

### bess_edify_riverina_projects

Edify Energy (n.d.). **Riverina and Darlington Point Energy Storage Systems**. [Source](https://edifyenergy.com/project/riverina-darlington-point/)

**Role:** data. Primary-source BESS factual metadata; see catalogue for access method and rating/scope qualifications.

**Used by:** `catalogues/bess/sources.json`, `catalogues/bess/research/2026-11-01_australia_chile.md`.

### bess_engie_libelula_loros_2026

ENGIE Chile (2026). **Entrada en operación de BESS Libélula y BESS Los Loros**. [Source](https://www.engie.cl/impulsamos-la-transicion-energetica-con-la-entrada-en-operacion-de-dos-nuevos-parques-de-almacenamiento/)

**Role:** data. Primary-source BESS factual metadata; see catalogue for access method and rating/scope qualifications.

**Used by:** `catalogues/bess/sources.json`, `catalogues/bess/research/2026-11-01_australia_chile.md`.

### bess_engie_tocopilla_cod_2026

ENGIE Chile (2026). **Entrada en operación comercial de BESS Tocopilla**. [Source](https://www.engie.cl/obtuvimos-la-entrada-en-operacion-comercial-de-bess-tocopilla/)

**Role:** data. Primary-source BESS factual metadata; see catalogue for access method and rating/scope qualifications.

**Used by:** `catalogues/bess/sources.json`, `catalogues/bess/research/2026-11-01_australia_chile.md`.

### bess_engie_lile_cod_2026

ENGIE Chile (2026). **Reconversión del Complejo Energético Mejillones: BESS Lile**. [Source](https://www.engie.cl/concluimos-la-primera-etapa-de-la-reconversion-del-complejo-energetico-mejillones/)

**Role:** data. Primary-source BESS factual metadata; see catalogue for access method and rating/scope qualifications.

**Used by:** `catalogues/bess/sources.json`, `catalogues/bess/research/2026-11-01_australia_chile.md`.

### bess_colbun_q3_2026_bess

Colbún (2026). **Resultados del tercer trimestre de 2026: avance BESS**. [Source](https://www.colbun.cl/corporativo/sala-de-prensa/noticias-y-comunicados/detalle/2026/10/28/colbun-informa-ebitda-de-us196-6-millones-durante-el-tercer-trimestre-de-2026)

**Role:** data. Primary-source BESS factual metadata; see catalogue for access method and rating/scope qualifications.

**Used by:** `catalogues/bess/sources.json`, `catalogues/bess/research/2026-11-01_australia_chile.md`.

### bess_colbun_celda_project

Colbún (n.d.). **Proyecto Sistema de Baterías Celda Solar**. [Source](https://www.colbun.cl/nuestras-energias/proyectos-de-energia-renovable/proyectos-de-almacenamiento/celda-solar)

**Role:** data. Primary-source BESS factual metadata; see catalogue for access method and rating/scope qualifications.

**Used by:** `catalogues/bess/sources.json`, `catalogues/bess/research/2026-11-01_australia_chile.md`.

### bess_colbun_das_ii_project

Colbún (n.d.). **BESS Diego de Almagro Sur II**. [Source](https://www.colbun.cl/nuestras-energias/proyectos-de-energia-renovable/proyectos-de-almacenamiento/bess-ii-das)

**Role:** data. Primary-source BESS factual metadata; see catalogue for access method and rating/scope qualifications.

**Used by:** `catalogues/bess/sources.json`, `catalogues/bess/research/2026-11-01_australia_chile.md`.

### bess_engie_vilvoorde_project

ENGIE Belgium (n.d.). **BESS Battery Park Vilvoorde**. [Source](https://corporate.engie.be/en/energy/batteries/bess-battery-park-vilvoorde)

**Role:** data. Primary-source BESS factual metadata; see catalogue for access method and rating/scope qualifications.

**Used by:** `catalogues/bess/sources.json`, `catalogues/bess/research/2026-11-01_australia_chile.md`.

### bess_engie_vilvoorde_cod_2025

ENGIE Belgium (2025). **Batterijpark van ENGIE in Vilvoorde volledig operationeel**. [Source](https://corporate.engie.be/nl/pers/batterijpark-van-engie-in-vilvoorde-volledig-operationeel)

**Role:** data. Primary-source BESS factual metadata; see catalogue for access method and rating/scope qualifications.

**Used by:** `catalogues/bess/sources.json`, `catalogues/bess/research/2026-11-01_australia_chile.md`.

### rwe_moerdijk_fid_2026

RWE (2026). **Moerdijk 400 MW final investment decision**. [Source](https://www.rwe.com/en/press/rwe-generation/2026-09-21-rwe-to-build-400-mw-battery-to-ease-grid-congestion-in-noord-brabant/)

**Role:** data_source. Primary-source factual catalogue evidence; source conditions and locators retained in catalogue source registry.

**Used by:** `catalogues/bess/sources.json`.

### rwe_eemshaven_page

RWE (2026). **Eemshaven battery storage**. [Source](https://benelux.rwe.com/en/locations-and-projects/eemshaven-battery-storage/)

**Role:** data_source. Primary-source factual catalogue evidence; source conditions and locators retained in catalogue source registry.

**Used by:** `catalogues/bess/sources.json`.

### rwe_moerdijk_cod_2025

RWE (2025). **Moerdijk inertia battery commercial operation**. [Source](https://benelux.rwe.com/en/press/2025-06-16-rwes-innovative-battery-storage-in-moerdijk-achieves-commercial-operation/)

**Role:** data_source. Primary-source factual catalogue evidence; source conditions and locators retained in catalogue source registry.

**Used by:** `catalogues/bess/sources.json`.

### rwe_hambach_2026

RWE (2026). **Large-scale storage at Hambach mine**. [Source](https://www.rwe.com/en/press/rwe-generation/2026-07-28-rwe-to-build-large-scale-storage-at-hambach-mine/)

**Role:** data_source. Primary-source factual catalogue evidence; source conditions and locators retained in catalogue source registry.

**Used by:** `catalogues/bess/sources.json`.

### rwe_bvb_2026

RWE (2026). **SIGNAL IDUNA PARK battery commissioned**. [Source](https://www.rwe.com/en/press/rwe-ag/2026-10-26-rwe-and-bvb-have-commissioned-a-battery-storage-system-at-signal-iduna-park/)

**Role:** data_source. Primary-source factual catalogue evidence; source conditions and locators retained in catalogue source registry.

**Used by:** `catalogues/bess/sources.json`.

### rwe_gundremmingen_2025

RWE (2025). **Gundremmingen groundbreaking**. [Source](https://www.rwe.com/en/press/rwe-generation/2025-10-29-rwe-is-constructing-germanys-largest-battery-storage-facility-in-gundremmingen/)

**Role:** data_source. Primary-source factual catalogue evidence; source conditions and locators retained in catalogue source registry.

**Used by:** `catalogues/bess/sources.json`.

### rwe_lingen_werne_2023

RWE (2023). **Lingen and Werne installation complete**. [Source](https://www.rwe.com/en/press/rwe-generation/2023-01-09-rwe-completes-megabattery-in-lingen-and-werne/)

**Role:** data_source. Primary-source factual catalogue evidence; source conditions and locators retained in catalogue source registry.

**Used by:** `catalogues/bess/sources.json`.

### rwe_lingen_werne_page

RWE (2026). **Megabatterie plus Wasserkraft**. [Source](https://www.rwe.com/der-konzern/laender-und-standorte/megabatterie-plus-wasserkraft/)

**Role:** data_source. Primary-source factual catalogue evidence; source conditions and locators retained in catalogue source registry.

**Used by:** `catalogues/bess/sources.json`.

### rwe_lingen_dralon_2026

RWE (2026). **Lingen 400 MW investment decision**. [Source](https://www.rwe.com/en/investor-relations/financial-calendar-and-publications/news-and-ad-hoc-announcements/news/news-2026-01-29/)

**Role:** data_source. Primary-source factual catalogue evidence; source conditions and locators retained in catalogue source registry.

**Used by:** `catalogues/bess/sources.json`.

### rwe_hamm_neurath_page_2026

RWE (2026). **Hamm and Neurath battery storage**. [Source](https://www.rwe.com/en/the-group/countries-and-locations/220-mw-battery-storage-system-in-germany/)

**Role:** data_source. Primary-source factual catalogue evidence; source conditions and locators retained in catalogue source registry.

**Used by:** `catalogues/bess/sources.json`.

### afdb_eskom_appraisal_2021

African Development Bank (2021). **Eskom Distributed Battery Energy Storage Project appraisal report**. [Source](https://www.afdb.org/sites/default/files/documents/projects-and-operations/south_africa_-_eskom_distributed_battery_energy_storage_project_-_appraisal_report.pdf)

**Role:** data_source. Factual BESS evidence; revision, access terms, field locators and available hashes: catalogues/bess/sources.json.

**Used by:** `catalogues/bess/sources.json`.

### afdb_eskom_ipr_20260521

African Development Bank (2026). **Eskom Distributed Battery Energy Storage Program IPR March 2026**. [Source](https://www.afdb.org/sites/default/files/documents/projects-and-operations/p-za-fa0-006.doc.pdf)

**Role:** data_source. Factual BESS evidence; revision, access terms, field locators and available hashes: catalogues/bess/sources.json.

**Used by:** `catalogues/bess/sources.json`.

### wsp_eskom_portfolio

WSP (2026). **Helping to shape South Africa’s energy transition**. [Source](https://www.wsp.com/en-za/projects/battery-energy-storage-solutions-across-several-eskom-distribution-sites)

**Role:** data_source. Factual BESS evidence; revision, access terms, field locators and available hashes: catalogues/bess/sources.json.

**Used by:** `catalogues/bess/sources.json`.

### nampower_projects_2026

NamPower (2026). **Generation projects: Omburu and Lithops BESS**. [Source](https://www.nampower.com.na/Projects)

**Role:** data_source. Factual BESS evidence; revision, access terms, field locators and available hashes: catalogues/bess/sources.json.

**Used by:** `catalogues/bess/sources.json`.

### nampower_omburu_factsheet

NamPower (2026). **Omburu BESS project fact sheet**. [Source](https://www.nampower.com.na/Media/Document/979f6783-27cf-46af-bfe2-c476d8fd645d.pdf)

**Role:** data_source. Factual BESS evidence; revision, access terms, field locators and available hashes: catalogues/bess/sources.json.

**Used by:** `catalogues/bess/sources.json`.

### nampower_lithops_202609

NamPower (2026). **Lithops BESS project fact sheet September 2026**. [Source](https://www.nampower.com.na/Media/Document/41c24ee5-90fa-412c-a87f-aee748e0348f.pdf)

**Role:** data_source. Factual BESS evidence; revision, access terms, field locators and available hashes: catalogues/bess/sources.json.

**Used by:** `catalogues/bess/sources.json`.

### axian_kolda_close_20260331

AXIAN Energy (2026). **Closing financier de la centrale NEA Kolda au Sénégal**. [Source](https://mediaroom.axian-group.com/presse/document/communique_de_presse_closing_inancier-nea-olda.pdf)

**Role:** data_source. Factual BESS evidence; revision, access terms, field locators and available hashes: catalogues/bess/sources.json.

**Used by:** `catalogues/bess/sources.json`.

### scatec_egypt

Scatec (2026). **Egypt operating and backlog portfolio**. [Source](https://www.scatec.com/en/project/egypt/)

**Role:** data_source. Factual BESS evidence; revision, access terms, field locators and available hashes: catalogues/bess/sources.json.

**Used by:** `catalogues/bess/sources.json`.

### scatec_obelisk

Scatec (2026). **Commercial operations reached for final phase of Obelisk**. [Source](https://www.scatec.com/en/commercial-operations-reached-for-the-final-phase-of-the-obelisk-project-in-egypt/)

**Role:** data_source. Factual BESS evidence; revision, access terms, field locators and available hashes: catalogues/bess/sources.json.

**Used by:** `catalogues/bess/sources.json`.

### scatec_dandara

Scatec (2026). **Financing secured for first phase of Dandara**. [Source](https://www.scatec.com/en/scatec-secures-financing-for-the-first-phase-of-the-dandara-solar-and-bess-project-in-egypt/)

**Role:** data_source. Factual BESS evidence; revision, access terms, field locators and available hashes: catalogues/bess/sources.json.

**Used by:** `catalogues/bess/sources.json`.

### scatec_valley

Scatec (2026). **Shadwan construction and Energy Valley financing**. [Source](https://www.scatec.com/en/scatec-starts-construction-of-the-900-mw-shadwan-wind-project-in-egypt/)

**Role:** data_source. Factual BESS evidence; revision, access terms, field locators and available hashes: catalogues/bess/sources.json.

**Used by:** `catalogues/bess/sources.json`.

### ebrd_nefertiti

European Bank for Reconstruction and Development (2026). **AMEA Nefertiti Battery Energy Storage, project 56522**. [Source](https://www.ebrd.com/home/work-with-us/projects/psd/56522.html)

**Role:** data_source. Factual BESS evidence; revision, access terms, field locators and available hashes: catalogues/bess/sources.json.

**Used by:** `catalogues/bess/sources.json`.

### ifc_abydos_finance

International Finance Corporation (2025). **IFC and AMEA Power launch first Egyptian battery storage**. [Source](https://www.ifc.org/en/pressroom/2025/ifc-and-amea-power-launch-egypt-s-first-battery-energy-storage-system-to-boost-ene)

**Role:** data_source. Factual BESS evidence; revision, access terms, field locators and available hashes: catalogues/bess/sources.json.

**Used by:** `catalogues/bess/sources.json`.

### ebrd_valley

European Bank for Reconstruction and Development (2026). **Energy Valley, project 57439**. [Source](https://www.ebrd.com/home/work-with-us/projects/psd/57439.html)

**Role:** data_source. Factual BESS evidence; revision, access terms, field locators and available hashes: catalogues/bess/sources.json.

**Used by:** `catalogues/bess/sources.json`.

### eib_dandara

European Investment Bank (2026). **Financing Dandara solar and battery project in Egypt**. [Source](https://www.eib.org/de/press/all/2026-363-eib-provides-up-to-usd90-million-for-one-of-the-largest-solar-and-battery-projects-in-egypt-and-africa)

**Role:** data_source. Factual BESS evidence; revision, access terms, field locators and available hashes: catalogues/bess/sources.json.

**Used by:** `catalogues/bess/sources.json`.

### ebrd_obelisk

European Bank for Reconstruction and Development (2025). **Scatec Solar PV and Battery Energy Storage System, project 55308**. [Source](https://www.ebrd.com/home/work-with-us/projects/psd/55308.html)

**Role:** data_source. Factual BESS evidence; revision, access terms, field locators and available hashes: catalogues/bess/sources.json.

**Used by:** `catalogues/bess/sources.json`.

### boe_a_2026_2014

Agencia Estatal Boletín Oficial del Estado (2026). **BOE-A-2026-2014**. [Source](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-2014)

**Role:** data_source. Adapted BOE data; source terms and scope in BESS register.

**Used by:** `catalogues/bess/sources.json`.

### boe_a_2026_2133

Agencia Estatal Boletín Oficial del Estado (2026). **BOE-A-2026-2133**. [Source](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-2133)

**Role:** data_source. Adapted BOE data; source terms and scope in BESS register.

**Used by:** `catalogues/bess/sources.json`.

### boe_a_2025_18285

Agencia Estatal Boletín Oficial del Estado (2025). **BOE-A-2025-18285**. [Source](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-18285)

**Role:** data_source. Adapted BOE data; source terms and scope in BESS register.

**Used by:** `catalogues/bess/sources.json`.

### boe_b_2026_35371

Agencia Estatal Boletín Oficial del Estado (2026). **BOE-B-2026-35371**. [Source](https://www.boe.es/diario_boe/txt.php?id=BOE-B-2026-35371)

**Role:** data_source. Adapted BOE data; source terms and scope in BESS register.

**Used by:** `catalogues/bess/sources.json`.

### boe_b_2026_35372

Agencia Estatal Boletín Oficial del Estado (2026). **BOE-B-2026-35372**. [Source](https://www.boe.es/diario_boe/txt.php?id=BOE-B-2026-35372)

**Role:** data_source. Adapted BOE data; source terms and scope in BESS register.

**Used by:** `catalogues/bess/sources.json`.

### byd_bcu20_hvs_20250328

BYD (2026). **Battery-Box Premium HVS BCU2.0 datasheet**. [Source](https://bydbatterybox.com/uploads/downloads/BCU2.0_BBOX_HVS_Datasheet_EN_V1.0_250328-67ee42d4ced21.pdf)

**Role:** data_source. Primary-source factual catalogue evidence; source conditions and locators retained in catalogue source registry.

**Used by:** `catalogues/bess_oem/sources.json`.

### byd_bcu20_hvm_20250328

BYD (2026). **Battery-Box Premium HVM BCU2.0 datasheet**. [Source](https://bydbatterybox.com/uploads/downloads/BCU2.0_BBOX_HVM_Datasheet_EN_V1.0_250328-67ee3a426f6ce.pdf)

**Role:** data_source. Primary-source factual catalogue evidence; source conditions and locators retained in catalogue source registry.

**Used by:** `catalogues/bess_oem/sources.json`.

### dyness_tower_pro_20250626

Dyness (2025). **Tower Pro datasheet EN 20250626**. [Source](https://dyness.com/Public/Uploads/uploadfile/files/20250729/TowerProDatasheetEN20250626.pdf)

**Role:** data_source. Primary-source factual catalogue evidence; source conditions and locators retained in catalogue source registry.

**Used by:** `catalogues/bess_oem/sources.json`.

### sungrow_sbr_es_v13

Sungrow (2022). **SBR battery datasheet (Spanish)**. [Source](https://spa.sungrowpower.com/upload/file/20220627/ES%20DS%20SBR096%20SBR128%20SBR160%20SBR192%20SBR224%20SBR256%20Datasheet.pdf)

**Role:** data_source. Factual BESS evidence; revision, access terms, field locators and available hashes: catalogues/bess_oem/sources.json. Year is printed copyright year, not asserted publication date.

**Used by:** `catalogues/bess_oem/sources.json`.

### sungrow_sbh_es_v3_1

Sungrow (2023). **SBH battery datasheet (Spanish)**. [Source](https://spa.sungrowpower.com/upload/file/20240308/ES_DS_SBH100_150_200_250_300_350_400_Ficha_T%C3%A9cnica.pdf)

**Role:** data_source. Factual BESS evidence; revision, access terms, field locators and available hashes: catalogues/bess_oem/sources.json. Year is printed copyright year, not asserted publication date.

**Used by:** `catalogues/bess_oem/sources.json`.

### freedomwon_solva_dc208_20260917

Freedom Won (2026). **SOLVA DC208 specification sheet**. [Source](https://www.freedomwon.co.za/wp-content/uploads/SOLVA-DC208-Spec-Sheet-170926.pdf)

**Role:** data_source. Factual BESS evidence; revision, access terms, field locators and available hashes: catalogues/bess_oem/sources.json.

**Used by:** `catalogues/bess_oem/sources.json`.

### freedomwon_solva_ac261_20260917

Freedom Won (2026). **SOLVA AC261 specification sheet**. [Source](https://www.freedomwon.co.za/wp-content/uploads/SOLVA-AC261-Spec-Sheet-170926.pdf)

**Role:** data_source. Factual BESS evidence; revision, access terms, field locators and available hashes: catalogues/bess_oem/sources.json.

**Used by:** `catalogues/bess_oem/sources.json`.

### freedomwon_solva_dc261_20260917

Freedom Won (2026). **SOLVA DC261 specification sheet**. [Source](https://www.freedomwon.co.za/wp-content/uploads/SOLVA-DC261-Spec-Sheet-170926.pdf)

**Role:** data_source. Factual BESS evidence; revision, access terms, field locators and available hashes: catalogues/bess_oem/sources.json.

**Used by:** `catalogues/bess_oem/sources.json`.

### freedomwon_solva_rt261_20260917

Freedom Won (2026). **SOLVA RT261 specification sheet**. [Source](https://www.freedomwon.co.za/wp-content/uploads/SOLVA-RT261-Spec-Sheet-170926.pdf)

**Role:** data_source. Factual BESS evidence; revision, access terms, field locators and available hashes: catalogues/bess_oem/sources.json.

**Used by:** `catalogues/bess_oem/sources.json`.

### freedomwon_solva_ac418_20260917

Freedom Won (2026). **SOLVA AC418 specification sheet**. [Source](https://www.freedomwon.co.za/wp-content/uploads/SOLVA-AC418-Spec-Sheet-170926.pdf)

**Role:** data_source. Factual BESS evidence; revision, access terms, field locators and available hashes: catalogues/bess_oem/sources.json.

**Used by:** `catalogues/bess_oem/sources.json`.

### freedomwon_solva_dc418_20260917

Freedom Won (2026). **SOLVA DC418 specification sheet**. [Source](https://www.freedomwon.co.za/wp-content/uploads/SOLVA-DC418-Spec-Sheet-170926.pdf)

**Role:** data_source. Factual BESS evidence; revision, access terms, field locators and available hashes: catalogues/bess_oem/sources.json.

**Used by:** `catalogues/bess_oem/sources.json`.

### goodwe_lynx_f_20230105

GoodWe (2023). **Lynx Home F datasheet, 2023-01-05 EN V2.1**. [Source](https://en.goodwe.com/Ftp/EN/Downloads/Datasheet/GW_Lynx%20Home%20F%20Series%20%28HV%29_Datasheet-EN.pdf)

**Role:** data_source. Exact configuration evidence and byte hash in BESS OEM source register.

**Used by:** `catalogues/bess_oem/sources.json`.

### goodwe_lynx_g2_20250124

GoodWe (2025). **Lynx F G2 datasheet, 2025-01-24 EN V2.1**. [Source](https://en.goodwe.com/Ftp/EN/Downloads/Datasheet/GW_Lynx-F-G2_Datasheet-EN.pdf)

**Role:** data_source. Exact configuration evidence and byte hash in BESS OEM source register.

**Used by:** `catalogues/bess_oem/sources.json`.

### fox_eq3300_20250416

Fox ESS (2025). **Fox ESS EQ3300 high voltage storage battery datasheet**. [Source](https://www.fox-ess.com/Public/Uploads/uploadfile/files/Download/EN-EQ3300-Datasheet-V1.2-20250416.pdf)

**Role:** data. Primary BESS factual evidence; V1.2 | 2025/04/16. Exact locators, downloaded-byte SHA-256 and reuse assessment are retained in the source register. No source documents redistributed.

**Used by:** `catalogues/bess_oem/sources.json`.

### fox_eq4800_20260526

Fox ESS (2026). **Fox ESS EQ4800 high voltage storage battery datasheet**. [Source](https://www.fox-ess.com/Public/Uploads/uploadfile/files/20260605/ENEQ4800DatasheetV1.320260526.pdf)

**Role:** data. Primary BESS factual evidence; V1.3 | 2026/05/26. Exact locators, downloaded-byte SHA-256 and reuse assessment are retained in the source register. No source documents redistributed.

**Used by:** `catalogues/bess_oem/sources.json`.

### freedomwon_coreva5_20260918

Freedom Won (Pty) Ltd (2026). **Freedom Won COREVA 5 specification sheet**. [Source](https://www.freedomwon.co.za/wp-content/uploads/Freedom-Won-COREVA-5-Spec-Sheet.pdf)

**Role:** data. Primary BESS factual evidence; 18-Sept-26. Exact locators, downloaded-byte SHA-256 and reuse assessment are retained in the source register. No source documents redistributed.

**Used by:** `catalogues/bess_oem/sources.json`.

### freedomwon_enva16_20260605

Freedom Won (Pty) Ltd (2026). **Freedom Won ENVA 16 specification sheet**. [Source](https://www.freedomwon.co.za/wp-content/uploads/Freedom-Won-ENVA-16-Spec-Sheet-280826.pdf)

**Role:** data. Primary BESS factual evidence; 05-June-2026. Exact locators, downloaded-byte SHA-256 and reuse assessment are retained in the source register. No source documents redistributed.

**Used by:** `catalogues/bess_oem/sources.json`.

### freedomwon_enva5_20260526

Freedom Won (Pty) Ltd (2026). **Freedom Won ENVA 5 specification sheet**. [Source](https://www.freedomwon.co.za/wp-content/uploads/Freedom-Won-ENVA-5-Spec-Sheet-260526.pdf)

**Role:** data. Primary BESS factual evidence; 26-May-2026. Exact locators, downloaded-byte SHA-256 and reuse assessment are retained in the source register. No source documents redistributed.

**Used by:** `catalogues/bess_oem/sources.json`.

### freedomwon_enva60hv_20260916

Freedom Won (Pty) Ltd (2026). **Freedom Won ENVA 60HV specification sheet**. [Source](https://www.freedomwon.co.za/wp-content/uploads/Freedom-Won-ENVA-60-HV-Spec-Sheet-180926.pdf)

**Role:** data. Primary BESS factual evidence; 16-Sept-2026. Exact locators, downloaded-byte SHA-256 and reuse assessment are retained in the source register. No source documents redistributed.

**Used by:** `catalogues/bess_oem/sources.json`.

### freedomwon_enva_guarantee_202608

Freedom Won (Pty) Ltd (n.d.). **ENVA Range Battery Guarantee**. [Source](https://www.freedomwon.co.za/wp-content/uploads/ENVA-Guarantee.pdf)

**Role:** data. Primary BESS factual evidence; Original release August 2026. Exact locators, downloaded-byte SHA-256 and reuse assessment are retained in the source register. No source documents redistributed.

**Used by:** `catalogues/bess_oem/sources.json`.

### freedomwon_solva_coreva_guarantee_v2

Freedom Won (Pty) Ltd (n.d.). **COREVA 5 and SOLVA Range Product Guarantee**. [Source](https://www.freedomwon.co.za/wp-content/uploads/COREVA-and-SOLVA-warranty-05082026-1.pdf)

**Role:** data. Primary BESS factual evidence; FW-COREVA5-SOLVA-GTY-001; Version 2; original release July 2026. Exact locators, downloaded-byte SHA-256 and reuse assessment are retained in the source register. No source documents redistributed.

**Used by:** `catalogues/bess_oem/sources.json`.

### iea_battery_storage_system_role_20260529

International Energy Agency (2026). **Battery storage is scaling up and taking on a larger system role**. [Source](https://www.iea.org/commentaries/battery-storage-is-scaling-up-and-taking-on-a-larger-system-role)

**Role:** background. CC BY 4.0; 2025 annual stationary battery power additions, not operating energy capacity. Country figures and regional aggregates remain separate.

**Used by:** `catalogues/bess/research/2026-11-01_india_fox_freedom_markets.json`.

### pib_india_bess_20260630

Ministry of Power, Government of India / Press Information Bureau (2026). **Assessment of National Power Grid**. [Source](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2291650&lang=2&reg=48)

**Role:** data. Primary BESS factual evidence; PIB release 2291650; 2026-07-30. Exact locators, downloaded-byte SHA-256 and reuse assessment are retained in the source register. No source documents redistributed.

**Used by:** `catalogues/bess/sources.json`.

### pib_kavaratti_20240104

Ministry of New and Renewable Energy, Government of India / Press Information Bureau (2024). **Kavaratti first on-grid solar power plant with BESS**. [Source](https://www.pib.gov.in/PressReleasePage.aspx?PRID=1993036&lang=2&reg=48)

**Role:** data. Primary BESS factual evidence; PIB release 1993036; 2024-01-04. Exact locators, downloaded-byte SHA-256 and reuse assessment are retained in the source register. No source documents redistributed.

**Used by:** `catalogues/bess/sources.json`.

### pib_modhera_20230801

Ministry of New and Renewable Energy, Government of India / Press Information Bureau (2023). **Modhera solar village and battery storage parliamentary reply**. [Source](https://www.pib.gov.in/PressReleseDetailm.aspx?PRID=1944691&lang=2&reg=48)

**Role:** data. Primary BESS factual evidence; PIB release 1944691; 2023-08-01. Exact locators, downloaded-byte SHA-256 and reuse assessment are retained in the source register. No source documents redistributed.

**Used by:** `catalogues/bess/sources.json`.

### pib_nandyal_20251115

Ministry of New and Renewable Energy, Government of India / Press Information Bureau (2025). **SECI and Andhra Pradesh finalise 1200 MWh BESS and 50 MW hybrid project**. [Source](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2190326&lang=2&reg=48)

**Role:** data. Primary BESS factual evidence; PIB release 2190326; 2025-11-15. Exact locators, downloaded-byte SHA-256 and reuse assessment are retained in the source register. No source documents redistributed.

**Used by:** `catalogues/bess/sources.json`.

### pib_netra_20251111

Ministry of Power, Government of India / Press Information Bureau (2025). **India first MWh-scale vanadium flow battery inaugurated at NTPC NETRA**. [Source](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2188916&lang=2&reg=48)

**Role:** data. Primary BESS factual evidence; PIB release 2188916; 2025-11-11. Exact locators, downloaded-byte SHA-256 and reuse assessment are retained in the source register. No source documents redistributed.

**Used by:** `catalogues/bess/sources.json`.

### pib_rajnandgaon_20240224

Ministry of New and Renewable Energy, Government of India / Press Information Bureau (2024). **SECI unveils solar-battery project in Chhattisgarh**. [Source](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2008681&lang=2&reg=48)

**Role:** data. Primary BESS factual evidence; PIB release 2008681; 2024-02-24. Exact locators, downloaded-byte SHA-256 and reuse assessment are retained in the source register. No source documents redistributed.

**Used by:** `catalogues/bess/sources.json`.

### ea_nz_fleet_20260702

Electricity Authority, New Zealand (2026). **Dispatched generation plant, 2 July 2026**. [Source](https://emidatasets.blob.core.windows.net/publicdata/Datasets/Wholesale/Generation/GenerationFleet/Existing/20260702_DispatchedGenerationPlant.csv)

**Role:** data. BESS factual observations; exact revision, source hash, locators and conditions in source registry.

**Used by:** `catalogues/bess/sources.json`.

### fox_ecs2900_20250401

Fox ESS (2025). **ECS2900 high voltage storage battery datasheet**. [Source](https://www.fox-ess.com/download/upfiles/EN-ECS2900-Datasheet-V3.7-20250401.pdf)

**Role:** data. BESS factual observations; exact revision, source hash, locators and conditions in source registry.

**Used by:** `catalogues/bess_oem/sources.json`.

### fox_ecs4300h_20250401

Fox ESS (2025). **ECS4300H high voltage storage battery datasheet**. [Source](https://www.fox-ess.com/Public/Uploads/uploadfile/files/Download/EN-ECS4300H-Datasheet-V1.8-20250401.pdf)

**Role:** data. BESS factual observations; exact revision, source hash, locators and conditions in source registry.

**Used by:** `catalogues/bess_oem/sources.json`.

### fox_ecs4800_20250401

Fox ESS (2025). **ECS4800 battery datasheet**. [Source](https://vn.fox-ess.com/download/upfiles/EN-ECS4800-Datasheet-V2.0-20250401.pdf)

**Role:** data. Exact revision, hash and field evidence in BESS source registry.

**Used by:** `catalogues/bess_oem/sources.json`.

### fox_ecs2800_20230707

Fox ESS (2023). **ECS2800 battery datasheet**. [Source](https://es.fox-ess.com/wp-content/uploads/2023/01/ES-ECS2800-Datasheet-V1.4-7.7.pdf)

**Role:** data. Exact revision, hash and field evidence in BESS source registry.

**Used by:** `catalogues/bess_oem/sources.json`.

### genesis_fy27q1_20261022

Genesis Energy / NZX (2026). **Genesis FY27 Q1 performance report**. [Source](https://announcements.nzx.com/attachment/479717.pdf)

**Role:** data. Exact revision, hash and field evidence in BESS source registry.

**Used by:** `catalogues/bess/sources.json`.

### genesis_huntly_fid_20260420

Genesis Energy / NZX (2026). **Genesis reaches FID on Second Stage Huntly BESS**. [Source](https://www.nzx.com/announcements/471153)

**Role:** data. Exact revision, hash and field evidence in BESS source registry.

**Used by:** `catalogues/bess/sources.json`.

### freedom_lite2_hv_202506

Freedom Won (2025). **LiTE 2 Commercial HV range specifications**. [Source](https://www.freedomwon.co.za/wp-content/uploads/LiTE-2-COMMERCIAL-HV-Range-Overview-Sheet.pdf)

**Role:** data. Primary-source factual observations; source registry records access and checksum limitations.

**Used by:** `catalogues/bess_oem/sources.json`.

### freedom_lite2_hvp_202506

Freedom Won (2025). **LiTE 2 Commercial HV+ range specifications**. [Source](https://www.freedomwon.co.za/wp-content/uploads/LiTE-2-COMMERCIAL-HV-Range-Overview-Sheet-2.pdf)

**Role:** data. Primary-source factual observations; source registry records access and checksum limitations.

**Used by:** `catalogues/bess_oem/sources.json`.

### edc_annual2025

Energy Development Corporation (2025). **EDC 2025 Annual Report**. [Source](https://www.energy.com.ph/wp-content/uploads/2026/04/2026-ASM-Annual-Report-2025.pdf)

**Role:** data. Primary-source factual observations; source registry records access and checksum limitations.

**Used by:** `catalogues/bess/sources.json`.

### ngcp_as_202603

National Grid Corporation of the Philippines (2026). **Existing ancillary services providers as of March2026**. [Source](https://www.ngcp.ph/Attachment-Uploads/Customer%20Bulletin%20Nos-2026-04-10-08-44-31.%202026-19.pdf)

**Role:** data. Primary-source factual observations; source registry records access and checksum limitations.

**Used by:** `catalogues/bess/sources.json`.

### pylon_h3_20250121

Pylon Technologies Co., Ltd. (2025). **Force-H3 high-voltage stackable battery specifications**. [Source](https://solar-distribution.baywa-re.de/out/media/07_Force_H3_EN-SD-250121-Force-H3-_ESS_Spec-Pylontech.pdf)

**Role:** data. Primary-authored factual evidence; access limitations and locators in source register.

**Used by:** `catalogues/bess_oem/sources.json`.

### pylon_h2_20250121

Pylon Technologies Co., Ltd. (2025). **Force-H2 high-voltage stackable battery specifications**. [Source](https://solarshop.baywa-re.lv/en/documents/pylontech-residential-battery-solutions-11fh9637mza00001-11fh9637mza-00001-0/382/415.pdf)

**Role:** data. Primary-authored factual evidence; access limitations and locators in source register.

**Used by:** `catalogues/bess_oem/sources.json`.

### pylon_h3_manual_v11

Pylon Technologies Co., Ltd. (n.d.). **Force-H3 Operation Manual**. [Source](https://pvundso.de/Doku/Pylontec/Pylontech_Force_H3_Battery_Operation_Manual_V1.1.pdf)

**Role:** data. Undated OEM-authored manual V1.1, 5PMPA08-00250, obtained from public distributor mirror; access and byte hash in source registry.

**Used by:** `catalogues/bess_oem/sources.json`.

### saft_axpo_france_20261006

Saft (2026). **Saft and Axpo to deliver two battery energy storage projects in France**. [Source](https://saft.com/en/media-resources/press-release/saft-and-axpo-deliver-two-battery-energy-storage-projects-france)

**Role:** data. Primary-authored factual evidence; access limitations and locators in source register.

**Used by:** `catalogues/bess/sources.json`.

### saft_huntly_20240919

Saft (2024). **Saft utility-scale BESS will power Huntly Portfolio to drive New Zealand’s green energy transition**. [Source](https://saft.com/en/media-resources/press-releases/saft-utility-scale-bess-will-power-huntly-portfolio-drive-new-zealand)

**Role:** data. Primary-authored factual evidence; access limitations and locators in source register.

**Used by:** `catalogues/bess/sources.json`.

### saft_huntly_20260428

Saft (2026). **Saft and Genesis enter next phase of Huntly BESS with 200 MWh extension**. [Source](https://saft.com/en/media-resources/press-release/saft-and-genesis-enter-next-phase-huntly-bess-200-mwh-extension)

**Role:** data. Primary-authored factual evidence; access limitations and locators in source register.

**Used by:** `catalogues/bess/sources.json`.

### dyness_tower_20240112

Dyness (2024). **Tower technical specifications**. [Source](https://es.dyness.com/Public/Uploads/uploadfile/files/20250102/DynessTowerdatasheetchangguibanEN-104.pdf)

**Role:** data. Primary factual evidence; version, table/paragraph locator, source terms and byte availability in catalogue source register. Undated-page year is retrieval-year grouping.

**Used by:** `catalogues/bess_oem/sources.json`.

### dyness_stack100_manual_20250307

Dyness Digital Energy Technology Co., Ltd. (2025). **STACK100 User Manual**. [Source](https://es.dyness.com/Public/Uploads/uploadfile/files/20250828/UMWL0G0004238STACK100UserManualENV29.pdf)

**Role:** data. Primary factual evidence; version, table/paragraph locator, source terms and byte availability in catalogue source register. Undated-page year is retrieval-year grouping.

**Used by:** `catalogues/bess_oem/sources.json`.

### dyness_stack100_sheet_20260520

Dyness (2026). **STACK100 specifications, EU**. [Source](https://es.dyness.com/Public/Uploads/uploadfile/files/20260709/DynessSTACK100DatasheetenEU20260520-938.pdf)

**Role:** data. Primary factual evidence; version, table/paragraph locator, source terms and byte availability in catalogue source register. Undated-page year is retrieval-year grouping.

**Used by:** `catalogues/bess_oem/sources.json`.

### neoen_akkula_20251230

Neoen (2025). **Neoen launches Finland’s first 4-hour battery in Rauma, Southwest Finland**. [Source](https://neoen.com/en/news/2025/neoen-launches-finlands-first-4-hour-battery-in-rauma-southwest-finland/)

**Role:** data. Primary factual evidence; version, table/paragraph locator, source terms and byte availability in catalogue source register. Undated-page year is retrieval-year grouping.

**Used by:** `catalogues/bess/sources.json`.

### neoen_isbillen_site

Neoen (2026). **Isbillen Power Reserve**. [Source](https://sweden.neoen.com/sv/projekt/isbillen-power-reserve/)

**Role:** data. Primary factual evidence; version, table/paragraph locator, source terms and byte availability in catalogue source register. Undated-page year is retrieval-year grouping.

**Used by:** `catalogues/bess/sources.json`.

### neoen_isbillen_20240131

Neoen (2024). **Neoen launches construction of Isbillen Power Reserve, the largest battery in Sweden**. [Source](https://neoen.com/en/news/2024/neoen-launches-construction-of-isbillen-power-reserve-the-largest-battery-in-sweden/)

**Role:** data. Primary factual evidence; version, table/paragraph locator, source terms and byte availability in catalogue source register. Undated-page year is retrieval-year grouping.

**Used by:** `catalogues/bess/sources.json`.

### ignitis_battery_portfolio_20261102

Ignitis Renewables (2026). **Battery energy storage system portfolio**. [Source](https://ignitisrenewables.com/flexibility-technologies/)

**Role:** data. Primary factual evidence; version, table/paragraph locator, source terms and byte availability in catalogue source register. Undated-page year is retrieval-year grouping.

**Used by:** `catalogues/bess/sources.json`.

### ignitis_renewables_annual_2025

Ignitis Renewables (2025). **Ignitis Renewables Annual Report 2025**. [Source](https://ignitisrenewables.com/wp-content/uploads/2026/04/Annual-report_Ignitis-renewables_2025_ENG-2.pdf)

**Role:** data. Primary factual evidence; version, table/paragraph locator, source terms and byte availability in catalogue source register. Undated-page year is retrieval-year grouping.

**Used by:** `catalogues/bess/sources.json`.

### ignitis_tume_20260721

Ignitis Renewables (2026). **Ignitis Renewables to develop 107 MW Tume battery energy storage system in Latvia**. [Source](https://ignitisrenewables.com/ignitis-renewables-to-develop-107-mw-tume-battery-energy-storage-system-in-latvia/)

**Role:** data. Primary factual evidence; version, table/paragraph locator, source terms and byte availability in catalogue source register. Undated-page year is retrieval-year grouping.

**Used by:** `catalogues/bess/sources.json`.

### ignitis_kruonis_20260513

Ignitis Gamyba (2026). **Kruonio teritorijoje energiją kaups ne tik baseinas, bet ir kaupikliai**. [Source](https://ignitisgamyba.lt/apie-mus/naujienos/kruonio-teritorijoje-energija-kaups-ne-tik-baseinas-bet-ir-kaupikliai/4858)

**Role:** data. Primary factual evidence; version, table/paragraph locator, source terms and byte availability in catalogue source register. Undated-page year is retrieval-year grouping.

**Used by:** `catalogues/bess/sources.json`.

### ignitis_bess_construction_2025

Ignitis Renewables (2025). **Ignitis Group starts building battery energy storage parks in Lithuania**. [Source](https://ignitisrenewables.com/https-ignitisrenewables-com-ignitis-group-starts-building-battery-energy-storage-parks-in-lithuania/)

**Role:** data. Primary factual evidence; version, table/paragraph locator, source terms and byte availability in catalogue source register. Undated-page year is retrieval-year grouping.

**Used by:** `catalogues/bess/sources.json`.

### neoen_storen_site

Neoen (2026). **Storen Power Reserve**. [Source](https://sweden.neoen.com/sv/projekt/storen-power-reserve/)

**Role:** data. Primary factual evidence; version, table/paragraph locator, source terms and byte availability in catalogue source register. Undated-page year is retrieval-year grouping.

**Used by:** `catalogues/bess/sources.json`.

### ast_bess_opening_20251023

AS Augstsprieguma tīkls (AST) (2025). **AST Battery Energy Storage Systems in Rēzekne and Tume will start providing balancing reserves**. [Source](https://ast.lv/en/events/ast-battery-energy-storage-systems-rezekne-and-tume-will-start-providing-balancing-reserves)

**Role:** data. Primary factual evidence; source register records table/paragraph locator, terms and original-byte checksum. Undated page year is retrieval-year grouping.

**Used by:** `catalogues/bess/sources.json`.

### ast_electricity_review_2025

AS Augstsprieguma tīkls (AST) (2025). **Latvian electricity market review, year 2025**. [Source](https://ast.lv/en/electricity-market-review?month=13&year=2025)

**Role:** data. Primary factual evidence; source register records table/paragraph locator, terms and original-byte checksum. Undated page year is retrieval-year grouping.

**Used by:** `catalogues/bess/sources.json`.

### ast_battery_portfolio

AS Augstsprieguma tīkls (AST) (2026). **Batteries — AST synchronisation projects**. [Source](https://ast.lv/en/projects/batteries)

**Role:** data. Primary factual evidence; source register records table/paragraph locator, terms and original-byte checksum. Undated page year is retrieval-year grouping.

**Used by:** `catalogues/bess/sources.json`.

### neoen_storen_ntp_20230110

Neoen (2023). **Neoen launches construction of Storen Power Reserve**. [Source](https://neoen.com/app/uploads/2023/01/2023-01-10_MR_Neoen_Startofconstruction_StorenPowerReserve.pdf)

**Role:** data. Primary factual evidence; source register records table/paragraph locator, terms and original-byte checksum. Undated page year is retrieval-year grouping.

**Used by:** `catalogues/bess/sources.json`.

### dyness_residential_es_20240829

Dyness (2024). **Residential product brochure, Spanish**. [Source](https://es.dyness.com/Public/Uploads/uploadfile/files/20250227/DynessResidentialProductBrochureES.pdf)

**Role:** data. Primary factual metadata only; exact revision, locator, source terms and SHA-256 in source register.

**Used by:** `catalogues/bess_oem/sources.json`.

### dyness_powerbox_g2_au_20241011

Dyness (2024). **Powerbox G2 technical specifications, Australian publisher download**. [Source](https://au.dyness.com/Public/Uploads/uploadfile/files/20250704/5.DynessPowerboxG2datasheetEN.pdf)

**Role:** data. Primary factual metadata only; exact revision, locator, source terms and SHA-256 in source register.

**Used by:** `catalogues/bess_oem/sources.json`.

### ignitis_kelme_nts_2026

Ignitis Renewables (2026). **Kelmė Battery Energy Storage System non-technical summary**. [Source](https://ignitisrenewables.com/wp-content/uploads/2024/02/EN-Kelme_BESS_NTS_report.pdf)

**Role:** data. Primary factual metadata only; exact revision, locator, source terms and SHA-256 in source register.

**Used by:** `catalogues/bess/sources.json`.

### ignitis_mazeikiai_nts_2026

Ignitis Renewables (2026). **Mažeikiai Battery Energy Storage System non-technical summary**. [Source](https://ignitisrenewables.com/wp-content/uploads/2024/01/EN-Mazeikiai_BESS_NTS_report.pdf)

**Role:** data. Primary factual metadata only; exact revision, locator, source terms and SHA-256 in source register.

**Used by:** `catalogues/bess/sources.json`.

### solax_hv_s25_s36_manual_es_v00

SolaX Power Network Technology (Zhejiang) Co., Ltd. (2026). **T-BAT-SYS-HV-S25 / S36 user manual, Spanish**. [Source](https://es.solaxpower.com/uploads/file/t-bat-sys-hv-s2.53.6-user-manaul-es.pdf)

**Role:** data. Primary factual evidence. Exact revision, locator, terms and checksum in source register; undated manual grouped by retrieval year.

**Used by:** `catalogues/bess_oem/sources.json`.

### juniper_fdre_portfolio_20261016

Juniper Green Energy Limited (2026). **FDRE and BESS project portfolio**. [Source](https://www.junipergreenenergy.com/fdre/)

**Role:** data. Primary factual evidence. Exact revision, locator, terms and checksum in source register; undated manual grouped by retrieval year.

**Used by:** `catalogues/bess/sources.json`.

### victron_multiplus_ii_230v_20261102

Victron Energy (2026). **MultiPlus-II Inverter/Charger 230 V**. [Source](https://www.victronenergy.com/upload/documents/Datasheet-MultiPlus-II-inverter-charger-EN-.pdf)

**Role:** data. PDF page 2, exact model column; inverter/charger/general/enclosure rows and footnotes 1–5; page 1 topology and external transfer switch qualification.

**Used by:** `catalogues/bess_oem/sources.json`.

### victron_multiplus_ii_new_230v_20261102

Victron Energy (2026). **MultiPlus-II Inverter/Charger, new models, 230 V**. [Source](https://www.victronenergy.com/upload/documents/Datasheet-MultiPlus-II-inverter-charger-4k-4k5-6k5-10k-EN.pdf)

**Role:** data. PDF page 2, four exact model columns and footnotes; page 1 ESS topology. Apparent-feed-in row prints kW, so not used as MVA.

**Used by:** `catalogues/bess_oem/sources.json`, `data-retrieval/src/energy_data_retrieval/bess_oem_catalogue/victron.py`.

### victron_multiplus_ii_manual_es_20261102

Victron Energy (2026). **MultiPlus-II 230V: 7. Especificaciones técnicas**. [Source](https://www.victronenergy.com/media/pg/MultiPlus-II_230V/es/technical-specifications-mp-ii-230v.html)

**Role:** data. Section 7, three model tables: mass, maximum efficiency, search-mode consumption and battery-charge-current rows. Column spans reviewed.

**Used by:** `catalogues/bess_oem/sources.json`.

### sma_sunny_island_13_ds_es_31

SMA Solar Technology AG (2022). **Sunny Island 4.4M / 6.0H / 8.0H datasheet**. [Source](https://files.sma.de/downloads/SI44M-80H-13-DS-es-31.pdf)

**Role:** data. PDF page 3, exact SI4.4M-13/SI6.0H-13/SI8.0H-13 columns, AC-1/AC-2/DC/general rows and footnotes 1–7.

**Used by:** `catalogues/bess_oem/sources.json`.

### sma_sunny_island_page_20261102

SMA Solar Technology AG (2026). **Sunny Island 4.4M / 6.0H / 8.0H**. [Source](https://www.sma.de/en/products/battery-inverters/sunny-island-44m-60h-80h)

**Role:** data. Product introduction: Sunny Island 4.4M version no longer produced.

**Used by:** `catalogues/bess_oem/sources.json`.

### scatec_south_africa_20261102

Scatec ASA (2026). **South Africa**. [Source](https://www.scatec.com/en/project/south-africa/)

**Role:** data. Assets table: Kenhardt operational 225 MW/1140 MWh; Mogobe construction 103/412; Haru backlog 123/492.

**Used by:** `catalogues/bess/sources.json`.

### scatec_philippines_20261102

Scatec ASA (2026). **Philippines**. [Source](https://www.scatec.com/en/project/philippines/)

**Role:** data. Assets table: Magat operational 40 MW/40 MWh; Binga, Binga 2 and Ambuklao construction each 40/40; exclude hydro and solar rows.

**Used by:** `catalogues/bess/sources.json`.

### scatec_kenhardt_cod_20231211

Scatec ASA (2023). **Energising tomorrow: Scatec ignites one of the world’s largest hybrid solar and battery project in South Africa**. [Source](https://www.scatec.com/en/energising-tomorrow-scatec-ignites-one-of-the-worlds-largest-hybrid-solar-and-battery-project-in-south-africa/)

**Role:** data. Opening paragraphs, equity paragraph and notes to editors: three-plant aggregate, 225 MW/1140 MWh, 456 battery units, 20-year PPA and hybrid capex.

**Used by:** `catalogues/bess/sources.json`.

### scatec_mogobe_close_20241018

Scatec ASA (2024). **Scatec reaches financial close and prepares for construction start for battery energy storage project in South Africa**. [Source](https://www.scatec.com/en/scatec-reaches-financial-close-and-prepares-for-construction-start-for-battery-energy-storage-project-in-south-africa/)

**Role:** data. Opening, PPA, capex/debt, equity, service-role and Kathu-location paragraphs.

**Used by:** `catalogues/bess/sources.json`.

### scatec_haru_award_20250530

Scatec ASA (2025). **Scatec wins battery storage project in South Africa**. [Source](https://www.scatec.com/en/scatec-wins-battery-storage-project-in-south-africa/)

**Role:** data. Opening award/capacity, 15-year contract, estimated capex, intended equity and Free State paragraphs.

**Used by:** `catalogues/bess/sources.json`.

### scatec_philippines_close_20260203

Scatec ASA (2026). **Scatec JV reaches financial close for 80 MW BESS in the Philippines and prepares for construction start**. [Source](https://www.scatec.com/en/scatec-jv-reaches-financial-close-for-80-mw-bess-in-the-philippines-and-prepares-for-construction-start/)

**Role:** data. Opening three paragraphs and ownership/financing paragraph; Binga phases remain distinct.

**Used by:** `catalogues/bess/sources.json`.

### scatec_magat2_cod_20260515

Scatec ASA (2026). **Scatec JV starts commercial operation of battery system in the Philippines**. [Source](https://www.scatec.com/en/scatec-jv-starts-commercial-operation-of-battery-system-in-the-philippines/)

**Role:** data. Opening two paragraphs, 40 MWh operating total and 50/50 JV/debt paragraphs. Phase1 24 MW; phase2 16 MW.

**Used by:** `catalogues/bess/sources.json`.

### scatec_obelisk_close_20250615

Scatec ASA (2025). **Scatec reaches financial close for the 1.1GW solar + 100MW/200MWh BESS Obelisk project**. [Source](https://www.scatec.com/en/scatec-reaches-financial-close-for-the-1-1gw-solar-100mw-200mwh-bess-obelisk-project/)

**Role:** data. Financing paragraphs: whole hybrid USD590m estimated capex, USD479.1m project financing, USD120m equity bridge; sovereign PPA guarantee.

**Used by:** `catalogues/bess/sources.json`.

### victron_quattro_230v_20261102

Victron Energy (2026). **Quattro Inverter/Charger 3kVA–15kVA 230 V**. [Source](https://www.victronenergy.com/upload/documents/Datasheet-Quattro-3kVA-15kVA-EN-.pdf)

**Role:** data. PDF page 2, five grouped columns containing nine exact codes; inverter, charger, enclosure and standards rows; footnotes 1–6.

**Used by:** `catalogues/bess_oem/sources.json`, `data-retrieval/src/energy_data_retrieval/bess_oem_catalogue/victron.py`.

### victron_multiplus_ii_120v_20261102

Victron Energy (2026). **MultiPlus-II Inverter/Charger 120 V**. [Source](https://www.victronenergy.com/upload/documents/Datasheet-MultiPlus-II-120V-EN-.pdf)

**Role:** data. PDF page 2, six exact model columns; inverter, charger, enclosure, listings and footnotes 1–7; 48/3000 dimensions use the UL1741-listed configuration.

**Used by:** `catalogues/bess_oem/sources.json`.

### giga_portfolio_20261102

GIGA Storage (2026). **GIGA Storage portfolio**. [Source](https://giga-storage.com/en/projects/)

**Role:** data. PROJECTS cards: eight listed assets, Hippo in project navigation. Capacity summary differences retained.

**Used by:** `catalogues/bess/sources.json`.

### giga_albatross_20261102

GIGA Storage (2026). **GIGA Storage albatross**. [Source](https://giga-storage.com/en/projects/albatross/)

**Role:** data. Project introduction, technical table, site description, partners and planning sections; see record extensions for exact sub-section.

**Used by:** `catalogues/bess/sources.json`.

### giga_blue_marlin_20261102

GIGA Storage (2026). **GIGA Storage blue marlin**. [Source](https://giga-storage.com/en/projects/blue-marlin/)

**Role:** data. Project introduction, technical table, site description, partners and planning sections; see record extensions for exact sub-section.

**Used by:** `catalogues/bess/sources.json`.

### giga_buffalo_20261102

GIGA Storage (2026). **GIGA Storage buffalo**. [Source](https://giga-storage.com/en/projects/buffalo/)

**Role:** data. Project introduction, technical table, site description, partners and planning sections; see record extensions for exact sub-section.

**Used by:** `catalogues/bess/sources.json`.

### giga_giraffe_20261102

GIGA Storage (2026). **GIGA Storage giraffe**. [Source](https://giga-storage.com/en/projects/giraffe/)

**Role:** data. Project introduction, technical table, site description, partners and planning sections; see record extensions for exact sub-section.

**Used by:** `catalogues/bess/sources.json`.

### giga_green_turtle_20261102

GIGA Storage (2026). **GIGA Storage green turtle**. [Source](https://giga-storage.com/en/projects/green-turtle/)

**Role:** data. Project introduction, technical table, site description, partners and planning sections; see record extensions for exact sub-section.

**Used by:** `catalogues/bess/sources.json`.

### giga_hippo_nl_20261102

GIGA Storage (2026). **GIGA Storage hippo nl**. [Source](https://giga-storage.com/en/projects/hippo-nl/)

**Role:** data. Project introduction, technical table, site description, partners and planning sections; see record extensions for exact sub-section.

**Used by:** `catalogues/bess/sources.json`.

### giga_leo_20261102

GIGA Storage (2026). **GIGA Storage leo**. [Source](https://giga-storage.com/en/projects/leo/)

**Role:** data. Project introduction, technical table, site description, partners and planning sections; see record extensions for exact sub-section.

**Used by:** `catalogues/bess/sources.json`.

### giga_leopard_20261102

GIGA Storage (2026). **GIGA Storage leopard**. [Source](https://giga-storage.com/en/projects/leopard/)

**Role:** data. Project introduction, technical table, site description, partners and planning sections; see record extensions for exact sub-section.

**Used by:** `catalogues/bess/sources.json`.

### giga_rhino_20261102

GIGA Storage (2026). **GIGA Storage rhino**. [Source](https://giga-storage.com/en/projects/rhino/)

**Role:** data. Project introduction, technical table, site description, partners and planning sections; see record extensions for exact sub-section.

**Used by:** `catalogues/bess/sources.json`.

### giga_lion_nl_20261102

GIGA Storage (2026). **GIGA Storage lion nl**. [Source](https://giga-storage.com/projecten/lion/)

**Role:** data. Project introduction, technical table, site description, partners and planning sections; see record extensions for exact sub-section.

**Used by:** `catalogues/bess/sources.json`.

### giga_lion_start_20261102

GIGA Storage (2026). **GIGA Storage lion start**. [Source](https://giga-storage.com/eerste-paal-geslagen-voor-giga-lion-in-amsterdam/)

**Role:** data. PROJECT GIGA LION; construction date, 10 MW/43 MWh, IJpolder 10 kV and contractor roles.

**Used by:** `catalogues/bess/sources.json`.

### giga_albatross_close_20261102

GIGA Storage (2026). **GIGA Storage albatross close**. [Source](https://giga-storage.com/en/giga-storage-bereikt-financial-close-voor-energieopslagproject-albatross-in-duitsland-en-bouwt-nu-aan-14-gw-in-drie-landen/)

**Role:** data. Opening paragraphs, financing, grid agreement, CATL role and schedule; portfolio aggregate wording excluded.

**Used by:** `catalogues/bess/sources.json`.

### giga_rhino_contract_20261102

GIGA Storage (2026). **GIGA Storage rhino contract**. [Source](https://giga-storage.com/en/repowered-ondertekenen/)

**Role:** data. Opening paragraphs: 12 MW/7.5 MWh, 2020 commissioning and prospective two-year Repowered contract.

**Used by:** `catalogues/bess/sources.json`.

### giga_leopard_close_20261102

GIGA Storage (2025). **GIGA Storage leopard close**. [Source](https://giga-storage.com/en/giga-storage-completes-%E2%82%AC300-million-financing-and-starts-construction-of-300mw-1200mwh-battery-storage-project-in-delfzijl/)

**Role:** data. Opening paragraphs: June 2025 construction, 300 MW/1200 MWh, financing and expected H2 2027 operation.

**Used by:** `catalogues/bess/sources.json`.

### victron_q120_20261102

Victron Energy (2026). **Datasheet Quattro 3 10kVA 120V EN **. [Source](https://www.victronenergy.com/upload/documents/Datasheet-Quattro-3-10kVA-120V-EN-.pdf)

**Role:** data. Page 2, exact model column and inverter/charger/enclosure rows; footnotes. Page 1 topology.

**Used by:** `catalogues/bess_oem/sources.json`.

### victron_q277_20261102

Victron Energy (2026). **Datasheet Quattro 15kVA 277V EN**. [Source](https://www.victronenergy.com/upload/documents/Datasheet-Quattro-15kVA-277V-EN.pdf)

**Role:** data. Page 2, exact model column and inverter/charger/enclosure rows; footnotes. Page 1 topology.

**Used by:** `catalogues/bess_oem/sources.json`.

### victron_qii_20261102

Victron Energy (2026). **Datasheet Quattro II inverter charger EN **. [Source](https://www.victronenergy.com/upload/documents/Datasheet-Quattro-II-inverter-charger-EN-.pdf)

**Role:** data. Page 2, exact model column and inverter/charger/enclosure rows; footnotes. Page 1 topology.

**Used by:** `catalogues/bess_oem/sources.json`.

### victron_m2_20261102

Victron Energy (2026). **Datasheet MultiPlus II 2x120V EN **. [Source](https://www.victronenergy.com/upload/documents/Datasheet-MultiPlus-II-2x120V-EN-.pdf)

**Role:** data. Page 2, exact model column and inverter/charger/enclosure rows; footnotes. Page 1 topology.

**Used by:** `catalogues/bess_oem/sources.json`.

### sembcorp_stacking_20251027

Sembcorp Industries (2025). **Sembcorp Unveils Landmark Clean Energy Initiatives on Jurong Island**. [Source](https://www.sembcorp.com/sg/news-and-insights/news/2025/sembcorp-unveils-landmark-clean-energy-initiatives-on-jurong-island/)

**Role:** data. Scaling up Singapore’s largest utility-scale energy storage system, paragraphs1–3

**Used by:** `catalogues/bess/sources.json`.

### deye_bosgpro_eu_20260414

Deye ESS (2026). **BOS-G Pro Series EU brochure**. [Source](https://deyeess.com/wp-content/uploads/2025/12/Deye-BOS-G-Pro-Series_Brochure_EU_20260414V1.0.pdf)

**Role:** data. Page 2 exact configuration columns and footnotes; page 3 component tables

**Used by:** `catalogues/bess_oem/sources.json`.

### deye_bosgpro_page_20261102

Deye ESS (2026). **BOS-G Pro product specifications**. [Source](https://deyeess.com/product/bos-g-pro/)

**Role:** data. Specifications: exact four-model energy and DC-power entries

**Used by:** `catalogues/bess_oem/sources.json`.

### hubble_am4_20261102

Hubble Energy (2026). **AM-4 technical datasheet**. [Source](https://www.hubbleenergy.com/_files/ugd/49fdd5_9419257cb76d42a8be8cc973f4392b7e.pdf)

**Role:** data. Page 2 Technical Data and current footnote; page 1 revision

**Used by:** `catalogues/bess_oem/sources.json`.

### hubble_blade_20261102

Hubble Energy (2026). **BLADE technical datasheet**. [Source](https://www.hubbleenergy.com/_files/ugd/49fdd5_f9bb221cac594943a759bab118a36261.pdf)

**Role:** data. Page 2 Technical Data and current footnote; page 1 revision

**Used by:** `catalogues/bess_oem/sources.json`.

### hubble_am5_20261102

Hubble Energy (2026). **AM5+ technical datasheet**. [Source](https://www.hubbleenergy.com/_files/ugd/49fdd5_d644c03ebbf54a7d8856a155276b2802.pdf)

**Role:** data. Page 2 Technical Data and current footnote; page 1 revision

**Used by:** `catalogues/bess_oem/sources.json`.

### hubble_am5_page_20261102

Hubble Energy (2026). **AM5+ product page**. [Source](https://www.hubbleenergy.com/am-5plus)

**Role:** data. Technical specifications and feature list; discrepancies against versioned brochure

**Used by:** `catalogues/bess_oem/sources.json`.

### hubble_am10_20261102

Hubble Energy (2026). **AM10+ technical datasheet**. [Source](https://www.hubbleenergy.com/_files/ugd/49fdd5_be08c357eb3a4fd982d87af81a5b00a9.pdf)

**Role:** data. Page 2 Technical Data and current footnote; page 1 revision

**Used by:** `catalogues/bess_oem/sources.json`.

### hubble_am10_page_20261102

Hubble Energy (2026). **AM10+ product page**. [Source](https://www.hubbleenergy.com/am-10plus)

**Role:** data. Technical specifications and feature list; discrepancies against versioned brochure

**Used by:** `catalogues/bess_oem/sources.json`.

### hubble_am16_20261102

Hubble Energy (2026). **AM16+ technical datasheet**. [Source](https://www.hubbleenergy.com/_files/ugd/49fdd5_f0d72a5160fe4266a92b55def8477e52.pdf)

**Role:** data. Page 2 Technical Data and current footnote; page 1 revision

**Used by:** `catalogues/bess_oem/sources.json`.

### hubble_am16_page_20261102

Hubble Energy (2026). **AM16+ product page**. [Source](https://www.hubbleenergy.com/am-16plus)

**Role:** data. Technical specifications and feature list; discrepancies against versioned brochure

**Used by:** `catalogues/bess_oem/sources.json`.

### sembcorp_assets_20260630

Sembcorp Industries (2026). **Energy and Water Assets as at June 30, 2026**. [Source](https://www.sembcorp.com/media/rwwnawta/2q2026-energy-and-water-assets.pdf)

**Role:** data. Page 1 named company rows; page 2 scope footnotes

**Used by:** `catalogues/bess/sources.json`.

### sembcorp_nusantara_20250120

Sembcorp Industries (2025). **Nusantara Sembcorp Solar Energi launch**. [Source](https://www.sembcorp.com/id/en/news-and-insights/news/2025/sembcorp-and-pln-nusantara-power-launches-first-utility-scale-integrated-solar-and-energy-storage-project-in-indonesia/)

**Role:** data. First two paragraphs; JV entities and battery/solar capacities

**Used by:** `catalogues/bess/sources.json`.

### sembcorp_indonesia_portfolio_20261102

Sembcorp Industries (2026). **Indonesia utility-scale projects**. [Source](https://www.sembcorp.com/id/en/our-solutions-in-indonesia/renewable-energy/utility-scale/)

**Role:** data. Nusantara and Morowali sections; PPA and development scope

**Used by:** `catalogues/bess/sources.json`.

### pln_nusantara_flagship_20261102

PLN Nusantara Power (2026). **Green flagship projects: IKN Nusantara SPP**. [Source](https://www.plnnusantarapower.co.id/about-us/achievements/green-flagship-projects)

**Role:** data. IKN Nusantara SPP capacity, location, connection and status bullets

**Used by:** `catalogues/bess/sources.json`.

### sesna_morowali_20260406

SESNA (2026). **SESMO commences solar construction with BNI financing**. [Source](https://sesna.id/media/news/detail/sesmo-commences-262-mwp-solar-construction-with-bni-financing)

**Role:** data. Opening paragraphs, project scope, capex and syndicated lender

**Used by:** `catalogues/bess/sources.json`.

### sesna_morowali_20260211

SESNA (2026). **SESMO secures financial close**. [Source](https://sesna.id/media/news/detail/sesmo-secures-financial-close-for-262-mwp-captive-solar-pv-project-in-morowali-with-pt-smi-as-strategic-financier)

**Role:** data. Financial-close date, sponsors, PT SMI and early-2027 target

**Used by:** `catalogues/bess/sources.json`.

### china_power_wuling_20230714

China Power International Development (2026). **Wuling projects connected and put into production in first half**. [Source](https://www.chinapower.hk/sc/media/news-p230714.php)

**Role:** data. Storage paragraph naming Shujiatang and Qidong Baidishi; 100 MW / 200 MWh each

**Used by:** `catalogues/bess/sources.json`.

### sembcorp_china_storage_20261102

Sembcorp Industries (2026). **China energy storage systems**. [Source](https://www.sembcorp.com/cn/our-solutions-in-china/renewables/energy-storage-systems/)

**Role:** data. Qidong June 2023 commissioning and Nanjing 0.4 MW / 0.4 MWh immersion-cooled demonstration

**Used by:** `catalogues/bess/sources.json`.

### sembcorp_seci_award_20241218

Sembcorp Industries (2024). **First solar-energy storage hybrid project award in India**. [Source](https://links.sgx.com/1.0.0/corporate-announcements/WSZ9V90R6M77WRIL/828228_SEMBCORP%20AWARDED%20SECI%20SOLAR-BESS%20PROJECT.pdf)

**Role:** data. Page 1 paragraphs 1-2; battery scope and conditional PPA

**Used by:** `catalogues/bess/sources.json`.

### sembcorp_sjvn_award_20250529

Sembcorp Industries (2025). **Second solar-energy storage hybrid project award in India**. [Source](https://www.sembcorpindia.com/public/admin/upload/announcements_pdf/290525.pdf)

**Role:** data. Page 1 paragraphs 1-2; battery scope and conditional PPA

**Used by:** `catalogues/bess/sources.json`.

### alinta_wagerup_operating_20261027

Alinta Energy (2026). **Wagerup Battery is now operational**. [Source](https://www.alintaenergy.com.au/about-us/news-hub/wagerup-battery-now-operational)

**Role:** data. Opening paragraphs; 100 MW / 200 MWh and September commercial operation

**Used by:** `catalogues/bess/sources.json`.

### alinta_reeves_delivery_20260915

Alinta Energy (2026). **First batteries arrive at Reeves Plains**. [Source](https://www.alintaenergy.com.au/about-us/news-hub/reeves-plains-first-battery-delivery)

**Role:** data. Opening and delivery paragraphs; battery and inverter suppliers/counts

**Used by:** `catalogues/bess/sources.json`.

### alinta_reeves_phases_20261102

Alinta Energy (2026). **Reeves Plains project status**. [Source](https://www.reevesplainsenergyhub.com.au/project)

**Role:** data. Current status section: stage 1 construction, stage 2 feasibility

**Used by:** `catalogues/bess/sources.json`.

### hubble_rack_20261102

Hubble Energy (2026). **100Ah HV racks**. [Source](https://www.hubbleenergy.com/_files/ugd/49fdd5_e102201ab7a64a688e17913192f0e6b1.pdf)

**Role:** data. Primary factual evidence; source documents retained outside Git.

**Used by:** `catalogues/bess_oem/sources.json`.

### hubble_stack_20261102

Hubble Energy (2026). **HV100Ah stackable solution**. [Source](https://www.hubbleenergy.com/_files/ugd/49fdd5_a5c2c6f1e2ee4552827cc8a85d25658e.pdf)

**Role:** data. Primary factual evidence; source documents retained outside Git.

**Used by:** `catalogues/bess_oem/sources.json`.

### hubble_hv280_20261102

Hubble Energy (2026). **HV 768-215**. [Source](https://www.hubbleenergy.com/_files/ugd/49fdd5_c2d30c81cde34e46af7c354ea2887432.pdf)

**Role:** data. Primary factual evidence; source documents retained outside Git.

**Used by:** `catalogues/bess_oem/sources.json`.

### hubble_hv314_20261102

Hubble Energy (2026). **HV 768-241**. [Source](https://www.hubbleenergy.com/_files/ugd/49fdd5_a7f038e207194340806ff66eda7a9137.pdf)

**Role:** data. Primary factual evidence; source documents retained outside Git.

**Used by:** `catalogues/bess_oem/sources.json`.

### wartsila_zenobe_20261102

Wärtsilä (2026). **Zenobē reference portfolio**. [Source](https://www.wartsila.com/energy/learn-more/references/ipps/zenobe)

**Role:** data. Primary factual evidence; source documents retained outside Git.

**Used by:** `catalogues/bess/sources.json`.

### lynx_20261102

GoodWe (2023). **Lynx C Series datasheet**. [Source](https://en.goodwe.com/Ftp/EN/Downloads/Datasheet/GW_Lynx%20C%20Series_Datasheet-EN.pdf)

**Role:** data. Primary source; exact technical and rights qualifications are recorded in the corresponding catalogue source entry.

**Used by:** `catalogues/bess_oem/sources.json`.

### btc_20261102

GoodWe (2024). **BTC Series datasheet**. [Source](https://en.goodwe.com/Skippower/downloadFileF?id=683&mid=60)

**Role:** data. Primary source; exact technical and rights qualifications are recorded in the corresponding catalogue source entry.

**Used by:** `catalogues/bess_oem/sources.json`.

### etc_20261102

GoodWe (2026). **ETC Series EMEA datasheet**. [Source](https://emea.goodwe.com/Skippower/downloadFileF?id=847&mid=60)

**Role:** data. Primary source; exact technical and rights qualifications are recorded in the corresponding catalogue source entry.

**Used by:** `catalogues/bess_oem/sources.json`.

### statkraft_20261102

Statkraft (n.d.). **Grid Services and Batteries**. [Source](https://www.statkraft.ie/what-we-do/Grid-Services-and-Batteries/)

**Role:** data. Primary source; exact technical and rights qualifications are recorded in the corresponding catalogue source entry.

**Used by:** `catalogues/bess/sources.json`.

### kelwin_20261102

Statkraft (2021). **Statkraft completes second Irish energy storage project**. [Source](https://www.statkraft.com/newsroom/news-and-stories/2021/statkraft-completes-second-irish-energy-storage-project/)

**Role:** data. Primary source; exact technical and rights qualifications are recorded in the corresponding catalogue source entry.

**Used by:** `catalogues/bess/sources.json`.

### cushaling_20261102

Statkraft (2026). **Statkraft officially opens Ireland’s first 4-hour duration BESS at Cushaling**. [Source](https://www.statkraft.ie/news/2026/statkraft-officially-opens-irelands-first-4hour-duration-battery-energy-storage-system-at-cushaling-co.-offaly)

**Role:** data. Primary source; exact technical and rights qualifications are recorded in the corresponding catalogue source entry.

**Used by:** `catalogues/bess/sources.json`.

### statkraft_kilathmoy_20261102

Statkraft (2020). **Statkraft unveils Ireland’s first battery project**. [Source](https://www.statkraft.com/newsroom/news-and-stories/2020/statkraft-unveils-irelands-first-battery-project/)

**Role:** data. Primary source; exact technical and rights qualifications are recorded in the corresponding catalogue source entry.

**Used by:** `catalogues/bess/sources.json`.

### statkraft_response_20261102

Statkraft (2021). **Statkraft batteries step up to stabilise the grid when needed the most**. [Source](https://www.statkraft.co.uk/newsroom/2021/statkraft-batteries-step-up-to-stabilise-the-grid-when-needed-the-most/)

**Role:** data. Primary source; exact technical and rights qualifications are recorded in the corresponding catalogue source entry.

**Used by:** `catalogues/bess/sources.json`.

### powercomm_20261102

Powercomm Group (n.d.). **Cushaling BESS**. [Source](https://www.powercomm.ie/projects/cushaling-bess)

**Role:** data. Primary source; exact technical and rights qualifications are recorded in the corresponding catalogue source entry.

**Used by:** `catalogues/bess/sources.json`.

### kirby_20261102

Kirby Group (n.d.). **Poolbeg BESS, Ireland**. [Source](https://www.kirbygroup.com/project/poolbeg-bess-ireland/)

**Role:** data. Primary source; exact technical and rights qualifications are recorded in the corresponding catalogue source entry.

**Used by:** `catalogues/bess/sources.json`.

### solis_small_20261102_1052

Ginlong Technologies Co., Ltd. (Solis) (n.d.). **S6-EH3P(3-10)K-H datasheet**. [Source](https://www.solisinverters.com/dataFile/8e6306a8c52d48a8b03beddfcd4194b7)

**Role:** data. Primary factual evidence; Page 1 exact model list; page 2 model columns, merged cells and footnote 1, visually checked. Copyright retained. Footer and linked privacy policy inspected; no open bulk-reuse licence found. Selected factual specifications/observations only with attribution; no document, artwork, table layout or webpage redistribution.

**Used by:** `catalogues/bess_oem/sources.json`.

### solis_mid_20261102_1052

Ginlong Technologies Co., Ltd. (Solis) (n.d.). **S6-EH3P(15-20)K-H datasheet**. [Source](https://www.solisinverters.com/dataFile/2c9fafbf8b1daf73018b27b597ec026f)

**Role:** data. Primary factual evidence; Page 2, 15K and 20K columns, shared rows, switching-time footnote 1, visually checked. Copyright retained. Footer and linked privacy policy inspected; no open bulk-reuse licence found. Selected factual specifications/observations only with attribution; no document, artwork, table layout or webpage redistribution.

**Used by:** `catalogues/bess_oem/sources.json`.

### solis_20261102_1052

Ginlong Technologies Co., Ltd. (Solis) (n.d.). **S6-EH3P(29.9-50)K-H datasheet**. [Source](https://www.solisinverters.com/dataFile/46be66dec2cf403daecbb90a4174c457)

**Role:** data. Primary factual evidence; Page 2 exact model columns and merged MPPT cells; footnote 1; visually checked. Copyright retained. Footer and linked privacy policy inspected; no open bulk-reuse licence found. Selected factual specifications/observations only with attribution; no document, artwork, table layout or webpage redistribution.

**Used by:** `catalogues/bess_oem/sources.json`.

### collins_20261102_1052

Collins Building & Civil Engineering Ltd (n.d.). **Kelwin Tarbert Substation**. [Source](https://collinsbce.ie/kelwin-tarbert-substation/)

**Role:** data. Primary factual evidence; Heading and Scope of Works: 26 MW / 26.6 MWh; civil works; adjacency to 110 kV substation. Copyright retained. Footer and linked privacy policy inspected; no open bulk-reuse licence found. Selected factual specifications/observations only with attribution; no document, artwork, table layout or webpage redistribution.

**Used by:** `catalogues/bess/sources.json`.

### gsc_acq_20261102_1052

Gore Street Capital (2026). **Two Initial Acquisitions in the Republic of Ireland for Fund III: GS EU**. [Source](https://www.gorestreetcap.com/blog/gs-eu-completes-first-acquisition/)

**Role:** data. Primary factual evidence; Transaction Information: capacities, ownership, readiness, grid/land/planning and forecast quarters. Copyright retained. Footer and linked privacy policy inspected; no open bulk-reuse licence found. Selected factual specifications/observations only with attribution; no document, artwork, table layout or webpage redistribution.

**Used by:** `catalogues/bess/sources.json`.

### gsc_japan_20261102_1052

Gore Street Capital (2025). **Initial Acquisition for Japan’s First Energy Storage Fund**. [Source](https://www.gorestreetcap.com/blog/initial-acquisition-for-japans-first-energy-storage-fund/)

**Role:** data. Primary factual evidence; Opening location/capacity/subsidy paragraphs and CIO quotation on auction participation. Copyright retained. Footer and linked privacy policy inspected; no open bulk-reuse licence found. Selected factual specifications/observations only with attribution; no document, artwork, table layout or webpage redistribution.

**Used by:** `catalogues/bess/sources.json`.

### bess_solis_research_discovery_0_20261102

Department of the Environment, Climate and Communications / Houses of the Oireachtas (2025). **Total Electricity storage capacity - January 2025**. [Source](https://data.oireachtas.ie/ie/oireachtas/debateRecord/dail/2025-03-19/supportingDoc/2025-03-19_pq170-19-03-25_en.pdf)

**Role:** data. Discovery/reuse assessment, not admitted technical evidence. Both pages inspected; mixed pumped hydro excluded. No ingestion. Network sources explicitly credited.

**Used by:** `catalogues/bess/research/2026-11-02_solis_ireland_japan_backlog.json`.

### bess_solis_research_discovery_1_20261102

SMA Altenso GmbH (n.d.). **References**. [Source](https://www.sma-altenso.com/references/)

**Role:** data. Discovery/reuse assessment, not admitted technical evidence. Lumcloon representative inspected; mismatch with owner held.

**Used by:** `catalogues/bess/research/2026-11-02_solis_ireland_japan_backlog.json`.

### bess_solis_research_discovery_2_20261102

Gore Street Capital (n.d.). **Investment portfolio**. [Source](https://www.gorestreetcap.com/investment-portfolio/)

**Role:** data. Discovery/reuse assessment, not admitted technical evidence. 32 cards screened; Kasama detail accepted from acquisition release; Susono/Naie/Yufu remain discovery.

**Used by:** `catalogues/bess/research/2026-11-02_solis_ireland_japan_backlog.json`.

### bess_solis_research_discovery_6_20261102

Energy Storage Ireland (2025). **Energy Storage Ireland Pipeline Survey 2025**. [Source](https://www.energystorageireland.com/wp-content/uploads/2025/06/ESI_Pipeline_Survey_Results_2025_For_Publication.pdf)

**Role:** data. Discovery/reuse assessment, not admitted technical evidence. 12-page publication inspected; individual pipeline details removed; no inferred155 records.

**Used by:** `catalogues/bess/research/2026-11-02_solis_ireland_japan_backlog.json`.

### bess_solis_research_discovery_7_20261102

RWE Renewables Ireland (n.d.). **Lisdrumdoagh Battery Storage Facility**. [Source](https://ie.rwe.com/projects-and-locations/battery-storage-lisdrumdoagh/)

**Role:** data. Discovery/reuse assessment, not admitted technical evidence. Lisdrumdoagh and Stephenstown owner pages inspected; reproduction restriction found afterward; no records accepted.

**Used by:** `catalogues/bess/research/2026-11-02_solis_ireland_japan_backlog.json`.

### eu_20261102_1150

Ginlong Technologies (Solis) (n.d.). **S6-EH1P(3-6)K-L-EU Spanish datasheet**. [Source](https://www.ginlong.com/uploads/file/Datasheet_S6-EH1P%283-6%29K-L-EU_ESP.pdf)

**Role:** data. PDF page 2, exact model/project columns and shared rows; page 1 context; visually checked; SHA256 416a828c6fbee566ed4e4cc79257df5205bc1f2c22dc124a9230aef886170bd1

**Used by:** `catalogues/bess_oem/sources.json`.

### pro_20261102_1150

Ginlong Technologies (Solis) (n.d.). **S6-EH1P(3-6)K-L-PRO datasheet**. [Source](https://www.solisinverters.au/uploads/files/202407/Solis%20datasheet_S6-EH1P%283-6%29K-L-PRO_AUS_V1.7_202407.pdf)

**Role:** data. PDF page 2, exact model/project columns and shared rows; page 1 context; visually checked; SHA256 5b7b9bee9090b70f9d32236c1b6cc0ac36b603ccd2cbe67fbbffa81e7414088d

**Used by:** `catalogues/bess_oem/sources.json`.

### itochu_20261102_1150

IBeeT (2026). **IBeeT participation in six-site 174 MW battery consortium**. [Source](https://www.itochu-bluestorage.com/common/file/20260403.pdf)

**Role:** data. PDF page 2, exact model/project columns and shared rows; page 1 context; visually checked; SHA256 d5f57d368b2f3074d9505490edbdaec305a248ca1426a90a3217f9ab16298927

**Used by:** `catalogues/bess/sources.json`.

### shiroishi_20261102_1150

IBeeT (2026). **Miyagi Shiroishi battery storage with Tokyu Land**. [Source](https://www.itochu-bluestorage.com/common/file/20260828.pdf)

**Role:** data. PDF page 2, exact model/project columns and shared rows; page 1 context; visually checked; SHA256 8b8f7aa736ff9518d029310c68123f764534193df414dbc48c2739dfa7c7e8eb

**Used by:** `catalogues/bess/sources.json`.

### chikuzen_20261102_1150

ITOCHU Corporation (2026). **Joint battery storage business in Chikuzen**. [Source](https://www.itochu-bluestorage.com/common/file/20260601.pdf)

**Role:** data. PDF page 2, exact model/project columns and shared rows; page 1 context; visually checked; SHA256 310d6edbb6d826794f27ce10a1aa74ee0ac0d48ed580d0df09ac334d13122d0e

**Used by:** `catalogues/bess/sources.json`.

### bess_blueterms_20261102

ITOCHU (n.d.). **Bluestorage privacy policy**. [Source](https://www.itochu-bluestorage.com/policy/)

**Role:** data. Access/discovery assessment only; no canonical technical data derived.

**Used by:** `catalogues/bess/research/2026-11-02_japan_solis_lv_report.md`.

### bess_japandiscovery_20261102

BESS Net (n.d.). **Japanese battery project directory (discovery only)**. [Source](https://bess-net.jp/projects)

**Role:** data. Access/discovery assessment only; no canonical technical data derived.

**Used by:** `catalogues/bess/research/2026-11-02_japan_solis_lv_report.md`.

### fwindex_20261102_1300

Freedom Won (n.d.). **Freedom Won downloads: legacy product index**. [Source](https://www.freedomwon.co.za/fw_downloads/)

**Role:** data. End-of-Life heading and LiTE Home/Business/Commercial and LiTE 2 Commercial HV/HV+ entries; primary search-service text; source-byte checksum unavailable

**Used by:** `catalogues/bess_oem/sources.json`.

### home_20261102_1300

Freedom Won (2024). **LiTE Home 52V Model A range overview**. [Source](https://www.freedomwon.co.za/wp-content/uploads/LiTE-HOME-52V-A-Range-Overview-Spec-Sheet.pdf)

**Role:** data. Page 1: named model columns, specification rows, notes 1–5; primary search-service text; source-byte checksum unavailable

**Used by:** `catalogues/bess_oem/sources.json`.

### business_20261102_1300

Freedom Won (2024). **LiTE Business 52V range overview**. [Source](https://www.freedomwon.co.za/wp-content/uploads/LiTE-BUSINESS-52V-Range-Overview-Spec-Sheet-3.pdf)

**Role:** data. Page 1: named model columns, specification rows, notes 1–5; primary search-service text; source-byte checksum unavailable

**Used by:** `catalogues/bess_oem/sources.json`.

### lv_20261102_1300

Freedom Won (2025). **LiTE Commercial 52V range overview**. [Source](https://www.freedomwon.co.za/wp-content/uploads/LiTE-COMMERCIAL-52V-Range-Overview-Spec-Sheet-3.pdf)

**Role:** data. Page 1: named model columns, specification rows and notes; primary search-service text; source-byte checksum unavailable

**Used by:** `catalogues/bess_oem/sources.json`.

### encore3_20261102_1300

Freedom Won (2024). **Encore 3K specification sheet**. [Source](https://www.freedomwon.co.za/wp-content/uploads/Spec-Sheet-Encore-Single-Phase-3K.pdf)

**Role:** data. Pages 1–2, single-model electrical/general tables and notes 1–5; primary search-service text; source-byte checksum unavailable

**Used by:** `catalogues/bess_oem/sources.json`.

### encore5_20261102_1300

Freedom Won (2024). **Encore 5K specification sheet**. [Source](https://www.freedomwon.co.za/wp-content/uploads/Spec-Sheet-Encore-Single-Phase-5K.pdf)

**Role:** data. Pages 1–2, single-model electrical/general tables and notes 1–5; primary search-service text; source-byte checksum unavailable

**Used by:** `catalogues/bess_oem/sources.json`.

### encore8_20261102_1300

Freedom Won (2024). **Encore 8K specification sheet**. [Source](https://www.freedomwon.co.za/wp-content/uploads/Spec-Sheet-Encore-Single-Phase-8K.pdf)

**Role:** data. Pages 1–2, single-model electrical/general tables and notes 1–5; primary search-service text; source-byte checksum unavailable

**Used by:** `catalogues/bess_oem/sources.json`.

### encore10_20261102_1300

Freedom Won (2024). **Encore 10K specification sheet**. [Source](https://www.freedomwon.co.za/wp-content/uploads/Spec-Sheet-Encore-Single-Phase-10K.pdf)

**Role:** data. Pages 1–2, single-model electrical/general tables and notes 1–5; primary search-service text; source-byte checksum unavailable

**Used by:** `catalogues/bess_oem/sources.json`.

### renewvia_20261102_1300

Renewvia Energy Corporation (n.d.). **Operating mini-grid portfolio**. [Source](https://www.renewvia.com/minigrid-sites)

**Role:** data. Named site headings and site paragraphs: Oloibiri, Akipelai, Ndeda, Kalobeyei Town and Settlement; SHA256 9ae3edc704dcba735b24b2d2d9082bb7d1149bcca8322c6fe192fb04a6c8b4f8

**Used by:** `catalogues/bess/sources.json`.

### allon_20261102_1300

Renewvia Energy Corporation (2020). **All On commitment and operating Akipelai/Oloibiri mini-grids**. [Source](https://www.renewvia.com/post/renewvia-receives-1-2-million-commitment-from-all-on-to-electrify-communities-in-the-niger-delta)

**Role:** data. Release body dated June 2 2020; CMS date April 22 2021; first two systems and lithium-ion paragraph; SHA256 2bd629d30c2e0ee134aaab984de6ec3d4fdaf405ef1903f73d4c50a6847325c8

**Used by:** `catalogues/bess/sources.json`.

### reads_20261102_1300

UNITAR (2023). **A Roadmap for Energy Access in Displacement Settings: Kenya**. [Source](https://www.humanitarianenergy.org/assets/resources/Compressed_READS_Kenya.pdf)

**Role:** data. Printed pages 89–91: Renewvia Kalobeyei project deep-dive; publication/copyright page 2; SHA256 831ccba3bb96d8c11fe13a79bb9932259a9974ab9ac90c64551dbdd2744db4c9

**Used by:** `catalogues/bess/sources.json`.

### africa_20261102_1300

Renewvia Solar Africa (n.d.). **Renewvia Solar Africa: technical excellence**. [Source](https://www.renewviaenergyafrica.com/)

**Role:** data. Technical Excellence paragraph: Kalobeyei Settlement 541 kWp and 1.1 MWh; SHA256 ffd0070f63deb3adf37d9e0eac849ac111fbc4d4d88810c88b9c2b637b3ab75e

**Used by:** `catalogues/bess/sources.json`.

### home2_20261102_1500

Freedom Won (2026). **LiTE 2 Home 52V Model A range overview**. [Source](https://www.freedomwon.co.za/wp-content/uploads/LiTE-2-HOME-52V-A-Range-Overview-Sheet-1.pdf)

**Role:** data. Page 1, four named columns; energy/current/power/voltage/dimensions rows and notes 1–5; primary search-service text; original-byte checksum unavailable

**Used by:** `catalogues/bess_oem/sources.json`.

### business2hv_20261102_1500

Freedom Won (2026). **LiTE 2 Business HV range overview**. [Source](https://www.freedomwon.co.za/wp-content/uploads/LiTE-2-BUSINESS-HV-Range-Overview-Sheet-1.pdf)

**Role:** data. Page 1, Business 40/32 HV and 60/48 HV columns, specification rows and notes 1–6; primary search-service text; original-byte checksum unavailable

**Used by:** `catalogues/bess_oem/sources.json`.

### homehv_20261102_1500

Freedom Won (2025). **LiTE Home HV range overview**. [Source](https://www.freedomwon.co.za/wp-content/uploads/LiTE-HOME-HV-Range-Overview-Spec-Sheet-3-1.pdf)

**Role:** data. Page 1, Home 15/12 HV, 20/16 HV and 30/24 HV columns; specification rows and notes 1–6; primary search-service text; original-byte checksum unavailable

**Used by:** `catalogues/bess_oem/sources.json`.

### etower2_20261102_1500

Freedom Won (2026). **eTower 2 configuration overview**. [Source](https://www.freedomwon.co.za/wp-content/uploads/Freedom-Won-eTower-2-Overview-Sheet-2.pdf)

**Role:** data. Pages 1–2, 1 x eTower 2 column and shared notes; pages 3–4 are incomplete duplicate templates and not used; primary search-service text; original-byte checksum unavailable

**Used by:** `catalogues/bess_oem/sources.json`.

### 1463636_20261102_1500

Nigerian Electricity Management Services Agency (applicant declaration) (n.d.). **NEMSA inspection application: Fadama Bauna North (entry 1463636)**. [Source](https://nemsa.gov.ng/admin-request-for-inspection-rea-solar-mini-grid/entry/1463636/)

**Role:** data. Community/site, total storage, storage technology, owner and date rows; battery manufacturer/model and Total C10 capacity tables; SHA256 68c5df49748e3f13302539d0631df5bff0d13a79f3e7a3cf2b8072b232c8e1dd

**Used by:** `catalogues/bess/sources.json`.

### 1479030_20261102_1500

Nigerian Electricity Management Services Agency (applicant declaration) (n.d.). **NEMSA inspection application: Kalong (entry 1479030)**. [Source](https://nemsa.gov.ng/admin-request-for-inspection-rea-solar-mini-grid/entry/1479030/)

**Role:** data. Community/site, total storage, storage technology, owner and date rows; battery manufacturer/model and Total C10 capacity tables; SHA256 1492728556db25369684e86d2b206fbf614343d31da3acdb25863c16704002d2

**Used by:** `catalogues/bess/sources.json`.

### 1511981_20261102_1500

Nigerian Electricity Management Services Agency (applicant declaration) (n.d.). **NEMSA inspection application: Ibaragun (entry 1511981)**. [Source](https://nemsa.gov.ng/admin-request-for-inspection-rea-solar-mini-grid/entry/1511981/)

**Role:** data. Community/site, total storage, storage technology, owner and date rows; battery manufacturer/model and Total C10 capacity tables; SHA256 be27244a75faa6458303942b5566da20d45df6c71dd687f750c9ae398565924f

**Used by:** `catalogues/bess/sources.json`.

### 1446317_20261102_1500

Nigerian Electricity Management Services Agency (applicant declaration) (n.d.). **NEMSA inspection application: Mebiowa Okposi (entry 1446317)**. [Source](https://nemsa.gov.ng/admin-request-for-inspection-rea-solar-mini-grid/entry/1446317/)

**Role:** data. Community/site, total storage, storage technology, owner and date rows; battery manufacturer/model and Total C10 capacity tables; SHA256 f38b1e7b8bdee994f477bb5f59a58ad01cd75a991e7f61c8e1c24ff089b34606

**Used by:** `catalogues/bess/sources.json`.

### 1442720_20261102_1500

Nigerian Electricity Management Services Agency (applicant declaration) (n.d.). **NEMSA inspection application: Mebiowa Okposi (earlier entry 1442720)**. [Source](https://nemsa.gov.ng/admin-request-for-inspection-rea-solar-mini-grid/entry/1442720/)

**Role:** data. Community/coordinates/owner identifying same site; malformed total storage field; SHA256 c5bf7ec4375e4ab6587e5aa6d68f3c006d65a5d3b90c189a9ff200aa4eda6ea7

**Used by:** `catalogues/bess/sources.json`.

### 1462965_20261102_1500

Nigerian Electricity Management Services Agency (applicant declaration) (n.d.). **NEMSA inspection application: Eriwe (entry 1462965)**. [Source](https://nemsa.gov.ng/admin-request-for-inspection-rea-solar-mini-grid/entry/1462965/)

**Role:** data. Community/site, total storage, storage technology, owner and date rows; battery manufacturer/model and Total C10 capacity tables; SHA256 73f8e7b7e3480c1bd418bb7197bceea0d460f61482ba7e917798887b57d3f5c9

**Used by:** `catalogues/bess/sources.json`.

### 1466822_20261102_1500

Nigerian Electricity Management Services Agency (applicant declaration) (n.d.). **NEMSA inspection application: Fagbo (entry 1466822)**. [Source](https://nemsa.gov.ng/admin-request-for-inspection-rea-solar-mini-grid/entry/1466822/)

**Role:** data. Community/site, total storage, storage technology, owner and date rows; battery manufacturer/model and Total C10 capacity tables; SHA256 11c2c6e015942d746712beafc12e4736b24f6d142ae23a42cd4df212b2c78c5a

**Used by:** `catalogues/bess/sources.json`.

### 1462943_20261102_1500

Nigerian Electricity Management Services Agency (applicant declaration) (n.d.). **NEMSA inspection application: Gurin (entry 1462943)**. [Source](https://nemsa.gov.ng/admin-request-for-inspection-rea-solar-mini-grid/entry/1462943/)

**Role:** data. Community/site, total storage, storage technology, owner and date rows; battery manufacturer/model and Total C10 capacity tables; SHA256 3632cb0059aabf43baff8268cdb3551fbda8d0c5d4c830a857f690d7d1b694da

**Used by:** `catalogues/bess/sources.json`.

### 1445190_20261102_1500

Nigerian Electricity Management Services Agency (applicant declaration) (n.d.). **NEMSA inspection application: Emereoke (entry 1445190)**. [Source](https://nemsa.gov.ng/admin-request-for-inspection-rea-solar-mini-grid/entry/1445190/)

**Role:** data. Community/site, total storage, storage technology, owner and date rows; battery manufacturer/model and Total C10 capacity tables; SHA256 47fd61ce839d0f4a9684e2ad5ff11e24029ed01fd0d24d59889eca71c8da5ad4

**Used by:** `catalogues/bess/sources.json`.

### 1542697_20261102_1500

Nigerian Electricity Management Services Agency (applicant declaration) (n.d.). **NEMSA inspection application: Gamakai (entry 1542697)**. [Source](https://nemsa.gov.ng/admin-request-for-inspection-rea-solar-mini-grid/entry/1542697/)

**Role:** data. Community/site, total storage, storage technology, owner and date rows; battery manufacturer/model and Total C10 capacity tables; SHA256 b77da98e846db0068b88a6fe741b09d4bce079ed10f4a206a37165210b50df33

**Used by:** `catalogues/bess/sources.json`.

### index_20261102_1600

Victron Energy B.V. (n.d.). **MultiPlus new-style product index**. [Source](https://www.victronenergy.com/inverters-chargers/multi-500-va)

**Role:** data. Exact named model columns, 230 V and 120 V variants; introduction distinguishes earlier Compact range; SHA256 5f031c6fc2eef43e4f8ee49868988796b15ec29e17173c54545b198d393aaefc

**Used by:** `catalogues/bess_oem/sources.json`.

### multi_20261102_1600

Victron Energy B.V. (n.d.). **MultiPlus inverter/charger 500 VA–2000 VA, 12/24/48 V–230 V**. [Source](https://www.victronenergy.com/upload/documents/Datasheet-MultiPlus-500VA-2000VA-EN.pdf)

**Role:** data. PDF page 2: five power columns, each containing three explicitly named DC-voltage models; row labels and footnotes 1–7. Page 1 product scope. Visually checked raster PDF.; SHA256 698a88ac643d2989d48c71cac6058c35f64c703f21fe1d58f4f67b7f379976e3

**Used by:** `catalogues/bess_oem/sources.json`.

### multi120_20261102_1600

Victron Energy B.V. (n.d.). **MultiPlus 12 V 500–1200 VA 120 Vac manual**. [Source](https://www.victronenergy.com/media/pg/MultiPlus_12V_500-1200VA_120Vac/en/technical-data.html)

**Role:** data. Section 7.1 three exact model columns, rating rows/footnotes; section 7.2 VE.Bus port; publication date blank; SHA256 1b770d098a664aa04c69644fa1780935091e172dc4da07e830ced8d8dfeedee7

**Used by:** `catalogues/bess_oem/sources.json`.

### multi2000_20261102_1600

Victron Energy B.V. (n.d.). **MultiPlus 2 kVA 230 V manual**. [Source](https://www.victronenergy.com/media/pg/MultiPlus_2kVA_230V/en/technical-data-2kva.html)

**Role:** data. Section 8, three model columns and footnotes; idle/search consumption, enclosure and automotive-standard differences retained; SHA256 d07d134b63367c7fb7c775e22533dd904cf0f59d202c8c0a729a3585406dedc4

**Used by:** `catalogues/bess_oem/sources.json`.

### uyo_20261102_1600

Nigerian Electricity Management Services Agency (applicant declaration) (n.d.). **NEMSA inspection application: University of Uyo, entry 1542032**. [Source](https://nemsa.gov.ng/admin-request-for-inspection-rea-solar-mini-grid/entry/1542032/)

**Role:** data. Site identity, owner, storage/PV summary and battery manufacturer/model/voltage tables; application 2025-11-14; SHA256 11c9a879e42bbf15e29bc16665756fddd121914259186cc8b789930d911320f9

**Used by:** `catalogues/bess/sources.json`.

### toto_20261102_1600

Nigerian Electricity Management Services Agency (applicant declaration) (n.d.). **NEMSA inspection application: Toto, entry 1467329**. [Source](https://nemsa.gov.ng/admin-request-for-inspection-rea-solar-mini-grid/entry/1467329/)

**Role:** data. Site identity, owner, storage/PV summary and five battery-bank rows; application 2023-03-27; SHA256 809176afc9e192383b870d4f6f88d31530ebde3b9ed83eec534e6f6d37e3842e

**Used by:** `catalogues/bess/sources.json`.

### totoowner_20261102_1600

PowerGen Renewable Energy (2025). **Toto interconnected solar hybrid mini-grid commissioned**. [Source](https://powergen-renewable-energy.com/press-release-nigerias-first-interconnected-hybrid-solar-mini-grid-plant-commissioned-in-toto-community-nasarawa-state/)

**Role:** data. Title and opening three paragraphs; website labels post July 12 2025, not accepted as exact commissioning date; primary indexed text; original-byte checksum unavailable

**Used by:** `catalogues/bess/sources.json`.

### 1463636_20261102_1600

Nigerian Electricity Management Services Agency (applicant declaration) (n.d.). **NEMSA battery electrical table: Fadama Bauna North**. [Source](https://nemsa.gov.ng/admin-request-for-inspection-rea-solar-mini-grid/entry/1463636/)

**Role:** data. Battery table: cell voltage, battery voltage, charge voltage, Series | Parallel; application identity unchanged; SHA256 d24b5f57f25e8687662a9226563ac0b2973baff6218ed1673d62da5d20f3852d

**Used by:** `catalogues/bess/sources.json`.

### 1462965_20261102_1600

Nigerian Electricity Management Services Agency (applicant declaration) (n.d.). **NEMSA battery electrical table: Eriwe**. [Source](https://nemsa.gov.ng/admin-request-for-inspection-rea-solar-mini-grid/entry/1462965/)

**Role:** data. Battery table: cell voltage, battery voltage, charge voltage, Series | Parallel; application identity unchanged; SHA256 3c27dcecc4d8fdd610d27ec08c6c91b8b1bb54fa233e373f2572d873efa74c45

**Used by:** `catalogues/bess/sources.json`.

### 1511981_20261102_1600

Nigerian Electricity Management Services Agency (applicant declaration) (n.d.). **NEMSA battery electrical table: Ibaragun**. [Source](https://nemsa.gov.ng/admin-request-for-inspection-rea-solar-mini-grid/entry/1511981/)

**Role:** data. Battery table: cell voltage, battery voltage, charge voltage, Series | Parallel; application identity unchanged; SHA256 e3ba93550bcde5d32b24fc0b66dd0a4b2e3a93432170de991001c1d0ecf10d2e

**Used by:** `catalogues/bess/sources.json`.

### cei2025_20261102_1600

CEI Africa (2025). **Renewvia Kakuma/Kalobeyei expansion financing: cei2025**. [Source](https://cei-africa.com/news/cei-africa-provides-usd-4-475-million-to-renewvia-to-expand-solar-power-for-refugees-and-host-communities-in-kakuma-and-kalobeyei/)

**Role:** data. Opening financing and existing-plant/expansion paragraphs; SHA256 cc055d2607429c796106dbf5b12c89658490abfddf706ca393d2e18b393e33e9

**Used by:** `catalogues/bess/sources.json`.

### cei2023_20261102_1600

Renewvia Energy (CEI Africa announcement) (2023). **Renewvia Kakuma/Kalobeyei expansion financing: cei2023**. [Source](https://www.renewvia.com/post/cei-africa-awards-a-total-of-usd-7-3m-in-rbf-grants-to-3-kenyan-gmg-developers)

**Role:** data. Renewvia grant and planned 2.4 MW / 6 MWh paragraphs; release date May 31, site posting July 12; SHA256 14c53a8b2edaabcfacf56871fc38f858f0224d7a6fc676c2d84f94c5f56f4b43

**Used by:** `catalogues/bess/sources.json`.

### odre_glossary_20261102

RTE / ODRÉ (2026). **National register field glossary**. [Source](https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/registre-national-installation-production-stockage-electricite-agrege/attachments/11_glossaire_gpc_registre_des_installations_vrte_docx)

**Role:** data. Field definitions: EIC, location, commissioning, power, stored and annual energy; aggregate policy; SHA256 e73caf2ea0be886efb7dda2734b0e4ce4112c1577b9c0558ccec9d7a967d9f0e

**Used by:** `catalogues/bess/sources.json`.

### odre_battery_ge1mw_1_20260831

RTE, Enedis, EDF SEI, ELD (2026). **National electricity installation register: odre_battery_ge1mw_1**. [Source](https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/registre-national-installation-production-stockage-electricite-agrege/records?where=filiere%3D%27Stockage+non+hydraulique%27+and+technologie%3D%27Batterie%27+and+typestockage%3D%27BATTE%27+and+puismaxinstallee%3E%3D1000&order_by=codeeicresourceobject&limit=100&offset=100)

**Role:** data. API results; exact row EIC identified in each record external_ids_json and review ledger; SHA256 2934179cadc60f6c7ca23d57479ff72aac36e720aa86ed9e9d8596cb221caa40

**Used by:** `catalogues/bess/sources.json`.

### odre_battery_ge1mw_0_20260831

RTE, Enedis, EDF SEI, ELD (2026). **National electricity installation register: odre_battery_ge1mw_0**. [Source](https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/registre-national-installation-production-stockage-electricite-agrege/records?where=filiere%3D%27Stockage+non+hydraulique%27+and+technologie%3D%27Batterie%27+and+typestockage%3D%27BATTE%27+and+puismaxinstallee%3E%3D1000&order_by=codeeicresourceobject&limit=100&offset=0)

**Role:** data. API results; exact row EIC identified in each record external_ids_json and review ledger; SHA256 daad0c57f835e1a36d22394ae113589b4378cf8a5e6dc31e4440f71c481519fb

**Used by:** `catalogues/bess/sources.json`.

### odre_rte_20260831

RTE, Enedis, EDF SEI, ELD (2026). **National electricity installation register: odre_rte**. [Source](https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/registre-national-installation-production-stockage-electricite-agrege/records?where=filiere%3D%27Stockage+non+hydraulique%27+and+technologie%3D%27Batterie%27+and+typestockage%3D%27BATTE%27+and+gestionnaire%3D%27RTE%27&order_by=codeeicresourceobject&limit=100)

**Role:** data. API results; exact row EIC identified in each record external_ids_json and review ledger; SHA256 01f61b90ae310ee022acc9d973fa07c261c9d6a37fb0e607a1fabbe21a3ca15f

**Used by:** `catalogues/bess/sources.json`.

### gopa_lithops_20261102

GOPA (2026). **Lithops battery: owner engineer technical requirements**. [Source](https://www.gopa.eu/en/projects/flagship/namibia-lithops-battery-storage/)

**Role:** data. Challenge, project facts and impact-in-numbers sections; SHA256 6355711f4f5b2ee8bc38c50a2dfe4c2d76458f3c7c9722c320829bfeebd58925

**Used by:** `catalogues/bess/sources.json`.

### rolls_6_cs_21p_20261102

Rolls Battery (2024). **6 CS 21P flooded deep-cycle battery specifications**. [Source](https://rollsbattery.com/battery/6-cs-21p/)

**Role:** data. Exact model heading; Series/Volts/Cells, Charge | Discharge, Hour Rate, Specifications, materials and printed revision; SHA256 6c55d6514e1a1d4cffa9c1387658ef1bea97dd2998665d9650bb09895599bdb1

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_s6_l16_20261102

Rolls Battery (2024). **S6 L16 flooded deep-cycle battery specifications**. [Source](https://rollsbattery.com/battery/s6-l16/)

**Role:** data. Exact model heading; Series/Volts/Cells, Charge | Discharge, Hour Rate, Specifications, materials and printed revision; SHA256 cdcbe9a8d9029c32ab6a6d5761897c34bc42d957e326c68788559f6418a1f525

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_6_cs_17p_20261102

Rolls Battery (2024). **6 CS 17P flooded deep-cycle battery specifications**. [Source](https://rollsbattery.com/battery/6-cs-17p/)

**Role:** data. Exact model heading; Series/Volts/Cells, Charge | Discharge, Hour Rate, Specifications, materials and printed revision; SHA256 2d02fcc3e8c1b134c0bb69d02e7bed657a08935231cd0d4f02bbd9d7578ca56b

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_s6_l16_hc_20261102

Rolls Battery (2024). **S6 L16-HC flooded deep-cycle battery specifications**. [Source](https://rollsbattery.com/battery/s6-l16-hc/)

**Role:** data. Exact model heading; Series/Volts/Cells, Charge | Discharge, Hour Rate, Specifications, materials and printed revision; SHA256 3ae92253087af17ce8b6184e34e827f53f42052eb7d5b19df796fd6746865f65

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_s6_gc2_20261102

Rolls Battery (2024). **S6 GC2 flooded deep-cycle battery specifications**. [Source](https://rollsbattery.com/battery/s6-gc2/)

**Role:** data. Exact model heading; Series/Volts/Cells, Charge | Discharge, Hour Rate, Specifications, materials and printed revision; SHA256 4b82b2d4f523ed6bb83b96c35645e6fca4000633dd338be519c4a3e694c2f2c9

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_catalogue_20261102

Rolls Battery (2026). **Rolls Battery catalogue renewable-energy model classifications**. [Source](https://rollsbattery.com/catalog/)

**Role:** data. data-battery_slug/model/applications attributes for 16 selected exact models; no sizing-calculator combinations; SHA256 90d62332a150a399d7ad9d84b026dcb317e4c144f3d98612811287256132a499

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_s12_185_20261102

Rolls Battery (2024). **S12 185 flooded deep-cycle battery specifications**. [Source](https://rollsbattery.com/battery/s12-185/)

**Role:** data. Exact model heading; Series/Volts/Cells, Charge | Discharge, Hour Rate, Specifications, materials and printed revision; SHA256 eb3138a0c41247b64228ee6534b084175b131c40f1a1d690df2b76c28a26b912

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_s6_305_20261102

Rolls Battery (2024). **S6-305 flooded deep-cycle battery specifications**. [Source](https://rollsbattery.com/battery/s6-305/)

**Role:** data. Exact model heading; Series/Volts/Cells, Charge | Discharge, Hour Rate, Specifications, materials and printed revision; SHA256 a9f7ca525a3ce704c21efe8bfe4a3924beb5cfda92be5d656f70c3922182095b

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_6_cs_25p_20261102

Rolls Battery (2024). **6 CS 25P flooded deep-cycle battery specifications**. [Source](https://rollsbattery.com/battery/6-cs-25p/)

**Role:** data. Exact model heading; Series/Volts/Cells, Charge | Discharge, Hour Rate, Specifications, materials and printed revision; SHA256 32fbaeebcf860927f0683d4471e530160e59e5ea05e330cb4395b27f6e79c82b

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_s6_l16_ex_20261102

Rolls Battery (2024). **S6 L16-EX flooded deep-cycle battery specifications**. [Source](https://rollsbattery.com/battery/s6-l16-ex/)

**Role:** data. Exact model heading; Series/Volts/Cells, Charge | Discharge, Hour Rate, Specifications, materials and printed revision; SHA256 b4f4be2bc2be1c769f84acc755e757e69727d9cc200d0459454e896efd234362

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_s6_145_20261102

Rolls Battery (2019). **S6 145 flooded deep-cycle battery specifications**. [Source](https://rollsbattery.com/battery/s6-145/)

**Role:** data. Exact model heading; Series/Volts/Cells, Charge | Discharge, Hour Rate, Specifications, materials and printed revision; SHA256 4efc59fed3755933eb4f04db0aadfcf897c6f230c04ed712a8548a04921002a9

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_s12_27_20261102

Rolls Battery (2024). **S12 27 flooded deep-cycle battery specifications**. [Source](https://rollsbattery.com/battery/s12-27/)

**Role:** data. Exact model heading; Series/Volts/Cells, Charge | Discharge, Hour Rate, Specifications, materials and printed revision; SHA256 c361222ef25f50382dd5f7cdc8849be7cd9854c49b6845f4addab7c2ee05f24e

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_s12_24_20261102

Rolls Battery (2024). **S12 24 flooded deep-cycle battery specifications**. [Source](https://rollsbattery.com/battery/s12-24/)

**Role:** data. Exact model heading; Series/Volts/Cells, Charge | Discharge, Hour Rate, Specifications, materials and printed revision; SHA256 e27a448dde7d4e2c377dd68fc5194ced666297ee40653d0dc9634ab00e5e6859

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_12_cs_11p_20261102

Rolls Battery (2024). **12 CS 11P flooded deep-cycle battery specifications**. [Source](https://rollsbattery.com/battery/12-cs-11p/)

**Role:** data. Exact model heading; Series/Volts/Cells, Charge | Discharge, Hour Rate, Specifications, materials and printed revision; SHA256 e0c0d19956d8d4b3565bbb987a1b794b453162f6e8ea155c3b2e52c9beb324de

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_s12_31_20261102

Rolls Battery (2024). **S12 31 flooded deep-cycle battery specifications**. [Source](https://rollsbattery.com/battery/s12-31/)

**Role:** data. Exact model heading; Series/Volts/Cells, Charge | Discharge, Hour Rate, Specifications, materials and printed revision; SHA256 3f14d9b3bd6473ff81868bff6981bcdf69bfc5863f9a214e330bc2ca5fbad955

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_4_cs_17p_20261102

Rolls Battery (2024). **4 CS 17P flooded deep-cycle battery specifications**. [Source](https://rollsbattery.com/battery/4-cs-17p/)

**Role:** data. Exact model heading; Series/Volts/Cells, Charge | Discharge, Hour Rate, Specifications, materials and printed revision; SHA256 9c6c6f50ac06036fff22cb8ed07f7fa5f1edfbd69c4d573f3f41773085675db3

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_s6_gc2_hc_20261102

Rolls Battery (2024). **S6 GC2-HC flooded deep-cycle battery specifications**. [Source](https://rollsbattery.com/battery/s6-gc2-hc/)

**Role:** data. Exact model heading; Series/Volts/Cells, Charge | Discharge, Hour Rate, Specifications, materials and printed revision; SHA256 2936664db113e9e90e2f0920c8535a00f892262a2fd048e15b74a8b14745dcb7

**Used by:** `catalogues/bess_oem/sources.json`.

### odre_eic_renaming_202601

RTE / ODRÉ (2026). **Modification de 79 codes EIC en W dans le registre national des installations de production et de stockage**. [Source](https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/registre-national-installation-production-stockage-electricite-agrege/attachments/note_d_information_concernant_les_modifications_de_79_codes_eic_v2_pdf)

**Role:** data. Page 1: BARBAS01, previous EIC 17W000001600745Y, 2026 EIC 17W000001637626Q; SHA256 9010abd65fdad62f9d9607ab47a8a17d231c7ef48f97f406b4e8aea15655ab99

**Used by:** `catalogues/bess/sources.json`.

### odre_partition_2_20261102

RTE, Enedis, EDF SEI, ELD (2026). **National battery installation register, offset 200**. [Source](https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/registre-national-installation-production-stockage-electricite-agrege/records?where=filiere%3D%27Stockage+non+hydraulique%27+and+technologie%3D%27Batterie%27+and+typestockage%3D%27BATTE%27+and+puismaxinstallee%3E%3D1000&order_by=codeeicresourceobject&limit=100&offset=200)

**Role:** data. API results; exact EIC and source row in review ledger; SHA256 853f52eda60b0cf0120acfcdb54d5cefd238c964b6850002db98f5ea603c00a8

**Used by:** `catalogues/bess/sources.json`.

### odre_partition_3_20261102

RTE, Enedis, EDF SEI, ELD (2026). **National battery installation register, offset 300**. [Source](https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/registre-national-installation-production-stockage-electricite-agrege/records?where=filiere%3D%27Stockage+non+hydraulique%27+and+technologie%3D%27Batterie%27+and+typestockage%3D%27BATTE%27+and+puismaxinstallee%3E%3D1000&order_by=codeeicresourceobject&limit=100&offset=300)

**Role:** data. API results; exact EIC and source row in review ledger; SHA256 2dbfc34884bbbe0f85aa7158fd3e5772eee9873f8ba43b00a7e9f8e967154e93

**Used by:** `catalogues/bess/sources.json`.

### rolls_index_partition2_20261102

Rolls Battery (2026). **Rolls renewable-energy model index**. [Source](https://rollsbattery.com/catalog/)

**Role:** data. Exact selected model data-battery_applications attributes; SHA256 d15eedd93a55f79534340b2e012030273bd9167ca03abd74069b4e7dfff02392

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_8_cs_17p_20261102

Rolls Battery (2024). **8 CS 17P flooded battery specifications**. [Source](https://rollsbattery.com/battery/8-cs-17p/)

**Role:** data. Exact model heading; charge/discharge, hour-rate and specifications tables; SHA256 c40f38a5004984a502118ed3f10e60d1abbd69a3f3e3e668aee6e52098f5308f

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_8_cs_25p_20261102

Rolls Battery (2024). **8 CS 25P flooded battery specifications**. [Source](https://rollsbattery.com/battery/8-cs-25p/)

**Role:** data. Exact model heading; charge/discharge, hour-rate and specifications tables; SHA256 f01d9deda9977109a3e016a838b960377a5284bc6813f3abb088627cb8f7c7f4

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_6_cs_27p_20261102

Rolls Battery (2024). **6 CS 27P flooded battery specifications**. [Source](https://rollsbattery.com/battery/6-cs-27p/)

**Role:** data. Exact model heading; charge/discharge, hour-rate and specifications tables; SHA256 2660558fadd757f9b4e7e6b6f7a030d8f289713381012e365e33fc600b8b5ac6

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_8_cs_27p_20261102

Rolls Battery (2024). **8 CS 27P flooded battery specifications**. [Source](https://rollsbattery.com/battery/8-cs-27p/)

**Role:** data. Exact model heading; charge/discharge, hour-rate and specifications tables; SHA256 1d46faa155a8971ed0ec359265d1f1a6651f8660af31e0a6141c545552862299

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_s2_l16_ex_20261102

Rolls Battery (2024). **S2 L16-EX flooded battery specifications**. [Source](https://rollsbattery.com/battery/s2-l16-ex/)

**Role:** data. Exact model heading; charge/discharge, hour-rate and specifications tables; SHA256 2640957a1011d68b272c9ae82e8c9e5880c47c94c2201972cde2a7babc327a4a

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_4_ks_21p_20261102

Rolls Battery (2024). **4 KS 21P flooded battery specifications**. [Source](https://rollsbattery.com/battery/4-ks-21p/)

**Role:** data. Exact model heading; charge/discharge, hour-rate and specifications tables; SHA256 c054e035681aca3453e972e8df429d19f46824c1803479ffe96bebb3bab540f6

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_s2_l16_20261102

Rolls Battery (2024). **S2 L16 flooded battery specifications**. [Source](https://rollsbattery.com/battery/s2-l16/)

**Role:** data. Exact model heading; charge/discharge, hour-rate and specifications tables; SHA256 29c2fd0b65c307fb7e69c4d86c4cc8053b446472de27e6bccfa4e2cca5430a3d

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_s2_l16_hc_20261102

Rolls Battery (2024). **S2 L16-HC flooded battery specifications**. [Source](https://rollsbattery.com/battery/s2-l16-hc/)

**Role:** data. Exact model heading; charge/discharge, hour-rate and specifications tables; SHA256 f76f78848eb9d6b6dfb21d751e7169ca6eb11402eeb264bfe36181915ec96ab8

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_4_ks_25p_20261102

Rolls Battery (2024). **4 KS 25P flooded battery specifications**. [Source](https://rollsbattery.com/battery/4-ks-25p/)

**Role:** data. Exact model heading; charge/discharge, hour-rate and specifications tables; SHA256 4ec1855cee0cbe819bf761bf9edfed98f6db38b2b9e0346d287ae2032a9ffabb

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_s2_l16_sc_20261102

Rolls Battery (2024). **S2 L16-SC flooded battery specifications**. [Source](https://rollsbattery.com/battery/s2-l16-sc/)

**Role:** data. Exact model heading; charge/discharge, hour-rate and specifications tables; SHA256 d5df89c0e2914b66527e5dd7523649553b6468573850cb85b2aa6c393c24f5c8

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_4_ks_27p_20261102

Rolls Battery (2024). **4 KS 27P flooded battery specifications**. [Source](https://rollsbattery.com/battery/4-ks-27p/)

**Role:** data. Exact model heading; charge/discharge, hour-rate and specifications tables; SHA256 648b6a6db8b9b1e5fbc4c698a813049e1db4712c33f2f37a4646b37f1ec475ed

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_2_ks_33p_20261102

Rolls Battery (2024). **2 KS 33P flooded battery specifications**. [Source](https://rollsbattery.com/battery/2-ks-33p/)

**Role:** data. Exact model heading; charge/discharge, hour-rate and specifications tables; SHA256 10dd64a23dcfd3bcbfe0c6553d0fdce1970655f519bcf96760fe60d2597fc568

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_2_os_33p_20261102

Rolls Battery (2024). **2 OS 33P flooded battery specifications**. [Source](https://rollsbattery.com/battery/2-os-33p/)

**Role:** data. Exact model heading; charge/discharge, hour-rate and specifications tables; SHA256 3528847408bbeae9fb9897f59a96bd253afb053e2dd77708532bb8b53a6f2bc8

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_2_ys_27p_20261102

Rolls Battery (2024). **2 YS 27P flooded battery specifications**. [Source](https://rollsbattery.com/battery/2-ys-27p/)

**Role:** data. Exact model heading; charge/discharge, hour-rate and specifications tables; SHA256 a6c27fc280ffe1cd1151854b8d9e93879ba013fc9b82fe587bfa91bde0950793

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_2_ys_31p_20261102

Rolls Battery (2024). **2 YS 31P flooded battery specifications**. [Source](https://rollsbattery.com/battery/2-ys-31p/)

**Role:** data. Exact model heading; charge/discharge, hour-rate and specifications tables; SHA256 0de959f4cb61da75a6eda3563604d55f93699f1931895d9cea6df32030df022e

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_2_ys_62p_20261102

Rolls Battery (2024). **2 YS 62P flooded battery specifications**. [Source](https://rollsbattery.com/battery/2-ys-62p/)

**Role:** data. Exact model heading; charge/discharge, hour-rate and specifications tables; SHA256 a333d418383ce3ac9428a3b07a1ba0e960839ba7de569916f3867dd6f77f9e51

**Used by:** `catalogues/bess_oem/sources.json`.

### rte_bellac_project_20261102

RTE (2026). **Stocker l’électricité renouvelable : expérimentation Ringo à Bellac**. [Source](https://www.rte-france.com/projets/nos-projets/stocker-lelectricite-renouvelable-lexperimentation-ringo-bellac-haute-vienne)

**Role:** data. Bellac: territoire favorable; expérimentation industrielle; 12 containers and Saft assembly in Bordeaux; SHA256 cf7d7fa67c85678339187de7188ec5b21e68c20bbe613b8e42500be6f25c920d

**Used by:** `catalogues/bess/sources.json`.

### odre_partition_4_20261102

RTE, Enedis, EDF SEI, ELD (2026). **National battery installation register, offset 400**. [Source](https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/registre-national-installation-production-stockage-electricite-agrege/records?where=filiere%3D%27Stockage+non+hydraulique%27+and+technologie%3D%27Batterie%27+and+typestockage%3D%27BATTE%27+and+puismaxinstallee%3E%3D1000&order_by=codeeicresourceobject&limit=100&offset=400)

**Role:** data. API results; exact EIC and source row in review ledger; SHA256 ff72cb71ea1364777e38a03a97f21c6da1bf09be12b082e9cd20204356c58d5b

**Used by:** `catalogues/bess/sources.json`.

### odre_partition_5_20261102

RTE, Enedis, EDF SEI, ELD (2026). **National battery installation register, offset 500**. [Source](https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/registre-national-installation-production-stockage-electricite-agrege/records?where=filiere%3D%27Stockage+non+hydraulique%27+and+technologie%3D%27Batterie%27+and+typestockage%3D%27BATTE%27+and+puismaxinstallee%3E%3D1000&order_by=codeeicresourceobject&limit=100&offset=500)

**Role:** data. API results; exact EIC and source row in review ledger; SHA256 120f173110ca8b23467b74d31a8df9c07c21651f7d86868b86a91d16864d1821

**Used by:** `catalogues/bess/sources.json`.

### rolls_lfp_g24_40lfp_20261102

Rolls Battery (2026). **G24-40LFP exact LFP specification**. [Source](https://rollsbattery.com/battery/g24-40lfp/)

**Role:** data. Exact model heading; Capacity, Charge/Discharge, Specifications tables; explicit row labels; SHA256 4cd270ecd15d53afba7c52f13e4c3c06ac9059bb2f73befdafc5cf81040d8538

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_lfp_r24_50lfp_20261102

Rolls Battery (2026). **R24-50LFP exact LFP specification**. [Source](https://rollsbattery.com/battery/r24-50lfp/)

**Role:** data. Exact model heading; Capacity, Charge/Discharge, Specifications tables; explicit row labels; SHA256 3916e7477b273ed5c959978a8a319b45e830991345af986e759f577dfda1cfa6

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_lfp_r48_90lfp_20261102

Rolls Battery (2026). **R48-90LFP exact LFP specification**. [Source](https://rollsbattery.com/battery/r48-90lfp/)

**Role:** data. Exact model heading; Capacity, Charge/Discharge, Specifications tables; explicit row labels; SHA256 7aa7a9a4257d60ca1fbccfe60d52223fd2c54ced91fff5aa1b93f1fbb578b467

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_lfp_vb12_100lfp_20261102

Rolls Battery (2026). **VB12-100LFP exact LFP specification**. [Source](https://rollsbattery.com/battery/vb12-100lfp/)

**Role:** data. Exact model heading; Capacity, Charge/Discharge, Specifications tables; explicit row labels; SHA256 7849c4a16374fc15748df4f31bcade6600a3cacdea0d14b9e7d4b0d72c9a495f

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_lfp_s48_100lfp_stack_lv_he_20261102

Rolls Battery (2026). **S48-100LFP STACK-LV HE exact LFP specification**. [Source](https://rollsbattery.com/battery/s48-100lfp-stack-lv-he/)

**Role:** data. Exact model heading; Capacity, Charge/Discharge, Specifications tables; explicit row labels; SHA256 c6dc1ae4af9e4cd002163c08c7069b4f6e3a653038ccf5f066a450e9198cf3b5

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_lfp_s48_100lfp_ess_he_20261102

Rolls Battery (2026). **S48-100LFP ESS HE exact LFP specification**. [Source](https://rollsbattery.com/battery/s48-100lfp-ess-he/)

**Role:** data. Exact model heading; Capacity, Charge/Discharge, Specifications tables; explicit row labels; SHA256 721cbb8847f649c00e759464bb337c0fc3780301dc7e8c71f6803851f5714ff5

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_lfp_s48_100lfp_stack_lv_e_20261102

Rolls Battery (2026). **S48-100LFP STACK-LV E exact LFP specification**. [Source](https://rollsbattery.com/battery/s48-100lfp-stack-lv-e/)

**Role:** data. Exact model heading; Capacity, Charge/Discharge, Specifications tables; explicit row labels; SHA256 08596e7d7c64420a6e0af14e64550234a47a45c190f43de496bdfbc4f30a3e57

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_lfp_s48_100lfp_ess_e_20261102

Rolls Battery (2026). **S48-100LFP ESS E exact LFP specification**. [Source](https://rollsbattery.com/battery/s48-100lfp-ess-e/)

**Role:** data. Exact model heading; Capacity, Charge/Discharge, Specifications tables; explicit row labels; SHA256 ddc9395b4483f5b91b58ae6a9dcd1e548fa44817900786ca5a238200c803171e

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_lfp_s24_100lfp_20261102

Rolls Battery (2026). **S24-100LFP exact LFP specification**. [Source](https://rollsbattery.com/battery/s24-100lfp/)

**Role:** data. Exact model heading; Capacity, Charge/Discharge, Specifications tables; explicit row labels; SHA256 8ab6e1bd4fd5395028d80b9b82dc3d9738771e3d35a3140ef75ce5e4de8dc2fb

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_lfp_s12_100lfp_20261102

Rolls Battery (2026). **S12-100LFP exact LFP specification**. [Source](https://rollsbattery.com/battery/s12-100lfp/)

**Role:** data. Exact model heading; Capacity, Charge/Discharge, Specifications tables; explicit row labels; SHA256 7a2e4465f851ebb0c1682427b3f5487b518af1bd79daff353135be192013e209

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_lfp_r24_100lfp_20261102

Rolls Battery (2026). **R24-100LFP exact LFP specification**. [Source](https://rollsbattery.com/battery/r24-100lfp/)

**Role:** data. Exact model heading; Capacity, Charge/Discharge, Specifications tables; explicit row labels; SHA256 556c197f1dcb2efb1dde3e42eb874adb3aec0b20b46dbdf362d7d84528f9a5db

**Used by:** `catalogues/bess_oem/sources.json`.

### rte_ventavon_project_20261102

RTE (2026). **Stocker l’électricité : expérimentation RINGO à Ventavon**. [Source](https://www.rte-france.com/projets/nos-projets/stocker-lelectricite-lexperimentation-ringo-ventavon)

**Role:** data. Industrial suppliers paragraph and Ventavon strategic junction paragraph; SHA256 d3fd255e252867d8e0ed7e01216695617f0d210c53b563002f00e9fc87a29e3b

**Used by:** `catalogues/bess/sources.json`.

### odre_partition_6_20261102

RTE, Enedis, EDF SEI, ELD (2026). **National battery installation register, offset 600**. [Source](https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/registre-national-installation-production-stockage-electricite-agrege/records?where=filiere%3D%27Stockage+non+hydraulique%27+and+technologie%3D%27Batterie%27+and+typestockage%3D%27BATTE%27+and+puismaxinstallee%3E%3D1000&order_by=codeeicresourceobject&limit=100&offset=600)

**Role:** data. API results; exact EIC and source row in review ledger; SHA256 a606938e5ba3d6b491ef0a10ea470b4d99be583fa2d3c44f6b2725542b4c8213

**Used by:** `catalogues/bess/sources.json`.

### odre_partition_7_20261102

RTE, Enedis, EDF SEI, ELD (2026). **National battery installation register, offset 700**. [Source](https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/registre-national-installation-production-stockage-electricite-agrege/records?where=filiere%3D%27Stockage+non+hydraulique%27+and+technologie%3D%27Batterie%27+and+typestockage%3D%27BATTE%27+and+puismaxinstallee%3E%3D1000&order_by=codeeicresourceobject&limit=100&offset=700)

**Role:** data. API results; exact EIC and source row in review ledger; SHA256 6f2c68e18f2ac1411687d9d29a4678380ab47118cdae085bd1e8de5a265bd89b

**Used by:** `catalogues/bess/sources.json`.

### rolls_lfp_r12_100lfp_20261102

Rolls Battery (2026). **R12-100LFP exact LFP specification**. [Source](https://rollsbattery.com/battery/r12-100lfp/)

**Role:** data. Exact model heading; Capacity, Charge/Discharge, Specifications tables; explicit row labels; SHA256 00856f5cba964a353f5de85de20b6006f16d6aaaa8041fc286b588362f4407e7

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_lfp_g24_130lfp_20261102

Rolls Battery (2026). **G24-130LFP exact LFP specification**. [Source](https://rollsbattery.com/battery/g24-130lfp/)

**Role:** data. Exact model heading; Capacity, Charge/Discharge, Specifications tables; explicit row labels; SHA256 d5525825e2e5be406273fd427892c5834252edbdbc59c9dd9572c0c3083b0aff

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_lfp_vb12_135lfp_rv_20261102

Rolls Battery (2026). **VB12-135LFP-RV exact LFP specification**. [Source](https://rollsbattery.com/battery/vb12-135lfp-rv/)

**Role:** data. Exact model heading; Capacity, Charge/Discharge, Specifications tables; explicit row labels; SHA256 21921f69057eb573dfab69bc672ad63459688eb417da4a226afe1d71501c0b6d

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_lfp_vb24_150lfp_20261102

Rolls Battery (2026). **VB24-150LFP exact LFP specification**. [Source](https://rollsbattery.com/battery/vb24-150lfp/)

**Role:** data. Exact model heading; Capacity, Charge/Discharge, Specifications tables; explicit row labels; SHA256 2040a2d8a2b43ac946bfe606c2d71c2a92f4e4472645e3877787796b318e942a

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_lfp_r24_150lfp_20261102

Rolls Battery (2026). **R24-150LFP exact LFP specification**. [Source](https://rollsbattery.com/battery/r24-150lfp/)

**Role:** data. Exact model heading; Capacity, Charge/Discharge, Specifications tables; explicit row labels; SHA256 631c67ebd2e257019b5d1ca51aa19e6076adaa692e4902a1b7a427158b6687e8

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_lfp_vb12_150lfp_rv_20261102

Rolls Battery (2026). **VB12-150LFP-RV exact LFP specification**. [Source](https://rollsbattery.com/battery/vb12-150lfp-rv/)

**Role:** data. Exact model heading; Capacity, Charge/Discharge, Specifications tables; explicit row labels; SHA256 cb756f8b7a2a42fa101e1d0114ee97b82759b478f6c4fb06d6331634421fab64

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_lfp_r12_150lfp_20261102

Rolls Battery (2026). **R12-150LFP exact LFP specification**. [Source](https://rollsbattery.com/battery/r12-150lfp/)

**Role:** data. Exact model heading; Capacity, Charge/Discharge, Specifications tables; explicit row labels; SHA256 b59511665780a9dfba44963075ad676ce241363a2ce35ac5f3b28eebca34c4a5

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_lfp_vb12_150lfp_20261102

Rolls Battery (2026). **VB12-150LFP exact LFP specification**. [Source](https://rollsbattery.com/battery/vb12-150lfp/)

**Role:** data. Exact model heading; Capacity, Charge/Discharge, Specifications tables; explicit row labels; SHA256 8f8807906324a5bef8ec224c65bbc5d109e3ba565169ea7e1148844a9adc8766

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_lfp_vb12_200lfp_20261102

Rolls Battery (2026). **VB12-200LFP exact LFP specification**. [Source](https://rollsbattery.com/battery/vb12-200lfp/)

**Role:** data. Exact model heading; Capacity, Charge/Discharge, Specifications tables; explicit row labels; SHA256 b74d7dffc8b97132b611c4581bf43af333dd52b3224045b63e7d5aa1ba0f0969

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_lfp_vb24_200lfp_20261102

Rolls Battery (2026). **VB24-200LFP exact LFP specification**. [Source](https://rollsbattery.com/battery/vb24-200lfp/)

**Role:** data. Exact model heading; Capacity, Charge/Discharge, Specifications tables; explicit row labels; SHA256 466bcf6ab53983587c471c21909bbee1357857f90c83389cc613ab726cd6e726

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_lfp_r12_200lfp_20261102

Rolls Battery (2026). **R12-200LFP exact LFP specification**. [Source](https://rollsbattery.com/battery/r12-200lfp/)

**Role:** data. Exact model heading; Capacity, Charge/Discharge, Specifications tables; explicit row labels; SHA256 04e3f0ee8bc6f4c639fdf44090c9fe38682a1afe3b9f8870087346aca07de34c

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_lfp_r12_300lfp_20261102

Rolls Battery (2026). **R12-300LFP exact LFP specification**. [Source](https://rollsbattery.com/battery/r12-300lfp/)

**Role:** data. Exact model heading; Capacity, Charge/Discharge, Specifications tables; explicit row labels; SHA256 b4cd454baff520aa61f361a6a294cfd0bd7ec8bb28fc08b450b1004b9a9f54f0

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_lfp_vb12_314lfp_20261102

Rolls Battery (2026). **VB12-314LFP exact LFP specification**. [Source](https://rollsbattery.com/battery/vb12-314lfp/)

**Role:** data. Exact model heading; Capacity, Charge/Discharge, Specifications tables; explicit row labels; SHA256 0d55655ee451c54f55d45af0c8a889c0fc462837b26d3ee51cc041e4484c3bbc

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_lfp_s48_314lfp_stack_lv_e_20261102

Rolls Battery (2026). **S48-314LFP STACK-LV E exact LFP specification**. [Source](https://rollsbattery.com/battery/s48-314lfp-stack-lv-e/)

**Role:** data. Exact model heading; Capacity, Charge/Discharge, Specifications tables; explicit row labels; SHA256 453faa0d6706223e891ec609e679d117fcf06f94c3d958ebe63676f438bd36be

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_lfp_vb12_314lfp_200_20261102

Rolls Battery (2026). **VB12-314LFP (200A) exact LFP specification**. [Source](https://rollsbattery.com/battery/vb12-314lfp-200/)

**Role:** data. Exact model heading; Capacity, Charge/Discharge, Specifications tables; explicit row labels; SHA256 494086debb5ebff0aba6f63dcb8283811098ca49f4c87da1db45e27475426daf

**Used by:** `catalogues/bess_oem/sources.json`.

### victron_lithium_smart_20261102

Victron Energy (2026). **Lithium Battery Smart manual: technical data**. [Source](https://www.victronenergy.com/media/pg/Lithium_Battery_Smart/en/technical-data.html)

**Role:** data. Technical data: exact battery model columns and labelled specification rows; review ledger locators; SHA256 025ac0673f80092118abc92f6e134ce4fbba659fa0af5f7e360b66cbe34980b0

**Used by:** `catalogues/bess_oem/sources.json`.

### victron_lithium_ng_20261102

Victron Energy (2026). **Lithium NG 12.8 V manual: technical data**. [Source](https://www.victronenergy.com/media/pg/Lithium_NG_battery_12%2C8_V/en/technical-data.html)

**Role:** data. Technical data: exact battery model columns and labelled specification rows; review ledger locators; SHA256 092a662759ca34febc5bbf9d07336e9c0efe4b4530bf673aae0f07ca0b0b1127

**Used by:** `catalogues/bess_oem/sources.json`.

### hubble_controls_am_4_20261102

Hubble Energy (2026). **AM-4 technical specifications**. [Source](https://www.hubbleenergy.com/am-4)

**Role:** data. Exact model TECHNICAL SPECIFICATIONS; protection, enclosure, current limiter and operating temperature rows; SHA256 163ba5a4a54f7f87d0acd0561507a456567878a8bcaab596995da5e3bf3adef4

**Used by:** `catalogues/bess_oem/sources.json`.

### hubble_controls_am_5plus_20261102

Hubble Energy (2026). **AM5+ technical specifications**. [Source](https://www.hubbleenergy.com/am-5plus)

**Role:** data. Exact model TECHNICAL SPECIFICATIONS; protection, enclosure, current limiter and operating temperature rows; SHA256 b3a335aa512a0f69e9fa0cd1ca8643c8746b703c539a758265e8d308fd83e30f

**Used by:** `catalogues/bess_oem/sources.json`.

### hubble_controls_am_10plus_20261102

Hubble Energy (2026). **AM10+ technical specifications**. [Source](https://www.hubbleenergy.com/am-10plus)

**Role:** data. Exact model TECHNICAL SPECIFICATIONS; protection, enclosure, current limiter and operating temperature rows; SHA256 a68c9a40e55257f0ef90870bbf7ec213504cc9594acc0d5b6b6a18d369576979

**Used by:** `catalogues/bess_oem/sources.json`.

### hubble_controls_am_16plus_20261102

Hubble Energy (2026). **AM16+ technical specifications**. [Source](https://www.hubbleenergy.com/am-16plus)

**Role:** data. Exact model TECHNICAL SPECIFICATIONS; protection, enclosure, current limiter and operating temperature rows; SHA256 80f5f84edc26da30d319a1d0b84958d3f6d869b7f10730acd9de4f87fc26a73c

**Used by:** `catalogues/bess_oem/sources.json`.

### eskom_ir2024_wb_20261102

Eskom (2024). **Eskom Integrated Report 2024**. [Source](https://documents1.worldbank.org/curated/en/099042925105519733/pdf/P122329-78739271-286e-4b2a-b89b-02d26966a43a.pdf)

**Role:** data. PDF page 83 / printed page 81, Other projects: BESS, package 2 and package 3 rows; SHA256 675003b367f89908f9713786e0acfb85f9b46776b53e66fd7b39e603cf05606a

**Used by:** `catalogues/bess/sources.json`.

### victron_ng_followup_25_20261102

Victron Energy (2026). **Lithium NG 25.6 V manual: technical data**. [Source](https://www.victronenergy.com/media/pg/Lithium_NG_battery_25%2C6_V/en/technical-data.html)

**Role:** data. Section 8.1 exact model columns; charge/float voltage rows; current, energy, dimensions and operating-condition rows for new NG models; SHA256 6a87910fa430b8c5f27782829f95ee598bad76bdd880671fe17802547c5aae64

**Used by:** `catalogues/bess_oem/sources.json`.

### victron_ng_followup_51_20261102

Victron Energy (2026). **Lithium NG 51.2 V manual: technical data**. [Source](https://www.victronenergy.com/media/pg/Lithium_NG_battery_51%2C2_V/en/technical-data.html)

**Role:** data. Section 8.1 exact model columns; charge/float voltage rows; current, energy, dimensions and operating-condition rows for new NG models; SHA256 c9958d54499a3eb90e35ea50bbf622b37ac2f9da58d4c7774393848603aba1b8

**Used by:** `catalogues/bess_oem/sources.json`.

### bms_iati_lynxng_20261102

Victron Energy (2026). **Lynx Smart BMS NG Manual — Technical specifications**. [Source](https://www.victronenergy.com/media/pg/Lynx_Smart_BMS_NG/en/technical-specifications.html)

**Role:** data. Exact model header; voltage, contactor/current, consumption, temperature, enclosure and physical rows; SHA256 d7a42206c631c65aa6ef4d3b125f79e80fb7b6d77fff59726c71807b3b6d4940

**Used by:** `catalogues/bess_oem/sources.json`.

### bms_iati_lynx_20261102

Victron Energy (2026). **Lynx Smart BMS — Technical specifications**. [Source](https://www.victronenergy.com/media/pg/Lynx_Smart_BMS/en/technical-specifications.html)

**Role:** data. Exact model header; voltage, contactor/current, consumption, temperature, enclosure and physical rows; SHA256 b0d072d3718bd96d0700782d8d865d2edaf0eee591e299b899fdb7034112d84f

**Used by:** `catalogues/bess_oem/sources.json`.

### bms_iati_smallng_20261102

Victron Energy (2026). **smallBMS NG — Specifications**. [Source](https://www.victronenergy.com/media/pg/smallBMS_NG/en/specifications.html)

**Role:** data. Exact model header; voltage, contactor/current, consumption, temperature, enclosure and physical rows; SHA256 2c7655a3c21d7accac17c120292a0e9e4264d497464c525425218c970abe38f5

**Used by:** `catalogues/bess_oem/sources.json`.

### bms_iati_small_20261102

Victron Energy (2026). **smallBMS with pre-alarm — Specifications**. [Source](https://www.victronenergy.com/media/pg/smallBMS_with_pre-alarm/en/specifications.html)

**Role:** data. Exact model header; voltage, contactor/current, consumption, temperature, enclosure and physical rows; SHA256 231029c774f8f7cccab06eb152da377cadf6cf4fb58fa9ac0d29558d68e43843

**Used by:** `catalogues/bess_oem/sources.json`.

### bms_iati_vebusng_20261102

Victron Energy (2026). **VE.Bus BMS NG — Technical specifications VE.Bus BMS NG**. [Source](https://www.victronenergy.com/media/pg/VE.Bus_BMS_NG_-_Manual/en/technical-specifications-ve-bus-bms-ng.html)

**Role:** data. Exact model header; voltage, contactor/current, consumption, temperature, enclosure and physical rows; SHA256 ac8e2f98eb12fb6a284131bd786879034e19325c69248b49c71aea825841af13

**Used by:** `catalogues/bess_oem/sources.json`.

### bms_iati_vebusv2_20261102

Victron Energy (2026). **VE.Bus BMS V2 — Technical specifications VE.Bus BMS V2**. [Source](https://www.victronenergy.com/media/pg/VE.Bus_BMS_V2/en/technical-specifications-ve-bus-bms-v2.html)

**Role:** data. Exact model header; voltage, contactor/current, consumption, temperature, enclosure and physical rows; SHA256 045e67f9a01d3b5276db86d27248edb86a8c9c80b885df280c9fb2bab60e1eb2

**Used by:** `catalogues/bess_oem/sources.json`.

### bms_iati_smart200_20261102

Victron Energy (2026). **Smart BMS 12-200 — Specifications**. [Source](https://www.victronenergy.com/media/pg/Smart_BMS_12-200/en/specifications.html)

**Role:** data. Exact model header; voltage, contactor/current, consumption, temperature, enclosure and physical rows; SHA256 b08c826c71c2722369ff8c4e23f75ca540de094802e2fc368c83329e5a696cbb

**Used by:** `catalogues/bess_oem/sources.json`.

### bms_iati_smartcl_20261102

Victron Energy (2026). **Smart BMS CL 12-100 — Specifications**. [Source](https://www.victronenergy.com/media/pg/Smart_BMS_CL_12-100/en/specifications.html)

**Role:** data. Exact model header; voltage, contactor/current, consumption, temperature, enclosure and physical rows; SHA256 bb813a1656fcf0b2a2fefee5f5c4f073c87abff509acf3c176cb74fcb25ac40d

**Used by:** `catalogues/bess_oem/sources.json`.

### bms_iati_iati_20261102

Asian Development Bank (2026). **ADB Uzbekistan IATI activities**. [Source](https://www.adb.org/iati/iati-activities-uz.xml)

**Role:** data. Activity IDs 57212-001-LN4380, 58338-001-LN4611, 58094-001-LN4661, 54056-003-GRNT4678; title, description, implementing entity, status/date fields; SHA256 34410bad5c2dd8c4ce96c60900618b1eeee6909887355c6a1fbc03b532954c43

**Used by:** `catalogues/bess/sources.json`.

### adb_india_20261102

Asian Development Bank (2026). **ADB India IATI activities**. [Source](https://www.adb.org/iati/iati-activities-in.xml)

**Role:** data_source. Primary factual evidence; exact locators, revision, checksum and source reuse qualification in catalogue sources.json.

**Used by:** `catalogues/bess/sources.json`.

### victron_vedirect_hw15_230v_20261102

Victron Energy (2026). **Inverter VE.Direct 230V HW15 technical specifications**. [Source](https://www.victronenergy.com/media/pg/Inverter_VE.Direct_230V_-_HW15/en/technical-specifications.html)

**Role:** data_source. Primary factual evidence; exact locators, revision, checksum and source reuse qualification in catalogue sources.json.

**Used by:** `catalogues/bess_oem/sources.json`.

### victron_hw15_120v_20261103

Victron Energy (2026). **Inverter VE.Direct 120V HW15 technical specifications**. [Source](https://www.victronenergy.com/media/pg/Inverter_VE.Direct_120V_-_HW15/en/technical-specifications.html)

**Role:** data. Exact model factual specifications; table/model locators and source hash in source register.

**Used by:** `catalogues/bess_oem/sources.json`.

### victron_hw15_230v_20261103

Victron Energy (2026). **Inverter VE.Direct 230V HW15 technical specifications**. [Source](https://www.victronenergy.com/media/pg/Inverter_VE.Direct_230V_-_HW15/en/technical-specifications.html)

**Role:** data. HW15 230 V manufacturer safety and EMC claims; not independent certification.

**Used by:** `catalogues/bess_oem/sources.json`.

### freedomwon_lite2_home_10_52v_model_b_20260206

Freedom Won (2026). **LiTE 2 Home 10/8 52V Model B specification sheet**. [Source](https://www.freedomwon.co.za/wp-content/uploads/FW-LiTE-2-Home-10_8-52V-B.pdf)

**Role:** data. Exact named model, page 1 rows/notes; source checksum in register.

**Used by:** `catalogues/bess_oem/sources.json`.

### freedomwon_lite2_home_15_52v_model_b_20260206

Freedom Won (2026). **LiTE 2 Home 15/12 52V Model B specification sheet**. [Source](https://www.freedomwon.co.za/wp-content/uploads/FW-LiTE-2-Home-15_12-52V-B.pdf)

**Role:** data. Exact named model, page 1 rows/notes; source checksum in register.

**Used by:** `catalogues/bess_oem/sources.json`.

### freedomwon_lite2_home_20_52v_model_b_20260206

Freedom Won (2026). **LiTE 2 Home 20/16 52V Model B specification sheet**. [Source](https://www.freedomwon.co.za/wp-content/uploads/FW-LiTE-2-Home-20_16-52V-B.pdf)

**Role:** data. Exact named model, page 1 rows/notes; source checksum in register.

**Used by:** `catalogues/bess_oem/sources.json`.

### freedomwon_lite2_business_40_52v_20260206

Freedom Won (2026). **LiTE 2 Business 40/32 52V specification sheet**. [Source](https://www.freedomwon.co.za/wp-content/uploads/FW-LiTE-2-Business-40_32-52V-1.pdf)

**Role:** data. Exact named model, page 1 rows/notes; source checksum in register.

**Used by:** `catalogues/bess_oem/sources.json`.

### freedomwon_lite2_business_60_52v_20260206

Freedom Won (2026). **LiTE 2 Business 60/48 52V specification sheet**. [Source](https://www.freedomwon.co.za/wp-content/uploads/FW-LiTE-2-Business-60_48-52V-1.pdf)

**Role:** data. Exact named model, page 1 rows/notes; source checksum in register.

**Used by:** `catalogues/bess_oem/sources.json`.

### freedomwon_lite2_business_80_52v_20260206

Freedom Won (2026). **LiTE 2 Business 80/64 52V specification sheet**. [Source](https://www.freedomwon.co.za/wp-content/uploads/FW-LiTE-2-Business-80_64-52V-1.pdf)

**Role:** data. Exact named model, page 1 rows/notes; source checksum in register.

**Used by:** `catalogues/bess_oem/sources.json`.

### freedomwon_lite2_home_10_hv_20260206

Freedom Won (2026). **LiTE 2 Home 10/8 HV specification sheet**. [Source](https://www.freedomwon.co.za/wp-content/uploads/FW-LiTE-2-Home-10_8-HV-1.pdf)

**Role:** data. Exact named model, page 1 rows/notes; source checksum in register.

**Used by:** `catalogues/bess_oem/sources.json`.

### freedomwon_lite2_home_15_hv_20260206

Freedom Won (2026). **LiTE 2 Home 15/12 HV specification sheet**. [Source](https://www.freedomwon.co.za/wp-content/uploads/FW-LiTE-2-Home-15_12-HV.pdf)

**Role:** data. Exact named model, page 1 rows/notes; source checksum in register.

**Used by:** `catalogues/bess_oem/sources.json`.

### freedomwon_lite2_home_20_hv_20260206

Freedom Won (2026). **LiTE 2 Home 20/16 HV specification sheet**. [Source](https://www.freedomwon.co.za/wp-content/uploads/FW-LiTE-2-Home-20_16-HV-1.pdf)

**Role:** data. Exact named model, page 1 rows/notes; source checksum in register.

**Used by:** `catalogues/bess_oem/sources.json`.

### freedomwon_lite2_home_30_hv_20260206

Freedom Won (2026). **LiTE 2 Home 30/24 HV specification sheet**. [Source](https://www.freedomwon.co.za/wp-content/uploads/FW-LiTE-2-Home-30_24-HV-1.pdf)

**Role:** data. Exact named model, page 1 rows/notes; source checksum in register.

**Used by:** `catalogues/bess_oem/sources.json`.

### akuo_tonga_opening_20221025

Akuo (2022). **Tonga BESS completion ceremony**. [Source](https://www.akuoenergy.com/en/press/official-completion-ceremony-tongas-1st-ever-large-scale-battery-energy-storage-systems)

**Role:** data. Opening paragraphs and named sites

**Used by:** `catalogues/bess/sources.json`.

### akuo_tonga_portfolio_20261103

Akuo (2026). **Tonga renewable energy storage project**. [Source](https://www.akuoenergy.com/en/akuo-in-the-world/all-our-projects/tonga)

**Role:** data. Two storage facilities and operation paragraphs

**Used by:** `catalogues/bess/sources.json`.

### tonga_ndc_review_2025

Government of Tonga (2025). **Tonga Second Nationally Determined Contributions Review Report**. [Source](https://www.unfccc.int/sites/default/files/2025-09/Tongas%20Second%20Nationally%20Determined%20Contribution%20Review%20Report.pdf)

**Role:** data. Printed page 16 / PDF page 24, battery storage paragraph

**Used by:** `catalogues/bess/sources.json`.

### encore_encore_12k_20261103

Freedom Won (2024). **Encore 12K exact inverter specification**. [Source](https://www.freedomwon.co.za/wp-content/uploads/Spec-Sheet-Encore-Three-Phase-Inverter-12K.pdf)

**Role:** data. Physical PDF page 1 electrical/thermal rows and numbered notes; page 2 physical rows for three-phase units

**Used by:** `catalogues/bess_oem/sources.json`.

### encore_encore_15k_20261103

Freedom Won (2024). **Encore 15K exact inverter specification**. [Source](https://www.freedomwon.co.za/wp-content/uploads/Spec-Sheet-Encore-Three-Phase-Inverter-15K.pdf)

**Role:** data. Physical PDF page 1 electrical/thermal rows and numbered notes; page 2 physical rows for three-phase units

**Used by:** `catalogues/bess_oem/sources.json`.

### encore_hps50_20261103

Freedom Won (2024). **HPS50 exact inverter specification**. [Source](https://www.freedomwon.co.za/wp-content/uploads/Spec-Sheet-Encore-HPS-Inverter-50_120K.pdf)

**Role:** data. Physical PDF page 1 electrical/thermal rows and numbered notes; page 2 physical rows for three-phase units

**Used by:** `catalogues/bess_oem/sources.json`.

### encore_hps100_20261103

Freedom Won (2024). **HPS100 exact inverter specification**. [Source](https://www.freedomwon.co.za/wp-content/uploads/Spec-Sheet-Encore-HPS-Inverter-100_180K.pdf)

**Role:** data. Physical PDF page 1 electrical/thermal rows and numbered notes; page 2 physical rows for three-phase units

**Used by:** `catalogues/bess_oem/sources.json`.

### encore_hps150_20261103

Freedom Won (2024). **HPS150 exact inverter specification**. [Source](https://www.freedomwon.co.za/wp-content/uploads/Spec-Sheet-Encore-HPS-Inverter-150_240K.pdf)

**Role:** data. Physical PDF page 1 electrical/thermal rows and numbered notes; page 2 physical rows for three-phase units

**Used by:** `catalogues/bess_oem/sources.json`.

### encore_hps250_20261103

Freedom Won (2024). **HPS250 exact inverter specification**. [Source](https://www.freedomwon.co.za/wp-content/uploads/Spec-Sheet-Encore-HPS-Inverter-250_300K.pdf)

**Role:** data. Physical PDF page 1 electrical/thermal rows and numbered notes; page 2 physical rows for three-phase units

**Used by:** `catalogues/bess_oem/sources.json`.

### encore_hps500_20261103

Freedom Won (2024). **HPS500 exact inverter specification**. [Source](https://www.freedomwon.co.za/wp-content/uploads/Spec-Sheet-Encore-HPS-Inverter-500_600K.pdf)

**Role:** data. Physical PDF page 1 electrical/thermal rows and numbered notes; page 2 physical rows for three-phase units

**Used by:** `catalogues/bess_oem/sources.json`.

### tonga_pmo_eua_202303

Government of Tonga, Prime Minister office (2023). **Eua solar and battery commissioning**. [Source](https://pmo.gov.to/kingdom-of-tonga-celebrates-major-milestone-towards-renewable-energy-target-with-commissioning-of-eua-island-350kw-solar-system-and-bess-tonga-renewable-energy-project/)

**Role:** data. Dated opening paragraph, system description and contractor paragraph

**Used by:** `catalogues/bess/sources.json`.

### tonga_pmo_vavau_202303

Government of Tonga, Prime Minister office (2023). **Vavau solar and battery commissioning**. [Source](https://pmo.gov.to/kingdom-of-tonga-celebrates-major-milestone-towards-renewable-energy-target-with-commissioning-of-vavau-island-300kw-solar-system-and-bess-tonga-renewable-energy-project/)

**Role:** data. Dated opening paragraph, system description and contractor paragraph

**Used by:** `catalogues/bess/sources.json`.

### tpl_trep03_lot1_status_20261103

Tonga Power Limited (2026). **TREP-03 Lot 1 Eua and Vavau solar and storage systems contract status**. [Source](https://tongapower.to/node/218)

**Role:** data. Contract summary: completion certificate October 2024; current status plant in operation

**Used by:** `catalogues/bess/sources.json`.

### freedomwon_ems_eol_20241021

Freedom Won (2024). **EMS Standard and Pro historical hardware**. [Source](https://www.freedomwon.co.za/wp-content/uploads/Freedom-Won-EMS-Range-Overview-Sheet-EOL.pdf)

**Role:** data. Pages 1-2, exact Standard/Pro columns and notes

**Used by:** `catalogues/bess_oem/sources.json`.

### epc_cab1000_3l2_20250923

Freedom Won (EPC Power distributor) (2025). **EPC Power CAB1000 (3L.2) specification**. [Source](https://www.freedomwon.co.za/wp-content/uploads/EPC-Power-CAB1000-Spec-Sheet.pdf)

**Role:** data. Page 1, five nominal-voltage columns and notes 1-8

**Used by:** `catalogues/bess_oem/sources.json`.

### fw_enva_5_detail_20261103

Freedom Won (2026). **ENVA 5 detailed specification**. [Source](https://www.freedomwon.co.za/wp-content/uploads/Freedom-Won-ENVA-5-Spec-Sheet-260526.pdf)

**Role:** data. Exact model table: storage/prospective short-circuit rows (ENVA pages 1-2); connection/protection rows (SOLVA page 1)

**Used by:** `catalogues/bess_oem/sources.json`.

### fw_enva_16_detail_20261103

Freedom Won (2026). **ENVA 16 detailed specification**. [Source](https://www.freedomwon.co.za/wp-content/uploads/Freedom-Won-ENVA-16-Spec-Sheet-280826.pdf)

**Role:** data. Exact model table: storage/prospective short-circuit rows (ENVA pages 1-2); connection/protection rows (SOLVA page 1)

**Used by:** `catalogues/bess_oem/sources.json`.

### fw_solva_ac261_detail_20261103

Freedom Won (2026). **SOLVA AC261 detailed specification**. [Source](https://www.freedomwon.co.za/wp-content/uploads/SOLVA-AC261-Spec-Sheet-170926.pdf)

**Role:** data. Exact model table: storage/prospective short-circuit rows (ENVA pages 1-2); connection/protection rows (SOLVA page 1)

**Used by:** `catalogues/bess_oem/sources.json`.

### fw_solva_dc208_detail_20261103

Freedom Won (2026). **SOLVA DC208 detailed specification**. [Source](https://www.freedomwon.co.za/wp-content/uploads/SOLVA-DC208-Spec-Sheet-170926.pdf)

**Role:** data. Exact model table: storage/prospective short-circuit rows (ENVA pages 1-2); connection/protection rows (SOLVA page 1)

**Used by:** `catalogues/bess_oem/sources.json`.

### dfat_tonga_completion_202402

Australian Department of Foreign Affairs and Trade (2024). **Independent Completion Review: Australia contribution to the multi-donor Tonga Outer Islands Renewable Energy Project**. [Source](https://www.dfat.gov.au/sites/default/files/tonga-outer-islands-renewable-energy-project.pdf)

**Role:** data. Table One, printed pages 11-12, PDF pages 20-21; surrounding text printed page 13

**Used by:** `catalogues/bess/sources.json`.

### sprep_tonga_bess_case_table

SPREP library (ADB technical publication mirror) (2024). **Hybrid and Battery Energy Storage Systems: Tonga case-study table**. [Source](https://library.sprep.org/sites/default/files/2022-09/hybrid-battery-energy-storage-systems.pdf)

**Role:** data. Table 3.2 continued, printed page 19; financed project infrastructure

**Used by:** `catalogues/bess/sources.json`.

### dc_nextdc_20261102

NEXTDC (n.d.). **Data Centres: complete displayed portfolio**. [Source](https://www.nextdc.com/data-centres)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nextdc_s1_sydney_20261102

NEXTDC (n.d.). **NEXTDC S1 facility specifications**. [Source](https://www.nextdc.com/data-centres/sydney-data-centres/s1-sydney)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nextdc_s2_sydney_20261102

NEXTDC (n.d.). **NEXTDC S2 facility specifications**. [Source](https://www.nextdc.com/data-centres/sydney-data-centres/s2-sydney)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nextdc_s3_sydney_20261102

NEXTDC (n.d.). **NEXTDC S3 facility specifications**. [Source](https://www.nextdc.com/data-centres/sydney-data-centres/s3-sydney)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nextdc_s4_sydney_20261102

NEXTDC (n.d.). **NEXTDC S4 facility specifications**. [Source](https://www.nextdc.com/data-centres/sydney-data-centres/s4-sydney)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nextdc_s5_sydney_20261102

NEXTDC (n.d.). **NEXTDC S5 facility specifications**. [Source](https://www.nextdc.com/data-centres/sydney-data-centres/s5-sydney)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nextdc_s6_sydney_20261102

NEXTDC (n.d.). **NEXTDC S6 facility specifications**. [Source](https://www.nextdc.com/data-centres/sydney-data-centres/s6-sydney)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nextdc_s7_sydney_20261102

NEXTDC (n.d.). **NEXTDC S7 facility specifications**. [Source](https://www.nextdc.com/data-centres/sydney-data-centres/s7-sydney)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nextdc_m1_melbourne_20261102

NEXTDC (n.d.). **NEXTDC M1 facility specifications**. [Source](https://www.nextdc.com/data-centres/melbourne-data-centres/m1-melbourne)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nextdc_m2_melbourne_20261102

NEXTDC (n.d.). **NEXTDC M2 facility specifications**. [Source](https://www.nextdc.com/data-centres/melbourne-data-centres/m2-melbourne)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nextdc_m3_melbourne_20261102

NEXTDC (n.d.). **NEXTDC M3 facility specifications**. [Source](https://www.nextdc.com/data-centres/melbourne-data-centres/m3-melbourne)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nextdc_ge1_geelong_20261102

NEXTDC (n.d.). **NEXTDC GE1 facility specifications**. [Source](https://www.nextdc.com/data-centres/geelong-data-centres/ge1-geelong)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nextdc_m4_melbourne_20261102

NEXTDC (n.d.). **NEXTDC M4 facility specifications**. [Source](https://www.nextdc.com/data-centres/melbourne-data-centres/m4-melbourne)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nextdc_b1_brisbane_20261102

NEXTDC (n.d.). **NEXTDC B1 facility specifications**. [Source](https://www.nextdc.com/data-centres/brisbane-data-centres/b1-brisbane)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nextdc_b2_brisbane_20261102

NEXTDC (n.d.). **NEXTDC B2 facility specifications**. [Source](https://www.nextdc.com/data-centres/brisbane-data-centres/b2-brisbane)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nextdc_gc1_gold_coast_20261102

NEXTDC (n.d.). **NEXTDC GC1 facility specifications**. [Source](https://www.nextdc.com/data-centres/gold-coast-data-centres/gc1-gold-coast)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nextdc_p1_perth_20261102

NEXTDC (n.d.). **NEXTDC P1 facility specifications**. [Source](https://www.nextdc.com/data-centres/perth-data-centres/p1-perth)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nextdc_p2_perth_20261102

NEXTDC (n.d.). **NEXTDC P2 facility specifications**. [Source](https://www.nextdc.com/data-centres/perth-data-centres/p2-perth)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nextdc_a1_adelaide_20261102

NEXTDC (n.d.). **NEXTDC A1 facility specifications**. [Source](https://www.nextdc.com/data-centres/adelaide-data-centre/a1-adelaide)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nextdc_c1_canberra_20261102

NEXTDC (n.d.). **NEXTDC C1 facility specifications**. [Source](https://www.nextdc.com/data-centres/canberra-data-centres/c1-canberra)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nextdc_d1_darwin_20261102

NEXTDC (n.d.). **NEXTDC D1 facility specifications**. [Source](https://www.nextdc.com/data-centres/darwin-data-centres/d1-darwin)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nextdc_d2_darwin_20261102

NEXTDC (n.d.). **NEXTDC D2 facility specifications**. [Source](https://www.nextdc.com/data-centres/darwin-data-centres/d2-darwin)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nextdc_sc1_sunshine_coast_20261102

NEXTDC (n.d.). **NEXTDC SC1 facility specifications**. [Source](https://www.nextdc.com/data-centres/sunshine-coast-data-centres/sc1-sunshine-coast)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nextdc_sc2_sunshine_coast_20261102

NEXTDC (n.d.). **NEXTDC SC2 facility specifications**. [Source](https://www.nextdc.com/data-centres/sunshine-coast-data-centres/sc2-sunshine-coast)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_odata_pt_20261102

ODATA (n.d.). **Complete public location-map inventory**. [Source](https://odatadc.com/localidades/)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_odata_brazil_20261102

ODATA (n.d.). **Brazil named campus overview and technology**. [Source](https://odatadc.com/localidades-brasil/)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_teraco_jb1_20261102

Teraco (n.d.). **Johannesburg Isando and Bredell named facilities**. [Source](https://www.teraco.co.za/data-centre-locations/johannesburg/)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_teraco_ct2_20261102

Teraco (n.d.). **Cape Town CT1 and CT2 facilities**. [Source](https://www.teraco.co.za/data-centre-locations/cape-town/?tab=brackenfell-ct2)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_teraco_db1_20261102

Teraco (n.d.). **Durban DB1 facility**. [Source](https://www.teraco.co.za/data-centre-locations/durban/)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_gdh_dubai_20261102

Gulf Data Hub (n.d.). **Dubai named facilities and lifecycle**. [Source](https://www.gulfdatahub.ae/dubai)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_gdh_abu_dhabi_20261102

Gulf Data Hub (n.d.). **Abu Dhabi ICAD and KIZAD facilities**. [Source](https://www.gulfdatahub.ae/abuDhabi)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_khazna_auh6_20261102

Khazna (2024). **AUH6 launch and physical solar supply**. [Source](https://khaznadatacenters.com/press-release/khazna-data-centers-fuels-uaes-digital-future-with-the-launch-of-hyperscale-ai-ready-data-center-in-masdar-city/)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_google_efficiency_20261102

Google (n.d.). **Power usage effectiveness: 2026 Q2 complete campus table**. [Source](https://www.datacenters.google/efficiency/)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_google_fredericia_20261102

Google (n.d.). **Fredericia location**. [Source](https://www.datacenters.google/locations/fredericia-denmark/)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_google_hamina_20261102

Google (n.d.). **Hamina location: cooling and heat recovery**. [Source](https://www.datacenters.google/locations/hamina-finland/)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nvidia_h100_20261102

NVIDIA (n.d.). **H100 official specifications**. [Source](https://www.nvidia.com/en-us/data-center/h100/)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nvidia_h200_20261102

NVIDIA (n.d.). **H200 official specifications**. [Source](https://www.nvidia.com/en-us/data-center/h200/)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nvidia_a100_20261102

NVIDIA (n.d.). **A100 official specifications**. [Source](https://www.nvidia.com/en-us/data-center/a100/)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nvidia_l4_20261102

NVIDIA (n.d.). **L4 official specifications**. [Source](https://www.nvidia.com/en-us/data-center/l4/)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nvidia_l40s_20261102

NVIDIA (n.d.). **L40S official specifications**. [Source](https://www.nvidia.com/en-us/data-center/l40s/)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nvidia_dgx_h100_20261102

NVIDIA (n.d.). **DGX H100 user guide hardware specifications**. [Source](https://docs.nvidia.com/dgx/dgxh100-user-guide/introduction-to-dgxh100.html)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_nvidia_dgx_b200_20261102

NVIDIA (n.d.). **DGX B200 user guide hardware specifications**. [Source](https://docs.nvidia.com/dgx/dgxb200-user-guide/introduction-to-dgxb200.html)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_amd_compare_20261102

AMD (n.d.). **ROCm MI300/MI350 architecture comparison**. [Source](https://rocm.docs.amd.com/projects/ai-ecosystem/en/latest/optimization/workload-optimization.html)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_eaton_1000_20261102

Eaton (n.d.). **9PX1000IRT2U exact SKU specifications**. [Source](https://www.eaton.com/gb/en-gb/skuPage.9PX1000IRT2U.html)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_eaton_1500_20261102

Eaton (n.d.). **9PX1500IRT2U exact SKU specifications**. [Source](https://www.eaton.com/gb/en-gb/skuPage.9PX1500IRT2U.html)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_eaton_2200_20261102

Eaton (n.d.). **9PX2200IRT2U exact SKU specifications**. [Source](https://www.eaton.com/gb/en-gb/skuPage.9PX2200IRT2U.html)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_eaton_3000_20261102

Eaton (n.d.). **9PX3000IRT2U exact SKU specifications**. [Source](https://www.eaton.com/gb/en-gb/skuPage.9PX3000IRT2U.html)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### dc_vertiv_xdu_20261102

Vertiv (2021). **Liebert XDU450/1350 guide specifications**. [Source](https://www.vertiv.com/48edce/globalassets/products/thermal-management/high-density-solutions/liebert-xdu-4501350-row-based-coolant-distribution-unit-guide-specifications-sl--70643.pdf)

**Role:** data. Field-level evidence and source-byte SHA-256 in the Data Center catalogue. Original content is not redistributed; public access does not imply an open licence.

**Used by:** `catalogues/data_centers/sources.json`.

### wind_wri_gppd_1_3_0_20261103

World Resources Institute (n.d.). **Global Power Plant Database v1.3.0, complete primary-fuel Wind partition**. [Source](https://github.com/wri/global-power-plant-database/blob/7a91cfbb2a4e272597acbc00506d61fc1ec73b3d/output_database/global_power_plant_database.csv)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Complete original CSV bytes obtained via upstream Git repository; SHA-256 is of CSV bytes; original CSV not redistributed; CC BY 4.0; attribution to WRI; historical baseline with added evidence and review qualifications

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_nordex_n169_5_x_20261103

Nordex (n.d.). **N169/5.X official product page**. [Source](https://www.nordex-online.com/de/product/n169-5-x/)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Web-reader rendered text reviewed; original HTML bytes unavailable, no original-file checksum claimed; Manufacturer copyright; factual specifications only; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_nordex_n193_7_x_20261103

Nordex (n.d.). **N193/7.X official product page**. [Source](https://www.nordex-online.com/en/product/3920436/)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Web-reader rendered text reviewed; original HTML bytes unavailable, no original-file checksum claimed; Manufacturer copyright; factual specifications only; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_nordex_n117_3600_20261103

Nordex (n.d.). **N117/3600 official product page**. [Source](https://www.nordex-online.com/en/product/n117-3600/)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Web-reader rendered text reviewed; original HTML bytes unavailable, no original-file checksum claimed; Manufacturer copyright; factual specifications only; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_nordex_n131_3600_20261103

Nordex (n.d.). **N131/3600 official product page**. [Source](https://www.nordex-online.com/en/product/n131-3600/)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Web-reader rendered text reviewed; original HTML bytes unavailable, no original-file checksum claimed; Manufacturer copyright; factual specifications only; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_nordex_n131_3900_20261103

Nordex (n.d.). **N131/3900 official product page**. [Source](https://www.nordex-online.com/en/product/n131-3900/)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Web-reader rendered text reviewed; original HTML bytes unavailable, no original-file checksum claimed; Manufacturer copyright; factual specifications only; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_nordex_n133_4_8_20261103

Nordex (n.d.). **N133/4.8 official product page**. [Source](https://www.nordex-online.com/en/product/n133-4-8/)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Web-reader rendered text reviewed; original HTML bytes unavailable, no original-file checksum claimed; Manufacturer copyright; factual specifications only; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_nordex_n149_4_x_20261103

Nordex (n.d.). **N149/4.X official product page**. [Source](https://www.nordex-online.com/en/product/n149-4-0-4-5/)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Web-reader rendered text reviewed; original HTML bytes unavailable, no original-file checksum claimed; Manufacturer copyright; factual specifications only; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_nordex_n149_5_x_20261103

Nordex (n.d.). **N149/5.X official product page**. [Source](https://www.nordex-online.com/en/product/n149-5-x/)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Web-reader rendered text reviewed; original HTML bytes unavailable, no original-file checksum claimed; Manufacturer copyright; factual specifications only; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_nordex_n163_5_x_20261103

Nordex (n.d.). **N163/5.X official product page**. [Source](https://www.nordex-online.com/en/product/n163-5-x/)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Web-reader rendered text reviewed; original HTML bytes unavailable, no original-file checksum claimed; Manufacturer copyright; factual specifications only; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_nordex_n163_6_x_20261103

Nordex (n.d.). **N163/6.X official product page**. [Source](https://www.nordex-online.com/en/product/n163-6-x/)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Web-reader rendered text reviewed; original HTML bytes unavailable, no original-file checksum claimed; Manufacturer copyright; factual specifications only; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_nordex_n175_6_x_20261103

Nordex (n.d.). **N175/6.X official product page**. [Source](https://www.nordex-online.com/en/product/n175-6-x/)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Web-reader rendered text reviewed; original HTML bytes unavailable, no original-file checksum claimed; Manufacturer copyright; factual specifications only; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_vestas_v110_2_0_mw_20261103

Vestas (n.d.). **V110-2.0 MW official product page**. [Source](https://www.vestas.com/en/energy-solutions/onshore-wind-turbines/2-mw-platform/V110-2-0-mw)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Web-reader rendered text reviewed; original HTML bytes unavailable, no original-file checksum claimed; Manufacturer copyright; factual specifications only; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_vestas_v120_2_2_mw_20261103

Vestas (n.d.). **V120-2.2 MW official product page**. [Source](https://www.vestas.com/en/energy-solutions/onshore-wind-turbines/2-mw-platform/V120-2-2-MW)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Web-reader rendered text reviewed; original HTML bytes unavailable, no original-file checksum claimed; Manufacturer copyright; factual specifications only; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_vestas_v117_4_2_mw_20261103

Vestas (n.d.). **V117-4.2 MW official product page**. [Source](https://www.vestas.com/en/energy-solutions/onshore-wind-turbines/4-mw-platform/V117-4-2-MW)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Web-reader rendered text reviewed; original HTML bytes unavailable, no original-file checksum claimed; Manufacturer copyright; factual specifications only; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_vestas_v126_3_45_mw_20261103

Vestas (n.d.). **V126-3.45 MW official product page**. [Source](https://www.vestas.com/en/energy-solutions/onshore-wind-turbines/4-mw-platform/V126-3-45-MW)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Web-reader rendered text reviewed; original HTML bytes unavailable, no original-file checksum claimed; Manufacturer copyright; factual specifications only; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_vestas_v136_4_2_mw_20261103

Vestas (n.d.). **V136-4.2 MW official product page**. [Source](https://www.vestas.com/en/energy-solutions/onshore-wind-turbines/4-mw-platform/V136-4-2-MW)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Web-reader rendered text reviewed; original HTML bytes unavailable, no original-file checksum claimed; Manufacturer copyright; factual specifications only; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_vestas_v150_4_2_mw_20261103

Vestas (n.d.). **V150-4.2 MW official product page**. [Source](https://www.vestas.com/en/energy-solutions/onshore-wind-turbines/4-mw-platform/V150-4-2-MW)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Web-reader rendered text reviewed; original HTML bytes unavailable, no original-file checksum claimed; Manufacturer copyright; factual specifications only; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_vestas_v163_4_5_mw_20261103

Vestas (n.d.). **V163-4.5 MW official product page**. [Source](https://www.vestas.com/en/energy-solutions/onshore-wind-turbines/4-mw-platform/V163-4-5-MW)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Web-reader rendered text reviewed; original HTML bytes unavailable, no original-file checksum claimed; Manufacturer copyright; factual specifications only; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_vestas_v136_4_5_mw_20261103

Vestas (n.d.). **V136-4.5 MW official product page**. [Source](https://www.vestas.com/en/energy-solutions/onshore-wind-turbines/4-mw-platform/v136-4-5-mw)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Web-reader rendered text reviewed; original HTML bytes unavailable, no original-file checksum claimed; Manufacturer copyright; factual specifications only; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_vestas_v150_4_5_mw_20261103

Vestas (n.d.). **V150-4.5 MW official product page**. [Source](https://www.vestas.com/en/energy-solutions/onshore-wind-turbines/4-mw-platform/v150-4-5-mw)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Web-reader rendered text reviewed; original HTML bytes unavailable, no original-file checksum claimed; Manufacturer copyright; factual specifications only; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_vestas_v172_7_2_mw_20261103

Vestas (n.d.). **V172-7.2 MW official product page**. [Source](https://www.vestas.com/en/energy-solutions/onshore-wind-turbines/enventus-platform/V172-7-2-MW)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Web-reader rendered text reviewed; original HTML bytes unavailable, no original-file checksum claimed; Manufacturer copyright; factual specifications only; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_vestas_v182_7_2_mw_20261103

Vestas (n.d.). **V182-7.2 MW official product page**. [Source](https://www.vestas.com/en/energy-solutions/onshore-wind-turbines/enventus-platform/V182-7-2-MW)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Web-reader rendered text reviewed; original HTML bytes unavailable, no original-file checksum claimed; Manufacturer copyright; factual specifications only; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_vestas_v150_6_0_mw_20261103

Vestas (n.d.). **V150-6.0 MW official product page**. [Source](https://www.vestas.com/en/energy-solutions/onshore-wind-turbines/enventus-platform/v150-6-0)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Web-reader rendered text reviewed; original HTML bytes unavailable, no original-file checksum claimed; Manufacturer copyright; factual specifications only; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_vestas_v162_6_2_mw_20261103

Vestas (n.d.). **V162-6.2 MW official product page**. [Source](https://www.vestas.com/en/energy-solutions/onshore-wind-turbines/enventus-platform/v162-6-2-mw)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Web-reader rendered text reviewed; original HTML bytes unavailable, no original-file checksum claimed; Manufacturer copyright; factual specifications only; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_vestas_v162_7_2_mw_20261103

Vestas (n.d.). **V162-7.2 MW official product page**. [Source](https://www.vestas.com/en/energy-solutions/onshore-wind-turbines/enventus-platform/v162-7-2-mw)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Web-reader rendered text reviewed; original HTML bytes unavailable, no original-file checksum claimed; Manufacturer copyright; factual specifications only; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_hywind_scotland_20261103

Equinor (n.d.). **Hywind Scotland project facts**. [Source](https://www.equinor.com/energy/hywind-scotland)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Rendered web/PDF text reviewed; original source bytes unavailable; no checksum claimed; Publisher copyright; factual data extracted with attribution; original document not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_hywind_tampen_20261103

Equinor (n.d.). **Hywind Tampen upgraded turbine and unchanged export-system scope**. [Source](https://www.equinor.com/energy/hywind-tampen)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Rendered web/PDF text reviewed; original source bytes unavailable; no checksum claimed; Publisher copyright; factual data extracted with attribution; original document not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_windfloat_20261103

Principle Power (n.d.). **WindFloat Atlantic project facts**. [Source](https://www.principlepower.com/projects/windfloat-atlantic)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Rendered web/PDF text reviewed; original source bytes unavailable; no checksum claimed; Publisher copyright; factual data extracted with attribution; original document not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_v164_84_20261103

MHI Vestas Offshore Wind (2019). **V164-8.4 MW installation at WindFloat Atlantic**. [Source](https://www.vestas.com/en/media/mwow-press-releases/2019/first-turbine-of-windfloat-atlantic-moves-into-position)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Rendered web/PDF text reviewed; original source bytes unavailable; no checksum claimed; Publisher copyright; factual data extracted with attribution; original document not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_kincardine_20261103

Principle Power (n.d.). **Kincardine project and mixed installation scope**. [Source](https://www.principlepower.com/projects/kincardine-offshore-wind-farm)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Rendered web/PDF text reviewed; original source bytes unavailable; no checksum claimed; Publisher copyright; factual data extracted with attribution; original document not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_v164_95_20261103

MHI Vestas Offshore Wind (n.d.). **Five V164-9.5 MW turbines for Kincardine**. [Source](https://www.vestas.com/en/media/mwow-press-releases/2019/kincarde-floating-offshore-v164-9-5-mw)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Rendered web/PDF text reviewed; original source bytes unavailable; no checksum claimed; Publisher copyright; factual data extracted with attribution; original document not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_changhua_open_20261103

Ørsted (2024). **Greater Changhua 1 and 2a inauguration**. [Source](https://orsted.com.au/news/2024/04/chw-1-and-2a-inaguration)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Rendered web/PDF text reviewed; original source bytes unavailable; no checksum claimed; Publisher copyright; factual data extracted with attribution; original document not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_changhua_jacket_20261103

Ørsted (n.d.). **Greater Changhua 1 and 2a jacket foundations**. [Source](https://orsted.tw/en/news/2021/11/first-100-taiwan-made-jacket-foundation)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Rendered web/PDF text reviewed; original source bytes unavailable; no checksum claimed; Publisher copyright; factual data extracted with attribution; original document not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_changhua_1_20261103

Ørsted (n.d.). **Greater Changhua 1 project facts**. [Source](https://orsted.tw/en/renewable-energy-solutions/offshore-wind/our-projects/chw1)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Rendered web/PDF text reviewed; original source bytes unavailable; no checksum claimed; Publisher copyright; factual data extracted with attribution; original document not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_changhua_2a_20261103

Ørsted (n.d.). **Greater Changhua 2a project facts**. [Source](https://orsted.tw/en/renewable-energy-solutions/offshore-wind/our-projects/chw2a)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Rendered web/PDF text reviewed; original source bytes unavailable; no checksum claimed; Publisher copyright; factual data extracted with attribution; original document not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_turkana_20261103

Lake Turkana Wind Power (n.d.). **Project overview and grid/PPA boundary**. [Source](https://ltwp.co.ke/overview-2/)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Rendered web/PDF text reviewed; original source bytes unavailable; no checksum claimed; Publisher copyright; factual data extracted with attribution; original document not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_dumat_award_20261103

Masdar (2019). **Dumat Al Jandal auction award**. [Source](https://masdar.ae/en/news/newsroom/the-edf-renewables-masdar-consortium-awarded-the-dumat-al-jandal-400-mw-wind-project-in-saudi-arabia)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Rendered web/PDF text reviewed; original source bytes unavailable; no checksum claimed; Publisher copyright; factual data extracted with attribution; original document not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_macintyre_20261103

ACCIONA Energía (2026). **MacIntyre operations and commissioning update**. [Source](https://community.acciona.com.au/macintyre/macintyre-wind-farm-operations-update)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Rendered web/PDF text reviewed; original source bytes unavailable; no checksum claimed; Publisher copyright; factual data extracted with attribution; original document not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_kallpa_20261103

ENGIE Chile (2025). **Kallpa commercial operation announcement**. [Source](https://www.engie.cl/entra-en-operacion-nuestro-mayor-parque-de-energia-renovable-en-chile/)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Rendered web/PDF text reviewed; original source bytes unavailable; no checksum claimed; Publisher copyright; factual data extracted with attribution; original document not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_vestas_enventus_case_20261103

Vestas (n.d.). **EnVentus portfolio and Mutkalampi case**. [Source](https://www.vestas.com/en/energy-solutions/onshore-wind-turbines/enventus-platform)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Rendered web/PDF text reviewed; original source bytes unavailable; no checksum claimed; Publisher copyright; factual data extracted with attribution; original document not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_vestas_neosho_20261103

Vestas (n.d.). **2 MW platform Neosho case**. [Source](https://www.vestas.com/en/energy-solutions/onshore-wind-turbines/2-mw-platform)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Rendered web/PDF text reviewed; original source bytes unavailable; no checksum claimed; Publisher copyright; factual data extracted with attribution; original document not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_vestas_v47_r4_20261103

Vestas Wind Systems A/S (2000). **V47 general specification 943111.R4 (school-hosted original manufacturer document)**. [Source](https://sti2d.ecolelamache.org/ressources/EE/premiere/TP/serie%202/Vestas_V47.pdf)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Rendered web/PDF text reviewed; original source bytes unavailable; no checksum claimed; Publisher copyright; factual data extracted with attribution; original document not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_vestas_v236_15_0_mw_20261103

Vestas (n.d.). **V236-15.0 MW official technical specification**. [Source](https://www.vestas.com/en/energy-solutions/offshore-wind-turbines/V236-15MW)

**Role:** data. Field evidence, revision and retrieval date in Wind source registry. Rendered HTML text reviewed; original bytes unavailable; Manufacturer copyright; factual specifications only

**Used by:** `catalogues/wind/sources.json`.

### wind_wri_gbr_crosswalk_2021_20261103

World Resources Institute (n.d.). **WRI historical GBR registry identity crosswalk**. [Source](https://github.com/wri/global-power-plant-database/blob/7a91cfbb2a4e272597acbc00506d61fc1ec73b3d/resources/GBR/matches_GBR.csv)

**Role:** data. Field evidence and revision in Wind source registry. Original CSV bytes obtained and hashed; source bytes not redistributed; CC BY 4.0; WRI attribution; used only for identity reconciliation

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_sg_7_0_170_20261103

Siemens Gamesa (n.d.). **SG 7.0-170 technical specification**. [Source](https://www.siemensgamesa.com/global/en/home/products-and-services/onshore/wind-turbine-sg-7-0-170.html)

**Role:** data. Field evidence and revision in Wind source registry. Original HTML bytes obtained; SHA-256 of original file; bytes not redistributed; Manufacturer copyright; extracted factual specifications; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_sg_5_0_145_20261103

Siemens Gamesa (n.d.). **SG 5.0-145 technical specification**. [Source](https://www.siemensgamesa.com/global/en/home/products-and-services/onshore/wind-turbine-sg-5-0-145.html)

**Role:** data. Field evidence and revision in Wind source registry. Original HTML bytes obtained; SHA-256 of original file; bytes not redistributed; Manufacturer copyright; extracted factual specifications; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_sg_4_4_164_20261103

Siemens Gamesa (n.d.). **SG 5.2-165 technical specification**. [Source](https://www.siemensgamesa.com/global/en/home/products-and-services/onshore/wind-turbine-sg-4-4-164.html)

**Role:** data. Field evidence and revision in Wind source registry. Original HTML bytes obtained; SHA-256 of original file; bytes not redistributed; Manufacturer copyright; extracted factual specifications; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_sg_3_4_132_20261103

Siemens Gamesa (n.d.). **SG 3.4-132 technical specification**. [Source](https://www.siemensgamesa.com/global/en/home/products-and-services/onshore/wind-turbine-sg-3-4-132.html)

**Role:** data. Field evidence and revision in Wind source registry. Original HTML bytes obtained; SHA-256 of original file; bytes not redistributed; Manufacturer copyright; extracted factual specifications; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_sg_3_4_145_20261103

Siemens Gamesa (n.d.). **SG 3.4-145 technical specification**. [Source](https://www.siemensgamesa.com/global/en/home/products-and-services/onshore/wind-turbine-sg-3-4-145.html)

**Role:** data. Field evidence and revision in Wind source registry. Original HTML bytes obtained; SHA-256 of original file; bytes not redistributed; Manufacturer copyright; extracted factual specifications; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_sg_3_2_129_dd_20261103

Siemens Gamesa (n.d.). **SG 3.2-129 technical specification**. [Source](https://www.siemensgamesa.com/global/en/home/products-and-services/onshore/wind-turbine-sg-3-2-129-dd.html)

**Role:** data. Field evidence and revision in Wind source registry. Original HTML bytes obtained; SHA-256 of original file; bytes not redistributed; Manufacturer copyright; extracted factual specifications; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_sg_2_6_114_20261103

Siemens Gamesa (n.d.). **SG 2.6-114 technical specification**. [Source](https://www.siemensgamesa.com/global/en/home/products-and-services/onshore/wind-turbine-sg-2-6-114.html)

**Role:** data. Field evidence and revision in Wind source registry. Original HTML bytes obtained; SHA-256 of original file; bytes not redistributed; Manufacturer copyright; extracted factual specifications; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_sg_onshore_dd_20261103

Siemens Gamesa (n.d.). **Onshore Direct Drive model specification table**. [Source](https://www.siemensgamesa.com/global/en/home/products-and-services/onshore/direct-drive-solutions.html)

**Role:** data. Field evidence and revision in Wind source registry. Original HTML bytes obtained; SHA-256 of original file; bytes not redistributed; Manufacturer copyright; extracted factual specifications; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_sg_8_0_167_dd_20261103

Siemens Gamesa (n.d.). **SG 8.0-167 DD technical specification**. [Source](https://www.siemensgamesa.com/global/en/home/products-and-services/offshore/wind-turbine-sg-8-0-167-dd.html)

**Role:** data. Field evidence and revision in Wind source registry. Original HTML bytes obtained; SHA-256 of original file; bytes not redistributed; Manufacturer copyright; extracted factual specifications; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_sg_11_0_200_dd_20261103

Siemens Gamesa (n.d.). **SG 11-200 technical specification**. [Source](https://www.siemensgamesa.com/global/en/home/products-and-services/offshore/wind-turbine-sg-11-0-200-dd.html)

**Role:** data. Field evidence and revision in Wind source registry. Original HTML bytes obtained; SHA-256 of original file; bytes not redistributed; Manufacturer copyright; extracted factual specifications; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_sg_14_222_dd_20261103

Siemens Gamesa (n.d.). **SG 14-222 technical specification**. [Source](https://www.siemensgamesa.com/global/en/home/products-and-services/offshore/wind-turbine-sg-14-222-dd.html)

**Role:** data. Field evidence and revision in Wind source registry. Original HTML bytes obtained; SHA-256 of original file; bytes not redistributed; Manufacturer copyright; extracted factual specifications; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_sg_14_236_dd_20261103

Siemens Gamesa (n.d.). **SG 14-236 technical specification**. [Source](https://www.siemensgamesa.com/global/en/home/products-and-services/offshore/wind-turbine-sg-14-236-dd.html)

**Role:** data. Field evidence and revision in Wind source registry. Original HTML bytes obtained; SHA-256 of original file; bytes not redistributed; Manufacturer copyright; extracted factual specifications; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_sg_15_236_20261103

Siemens Gamesa (n.d.). **SG 15-236 technical specification**. [Source](https://www.siemensgamesa.com/global/en/home/products-and-services/offshore/wind-turbine-sg-15-236.html)

**Role:** data. Field evidence and revision in Wind source registry. Original HTML bytes obtained; SHA-256 of original file; bytes not redistributed; Manufacturer copyright; extracted factual specifications; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_sg_8_167_apac_2018_20261103

Siemens Gamesa (2018). **SG 8.0-167 DD Asia-Pacific variant and B81 blade announcement**. [Source](https://www.siemensgamesa.com/global/en/home/press-releases/Siemens-Gamesa-tailors-SG-80-167-DD-for-Asia-Pacific-markets.html)

**Role:** data. Field evidence and revision in Wind source registry. Original HTML bytes obtained; SHA-256 of original file; bytes not redistributed; Manufacturer copyright; extracted factual specifications; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_ge_6mw_2026_20261103

GE Vernova (n.d.). **GE Vernova 6mw model technical tables**. [Source](https://www.gevernova.com/wind-power/wind-turbines/onshore-wind-turbines-6mw)

**Role:** data. Field evidence and revision in Wind source registry. Original HTML bytes obtained; SHA-256 of original file; bytes not redistributed; Manufacturer copyright; extracted factual specifications; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_oem_ge_3mw_2026_20261103

GE Vernova (n.d.). **GE Vernova 3mw model technical tables**. [Source](https://www.gevernova.com/wind-power/wind-turbines/onshore-wind-turbines-3mw)

**Role:** data. Field evidence and revision in Wind source registry. Original HTML bytes obtained; SHA-256 of original file; bytes not redistributed; Manufacturer copyright; extracted factual specifications; original text/images not redistributed

**Used by:** `catalogues/wind/sources.json`.

### wind_abb_77cc_reva_2021

ABB (2021). **ACS880-77CC wind turbine converters Hardware manual**. [Source](https://library.e.abb.com/public/9fc16ed5881b4af8ad9f91ca6880be52/EN_ACS880-77CC_HW_A_A4.pdf)

**Role:** data. Rev A, pp87-92; original SHA256 in registry; grid kW, generator kW and kVA separated.

**Used by:** `catalogues/wind/sources.json`.

### discover_dry_solar_revb

Discover Battery (2020). **DRY CELL solar energy storage guide**. [Source](https://assets.discoverbattery.com/documents/02_dry_cell/885_product_literature/gui-dry-cell-solar-energy-storage-product-guide-20200813.pdf)

**Role:** data. Page 1 exact model rows; page 2 chemistry

**Used by:** `catalogues/bess_oem/sources.json`.

### discover_aes_6650_revc

Discover Energy Systems (2026). **AES 42-48-6650 installation and operation manual**. [Source](https://discoverenergysys.com/s4x_files/resources/des-aes-42-48-6650-manual.pdf)

**Role:** data. Tables 3-1 to 3-3, pages 6-7; undated manual year is access year, not publication year

**Used by:** `catalogues/bess_oem/sources.json`.

### discover_rack_revd

Discover Energy Systems (2026). **AES RACKMOUNT installation and operation manual**. [Source](https://discoverbattery.com/s4x_files/resources/des-aes-rackmount-user-manual.pdf)

**Role:** data. Tables 3-1 to 3-3, pages 7-9; undated manual year is access year, not publication year

**Used by:** `catalogues/bess_oem/sources.json`.

### discover_aes_3000_revc

Discover Battery (2026). **44-48-3000 operating manual**. [Source](https://assets.discoverbattery.com/documents/03_aes/805_product_manual/aes-44-48-3000-manual.pdf)

**Role:** data. Section 11 page 13; undated manual year is access year, not publication year

**Used by:** `catalogues/bess_oem/sources.json`.

### ppa_grid_case_studies_202009

Pacific Power Association / SEIAPI (GSES with TAU, EPC and TPL) (2020). **Case Studies from Integrating Renewables into the Grid**. [Source](https://www.ppa.org.fj/wp-content/uploads/2020/10/Case-Studies-Guideline-September-2020.pdf)

**Role:** data. Table 3 pp10-11; Samoa section 3.1.6 p23; Tonga Table 15 p37

**Used by:** `catalogues/bess/sources.json`.

### infratec_cook_four_portfolio

Infratec (2026). **Southern Group Cook Islands Renewable Microgrids**. [Source](https://infratec.co.nz/projects/southern-group-cook-islands-renewable-microgrids/)

**Role:** data. Undated portfolio, access year; four named islands and aggregate discrepancy

**Used by:** `catalogues/bess/sources.json`.

### crown_renewable_g0720

Crown Battery Manufacturing Co. (2020). **Renewable Energy Storage Solutions, SB-CRP-G0720**. [Source](https://www.crownbattery.com/hubfs/Downloads/Renewable-Energy-Batteries.pdf)

**Role:** data. Page 7 exact rows; chemistry groups; energy footnote

**Used by:** `catalogues/bess_oem/sources.json`.

### ingrid_eight_20240213

Ingrid Capacity (2024). **Ingrid Capacity and BW ESS continue large-scale expansion of energy storage in Sweden**. [Source](https://www.ingridcapacity.com/press-releases/ingrid-capacity-and-bw-ess-continue-large-scale-expansion-of-energy-storage-in-sweden-e90ec3b6)

**Role:** data. Named eight-site MW list; grid services paragraphs

**Used by:** `catalogues/bess/sources.json`.

### ingrid_operating_20241010

Ingrid Capacity (2024). **Swedish battery portfolio inauguration**. [Source](https://www.ingridcapacity.com/press-releases/swedens-minister-for-climate-and-the-environment-inaugurates-the-largest-battery-storage-portfolio-in-the-nordics-939df843)

**Role:** data. 14-site portfolio; grid-connected status and joint ownership

**Used by:** `catalogues/bess/sources.json`.

### bw_nordics_portfolio_20261103

BW ESS (2026). **Nordics operating portfolio**. [Source](https://bw-ess.com/projects/nordics)

**Role:** data. Named 14-site list and In operation label; access year for undated portfolio

**Used by:** `catalogues/bess/sources.json`.

### ingrid_mirova_20260923

Ingrid Capacity (2026). **Ingrid Capacity and Mirova Nordic partnership**. [Source](https://www.ingridcapacity.com/news/ingrid-capacity-and-global-investor-mirova-enter-strategic-partnership-for-a-large-scale-bess-portfolio-in-the-nordics)

**Role:** data. Pedersöre and Vaggeryd paragraphs; portfolio investment

**Used by:** `catalogues/bess/sources.json`.

### ingrid_alpiq_20261027

Ingrid Capacity (2026). **Ingrid Capacity and Alpiq offtake partnership**. [Source](https://www.ingridcapacity.com/news/ingrid-capacity-and-alpiq-partner-to-accelerate-battery-storage-deployment-in-the-nordics)

**Role:** data. Pedersöre executed agreement paragraph

**Used by:** `catalogues/bess/sources.json`.

### nepower_haapajarvi_20251112

Nordic Electro Power Oy (2025). **NEPower and Alpiq expand Haapajärvi cooperation**. [Source](https://nepower.fi/news/haapajarvi-september-26-2025-nepower-and-alpiq-have-expanded-their-cooperation-to-build-finlands-largest-125-mw-250-mwh-energy-storage-project)

**Role:** data. EPC scope, 110/33 kV connection, construction and forecast paragraphs

**Used by:** `catalogues/bess/sources.json`.

### merus_valkeakoski_20251030

Merus Power Oyj via STT Info (2025). **Important launch from Merus Power: grid-forming storage**. [Source](https://www.sttinfo.fi/tiedote/71567312/important-launch-from-merus-power-new-energy-storage-technology-in-the-nordics?lang=en)

**Role:** data. Opening paragraph and EPC responsibility paragraph

**Used by:** `catalogues/bess/sources.json`.

### merus_mertaniemi_20250516

Merus Power Oyj via STT Info (2025). **Lappeenranta storage commissioned; EUR15 million delivery**. [Source](https://www.sttinfo.fi/tiedote/71171076/one-of-finlands-largest-energy-storage-facilities-commissioned-in-lappeenranta-merus-powers-eur-15-million-delivery-completed?lang=en&publisherId=69821243)

**Role:** data. Opening, capacity and Mertaniemi paragraphs

**Used by:** `catalogues/bess/sources.json`.

### destia_ypr2_20260304

Destia (2026). **Yllikkälä battery construction and electrical delivery**. [Source](https://destia.fi/en/article/the-largest-battery-storage-in-the-nordics-was-built-with-precise-teamwork/)

**Role:** data. Infrastructure and electrical work; final equipment paragraph

**Used by:** `catalogues/bess/sources.json`.

### epc_fiaga_tender_20261026

Electric Power Corporation Samoa (2026). **SAMEPC12/2026 Fiaga solar and battery tender notice**. [Source](https://www.epc.ws/wp-content/uploads/2026/10/SAMEPC202026TENDERNOTICEFINALCLEANVERSION261026-1.pdf)

**Role:** data. Public notice pages 1-2; excludes NDA-controlled bid documents

**Used by:** `catalogues/bess/sources.json`.

### ingrid_ai4energy_portfolio_20241111

Sara Frimodig; Ingrid Capacity (2024). **AI-driven stokastisk optimering för batterilagringssystem**. [Source](https://energiforsk.se/media/33870/9-sara-frimodig-ingrid-capacity.pdf)

**Role:** data. PDF page 5, printed slide 6: named 2024 portfolio map; cover date with revision caveat in source register

**Used by:** `catalogues/bess/sources.json`.

### rolls_agm_s12_33agm_re

Rolls Battery (2024). **S12-33AGM-RE technical specification**. [Source](https://www.rollsbattery.com/battery/s12-33agm-re/)

**Role:** data. Exact named model: Charge/Discharge, Hour Rate and Specifications tables; printed revision footer

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_agm_s12_55agm_re

Rolls Battery (2024). **S12-55AGM-RE technical specification**. [Source](https://www.rollsbattery.com/battery/s12-55agm-re/)

**Role:** data. Exact named model: Charge/Discharge, Hour Rate and Specifications tables; printed revision footer

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_agm_s12_95agm_re

Rolls Battery (2024). **S12-95AGM-RE technical specification**. [Source](https://www.rollsbattery.com/battery/s12-95agm-re/)

**Role:** data. Exact named model: Charge/Discharge, Hour Rate and Specifications tables; printed revision footer

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_agm_s12_116agm_re

Rolls Battery (2024). **S12-116AGM-RE technical specification**. [Source](https://www.rollsbattery.com/battery/s12-116agm-re/)

**Role:** data. Exact named model: Charge/Discharge, Hour Rate and Specifications tables; printed revision footer

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_agm_s12_128agm_re

Rolls Battery (2024). **S12-128AGM-RE technical specification**. [Source](https://www.rollsbattery.com/battery/s12-128agm-re/)

**Role:** data. Exact named model: Charge/Discharge, Hour Rate and Specifications tables; printed revision footer

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_agm_s12_160agm_re

Rolls Battery (2024). **S12-160AGM-RE technical specification**. [Source](https://www.rollsbattery.com/battery/s12-160agm-re/)

**Role:** data. Exact named model: Charge/Discharge, Hour Rate and Specifications tables; printed revision footer

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_agm_s12_170agm_re

Rolls Battery (2024). **S12-170AGM-RE technical specification**. [Source](https://www.rollsbattery.com/battery/s12-170agm-re/)

**Role:** data. Exact named model: Charge/Discharge, Hour Rate and Specifications tables; printed revision footer

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_agm_s12_180agm_re

Rolls Battery (2023). **S12-180AGM-RE technical specification**. [Source](https://www.rollsbattery.com/battery/s12-180agm-re/)

**Role:** data. Exact named model: Charge/Discharge, Hour Rate and Specifications tables; printed revision footer

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_agm_s12_230agm_re

Rolls Battery (2022). **S12-230AGM-RE technical specification**. [Source](https://www.rollsbattery.com/battery/s12-230agm-re/)

**Role:** data. Exact named model: Charge/Discharge, Hour Rate and Specifications tables; printed revision footer

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_agm_s12_240agm_re

Rolls Battery (2022). **S12-240AGM-RE technical specification**. [Source](https://www.rollsbattery.com/battery/s12-240agm-re/)

**Role:** data. Exact named model: Charge/Discharge, Hour Rate and Specifications tables; printed revision footer

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_agm_s12_290agm_re

Rolls Battery (2022). **S12-290AGM-RE technical specification**. [Source](https://www.rollsbattery.com/battery/s12-290agm-re/)

**Role:** data. Exact named model: Charge/Discharge, Hour Rate and Specifications tables; printed revision footer

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_agm_s12_380agm_re

Rolls Battery (2023). **S12-380AGM-RE technical specification**. [Source](https://www.rollsbattery.com/battery/s12-380agm-re/)

**Role:** data. Exact named model: Charge/Discharge, Hour Rate and Specifications tables; printed revision footer

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_agm_s8_200agm_re

Rolls Battery (2022). **S8-200AGM-RE technical specification**. [Source](https://www.rollsbattery.com/battery/s8-200agm-re/)

**Role:** data. Exact named model: Charge/Discharge, Hour Rate and Specifications tables; printed revision footer

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_agm_s8_210agm_re

Rolls Battery (2021). **S8-210AGM-RE technical specification**. [Source](https://www.rollsbattery.com/battery/s8-210agm-re/)

**Role:** data. Exact named model: Charge/Discharge, Hour Rate and Specifications tables; printed revision footer

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_agm_s8_230agm_re

Rolls Battery (2022). **S8-230AGM-RE technical specification**. [Source](https://www.rollsbattery.com/battery/s8-230agm-re/)

**Role:** data. Exact named model: Charge/Discharge, Hour Rate and Specifications tables; printed revision footer

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_agm_s6_220agm_re

Rolls Battery (2022). **S6-220AGM-RE technical specification**. [Source](https://www.rollsbattery.com/battery/s6-220agm-re/)

**Role:** data. Exact named model: Charge/Discharge, Hour Rate and Specifications tables; printed revision footer

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_agm_s6_245agm_re

Rolls Battery (2022). **S6-245AGM-RE technical specification**. [Source](https://www.rollsbattery.com/battery/s6-245agm-re/)

**Role:** data. Exact named model: Charge/Discharge, Hour Rate and Specifications tables; printed revision footer

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_agm_s6_260agm_re

Rolls Battery (2022). **S6-260AGM-RE technical specification**. [Source](https://www.rollsbattery.com/battery/s6-260agm-re/)

**Role:** data. Exact named model: Charge/Discharge, Hour Rate and Specifications tables; printed revision footer

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_agm_s6_275agm_re

Rolls Battery (2022). **S6-275AGM-RE technical specification**. [Source](https://www.rollsbattery.com/battery/s6-275agm-re/)

**Role:** data. Exact named model: Charge/Discharge, Hour Rate and Specifications tables; printed revision footer

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_agm_s6_250agm_re

Rolls Battery (2022). **S6-250AGM-RE technical specification**. [Source](https://www.rollsbattery.com/battery/s6-250agm-re/)

**Role:** data. Exact named model: Charge/Discharge, Hour Rate and Specifications tables; printed revision footer

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_agm_s6_300agm_re

Rolls Battery (2025). **S6-300AGM-RE technical specification**. [Source](https://www.rollsbattery.com/battery/s6-300agm-re/)

**Role:** data. Exact named model: Charge/Discharge, Hour Rate and Specifications tables; printed revision footer

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_agm_s6_370agm_re

Rolls Battery (2022). **S6-370AGM-RE technical specification**. [Source](https://www.rollsbattery.com/battery/s6-370agm-re/)

**Role:** data. Exact named model: Charge/Discharge, Hour Rate and Specifications tables; printed revision footer

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_agm_s6_460agm_re

Rolls Battery (2024). **S6-460AGM-RE technical specification**. [Source](https://www.rollsbattery.com/battery/s6-460agm-re/)

**Role:** data. Exact named model: Charge/Discharge, Hour Rate and Specifications tables; printed revision footer

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_agm_s2_1275agm_re

Rolls Battery (2019). **S2-1275AGM-RE technical specification**. [Source](https://www.rollsbattery.com/battery/s2-1275agm-re/)

**Role:** data. Exact named model: Charge/Discharge, Hour Rate and Specifications tables; printed revision footer

**Used by:** `catalogues/bess_oem/sources.json`.

### mulilo_bw2_20241224

Mulilo (2024). **BESIPPPP Round 2 awards**. [Source](https://www.mulilo.com/news/2024/mulilo-secures-preferred-bidder-status-in-round-2-of-south-africa-s-besipppp-and-bw7/)

**Role:** data. Five named BESS bullets; lead-member responsibilities; excludes Middlepunt solar

**Used by:** `catalogues/bess/sources.json`.

### mulilo_bw3_20250530

Mulilo (2025). **BESIPPPP Round 3 awards**. [Source](https://www.mulilo.com/news/2025/mulilo-secures-preferred-bidder-status-in-south-africa-s-besipppp-round-3/)

**Role:** data. Four named BESS bullets; contract paragraph

**Used by:** `catalogues/bess/sources.json`.

### mulilo_hartebeesfontein_20260611

Mulilo (2026). **Hartebeesfontein financial close**. [Source](https://www.mulilo.com/news/2026/mulilo-makes-further-inroads-with-hartebeesfontein-bess-financial-close/)

**Role:** data. Capacity, locality, PPA and lenders paragraphs

**Used by:** `catalogues/bess/sources.json`.

### mulilo_vanilla_application

Mulilo / Vanilla Energy Facility (RF) (Pty) Ltd (2026). **Vanilla BESS redacted NERSA application**. [Source](https://www.mulilo.com/media/wntkyjd1/registration-application-form-for-electricity-gen-license_vanilla_redacted.pdf)

**Role:** data. Sections C2-C7 pp7-9; D pp12; F2 p14; not an issued licence; undated: year is access year

**Used by:** `catalogues/bess/sources.json`.

### mulilo_bloemhoek_application

Mulilo / Bloemhoek BESS (Pty) Ltd (2026). **Bloemhoek BESS redacted NERSA application**. [Source](https://www.mulilo.com/media/ljibzk0x/annexure-c-licence-application-form-with-redacted-confidential-information_final.pdf)

**Role:** data. Sections A1/A7 pp2-3; C2-C7 pp7-9; D p12; F2 p14; undated: year is access year

**Used by:** `catalogues/bess/sources.json`.

### edf_oasis_portfolio_20261103

EDF power solutions (2026). **Oasis 1 construction portfolio**. [Source](https://southafrica.edf-powersolutions.com/construction/oasis-1/)

**Role:** data. Three named site capacity bullets; developers, debt and PPA paragraphs; undated: year is access year

**Used by:** `catalogues/bess/sources.json`.

### edf_umoyilanga_portfolio_20261103

EDF power solutions (2026). **Umoyilanga project portfolio**. [Source](https://southafrica.edf-powersolutions.com/construction/umoyilanga/)

**Role:** data. Individual Avondale/Dassiesridge battery MW; technology-specific contractor list; undated: year is access year

**Used by:** `catalogues/bess/sources.json`.

### edf_umoyilanga_provisional_20251212

EDF power solutions (2025). **Umoyilanga provisional COD at Dassiesridge**. [Source](https://southafrica.edf-powersolutions.com/https-southafrica-edf-powersolutions-com-umoyilanga-hybrid-project-reaches-provisional-cod-with-dassiesridge-plant/)

**Role:** data. Opening milestone, 55 MW hybrid NDC, Avondale outstanding work and financial-close paragraphs

**Used by:** `catalogues/bess/sources.json`.

### exilion_portfolio_20261103

Exilion (2026). **Exilion Tuuli Ky portfolio**. [Source](https://exilion.fi/omistukset/exilion-tuuli-ky/)

**Role:** data. SÄHKÖVARASTOT; Viinamäki, Mäntyharju, Tjusterby, Palanutkangas sections; undated: year is access year

**Used by:** `catalogues/bess/sources.json`.

### exilion_mantyharju_20251101

Exilion (2025). **Exilion orders Mäntyharju storage**. [Source](https://exilion.fi/exilion-tilaa-merus-powerilta-sahkovaraston/)

**Role:** data. Opening capacity, Kuortti locality, EUR17m value and developer paragraph

**Used by:** `catalogues/bess/sources.json`.

### merus_mantyharju_trade_20261027

Merus Power Oyj (2026). **Mäntyharju trading and lifecycle service agreement**. [Source](https://www.sttinfo.fi/tiedote/72444702/exilion-starts-using-merus-powers-trading-service-at-its-mantyharju-battery-energy-storage?lang=en&publisherId=69821243)

**Role:** data. Opening agreement and markets paragraphs

**Used by:** `catalogues/bess/sources.json`.

### scatec_kenhardt_close_20220719

Scatec ASA (2022). **Kenhardt construction and financial close**. [Source](https://www.scatec.com/en/scatec-is-starting-construction-of-solar-and-battery-project-in-south-africa-after-reaching-financial-close/)

**Role:** data. Financial-close, funding and EPC/O&M paragraphs

**Used by:** `catalogues/bess/sources.json`.

### exilion_sustainability_2025

Exilion (2026). **Exilion Tuuli Ky sustainability report 2025**. [Source](https://exilion.fi/wp-content/uploads/2026/04/Exilion-Tuuli-Ky-Vastuullisuusraportti-2025-Final-1.pdf)

**Role:** data. Page 3: planning list entries 2 and 5 explicitly say aurinko- ja akkuhanke; construction list Mäntyharju; year is access year, report covers 2025

**Used by:** `catalogues/bess/sources.json`.

### exilion_varevaara_20260701

Exilion (2026). **Exilion signs over 8 million euro battery energy storage deal with Merus Power**. [Source](https://exilion.fi/en/exilion-signs-over-8-million-euro-battery-energy-storage-deal-with-merus-power/)

**Role:** data. Opening three paragraphs: named site, 20 MW / 41 MWh, turnkey order value and autumn 2027 delivery

**Used by:** `catalogues/bess/sources.json`.

### rolls_r2_r2_1000agm

Rolls Battery (2026). **R2-1000AGM exact technical table**. [Source](https://www.rollsbattery.com/battery/r2-1000agm/)

**Role:** data. Exact model heading; charging, hour-rate and physical specifications tables; Rev.#1; undated: year is retrieval year

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_r2_r2_1200agm

Rolls Battery (2026). **R2-1200AGM exact technical table**. [Source](https://www.rollsbattery.com/battery/r2-1200agm/)

**Role:** data. Exact model heading; charging, hour-rate and physical specifications tables; Rev.#1; undated: year is retrieval year

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_r2_r2_1500agm

Rolls Battery (2026). **R2-1500AGM exact technical table**. [Source](https://www.rollsbattery.com/battery/r2-1500agm/)

**Role:** data. Exact model heading; charging, hour-rate and physical specifications tables; Rev.#1; undated: year is retrieval year

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_r2_r2_2000agm

Rolls Battery (2026). **R2-2000AGM exact technical table**. [Source](https://www.rollsbattery.com/battery/r2-2000agm/)

**Role:** data. Exact model heading; charging, hour-rate and physical specifications tables; Rev.#1; undated: year is retrieval year

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_r2_r2_200agm

Rolls Battery (2026). **R2-200AGM exact technical table**. [Source](https://www.rollsbattery.com/battery/r2-200agm/)

**Role:** data. Exact model heading; charging, hour-rate and physical specifications tables; Rev.#1; undated: year is retrieval year

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_r2_r2_250agm

Rolls Battery (2026). **R2-250AGM exact technical table**. [Source](https://www.rollsbattery.com/battery/r2-250agm/)

**Role:** data. Exact model heading; charging, hour-rate and physical specifications tables; Rev.#1; undated: year is retrieval year

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_r2_r2_300agm

Rolls Battery (2026). **R2-300AGM exact technical table**. [Source](https://www.rollsbattery.com/battery/r2-300agm/)

**Role:** data. Exact model heading; charging, hour-rate and physical specifications tables; Rev.#1; undated: year is retrieval year

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_r2_r2_400agm

Rolls Battery (2026). **R2-400AGM exact technical table**. [Source](https://www.rollsbattery.com/battery/r2-400agm/)

**Role:** data. Exact model heading; charging, hour-rate and physical specifications tables; Rev.#1; undated: year is retrieval year

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_r2_r2_500agm

Rolls Battery (2026). **R2-500AGM exact technical table**. [Source](https://www.rollsbattery.com/battery/r2-500agm/)

**Role:** data. Exact model heading; charging, hour-rate and physical specifications tables; Rev.#1; undated: year is retrieval year

**Used by:** `catalogues/bess_oem/sources.json`.

### rolls_r2_r2_800agm

Rolls Battery (2026). **R2-800AGM exact technical table**. [Source](https://www.rollsbattery.com/battery/r2-800agm/)

**Role:** data. Exact model heading; charging, hour-rate and physical specifications tables; Rev.#1; undated: year is retrieval year

**Used by:** `catalogues/bess_oem/sources.json`.

### ingrid_west_20251204

Ingrid Capacity (2025). **Western Sweden six named battery sites**. [Source](https://www.ingridcapacity.com/press-releases/ingrid-in-partnership-with-the-seb-nordic-energy-fund-through-locus-energy-is-strengthening-grid-flexibility-in-western-sweden-contributing-to-a-doubling-of-effekthandel-vast-992c11c5)

**Role:** data. Battery storage that relieves the grid; growing presence section

**Used by:** `catalogues/bess/sources.json`.

### ingrid_rattvik_20250925

Ingrid Capacity (2025). **Rättvik inauguration and operation**. [Source](https://www.ingridcapacity.com/news/ingrid-capacity-and-the-seb-nordic-energy-fund-through-locus-energy-inaugurate-a-new-battery-storage-facility-in-rattvik-to-strengthen-grid-flexibility)

**Role:** data. Opening capacity; project developer explicitly confirms fully operational facility

**Used by:** `catalogues/bess/sources.json`.

### ingrid_nivala_20250527

Ingrid Capacity (2025). **Nivala groundbreaking**. [Source](https://www.ingridcapacity.com/press-releases/ingrid-capacity-in-collaboration-with-seb-nordic-energys-portfolio-company-locus-energy-break-ground-on-one-of-finlands-largest-battery-energy-storage-system-e73e89b7)

**Role:** data. Opening project capacity, location, construction and optimization sections

**Used by:** `catalogues/bess/sources.json`.

### ingrid_varberg_20251218

Ingrid Capacity (2025). **Varberg peak shaving service**. [Source](https://www.ingridcapacity.com/press-releases/ingrid-launches-peak-shaving-products-to-strengthen-local-power-grids-f24eba32)

**Role:** data. Opening 20 MW / 20 MWh and co-owners; Varbergortens Elnät collaboration

**Used by:** `catalogues/bess/sources.json`.

### ingrid_south_20260417

Ingrid Capacity (2026). **Vaggeryd and Horsaryd development**. [Source](https://www.ingridcapacity.com/press-releases/ingrid-doubles-the-size-of-its-battery-storage-portfolio-with-groundbreaking-projects-in-southern-sweden-surpassing-1-gwh-in-capacity-384cb2c0)

**Role:** data. Individual ratings; legally effective permits and planned dates paragraph

**Used by:** `catalogues/bess/sources.json`.

### sinexcel_1250_20261103

Shenzhen Sinexcel Electric Co., Ltd. (2026). **PWS1-1250KTL-H / PWS1-1375KTL-H / PWS1-1500KTL-H Chinese PCS specification**. [Source](https://www.sinexcel.com/uploads/soft/20231102/1698895813.pdf)

**Role:** data. PDF page 2 产品参数 exact model columns; page 1 operating features; undated: year is retrieval year

**Used by:** `catalogues/bess_oem/sources.json`.

### sinexcel_1575_20261103

Shenzhen Sinexcel Electric Co., Ltd. (2026). **PWS1-1575KTL-H / PWS1-1725KTL-H Chinese PCS specification**. [Source](https://www.sinexcel.com/uploads/soft/20231102/1698893815.pdf)

**Role:** data. PDF page 2 产品参数 exact model columns; page 1 operating features; undated: year is retrieval year

**Used by:** `catalogues/bess_oem/sources.json`.

### sinexcel_100m_20261103

Shenzhen Sinexcel Electric Co., Ltd. (2026). **PWS1-100M Chinese PCS specification**. [Source](https://www.sinexcel.com/uploads/soft/20250815/1755250326.pdf)

**Role:** data. PDF page 2 产品参数 exact model columns; page 1 operating features; undated: year is retrieval year

**Used by:** `catalogues/bess_oem/sources.json`.

### sinexcel_125m_20261103

Shenzhen Sinexcel Electric Co., Ltd. (2026). **PWS1-125M Chinese PCS specification**. [Source](https://www.sinexcel.com/uploads/soft/20250815/1755250494.pdf)

**Role:** data. PDF page 2 产品参数 exact model columns; page 1 operating features; undated: year is retrieval year

**Used by:** `catalogues/bess_oem/sources.json`.

### sinexcel_500_20261103

Shenzhen Sinexcel Electric Co., Ltd. (2026). **PWS1-500KTL Chinese PCS specification**. [Source](https://www.sinexcel.com/uploads/soft/20250815/1755246686.pdf)

**Role:** data. PDF page 2 产品参数 exact model columns; page 1 operating features; undated: year is retrieval year

**Used by:** `catalogues/bess_oem/sources.json`.

### sinexcel_630_20261103

Shenzhen Sinexcel Electric Co., Ltd. (2026). **PWS1-630KTL Chinese PCS specification**. [Source](https://www.sinexcel.com/uploads/soft/20250815/1755247013.pdf)

**Role:** data. PDF page 2 产品参数 exact model columns; page 1 operating features; undated: year is retrieval year

**Used by:** `catalogues/bess_oem/sources.json`.

### sinexcel_30p_20261103

Shenzhen Sinexcel Electric Co., Ltd. (2026). **PWS2-30P-CN Chinese PCS specification**. [Source](https://www.sinexcel.com/uploads/soft/20231102/1698895619.pdf)

**Role:** data. PDF page 2 产品参数 exact model columns; page 1 operating features; undated: year is retrieval year

**Used by:** `catalogues/bess_oem/sources.json`.

### sinexcel_215m_20261103

Shenzhen Sinexcel Electric Co., Ltd. (2026). **PWS1-215M-H-O Chinese PCS specification**. [Source](https://www.sinexcel.com/uploads/soft/20250512/1747041466.pdf)

**Role:** data. PDF page 2 产品参数 exact model columns; page 1 operating features; undated: year is retrieval year

**Used by:** `catalogues/bess_oem/sources.json`.

### nz_pipeline_20261103

Electricity Authority New Zealand (2024). **Generation investment pipeline, September 2024**. [Source](https://www.emi.ea.govt.nz/Wholesale/Datasets/Generation/GenerationFleet/Proposed/20240912%20Generation%20investment%20pipeline.csv)

**Role:** data. CSV rows 18, 48 and 116; explicit chemical battery classification; historical planning observations only

**Used by:** `catalogues/bess/sources.json`.

### nz_services_20261103

Electricity Authority New Zealand (2026). **Battery performance in New Zealand**. [Source](https://www.ea.govt.nz/news/eye-on-electricity/eye-on-electricity-battery-performance-in-new-zealand/)

**Role:** data. 19 May 2026 header; energy versus instantaneous reserve dispatch through 28 April 2026

**Used by:** `catalogues/bess/sources.json`.

### nzce_masterton_20261103

NZ Clean Energy (2026). **Masterton Solar & Energy Storage Project**. [Source](https://www.nzcleanenergy.nz/projects/masterton-solar-energy-storage)

**Role:** data. Project information, location/grid and current status sections; undated: year is retrieval year

**Used by:** `catalogues/bess/sources.json`.

### nzce_darfield_20261103

NZ Clean Energy (2026). **Darfield Solar & Energy Storage Project**. [Source](https://www.nzcleanenergy.nz/projects/darfield-solar-energy-storage)

**Role:** data. Project information, location/grid and current status sections; undated: year is retrieval year

**Used by:** `catalogues/bess/sources.json`.

### nzce_dannevirke_20261103

NZ Clean Energy (2026). **Dannevirke Solar & Energy Storage Project**. [Source](https://www.nzcleanenergy.nz/projects/dannevirke-solar-energy-storage)

**Role:** data. Project information, location/grid and current status sections; undated: year is retrieval year

**Used by:** `catalogues/bess/sources.json`.

### contact_1_20261103

Contact Energy (2026). **Glenbrook Ohurua Battery 1**. [Source](https://contact.co.nz/about-us/our-story/our-generation-and-power-sites/battery/glenbrook-ohurua-battery)

**Role:** data. Commissioned, operating narrative and partners sections; undated: year is retrieval year

**Used by:** `catalogues/bess/sources.json`.

### contact_2_20261103

Contact Energy (2026). **Glenbrook Ohurua Battery 2**. [Source](https://contact.co.nz/about-us/sustainability/our-projects/battery/glenbrook-ohurua-battery-2)

**Role:** data. Status, capacity, technology and grid connection table; separate adjacent Battery 1; undated: year is retrieval year

**Used by:** `catalogues/bess/sources.json`.

### contact_news_20261103

Contact Energy (2026). **Glenbrook Ohurua Battery opening**. [Source](https://contact.co.nz/investor-centre/news/2026/glenbrook-ohurua-battery)

**Role:** data. 21 May 2026 announcement: separate Battery 1 and Battery 2 investment and equipment

**Used by:** `catalogues/bess/sources.json`.

### mistralai_2026_timestral

Mistral AI (2026). **Timestral: standalone probabilistic time-series forecasting inference**. [Source](https://github.com/mistralai/timestral/tree/a534bdbd244d64f3d9d743f46c7bf6fc330ed4ff)

**Role:** software. Official model inference wrapped through an optional local connector. No retraining or reimplementation of the neural architecture. Inference code: Apache-2.0; separately distributed checkpoint weights: Modified MIT. Gallery replays pinned real Timestral-5M inference on attributed EIA CISO generation and offers explicit live inference. One historical holdout with unknown pretraining overlap is not operational validation or proof of superior accuracy.

**Used by:** `methods/src/energy_methods/timestral.py`, `analysis/src/energy_analysis/timestral_case.py`, `examples/connectors/plot_timestral_forecast.py`, `scripts/prepare_timestral_example.py`, `docs/timestral.md`, `analysis/src/energy_analysis/forecast_benchmark.py`, `scripts/prepare_forecast_benchmark.py`, `examples/analysis/plot_forecast_model_benchmark.py`, `docs/forecast-benchmark.md`.

### nrcan_wind_turbine_database_2026

Natural Resources Canada (2026). **Canadian Wind Turbine Database**. [Source](https://open.canada.ca/data/en/dataset/79fdad93-9025-49ad-ba16-c26d718cc070)

**Role:** data_source. Inventory snapshot with source project/turbine attributes; not independent evidence of current operation.

**Used by:** `data-retrieval/src/energy_data_retrieval/wind_catalogue/canada.py`.

### vindbrukskollen_open_inventory_2026

Länsstyrelserna; Swedish Energy Agency (2026). **Vindbrukskollen land-based project areas and wind turbines**. [Source](https://www.energimyndigheten.se/energisystem-och-analys/el--och-varmeproduktion/vindkraft/vindbrukskollen/)

**Role:** data source. CC0 registry data. Complete OMRID < 0500 query partition; original response checksums and raw status semantics retained.

**Used by:** `catalogues/wind`, `docs/wind-catalogue.md`.

### vensys_technical_sheets_2025

VENSYS Energy AG (2025). **VENSYS current product technical data sheets, July–August 2025**. [Source](https://www.vensys.de/en/media)

**Role:** data source. Seven exact OEM configurations; p2 tables; original PDF checksums in Wind source registry. AEP tables are not instantaneous power curves.

**Used by:** `catalogues/wind`, `docs/wind-catalogue.md`.

### mastr_full_export_20261103

Bundesnetzagentur (2026). **Marktstammdatenregister Gesamtdatenexport 26.2**. [Source](https://www.marktstammdatenregister.de/MaStR/Datendownload)

**Role:** data source. Original wind XML extracted with HTTP byte ranges. Full ZIP checksum unavailable. Complete Schleswig-Holstein partition reviewed; accepted park groups retain unresolved capacity scope.

**Used by:** `catalogues/wind`, `docs/wind-catalogue.md`, `data-retrieval/src/energy_data_retrieval/wind_catalogue/mastr.py`.

### enercon_technical_sheets_202608

ENERCON (2026). **E-138 EP3 E3, E-160 EP5 E3, E-175 EP5 E1/E2 technical data**. [Source](https://www.enercon.de/en/news-media/publications)

**Role:** data source. August2026 revision; original three PDF hashes and p2/p4 locators retained. E2 power options and mode-dependent acoustic observations not collapsed into unqualified scalars.

**Used by:** `catalogues/wind`, `docs/wind-catalogue.md`.

### enercon_yield_modes_e82_e103

ENERCON (n.d.). **Yield Optimized Mode for E-82 E2 and E-103 EP2**. [Source](https://www.enercon.de/en/news-media/publications)

**Role:** data source. Undated three-slide original presentation; site-specific load study required. Exact optional modes, no original numerical curve tables.

**Used by:** `catalogues/wind`, `docs/wind-catalogue.md`.

### winergy_hybriddrive_pzfg

Winergy (n.d.). **HybridDrive PZFG2456/PZFG2535 technical table**. [Source](https://www.winergy-group.com/en/medias/product-brochure-hybriddrive-winergy.pdf?context=bWFzdGVyfGRvY3VtZW50c3wyNDQ2ODV8YXBwbGljYXRpb24vcGRmfGRvY3VtZW50cy9oYzgvaGExLzg4MTUwODEwNjI0MzAucGRmfDQwYzc2MWQwY2I2NDcwODlhMzVmM2NhM2MxMjUxNzA2MDBlNGRiNzE4NDVhY2I4NWQ0ZWFjOGU4YjA2MDAzNWY)

**Role:** data source. Original PDF p2 table; historical two-stage integrated gearbox-generator models. PDF creation metadata is not publication date. No turbine compatibility inferred.

**Used by:** `catalogues/wind`, `docs/wind-catalogue.md`.

### ngc_wind_yaw_pitch_2022

NGC (n.d.). **Wind All New Products; SYW/SPT exact type tables**. [Source](https://ngcamericas.com/wp-content/uploads/2022/02/Wind-All-New-Products.pdf)

**Role:** data source. Regional archive PDF; original checksum retained. Physical pages9/10, printed08/09 exact SYW/SPT types. Generic platform limits not transferred.

**Used by:** `catalogues/wind`, `docs/wind-catalogue.md`.

### bonfiglioli_wind_r05_2

Bonfiglioli (n.d.). **Solutions for WIND;700TW yaw/pitch models**. [Source](https://www.bonfiglioli.com/_default_upload_bucket/TR_CAT_WIND_STD_ENG_R05_2.pdf)

**Role:** data source. R05_2 original PDF p14; application-specific reference peak torque. No turbine compatibility or T/TW identity inferred.

**Used by:** `catalogues/wind`, `docs/wind-catalogue.md`.

### abb_wind_converters_2018_reva

ABB (2018). **ABB wind converters ACS880 wind turbine converters**. [Source](https://library.e.abb.com/public/25e19011bbcd4f2782f4b2c8271072af/Wind_converter_catalog_3AUA0000231755_RevA_EN.pdf)

**Role:** data source. 3AUA0000231755 Rev A 20 September2018, p10 full15-row rating table; typical kW distinguished from kVA; twin cabinet units retained.

**Used by:** `catalogues/wind`, `docs/wind-catalogue.md`.

### bonfiglioli_acu_vec521r6

Bonfiglioli (2024). **ACTIVE CUBE Operating Instructions**. [Source](https://www.bonfiglioli.in/_default_upload_bucket/ACUx01_Operating%20Instructions_VEC521R6.pdf)

**Role:** data source. VEC521R6 printed06/24 pp32,35–43: exact ACU201 sizes1–4 and ACU401 sizes1–7; motor ratings, frequency/phase limits and time-qualified overloads. Wind-series application from WIND R05_2 p13; no exact turbine compatibility. Page44 has derating diagrams, not a size8 table.

**Used by:** `catalogues/wind`, `docs/wind-catalogue.md`.

### chen_guestrin_2016_xgboost

Chen, Tianqi; Guestrin, Carlos (2016). **XGBoost: A Scalable Tree Boosting System**. Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, 785-794. [DOI: 10.1145/2939672.2939785](https://doi.org/10.1145/2939672.2939785)

**Role:** implemented. XGBoost software lineage. CPU histogram trees, fixed hyperparameters and chronological forecasting are repository choices.

**Used by:** `methods/src/energy_methods/xgboost.py`, `analysis/src/energy_analysis/forecast_benchmark.py`, `examples/analysis/plot_forecast_model_benchmark.py`, `docs/forecast-benchmark.md`.

### xgboost_python_api

XGBoost contributors (2026). **XGBoost Python API Reference**. [Source](https://xgboost.readthedocs.io/en/stable/python/python_api.html)

**Role:** implemented. Official XGBRegressor and native JSON model serialization documentation; access-year metadata, not a paper publication date.

**Used by:** `methods/src/energy_methods/xgboost.py`.

### jonkman_2009_nrel_5mw

Jonkman, Jason; Butterfield, Sandy; Musial, Walt; Scott, George (2009). **Definition of a 5-MW Reference Wind Turbine for Offshore System Development**. [Source](https://www.nrel.gov/docs/fy09osti/38060.pdf)

**Role:** background. NREL/TP-500-38060. Source of reference cut-in/rated/cut-out speeds 3/11.4/25 m/s only. The repository cubic interpolation and fitted farm scale do not reproduce the NREL aerodynamic curve or identify the actual farm equipment.

**Used by:** `methods/src/energy_methods/wind_physics.py`, `analysis/src/energy_analysis/forecast_benchmark.py`, `examples/analysis/plot_forecast_model_benchmark.py`, `docs/forecast-benchmark.md`.

### ons_wind_curtailment

Operador Nacional do Sistema Elétrico (2026). **ONS Restrições de operação por constrained-off de usinas eólicas: detalhamento por usina**. [Source](https://dados.ons.org.br/dataset/restricao_coff_eolica_detail)

**Role:** data. Native half-hour mean generation, wind resource and restriction/quality flags. Access-year metadata. The September 2026 dictionary prints m3/s for a wind-speed column; the benchmark explicitly assumes its numerical readings are m/s, retaining this source inconsistency in provenance. No estimated/reference generation is substituted for measured power.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/ons/client.py`, `scripts/prepare_forecast_benchmark.py`, `analysis/src/energy_analysis/forecast_benchmark.py`, `examples/analysis/plot_forecast_model_benchmark.py`, `docs/forecast-benchmark.md`.

### kaaya_2021_uncertainties

Kaaya, Ismail; Ascencio-Vásquez, Julián; Weiss, Karl-Anders; Topič, Marko (2021). **Assessment of uncertainties and variations in PV modules degradation rates and lifetime predictions using physical models**. Solar Energy, 218, 354-367. [DOI: 10.1016/j.solener.2021.01.071](https://doi.org/10.1016/j.solener.2021.01.071)

**Role:** implemented. Verified from the user-supplied article PDF (SHA-256 dc16f0c30c75ac87e9755421985153173c2efd1c55d870ecc6734f37c528fb80). Table 2 reliability curves, Eqs. 1 and 3–17, Sections 2.5/3.4 preprocessing and Eqs. 19–20 metrics are implemented with explicit conventions. Table 5 omits A_N and C_N; the printed 273+delta-T term and incomplete rate-unit conventions are documented separately from the existing 2019 mapping model. Published-table checks and synthetic/scenario analyses are not reproduction or field validation of the original measurement study. Gamma is held fixed in wear-out fitting because only gamma/k is identifiable.

**Used by:** `methods/src/energy_methods/pv_reliability.py`, `methods/src/energy_methods/degradation_uncertainty.py`, `methods/src/energy_methods/pv_stress_weather.py`, `methods/src/energy_methods/degradation_preprocessing.py`, `analysis/src/energy_analysis/degradation_uncertainty/study.py`, `docs/degradation-uncertainty.md`, `examples/analysis/plot_degradation_uncertainty.py`.

### bonfiglioli_acu_r04_0

Bonfiglioli (n.d.). **ACTIVE CUBE product catalogue**. [Source](https://www.bonfiglioli.com/_default_upload_bucket/VE_CAT_ACU_STD_ENG_R04_0.pdf)

**Role:** data source. R04_0 pp12–14 nomenclature and pp24–25 complete ACUx10 frame7/8 rating tables. Publication date unknown; PDF metadata is not publication evidence. Mechanical options remain nested; ACUx01 not relabelled.

**Used by:** `catalogues/wind`, `docs/wind-catalogue.md`.

### ozkalay_2025_three_decades

Özkalay, Ebrar; Quest, Hugo; Gassner, Anika; Virtuani, Alessandro; Eder, Gabriele C.; Vorstoffel, Stefanie; Buerhop-Lutz, Claudia; Friesen, Gabi; Ballif, Christophe; Burri, Matthias; Bucher, Christof (2025). **Three decades, three climates: environmental and material impacts on the long-term reliability of photovoltaic modules**. EES Solar, 1(4), 580–599. [DOI: 10.1039/D4EL00040D](https://doi.org/10.1039/D4EL00040D)

**Role:** data. Published online 30 May 2025. Swiss multi-decade field evidence. Analysis uses attributed numerical extracts from the pre-publication Zenodo v1.0.0 archive, preserving date/count/rate differences from the final article. No 50-year measurement or fleet survival estimate is claimed.

**Used by:** `analysis/src/energy_analysis/pv_lifetime/study.py`, `examples/analysis/plot_pv_lifetime_50_years.py`, `docs/pv-lifetime.md`.

### quest_2024_swiss_data

Quest, Hugo; Özkalay, Ebrar; Gassner, Anika (2024). **Three Decades, Three Climates: Environmental and Material Impacts on the Long-Term Reliability of Photovoltaic Modules - Shared data and results**. [DOI: 10.5281/zenodo.14524159](https://doi.org/10.5281/zenodo.14524159)

**Role:** data. Version 1.0.0, 19 December 2024. Archive downloaded 3 November 2026 and verified against published MD5 b19a01369228f92769096a5a45965b1f. PM cell values and system PLRs extracted with addresses and hashes. Dataset CC-BY-4.0 confirmed from Zenodo API metadata; no license inferred from the article.

**Used by:** `analysis/src/energy_analysis/pv_lifetime/study.py`, `examples/analysis/plot_pv_lifetime_50_years.py`, `docs/pv-lifetime.md`, `scripts/prepare_pv_lifetime_data.py`.

### ravindrababu_2026_maple

Ravindrababu, Suraj; Hädrich, Ingrid; Paetzold, Ulrich W.; Gebhardt, Paul (2026). **Development of a modular approach for photovoltaic module lifetime and reliability estimation**. Energy Reports, 15, 109323. [DOI: 10.1016/j.egyr.2026.109323](https://doi.org/10.1016/j.egyr.2026.109323)

**Role:** implemented. Online 25 April 2026. Independent implementation of selected MAPLE MSM equations: independent mode product (8), sigmoid power (10), equivalent-time update (13; discussion 24–28). Rates are reciprocal years; shapes and stress histories in the example are hypothetical. Full CFM, dependent modes and multi-scale modelling are not implemented here.

**Used by:** `methods/src/energy_methods/pv_lifetime.py`, `analysis/src/energy_analysis/pv_lifetime/study.py`, `examples/analysis/plot_pv_lifetime_50_years.py`, `docs/pv-lifetime.md`.

### cabo_santiago_sal_2150

Cabeolica SA / Advisian (2025). **Cabeolica expansion components1–3 Santiago and Sal NTS**. [Source](https://cabeolica.com/wp-content/uploads/2025/02/NTS_Simplified_ESIA_Sal_and_Santiago_Final_251601.pdf)

**Role:** data. Primary source for bounded factual catalogue observations; source-specific reuse assessment, revision, locators and checksums are in the catalogue source register. No source licence inferred from this bibliographic entry.

**Used by:** `catalogues/bess/sources.json`.

### cabo_boa_2150

Cabeolica SA / Advisian (2025). **Cabeolica expansion component5 Boa Vista NTS**. [Source](https://cabeolica.com/wp-content/uploads/2025/03/NTS_Simplified_ESIA_BESS_Boa_Vista.pdf)

**Role:** data. Primary source for bounded factual catalogue observations; source-specific reuse assessment, revision, locators and checksums are in the catalogue source register. No source licence inferred from this bibliographic entry.

**Used by:** `catalogues/bess/sources.json`.

### cabo_vicente_2150

Cabeolica SA / Advisian (2025). **Cabeolica expansion component4 São Vicente NTS**. [Source](https://cabeolica.com/wp-content/uploads/2025/03/NTS_Simplified_ESIA_BESS_Sao_Vicente.pdf)

**Role:** data. Primary source for bounded factual catalogue observations; source-specific reuse assessment, revision, locators and checksums are in the catalogue source register. No source licence inferred from this bibliographic entry.

**Used by:** `catalogues/bess/sources.json`.

### gov_vicente_2150

Governo de Cabo Verde (2026). **Inauguração do sistema de armazenamento em São Vicente**. [Source](https://www.governo.cv/primeiro-ministro-inaugura-sistema-de-armazenamento-de-energia-em-baterias-em-s-vicente/)

**Role:** data. Primary source for bounded factual catalogue observations; source-specific reuse assessment, revision, locators and checksums are in the catalogue source register. No source licence inferred from this bibliographic entry.

**Used by:** `catalogues/bess/sources.json`.

### gov_boa_2150

Governo de Cabo Verde (2026). **Inauguração do sistema de armazenamento na Boa Vista**. [Source](https://www.governo.cv/primeiro-ministro-na-boa-vista-inaugurado-o-sistema-de-armazenamento-de-energia-em-baterias/)

**Role:** data. Primary source for bounded factual catalogue observations; source-specific reuse assessment, revision, locators and checksums are in the catalogue source register. No source licence inferred from this bibliographic entry.

**Used by:** `catalogues/bess/sources.json`.

### gov_sal_2150

Governo de Cabo Verde (2026). **Inauguração no Sal da extensão da central e sistema de baterias**. [Source](https://www.governo.cv/primeiro-ministro-inaugura-no-sal-a-extensao-da-central-electrica-e-o-sistema-de-armazenamento-de-energia-em-baterias/)

**Role:** data. Primary source for bounded factual catalogue observations; source-specific reuse assessment, revision, locators and checksums are in the catalogue source register. No source licence inferred from this bibliographic entry.

**Used by:** `catalogues/bess/sources.json`.

### gov_santiago_2150

Governo de Cabo Verde (2025). **Governo em Ação Novembro2025 No29**. [Source](https://www.governo.cv/wp-content/uploads/2025/12/newsletter_novembro_2025_n29_suple_especial_oe2026.pdf)

**Role:** data. Primary source for bounded factual catalogue observations; source-specific reuse assessment, revision, locators and checksums are in the catalogue source register. No source licence inferred from this bibliographic entry.

**Used by:** `catalogues/bess/sources.json`.

### bsl_s205_2150

BSLBATT / BSL NEW ENERGY TECHNOLOGY CO., LTD (n.d.). **ESS-GRID S205 Station Series**. [Source](https://bslbatt.com/wp-content/uploads/2025/05/ESS-GRID-S205-250508.pdf)

**Role:** data. Primary source for bounded factual catalogue observations; source-specific reuse assessment, revision, locators and checksums are in the catalogue source register. No source licence inferred from this bibliographic entry.

**Used by:** `catalogues/bess_oem/sources.json`.

### bsl_s314_2150

BSLBATT / BSL NEW ENERGY TECHNOLOGY CO., LTD (n.d.). **ESS-GRID S314 Station Series**. [Source](https://bslbatt.com/wp-content/uploads/2025/10/ESS-GRID-S314-250508.pdf)

**Role:** data. Primary source for bounded factual catalogue observations; source-specific reuse assessment, revision, locators and checksums are in the catalogue source register. No source licence inferred from this bibliographic entry.

**Used by:** `catalogues/bess_oem/sources.json`.

### bsl_cabinet_2150

BSLBATT / BSL NEW ENERGY TECHNOLOGY CO., LTD (n.d.). **ESS-GRID Cabinet Series C225/C241**. [Source](https://bslbatt.com/wp-content/uploads/ESS-GRID-Cabinet-Series-260915.pdf)

**Role:** data. Primary source for bounded factual catalogue observations; source-specific reuse assessment, revision, locators and checksums are in the catalogue source register. No source licence inferred from this bibliographic entry.

**Used by:** `catalogues/bess_oem/sources.json`.

### bsl_rack_2150

BSLBATT / BSL NEW ENERGY TECHNOLOGY CO., LTD (n.d.). **B-LFP48 Series 100E/200E/300E Rack Batteries**. [Source](https://bslbatt.com/wp-content/uploads/2025/05/机架合集（黑）-250329.pdf)

**Role:** data. Primary source for bounded factual catalogue observations; source-specific reuse assessment, revision, locators and checksums are in the catalogue source register. No source licence inferred from this bibliographic entry.

**Used by:** `catalogues/bess_oem/sources.json`.

### bsl_cabinet_web_2150

BSLBATT (n.d.). **ESS-GRID Cabinet C200/C215/C225/C241 product page**. [Source](https://bslbatt.com/ess-grid-c200-c215-c225-c241-industry-ess-cabinet-series/)

**Role:** data. Primary source for bounded factual catalogue observations; source-specific reuse assessment, revision, locators and checksums are in the catalogue source register. No source licence inferred from this bibliographic entry.

**Used by:** `catalogues/bess_oem/sources.json`.

### bsl_ci_warranty_v12_2150

BSL NEW ENERGY TECHNOLOGY CO., LTD (n.d.). **BSLBATT ESS Limited Warranty Letter V1.2**. [Source](https://bslbatt.com/wp-content/uploads/ESS-GRID-system-Limited-warranty-V1.2.pdf)

**Role:** data. Printed V1.2; no publication date stated. Conditional cabinet warranty, not installation eligibility or a universal ten-year system guarantee.

**Used by:** `catalogues/bess_oem/sources.json`.

### bsl_residential_2026_2348

BSLBATT (2026). **BSLBATT Residential Energy Storage Products 2026**. [Source](https://bslbatt.com/wp-content/uploads/BSLBATT-Residential-Energy-Storage-Products-2026.pdf)

**Role:** data. Year in catalogue filename; selected exact tables PDF pp12,13,17,18. Manufacturer claims, not independently certified performance. Publication day/revision unverified.

**Used by:** `catalogues/bess_oem/sources.json`.

### cabeolica_annual2024_2348

Cabeólica S.A. (2025). **Cabeolica Annual Report 2024**. [Source](https://cabeolica.com/wp-content/uploads/2025/09/RC_2024_EN.pdf)

**Role:** data. 2024 reporting year; board report dated27March2025; public reader, direct403. Programme milestones are not site construction/COD or finance allocations.

**Used by:** `catalogues/bess/sources.json`.

### sie_sie002_20261104

Superintendencia de Electricidad, República Dominicana (2026). **Resolución SIE-002-2026-RCD — Parque Solar Mirasol SAEB**. [Source](https://sie.gob.do/wp-content/uploads/2026/01/SIE-002-2026-RCD.pdf)

**Role:** data. PDF pp1–3,8–13; technical report pp9–10; original decision incomplete; Public official resolution; site terms retain copyright and do not grant open bulk reuse. Bounded attributed factual review only; no full text, personal data or PDF redistribution.

**Used by:** `catalogues/bess/sources.json`.

### sie_sie002corrected_20261104

Superintendencia de Electricidad, República Dominicana (2026). **Acto rectificativo y Resolución SIE-002-2026-RCD — Mirasol SAEB**. [Source](https://sie.gob.do/wp-content/uploads/2026/03/SIE-002-2026-RCD-3.pdf)

**Role:** data. PDF p1 correction notice; pp2–15 corrected resolution; decision printed pp11–14 (PDF12–15). Original number/date retained; March URL is not issue date.; Public official resolution; site terms retain copyright and do not grant open bulk reuse. Bounded attributed factual review only; no full text, personal data or PDF redistribution.

**Used by:** `catalogues/bess/sources.json`.

### sie_sie004_20261104

Superintendencia de Electricidad, República Dominicana (2026). **Resolución SIE-004-2026-RCD — Planta Santanasol SAEB**. [Source](https://sie.gob.do/wp-content/uploads/2026/01/SIE-004-2026-RCD.pdf)

**Role:** data. PDF pp1–3,10–13,17; printed page numbers match PDF; Public official resolution; site terms retain copyright and do not grant open bulk reuse. Bounded attributed factual review only; no full text, personal data or PDF redistribution.

**Used by:** `catalogues/bess/sources.json`.

### sie_sie006_20261104

Superintendencia de Electricidad, República Dominicana (2026). **Resolución SIE-006-2026-RCD — Peravia Solar I SAEB**. [Source](https://sie.gob.do/wp-content/uploads/2026/01/SIE-006-2026-RCD.pdf)

**Role:** data. PDF pp1–3,9–12,15; cover/year2026 and signed date15January2026; footer says2025; Public official resolution; site terms retain copyright and do not grant open bulk reuse. Bounded attributed factual review only; no full text, personal data or PDF redistribution.

**Used by:** `catalogues/bess/sources.json`.

### sie_haina_20261104

Superintendencia de Electricidad, República Dominicana (2026). **Resolución SIE-114-2026-AMEM — BESS-Haina installation authorization**. [Source](https://sie.gob.do/wp-content/uploads/2026/09/SIE-114-2026-AMEM.pdf)

**Role:** data. PDF pp1,6–12; authorized ratingsp10, commissioning prerequisitespp9,11–12; technical paragraphp7 misnames asset; Public official resolution; site terms retain copyright and do not grant open bulk reuse. Bounded attributed factual review only; no full text, personal data or PDF redistribution.

**Used by:** `catalogues/bess/sources.json`.

### bsl_warranty_v141_20261104

BSLBATT / Huizhou BSL NEW ENERGY Technology Co., Ltd. (n.d.). **BSLBATT Lithium Battery Limited Warranty Letter V1.41**. [Source](https://bslbatt.com/wp-content/uploads/BSLBATT-ESS-Battery-Warranty-V1.41.pdf)

**Role:** data. PDF pp1–3 applicable types, clauses1.1–1.3 and Table1.0; pp4–5 coverage; pp7–10 exclusions, registration and AppendixA; Copyright retained; bounded factual model/condition observations from OEM public document. No full-document redistribution or open bulk-reuse licence inferred.

**Used by:** `catalogues/bess_oem/sources.json`.

### bonfiglioli_br_vec501_r0

Bonfiglioli Vectron (n.d.). **Braking Resistors**. [Source](https://www.bonfiglioli.com/international/usefulDocuments/braking-resistors-manual_inverters---servo-drives_brakings-resistor_eng_r00_0.pdf)

**Role:** data source. COD.VEC501R0 physical pp2,4 complete11type tables. Publication date unknown. Legacy observations retained separately from current ACU catalogue; dimension units unspecified.

**Used by:** `catalogues/wind`, `docs/wind-catalogue.md`.

### enercon_e82_e2_201908

ENERCON (2019). **Technical data E-82 E2**. [Source](https://assets-global.website-files.com/64c38ca9b1a2e59bd5b7d64a/65685f63f40d9a2bf64b4e59_ENERCON%20E-82%20EP2%20E2%20en.pdf)

**Role:** data source. 08/2019 single-page OEM table. Nominal and hub-height options retained; annual yield graph not ingested as power curve.

**Used by:** `catalogues/wind`, `docs/wind-catalogue.md`.

### abb_wind_system_2020_revc

ABB (2020). **ACS880-77LC/-87LC/-87CC wind turbine converters system description**. [Source](https://library.e.abb.com/public/2b4b8597d93940f59ee37087613d9518/EN_ACS880-77LC_87LC_87CC_SD_C_A4.pdf)

**Role:** data source. 3AXD50000022022 Rev C, effective 2020-04-27; pp13–14,24–25 system interfaces and explicit optional NETA-21. Series-level conditions do not replace historical exact ratings.

**Used by:** `catalogues/wind`, `docs/wind-catalogue.md`.

### abb_neta21_2026_revq

ABB (2026). **NETA-21 remote monitoring tool user manual**. [Source](https://search.abb.com/library/Download.aspx?DocumentID=3AUA0000096939&LanguageCode=en&DocumentPartId=1&Action=Launch)

**Role:** data source. 3AUA0000096939 Rev Q effective2026-09-18; joint NETA/NEXA technical table pp225–226. Conflicting temperature endpoints retained; no whole-product UL certification inferred.

**Used by:** `catalogues/wind`, `docs/wind-catalogue.md`.
