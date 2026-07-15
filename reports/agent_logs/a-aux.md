# A-AUX agent log — silent-fail-forecast phase-0

## 2026-07-16 — Task 1: P3 (HSP cohorts + proactive-detectability heuristic)

**Dispatched by:** LEAD (plan.md §3 step 6), P3 ONLY — P4 not started, awaiting
separate dispatch after P3 audit.

### What I did (in order)

1. Read `.claude/agents/a-aux.md`, `CLAUDE.md`, `phase0_probe.md` in full
   (§4 + Amendments 1–3), `plan.md`, `data/PROVENANCE.md`, `data/p1_stats.json`,
   and `src/p1_pull.py` + `src/p2_gate.py` (to mirror the P1 pull pattern and
   P2's exact association-rule conventions) before acting.
2. **P3.1 — located all four cohort lists.** Web search found the nyc.gov PDFs
   for 2020/2022/2025 and the 2024 URL followed the same pattern (verified live,
   HTTP 200, valid PDF). Also found the official HPD open-data dataset
   `h4mf-f24e` (200 rows = 4 cohorts × 50, with bbl + program_start_date +
   current_status), verified live per Rule 5. All fetched programmatically —
   **no manual_downloads.md, no halted sub-branch, no guessed membership.**
   Note: nyc.gov serves 403 to non-browser user agents (WebFetch failed; curl
   with a browser UA succeeded — recorded, and encoded in `src/p3_hsp.py`).
3. **Cross-checked PDFs ↔ dataset**: 199/200 exact on normalized address keys;
   the 1 miss is a 2025-PDF spelling variant ("CLAREDON"/"CLARENDON" ROAD, same
   building). Membership is consistent across sources for all 200.
4. **Address → BBL via PLUTO (§4)**: the P1 PLUTO cache lacks addresses, so I
   made a small supplementary pull (`pluto_address.parquet`, bbl/address/borough,
   858,602 rows, logged in PROVENANCE). Independent exact-match resolution:
   171/200 (85.5%); where both the resolver and the dataset give a BBL they
   agree 171/171. Final BBLs = official dataset BBLs (200/200 present, 200/200
   found in the P1 PLUTO lot universe; address fallback needed 0 times).
5. **HPD-complaints dataset verification BEFORE choosing the heuristic version
   (§4 P3.2 + my definition):** `uwyv-629c` and `a2nx-4u46` are login-walled
   (retired from public API); `ygpa-z7cr` (merged Complaints and Problems) is
   live but is the exact dataset probe doc **Amendment 1 item 2** excludes from
   phase-0. Logged either way, as required → **311-only version runs, labeled.**
6. **P3.2 heuristic** (`src/p3_hsp.py`, `.venv/bin/python`, seed 42, idempotent
   — rerun twice, byte-identical stats): association rule identical to P2
   (W=30 per §4, inclusive bounds, calendar-date truncation, int64 bbl,
   explicit class-C); Amendment 3 window-coverage eligibility (0 exclusions);
   program seasons = heat seasons (Oct–May) from each lot's earliest
   program_start_date (all 200 rows "Active", no discharges); every exclusion
   counted in a waterfall.
7. Wrote `outputs/checkpoints/phase0_p3_hsp.md`, `data/p3_stats.json`, appended
   the P3 section to `data/PROVENANCE.md`. Did not commit (workers never commit).

### Results

| Quantity | Value |
|---|---|
| Cohorts located | 4/4 (2020, 2022, 2024, 2025; 50 each) |
| PDF ↔ dataset membership agreement | 199/200 exact, 200/200 after the spelling variant |
| Address→BBL resolution (independent, via PLUTO) | 171/200 (85.5%), 0 disagreements with dataset BBLs |
| Final BBL coverage | 200/200 in PLUTO lot universe; 197 distinct lots |
| Eligible in-program heat-season class-C violation events | 3,633 |
| **Zero-311-complaint events @ W=30 (311-only version)** | **377** (10.38%; 95 distinct lots) |
| §4 floor | 30 → **PASS** (stated, not argued) |

Robustness (facts): Oct–Jan cadence subset = 223 ≥ 30; (bbl, inspectiondate)-
deduped = 244 ≥ 30 — the floor side does not depend on those interpretive
choices. 311-only caveat stated in the checkpoint: without an HPD-complaints
screen the count is an upper bound on complaint-independent events.

### Decisions / deviations (all disclosed in checkpoint + PROVENANCE)

1. Official dataset `h4mf-f24e` used as membership/BBL authority (§4 anticipated
   PDFs only); PDFs parsed and cross-checked as the §4-named source.
2. Supplementary PLUTO address pull (bbl,address,borough) to perform §4's
   address→BBL resolution — P1's PLUTO cache carries only bbl+unitstotal.
3. "Program seasons" read as NYC heat seasons (Oct 1–May 31, P2's definition)
   from program_start_date onward; Oct–Jan cadence subset reported alongside.
4. Analysis grain = tax lot (violations/311 are bbl-keyed): 200 selections →
   197 distinct bbls; 3 shared-lot groups reported verbatim.

### Anomalies (all benign, none met Rule 9)

- 2025 PDF street-name typo (CLAREDON→CLARENDON).
- Shared tax lots: 2031240001 (two distinct BINs, cohorts 2020/2022),
  4067020001 (two Queens BINs, both cohort 2025), 2031250006 = true repeat
  selection (2112 Honeywell Ave, 2020 + 2024).
- nyc.gov 403s non-browser UAs (harness/etiquette note, not a data problem).
- Harness mechanics: two sandbox network interferences (pip index unreachable;
  Socrata paged responses truncated at ~3.8 MB) — retried per harness guidance
  outside sandbox, per LEAD's dispatch note. Not Rule 9 conditions.

**Not done (out of current dispatch):** P4 — awaiting LEAD dispatch after the
R-AUDIT P3 pass. No commits, no spawns, no messages to other workers.

---

## 2026-07-16 — Task 2: P4 (zero-mass descriptives)

**Dispatched by:** LEAD after P3 sign-off (commit eb48b48; plan.md §3 step 7).

### What I did (in order)

1. Read probe doc §5 + my definition's P4 paragraph; read WFF
   `src/s3d_income_equity.py` (READ-ONLY — repo untouched) to port the
   CD-income machinery and Census plumbing.
2. **Verified prerequisites:** ACS 2024 acs5 endpoint live (Rule 5) with all
   seven P4 variables; keyless requests rejected with an HTML "Missing Key"
   page (Census requires a key for all queries — matches WFF's 2026-05-12
   note). `CENSUS_API_KEY` present in `.env` (boolean check only, value never
   printed). NOTE: the sandbox denies `.env` reads, so a sandboxed check
   falsely reports the key missing — verified unsandboxed; recorded as a
   harness mechanic, not a Rule 9 credential failure.
3. **Pulls** (`src/p4_zeromass.py`, idempotent, seed 42, storage-guarded):
   `pluto_geo.parquet` (bbl, cd, bct2020; 858,602 rows) and
   `acs_tract_2024.parquet` (2,327 tracts; B19013 income, B11001 households,
   C16002 LEP; sentinels → null, logged).
4. **Analysis:** universe = 181,863 distinct spine bbls (frozen R4 import);
   zero mass = 0 whitelisted 311 complaints over 2019-06-01…2026-07-13 →
   114,890 (63.2%; WFF's ~70% was its own window — reported, not reconciled).
   Covariates: unitstotal (P1 cache, P2 hygiene), borough (bbl digit), CD
   income tercile (s3d method verbatim in semantics), tract LEP share
   (C16002 limited-English-speaking-household share, definition documented).
   Support-overlap described over unit-class × borough × income-tercile ×
   LEP-tercile cells. Figure = SVG (vector; no raster on disk).
5. Wrote `outputs/checkpoints/phase0_p4_zeromass.md`, `data/p4_stats.json`,
   `outputs/figures/phase0_p4_zeromass.svg`; appended PROVENANCE P4 section.
   Reran twice — byte-identical stats. No commits.

### Results (description, not conclusion — P4 gates nothing)

| Quantity | Value |
|---|---|
| Universe / zero mass | 181,863 / 114,890 (63.2%) |
| Occupied covariate cells shared by both masses | 146/148 |
| Zero-mass buildings in cells with ≥1 positive | 106,231/106,232 (100.0%; ≥10: 99.9%) |
| Positive-mass buildings in cells with ≥1 zero | 65,508/65,513 (100.0%; ≥10: 99.3%) |
| Median unitstotal zero vs positive | 3 vs 8 |
| Zero-311 share by unit class | 2–5: 78.4% → 50+: 16.8% |
| Median CD income zero vs positive | $85,263 vs $79,943 |
| Median tract LEP share zero vs positive | 0.101 vs 0.105 |

### Exclusions (logged, never imputed)

Spine bbls without PLUTO geo 1,209; undefined tract LEP 14; unit-join
unmatched 1,043; conflicting-units bbls 0; ACS income-null tracts 128 of
2,327; zero-household (LEP-undefined) tracts 96.

### Anomalies

None beyond recorded harness mechanics (sandbox `.env` read-deny; api.census.gov
and pip requiring unsandboxed runs). No Rule 9 conditions. Storage 96.2 MB.
