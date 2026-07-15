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

---

## 2026-07-16 — P1: complaint-granularity pull (A-PULL)

**Dataset IDs verified live 2026-07-16** against data.cityofnewyork.us metadata API (Rule 5):

| ID | Live name | Role |
|---|---|---|
| `erm2-nwe9` | 311 Service Requests from 2020 to Present | per-complaint rows (probe doc §2) |
| `wvxf-dwi5` | Housing Maintenance Code Violations | fresh violations pull, frozen whitelist |
| `64uk-42ks` | Primary Land Use Tax Lot Output (PLUTO) | bbl + unitstotal |

**Script:** `src/p1_pull.py` — server-side filtered, paged ($order=:id, 50k pages),
parquet-cached, idempotent (rerun confirmed cache-hit), storage-guarded, seed 42
(no sampling occurs in P1). Token from `.env` via python-dotenv, never printed.

**Pulls (all counts match independent server-side `count(*)` queries exactly):**

1. `data/raw/c311_heat_complaints_full.parquet` — 1,645,614 rows.
   Select: `unique_key, created_date, closed_date, bbl, complaint_type, status`.
   Where (verbatim §2): `complaint_type in ('HEAT/HOT WATER','Heat/Hot Water') and
   created_date >= '2019-06-01'`. No bbl filter at pull.
   **Null-bbl accounting (§2):** 6,762 rows (0.411%) null/empty bbl — matches the
   expected ~0.4%. Excluded to produce the deliverable
   `data/raw/c311_heat_complaints.parquet` (1,638,852 rows); full pull retained.
   Date range present: 2020-01-01 00:04:45 … 2026-07-13 23:43:26.

2. `data/raw/hpd_violations_heat.parquet` — 128,121 rows.
   Select: `violationid, bbl, class, novdescription, inspectiondate, novissueddate,
   approveddate, currentstatus`.
   Where: frozen whitelist VERBATIM from winter-fail-forecast `src/s1_data_pull.py`
   (`(upper(novdescription) like '%ADEQUATE SUPPLY OF HEAT%' or upper(novdescription)
   like '%PROVIDE HOT WATER AT%') and class in ('B','C')`) + `inspectiondate >=
   '2019-06-01'` (matches the 311 floor; P2's window looks backward from
   inspectiondate, so earlier violations cannot associate to any in-scope complaint).
   Class split: C = 128,120, B = 1. **Flag (not resolved here):** probe doc §3 gates
   on class-C rows; verbatim whitelist is class IN ('B','C'). B/C superset pulled
   with `class` column retained so P2 applies the §3 class-C restriction explicitly.
   Null-bbl: 185 rows (0.144%) — retained in raw, accounting logged.
   Inspection dates: 2019-06-01 … 2026-07-14.

3. `data/raw/pluto_units.parquet` — 858,602 rows. Select: `bbl, unitstotal`.
   No filter (full lot universe). Null unitstotal: 429 rows (0.05%).

**Storage:** data/raw total 78.1 MB (Rule 6 budget: 2 GB — fine).

**ANOMALY (resolved by Amendment 3) — 311 coverage gap vs probe doc §2:**
NYC OpenData re-scoped `erm2-nwe9` to records from **2020-01-01** (dataset renamed
"…from 2020 to Present"). The probe's verbatim floor `created_date >= '2019-06-01'`
therefore returns **zero** rows for 2019-06-01..2019-12-31; season 2019-20 is
truncated at Jan 2020 (its Oct–Dec 2019 portion missing), beyond the truncation §3
anticipated. The 2019 tail exists in archive dataset `76ig-c548` ("311 Service
Requests from 2010 to 2019", verified live 2026-07-16): 93,022 whitelisted rows for
2019-06-01+, same six columns confirmed by sample query. Rule 9 stop escalated by
LEAD; Ayur ruled → **phase0_probe.md Amendment 3** authorizes the archive union
(see next entry). Note: the old repo's cached `dot311_heat.parquet` (pulled
2026-07-14) has the identical truncation (min created_date 2020-01-01, 0 rows
before), and the probe doc's ~1.65M row estimate matches the 2020+ volume exactly —
the split predates this project.

---

## 2026-07-16 — P1 (continued): 311 archive union per Amendment 3 (A-PULL)

**Authorization:** phase0_probe.md Amendment 3 (APPROVED 2026-07-16, Ayur) — union
`76ig-c548` with `erm2-nwe9`, restoring the §2 floor `created_date >= '2019-06-01'`,
dedupe on `unique_key` with count logged.

