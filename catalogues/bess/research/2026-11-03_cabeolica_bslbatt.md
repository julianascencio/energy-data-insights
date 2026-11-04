# Cabo Verde owner portfolio and exact BSLBATT equipment

Started **3 November 2026, 21:49:15 Atlantic/Canary (UTC)**. The isolated branch
starts from main `8156f311da2db37a2e165e5b854105afd36ac1ba`; PR113 is merged,
and the November1 PR44 checkpoint is historical. Main's instructions, schemas,
dictionaries, source registers, completeness manifests and recent research were
reviewed. The existing PV upsert API and catalogue-specific validation are reused.
No compatible open BESS PR existed. Open PR titles and changed paths were checked:
47–49 are workflow dependency changes; the later Wind116 changes do not overlap
BESS code/data or shared bibliography. No parallel agents or automatic merges.

## Accepted work

**Four new projects, zero existing project changes:** the complete four-island
Cabeólica battery expansion portfolio adds **Cabo Verde (CPV)**. Each island is
one canonical component: Santiago2, Sal3, São Vicente4 and Boa Vista5. No programme
aggregate, wind expansion, alternative site or battery-block duplicate is added.
Design service ratings are6/6,6/6,8/8 and6/6 MW/MWh. Each gains20kV connection,
container counts, applications, developer, location and precise evidence scope.
São Vicente/Boa Vista gain lithium-ion chemistry, connection substations and
20-year planned operation/maintenance periods, not a battery warranty. Sal and
Boa Vista each gain the government's reported EUR6million battery investment;
price year is unknown and thermal/solar investment is excluded.

Three original owner ESIA summaries (January/February2025) identify proposed
Narada76.8NESP200 batteries and distinct SMA converter models. Those assignments
remain explicitly design-stage in extensions, without fabricated links to OEM
records. The6/8MWh service ratings are separate from7.392/10.395MWh installed-block
observations. No apparent-power-to-active-power conversion is made. Boa Vista's
50m table/approximately60m narrative cable lengths remain separate observations.

Government releases confirm inauguration milestones for São Vicente29January2026,
Sal11February2026 and Boa Vista21February2026. The November2025 government
newsletter confirms an installed Santiago battery. **Inauguration does not establish
COD:** all four operating statuses remain unknown pending an acceptance certificate
or unambiguous service evidence. The Santiago month is normalized to month-end
and explicitly marked as reporting precision. Design ratings are not asserted to
be verified as-built capacities. No coordinates are borrowed from wind turbines.

**19 new exact equipment configurations, zero existing equipment changes:**
seven S205 strings, seven S314 strings, three B-LFP48 rack batteries and two
C225/C241 integrated cabinets add **BSLBATT** as a product supplier. This is a brand/
system-supplier attribution, not proof of cell manufacturing. Model-specific energy,
voltage, pack/cell arrangement, current, charge/discharge temperature, enclosure,
communications, mass tolerances, cycle conditions and safety claims are retained.
Rack nominal/usable energy and continuous/one-second power are separate. Cabinets
retain AC125kW and DC current limitations separately; optional PV/transformers are
nested options, not extra catalogue rows. Efficiency claims without a clear RTE
boundary are not promoted. Printed document revision is unknown where only an
index/filename version exists. Rated kWh without explicit nominal/usable wording
retains an unspecified energy basis.

**Twelve accepted models have quarantined fields:** seven S205 configurations
retain the incompatible0.5C/200A maximum-current assertions; two cabinets retain
1850mm PDF versus1800mm web dimensions and55C versus60C upper-ambient claims;
three rack models retain ambiguous W/H/D labels without silently swapping axes.
Those fields stay unset or in explicit conflict structures; unaffected evidence
is accepted with `needs_review`. Ten HV PACK configurations are held for electrical
and current-scope reconciliation. C200/C215 are held because this selected sheet
has no corresponding exact specification columns. **31 equipment candidates →
19 accepted,12 held; no permanent rejections.** The unnamed BCU is not an exact
model and is excluded from candidate counts.

The linked V1.2 C&I warranty adds conditional terms to C225/C241: three-year listed
electronics versus ten-year/8000-cycle battery performance at80%DoD0.5C for314Ah
cells, whichever occurs first. Registration, contract incorporation, start-date,
coastal restrictions and exclusions remain explicit. No capacity-retention threshold
is supplied. The generic contract is not extrapolated to the fourteen DC strings
or the sub100kWh rack products.

