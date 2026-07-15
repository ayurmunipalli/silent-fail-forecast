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

---

## 2026-07-16 — Task 2: P1 complaint-granularity pull

**Dispatched by:** LEAD after bootstrap commit 0cd8294 (plan.md §3 step 3).

### What I did
1. Recovered dataset IDs and the frozen whitelist VERBATIM from the read-only old
   repo (`nyc-heat/src/s1_data_pull.py:41-46`); old repo untouched.
2. Verified all three dataset IDs live via the Socrata metadata API (Rule 5),
   logged to PROVENANCE.md with dates.
3. Ran server-side `count(*)` probes per source before pulling (non-empty check +
   storage projection).
4. Wrote `src/p1_pull.py` (paged, server-side filtered, parquet-cached, idempotent,
   storage-guarded, seed 42, token via python-dotenv never printed) and ran it.
5. Rerun confirmed idempotency (all three caches hit, identical stats).
6. Updated `data/PROVENANCE.md` in full (P1 section).

### P1 pull report

| Source | Cache | Rows | Notes |
|---|---|---|---|
| `erm2-nwe9` (311) | `c311_heat_complaints_full.parquet` | 1,645,614 | full pull, no bbl filter |
| — after null-bbl exclusion | `c311_heat_complaints.parquet` (deliverable) | 1,638,852 | 6,762 null-bbl rows (0.411%) excluded, logged; matches expected ~0.4% |
| `wvxf-dwi5` (HPD violations) | `hpd_violations_heat.parquet` | 128,121 | frozen whitelist verbatim, class B/C superset (B=1, C=128,120); 185 null-bbl (0.144%) retained+logged |
| `64uk-42ks` (PLUTO) | `pluto_units.parquet` | 858,602 | bbl+unitstotal; 429 null unitstotal |

All row counts match independent server-side count queries exactly.
**Storage:** data/raw = 78.1 MB (≪ 2 GB, Rule 6). Stats: `data/p1_stats.json`.

### Flags for LEAD / Ayur
1. **311 coverage gap (AWAITING RULING).** `erm2-nwe9` was re-scoped by NYC OpenData
   to 2020-01-01+ ("311 Service Requests from **2020** to Present"). The probe's
   verbatim floor 2019-06-01 returns zero 2019 rows; season 2019-20 loses Oct–Dec
   2019. The 2019 tail (93,022 whitelisted rows, same 6 columns confirmed) exists in
   archive `76ig-c548` ("311 Service Requests from 2010 to 2019", verified live) —
   NOT named in the probe doc, NOT pulled; pulling it is a deviation needing a
   ruling. The old repo's 2026-07-14 cache shows the identical truncation and the
   probe doc's ~1.65M estimate matches the 2020+ volume, so the split predates this
   project.
2. **Whitelist class conflict (flagged, not resolved).** Verbatim frozen whitelist =
   class IN ('B','C'); probe doc §3 gates on class C. Pulled the superset with
   `class` retained so A-GATE applies the §3 restriction explicitly. Numerically
   trivial here: exactly 1 class-B row.

**Anomalies otherwise:** none. No credential failures (one pip/network sandbox
mechanic, retried per harness guidance — not a Rule 9 condition).

---

## 2026-07-16 — Task 2 (continued): 311 archive union per Amendment 3

**Dispatched by:** LEAD relaying Ayur's ruling (option a); executed exactly per
phase0_probe.md Amendment 3, read in full before acting.

### What I did
1. Pulled `76ig-c548` (verified live 2026-07-16) under the same verbatim whitelist,
   same six §2 columns, `created_date >= '2019-06-01'` →
   `data/raw/c311_heat_complaints_archive_2019.parquet`, 93,022 rows (matches
   pre-pull server-side count exactly).
2. Extended `src/p1_pull.py`: union archive + current, dedupe on `unique_key`
   (count logged), deterministic sort, deliverable regenerated from cached pulls on
   every run. Rerun confirmed idempotency (both 311 caches hit, identical stats).
3. Updated `data/PROVENANCE.md` (new Amendment-3 section: ID + verification date,
   union arithmetic, updated null-bbl accounting, seam diagnostic).

### Union report
- **Arithmetic:** 93,022 (archive) + 1,645,614 (current) = 1,738,636; dedupes on
  unique_key = **0**; union = **1,738,636 rows**, 2019-06-01 … 2026-07-13 (floor
  restored).
- **Null-bbl (updated):** 7,123 / 1,738,636 = 0.410% — excluded, logged.
  Deliverable `c311_heat_complaints.parquet` regenerated: **1,731,513 rows**.
- **Seam continuity (reported, not smoothed):** daily counts 2019-12-25..2020-01-07:
  664, 678, 457, 437, 515, 850, 608 | 692, 673, 533, 554, 746, 804, 831 — no gap,
  no pileup at the archive/current boundary.
- **Storage:** data/raw = 79.2 MB (Rule 6 fine).

**Anomalies:** none. Zero overlap between the two datasets (dedupe count 0 —
consistent with a clean re-scope split at 2020-01-01).
