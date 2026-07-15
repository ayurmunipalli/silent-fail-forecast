# PROVENANCE.md — silent-fail-forecast

Provenance record per CLAUDE.md Rule 8a. Updated in the same commit as every probe
stage. Entries appended, dated, never edited in place.

---

## 2026-07-16 — Bootstrap: R4 frozen-artifact import (A-PULL)

**Action:** copied the three R4 frozen artifacts (probe doc §0 R4) from the
winter-fail-forecast repo into `imports/`. Source repo is READ-ONLY; originals
untouched (copy only — no write, edit, or delete performed under the source path).

**Source repo path (<WFF_PATH>):** `/Users/ayurmunipalli/Desktop/super-grind/nyc-heat`

| File (in `imports/`) | Source path (relative to <WFF_PATH>) | Size (bytes) | sha256 |
|---|---|---|---|
| `primary_lgbm.txt` | `outputs/models/primary_lgbm.txt` | 1,234,931 | `cd95a00e692a3d406c1a3aff1cabd1c3a384be227f7accea0dd97db7bdd38c93` |
| `building_season_labels.parquet` | `data/processed/building_season_labels.parquet` | 7,560,686 | `1c9be931c222fa852aeeb7dbaa1a3ef6dad996e0deac899069c1143b573974eb` |
| `test_predictions.parquet` | `outputs/test_predictions.parquet` | 24,372,862 | `fa8dc996e1789ce867c54bf510e4a90ccea6e73190bcbcd6047b2b16b722ff3e` |

**Integrity check:** sha256 computed on each ORIGINAL and each COPY with
`shasum -a 256`; all three pairs match exactly. File sizes of copies match
originals byte-for-byte.

**Anomalies:** none.

**Storage note:** imports/ total ≈ 33.2 MB — negligible against the 2 GB tabular budget (Rule 6).
