# BESS launch research — 1 November 2026

Initial scope: **37 named projects, 22 countries, 30 primary sources**. Research prioritizes broad geographic coverage and auditable identity over a claim of completeness.

## Country coverage

| Country (ISO alpha-3) | Projects |
| --- | ---: |
| AUS | 4 |
| BRA | 1 |
| CAN | 1 |
| CHL | 2 |
| CHN | 1 |
| DEU | 2 |
| ESP | 1 |
| FIN | 2 |
| FRA | 1 |
| GBR | 4 |
| IND | 1 |
| JPN | 1 |
| LTU | 4 |
| NLD | 1 |
| NZL | 3 |
| PHL | 1 |
| PRT | 1 |
| SAU | 2 |
| SGP | 1 |
| SWE | 1 |
| USA | 1 |
| ZAF | 1 |

## Status observations

| Last sourced status | Records |
| --- | ---: |
| operational | 33 |
| partially_operational | 1 |
| under_construction | 2 |
| unknown | 1 |

These are historical source observations with explicit dates, not a real-time
operating inventory. Most sources are owner, regulator, government, research
institute or equipment supplier publications. Search excerpts are identified as
such in the registry. No geocoding or assumed equipment specifications are used.

## Material decisions

- **Edwards & Sanborn:** retain 3,287 MWh; the 1,300 MW connection limit is not
  battery output. BESS MW stays null. The EPC's 864/875 MWdc solar discrepancy
  is noted but excluded from the BESS ratings.
- **Collie:** one project row, with 219+341 MW and 877+1,363 MWh explicitly
  aggregated from two stages. No overlapping phase rows or Synergy project.
- **Hazelwood:** operating first-stage 150 MW / 150 MWh remains the numeric
  scope; unfinished 150 MW / 600 MWh extension is phase metadata only.
- **Coya / Tamaya:** public owner descriptions give 139 / 68 MW; financial
  disclosures give 140.97 / 76 MW. Both observations remain, marked needs_review.
  The discrepancy is not resolved by assuming AC/DC or rounding.
- **Jurong Island:** current Sembcorp page states 326 MWh; EMA's 2023 opening
  release stated 285 MWh. Expansion or rating basis is unresolved. Neither
  the values nor the component sites are double-counted; BESS MW is unknown.
- **Dalian:** only the 100 MW / 400 MWh first grid-connected phase; planned
  200 MW / 800 MWh full build is excluded. Formal grid-connected generation is documented; exact commercial COD is unknown.
- **Bisha:** the supplier's black-start test demonstrates a test milestone and
  500 MW / 2,000 MWh rating. Lifecycle status remains unknown; a test alone
  does not establish commissioning or commercial operation.
- **Yllikkälä / Lithuania / Hamm-Neurath:** separate named installations or
  substations are separate project rows; aggregate fleet totals are excluded.
- **Arañuelo / Alcoutim / Rajnandgaon / Red Sea:** solar MW never substitutes
  for BESS MW. Alcoutim's later four-system expansion is outside the first row.

## Known gaps and next import work

No country is complete. Project coordinates, OEM/model details, usable energy,
round-trip efficiency, capex and exact COD are sparse. This batch does not claim
to import EIA, UK REPD, AEMO, Chile CEN or any complete national storage registry.
National bulk adapters should be added with pinned source snapshots, tested
battery-only filtering, project/generator/phase reconciliation and source terms.

Next priorities are broader China/USA/Australia coverage, Chile project registry
reconciliation, European national registries, and additional African, Asian and
Latin American markets. BESS equipment tables are not yet part of version 1.
No recurring automation has been created or changed by this contribution.

## Primary-source register

Dates are publication dates only when established, otherwise unknown. Full
retrieval timestamps and field-level source mappings are in the canonical data.
Source rights remain with the respective publishers. Notes below are factual
summaries; original source articles and PDFs are not bundled.

| ID | Publisher | Publication date | Evidence |
| --- | --- | --- | --- |

