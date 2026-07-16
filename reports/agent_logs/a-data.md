# A-DATA agent log — silent-fail-forecast BUILD phase

## 2026-07-16 — S1: all pulls, 311 union refresh, spine verification

**Dispatched by:** LEAD (plan.md §3 step 2). Initial dispatch carried **R-A
RELAY: UNRULED** (no ygpa-z7cr contact); LEAD later relayed **R-A = ADMIT**
(model_spec.md Amendment 1, 2026-07-16, read in full) mid-stage — the ygpa-z7cr
branch was folded into this same stage per the relay.

### Documents read in full before acting (order per dispatch)
1. `.claude/agents/a-data.md` (binding scope)
2. `CLAUDE.md` (Rules 1–10, scope fence, test-season sanctity)
3. `model_spec.md` §2 (+ full spec; + Amendment 1 after the R-A relay)
4. `plan.md` §3 step 2
5. Phase-0 context: `data/PROVENANCE.md`, `phase0_probe.md` (incl. Amendments
   1–3), `src/p1_pull.py`, `data/p1_stats.json`
6. Read-only WFF recipe (never edited): `nyc-heat/src/s1_data_pull.py`,
   `s1c_pull_violation_context.py`, `s2_features.py`, `s1b_freeze_labels.py`,
   `outputs/checkpoints/data_coverage_report.md`, `_s1b_frozen_labels.json`

### Rule-5 live ID verification (2026-07-16, data.cityofnewyork.us metadata API)

| ID | Live name | rows updated | Status |
|---|---|---|---|
| `erm2-nwe9` | 311 Service Requests from 2020 to Present | 2026-07-15 | OK — union current side |
| `76ig-c548` | 311 Service Requests from 2010 to 2019 | 2025-12-24 | OK — archive side (closed dataset; staleness expected) |
| `wvxf-dwi5` | Housing Maintenance Code Violations | 2026-07-15 | OK — WFF-recipe violations + family-2 aggregate |
| `tesw-yqqr` | Multiple Dwelling Registrations | 2026-06-01 | OK — family 5 / universe |
| `feu5-w2e2` | Registration Contacts | 2026-06-01 | OK — family 5 |
| `64uk-42ks` | Primary Land Use Tax Lot Output (PLUTO) | 2026-05-28 | OK — family 4 full attributes |
| `ygpa-z7cr` | Housing Maintenance Code Complaints and Problems | 2026-07-15 | OK — verified ONLY after LEAD relayed R-A = ADMIT |

ygpa-z7cr pre-pull server-side probe (post-relay): single heat major
`'HEAT/HOT WATER'` = 1,754,951 problem rows for `received_date >= 2019-06-01`
(range 2019-06-01 … 2026-07-15); minor split ENTIRE BUILDING 1,148,242 /
APARTMENT ONLY 606,709; schema carries `bbl`, `apartment`, `unit_type`,
`space_type`, `problem_duplicate_flag`, `received_date`, `problem_status_date`
— everything family 7 and the criterion-3 screen need.

### Stage script
`src/s1_pull.py` — one idempotent script for the stage (paged, server-side
filtered, parquet-cached, storage-guarded vs the ≤2 GB repo tabular total
including imports/, seed 42 (no sampling in S1), token via python-dotenv never
printed). Hard stops coded per Rule 9: empty pull, schema surprise (column-set
check per page), ID name mismatch, spine mismatch vs the WFF committed report,
storage breach, >1% row disappearance at the 311 refresh edge.

### Key decisions (all disclosed, none silent)
1. **Phase-0 raw caches preserved untouched.** The 311 refresh pulls the
   current side to a NEW cache (`c311_current_refresh.parquet`); the phase-0
   `c311_heat_complaints_full.parquet` (max created 2026-07-13) is retained as
   the comparison side of the refresh-edge seam diagnostic. The union
   deliverable `c311_heat_complaints.parquet` is regenerated deterministically
   from the two caches — its standing semantics since Amendment 3.
2. **Archive side reused from cache, not re-pulled.** `76ig-c548` is a closed
   2010–2019 dataset (live metadata: rows last updated 2025-12-24); the
   phase-0 cache (93,022 rows, matched the server-side count at pull time) is
   byte-identical input to the union. ID re-verified live regardless.
