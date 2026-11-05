# TAB OPzS equipment and Slovenian project reconciliation

5 November 2026. Started 13:54:15 Atlantic/Canary (UTC). Isolated checkout of
open PR #172 at dc81d72bf2aabe1a85a424db093a07ff9136a476; current main
76179409be2ce1166d60714145f1711776182b16. Read existing BESS/OEM workflows,
schemas, dictionaries, source registers, current coverage/review logs and PV
upsert conventions. No competing catalogue or OEM entity table was created.
Historical PR #44 and launch totals were not reused as current counts.

## Accepted batch

- **28 new exact equipment configurations** from TAB, a newly represented
  Slovenian manufacturer: all 22 cells on PDF page 5 and all six monoblocs on page 4.
  Thirty candidates were identified across PDF/current HTML; two website-only
  higher-capacity cells remain deferred pending their applicable edition/conditions.
  No existing equipment records were changed, and none were quarantined/rejected.
- **Two new projects in newly represented Slovenia:** Neoenergija Dobja vas,
  2 MW / 5 MWh, commissioned as of TAB's 28 May 2026 statement; and TAB Prevalje,
  2.2 MWh, commissioned as of 10 July 2025. These are different locations/projects.
- **Two substantive Irish project enrichments:** Fluence delivery/integration
  roles for Cushaling and Kelwin-2, plus Cushaling's 2023 design observation of
  20 MW for up to four hours and market-service context. This historical design
  remains separate from as-built power and does not generate an inferred 80 MWh.
  Kilathmoy was reviewed and left unchanged because the facts were already present.
- **One new project power-rating hold**, within the accepted Prevalje record:
  TAB reports 1.325 MVA, HSE 1.325 MW. Both original observations are retained,
  active MW is null and quality is needs_review. These quantities may ultimately
  coexist, but no unity power factor or silent unit correction is assumed.
  No whole project rows were rejected or withheld from this five-project review.

TAB specifications include four rate-dependent Ah observations and their end
voltages, reference temperature, nominal voltage, dimensions, separate wet/dry
masses, mass tolerance, approximate resistance/fault current, terminal poles for
cells, operating/recommended temperatures, charge-voltage conditions, self-discharge,
normal DoD limit and qualified life/standards claims. Block Ah never becomes cell
Ah. Cell life of up to 20 years/1500 standard-test cycles and block footnotes of
18 years/1200 cycles remain distinct; none are warranties. Fault current is not
operating output. No energy, active power, efficiency or universal certification
was inferred. IP25 is scoped to the blocks page. Every row retains exact model,
source ID, original checksum and field/page/table locators.

Slovenian equipment and project roles remain separate: no OPzS model is assigned
to either commissioned BESS, and no LFP chemistry is inferred from TAB's wider
portfolio. Neoenergija is retained as customer, Kolektor sETup as the announced
market-operation provider, and Elektro Celje as supporting utility. Prevalje's
promised end-2025 HSE management takeover is not treated as verified completion.

## Source selection, rights and reconciliation

Attempted scalable Ireland coverage before relying on individual project releases.
The fresh EirGrid index links an August 2026 non-wind contracted report; a different
CMS landing returned 403 and the indexed generic download was a stale 2018 report.
EirGrid's disclaimer restricts public reuse absent authorization. ESB Networks'
Q3 2026 index exposed six current downloads, but its copyright page also restricts
public republication. Neither inventory was bulk imported. SEMO's market-report
route was inaccessible; private participant auction reports were not accessed and
auction awards were not treated as operation. The Statkraft owner portfolio was
then reconciled against all three existing identities, followed by the two TAB
project releases and HSE corroboration. Original bytes/checksums stay outside Git.

The TAB public catalogue and current HTML were checked for scope, copyright,
revision and a representative rendered table. No open bulk licence is claimed;
only bounded factual specifications are committed, not PDF text/images/documents.
All **28 accepted numerical table rows match the independently downloaded HTML**,
after explicitly reversing its wet/dry column order. The two website-only models
are not padded into the PDF edition. All created_at values and existing scalar,
nested and conflicting facts were preserved through reviewed additive upsert.
Exact identity and incoming-duplicate checks passed; replay is idempotent.