## Scalable coverage, access and reconciliation

The first scalable source attempted was Eskom's twelve-site rollout inventory and
fresh FY2026 reports. Eight phase1 sites were reviewed for possible lifecycle
updates (seven existing,one absent). Its website terms prohibit automated collection
without permission and restrict reuse; fresh ingestion stopped. Four phase2 sites
remain an unprocessed partition. Independent AfDB material available in this pass
was older/already represented. Thus **12 selected project candidates →4 accepted,
8 held; zero permanent rejections or canonical project conflicts**. This explains
the project yield below50; it does not substitute eight held candidates for changes.
The equipment objective is met with substantive19-model specifications.

The owner portfolio was the alternative. Its three direct PDF requests returned403,
but public document-reader views exposed the tables. No bypass or repeated retry:
original PDF checksums remain null, and error-response hashes are labelled as such
in the access ledger. The owner report prohibits copying; no report text, images or
full document is committed, only bounded attributed factual observations. Government
and OEM originals were downloaded and hashed outside Git. Public access is never
labelled an open bulk-reuse licence. WinPower and AFC pages remain discovery-only
because of their restrictive terms; independent owner/government sources support
the accepted project data. No contacts, forms, registration or paid access were used.

The new offline BSLBATT adapter stages all14 station columns from local layout text,
checks header/model order, row uniqueness, unit labels, merged-cell counts and voltage
envelopes, and preserves the misleading `Rate Power(kWh)` label as energy. It never
calculates active power or imports identities. Twelve synthetic tests cover malformed
headers/units, missing/duplicate columns/rows, invalid envelopes and unresolved current
claims. The canonical batch was imported through existing upsert, with duplicate checks
against both existing and incoming natural identities. All1985 prior projects and718
prior equipment records remain byte-for-value unchanged, including creation dates.

## Coverage and continuation

Current proposed totals: **1,989 projects /41 countries /307 sources**;
**737 equipment records /46 suppliers /365 sources**, comprising724 configurations
and13 families. Africa is deepened while all six world regions remain represented.
Counts describe catalogue coverage, not national installed capacity or market share.

The dated market comparison in `2026-11-03_poland_containers_markets.json` is reused:
IEA29May2026, **2025 annual stationary battery power additions in GW**, quantified
country examples China >United States >Australia >Chile. Europe/Middle East aggregates
remain separate; this is not an exhaustive country ranking. Comparable worldwide
operational stationary battery GWh was unavailable, and no GW-to-GWh conversion or
unsupported ranking is introduced. The regional rotation selected an underserved
African island market and exact OEM configurations after earlier leading-market passes.

The selected four-island owner batch and four exact OEM tables are exhausted.
The ranked companion backlog records every batch's URL, revision, access/licence,
yield, fields, processed partition, outcome and retry/next action. Next: resolve
HV PACK electrical inconsistencies; obtain Cabeólica acceptance/as-built evidence;
then use an independent permitted source for Eskom lifecycle or rotate to a
Latin-American regulator portfolio. Recheck freshness before resuming.

Final checks, failures corrected, actual elapsed effort and publication preflight
are recorded in the companion validation JSON. Both catalogues regenerate immutable
typed Zstandard Parquet and completeness manifests twice with matching hashes.
Source bytes and binary snapshots stay outside Git under `/tmp/bess2150`; the normal
documentation artifact pipeline publishes regenerated snapshots after review/merge.
This PR is left OPEN. Historical reports and earlier identity/conflict holds are preserved.

Publication resumed on the same worktree after an execution interruption. Main advanced
to `6a84bebbcfe73b76f80aa782c8e212b28103fd29`; bibliography conflicts were resolved
by retaining every main reference and appending only the13 BESS entries. PV117
and Wind116 merged; open Wind119 has no overlapping changed paths. The new
main PV lifetime module has repository-wide type errors; its file is byte-identical
to main and remains outside this PR. Scoped BESS typing passes.

Final strict Sphinx also reports six heading-underline warnings in the unchanged
PV lifetime example; its generated 518-page HTML passes the local link/asset audit.
The final full Python suite passes 2,124 tests. Open Data Center120 was also checked
by changed paths and does not overlap this update. See validation JSON for actual
elapsed wall time, the execution interruption and estimated active effort.