3. **DISCLOSED ADDITION — WFF-recipe violations pull** (`hpd_violations_wff`,
   floor `inspectiondate >= 2017-10-01`, WFF's 13-column select, frozen
   whitelist VERBATIM, B+C superset with `class` retained). Not in my
   enumerated pull list, but WFF family 1 (`s2_features.py` source B) consumes
   whitelisted violation ROWS from 2017-10-01, and the phase-0 cache (floor
   2019-06-01, narrower columns) cannot feed the WFF-recipe frame A-FEAT must
   re-implement. Acquisition-only judgment call under "A-DATA: all pulls"
   (plan.md roster); flagged here for R-AUDIT.
4. **Family-2 context aggregate mirrored verbatim from WFF `s1c`** —
   server-side `(bbl, class, year)` counts, floor 2014-06-01, `yr`/`n` coerced
   to Int64 to match the WFF cache contract (raw rows would be ~8.5M and
   pointless; the aggregate is the recipe).
5. **ygpa-z7cr whitelist** = `upper(major_category) = 'HEAT/HOT WATER'` +
   `received_date >= '2019-06-01'` (floor aligned with the §2 union floor;
   both admitted capacities are 2019-20+ so earlier rows serve nothing).
   21-column select: identifiers (problem/complaint/unique keys), building
   keys (bbl, building_id, borough/block/lot), apartment identifiers
   (apartment, unit_type, space_type, type), categories, statuses, timestamps,
   duplicate/anonymous flags. No null-bbl filter at pull (counted and logged,
   §2 pattern). Amendment-1 boundary noted in the script docstring: this cache
   feeds family 7 + the criterion-3 screen ONLY, never the reporting-head
   likelihood.
6. **Spine verification target** = WFF's committed
   `outputs/checkpoints/_s1b_frozen_labels.json` (grid 1,624,255 rows;
   181,863-BBL universe; per-season denom/pos transcribed into the script).
   Also re-checks the import's sha256 against PROVENANCE before reading.
7. **Season 2026-27 untouched** (Rule 3): every pull ends at pull time
   (2026-07-16, pre-season); no 2026-27 window exists anywhere in the script.

### Harness mechanics recorded (not Rule-9 conditions)
- Sandbox denies reads of `./.env` (recorded precedent: phase-0 P4 entry), so
  the stage script runs unsandboxed to load `SOCRATA_APP_TOKEN`; the token is
  never printed. Sandboxed `pgrep`/process-listing is also unavailable
  (`sysmond service not found`) — a process-watch false alarm during the run,
  no effect on data.
- One transient `IncompleteRead` on the first ygpa-z7cr metadata fetch;
  resolved on retry (retries are built into the pull loop).

### Disclosed anomaly — external kill of run 2 (harness-side, not data-side)
Run 2 (ygpa-z7cr pull + idempotency rerun) was killed EXTERNALLY at ~700k of
1,754,951 ygpa rows; an unrelated trivial progress-check background task was
killed at the same instant → session-level background-task stop, not a script
or data failure. State verified clean before restart: no partial parquet (pulls
write only on completion; no `hpd_complaints_heat.parquet` existed), all seven
run-1 caches intact and cache-hit by run 2 before the kill (idempotency
confirmed), union deliverable regenerated identically. Reported to LEAD BEFORE
restarting (no silent restart); LEAD approved (ledger B15) with the standing
rule: a second kill of the same shape = stop and escalate, no third attempt.
Run 3 = same idempotent script, cache-hits everything, re-pulls only ygpa.

**Second kill (same shape) → Rule-9 STOP, branch HELD.** Run 3 was killed
externally at ~900k of 1,754,951 ygpa rows, again simultaneously with its
companion progress-check background task — identical pattern to the run-2
kill. No data-layer failure of any kind (no HTTP error, schema surprise, or
storage breach); disk verified clean again (no partial parquet, all 15 raw
caches intact, run-1 idempotency re-confirmed at the start of both killed
runs). Per LEAD's standing B15 rule, NO third attempt: exact state escalated
to LEAD with options (single foreground call ~8–9 min; two resumable
foreground halves via a created-date split — recommended; or investigate
first). LEAD acknowledged (B16), escalated to Ayur (B17); ygpa-z7cr branch
HELD pending relay. S1 is otherwise COMPLETE and verified (all run-1 results
final, in PROVENANCE).