## Market priorities and coverage

The IEA commentary dated 29 May 2026 was freshly rechecked. Its comparable metric
is **2025 utility-scale battery power additions (GW)**. Among explicitly quantified
countries it orders China about 55, United States over 16, Australia about 4.2.
This is a selected-country ordering, not an exhaustive global rank. Europe's
regional value is not ranked as a country. Comparable operational stationary
energy GWh is unavailable in this source; no MW-to-MWh conversion is made.
The dated market file retains these limitations. This pass adds underserved
Slovenia and regional-manufacturer depth; all six geographic regions remain covered.

Current totals: **2,138 projects, 48 countries, 398 project sources; 1,092 equipment
records (1,079 exact configurations and 13 families), 55 supplier labels and 478
OEM sources**. This pass adds four project sources and two OEM sources. Cumulative
PR #172 versus unchanged main: four new projects, two enriched projects, 28 new
equipment and 17 previously enriched Microcare configurations. All remain proposed
in the open PR, not merged content.

## Implementation and validation

The new offline `stage_bess_tab_opzs.py` adapter stages either reviewed partition.
It fails on missing/duplicate rows, changed boundaries, swapped mass columns,
changed units/end voltages, malformed numbers or impossible ordering. Eleven new
synthetic tests exercise parsing and identity/measurement-boundary failures.
No shared schema/importer API or viewer files changed.

- 448 BESS Python tests passed, including the 11 new parser tests.
- Broader data-retrieval suite: 2,130 passed, four optional-dependency skips,
  three failures in unrelated climate-source tests from host
  `psutil.NoSuchProcess(pid=5)`. This is the same failure previously reproduced on
  unchanged main; it is not suppressed or patched. This is not a full-suite pass.
- Both catalogues validate; field-source references, duplicate checks, exact
  source-row corroboration, prior-fact preservation and idempotence pass.
- Two independent builds of each typed Zstandard Parquet snapshot are byte-identical;
  readback rows, types and compression checked. Snapshot manifests and coverage
  are committed; binary snapshots remain outside Git.
- Repository-wide Ruff, formatting and ty pass; hygiene and citation checks pass.
- Offline OEM example and all 25 viewer tests pass.
- Strict Sphinx with gallery execution disabled passes; 656 HTML pages pass the
  local links/assets check. Full offline gallery is left to remote CI.
- All three package distributions build; metadata/wheel checks are recorded with
  the publication checks. Final-head CI status is reported on the PR.

Open PR titles and changed paths were rechecked, including PV #173 (advanced during
this run), data centers #174, Wind #171, Hydro #167 and other active branches.
None overlap this BESS batch. Shared viewer, schemas, bibliography and docs config
were left untouched. The target head/main are checked again immediately before
normal expected-head publication; no force-push or automatic merge.

## Effort, yield and next action

Research/extraction and local validation took approximately 21 minutes from
13:54:15 to 14:15 Atlantic/Canary; publication/remote checks follow in the same run.
The 28-model batch meets the equipment planning range. Project yield is below
50–200 because two promising registry batches are rights-held, the reviewed owner
portfolio mostly already exists, and two new projects warranted precise role and
rating reconciliation. No extra phases, aggregate facilities or sparse rows were
invented to raise counts. The selected OPzS PDF partitions and five-project review
are exhausted; the broader backlog is not.

Next highest-yield equipment partition: TAB OPzV exact-model table, after checking
revision and its own conditions. Next project discovery: Saules BESS's eight-site
Latvian portfolio, requiring named site allocations and issuer-document review
before acceptance. Preserve CEA and Microcare source backoff dates, the four
Microcare monitoring holds, prior Chile Atacama/Solar Ray holds and all prior
rating conflicts. See the dated backlog for URLs, versions, permissions, cursors,
retry conditions and expected fields/yield. Recurring research remains active.
