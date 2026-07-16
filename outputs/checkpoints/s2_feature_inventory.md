# S2 feature-inventory checkpoint (A-FEAT) — silent-fail-forecast

**Stage:** S2 features (A-FEAT). **Date:** 2026-07-16. **Spec refs:** §1, §2, §3, §7,
Amendment 1 (family 7), Amendment 2 (leakage sign-off binding on this stage).
**Reproduce:** `.venv/bin/python src/s2_features.py` — idempotent, no network, seed 42;
reran to **byte-identical** output (sha256 equal across runs, both frames + stats).
**Outputs (one row per spine row of the frozen R4 label grid, 1,624,255 rows each):**

| Frame | Path | Features | Size | sha256 |
|---|---|---|---|---|
| (a) B3-scoring | `data/processed/features_b3.parquet` | 30 (WFF recipe, exact order of the frozen model's `feature_names`) | 27.5 MB | `09f8e94df5c51fa66778e17cc2d9bbba0eceb0aeef2453b411d7662ef324fa09` |
| (b) main | `data/processed/features_main.parquet` | 49 = families 1–5 (30) + family 6 (11) + family 7 (8) | 35.4 MB | `477d3079fae0a4a76ee5507739c6f790448caa258c11ea78776583f2e4734090` |

Keys `bbl_n, season`; labels `label_c` (both frames) + `label_bc` (main frame) joined
verbatim from `imports/building_season_labels.parquet` (read-only; never read by any
feature computation for its own season). Stats: `outputs/checkpoints/s2_stats.json`.

**Handoff:** → R-AUDIT S2 temporal-leakage protocol (BINDING per Amendment 2).

---

## The leakage rule as implemented (for R-AUDIT)

Target season start year `sy` (Oct 1 `sy` – May 31 `sy+1`). Cutoff = Oct 1 `sy` 00:00.

- **Season-indexed sources** (families 1, 5): only seasons `s' < sy` are read; season
  `s'` ends May 31 `s'+1` ≤ May 31 `sy` < cutoff. `season_of()` copied verbatim from
  WFF `src/s2_features.py` L46–57 (same assignment as the label build). Family-1/5
  rolling state updates only AFTER season `sy`'s features are emitted.
- **Calendar-year-indexed sources** (families 2, 3): only `yr ≤ sy−1`; the wide year
  matrices carry columns capped at **2024**, so a `yr == sy` read for season 2025 is
  structurally impossible, not merely avoided.
- **Timestamp-windowed sources** (families 6, 7): every slice goes through `win()`
  (`src/s2_features.py`), which **hard-asserts window_hi ≤ cutoff** before returning
  rows. Windows are half-open `[lo, hi)`. There is no other timestamp access path.
- **Availability masks** (spec §2): a family-6/7 window is available only if its LEFT
  edge ≥ the 2019-06-01 complaint floor; unavailable → NULL, **never zero-filled**.
  Family 3 keeps WFF's coarser year-grain mask verbatim (floor year 2020) for B3
  fidelity — see D2.
- **Season 2026-27:** the spine ends at season 2025 (asserted at load); both frames
  assert `max(season) == 2025` before writing. No filter, window, or artifact touches
  2026-27.

## Frame (a): B3 fidelity statement

Re-implemented from read-only WFF `src/s2_features.py` with line ranges: family 1
L84–94 + L189–203; family 2 L96–106 + L205–218; family 3 L108–115 + L220–231
(aggregate recipe from WFF `src/s1d_pull_311_by_building.py` L47–51); family 4
L117–130 + L233–239; family 5 L132–172 + L241–249; assembly/state-roll L174–261.
Input-cache mapping (S1-audited, same column contracts): `hpd_violations.parquet` →
`hpd_violations_wff.parquet`; `c311_heat_by_building_year.parquet` → in-memory
aggregate of the union deliverable (D2); `pluto.parquet` → `pluto_full.parquet`.

**Verification against WFF's own frozen frame** (`<WFF>/data/processed/features.parquet`,
read-only): after key alignment (all 1,624,255 × keys identical, `label_c` identical),
**26/30 feature columns are exactly equal on every row**. The only differences:
`ctx_c_prior1` (1 row), `ctx_c_cum` (4 rows), and the two `ctx_total_*` columns that
contain them — all on **one building** (BBL 1012410023), whose class-C context count
for calendar 2021 is 1 higher in our 2026-07-16 pull than in WFF's 2026-07-14 pull.
Late HPD data entry into a historical year bucket (source accrual), disclosed — not
patched (fidelity over improvement; the recipe itself reproduces WFF exactly).

**Categorical alignment:** `bldgclass_1` / `borough` written as pandas Categorical
with vocabularies fixed VERBATIM from the frozen model's `pandas_categorical` footer
(24 letters; BK/BX/MN/QN/SI). Novel values observed: **0 / 0** (asserted at build).

## Feature inventory

### Families 1–5 (identical in both frames; WFF semantics)

