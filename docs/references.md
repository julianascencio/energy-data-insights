# Scientific references and attribution

## Main scientific reference

**Julián Andrés Ascencio Vásquez (2021). _Modelling and worldwide assessment
of performance and aging of photovoltaic modules and systems_. Doctoral
dissertation, University of Ljubljana, Faculty of Electrical Engineering.**
[Permanent national-library record](https://www.dlib.si/details/URN:NBN:SI:DOC-TMG3QFI9).

The thesis is the preferred citation in the root `CITATION.cff` and appears
first in analysis report bibliographies. Its institutional catalogue identifier
is **COBISS 77808131**. The university records the defense on **21 September 2021**:
[LPVO thesis catalogue](https://lpvo.fe.uni-lj.si/en/education/final-theses/completed/)
and [defense announcement](https://lpvo.fe.uni-lj.si/en/2021/).
The later national-library upload date is not the thesis publication year.
Marko Topič is the advisor, not a thesis coauthor. No thesis DOI is asserted.

## How to cite work using this repository

1. Cite the thesis as the main scientific reference.
2. Cite the individual algorithm papers, software and data sources actually used
   by your analysis. A primary thesis citation does not replace their attribution.
3. Cite the repository URL and exact Git commit, and retain the input hashes,
   parameters, software versions and source-access timestamps in your manifest.

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

**Role:** primary. Primary scientific reference for this repository. University of Ljubljana catalogue: COBISS 77808131; national-library URN:NBN:SI:DOC-TMG3QFI9. Defended 21 September 2021. Marko Topič is the advisor, not a coauthor. No thesis DOI has been verified. Citation does not claim that every thesis chapter is implemented. CCYA implementation follows sections 7.5.1–7.5.3 (pp. 150–164), with equations 3.6/3.8 for thermal context. The institutional full text is https://repozitorij.uni-lj.si/Dokument.php?id=148326&lang=eng. Explicit choices for monthly centroid scaling, incremental temperature normalization, nonexceedance quantiles and cumulative ratio versus signed gain are documented in docs/ccya.md; no numerical reproduction of Bolzano is claimed. Soiling and snow indicators follow Eqs. 3.2–3.4 (pp. 49–51) and Tables 6.6–6.7 (pp. 135–136), with explicit equality/low-domain conventions and alternative example data documented in docs/soiling-snow.md.

**Used by:** `README.md`, `methods/README.md`, `analysis/README.md`, `methods/src/energy_methods/degradation.py`, `docs/degradation.md`, `methods/src/energy_methods/ccya.py`, `docs/ccya.md`, `analysis/examples/ccya/README.md`, `analysis/src/energy_analysis/ccya_case/pipeline.py`, `examples/analysis/plot_kgpv_worldwide.py`, `docs/kgpv.md`, `methods/src/energy_methods/weather_risk.py`, `methods/src/energy_methods/weather_risk_mapping.py`, `docs/soiling-snow.md`, `examples/analysis/plot_soiling_snow_risk.py`, `examples/analysis/plot_country_risk.py`, `examples/connectors/plot_generation_coverage.py`, `docs/worldwide-generation.md`, `scripts/prepare_connector_station_coverage.py`, `examples/connectors/data/generation_coverage_stations.csv`, `examples/connectors/data/generation_coverage_stations_provenance.json`, `analysis/src/energy_analysis/canary_kgpv/pipeline.py`, `examples/analysis/plot_kgpv_canary.py`, `docs/kgpv-canary.md`, `analysis/src/energy_analysis/chile_kgpv/pipeline.py`, `examples/analysis/plot_kgpv_chile.py`, `docs/kgpv-chile.md`, `methods/src/energy_methods/climate_zones.py`, `methods/src/energy_methods/jrc_climate.py`, `methods/src/energy_methods/ml21.py`, `methods/src/energy_methods/pvcz.py`, `docs/climate-comparison.md`.

### ascencio_vasquez_2021_tdp

Ascencio-Vásquez, Julián; Osorio-Aravena, Juan Carlos; Brecl, Kristijan; Muñoz-Cerón, Emilio; Topič, Marko (2021). **Typical Daily Profiles, a novel approach for photovoltaics performance assessment: Case study on large-scale systems in Chile**. Solar Energy, 225, 357-374. [DOI: 10.1016/j.solener.2021.07.007](https://doi.org/10.1016/j.solener.2021.07.007)

**Role:** implemented. Source of the Typical Daily Profiles approach and original Chile fleet case study. Project qualification rules, missing-data handling, fixed-clock pooling and unavailable historical capacity gates are documented adaptations, not a claim of byte-identical author software.

**Used by:** `methods/src/energy_methods/tdp.py`.

### ascencio_vasquez_2020_modelling

Ascencio-Vásquez, Julián; Bevc, Jakob; Reba, Kristjan; Brecl, Kristijan; Jankovec, Marko; Topič, Marko (2020). **Advanced PV Performance Modelling Based on Different Levels of Irradiance Data Accuracy**. Energies, 13(9), 2166. [DOI: 10.3390/en13092166](https://doi.org/10.3390/en13092166)

**Role:** implemented. Source of the two-stage irradiance/power acceptance band and low/medium/high irradiance evidence levels. The repository states its interpretation of inconsistent printed roughness/distance expressions. Chronological validation and monotonic LightGBM settings are project adaptations.

**Used by:** `methods/src/energy_methods/acceptance_band.py`, `methods/src/energy_methods/lightgbm.py`.

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

**Used by:** `methods/src/energy_methods/lightgbm.py`.

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

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/ons/client.py`, `data-retrieval/src/energy_data_retrieval/sources/ons/README.md`, `examples/connectors/plot_generation_ons.py`, `docs/worldwide-generation.md`, `examples/connectors/plot_generation_coverage.py`, `examples/connectors/data/generation_coverage_catalogue.json`.

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
