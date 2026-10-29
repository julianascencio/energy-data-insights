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
| Acceptance bands | Ascencio-Vásquez et al. (2020); documented roughness/distance interpretation. |
| Effective POA | Reda-Andreas, Erbs, Hay-Davies, Spencer and pvlib. |
| Single-axis geometry | Anderson-Mikofski and Lorenzo et al. through pvlib; inferred geometry. |
| LightGBM | Ke et al. and LightGBM documentation; project chronology and monotonic settings. |
| Physical response | Stark-Parker BVLS through SciPy; repository-specific PV basis. |
| Operational screening | IEC TS 63019 context; no conformity or certified availability claim. |
| Generation and weather | Selected CEN and weather sources identified by run provenance. |

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

**Role:** primary. Primary scientific reference for this repository. University of Ljubljana catalogue: COBISS 77808131; national-library URN:NBN:SI:DOC-TMG3QFI9. Defended 21 September 2021. Marko Topič is the advisor, not a coauthor. No thesis DOI has been verified. Citation does not claim that every thesis chapter is implemented.

**Used by:** `README.md`, `methods/README.md`, `analysis/README.md`.

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

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/cen`.

### cen_infotecnica_registry

Coordinador Eléctrico Nacional (n.d.). **Infotécnica: registro público de centrales**. [Source](https://api-infotecnica.coordinador.cl/v1/centrales-sin-filtrar/extended/)

**Role:** data. Public plant registry source. Reported maximum power is retained without silently treating it as verified AC or DC nameplate capacity.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/cen`.

### cen_historical_reports

