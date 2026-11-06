# Exact ATESS converter continuation — 6 November 2026

Started06:53 Atlantic/Canary. Research and implementation checkpoint07:00; final publication/check time is recorded in PR188. Continue current head58c6295; main036429f was read from the isolated checkout. PR188 and all other openPR189–192 titles and changed paths were inspected; no BESS overlap. No repository AGENTS.md found in the tree. Prior workflow, dictionaries, sources, latest manifests/backlog and PV conventions retained. No schema, importer, shared viewer or historical launch report changes.

## Accepted and held

Twelve exact model columns from five current-linked OEM PDFs accepted: PCS1000HV/1200HV/1500HV, HPS100KTL/125KTL, HPS40000TL/50000TL PCS250S/350S and HPS15000TL/20000TL/30000TL. Zero existing-model enrichments; no new suppliers/countries. Five datasheet page2 images visually checked, including merged scope, exact headings and W/H/D order. Selected electrical, mechanical and environmental facts mapped to exact source IDs; original bytes/checksums remain outside Git. HPS100KTL/125KTL headings are not duplicated under website100000TL/125000TL aliases. No parallel configurations generated.

Power MW, apparent MVA, AC input, DC rating and maximum charge/discharge remain separate. HV currents preserve asymmetric charge/discharge values. Battery energy, chemistry, warranty, cycle life and RTE remain unknown. Maximum converter efficiency is not RTE. Optional WiFi/4G are not standard interfaces. No independent certificate claims.

Seven accepted records have scoped conflicts: PCS1000HV nominal540V versus360–440V range; two larger TL models PDF950V versus web900V maximum (canonical maximum null); two smaller TL transfer6ms web versus10ms PDF; two S converters optional/manual web versus automatic PDF transfer. Evidence is retained rather than silently resolving editions. Earlier April HV sheet differs from July in noise65/75dBA; current-linked July edition used explicitly, not a separate model variant.

Zero projects accepted or enriched. Attempted Latvenergo procurement inventory/owner portfolio before isolated alternatives. Current contract index is accessible, but footer prohibits commercial copying/republication; press-release route redirects to inaccessible Elektrum domain. Two earlier unnamed Riga identities remain held; index title alone does not reconcile both sites. Local-language search used; secondary results not imported. Kenyan ministry inventory search produced no defensible battery-specific downloadable result. No project quantities inferred from aggregate strategy.

Seven previously held EnerStack100 clusters remain held after Spanish sheet/brochure discovery showed unchanged weight inconsistency. These are not new rejected records. No whole-record quarantines or permanent rejections.

## Coverage and source queue

Totals:2226 projects /50 countries and territories /442 project sources;1325 equipment /58 suppliers /579 sources (1312 exact configurations,13 families). All six regions retained. Counts are not capacity or completeness. Existing IEA2026-05-29 comparison was freshly opened: selected-country2025 utility-scale battery power additions China~55GW, US>16GW, Australia~4.2GW. Europe4.6GW is regional and excluded. Comparable operational GWh stock remains unavailable; no MW-to-MWh inference. See preceding merus_atess_markets.json for metric and URL.

Five selected current PDFs are exhausted (12/12 columns); equipment planning objective met. Project yield is constrained by rights/access and unreconciled identities, not quota padding. Next: an independent Latvian two-site primary crosswalk; then an Asian/African rights-cleared named inventory. Review ledger supplies exact URLs, dates, attempts and retry conditions. Existing holds are preserved.

## Implementation and checks

Existing upsert API used. All prior records and source entries preserved; natural manufacturer/model identities checked against canonical and incoming sets. Final API replay is idempotent. No new parser/code, so no synthetic parser tests added. Both typed Zstandard snapshots rebuilt through existing package; binary files remain outside Git. Full local test collection initially caught verification dates earlier than subsequently added conflict sources; new records were corrected and validation rerun. Final checks and remote publication results are recorded in PR188; do not treat earlier headCI as validation of this continuation.

Final local checks:627 focused tests pass, catalogue validation, API replay/preservation, byte-identical Zstandard snapshots, offline equipment example, repository Ruff lint/format and ty pass. Hygiene passes. No parser/schema changes. Full hosted CI will be reported separately. Local citation check was first invoked against an old installed package; rerun uses current source paths.