| Column | Family | Source | Exact leakage window |
|---|---|---|---|
| `viol_lag1/2/3` | 1 | frozen spine `label_c` | label at seasons `sy−1/−2/−3` (< sy); pre-panel (<2017) → 0, flagged by `hist_horizon` |
| `hist_horizon` | 1 | derived | `sy − 2017`; no event data |
| `viol_recency` | 1 | frozen spine `label_c` | `sy −` (latest season < sy with `label_c=1`); NULL if none |
| `viol_chronicity` | 1 | frozen spine `label_c` | (# positive seasons < sy) / (# panel seasons < sy); NULL if denom 0 |
| `viol_cnt_prior1/_cum` | 1 | `hpd_violations_wff.parquet` (whitelisted, **class C only**, floor 2017-10-01) | row count in season `sy−1` / seasons 2017…`sy−1`; NULL for sy=2017 (pre-pull, unobservable ≠ 0) |
| `ctx_{a,b,c,i}_prior1/_cum`, `ctx_total_*` | 2 | `hpd_viol_context_by_year.parquet` | calendar year `yr == sy−1` / `2014 ≤ yr ≤ sy−1`; matrix columns capped 2024 |
| `c311_available` | 3 | derived | 1 iff `sy−1 ≥ 2020` (WFF mask verbatim; D2) |
| `c311_prior1/_cum` | 3 | union deliverable, aggregated by (bbl, calendar yr) | `yr == sy−1` / `2020 ≤ yr ≤ sy−1`; NULL when masked, never 0-filled |
| `building_age` | 4 | `pluto_full.parquet` | `sy − yearbuilt`; NULL if missing/0 |
| `prewar` | 4 | same | 1 iff 0 < yearbuilt < 1940, else 0 (missing → 0; `building_age` NULL carries missingness) |
| `unitsres`, `unitstotal`, `numfloors` | 4 | same | static; missing → NULL, no imputation |
| `bldgclass_1`, `borough` | 4 | same | static categoricals, frozen-B3 vocabularies |
| `portfolio_size` | 5 | registrations + contacts | # distinct panel buildings sharing owner key (current snapshot; C2); NULL if no key |
| `portfolio_loo_rate` | 5 | + frozen spine `label_c` | exact leave-one-out: Σ label over owner's OTHER buildings' panel seasons < sy ÷ that count; NULL if denom 0 |

### Family 6 — complaint-granularity (main frame only; source: union deliverable `c311_heat_complaints.parquet`, complaint level, floor 2019-06-01)

Windows: **ps** = prior season `[Oct 1 sy−1, Jun 1 sy)`; **t365/t730** = `[cutoff−365d/730d, cutoff)`.
Availability: window left edge ≥ 2019-06-01 → `ps`,`t365` from season 2020; `t730` from
season 2021. Unavailable → NULL. Within available windows, counts are true 0 for
complaint-free buildings; ratio/gap features NULL where undefined (their definedness
conditions are in the null audit).

| Column | Definition | Leakage window |
|---|---|---|
| `c6_available_ps/_t365/_t730` | availability masks (features themselves, WFF §3 pattern) | derived from calendar only |
| `c6_evt_ps` | complaint events in prior season | `[Oct 1 sy−1, Jun 1 sy)` |
| `c6_days_ps` | distinct complaint DAYS in prior season | same |
| `c6_dup_intensity_ps` | `c6_evt_ps / c6_days_ps` — same-day repeat intensity; NULL if 0 days | same |
| `c6_evt_t365`, `c6_evt_t730` | trailing event counts | `[cutoff−365d/730d, cutoff)` |
| `c6_gap_median_t730`, `c6_gap_min_t730` | median/min inter-complaint gap (days) between consecutive events; NULL if < 2 events | `[cutoff−730d, cutoff)` |
| `c6_days_since_last_t730` | days from latest event in window to cutoff; NULL if none (bounded lookback keeps the mask exact) | same |

### Family 7 — distinct-apartments (main frame only; source: `hpd_complaints_heat.parquet`, ygpa-z7cr per Amendment 1 — FEATURES ONLY, never the loss)

Apartment-complaining row := `unit_type == 'APARTMENT'` AND normalized apartment
∉ {'', 'BLDG'} (normalization: UPPER/strip/collapse-space). Apartment key = the
normalized string. Same window/mask calendar as family 6 (same 2019-06-01 floor).

| Column | Definition | Leakage window |
|---|---|---|
| `c7_available_ps/_t730` | availability masks | calendar only |
| `c7_apts_ps`, `c7_apts_t730` | distinct apartment keys complaining | `[Oct 1 sy−1, Jun 1 sy)` / `[cutoff−730d, cutoff)` |
| `c7_apt_share_ps` | `c7_apts_ps / unitstotal` (PLUTO); NULL if units missing/0; uncapped (messy apt strings can exceed 1 — left visible, D4) | prior season |
| `c7_evt_all_ps` | ALL ygpa problem rows in prior season | prior season |
| `c7_evt_dedupN_ps` | rows with `problem_duplicate_flag == 'N'` only | prior season |
| `c7_dupflag_share_ps` | share of prior-season rows HPD flags 'Y'; NULL if 0 rows | prior season |

**Duplicate-flag decision (standing flag B21, ruled here, both-ways per dispatch):**
HPD's own dedup marking (Y = 761,130 rows, 43.4%; OSC 2019-N-3 context) is treated as
**data, not truth**: (i) distinct-apartment counts use ALL rows — distinctness is
set-valued and invariant to duplicate rows within an apartment, so the flag's
reliability is immaterial there; (ii) event-count features are carried BOTH ways
(`c7_evt_all_ps` vs `c7_evt_dedupN_ps`) so no irreversible dedup choice is baked in;
(iii) the flag itself is surfaced as a feature (`c7_dupflag_share_ps`) — under-
reporting-relevant signal per spec §3 motivation. Downstream may use either count;
nothing is dropped. Both-ways magnitudes: over covered prior-season windows,
Σ all-rows = 1,254,133 vs Σ flag-N = 699,747; mean per-building Y-share where
defined = 0.157.

## Mask coverage (families 3, 6, 7)

| Season | rows | `c311_available` (fam 3) | `*_available_ps`/`_t365` (fams 6–7) | `*_available_t730` |
|---|---|---|---|---|
| 2017-18 | 178,503 | 0 | 0 | 0 |
| 2018-19 | 179,143 | 0 | 0 | 0 |
| 2019-20 | 179,767 | 0 | 0 | 0 |
| 2020-21 | 180,157 | 0 | **1** | 0 |
| 2021-22 | 180,547 | 1 | 1 | 1 |
| 2022-23 … 2025-26 | 181,087 … 181,863 | 1 | 1 | 1 |

Family 6/7 prior-season features unlock one season EARLIER than family 3 (2020-21 vs
2021-22): the complaint floor 2019-06-01 fully covers prior-season window Oct 2019–May
2020, while WFF's year-grain mask needs full calendar 2019 and stays 0. Masked rows:
fam-3 717,570 (44.2%); fam-6/7 ps/t365 537,413 (33.1%); t730 717,570 (44.2%).

## NULL audit headline (full table in `s2_stats.json`)

- **B3 frame: every family-1–5 NULL count matches WFF's committed S2 report EXACTLY**
  (`viol_recency` 1,504,470 = 92.62%; `viol_chronicity` 181,863; `viol_cnt_*` 178,503;
  `c311_*` 717,570; `portfolio_loo_rate` 1,026,714 = 63.21%; `portfolio_size` 103,964;
  PLUTO fields 0.57–1.24%; ctx 0).
- Family 6: counts NULL only where masked (537,413 / 717,570 per window);
  `c6_dup_intensity_ps` 90.6% NULL (defined only when ≥1 complaint day);
  `c6_gap_*_t730` 92.1% NULL (≥2 events required); `c6_days_since_last_t730` 88.6%
  NULL (≥1 event required) — structural definedness, expected under the ~63% zero-311
  mass (P4), not missingness.
- Family 7: `c7_apts_*`/`c7_evt_*` NULL only where masked; `c7_apt_share_ps` +10,311
  extra NULLs (unitstotal missing/0); `c7_dupflag_share_ps` 90.5% NULL (≥1 row required).
- No imputation anywhere; all numeric features float64 (NaN = NULL); masks int64.

## Deviations & caveats (disclosed, none silently patched)

- **D1 (source accrual, 5 feature cells).** The single-building ctx_c difference vs
  WFF's frozen frame documented above (BBL 1012410023, +1 class-C context row in
  calendar-2021 bucket, entered between the two pull dates).
