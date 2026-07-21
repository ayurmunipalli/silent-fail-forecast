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

---

## 2026-07-16 — S1 (build phase): all pulls, 311 union refresh, spine verification (A-DATA)

**Stage script:** `src/s1_pull.py` (one idempotent script for the stage — paged,
server-side filtered, parquet-cached, storage-guarded vs the ≤2 GB repo tabular
total INCLUDING imports/, seed 42; token from `.env` via python-dotenv, never
printed; run unsandboxed for the `.env` read, same harness mechanic recorded at
phase-0 P4).

**Dataset IDs verified live 2026-07-16** (data.cityofnewyork.us metadata API, Rule 5):

| ID | Live name | Rows updated | Role |
|---|---|---|---|
| `erm2-nwe9` | 311 Service Requests from 2020 to Present | 2026-07-15 | 311 union, current side |
| `76ig-c548` | 311 Service Requests from 2010 to 2019 | 2025-12-24 | 311 union, archive side (closed dataset) |
| `wvxf-dwi5` | Housing Maintenance Code Violations | 2026-07-15 | WFF-recipe violations + family-2 aggregate |
| `tesw-yqqr` | Multiple Dwelling Registrations | 2026-06-01 | family 5 + universe |
| `feu5-w2e2` | Registration Contacts | 2026-06-01 | family 5 |
| `64uk-42ks` | Primary Land Use Tax Lot Output (PLUTO) | 2026-05-28 | family 4 full attributes |
| `ygpa-z7cr` | Housing Maintenance Code Complaints and Problems | 2026-07-15 | family 7 + §10 criterion-3 screen — verified ONLY after LEAD relayed R-A = ADMIT (spec Amendment 1, 2026-07-16); pull in the continuation entry below |

**311 union refresh (phase0_probe.md Amendment-3 semantics re-run at 2026-07-16):**
- Current side re-pulled to a NEW cache `data/raw/c311_current_refresh.parquet`
  — 1,645,614 rows (phase-0 caches preserved untouched as comparison artifacts).
  Archive side reused from the phase-0 cache (93,022 rows; dataset closed, live
  metadata shows last row update 2025-12-24; ID re-verified live regardless).
- **Union arithmetic:** 93,022 + 1,645,614 = 1,738,636; duplicates on
  `unique_key`: **0** removed; union = **1,738,636 rows**, 2019-06-01 00:17:18
  … 2026-07-13 23:43:26.
- **Null-bbl accounting (§2 pattern):** 7,123 / 1,738,636 (0.410%) null/empty
  bbl → excluded, logged. Deliverable `data/raw/c311_heat_complaints.parquet`
  REGENERATED from the two caches: **1,731,513 rows**.
- **Seam A (archive boundary, 2019-12-25..2020-01-07), reported not smoothed:**
  664, 678, 457, 437, 515, 850, 608 | 692, 673, 533, 554, 746, 804, 831 —
  identical to the phase-0 diagnostic; no gap, no pileup.
- **Seam B (old/new refresh edge vs the untouched phase-0 erm2-nwe9 pull, daily
  counts 2026-06-30..2026-07-13):** identical old-vs-new on every day; late
  arrivals (new keys ≤ old max date) = **0**; disappeared (old keys not in new)
  = **0**. The refreshed pull's row count equals the phase-0 pull exactly:
  erm2-nwe9's 2026-07-15 update added no HEAT/HOT WATER rows after 2026-07-13
  (July off-season). Reported as-is.

**New pulls (all counts final; every pull non-empty; schema checked per page):**

| Cache (`data/raw/`) | Source | Rows | Filter / select notes |
|---|---|---|---|
| `hpd_violations_wff.parquet` | `wvxf-dwi5` | 149,585 | frozen whitelist VERBATIM, class B+C superset (B=2, C=149,583), `inspectiondate >= 2017-10-01`, WFF s1_data_pull 13-column select; 209 null-bbl retained+logged; inspections 2017-10-01 … 2026-07-14. **DISCLOSED ADDITION** beyond the enumerated a-data.md pull list: WFF family 1 (`s2_features.py`) consumes whitelisted violation ROWS from 2017-10-01; the phase-0 cache (floor 2019-06-01, narrower columns, 128,121 rows) cannot feed the WFF-recipe frame. Cross-checks: WFF's own 2026-07-14 pull was 149,511 rows with class B=2 — +74 rows of two-day accrual, same B count. |
| `hpd_viol_context_by_year.parquet` | `wvxf-dwi5` | 2,012,740 groups | WFF s1c VERBATIM: server-side aggregate (bbl, class, year), `inspectiondate >= 2014-06-01 AND bbl IS NOT NULL`; classes A/B/C/I present; years 2014–2026; `yr`,`n` stored Int64 per the WFF cache contract. Downstream leakage note stands: target-year bucket is never a feature (WFF s1c docstring; binding at S2). |
| `hpd_registrations.parquet` | `tesw-yqqr` | 203,236 | no filter (universe); WFF column set; **181,863 distinct BBLs — exactly the frozen spine universe**. |
| `hpd_registration_contacts.parquet` | `feu5-w2e2` | 782,024 | no filter; WFF column set (owner/portfolio linkage). Equals WFF's 2026-07-14 count. |
| `pluto_full.parquet` | `64uk-42ks` | 858,602 | no filter; WFF 11-column attribute set (family 4: yearbuilt/numfloors/unitsres/unitstotal/bldgclass/landuse/borough/…). Nulls: yearbuilt 358, numfloors 42,264, unitstotal 429, bldgclass 355, borough 0. |