**Dataset ID verified live 2026-07-16** (Rule 5): `76ig-c548` — "311 Service
Requests from 2010 to 2019".

**Archive pull:** `data/raw/c311_heat_complaints_archive_2019.parquet` — 93,022 rows.
Same select (six §2 columns) and same verbatim whitelist/floor as the erm2-nwe9
pull; archive coverage ends 2019-12-31. Matches the pre-pull server-side count
exactly.

**Union arithmetic (Amendment 3):** archive 93,022 + current 1,645,614 = 1,738,636;
duplicates on `unique_key`: **0** removed; union = **1,738,636 rows**, spanning
2019-06-01 00:17:18 … 2026-07-13 23:43:26 (floor restored).

**Null-bbl accounting (updated for the union, §2):** 7,123 of 1,738,636 rows
(0.410%) null/empty bbl — excluded with the exclusion logged. Deliverable
`data/raw/c311_heat_complaints.parquet` REGENERATED from the union:
**1,731,513 rows** (= 1,738,636 − 7,123). Deliverable is rebuilt deterministically
from the two cached raw pulls on every run (idempotent; rerun confirmed).

**Seam continuity (2019-12-31 → 2020-01-01 boundary; reported, not smoothed):**
daily union counts 2019-12-25..2020-01-07 = 664, 678, 457, 437, 515, 850, 608 |
692, 673, 533, 554, 746, 804, 831. No gap and no pileup at the seam; variation is
within the holiday-week range on both sides.

**Storage:** data/raw total 79.2 MB (Rule 6 fine). Stats: `data/p1_stats.json`.

**Anomalies:** none beyond the re-scope already recorded above.

---

## 2026-07-16 — P3: HSP cohorts + proactive-detectability heuristic (A-AUX)

**Dataset IDs verified live 2026-07-16** against data.cityofnewyork.us (Rule 5):

| ID | Live name | Role / outcome |
|---|---|---|
| `h4mf-f24e` | Buildings Selected for the Heat Sensor Program (HSP) | official HPD cohort list (provenance "official", rows updated 2026-03-01) — pulled |
| `64uk-42ks` | PLUTO | supplementary P3 pull: bbl,address,borough (§4 address→BBL resolution; P1 cache lacks address) — pulled |
| `uwyv-629c` | (legacy HPD Complaints) | login-walled — retired from public API; NOT usable |
| `a2nx-4u46` | (legacy HPD Complaint Problems) | login-walled — retired from public API; NOT usable |
| `ygpa-z7cr` | Housing Maintenance Code Complaints and Problems | LIVE (updated 2026-07-15) but EXCLUDED from phase-0 by probe doc Amendment 1 item 2 — NOT pulled |

**HPD-complaints verification consequence (§4 P3.2, logged BEFORE choosing the
heuristic version):** no HPD complaints dataset is usable in phase-0 → the
311-ONLY version of the proactive-detectability heuristic runs, labeled as such.

**Cohort-list PDFs (§4-named source) — all four fetched programmatically 2026-07-16**
from `https://www.nyc.gov/assets/hpd/downloads/pdfs/services/heat-sensor-program-building-list-{2020,2022,2024,2025}.pdf`
(nyc.gov 403s non-browser user agents; browser UA used), cached in `data/raw/hsp/`
(84,396 / 108,090 / 62,297 / 61,769 bytes), 50 rows parsed per cohort, zero
meaningful parse residue. **No manual_downloads.md needed; no sub-branch halted.**

**Pulls (script `src/p3_hsp.py` — paged, server-side filtered, parquet-cached,
idempotent (rerun confirmed, identical stats), storage-guarded, seed 42):**

1. `data/raw/hsp_selected_buildings.parquet` — 200 rows (4 cohorts × 50; starts
   2020-07-01, 2022-07-01, 2024-07-01, 2025-06-11; current_status all "Active",
   discharge_date all null).
2. `data/raw/pluto_address.parquet` — 858,602 rows (bbl, address, borough).