- **D2 (family-3 aggregation site).** WFF consumed a SERVER-side (bbl, year) aggregate
  (s1d L47–51); we reproduce the identical aggregate LOCALLY from the S1-audited union
  deliverable. The P311 matrix columns are 2020–2024, so the union's 2019 archive rows
  are structurally excluded and the WFF mask semantics (floor year 2020) are preserved
  verbatim. Verified: family-3 columns match WFF's frame exactly on all rows.
- **D3 (cache-contract note).** `hpd_viol_context_by_year.parquet` stores `yr`/`n` as
  strings on disk (PROVENANCE says Int64); coerced with zero parse loss (asserted).
  Flagged for the record; values identical.
- **D4 (apartment-string noise).** ygpa apartment identifiers are free-text; distinct
  counts inherit HPD's entry noise ('2H' vs '2-H' would double-count). Normalization
  is UPPER/strip/collapse-space only — no fuzzy merging (would be invented structure).
- **C1/C2 (PLUTO + registration vintage).** Carried over from WFF verbatim: both are
  current-vintage snapshots of slowly-varying attributes projected across seasons;
  flagged for R-AUDIT's ruling, same as WFF's R-LEAK accepted.
- **Amendment-1 boundary restated:** ygpa-z7cr appears ONLY in `c7_*` feature columns.
  It contributes no count, exposure, mask, or weight to any loss input; the union
  deliverable is the sole complaint source for families 3 and 6.

**No fabrication events; no empty inputs; no join failures; storage after S2:
data/ + imports/ ≈ 405 MB ≤ 2 GB.**