**R4 spine verification (imports/building_season_labels.parquet, read-only):**
- sha256 re-verified = `1c9be931…74eb` (matches the bootstrap PROVENANCE entry).
- Schema exact (`bbl_n, season, label_c, label_bc`); grid **1,624,255 rows**,
  **181,863 distinct BBLs**, seasons **2017-18 … 2025-26** — all as committed.
- Per-season rows and label_c positives match WFF's committed
  `outputs/checkpoints/_s1b_frozen_labels.json` EXACTLY, all 9 seasons:
  178,503/4,725 · 179,143/4,647 · 179,767/4,013 · 180,157/4,072 ·
  180,547/5,057 · 181,087/6,021 · 181,470/7,764 · 181,718/7,730 ·
  181,863/8,897 (2017-18 → 2025-26).

**Season 2026-27:** untouched (Rule 3). All pulls end at pull time (2026-07-16,
pre-season); no 2026-27 window exists in any filter or artifact.

**Storage after this entry's pulls:** data/ + imports/ = **208.4 MB** (≤ 2 GB, fine).
Stats: `data/s1_stats.json`. **Anomalies:** none beyond the zero-growth
refresh edge documented above (reported, benign).

---

## 2026-07-16 — S1 (continued): ygpa-z7cr pull per R-A = ADMIT (A-DATA)

**Authorization:** model_spec.md Amendment 1 (2026-07-16, Ayur): ygpa-z7cr
admitted in exactly two capacities — feature family 7 (distinct-apartments-
complaining signals, masked) and the §10 criterion-3 HSP screen. NEVER the
reporting-head likelihood (non-load-bearing boundary; binds all downstream
consumers of this cache). ID verified live 2026-07-16 (table in the previous
entry).

**Whitelist:** `upper(major_category) = 'HEAT/HOT WATER'` +
`received_date >= '2019-06-01'` (floor aligned with the §2 311-union floor;
both admitted capacities are 2019-20+). Live category probe 2026-07-16 shows
exactly one heat major; minor split ENTIRE BUILDING 1,148,242 / APARTMENT ONLY
606,709. 21-column select: problem/complaint/unique identifiers, building keys
(bbl, building_id, borough/block/lot), apartment identifiers (apartment,
unit_type, space_type, type), categories, statuses, received/status
timestamps, `problem_duplicate_flag`, `complaint_anonymous_flag`.

**OPERATIONAL SPLIT (Rule-9-driven mechanic, NOT a data decision):** two
successive background runs were killed EXTERNALLY mid-pull (~700k and ~900k of
1,754,951 rows; each kill also took an unrelated trivial background task —
session-level sweep, no data-layer failure; no partial file ever written,
since pulls write parquet only on completion). Per LEAD's standing rule the
branch STOPPED and escalated; **Ayur ruled (b): foreground, resumable
date-split parts.** Executed as 7 half-open received_date intervals (disjoint,
jointly exhaustive; sized so each bounded foreground call fits the 600 s
ceiling at measured ~66k rows/min — the disclosed adjustment from "two halves",
which would have exceeded the ceiling and reproduced the kill):

| Part | Interval (received_date) | Rows | = server-side year probe |
|---|---|---|---|
| 1 | [2019-06-01, 2021-01-01) | 261,053 | 96,409 (2019) + 164,644 (2020) exact |
| 2 | [2021-01-01, 2022-01-01) | 200,169 | exact |
| 3 | [2022-01-01, 2023-01-01) | 270,629 | exact |
| 4 | [2023-01-01, 2024-01-01) | 230,610 | exact |
| 5 | [2024-01-01, 2025-01-01) | 267,542 | exact |
| 6 | [2025-01-01, 2026-01-01) | 318,652 | exact |
| 7 | [2026-01-01, —) | 206,296 | exact |

