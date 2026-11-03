# Mauritius, Philippine owner filings and BlueNova configurations

Research began **3 November 2026, 11:50:06 Atlantic/Canary (UTC)** in an isolated
checkout of OPEN PR102, head `c9ed952cf13b0194b723ee6c4eb1736c16c76ab6`.
Main was `5063c41694b17b1a3fc856ea9527a32211278203`. Earlier Australia/Chile
and foundation work is already merged; historical ledgers were preserved.
Actual elapsed effort and executed checks are recorded below after validation.

## Accepted facts and identity decisions

This increment adds **21 projects**, substantively enriches **four existing
projects**, and adds **13 exact BlueNova configurations**. No existing equipment
record is changed and no new supplier is claimed. Proposed totals are **1,830
projects / 38 countries / 271 sources** and **658 equipment records / 44 suppliers /
319 sources**: 645 exact configurations and 13 families. Mauritius is the new
country; all six world regions remain represented. These are dated research
records, not a present operating-capacity census.

The complete SMGP annual-filing licence table and named development paragraph
contain 21 distinct candidates. Fourteen become new records and Kabankalan is
enriched; six remain held. Eleven PAO rows retain individually printed MW,
barangay/city/province and validity periods. Their status is **permitted as of
31 December 2025**, when those permits were valid, not operational in November 2026.
The April 2026 filing's pending extensions are retained separately. The printed
MW units are not silently corrected to MWh or labelled AC/gross nameplate. Limay
and Lamao have different explicit facility names and barangays. Villanueva's
reported Tagoloan location is preserved instead of corrected from its name.

Masinloc is one combined two-phase battery, with 35.258 MWh, project-company
ownership, LPDSI O&M, phase 1 acquisition date, phase 2 energy and NGCP regulating
reserve contract context. Coal unit ratings,230 kV connection and unrelated power
sales are excluded. Mariveles is one 320 MWh development with ATE Energy EPC and
separately reported 44%/83% unit progress; no unit capacities are invented. Dingle
is 40 MWh with a 2027target, not operation. Kabankalan keeps its historic 20 MW/20 MWh
phase 1 ratings and stable ID;33.867 MWh combined-phase energy and the 2026 PAO are
added in evidence extensions, with an explicit phase 1 canonical capacity scope.
No phase 2 residual capacity, duplicate aggregate or project-specific equipment
assignment is fabricated. Toledo/Malita need more than COC-only rows; Magapit,
Tabango, Tagum and Mexico lack individual ratings within a 140 MWh aggregate.

The CEB presentation is actually dated **26 May 2022**, despite recent search-index
metadata. Its complete table gives six installations totaling 18 MW/9 MWh and a
separate Amaury 20 MW/10 MWh expansion. All seven have reviewed identities and
technical ratings. The six older records have **unknown lifecycle** because the
accepted table does not establish commissioning. The Ministry's2023–2024 report
supports operation of the 20 MW expansion, early-February 2024handover, July 2022
contract, Siemens Energy contractor wording,66 kV bay and peak-shaving/frequency
services. Inauguration dates are not substituted for COD. The earlier 2 MW Amaury
record and expansion have explicit scopes and a stable related-record link.

AfDB's latest report was freshly downloaded: its hash matches the already
registered2026 report. Three existing Eskom sites gain previously uncaptured
milestones: Pongola 28April 2024and Elandskop 9June 2024test/dry-run completions,
and Hex's site-specific 9November 2023commissioning observation. The report's
aggregate November 2024statement includes Hex elsewhere: that conflict is
quarantined rather than replacing COD. Four other existing sites are unchanged;
Rietfontein/Reinfontein/Reinfointein remains an identity hold. Existing source
metadata is not timestamp-churned when identical bytes are rechecked.

BlueNova's five integrated AIO sheets and eight legacy 280 Ah cabinet sheets were
individually rendered and reviewed. They are distinct from the 314 Ah models
accepted earlier. Exact Wh values, voltage, module/cell capacities, C-rate,
thermal/storage limits, IP, fire suppression, dimensions, mass qualifiers,
communications and manufacturer standards claims are retained. The129k cabinet's
20-unit 2.85 MWh feature claim conflicts with its 2580 kWh graph and is quarantined;
the exact single-cabinet129024 Wh table value is retained. No parallel-system
configuration rows are generated. “AC” in the names means air cooled; actual
AC integration is separately evidenced for AIOs.

The 125 kW AIO explicitly includes the Solis S6-EH3P(125)K10-NV-YD-H inverter.
Its inverter rated/peak AC output, PV input limits, MPPT/string counts, per-port
current, backup switching and inverter-only self-consumption are separately
scoped. IP66,3000m and inverter temperature limits do not replace cabinet IP55,
2000 m and battery limits.125 kW inverter output is not a guarantee of battery-only
continuous discharge.105 kW PV configurations preserve unmapped slash alternatives
rather than assigning3/2 MPPT or300/550 A to a particular option. Poweroad logos are
not proof of an exact rebrand equivalence or cell OEM. No RTE, warranty, usable
energy or derived mixed-boundary duration is inferred.

