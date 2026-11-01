# BESS OEM research iteration

Extend the OEM product catalogue, preserving the current IDs, sources and dates.
Read the schema, README and latest research report before collecting records.

1. Inspect open PRs and latest main. Use an isolated branch. Reuse a matching OEM
   research PR only when its scope and ownership are clear; never force-push.
2. Prioritize uncovered suppliers and missing specifications over duplicate family
   records. Research OEM-hosted datasheets, manuals, product pages and investor
   releases; use third-party directories only to find primary evidence.
3. One exact model/configuration per row. Preserve model punctuation and regional,
   voltage, hardware and printed document revisions. Configurable families stay
   labelled; never create a Cartesian product of independently advertised options.
4. Extract active MW, apparent MVA, energy basis/boundary, duration, cell chemistry,
   voltage, cooling, enclosure, temperatures, dimensions, weight, PCS/EMS, protocols,
   source-qualified efficiency, lifecycle and standards claims when documented.
5. Retain conditions and footnotes. Inspect PDF images when extraction loses signs,
   table-column alignment or qualifiers. Leave unsupported values null.
6. Register exact sources and cite each field. Retain creation dates. Changed evidence
   receives a new source revision and substantive update date. Keep incompatible
   observations in conflicts instead of automatically choosing the larger number.
7. Reconcile aliases and historical/discontinued products. Never infer product
   availability from an old launch release. Do not copy specs between generations.
8. Validate, rebuild Parquet and browser assets, run catalogue/viewer tests, and
   update the research report with added records, field coverage, limitations and
   excluded candidates. Report supplier counts separately from configuration counts.

This procedure is not a schedule. Any future automation must be separately authorized.
