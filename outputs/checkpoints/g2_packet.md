# G2 gate packet — silent-fail-forecast build phase

Compiled by LEAD 2026-07-16 from signed-off artifacts only. States what the
pre-committed criteria say; recommends nothing. Adjudication is Ayur's.

## What Amendment 2 says G2 requires
"G2 = S2 leakage sign-off + baselines B0–B4 committed + grid lock."
All three components below, each cited to its signed-off source.

## 1. S2 temporal-leakage sign-off (R-AUDIT, binding; Amendment 2 requires it
reach Ayur verbatim in this packet)

The following is copied VERBATIM from reports/agent_logs/r-audit.md, build-phase
S2 section (audit of commit-2712d65 artifacts):

> ### TEMPORAL-LEAKAGE SIGN-OFF (binding, Amendment 2; own subsection)
>
> Every feature's timestamp lineage was traced against the Oct-1-`sy` cutoff:
>
> - **Season-indexed (families 1, 5):** read only seasons `s < sy` (end May 31
>   `sy` < cutoff); rolling state (`last_pos`, `cum_*`, `own_cum_*`) updates only
>   AFTER season `sy` is emitted — verified in code. `portfolio_loo_rate` uses
>   prior-season label aggregates with the index building subtracted (LOO, no
>   self-leak).
> - **Calendar-year (families 2, 3):** read only `yr ≤ sy−1`; the wide matrices
>   carry columns **2014–2024 / 2020–2024** — a `yr == sy` (or 2025) read is a
>   KeyError, i.e. **structurally impossible, not merely avoided**. Calendar
>   `sy−1` ends Dec 31 `sy−1` < cutoff.
> - **Timestamp-windowed (families 6, 7):** every slice goes through `win()`,
>   which **hard-asserts `hi ≤ cutoff`**; all windows have `hi ∈ {Jun 1 sy,
>   cutoff}` ≤ cutoff. Empirically confirmed on the latest dev season 2025: the
>   max timestamp entering any window is **2025-09-30 23:57** (c6 t365) /
>   **2025-05-31 23:42** (c7 ps) — strictly before the 2025-10-01 cutoff.
> - **Masks NULL not zero (spec §2):** per-season checks — masked seasons are
>   **all-NaN, zero literal-zeros** (e.g. `c311_prior1`@2020: 180,157 rows all
>   NaN; `c6_evt_ps`@2019, `c7_apts_ps`@2019 all NaN); available seasons carry
>   **true zeros** for complaint-free buildings (`c311_prior1`@2021: 0 NaN,
>   158,015 zeros). Aggregate NULLs reconcile to season arithmetic exactly (fam3
>   717,570 = seasons 2017–20; fam6/7 ps 537,413 = 2017–19; t730 717,570).
> - **Fam-6/7 unlock one season before fam-3:** reproduced from first-principles
>   date arithmetic — fam-3 needs full calendar 2019 (floor 2019-06-01 leaves it
>   uncovered → masked through 2020-21), while the prior-season window Oct 2019–May
>   2020 is fully covered → fam-6/7 available from 2020-21. Sound.
> - **B3-frame values recomputed from raw:** `c6_evt_t365`@2025 agrees with the
>   frame on **all 181,863** buildings; `c7_apts_ps`@2025 distinct-apartment counts
>   match on spot-checked buildings.
> - **Target-season sanctity:** both frames assert `max(season) == 2025`; **0 rows
>   ≥ season 2026** in either frame; the spine has no 2026 season. Season 2026-27
>   is structurally absent, not merely untouched.
> - **C1/C2 ruling (flagged for R-AUDIT):** the current-vintage PLUTO (family 4)
>   and registration/owner (family 5 `portfolio_size`) snapshots of slowly-varying
>   STRUCTURAL/ownership attributes are **ACCEPTED**, consistent with WFF's
>   R-LEAK precedent — they encode no post-cutoff EVENT information; the
>   event/label-derived signals (`portfolio_loo_rate`) are properly time-indexed.
>
> **LEAKAGE VERDICT: SIGN-OFF.** No Oct-1 violation on any feature; target-season
> reads are structurally impossible; masks are NULL-not-zero; the bright line
> (season 2026-27) is structurally absent from both frames.

## 2. Baselines B0–B4 committed (source: R-AUDIT S3a SIGN-OFF after one reject
cycle, r-audit.md build §S3a; ledger B42–B48; commit 07df605, pushed)

5-fold forward-chaining means, v ∈ {2021-22…2025-26} (AP / global p@250 /
zero-311 p@250; all average_precision_score, audited):

| Baseline | AP | p@250 | zero-311 p@250 |
|---|---|---|---|
| B0 persistence | 0.1612 | 0.640 | 0.020 |
| B1 logistic-4 | 0.2240 | 0.570 | 0.043 |
| B2 trailing-3 | 0.2077 | 0.670 | 0.042 |
| B3 frozen WFF | 0.3823 | 0.830 | 0.118 |
| B4 two-stage | 0.3865 | 0.810 | 0.110 |

- B3: frozen booster, 343-tree assertion PASS, never retrained; fold metrics
  re-derived from scratch by R-AUDIT (match exact). CAVEAT on the record:
  v=2021–23 are B3's own training seasons (in-sample); on the two out-of-sample
  folds B4 leads AP (0.440 vs 0.422; 0.454 vs 0.434) and zero-311 p@250 at
  v=2025 (0.164 vs 0.124). Descriptive only; the binding comparison is G3.
- B4 effort check ADJUDICATED by R-AUDIT: search genuine (both n=60 samples
  reproduced from seed 42; 300+300 per-config checkpoints; winners re-derived
  from files). Edge-heavy winners on the FROZEN grid ruled satisfactory —
  re-opening toward winners would be post-hoc; tree-count ceilings non-binding
  (early stopping well short). Clip-floor 0.10 INERT (min R̂ 0.2366, zero
  weights clipped; applied IPW ~1.0–4.0, max 3.97).
- Amendment-1 boundary: B4 stage-1 target/signal 311-union-only; c7_* features
  appear only as features (Amendment-1(i) capacity) — no violation.
- Guards: 50 recorded passes / 36 sites; max season ever touched 2025.
- Sequencing: NO S3b/primary code exists in the repo at commit 07df605 —
  baselines-before-primary is now git history.
- Reject cycle on record: 1 REJECT (5 hand-transcribed checkpoint cells vs
  machine stats; code/stats correct throughout) → corrected → re-audit
  SIGN-OFF with source-integrity re-verification. Counter closed at 1.

## 3. Grid lock (source: hyperparam_grid.md; Amendment 2)
The grid was APPROVED at G1 and ratified as the pre-registration (R-B) by
Amendment 2, committed 9eafc29 and pushed 2026-07-16. G2 approval LOCKS it:
S3b trains inside it with no re-opening; selection by the pre-registered rule;
λ frozen in-grid before any test contact (spec §3).

## What clearing G2 authorizes (plan §3 step 8)
A-MODEL S3b: the spec-§3 two-head net exactly, inside the locked grid;
5-seed VALIDATION spread (42–46); freeze candidate = seed-42 artifact +
config + both frames' recipe hashes. Then R-AUDIT S3b including BLIND loss
re-derivation, then the FREEZE gate.

## Calendar
2026-07-16, week 1. G2 target was ~mid-August: ~4 weeks ahead. FREEZE target
early-to-mid Sept; hard line Oct 1; Sep-15 escalation trigger armed.