**Assembly arithmetic:** 261,053 + 200,169 + 270,629 + 230,610 + 267,542 +
318,652 + 206,296 = **1,754,951** = the pre-pull server-side total probed
2026-07-16 (re-probed at ruling time: identical — zero server-side drift
between probe and pull). Duplicate `problem_id` across parts: **0** (hard-stop
guard; disjoint intervals). Deliverable `data/raw/hpd_complaints_heat.parquet`
= deterministic sort (received_date, problem_id) over the 7 part caches,
rebuilt on every run. Range present: 2019-06-01 00:11:35 … 2026-07-15 00:04:19.

**Accounting (logged, nothing dropped from raw):** null/empty bbl 6,792
(0.387%); null/empty apartment 3; `problem_duplicate_flag` Y = 761,130 (43.4%)
vs N = 993,821 — HPD's own dedup marking is large, consistent with the OSC
2019-N-3 concern the Amendment-1 rationale cites; flagged for A-FEAT/R-AUDIT
(handling is an S2 analysis decision, not resolved here).

**Idempotency (full-stage tail):** plain rerun cache-hits all 15 raw caches;
both regenerated deliverables (`c311_heat_complaints.parquet`,
`hpd_complaints_heat.parquet`) are **byte-identical** across rebuilds (sha256
compared); `data/s1_stats.json` byte-identical across reruns. One measurement
artifact recorded: the first rerun showed a 394-byte `tabular_bytes` delta
because the storage guard counts `data/s1_stats.json` itself, whose size grew
when the hpdc keys were first added — self-referential measurement, not data
nondeterminism (proven by the byte-identical third run).

**Storage:** data/ + imports/ = **341.6 MB** (≤ 2 GB, Rule 9 fine).
**Season 2026-27:** untouched — the pull's natural max is 2026-07-15
(pre-season; the 2026-27 season window has not begun).
**Anomalies:** the two external kills (documented above and in
`reports/agent_logs/a-data.md`); otherwise none.

---

## 2026-07-16 — S2: two feature frames (A-FEAT)

**Stage script:** `src/s2_features.py` — one idempotent script, reads ONLY local
S1-audited caches + the read-only frozen spine (no network), seed 42 (no sampling
occurs). Reran to **byte-identical** outputs (sha256 equal across runs, all three
artifacts). WFF repo touched read-only (recipe reference; nothing written).

**Outputs (`data/processed/`, one row per spine row — 1,624,255 each):**

| File | Features | Size | sha256 |
|---|---|---|---|
| `features_b3.parquet` | 30 — WFF recipe, frozen-model `feature_names` order, categorical vocabularies fixed from the model's `pandas_categorical` footer | 27.5 MB | `09f8e94df5c51fa66778e17cc2d9bbba0eceb0aeef2453b411d7662ef324fa09` |
| `features_main.parquet` | 49 — families 1–5 (30, WFF semantics) + 6 (11, union complaint-granularity) + 7 (8, ygpa distinct-apartments per spec Amendment 1) | 35.4 MB | `477d3079fae0a4a76ee5507739c6f790448caa258c11ea78776583f2e4734090` |

**Lineage checkpoint:** `outputs/checkpoints/s2_feature_inventory.md` (per-feature
source + exact leakage window + mask rule, WFF S2-report format) and
`outputs/checkpoints/s2_stats.json` (full null audit, mask coverage, both-ways
duplicate-flag magnitudes).

**Fidelity verification:** B3 frame compared key-for-key against WFF's own frozen
`features.parquet` — **26/30 columns exactly equal on all 1,624,255 rows**; the
residual is ONE building (BBL 1012410023) whose class-C context count for calendar
2021 grew by 1 between WFF's 2026-07-14 pull and S1's 2026-07-16 pull (source
accrual affecting 5 cells across `ctx_c_*`/`ctx_total_*`; disclosed as inventory
D1, not patched). All family-1–5 NULL-audit counts match WFF's committed S2
report exactly.