## Access, reproducibility and remaining work

Scalable registry/owner sources were attempted first. EirGrid, ESB and IEMOP have
explicit reuse restrictions; no bulk import followed. Kirby returned403. The
FOI-linked DOE inventory URL returns an HTTP200 application shell saying Page Not
Found, not a downloaded inventory. CEB's current portfolio and disclaimer return
404, so cached search snippets are not accepted evidence. UNDP terms restrict
redistribution/derivatives; its otherwise useful lifecycle article is held. These
blocks triggered independent owner/ministry alternatives, not an end to the pass.

Mauritius State terms permit accurate attributed reproduction with copyright
acknowledgement and third-party exceptions. Sources explicitly credit CEB and
Government of Mauritius; no slides, figures or full reports are redistributed.
SMGP/BlueNova/AfDB do not become open-licensed datasets: only bounded factual
observations are committed with exact URLs, publisher, known document date,
page/row mapping, actual retrieval timestamps and SHA256. Downloaded bytes remain
outside Git. The source register and review ledger distinguish fresh downloads,
404/403 attempts and existing identical-source reuse.

The new source-specific adapter is offline and stages candidates only:

```bash
pdftotext -layout ceb-smart-grid.pdf ceb.txt
uv run python scripts/stage_bess_ceb.py ceb.txt --output ceb-candidates.jsonl
```

It checks the printed date, row count, MW/MWh units, duplicate names and both
control totals, while keeping Amaury's expansion separate and lifecycle unknown.
Eight synthetic tests cover malformed dates/units/totals, missing/duplicate rows
and an unexpected expansion identity. Original-table replay matches all seven
reviewed candidates. Other exact specifications are manually reviewed and
submitted through the existing upsert API. That API refused four changes to
populated evidence/scope fields; explicit reviewed edits preserve all creation
times and original capacity facts. The audit checks 1,805 unchanged prior project
records and all 645 prior equipment rows. No schema extension was needed.

IEA's 2025 annual stationary battery power-additions comparison was freshly checked.
It ranks only quantified country examples using GW; comparable worldwide
operational stationary GWh remains unavailable. No MW-to-MWh conversion or
incomparable country ranking is introduced. New research deepens Africa and Asia
while preserving prior global coverage.

Project yield of21 new plus 4 enriched is below 50: selected source batches are small,
six SMGP candidates lack individual technical detail, several registry sources
have access/reuse limits, and much of Eskom's latest report was already covered.
All 13selected exact equipment candidates are accepted, meeting the10–30 model
working objective. The complete selected CEB/SMGP/BlueNova partitions are exhausted;
no thin residual rows or timestamp-only changes are added to meet a quota.
The ranked backlog's next high-value source is the current public-domain DOE
regional plant inventory, once its migrated download location is resolved,
followed by SMGP quarterly permit/COD updates and Mauritius ministry lifecycle
records. Every hold has a retry condition and next action.

Open PRs 100/DC,101/Wind and103/PV were checked by title and changed paths.
They do not overlap this increment's catalogue/adapter writes. Wind 101 owns shared
bibliography paths: 16 new bibliography entries are queued in this scoped research
directory, alongside 37 earlier pending entries. Existing citation consistency is
checked, but shared bibliography integration remains pending. No unrelated files,
force-push, comments, contacts, payments or merges are part of this iteration.

## Executed validation

Checks completed at **12:18:11 Atlantic/Canary on 3 November 2026**,
**28.09 minutes** after research began; publication follows immediately.

- Full Python suite: **1,848 passed**, one optional `cdsapi` skip. Eight focused
  adapter tests and complete original-table replay passed.
- Both catalogue validators, preservation/reference checks and duplicate checks
  passed. Two independent typed Zstandard builds match, with coverage/completeness
  and input/output hashes recorded in the committed manifest.
- Ruff, formatting, ty, 13 viewer Node tests and both offline BESS examples passed.
- Strict Sphinx and the **447-page** local link/asset audit passed. An initial link
  audit ran before the concurrent docs build finished publishing datasets; rerun
  after build completion passed. No missing assets remain.
- All three wheels/sdists built; strict Twine and installed-wheel public entry-point
  checks passed. Existing citation consistency and repository checks passed;
  shared-reference integration is still queued, not claimed complete.
- No new schema or dependency change; no optional imagery or fresh interactive
  browser check claimed. Final whitespace/repository checks precede commit.

The selected source partitions are exhausted or explicitly held. Remaining time
is used for publication and remote verification rather than adding thin records.
Main and the target PR head were unchanged at validation; open PV/Wind/DC work
was checked by changed paths and left untouched. The final branch update uses
an expected-head lease and is non-forced. Leave PR102 open and unmerged.

Publication prepared at 2026-11-03T12:19:15.396079+00:00; **29.16 minutes** elapsed through preparation.