### Run log
- Run 1 (pre-relay scope) launched in background; all six original IDs
  verified in-run; 311 refresh + downstream pulls executing.
- R-A = ADMIT relayed mid-run; ygpa-z7cr branch added to the stage script
  (safe: the running interpreter had already loaded its code). Run 2 executes
  the ygpa pull and doubles as the idempotency rerun (cache-hits expected on
  every run-1 pull).
- Ruling (b) executed with one DISCLOSED adjustment (messaged to LEAD before
  starting): 7 bounded date-split parts instead of 2 halves — measured
  throughput ~66k rows/min makes a ~875k-row half ≈ 13 min > the 600 s
  foreground ceiling; a "half" would have been killed at timeout. Parts are
  half-open received_date intervals, disjoint and jointly exhaustive.

### Final results (all verified, all in PROVENANCE)

**311 union refresh (Amendment-3 semantics):** archive 93,022 + current
1,645,614 = 1,738,636; dedupes on unique_key **0**; null-bbl 7,123 (0.410%)
excluded with logging; deliverable regenerated **1,731,513 rows**
(2019-06-01 … 2026-07-13). Seam A (archive boundary) identical to phase-0:
664, 678, 457, 437, 515, 850, 608 | 692, 673, 533, 554, 746, 804, 831. Seam B
(refresh edge vs untouched phase-0 pull, daily 2026-06-30..07-13): identical
on every day; late arrivals 0; disappeared 0 — erm2's 07-15 update added no
heat rows after 07-13 (July off-season); reported as-is.

**Pulls:** hpd_violations_wff 149,585 (B=2/C=149,583, floor 2017-10-01,
inspections through 2026-07-14; WFF's own 07-14 pull was 149,511 with B=2 —
+74 rows two-day accrual; phase-0 2019-06-01-floor cache holds 128,121 rows
for comparison) · hpd_viol_context_by_year 2,012,740 groups (classes A/B/C/I,
years 2014–2026) · hpd_registrations 203,236 rows / **181,863 distinct BBLs =
the frozen spine universe exactly** · hpd_registration_contacts 782,024 ·
pluto_full 858,602 (nulls: yearbuilt 358, numfloors 42,264, unitstotal 429,
bldgclass 355, borough 0).

**ygpa-z7cr (post-ruling):** 7 parts 261,053 / 200,169 / 270,629 / 230,610 /
267,542 / 318,652 / 206,296 — every part exactly matches the server-side year
probe; sum **1,754,951** = the probed total (zero drift); cross-part duplicate
problem_id **0**; deliverable `hpd_complaints_heat.parquet` assembled
deterministically (range 2019-06-01 … 2026-07-15). Accounting: null-bbl 6,792
(0.387%), null apartment 3, `problem_duplicate_flag` **Y = 761,130 (43.4%)** —
HPD's own dedup marking is large (OSC 2019-N-3 context); flagged for
A-FEAT/R-AUDIT, handling is an S2 decision.

**Spine verification:** import sha256 matches PROVENANCE; schema exact; grid
1,624,255 rows / 181,863 BBLs; per-season rows and positives match WFF's
committed `_s1b_frozen_labels.json` EXACTLY, 9/9 seasons (2017-18 … 2025-26).

**Idempotency:** all 15 raw caches hit on rerun; both regenerated deliverables
byte-identical across rebuilds (sha256); s1_stats.json byte-identical (one
394-byte tabular_bytes artifact on the first rerun = the storage guard
counting the stats file itself after the hpdc keys grew it — proven benign by
the byte-identical third run).

**Storage:** data/ + imports/ = **341.6 MB** (≤ 2 GB). **Season 2026-27:**
untouched throughout (natural data max 2026-07-15, pre-season).

**Not done (out of scope):** no analysis, no features, no commits (LEAD
commits after R-AUDIT), no contact with anything beyond LEAD.
