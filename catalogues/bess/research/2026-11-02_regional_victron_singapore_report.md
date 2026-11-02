# Regional Victron tables and Singapore reconciliation — 2 November 2026

Continues PR #62 from `e673909` in an isolated checkout. Main remains `65931a16`.
The catalogue workflow, dictionaries, schemas, source registers, recent manifests
and GIGA/Scatec research were reviewed; no AGENTS.md found. PV #61 advanced to
`1164ca1` but its 164 paths remain confined to catalogues/pv. Dependency PRs touch
workflows only. No schema or parser code is changed by this bounded manual batch.

## Results

Eleven exact configurations were reviewed and accepted: five Quattro 120 V, one
Quattro 277 V, two Quattro-II 230 V and three MultiPlus-II 2x120 V. Four complete OEM
specification tables were downloaded and visually checked, including their model
column spans and footnotes. The 2x120 V product is electrically distinct from the
previous 120 V unit: inverter mode supplies 120 V on joined outputs;240 V loads need
external split-phase AC. No duplicate certification-only variants were generated.

Ratings include continuous active power at 25/40/65 degC, apparent and peak power,
DC limits, charging current, maximum inverter conversion efficiency, auxiliary
consumption, mass/dimensions, IP, communications and qualified standards claims.
One charger-current field is withheld: the 12/5000/220-100/100120 V table says 200 A,
while the exact model designation contains 220. Neither the 230 V rating nor the
model name is used to invent a corrected current. Other specs remain accepted.
The early HQ2107 auxiliary-output limit is retained for 2x120 V; no universal 50 A
claim is made for all historical units. No energy, chemistry or RTE is inferred.

One existing Singapore project is substantively enriched. Sembcorp's dated
27 October 2025 release explicitly identifies vertical expansion from 285 to 326 MWh
without more land. This resolves the previous unknown expansion/basis explanation;
326 MWh and the original identity/creation time remain unchanged. Historical 285 MWh
is retained in the conflict history, not counted as a second project. Planned
inertia testing with EMA is recorded as prospective, not delivered service.
No new project, country or OEM is added. Totals:1,312 projects /31 countries /
139 sources;281 equipment /35 suppliers /97 sources (268 configurations,13 families).
No whole-record rejection; one equipment field held; earlier holds preserved.

## Inventory attempt and limits

The project stream began with EMA's current Energy Storage Systems overview and
second grant-call portfolio. They provide policy/award summaries, not a reusable
site inventory. The grant page also contains placeholder text, so no applicant
or capacity was extracted from its placeholder sections. The 2020 deployment release
identifies a 2.4 MW/2.4 MWh substation testbed and a five-block Punggol aggregation;
both remain candidates pending exact site identities, lifecycle and battery scope.
The older 2017 two-site 4.4 MWh award is not added alongside the 2020 testbed.
SIEW's terms reserve rights and are not an open bulk licence. Its mirrored release
was used for discovery; the Sembcorp issuer release is the accepted primary source.
The issuer PDF returned 403; HTML was readable through web retrieval, so no original
byte checksum is asserted. OEM PDFs are hash-pinned and kept outside Git. Bounded
factual specifications are committed, not source documents or source prose.

The dated IEA comparison in 2026-11-02_dyness_baltic_markets.json remains a partial
ranking of 2025 annual stationary power additions inGW, not operational energyGWh.
No new globally comparable GWh table was established. Six-region catalogue coverage
is retained; this pass targets an Asian evidence gap and regional PCS boundaries.

The existing upsert API was used, incoming and canonical identities were checked,
and original creation times preserved. Two independent typed Zstandard builds per
catalogue produced identical manifests. The source tables are exhausted; eleven
models meet the equipment planning range. Project yield is lower because the
regulator portfolio is not a site inventory and two historical scopes remain held.
No tests were added for data-only transcription; existing catalogue tests apply.

## Next work

Resolve the Singapore 2020 substation identity and Punggol aggregation using SP Group
and Sunseap site documents. Obtain a corrected Quattro 120 V charge-current table.
Prefer a new regional OEM or battery-cell/rack table next rather than indefinitely
expanding one PCS brand. Preserve all earlier CEA, Eskom and Chile phase holds.

The IEA primary page was reopened on 2 November 2026; its quantified 2025 country examples remain China >63 GW, United States 19 GW, Australia nearly 8 GW and Chile nearly 1 GW. Europe 6.2 GW is regional and is not inserted into the country ordering.

## Validation and elapsed effort

Started 06:48:30 and completed validation 06:56:07 Atlantic/Canary (UTC):
7.62 minutes before publication, approximately 4 minutes source review/transcription
and 4 minutes implementation/checks, with independent checks overlapping. The four
selected tables are exhausted; no idle wait was used. The 11 accepted equipment
configurations meet the equipment planning range. The project workstream reviewed
three scopes: one existing enrichment and two held candidates, with zero additions.

Passed 28 catalogue tests, 4 viewer tests, both catalogue validators, Ruff/format/ty,
repository and citation checks, both offline examples, six package builds and
strict Sphinx. All 395 HTML pages passed local-link/asset checks. Typed Zstandard
snapshots reproduced identically. Full Python suite was not rerun for data-only
changes. No parser or schema implementation changed. Main and PR heads were
rechecked; PV #61 has 164 non-overlapping catalogue paths; no active GitHub workflow
run was reported. PR #62 stays open, with a leased non-force update.
