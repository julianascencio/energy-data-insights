# 2 November 2026: South African reconciliation and battery pack specifications

Started20:54:17 Atlantic/Canary (UTC+00). PR79 was merged; isolated worktree from current main38587c2. Read updated CONTRIBUTING (including descriptive method naming), workflow, dictionaries/schema, source registers, latest manifests and prior holds. Open PR47–49 inspected by title and paths: workflows only. No overlapping BESS PR. No shared code/schema or PV edits.

## Accepted and held

**12 new exact Victron batteries**: eight Lithium Battery Smart and four12.8V Lithium NG configurations. Nominal energy, voltage, temperature-dependent Ah (pack, not cell), charging/discharging currents, pulse10s ratings, dimensions, IP and conditional lifecycle claims. NG resistance uses explicit two-column spans; BMS is separate, Bluetooth resides in BMS; NG mass is estimated and remains qualified. Smart final model has an HTML colspan, not multiple configurations. Published4220Wh/5210Wh retained as printed, never silently repaired from V×Ah. Efficiency92% has unspecified measurement boundary, not AC-to-AC. Certifications withheld pending scope review. No power/energy extrapolation, project assignments or warranty invention. Manual reviewed table extraction reused existing HTML cell reader and existing upsert API; no new parser/schema.

**Four Hubble models enriched** with enclosure/protection details, AM-4 discharge/storage limits and AM10+/AM16+ control current-limiter thresholds (not charge ratings). All previous nested facts, revision distinctions and conflicts preserved. AM-4 website reverses approximate/greater-than cycle qualifiers versus existing datasheet: one additional equipment conflict quarantined. AM2/AM2+ held for successor identity and116/117Ah difference; no thin variant added.

**Five South African projects enriched**, no new projects. Publicly disclosed owner Integrated Report2024 hosted at World Bank, PDF83/printed81, explicitly establishes15October2024 COD for Pongola/Elandskop. Keep WSP acceptance and lender November commissioning observations separately. Skaapvlei/Paleisheuwel/Graafwater gain historical completion of battery equipment manufacture/delivery; newer lifecycle states unchanged.

Project inventory attempt: Eskom12-site portfolio, eight linked licence applications, dated2022 award tables and lender alternatives. Seven sites already canonical; five prior holds remain. Eskom termsPDF sections2.1–2.2 and2.10 restrict reuse/automated collection; stopped direct ingestion after reading them. No coordinates/design claims from that restricted batch committed. World Bank disclosure provided the independent access route for bounded milestone facts; copyright remains with publisher and full documents are not redistributed. Searches for new lender reports found the already cataloguedMay2026 AfDB report. No stale forecast promoted to operation. Rietfontein, Witzenberg, Ashton, Cuprum and Kiwano remain held.

Totals:1,707 projects/34countries/203sources;451 equipment/39suppliers/201sources (438configurations,13families). No new countries/OEMs. Six-region coverage retained. No whole-record rejection or new project rating quarantine. Equipment12new+4enriched; one held identity and one new field-conflict record.

## Evidence and continuation

Original accepted-source bytes and SHA256 remain outside Git. Sources and per-field evidence, exact model-column review, audit, deterministic typed Zstandard manifests and backlog committed. No full source documents/binary snapshots in Git. IEA29May2026 country examples rechecked:2025 stationary power additions China>63GW,US19GW,Australia nearly8GW,Chile nearly1GW. These are annualGW additions, not exhaustive operationalGWh ranking; regions kept separate.

Selected two OEM tables and five AM pages are exhausted. Project yield below50–200 because existing identities, stale lifecycle evidence and restrictive inventory terms prevented safe bulk acceptance; equipment working range reached. Next highest value: exact25.6/51.2V NG manual tables, new lender lifecycle disclosures, and held OEM identity reconciliation. Do not repeat blocked Eskom collection or completed French>=1MW/40RollsLFP partitions.

## Validation

Validation results and elapsed effort finalized before publication below. Initial environment reused another worktree's editable packages; this produced reference/type discovery failures. Created a fresh locked environment for this worktree and reran checks; no failed check is treated as passed.

Final full Python suite: **1,647 passed, one optional cdsapi skip**. Both catalogue validators, source-byte hash audit, original facts/creation dates/conflict preservation, deterministic repeated typed Zstandard builds, Ruff/format, ty, hygiene and citation checks passed. Eight viewer DOM tests, both offline examples, three package builds, six Twine artifacts and installed-wheel public entry points passed. Strict documentation and final local-link checks are recorded below after completion. Initial snapshot rerun refused existing output directories; reran in fresh final directories successfully. No implementation/schema changes required new parser tests.

Candidate accounting:12 portfolio sites→5enriched,2existing unchanged,5previous holds retained;17 OEM candidates→12new,4enriched,1held. One additional equipment qualifier conflict; no new project field conflict or whole-record rejection. Detailed accepted model columns and preservation audit are adjacent JSON.

Strict Sphinx passed;405 HTML pages passed local links/assets. Active effort through publication preparation approximately13minutes (20:54–21:07 Atlantic/Canary). Selected defensible tables exhausted; source access restrictions and prior coverage explain lower project yield. Main rechecked at38587c2; leave the new research PR open, no merge.
