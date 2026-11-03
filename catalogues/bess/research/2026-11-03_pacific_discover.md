# Pacific portfolio and Discover equipment — 3 November 2026

Started 04:48 UTC (Atlantic/Canary also UTC). Main a95521c includes merged PR86;
PR88 changes only viewer files and was kept separate. No open BESS catalogue PR
was found. Existing schemas, dictionaries, manifests, sources and the latest
Tonga/EMS backlog were reviewed before accepting new identities.

## Accepted scope

Eight projects added: six Cook Islands sites and two Samoa installations. Two
existing Tonga records gain historical design observations (Tungua and Niuafoou);
these do not resolve or erase existing conflicts. Eleven exact Discover Battery
models added: seven DRY CELL solar monoblocs and four AES modules/packs. No OEM
record enrichments, no permanent record rejections. New countries: Cook Islands
and Samoa; new supplier: Discover Battery. Six-region coverage retained.

Branch totals: 1,738 projects / 37 countries / 215 sources; 536 equipment records /
41 suppliers / 241 sources. Main baseline: 1,730 projects and 525 equipment.
All additions are proposed, not merged. Existing creation times and facts preserved.

## Evidence and decisions

The downloadable PPA/SEIAPI September 2020 regional portfolio was processed before
individual announcements. Its acknowledgement identifies GSES with TAU, EPC and
TPL operator support and technical-committee review. The copyright page was checked;
no open bulk licence is asserted. Only selected factual observations are recorded;
the full report remains outside Git with SHA256 in the source register.

Nine new-site candidates reviewed: eight accepted; the Rarotonga 2.6 MW/10.5 MWh
entry is deferred because the narrative describes two facilities without separating
their individual capacity scopes. Table 3's four outer-island capacities sum to
8.4 MWh, versus Infratec's 7.3 MWh portfolio. Four energy fields are quarantined
rather than allocating the discrepancy. Per-site power and EPC identity are retained.
Aitutaki's 502 kWh is the dated PPA observation, not a silently rounded 500 kWh.
Installation years are not substituted for contractual COD. September 2020 status
uses report-month-end with explicit precision; no current operating claim is made.
Samoa's 2018 Fiaga installation is distinct from newly discovered 2026 procurement.

All eleven exact OEM candidates accepted. Four source documents were reviewed:
DRY CELL REV B; AES 6650 805-0065 REV C; rackmount 805-0043 REV D; AES 3000
805-0025 REV C. OEM direct downloads returned 403; complete primary PDF tables
were available in the web reader. Checksums are explicitly unavailable, not fabricated.
No copyrighted PDFs are committed and no open OEM bulk licence is inferred.

DRY CELL Ah stays rate-dependent at 30 C and 1.75 V/cell; it is not converted to
energy or stored as cell Ah. Case height excludes terminals. Rackmount heated and
unheated variants are actual model numbers, not invented combinations. Continuous
70 A and one-hour 95 A limits stay separate. Cell temperatures are not assigned to
ambient temperature columns. AES 6650's nominal 7.39 kWh is distinct from rated
6.65 kWh at 1C; old nominal 6.656 kWh editions are not conflated. AES 3000's
114 A twenty-minute rating is not continuous power. No warranty, energy efficiency,
active power, chemistry or certification is inferred beyond the reviewed fields.

The existing upsert API and validators were used. Two reviewed nested-JSON updates
preserve every previous scalar fact and creation timestamp. No parser or schema
change was needed for the manually reviewed tables. Separate typed Zstandard
Parquet builds and coverage/completeness manifests match; binaries remain build
artifacts outside Git.

The IEA May 29, 2026 comparison was reopened. The existing dated ranking remains
2025 stationary power additions (GW): quantified examples China >63, US19,
Australia nearly8, Chile approaching1. It is neither exhaustive nor operational
energy GWh. No comparable operational-energy ranking was obtained or fabricated.

Project yield is below 50–200 because the selected regional source has eight
individually defensible new sites and one unresolved aggregate. Eleven exact models
meet the equipment objective. All selected model rows are exhausted. Additional
sources were checked: Infratec portfolio/completion, EPC public tender index and
JICA Samoa planning-table discovery. The latter two need phase/identity review;
Fiaga's NDA-gated detail is not accessed. Ranked backlog records exact next actions.

## Validation and elapsed effort

- 1,746 Python tests passed, one optional cdsapi dependency skipped; 30 focused
  catalogue/analysis tests also passed.
- Both catalogue validators and two independent Parquet/manifest builds passed.
- Eleven viewer tests, both offline examples, Ruff lint/format, ty, citation and
  repository hygiene checks passed. The first ty attempt selected the wrong
  environment; explicit local environment selection fixed it. The temporary
  environment symlink was removed before the final hygiene check.
- Main advanced to 15e9d60 as dashboard PR88 merged; incorporated without conflicts
  and all eleven viewer tests were rerun. Wind PR89 was inspected by changed paths;
  no BESS catalogue overlap. Shared reference changes remain additive.
- Research/reconciliation about 4 minutes; validation/publication about 5 minutes
  at the final checkpoint, approximately 9 minutes total. Selected source tables
  are exhausted, not an assertion that global research is exhausted. Follow-up
  phase reconciliation is preserved in the backlog. No idle time added.
- Shell push lacked credentials; connected GitHub API used instead. Uploaded blob
  hashes were independently compared to local files. Remote CI is separate from
  local validation. No automatic merge.

Final integrated strict Sphinx build succeeded; all 420 HTML pages pass local link
and asset checks. Final validation checkpoint approximately 04:57 UTC. Package
builds were not repeated because no package code/schema/dependency changed.