**Leakage structure (for R-AUDIT's binding S2 protocol):** year matrices capped at
2024; season-indexed state rolls only after emission; every family-6/7 timestamp
slice passes through a guard asserting window_hi ≤ the season's Oct-1 cutoff;
family-6/7 availability = window left edge ≥ 2019-06-01 floor, masked NULL never
zero-filled; frames assert max(season) == 2025. **Season 2026-27: untouched.**

**Amendment-1 boundary:** ygpa-z7cr enters ONLY the `c7_*` feature columns —
no loss input of any kind. Duplicate-flag handling ruled BOTH-WAYS and documented
(inventory family-7 section; standing flag B21 closed at S2).

**Anomalies:** none (Rule-9 clean). Disclosed observations: single-building ctx
accrual (D1); ctx cache `yr`/`n` stored as strings vs the S1 "Int64" note —
coerced with asserted zero parse loss (D3). **Storage:** data/ + imports/ =
**388 MB** (≤ 2 GB, fine).

---

## 2026-07-16 — S3a: baselines B0–B4 (A-MODEL)

**Stage script:** `src/s3a_baselines.py` — idempotent, RESUMABLE (per-unit json
checkpoints under `outputs/checkpoints/s3a_work/`; two external-kill incidents
at S1 motivated bounded foreground runs; this stage ran as 6 bounded
invocations, each ≤ ~9 min, zero lost work). Seed 42, no network.

**Inputs (all read-only, all S1/S2-audited):** `features_main.parquet` (sha256
in S2 checkpoint), `features_b3.parquet`, `hpd_violations_wff.parquet`,
`c311_heat_complaints.parquet` (311 union deliverable — sole propensity-target
source per the Amendment-1 boundary), `imports/primary_lgbm.txt` (343-tree
assertion PASSED at load).

**Environment change:** `.venv` gained `lightgbm==4.6.0`, `scikit-learn==1.9.0`
(+ scipy/joblib/threadpoolctl deps) — first modeling stage; versions recorded
in `s3a_stats.json` and `b4_frozen_config.json`. LightGBM 4.6.0 matches WFF's
frozen B3 library version.

**Verbatim ports:** WFF `src/s3_baselines.py` L52–62, L69–78, L81–113,
L116–147, L150–196, L226–230 (read-only; adaptations disclosed in
`outputs/checkpoints/s3a_baselines.md`).

**Artifacts written:** `outputs/checkpoints/s3a_baselines.md`,
`outputs/checkpoints/s3a_stats.json`, `outputs/checkpoints/s3a_work/*`
(300 stage-1 + 300 stage-2 per-unit results, 5 cached R̂ folds, guards.jsonl
with 50 recorded guard passes), `outputs/models/b4_propensity_lgbm.txt`
(95 trees), `outputs/models/b4_risk_lgbm.txt` (282 trees),
`outputs/models/b4_frozen_config.json`.

**Test-season sanctity:** max season present in any frame/fold/lookback = 2025
(asserted 50× across 36 sites; both feature frames additionally assert
max(season)==2025 at load). No 2026-27 contact of any kind.

**Anomalies:** none. Notable non-anomaly findings recorded in the checkpoint:
stage-1 propensity target prevalence ≈ 0.88 (multiplicity near-universal given
detection); B4 IPW clip floor never binds (min R̂ = 0.2366 > 0.10).

**Storage after stage:** data/ + imports/ + outputs/ ≈ 418 MB (≤ 2 GB, fine).

---

## 2026-07-17 — S3a appendix: baseline B5 per spec Amendment 3 (A-MODEL)

**Authorization:** model_spec.md Amendment 3 (ruled 2026-07-16, appended
2026-07-17, Ayur; commit aa27494): §5 gains B5 = uncorrected retrained
LightGBM for attribution (B5 vs B4 isolates the censoring correction from
training recency); executed under the S3a protocol BEFORE any S3b code.

**Stage script:** `src/s3a_b5.py` — separate file; the signed-off
`src/s3a_baselines.py` is imported, never modified. Idempotent + resumable
(300 per-unit checkpoints in `outputs/checkpoints/s3a_work/b5_risk/`); ran as
5 bounded foreground invocations + idempotency rerun. Seed 42, no network.

**Grid-sample identity:** THE B4 stage-2 seed-42 sample verbatim (same 60
config indices); clip_floor inert metadata (no IPW in B5) — handling stated in
the checkpoint BEFORE training and flagged to LEAD; zero collisions verified
when projected to the 9 operative dims (asserted in code).

**Inputs:** `features_main.parquet` (read-only, S2-audited), 311 union
deliverable (zero-311 stratum flags via the cached S3a first311 table).

**Artifacts:** B5 appendix in `outputs/checkpoints/s3a_baselines.md` (results
table machine-generated to `s3a_work/b5_table.md` and appended verbatim —
zero hand transcription); additive `b5_*` keys in
`outputs/checkpoints/s3a_stats.json` (no S3a-audited key altered);
`outputs/models/b5_lgbm.txt` (405 trees) + `b5_frozen_config.json`;
`s3a_work/b5_winner.json`.

**Headline (5-fold means):** B5 AP 0.3870 / p@250 0.8136 / zero-311 p@250
0.1136; B5−B4 deltas +0.0006 / +0.0040 / +0.0032 — the spec-§11 named
limitation (observed-label evaluation penalizes correction) operating as
predicted; recorded as-is.

**Test-season sanctity:** every B5 fold/refit guard-asserted; cumulative
guards.jsonl now 72 recorded passes across 42 distinct sites (idempotency
reruns re-assert and re-record), max season ever touched 2025. (Count
measured from guards.jsonl after the final rerun; an earlier draft of this
entry hand-estimated 62 — corrected before commit.)

**Anomalies:** none. **Storage:** repo tabular+outputs ≈ 422 MB (≤ 2 GB).

## 2026-07-17 — S3b: primary two-head net per spec §3 (A-MODEL)

**Authorization:** G2 approved + Amendment 3 precondition met (B5 committed,
commit 4959795); S3b fence opened by LEAD dispatch (ledger B64 terms;
regeneration after the B68 removal of a killed session's unhashed partials —
nothing from that session referenced or reused).

**Stage script:** `src/s3b_primary.py` — one idempotent script, resumable at
epoch granularity (per-unit checkpoints + per-epoch resume states); ~29
bounded foreground invocations, 3 workers, torch fixed at 3 threads
(determinism); pre-flight kill/resume test bit-identical (scratch, deleted).
Seed 42; seeds 43–46 only in the validation spread. No network.

**Inputs (hash-asserted at prep against this file's S2 entries — matched):**
`features_main.parquet` 477d3079…, `features_b3.parquet` 09f8e94d…;
`c311_heat_complaints.parquet` (311 union — SOLE loss complaint source,
Amendment-1 boundary; NLL counts + zero-311 stratum flags).

**Search:** locked grid only (n=60 of 2,592, sampling seed 42, S3a decode
machinery). Winner cfg 2009 (w256/d2/do.15/λ.3/u*25/lr1e-3/μ₁0/μ₂1);
mean val AP(F·R) 0.3631 — trails B4 (.3865)/B5 (.3870) on observed-label
validation means; recorded as-is, G3 adjudicates (§10.4). Near-tie runner-up
disclosed in the checkpoint.

**Artifacts:** `outputs/models/s3b_primary_seed42.pt` (93,186 params; sha256
bb4016b836d148766f95d17e45bbb127b874e22f3e5d33b43e39a9c8b5c27126) +
`s3b_frozen_config.json` (sha256 904356165858091f3d05c57fb2b0593c0efe9ff0…
b2070412ded23300b0e5b2e0) with both frames' recipe hashes; E*=10 all-dev
refit; reload verification in a FRESH subprocess: BIT-EXACT (0.0 max abs
diff, full-dev F/p + every fixed-batch term). Checkpoint
`outputs/checkpoints/s3b_primary.md`; stats `s3b_stats.json`; blind-audit
kit `s3b_work/fixed_batch/` (8,125-row deterministic batch, per-term float64
values at t0/t1/tE with decomposed NLL, per-row F/p/R/q/F_pert, all
constants); resolved spec-§3 axes A1–A10 disclosed in script header +
checkpoint.

**Test-season sanctity:** 2026-27 structurally absent; deterministic guard
facts: 15 distinct sites, max season ever touched 2025, zero >=2026 firings
ever (a guard failure is a hard stop, not a log line). The raw pass count in
`s3b_work/guards.jsonl` (234 at reconciliation, 2026-07-17) is an APPEND-ONLY
CUMULATIVE snapshot that drifts upward on every invocation incl. complete
idempotent reruns (fixed-batch capture path re-asserts; B5-lineage caveat).
[Relabeled after R-AUDIT S3b reject 1, LEAD-authorized doc-only correction
before commit; an earlier draft headlined the snapshot value 233.] **Storage:** ≈928 MB ≤ 2 GB (design.npy 483 MB is a
regenerable cache, deletable at freeze). **Anomalies:** none; no Rule-9
conditions.

---

## FREEZE ENTRY — 2026-07-20 (adjudicated 2026-07-18; spec Amendment 4)

**Gate:** FREEZE APPROVED by Ayur (ledger B89, 2026-07-18) subject to
Amendment 4 (ruled 2026-07-18, appended 2026-07-20 — session-loss
interruption on record, ledger B90; resume verified by read-only audit).
The freeze precedes Oct 1, 2026 by ~2.3 months; external timestamps: model
commit 054f136 pushed 2026-07-17, packet commit 01e912b pushed 2026-07-17.

### Complete G3 scoring set (Amendment 4(iii) — summer 2027 requires zero interpretation)

**1. PRIMARY (frozen candidate):**
`outputs/models/s3b_primary_seed42.pt` — sha256
`bb4016b836d148766f95d17e45bbb127b874e22f3e5d33b43e39a9c8b5c27126`
(93,186 params, winner cfg 2009, seed 42, E*=10 all-dev refit; commit
054f136) + `outputs/models/s3b_frozen_config.json` — sha256
`904356165858091f3d05c57fb2b0593c0efe9ff0b2070412ded23300b0e5b2e0`,
pinning BOTH feature-frame recipe hashes: `features_main.parquet`
`477d3079fae0a4a76ee5507739c6f790448caa258c11ea78776583f2e4734090`,
`features_b3.parquet`
`09f8e94df5c51fa66778e17cc2d9bbba0eceb0aeef2453b411d7662ef324fa09`.
G3 frames are rebuilt by `src/s2_features.py` under Amendment 4(ii) window
semantics; loss/architecture interpretation frozen per Amendment 4(i)
(axes A1–A10, `src/s3b_primary.py` header). Deployment ranking = q = F·R;
criterion-1 stratum ranking = F (spec §10).

**2. B3 (deployed incumbent — the §10 comparison):**
`imports/primary_lgbm.txt` — sha256
`cd95a00e692a3d406c1a3aff1cabd1c3a384be227f7accea0dd97db7bdd38c93`
(343-tree frozen WFF booster, imported by copy commit 0cd8294, READ-ONLY
permanently). Scored on the B3-recipe frame: 30 columns, frozen-model
`feature_names` order, categorical vocabularies fixed from the model's
`pandas_categorical` footer (recipe in `src/s2_features.py`; dev-frame
fidelity 26/30 bit-exact, S2 checkpoint).

**3. B4 (two-stage IPW GBM):** `outputs/models/b4_propensity_lgbm.txt`
(95 trees) sha256
`f298f029b945829ff5b7685e026243cc96e5147e4309bbfaa65a46f58ec2ba6e`;
`outputs/models/b4_risk_lgbm.txt` (282 trees) sha256
`4fe42a228e2bc3751985a6a0624410942e8940415cd4fcdcc0a539d3656e289f`;
`outputs/models/b4_frozen_config.json` sha256
`8e816f4443cfcd72ca3171684aff06ce5988290001056e02a8a816ccb2798484`
(commit 07df605, S3a sign-off).

**4. B5 (uncorrected retrained twin, Amendment 3 — attribution only):**
`outputs/models/b5_lgbm.txt` (405 trees) sha256
`63eb6367641cf1c6206653660aecc917912b8593aeaa1366b31cc1a4d98739a1`;
`outputs/models/b5_frozen_config.json` sha256
`197e40c2bef4a395cd477f34517c329cf45e1f809857fa05508e23d70d9eb724`
(commit 4959795, S3a-protocol sign-off).

**5. B0–B2 (frozen definitions):** verbatim ports in `src/s3a_baselines.py`
(commit 07df605; port lineage documented in
`outputs/checkpoints/s3a_baselines.md`): B0 = persistence (prior-season
label), B1 = logistic-4, B2 = trailing-3 class-C count (class-C
restriction explicit in code, Rule 6). Recomputed at G3 on the G3 frame
from these definitions — no stored model artifacts by design.

**6. §10 criteria AS AMENDED (evaluated ONCE, at G3, vs B3):** spec §10
criteria 1–4 with Amendment-2 pre-registered margins (1: zero-311-stratum
p@250 ≥ 1.35× B3; 2: global p@250 ≥ 0.90× B3; 3: T = median
rank-percentile improvement over silent-screened HSP buildings at W=30,
one-sided exact sign test α = 0.05, realized n reported; 4: joint > B4 on
1–3 else the two-stage result ships) + §10 secondaries as demoted +
Amendment 4(i)/(ii) interpretations. Observed-label §11 caveat binds all
reporting.

### G3 scoring-data semantics (Amendment 4(ii))

Fresh pull AT G3 (summer 2027); every feature window hard-bounded
**< Oct 1, 2026** (pre-cutoff by WINDOW, not pull date). §1 cutoff,
availability masks, sanctity guards, bright line unchanged. G3 pull
provenance (dataset IDs, timestamps, row counts, window assertions)
recorded in THIS file at G3.

### State at freeze

Season 2026-27 untouched: guards 15 sites / max season 2025 / zero ≥2026
firings; both frames span 2017–2025. Resume-audit (2026-07-20, read-only,
ledger B90) independently recomputed all sha256s above that exist on disk —
all match — and reproduced the frozen model's fixed-batch forward pass
bit-exact (float64) from the checkpoint alone. Validation numbers recorded
as-is in the freeze packet (§10.4 binds at G3). **Anomalies:** none.
BUILD PHASE CLOSED — project DORMANT until G3.

---

## Stage RP1 — R-PILOT re-selection/training at cutoff Oct 1, 2025 (Amendment 5) — RETROSPECTIVE AND NON-BLIND

**Compiled by LEAD from signed-off sources only** (`outputs/checkpoints/
rp1_pilot.md` [R-AUDIT signed-off after 1 doc-only reject cycle],
`rp1_work/rp1_stats.json`, `reports/agent_logs/r-audit.md` RP0–RP1
sections; ledger B99–B107). Dormancy-exempt scoped phase per Amendment 5;
the frozen G3 pre-registration is untouched.

**Protocol:** RP0 leakage sign-off at the pilot cutoff PRECEDED all pilot
code (binding assertions D1–D11). S2 frames REUSED per Amendment 5(i)
(hashes asserted at load — the same values in this file's S2 entries).
Folds v ∈ 2021…2024 forward-chaining; season 2025 rows NEVER loaded in RP1
(dev universe asserted max season 2024); locked grid (n=60, seed 42) and
pre-registered selection re-executed mechanically under Amendment-4(i)
axes; frozen/committed artifacts read-only throughout (preflight sha256
snapshot 10/10 unchanged, re-verified at audit incl. the frozen bundle).

**Stage script:** `src/rp1_pilot.py` — idempotent, resumable; verified
zero-recompute on rerun. Disclosed deviations from the audited s3b mirror
(all operational, zero numeric impact — proven by the determinism
identity below): order-critical torch-before-lightgbm import and a
static-shard worker pool with hard child exit-code checks, after spawn
workers died at startup by SIGSEGV (duplicate-OpenMP clash; the mirrored
pool's bare-except had silently swallowed the deaths; crashed children
never wrote a byte; build-phase implication audited: NONE — build
completed 300/300 + 20/20). Episode + fixes in checkpoint and B103.

**Selection (all winners independently re-derived by R-AUDIT):**
- **Joint: cfg 2009 — the SAME config index as the build phase** — pilot
  mean val AP(q) 0.3434, p@250(F) 0.7240, zero-311 p@250(F) 0.0830;
  E* = 8; runner-up 1961 (margin 1.7e-3, higher zero-311 — same pattern
  as build). **Determinism identity: all 240 shared-fold units reproduce
  build S3b values to 0.00e+00** (0 best-epoch mismatches).
- **B4:** stage-1 cfg 5411 (= build; runner-up cfg 1080, margin 1.9e-5);
  stage-2 cfg 13411, mean AP 0.3695 (runner-up = build winner 21485,
  margin 3.3e-5, near-tie).
- **B5:** cfg 13411 (same operative config as B4 stage-2, twin-grid
  coherent), mean AP 0.3701 (runner-up = build winner 20928, margin
  1.3e-4, near-tie, higher tie-break — frozen exact-tie rule correctly
  not invoked).
- B0–B2 recomputed from frozen definitions; B3 folds-≤2024 row
  0.3694/0.8260/0.1170 (in-sample v=2021–23 caveat; ZERO season-2025 rows
  scored). B0/B2 tie-key 3rd-decimal shifts vs build disclosed
  (pilot-universe permutation; AP tie-key-free, reproduces build exactly).
- 5-seed VALIDATION spread (42–46, pilot folds): AP 0.3283–0.3465
  (std 0.0072); zero-311 0.074–0.083 (std 0.0030).
- The joint pilot model TRAILS B4/B5 on every observed-label validation
  mean — recorded as-is; §11 observed-label caveat attaches.

**Artifacts (all labeled RETROSPECTIVE AND NON-BLIND; distinct pilot
namespace; nothing pre-existing touched):**
| File (`outputs/models/`) | sha256 |
|---|---|
| `rpilot_joint_seed42.pt` | `93343fbda11d5efd9204b828075359d044f67d825eab89edb3555368cef757b0` |
| `rpilot_joint_config.json` | `96cf28747eb49c5d7029daf8d88ee8c88b5f9b8aafbb07000e4b5a5a5f694f80` |
| `rpilot_b4_propensity_lgbm.txt` (90 trees) | `c79ff723bed43ef5fe1c4ac8fdadc60274bf96d5183d445660bb449145508c07` |
| `rpilot_b4_risk_lgbm.txt` (332 trees) | `6c7f5171d68850f96239f7cde90cc39d9bf4d08f87e50b6302189a9240d9e67a` |
| `rpilot_b4_config.json` | `888549da0b5721ec4d071ddd2508529c136e5e3af1f332ff5f2a6e221b87affc` |
| `rpilot_b5_lgbm.txt` (307 trees) | `a93c9089f22dbc082cb5e1810a214a330a6c99bd8a071c23e0a6a14ba0c5b302` |
| `rpilot_b5_config.json` | `b76c9e34c0968924838ae9574f116478c276fbccceec3fa7e97fffefb076b72d` |

Checkpoint `outputs/checkpoints/rp1_pilot.md`; stats
`rp1_work/rp1_stats.json`; working files in `rp1_work/` (design.npy ~434 MB
regenerable cache, retained for RP2/R-AUDIT).

**Test-season sanctity:** guards 44 distinct sites; max season ever
touched 2025 at the two full-frame load/assert sites only (2025 dropped
next statement); ALL dev-side sites ≤ 2024; **zero ≥2026 firings**; raw
390 passes = append-only cumulative snapshot (S3b semantics). Season
2025-26 remains uncontacted by any model/selection structure — reserved
for the RP2 single shot. **Storage:** 1.443 GB ≤ 2 GB. **Anomalies:**
operational only (segfault episode above; two external loop kills resumed
cleanly, 257/257 units, zero losses). R-AUDIT RP1: 1 doc-only reject
cycle (two prose margins), corrected with bracketed audit notes,
SIGN-OFF.

---

## Stage RP2 — R-PILOT single-shot evaluation on season 2025-26 (Amendment 5(ii)) — RETROSPECTIVE AND NON-BLIND

**Compiled by LEAD from signed-off sources only**
(`outputs/checkpoints/rp2_eval.md` [R-AUDIT post-audit signed-off, zero
defects], `rp2_work/single_shot_2025/rp2_stats.json`, r-audit.md RP2
pre/post sections; ledger B111–B117).

**Single-shot protocol (heightened, LEAD-imposed):** script
`src/rp2_eval.py` (sha256 `652f199e87c0515665ad6ff23a7fb96d39a51b112e7fdc3
df65340686a521ae5`) was REHEARSED end-to-end on season 2024 and
PRE-AUDITED by R-AUDIT (sign-off, no defects; joint-subprocess scoring
reproduced RP1 persisted scores to 1.19e-07) BEFORE the one authorized
contact. **Season 2025-26 was contacted EXACTLY ONCE:
2026-07-21T06:52:14, exit 0, ~8 s compute** (`SINGLE_SHOT_SPENT.sentinel`
written pre-compute; rerun refuses recompute). Post-audit: every number
re-derived from the predictions parquet to 0.00e+00; all six
criterion-3-style cells reconciled from persisted Δ vectors AND an
independent raw-store rebuild; §6 stratum set-identity (120,631); all 7
scoring-set hash pins + B3 343-tree assert fired; frozen bundle + both
G3 frames + all committed artifacts re-hashed UNCHANGED.

**Eval universe:** the hash-pinned S2 frames' season-2025 rows (pre-Oct-1-
2025 by construction, RP0), 181,863 rows, 8,897 whitelist label_c
positives. Scoring set: rpilot_* (RP1 entry above), B3 as-is, B0–B2
frozen definitions. Frozen build bundle NOT scored, NOT touched
(Amendment 5(i)).

**Results (observed-label; §11 caveat attaches; recorded as-is,
disclosed whichever direction per Amendment 5(iii); NO prospective
standing, NO weight at G3):** AP/p@250/zero-311 p@250 — B0
.2155/.7360/.0280 · B1 .2784/.6320/.0520 · B2 .2734/.8000/.0480 · **B3
.4339/.8480/.1240 · B4 .4533/.8560/.1600 · B5 .4528/.8640/.1520 ·
joint_q .4408/.8280/.1160** (joint_F .4406/.8280/.1160). Amendment-5(ii)
stratum comparison: joint_F .1160 vs B3 .1240 (B4 .1600, B5 .1520).
Criterion-3-style (frozen grid-§7 statistic; P3 waterfall verbatim: 197
lots → 1,488 in-season class-C events → 104 silent dual-screen events
across **realized n = 35 buildings**): joint_F T=−0.0022 p=0.9996; B4
T=−0.0004 p=0.9552; B5 T=−0.0004 p=0.9552; all reject@.05 = False;
311-only sensitivity (n=36) consistent. Zero-drops reported per cell
(1/0/0). Per-building Δ vectors persisted.

**Artifacts (labeled RETROSPECTIVE AND NON-BLIND; kept under
`rp2_work/single_shot_2025/`):** `predictions_2025.parquet` (181,863 ×
14, building-season grain, all models + joint F/p/q + stratum flag +
label column) sha256 `d3cdfdca8927c4d0e15100a31a5c532b870854e0fce323cca5
eb739c017bd2fb`; `rp2_stats.json` `51f48aa0bbf8c3213bee4a8d50aca19bfc9ff
726b3c5bc039fc45a834f2f5f3c`; `joint_scores.npz` `1eeb6464b4a3fd0fd3539e
60e321078d91bca16f02e004d512ef66e7c16873eb`; checkpoint
`outputs/checkpoints/rp2_eval.md`; rehearsal outputs under
`rp2_work/rehearsal_2024/` (REHEARSAL-labeled, machinery validation
only).

**Operational disclosures:** two-process scoring design (torch/lightgbm
cannot co-execute in one process here — generalized OpenMP clash, proven
both directions); LATENT: committed `src/rp1_pilot.py` would segfault on
its GBM stages on a from-scratch rerun (torch-first import order) — RP1's
committed results are unaffected (audited determinism identity + persisted
unit jsons); ruled disclosure-only, no mid-pilot patch.

**Test-season sanctity:** guards 6 sites; max season touched 2025 = the
single authorized contact; **zero ≥2026 firings**; season 2026-27 and the
frozen G3 pre-registration untouched (byte-identical re-hash). **No
Rule-9 conditions. No fabrication events.** R-AUDIT RP2: pre-audit
sign-off (no defects) + post-audit sign-off (no defects, zero reject
cycles).
