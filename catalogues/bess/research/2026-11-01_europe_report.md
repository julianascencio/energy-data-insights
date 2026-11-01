# Germany and Netherlands owner-portfolio pass — 1 November 2026

11 new projects (Germany 8, Netherlands 3), two enriched existing projects, four added factual fields (chemistry and integrator on Hamm/Neurath). Total: 1,250 rows, 28 countries, 64 sources. No new country. The previous 126-row Australia/Chile/Belgium batch and all held candidates remain unchanged. New rows and manifests are staged on the existing PR #44; not merged.

## Reconciliation and evidence

Reviewed 13 named identities against all 1,239 rows: 11 absent identities accepted and two exact existing identities enriched through the upsert API. No fuzzy merges. No new project quarantine or rejection. Power remains unspecified AC/DC unless evidenced; no coordinates, equipment OEMs or exact COD dates inferred.

Moerdijk's operating 7.5 MW inertia pilot is distinct from the 400 MW FID project. Lingen Emsland (45 MW) is distinct from the Dralon development (400 MW). The two Lingen/Werne sites are individual records, without an extra combined row. Their 49/79 MWh energy ratings come from the 2023 release, power and operating status from the owner location page. Shared EUR50m and 47-container totals are not allocated to individual sites.

Hambach's new 236 MW project, existing integrated 4.1 MW solar battery and Manheimer Bucht battery have explicit separate scopes. For Dralon, retain >=800 MWh as an extension bound, not an exact scalar; status is permitted as of the release before planned site work. Gundremmingen's cost and container estimates remain qualified extensions. Dortmund has no inferred MWh from its approximate duration. PV and battery power remain separate. See each row's field_sources_json and registered URL/paragraph locator.

## Discovery breadth and lower project yield

An official multi-record source was attempted before publication: MaStR's daily export index carries an attribution licence and advertises about 3 GB of XML ZIP data. A bounded range probe returned HTTP 503; no registry candidate was accepted. Alternative owner-portfolio discovery and ten primary owner pages produced the accepted batch. The model workstream separately completed 15 exact BYD/Dyness configurations in existing PR #45. These named OEM tables and selected project pages were exhausted; this is a model-focused pass, not a 50–200-project bulk-import result. No filler variants or repeated timestamp updates were used.

## Market prioritization

[IEA Global Energy Review 2026](https://www.iea.org/reports/global-energy-review-2026/technology-battery-storage), checked 2026-11-01, ranks **2025 new battery power deployment** as China, United States, then Europe (a region). This is a dated qualitative power-additions ordering, not cumulative operational GWh or a ten-country ranking. Comparable top-ten country GWh data remains unverified; do not fabricate it or rank using this catalogue's row counts. Next coverage priority remains China/India and underserved countries, alongside the licensed German archive retry.

## Durable next step

See 2026-11-01_europe_backlog.json for source terms, access results and retry conditions. Retry MaStR, inspect its new export dictionary and identify electrochemical storage before ingestion; then reconcile plants/phases. Herdecke and later Hamm phases remain discovery backlog, not accepted candidates. No adapter was introduced without a downloaded sample.

## Validation

Validation results and actual elapsed effort are recorded in the final validation section below. Fresh typed Parquet and completeness manifest generated; no binaries committed. Historical launch/earlier research files are unchanged.

### Final checks (2026-11-01)

Full Python suite: 1,437 passed, five skipped (optional CDS/orbital imagery dependencies absent). Focused tests: 28 project/inventory/analysis passed. Ruff lint and format, ty with the locked Python 3.13 environment, repository hygiene, citation consistency and diff whitespace passed. Both offline gallery examples executed and matched exported manifest fingerprints. Preservation audit: no deleted rows; old creation dates unchanged; exactly two existing project rows changed, zero existing OEM rows changed. No schema, parser or viewer-code changes; strict Sphinx/browser/package builds were not rerun in this data-only pass.

Elapsed to final validation: approximately 8 minutes (09:45–09:54 UTC). Selected model tables and project batch exhausted; OEM objective met. Bulk project yield was constrained by transient MaStR HTTP 503, not evidence acceptance quotas. Continue with the documented source queue next pass.
