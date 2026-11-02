# Philippine battery reconciliation and South African commercial batteries

1 November 2026, Atlantic/Canary / UTC. Started 23:53:22. Main 9bab286 includes
merged BESS PR #52 and PV PR #53; no compatible open BESS PR remains. Open PRs
#47–49 were inspected by title and paths (workflow dependency changes only).
This isolated branch leaves PV records, shared schema and importers untouched.

## Results

**Three new projects, one project enrichment and ten exact equipment models**.
Current totals: **1,281 projects / 30 countries / 96 sources; 172 equipment
records / 31 suppliers / 77 sources** (159 configurations and 13 families).
No new country or supplier. Existing coverage across Africa, Asia, Europe,
Latin America/Caribbean, North America and Oceania remains. Zero new quarantines
or rejections; 17 project candidates held. All prior creation timestamps remain;
only Kabankalan has substantive updates among existing records.

The national grid operator's March2026 ancillary-services bulletin was reviewed
before owner-specific extraction: 21 battery candidates identified across the
contracted-provider and certified-without-ASPA tables. These are different scopes;
AS certification alone does not establish commercial operation, ownership or MW.
BSS in the legend means black-start service, not battery storage. Seventeen
candidates need owner/DOE capacity and physical-identity reconciliation. No thin
rows were created just from their names. San Manuel and Jasaan have explicit
contracted-firm-capacity unavailability flags that future imports must preserve.

EDC's 2025 annual financial statements, note21(h), printed page87, explicitly
report Bac-Man 20MW/20MWh, Tongonan 10MW/10MWh and Southern Negros 10MW/10MWh,
with respective commercial-operation dates 2025-09-12, 2025-12-09 and 2025-11-13.
The battery-only records preserve these dates, ancillary-service purpose,
geothermal co-location and developer. Chemistry, precise coordinates and
AC/DC/gross/usable bases are unknown. No generation capacity is assigned to the
batteries. Kabankalan gains regulating-reserve service, ERC case2021-056RC and
separate current/former listed AS-provider entities; its owner and existing
20MW/20MWh ratings remain unchanged. The NGCP evidence is dated, not a claim of
real-time service availability.

Two Freedom Won tables contain five exact LiTE2 Commercial HV and five HV+
configurations. Every printed column was reconciled independently: total energy,
continuous DC discharge power, maximum/charge powers and currents, voltage limits,
dimensions, mass and communication protocols. Five-minute maximum duty every ten
minutes and five-second overload are distinct from continuous output. Current
ratings apply at 10–25°C; environmental ranges and charge restrictions are retained.
DoD-based energy rows remain separate from total energy. The96–97% efficiency
range and conditional warranty language stay qualified in extensions; no AC-to-AC
RTE or independently verified warranty/certification claim is asserted. Cooling
cells with ambiguous spans were left unknown. These June2025 tables are in the
OEM end-of-life documentation section; current sale/availability is not inferred.
No PCS inclusion, project assignment or arbitrary family variant was invented.

## Access and evidence limitations

IEMOP's legal terms explicitly require prior written consent for adopting,
modifying or reproducing information. The register was not bulk-extracted or
imported; no consent request/contact was sent. DOE's accessible 2025 statistics
page supplies aggregates rather than a project partition. NGCP provided an
alternative downloadable official inventory, retained outside Git with SHA-256.
Its bounded factual review is not an assertion of an open bulk-reuse licence.

Direct HTTP downloads of the EDC report and both Freedom Won PDFs returned403.
Their primary-document content was available through the research service's
indexed retrieval. Accepted records explicitly retain the historical publication
revision and this access method. No original-file checksum is claimed for bytes
not obtained; filling those three checksum gaps is in the backlog. No access
control was bypassed. Exact URLs and page/column locators are registered. Neither
full copyrighted source text nor PDF binaries are committed. This limitation is
material: the observations verify the cited editions, not a fresh live PDF hash.

## Priorities and validation

The existing dated IEA comparison remains applicable: annual2025 stationary
battery power additions in GW, with quantified country examples China, US,
Australia and Chile; not an exhaustive ranking or operational GWh inventory.
The Philippine expansion improves an underserved market; South African OEM depth
avoids another FoxESS-only iteration. Candidate, evidence/access, retry and next
partition details are in the dated review, audit and ranked backlog.

Below-target project yield reflects 17 unresolved identities/capacities, IEMOP
reuse restrictions and the aggregate-only DOE landing page. The selected 21-entry
battery inventory partition and ten exact OEM columns are exhausted. Next:
current DOE plant-level attachments/owner portfolios for the held sites, then
original PDF bytes and model-specific warranty terms for the accepted equipment.

Local validation completed around 23:59 Atlantic/Canary / UTC, approximately
seven minutes elapsed: four minutes discovery/reconciliation and three minutes
implementation/checks/publication preparation. Early completion follows exhaustion
of the selected inventory partition and exact tables, with specific access/rights
and identity follow-ups recorded instead of padding counts.

Both catalogue validators passed; 28 focused tests passed and were repeated after
final energy-basis clarification. Ruff lint/format (517 files), ty using the project
environment, repository hygiene and citation consistency passed. Four viewer JS
tests passed. Strict Sphinx and all executable offline gallery examples passed;
387 HTML pages passed local-link checks. Both BESS offline usage examples ran.
Typed Zstandard Parquet snapshots were rebuilt twice with matching manifests.
Preservation audit verifies all prior IDs and creation times. No code or schema
changed; full Python and package-build suites were not rerun. Remote CI is
separate. Commit/PR publication does not mean merged database content.
