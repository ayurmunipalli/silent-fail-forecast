# A-PULL agent log — silent-fail-forecast phase-0

## 2026-07-16 — Task 1: Bootstrap (R4 frozen-artifact import)

**Dispatched by:** LEAD (plan.md §3 step 2). Scope: bootstrap only — P1 not started.

**What I did:**
1. Read `.claude/agents/a-pull.md`, `CLAUDE.md`, `phase0_probe.md` (full, incl.
   Amendments 1–2) before acting.
2. Verified all three R4 artifacts exist at `<WFF_PATH>` =
   `/Users/ayurmunipalli/Desktop/super-grind/nyc-heat` (read-only; never written to).
3. Created `imports/` and copied the three artifacts with `cp`.
4. Computed sha256 (`shasum -a 256`) on each ORIGINAL and each COPY.
5. Created `data/PROVENANCE.md` (Rule 8a — first action of the repo) recording date,
   source paths, sizes, sha256s, and the originals-untouched statement.

**Results (copy = original for all three):**

| File | Size (bytes) | sha256 |
|---|---|---|
| `imports/primary_lgbm.txt` | 1,234,931 | `cd95a00e692a3d406c1a3aff1cabd1c3a384be227f7accea0dd97db7bdd38c93` |
| `imports/building_season_labels.parquet` | 7,560,686 | `1c9be931c222fa852aeeb7dbaa1a3ef6dad996e0deac899069c1143b573974eb` |
| `imports/test_predictions.parquet` | 24,372,862 | `fa8dc996e1789ce867c54bf510e4a90ccea6e73190bcbcd6047b2b16b722ff3e` |

**Integrity:** all three original↔copy sha256 pairs match exactly. Sizes match.

**Anomalies:** none. No sandbox failures, no missing artifacts, no mismatches.

**Storage:** imports/ ≈ 33.2 MB total (Rule 6 budget unaffected).

**Not done (out of current dispatch):** P1 pulls — awaiting separate LEAD dispatch.
I did not commit (workers never commit; LEAD commits the bootstrap stage).
