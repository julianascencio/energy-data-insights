# Replaying one GEM publication batch

The original replay command emits the complete 56,605-record approved recovery.
Use the explicit batch selector for a single scoped PR. Selection occurs **after**
the checksum-pinned workbook is parsed, source/technology/identity gates run against
the catalogue, and the complete accepted-ID digest is verified. It does not relax
the original screening or turn held records into accepted records.

```bash
uv run python scripts/stage_pv_gem.py \
  --input /path/to/Global-Solar-Power-Tracker-February-2026.xlsx \
  --review catalogues/pv/research/20261102_gem_review.json \
  --summary catalogues/pv/research/20261102_gem_summary.json \
  --batch 4 \
  --output /tmp/gem-batch04.jsonl
```

This produces only the 3,666 approved records in UUID prefixes `30`–`3f`.
Both `--batch` and `--summary` are required together. Omitting both preserves
the full-set replay behavior. Existing output files are never overwritten.

All ledger partitions are checked, including ones not selected: unique batch
numbers, valid lowercase hexadecimal prefix bounds, disjoint exhaustive coverage,
record counts and exact country distributions. Partial input, duplicate IDs,
changed accepted identities, source/entity mismatches and inconsistent ledgers fail
before output. The selected records retain their original values and timestamps.

After review, use the existing catalogue upsert API, validate, build a fresh
Parquet snapshot and inspect the staged Git paths. This command does not push,
merge, create PRs or authorize acceptance. Recheck current main and every open
research PR before publication. New overlapping catalogue identities may cause the
complete-set digest to fail: reconcile and re-review rather than bypassing it.

The prepared-union total is not the total on any individual batch branch or main.
Use each checkout's freshly built manifest for its actual counts. Do not overwrite
the historical launch baseline or the immutable recovery ledger with live counts.