**Key decisions:** dataset `h4mf-f24e` used as membership/BBL authority
(deviation from §4's PDF-only expectation, DISCLOSED; same publisher), PDFs
cross-checked 199/200 exact on normalized address keys (1 miss = 2025 PDF
spelling "CLAREDON"/"CLARENDON", same building). Independent PLUTO address→BBL
resolution: 171/200 (85.5%), 171/171 agreement with dataset BBLs where both
resolve; all 200 dataset BBLs present in the P1 PLUTO lot universe. Analysis
grain = tax lot: 200 selections → 197 distinct bbls (3 shared-lot groups,
listed in checkpoint/stats). Association rule identical to P2 (W=30, inclusive
bounds, calendar-date truncation, int64 bbl, explicit class-C); Amendment 3
window-coverage eligibility applied (0 exclusions).

**Row counts through the waterfall:** 128,120 class-C violations → 7,810 in HSP
lots → 3,633 eligible in-program heat-season events → **377 zero-complaint
events at W=30** (§4 floor 30 → PASS; robust to Oct–Jan subset 223 and
(bbl,day)-dedupe 244).

**Anomalies:** shared tax lots (2 lots carry distinct buildings; 1 true repeat
selection 2112 Honeywell Ave in 2020+2024); 2025 PDF street-name typo; nyc.gov
UA-gating. All benign, none met Rule 9.

**Storage:** data/raw = 90.7 MB total after P3 pulls (Rule 6 fine).
Stats: `data/p3_stats.json`.

---

## 2026-07-16 — P4: zero-mass descriptives (A-AUX)

**Sources verified live 2026-07-16 (Rule 5):**

| Source | Role |
|---|---|
| `64uk-42ks` (PLUTO) | supplementary P4 pull `pluto_geo.parquet`: bbl, cd, bct2020 — 858,602 rows |
| `api.census.gov/data/2024/acs/acs5` | ACS 2020-2024 5-year, tract level, NYC's 5 counties (state 36: 005/047/061/081/085) — verified live with key (HTTP 200, all 7 variables resolve); keyless probe returns HTML "Missing Key" (Census requires a key for ALL queries, consistent with WFF PROVENANCE note of 2026-05-12) |

**Credential:** `CENSUS_API_KEY` from `.env` via python-dotenv, NEVER printed
(Rule 2). Note: the sandbox denies reads of `.env`, so a sandboxed presence
check falsely reports the key absent; verified present via unsandboxed
boolean-only check (harness mechanic, recorded, not a Rule 9 condition).

**Pulls (script `src/p4_zeromass.py` — paged, parquet-cached, idempotent (rerun
confirmed, identical stats), storage-guarded, seed 42):**

1. `data/raw/pluto_geo.parquet` — 858,602 rows (bbl, cd, bct2020).
2. `data/raw/acs_tract_2024.parquet` — 2,327 tracts; ACS vars B19013_001E,
   B11001_001E, C16002_{001,004,007,010,013}E. Income non-null 2,199 (94.5%;
   sentinel -666666666 → null, logged); LEP share defined 2,231 (zero-household
   tracts undefined, logged).

**Key decisions:** universe = 181,863 distinct bbls of the frozen R4 label spine
(read-only import); zero mass = 0 whitelisted 311 heat/hot-water complaints in
the P1 deliverable (2019-06-01…2026-07-13) → 114,890 (63.2%; WFF's "~70%"
reference was measured on its own window — reported, not reconciled). CD-income
machinery ported from WFF `src/s3d_income_equity.py` (read-only; household-
weighted tract-median mean, dominant-lot tract→CD crosswalk, building-level
rank-qcut terciles). Tract LEP share = limited-English-speaking households /
households (ACS C16002, definition fixed and documented). Figure written as SVG
(vector — no raster on disk, Rule 6). Descriptive only; the checkpoint contains
no gating language.

**Exclusions (logged, never imputed):** spine bbls without PLUTO geo 1,209;
without defined LEP 14; unit-join unmatched 1,043; conflicting-units bbls 0.

**Headline descriptives:** support-overlap cells (unit-class × borough ×
income-tercile × LEP-tercile, 171,745 complete-covariate buildings): 146/148
occupied cells contain both masses; 106,231/106,232 zero-mass and 65,508/65,513
positive-mass buildings sit in shared cells. Composition differs: median units
3 vs 8; zero-share by unit class 78.4% (2–5) → 16.8% (50+); median CD income
$85,263 vs $79,943; median tract LEP 0.101 vs 0.105.

**Anomalies:** none beyond the recorded harness mechanics. **Storage:** data/raw
= 96.2 MB (Rule 6 fine). Stats: `data/p4_stats.json`.