Coordinador Eléctrico Nacional (n.d.). **Reportes y estadísticas: generación del Sistema Eléctrico Nacional**. [Source](https://www.coordinador.cl/reportes-y-estadisticas/)

**Role:** data. Provider catalogue for historical generation and Qlik exports. Every imported export requires its specific source URL/file, timestamp conventions and hash; this general catalogue does not certify the completeness of a supplied export.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/cen`, `data-retrieval/README.md`.

### cen_qlik_generation

Coordinador Eléctrico Nacional (n.d.). **Generación real descargable (Qlik)**. [Source](https://qap-prd.coordinador.cl/ext/extensions/mashup_Generacion_Real_Descargable/mashup_Generacion_Real_Descargable.html)

**Role:** data. Source interface for preserved generation exports. The adapter imports user-supplied CSV/XLSX/ZIP exports with an explicit contract; citation does not imply anonymous live access, successful authorization or an implemented Qlik session client.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/cen/history.py`, `data-retrieval/README.md`.

### hersbach_2020_era5

Hersbach, Hans; Bell, Bill; Berrisford, Paul; Hirahara, Shoji; Horányi, András; Muñoz‐Sabater, Joaquín; Nicolas, Julien; Peubey, Carole; Radu, Raluca; Schepers, Dinand; Simmons, Adrian; Soci, Cornel; Abdalla, Saleh; Abellan, Xavier; Balsamo, Gianpaolo; Bechtold, Peter; Biavati, Gionata; Bidlot, Jean; Bonavita, Massimo; De Chiara, Giovanna; Dahlgren, Per; Dee, Dick; Diamantakis, Michail; Dragani, Rossana; Flemming, Johannes; Forbes, Richard; Fuentes, Manuel; Geer, Alan; Haimberger, Leo; Healy, Sean; Hogan, Robin J.; Hólm, Elías; Janisková, Marta; Keeley, Sarah; Laloyaux, Patrick; Lopez, Philippe; Lupu, Cristina; Radnoti, Gabor; de Rosnay, Patricia; Rozum, Iryna; Vamborg, Freja; Villaume, Sebastien; Thépaut, Jean‐Noël (2020). **The ERA5 global reanalysis**. Quarterly Journal of the Royal Meteorological Society, 146(730), 1999-2049. [DOI: 10.1002/qj.3803](https://doi.org/10.1002/qj.3803)

**Role:** data. Scientific description of ERA5 reanalysis. Reanalysis is modelled weather and cannot be relabelled as a measured station. Cite the actual dataset and acquisition wrapper separately.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/open_meteo`, `data-retrieval/src/energy_data_retrieval/sources/earthmover_era5`.

### era5_single_levels

Copernicus Climate Change Service (C3S) Climate Data Store (CDS) (2023). **ERA5 hourly data on single levels from 1940 to present**. [DOI: 10.24381/cds.adbb2d47](https://doi.org/10.24381/cds.adbb2d47)

**Role:** data. Single-level dataset citation as recommended by the Earthmover source catalogue. Record the actual retrieval date and selected data vintage; do not use the metadata-verification date as a data-access date.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/open_meteo`, `data-retrieval/src/energy_data_retrieval/sources/earthmover_era5`.

### earthmover_icechunk_era5

Earthmover (n.d.). **Icechunk ERA5**. [Source](https://registry.opendata.aws/earthmover-era5/)

**Role:** data. Optional native ERA5 source. Cite Earthmover, the C3S single-level dataset, and underlying ERA5 research; acquisition must retain the pinned snapshot and actual access date. Catalogue metadata verification does not establish current snapshot coverage or a new data acquisition.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/earthmover_era5`.

### open_meteo_historical_weather

Open-Meteo (n.d.). **Historical Weather API**. [Source](https://open-meteo.com/en/docs/historical-weather-api)

**Role:** data. Optional ERA5 weather wrapper. Cite the underlying ERA5 dataset/paper and retain the explicitly requested product, grid cell and interval semantics; this is not measured irradiance.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/open_meteo`.

### open_meteo_historical_forecast

Open-Meteo (n.d.). **Historical Forecast API**. [Source](https://open-meteo.com/en/docs/historical-forecast-api)

**Role:** data. Optional archive of numerical forecasts. The adapter explicitly selects ECMWF IFS; do not describe these records as ERA5 or observations. Record model, vintage and interval semantics from provenance.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/open_meteo`.

### open_meteo_variable_definitions

Open-Meteo (n.d.). **Weather Forecast API: hourly variable definitions**. [Source](https://open-meteo.com/en/docs)

**Role:** data. Provider definitions for preceding-hour radiation/gust variables and instantaneous temperature/wind. Archive-specific variable definitions take priority where products differ.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/open_meteo`, `data-retrieval/README.md`.

### eyring_2016_cmip6

Eyring, V.; Bony, S.; Meehl, G. A.; Senior, C. A.; Stevens, B.; Stouffer, R. J.; Taylor, K. E. (2016). **Overview of the Coupled Model Intercomparison Project Phase 6 (CMIP6) experimental design and organization**. Geoscientific Model Development, 9, 1937-1958. [DOI: 10.5194/gmd-9-1937-2016](https://doi.org/10.5194/gmd-9-1937-2016)

**Role:** data. Scientific design of the CMIP6 archive accessed by the retrieval provider. The repository retrieves published climate-model output; it does not implement or run the contributing climate models. Cite each selected model/experiment dataset and its version separately using the preserved provider citation links.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/cmip6`, `data-retrieval/README.md`.

### oneill_2016_scenariomip

O'Neill, B. C.; Tebaldi, C.; van Vuuren, D. P.; Eyring, V.; Friedlingstein, P.; Hurtt, G.; Knutti, R.; Kriegler, E.; Lamarque, J.-F.; Lowe, J.; Meehl, G. A.; Moss, R.; Riahi, K.; Sanderson, B. M. (2016). **The Scenario Model Intercomparison Project (ScenarioMIP) for CMIP6**. Geoscientific Model Development, 9, 3461-3482. [DOI: 10.5194/gmd-9-3461-2016](https://doi.org/10.5194/gmd-9-3461-2016)

**Role:** data. Scientific description of the SSP scenario experiments selectable by the CMIP6 retrieval provider. Scenario simulations are conditional climate projections, not observations or deterministic weather forecasts. Their availability and coverage are established by each saved catalogue result, not by this paper citation.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/cmip6`, `data-retrieval/README.md`.

### esgf_stac_access

Earth System Grid Federation (ESGF) contributors (n.d.). **ESGF PyClient documentation: STAC migration and data-access services**. [Source](https://esgf-pyclient.readthedocs.io/en/latest/)

**Role:** data. Official access guidance identifies the east and west ESGF STAC discovery services and deprecates the legacy Solr search interface. This provider uses direct HTTP requests; this reference does not mean esgf-pyclient is a runtime dependency. Preserve the actual endpoint, search criteria, resolved dataset version, asset URLs and access time in acquisition provenance.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/cmip6`.

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

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/cmip6`.

### cmip6_terms_of_use

Program for Climate Model Diagnosis and Intercomparison (PCMDI) (2022). **CMIP6: Terms of Use, version 6.2**. [Source](https://pcmdi.llnl.gov/CMIP6/TermsOfUse/TermsOfUse6-2.html)

**Role:** data. Document version 12 October 2022. Defines acknowledgement and data-citation requirements and directs users to the official per-model license inventory, which supersedes older file-header restrictions. Preserve source metadata and consult that inventory for data reuse; a catalogue-record license alone does not establish the license of the underlying model output or of this repository.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/cmip6`.

### driemel_2018_bsrn

Driemel, Amelie; Augustine, John; Behrens, Klaus; Colle, Sergio; Cox, Christopher; Cuevas-Agulló, Emilio; Denn, Fred M.; Duprat, Thierry; Fukuda, Masato; Grobe, Hannes; Haeffelin, Martial; Hodges, Gary; Hyett, Nicole; Ijima, Osamu; Kallis, Ain; Knap, Wouter; Kustov, Vasilii; Long, Charles N.; Longenecker, David; Lupi, Angelo; Maturilli, Marion; Mimouni, Mohamed; Ntsangwane, Lucky; Ogihara, Hiroyuki; Olano, Xabier; Olefs, Marc; Omori, Masao; Passamani, Lance; Pereira, Enio Bueno; Schmithüsen, Holger; Schumacher, Stefanie; Sieger, Rainer; Tamlyn, Jonathan; Vogt, Roland; Vuilleumier, Laurent; Xia, Xiangao; Ohmura, Atsumu; König-Langlo, Gert (2018). **Baseline Surface Radiation Network (BSRN): structure and data description (1992–2017)**. Earth System Science Data, 10(3), 1491-1501. [DOI: 10.5194/essd-10-1491-2018](https://doi.org/10.5194/essd-10-1491-2018)

**Role:** data. Canonical scientific description of the BSRN radiation archive. The provider retrieves station observations through PANGAEA and preserves their published identity and provenance. Cite the actual station collection and monthly dataset DOIs in addition to this network paper. Archive checks do not establish that a downloaded value passed every subsequent scientific quality check or represents a particular PV site.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/bsrn`.

### bsrn_pangaea_access

World Radiation Monitoring Center, Alfred Wegener Institute (n.d.). **Baseline Surface Radiation Network: Data retrieval via PANGAEA**. [Source](https://bsrn.awi.de/data/data-retrieval-via-pangaea/)

**Role:** data. Official source guidance for UTC timestamps, station/month datasets and logical records. The adapter targets basic radiation records; other record types require their own explicit contract. AWI states that resulting detailed BSRN quality-check flags are not archived. PANGAEA value annotations, when present, are preserved separately and do not establish completed scientific quality control. Preserve each dataset's citation, station metadata and BSRN data-release conditions.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/bsrn`.

### pangaea_data_access

PANGAEA Data Publisher for Earth & Environmental Science (n.d.). **PANGAEA Data Access and Reuse**. [Source](https://wiki.pangaea.de/wiki/Data_Access_and_Reuse)

**Role:** data. Documents DOI-based programmatic access, tab-delimited exports, structured metadata and citation links. PANGAEA describes these as standard HTTP access rather than a separate proprietary data API. The adapter retains the original citation/license text and source hashes; a DOI identifies the selected dataset and does not imply unrestricted access or a license for all PANGAEA holdings.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/bsrn`.

### menne_2023_ghcnh

Menne, Matthew J.; Noone, Simon; Casey, Nancy W.; Dunn, Robert H.; McNeill, Shelley; Kantor, Diana; Thorne, Peter W.; Orcutt, Karen; Cunningham, Sam; Risavi, Nicholas (2023). **Global Historical Climatology Network-Hourly (GHCNh)**. NOAA National Centers for Environmental Information. [DOI: 10.25921/jp3d-3v19](https://doi.org/10.25921/jp3d-3v19)

**Role:** data. Official NOAA dataset citation, including all ten credited authors. Identify the actual station/year subset, product version and access date when citing an acquisition. The adapter retrieves GHCNh station reports and retains measurement, quality, source and report codes; the word hourly does not convert every reported value into a one-hour mean or supply missing irradiance observations.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/noaa`.

### noaa_ghcnh_documentation

NOAA National Centers for Environmental Information (2026). **Global Historical Climatology Network hourly (GHCNh): Documentation, version 1.1.0**. [Source](https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly/doc/ghcnh_DOCUMENTATION.pdf)

**Role:** data. Official documentation updated 10 March 2026. Defines native station/year PSV access, station identifiers, units and measurement/quality/report/source codes. GHCNh version 1.1.0 supersedes previous versions and replaces the legacy ISD product. Preserve source fields and actual report timestamps; transformations into analysis intervals require a separately stated aggregation policy.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/noaa`.

### noaa_isd_service_transition

NOAA National Centers for Environmental Information (2026). **Service Location Change for Integrated Surface Data (Global Hourly)**. [Source](https://www.nesdis.noaa.gov/news/service-location-change-integrated-surface-data-global-hourly)

**Role:** background. Official notice dated 23 June 2026 explains why new acquisition uses GHCNh. It records that legacy ISD updates stopped after 24 August 2025 and announces retirement of NCEI's ISD FTP/HTTPS distribution, while legacy files remain available through NODD. This repository's NOAA provider does not implement a legacy ISD fallback.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/noaa`.

### pangaea_quality_flags

PANGAEA Data Publisher for Earth & Environmental Science (n.d.). **PANGAEA Quality flag definitions**. [Source](https://wiki.pangaea.de/wiki/Quality_flag)

**Role:** data. Defines numeric-value annotations for questionable, invalid, unknown, individually defined and inequality-qualified observations. The BSRN parser preserves the annotation and original field rather than silently treating an annotated value as unqualified. PANGAEA syntax alone does not certify detailed BSRN scientific quality control.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/bsrn`.

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

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/aemet/client.py`, `data-retrieval/README.md`.

### aemet_opendata_access

Agencia Estatal de Meteorología (AEMET) (n.d.). **AEMET OpenData: Frequently asked questions and two-stage data access**. [Source](https://opendata.aemet.es/centrodedescargas/faqs)

**Role:** data. Official documentation of API estado responses and temporary datos/metadatos links, which expire after about five minutes. Field metadata contains source units, definitions, attribution and usage conditions. Canonical JSON snapshots retain data values and metadata; they do not claim to preserve exact HTTP encoding. Key expiry follows the newer published access notices rather than older FAQ PDF statements.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/aemet/client.py`, `data-retrieval/README.md`.

### aemet_observation_guidance

Agencia Estatal de Meteorología (AEMET) (n.d.). **Interpretación: Hoy y últimos días**. [Source](https://www.aemet.es/es/eltiempo/observacion/ultimosdatos/ayuda)

**Role:** data. Official interpretation guidance distinguishing instantaneous temperature, wind averaging intervals, gusts and accumulated precipitation. The public website and API may display different units; this implementation checks returned API field metadata before assigning physical-unit columns. Native reporting dates and variable-specific aggregation periods are retained without inferring a uniform hourly observation contract.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/aemet/client.py`, `data-retrieval/README.md`.

### aemet_opendata_key_policy

Agencia Estatal de Meteorología (AEMET) (2026). **AEMET OpenData: API access and key-expiration notices**. [Source](https://opendata.aemet.es/centrodedescargas/novedades)

**Role:** background. Current 2026 notices describe retirement of keys issued without expiration and three-month validity for newly issued keys. The source reads AEMET_API_KEY from the environment, sends it through the documented private HTTP header and excludes credentials from output, provenance and public caches.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/aemet/client.py`, `data-retrieval/README.md`.

### dwd_2024_hourly_solar

Deutscher Wetterdienst (2024). **Hourly station observations of solar incoming (total/diffuse) and longwave downward radiation for Germany**. [Source](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/solar/)

**Role:** data. DWD CDC dataset version v24.03; published 29 March 2024. Dataset identifier urn:x-wmo:md:de.dwd.cdc::obsgermany-climate-hourly-solar. CC BY 4.0. Native hourly radiation energy remains in J/cm², and acquisition hashes record the separately changing station-archive vintage.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/dwd/client.py`, `data-retrieval/README.md`.

### dwd_hourly_solar_documentation

Deutscher Wetterdienst (2024). **DWD CDC dataset description: Hourly station observations of solar incoming (total/diffuse) and longwave downward radiation for Germany**. [Source](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/solar/DESCRIPTION_obsgermany_climate_hourly_solar_en.pdf)

**Role:** data. Official version v24.03, published 29 March 2024 and last edited 6 May 2024. Defines native fields, hourly energy sums, missing sentinel -999, QN quality-procedure codes, true-solar-time labels, station metadata and CC BY 4.0. The adapter also verifies per-archive parameter metadata specifying UTC and WOZ; interval boundaries and irradiance flux are not inferred.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/dwd/client.py`, `data-retrieval/README.md`.

### augustine_2000_surfrad

Augustine, John A.; DeLuisi, John J.; Long, Charles N. (2000). **SURFRAD—A National Surface Radiation Budget Network for Atmospheric Research**. Bulletin of the American Meteorological Society, 81(10), 2341-2357. [DOI: 10.1175/1520-0477(2000)081<2341:sansrb>2.3.co;2](https://doi.org/10.1175/1520-0477%282000%29081%3C2341%3Asansrb%3E2.3.co%3B2)

**Role:** data. Scientific network reference explicitly requested by NOAA in README_SURFRAD for publications using SURFRAD data. Author names and bibliographic fields verified against publisher-deposited Crossref metadata. Cite the actual station/day subset and access date as well. Page range follows Crossref and the NOAA README (2341–2357); the current AMS web display ends at 2358.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/surfrad/client.py`, `data-retrieval/README.md`.

### augustine_2005_surfrad

Augustine, John A.; Hodges, Gary B.; Cornwall, Christopher R.; Michalsky, Joseph J.; Medina, Carlos I. (2005). **An Update on SURFRAD—The GCOS Surface Radiation Budget Network for the Continental United States**. Journal of Atmospheric and Oceanic Technology, 22(10), 1460-1472. [DOI: 10.1175/jtech1806.1](https://doi.org/10.1175/jtech1806.1)

**Role:** data. Scientific network reference explicitly requested by NOAA in README_SURFRAD for publications using SURFRAD data. Author names and bibliographic fields verified against publisher-deposited Crossref metadata. Cite the actual station/day subset and access date as well. Describes the seven-station network and its BSRN affiliation; this affiliation creates potential overlap between archive routes.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/surfrad/client.py`, `data-retrieval/README.md`.

### noaa_surfrad_documentation

NOAA Global Monitoring Laboratory (n.d.). **Description of SURFRAD Daily Data Files**. [Source](https://gml.noaa.gov/aftp/data/radiation/surfrad/bon/README_SURFRAD.txt)

**Role:** data. Official 48-field native daily format, station filename aliases, UTC interval-end labels, three-minute averages before 1 January 2009 and one-minute averages thereafter. Defines missing sentinel -9999.9, native quality codes, physical units including UVB in mW/m² and instrument temperatures in Kelvin, and CC0-1.0 licensing. The provider preserves original flags and source values without additional filtering or correction.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/surfrad/client.py`, `data-retrieval/README.md`.

### noaa_surfrad_stations

NOAA Global Monitoring Laboratory (n.d.). **SURFRAD Site Information**. [Source](https://gml.noaa.gov/grad/surfrad/sitepage.html)

**Role:** data. Official current station catalogue. The seven SURFRAD archive aliases are bon, tbl, dra, fpk, gwn, psu and sxf; Bondville has site code BND but file prefix bon. The separately linked ARM Southern Great Plains site is outside this provider. Current catalogue positions do not override historical file-header coordinates or elevations.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/surfrad/client.py`, `data-retrieval/README.md`.

### noaa_surfrad_overview

NOAA Global Monitoring Laboratory (n.d.). **SURFRAD Overview: Surface Radiation Budget Monitoring**. [Source](https://gml.noaa.gov/grad/surfrad/overview.html)

**Role:** data. Official network scope, radiation and meteorological instrumentation, calibration context and BSRN participation. SURFRAD and BSRN archive acquisitions must not be treated as independent observations without checking station/time/variable/vintage overlap.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/surfrad/client.py`, `data-retrieval/README.md`.

### noaa_surfrad_archive

NOAA Global Monitoring Laboratory (n.d.). **NOAA GML SURFRAD daily radiation and meteorological observations**. [Source](https://gml.noaa.gov/aftp/data/radiation/surfrad/)

**Role:** data. Public GML station/year daily text archive actually used by this provider. Cite the selected station, UTC days and acquisition date; preserve its native files, quality flags and hashes. CC0-1.0 with NOAA attribution and fair-use guidance. This is not a claim to retrieve the separately published NCEI NetCDF, QCRAD, or realtime products.

**Used by:** `data-retrieval/src/energy_data_retrieval/sources/surfrad/client.py`, `data-retrieval/README.md`.
