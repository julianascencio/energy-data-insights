# Battery configuration and project-evidence continuation — 6 November 2026

Started07:48:43 Atlantic/Canary. This checkpoint: 2026-11-06T08:15:33.290856+00:00; actual elapsed approximately26.8minutes, with research and validation overlapping. Final publication and hosted-CI times are recorded in the successor PR. Main036429f and open BESS head02abe346 were read; isolated checkout continues PR188. All openPR188–192 titles and full changed-path lists inspected at discovery and refreshed before publication. No BESS overlap, no subagents, no merge. Existing workflow, schemas, dictionaries, sources, manifests and prior logs/PV conventions retained; historical reports remain unchanged.

## Accepted records and boundaries

**20 new exact equipment records:** ATESS6 BC55NPB cabinet configurations,7 VoltStack rack configurations and1 named ESS-BM-51.2-100NPB module; INTILION6 scalepac enclosure configurations. These are explicit table columns, not generated parallel combinations. INTILION is one new supplier label, identified as system integrator. No new OEM-entity table or project-to-equipment assignment.

Capture includes nominal and separately reported usable energy, voltages, C-rates, explicit module/BPU counts, module relationships, approximate/upper mass bounds, dimensions, IP, cooling, temperature/altitude/derating, protocol and conditional warranty-throughput/life evidence. MW is never inferred from kVA or C-rate. Unqualified ATESS cover life/year claims and INTILION system-level RTE are not transferred as tested configuration guarantees. BC55NPB's unnamed module is not equated with the physically different VoltStack module. Three exact-table images reviewed visually.

VoltStack9-module46.8kWh/468V disagrees with its module arithmetic: canonical energy and nominal voltage stay null and source assertions/calculations remain quarantined in conflicts_json. Arithmetic checks are not replacement specifications. INTILION scalepac5's >12.5GWh throughput qualifier remains as printed. No cosmetic model variants or family expansions.

**Three existing projects enriched, zero new projects:** Rajnandgaon gains the awarded Tata Power Solar Systems contractor and dated award scope; Kavaratti gains ministry grant support with amount/battery allocation unknown; Obelisk gains evidence that the whole battery phase had reached COD by23February2026, without asserting the exact COD day or adding a second battery phase. Scatec February/ August releases disagree on PPA signing month; both remain scoped conflicts, not a chosen contract date. Existing ratings, phases, sources and creation timestamps retained.

Ten project identities reviewed:3 enriched,1 unchanged(Nandyal),6 held. Taru/Phyang is one unresolved candidate, not two accepted projects. Equipment23 exact candidates:20 accepted,3 old scalebloc configurations held because original URLs404. Two further INTILION documents(i4/IAU) received preliminary source review and are queued, not counted as accepted records or completed candidate extraction. Zero permanent rejections and zero whole-record quarantines; two accepted records have scoped field conflicts. Prior holds remain intact.

## Sources, market priorities and yield

CEA national inventory attempted first; fresh September2026 endpoint returns502 and alternate former index404. SECI owner portfolio and July2025 parliamentary inventory were examined next; reproduction-permission requirements prevent importing these tables. Ladakh's historical PPA page has the same permission gate. Independent reusable PIB evidence supports two existing-project enrichments; Scatec adds an African lifecycle/contract reconciliation. No forms, contacts, payments or bypasses.

Accepted batches are two ATESS PDFs, one INTILION PDF plus corporate-role page, two PIB releases and one Scatec release. Original bytes/checksums stay outside Git. Copyright retained; bounded OEM/owner facts are not an asserted open bulk licence. No complete source documents, prose, artwork or private contacts committed.

Fresh IEA29May2026 comparison retains selected-country2025 utility-scale battery POWER additions: China~55GW, US>16GW, Australia~4.2GW. Europe's4.6GW is regional, excluded from country ranking. Comparable operational stationary energy stock in GWh remains unavailable; no MW/MWh conversion. Catalogue counts are not capacity or national completeness. All six regions remain represented. Equipment objective met; project yield is below the planning range because the promising official/owner batches have access/reuse/identity gates, not because sparse rows were padded.

Next: use the ranked review ledger. Review current downloaded INTILION i4 BESU and IAU control boundaries; recover CEA only when original access and reuse conditions change; seek independent permissible Ladakh project evidence and resolve Taru/Phyang and Stakna revisions. The three selected accepted OEM tables are exhausted.

## Implementation and validation

New offline ATESS parser/CLI stages13 explicit rack/cabinet columns, rejecting changed units, column order, missing/duplicate rows and BPU scope;14 synthetic tests exercise these failures. The named module and six INTILION columns were individually curated from the visually reviewed tables. Existing upsert API used. Three existing JSON namespace additions trigger its collision guard and were explicitly reviewed as additive merges preserving every prior nested value; PPA conflict metadata is separate. No schema or shared viewer changes.

Final local checks:641 focused BESS tests;35 viewer tests; both catalogue validation/builds; original-source parser replay; natural identity/module-link checks; all prior IDs/creation timestamps/source entries preserved; API replay idempotent; repeat typed Zstandard snapshots byte-identical; both offline examples; repository Ruff lint/format and ty; package builds and strict metadata; hygiene/citations. Manifests and detailed preservation evidence accompany this log.

Full local suite:3277 passed,5 optional skips,1 unrelated PV subprocess failure(psutil.NoSuchProcess PID48). Targeted retry reproduces the environment PID failure. Strict Sphinx initially lacked pinned Orbital PV; installing that dependency clears the first blocker, but gallery then encounters the same psutil PID visibility failure. No unrelated code patched or full local pass claimed. Hosted final-head CI is tracked separately in the successor PR.

Current totals:2226 projects /50 countries and territories /445 sources;1345 equipment /59 suppliers /583 sources(1332 configurations,13 families). Historical cumulative PR188 delta:16 new projects,4 enriched projects,60 new equipment,18 enriched equipment including this then-unpublished batch. PR188 was externally merged at08:21:56 before this batch was published. Successor PR delta versus updated main:zero new projects,3 enriched projects,20 new equipment,zero existing equipment enrichments. Open and unmerged; publication status is not merged content.

## Publication reconciliation

At08:23 Atlantic/Canary the final guard detected PR188 externally merged. No write was made to its closed branch. The completed batch was replayed without conflicts onto current main27f6765c7567f76bed6cde4fe74a270ba72aef70, which also contains the merged PV and data-centre passes. Their changed paths do not overlap this batch. A new research/bess-database-20261106T0823 branch is used. Focused validation and repository checks are repeated on the reconciled tree; final hosted results are recorded in its PR description. Actual elapsed to this checkpoint is approximately35minutes; approximately27minutes research/extraction/reconciliation with overlapping validation, then final audits/publication.