| `neoen_au_2024` | Neoen | 2024-10-24 | [Collie Battery Stage 1 begins operating and delivering grid reliability services](https://neoen.com/en/news/2024/neoens-collie-battery-stage-1-begins-operating-and-delivering-grid-reliability-services-in-western-australia/) — Lists operating Hornsdale at 150 MW / 193.5 MWh and Victorian Big Battery at 300 MW / 450 MWh. |
| `nzea_collie` | Net Zero Economy Authority | Unknown / undated | [Neoen Collie Battery](https://www.nzea.gov.au/neoen-collie-battery) — Two operating stages: 219 MW / 877 MWh from October 2024, and 341 MW / 1363 MWh from July 2025. Total computed as the sum of these non-overlapping stages. |
| `engie_hazelwood` | ENGIE Australia | Unknown / undated | [Hazelwood Battery](https://engie.com.au/about-us/our-generation-activities/battery-storage/hazelwood-battery) — Original HBESS operational from 2023, 150 MW / 150 MWh; separate HBESS2 expansion of 150 MW / 600 MWh under construction. |
| `mortenson_edwards` | Mortenson | Unknown / undated | [Edwards & Sanborn Solar + Storage Project Complete](https://www.mortenson.com/news-insights/edwards-sanborn-solar-storage-completion) — Completed project: 3287 MWh BESS, 1300 MW site interconnection and 875 MWdc solar. Interconnection is not BESS output; no battery MW inferred. |
| `aecon_oneida` | Aecon | 2025-05-07 | [Oneida Energy Storage Project Commences Commercial Operations](https://www.aecon.com/press-room/news/2025/05/07/oneida-commences-commercial-operations) — 250 MW / 1000 MWh at Haldimand County; lithium-ion units; Northland oversees operations. |
| `engie_coya_2024` | ENGIE Chile | 2024-03-18 | [Inicia su operación comercial el sistema de almacenamiento más grande de América Latina](https://www.engie.cl/inicia-su-operacion-comercial-el-sistema-de-almacenamiento-mas-grande-de-america-latina/) — Coya at María Elena: 139 MW / 638 MWh, lithium batteries; operation authorized by CEN. |
| `engie_storage` | ENGIE Chile | Unknown / undated | [Almacenamiento BESS](https://www.engie.digital/almacenamiento-bess/) — Operating Tamaya: 68 MW / 418 MWh, Tocopilla, 2025. Coya listed at 139 MW / 638 MWh. |
| `engie_financial_2025` | ENGIE Chile / Comisión para el Mercado Financiero | Unknown / undated | [ENGIE Energia Chile financial disclosure, 2025](https://www.cmfchile.cl/institucional/inc/inf_financiera/ifrs/safec_ifrs_verarchivo.php?auth=YTkzMzg5N2Q1NzVhYjg0YmQxNGVkZDQ1ZDY1YjU5MmI%3D&send=aTLbRr%2F7WtG0t9iSEYFzO7yoE2%2FVR6LkV0F57PF3dpY8m4jmpYcoaGZpfwneYsXRwIlXZjuYRoRicccbOcDrZ0gHG6YUSV2RxGE71hXYJrKSw7IXoi1yVuWH7hiH5GAZhoC6eH+HvxGZ7yP10tgDpCUpJvbQPBAl2L8V56+AXzTHOAQ%3D) — Financial report lists Coya at 140.97 MW and Tamaya at 76 MW. Basis discrepancy with public project descriptions is unresolved. |
| `isa_registro` | ISA Energia Brasil | 2025-03-14 | [ISA Energia Brasil receives MME, EPE and ONS at its battery storage facility](https://www.isaenergiabrasil.com.br/centro-de-midia/noticias/isa-energia-brasil-recebe-mme-epe-e-ons-para-visita-ao-primeiro-sistema-de-armazenamento-de-energia-em-larga-escala-da-transmissao-nacional/) — Registro substation battery system: 30 MW / 60 MWh and two-hour peak support. |
| `sse_ferrybridge` | SSE | 2026-03-20 | [Ferrybridge Battery Storage System enters full operation](https://www.sse.com/news-and-views/2026/03/sse-s-ferrybridge-battery-storage-system-enters-full-operation/) — Ferrybridge 150/300 operating; Salisbury 50/100 operating; Monk Fryston 320/640 and Fiddlers Ferry 150/300 under construction. |
| `iberdrola_aranuelo` | Iberdrola | 2021-09-16 | [Iberdrola commissions Arañuelo III, the first photovoltaic plant in Spain with a storage battery](https://www.iberdrola.com/press-room/news/detail/aranuelo-iii-first-photovoltaic-plant-spain-storage-battery) — 3 MW / 9 MWh battery with Arañuelo III solar plant; commissioned announcement. |
| `galp_alcoutim` | Galp | 2024-02-07 | [Galp and Powin to build large-scale energy storage system in Portugal](https://www.galp.com/corp/en/media/press-releases/press-release/id/1515/galp-and-powin-to-build-large-scale-energy-storage-system-in-portugal) — 5 MW / 20 MWh BESS near Alcoutim, integrated by Powin with solar. |
| `galp_alcoutim_2025` | Galp | 2025-07-31 | [Galp instala 74 MW de baterias para armazenar energia solar em Portugal e Espanha](https://www.galp.com/corp/Portals/0/Comunicados_Media/2025/07-Jul/Galp-instala-74-MW-de-baterias-para-armazenar-energia-solar-em-Portugal-e-Espanha.pdf) — Original Alcoutim 5 MW / 20 MWh system operating since early 2025; additional four-system 60.5 MW / 120.4 MWh expansion distinct. |
| `total_dunkirk` | TotalEnergies | 2021-12-21 | [TotalEnergies Launches the Largest Battery-Based Energy Storage Site in France](https://totalenergies.com/newsroom/totalenergies-launches-largest-battery-based-energy-storage-site-france/?lang=eng) — Completed Dunkirk facility: 61 MW and 61 MWh; Saft containers. Initial 25 MW unit included, not additive. |
| `rwe_hamm_neurath` | RWE | 2025-02-14 | [220 megawatts of power to stabilise the grid: RWE commissions Hamm and Neurath battery storage systems](https://www.rwe.com/en/press/rwe-generation/2025-02-14-220-megawatts-of-power-to-stabilise-the-grid-new-battery-storage-systems/) — Separate sites: Hamm 140 MW / 151 MWh and Neurath 80 MW / 84 MWh; exclude 220 MW portfolio total. |
| `neoen_storen` | Neoen | 2024-06-20 | [Sveriges största batteri tas i bruk](https://sweden.neoen.com/sv/okategoriserad/2024/sveriges-storsta-batteri-tas-i-bruk/) — Storen in Ragunda: 52 MW / 52 MWh; inaugurated and operating. Isbillen is a different project. |
| `neoen_yllikkala` | Neoen | 2025-09-08 | [Neoen ottaa käyttöön toisen suuren akkuvarastonsa Suomessa](https://finland.neoen.com/fi/okategoriserad/2025/neoen-ottaa-kayttoon-toisen-suuren-akkuvarastonsa-suomessa/) — Two distinct installations ~100 metres apart: original 30 MW / 30 MWh; new Two project 56.4 MW / 112.9 MWh, Nidec and Destia. |
| `energy_cells` | Energy Cells | Unknown / undated | [About the project: Lithuanian battery parks](https://energy-cells.eu/about-project/) — Four separate 50 MW / 50 MWh parks at Vilnius, Šiauliai, Alytus, Utena; operational reserve service in 2023; Siemens Energy/Fluence consortium. |
| `giga_buffalo` | GIGA Storage | Unknown / undated | [Buffalo NL](https://giga-storage.com/en/projects/buffalo/) — Lelystad: 25 MW / 48 MWh, lithium LFP, supplier Wärtsilä, delivered 2022; connected to Windnet smart grid. |
| `eskom_hex` | Eskom | 2023-11-10 | [Eskom unveils a first of its kind largest battery storage project in the African continent](https://www.eskom.co.za/eskom-unveils-a-first-of-its-kind-largest-battery-storage-project-in-the-african-continent/) — Hex opened in Worcester; 100 MWh storage. |
| `eskom_rollout` | Eskom | Unknown / undated | [Battery Energy Storage System - Distribution](https://www.eskom.co.za/distribution/battery-energy-storage-system/) — Site-level table lists Hex at 20 MW / 100 MWh. Rollout totals are not separate projects. |
| `seci_rajnandgaon` | Solar Energy Corporation of India | Unknown / undated | [Own projects: commissioned Rajnandgaon solar and BESS](https://seci.co.in/own-projects) — Commissioned Rajnandgaon: 40 MW / 120 MWh lithium-ion storage paired with 100 MW solar PV. |
| `dicp_dalian` | Dalian Institute of Chemical Physics, Chinese Academy of Sciences | 2022-10-31 | [百兆瓦级大连液流电池储能调峰电站并网发电](https://dicp.cas.cn/xwdt/kyjz/202210/t20221031_6541871.html) — Grid-connected first phase: 100 MW / 400 MWh vanadium flow battery. Planned 200 MW / 800 MWh total is excluded. |
| `sembcorp_ess` | Sembcorp | Unknown / undated | [Energy Storage Systems](https://www.sembcorp.com/en/driving-energy-transition/our-businesses/renewable-energy/energy-storage-systems/) — Current owner page reports operating Jurong Island ESS with 326 MWh; no battery MW stated. |
| `ema_sembcorp_2023` | Energy Market Authority | 2023-02-02 | [Southeast Asia’s largest energy storage system officially opens](https://www.ema.gov.sg/news-events/news/media-releases/2023/southeast-asias-largest-energy-storage-system-officially-opens) — Jurong Island Banyan and Sakra project: 285 MWh at opening, operations began December 2022. |
| `sumitomo_hayakita` | Sumitomo Electric | 2026-04-28 | [Sumitomo Electric’s Vanadium Redox Flow Battery Selected by Hokkaido Electric Power Network for the Third Time](https://sumitomoelectric.com/press/2026/04/prs015) — Original 15 MW / 60 MWh demonstration battery remains commercially operational; separate 17/51 project and future 11/33 project excluded. |
| `fluence_kabankalan` | Fluence | 2022-01-27 | [SMCGPH and Fluence’s First Battery Project of 470 MW Portfolio Begins Commercial Operation in the Philippines](https://blog.fluenceenergy.com/smcgph-and-fluences-first-battery-energy-storage-project-of-470-mw-portfolio-begins-commercial-operation-in-the-philippines) — Kabankalan 20 MW / 20 MWh enters commercial operation; not the complete 470 MW portfolio. |
| `huawei_redsea` | Huawei | Unknown / undated | [City of Tomorrow: Huawei FusionSolar contributes to the first city powered by clean energy](https://digitalpower.huawei.com/en/cases/fusionsolar/first-fity-powered-by-clean-energy) — Red Sea hotels and airport operating; project package includes 400 MW PV and 1.3 GWh ESS. No BESS power rating stated. |
| `nrec_bisha` | NR Electric | Unknown / undated | [Saudi Arabia achieves black start of 500MW energy storage station for the first time](https://www.nrec.com/en/index.php/about/newsInfo/203.html) — Black-start test dated February 9, 2026 for 500 MW / 2 GWh Bisha project; NR supplies AC-side PCS/PMS/EMS. Commercial status not established by this test. |
| `ea_nz_batteries` | Electricity Authority New Zealand | Unknown / undated | [Eye on electricity: Battery performance in New Zealand](https://www.ea.govt.nz/news/eye-on-electricity/eye-on-electricity-battery-performance-in-new-zealand/) — Operating grid batteries listed: Rotohiko 35 MW / 35 MWh, Ruakākā 100 MW / 200 MWh and Glenbrook-Ohurua 100 MW / 200 MWh. |
