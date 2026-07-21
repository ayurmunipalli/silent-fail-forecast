# RP2 checkpoint — R-PILOT single-shot evaluation on season 2025-26 (A-MODEL)

**RETROSPECTIVE AND NON-BLIND** (model_spec.md Amendment 5(iii)): the
project's conception and the frozen spec postdate season 2025-26; nothing
here has prospective standing or carries any weight at G3; the frozen G3
pre-registration (§10 margins, frozen bundle, Amendment-4 freeze entry,
2026-27 bright line) is untouched. R-PILOT results are reported separately
from G3 and never enter it.

**Stage:** RP2 (Amendment 5(ii)), under LEAD's heightened single-shot
protocol: script pre-audited by R-AUDIT (sign-off, no defects; subprocess
scoring reproduced RP1 persisted scores to 1.19e-07) and REHEARSED on season
2024 before the one contact. **The single shot was executed EXACTLY ONCE,
2026-07-21T06:52:14** (`SINGLE_SHOT_SPENT.sentinel`; authorization ledger
B114; commit c8f10d9 lineage). **Script:** `src/rp2_eval.py --the-single-shot`
— a rerun refuses to recompute (sentinel semantics). **Seed 42.** Full
numbers: `outputs/checkpoints/rp2_work/single_shot_2025/rp2_stats.json`;
predictions persisted at building-season grain:
`outputs/checkpoints/rp2_work/single_shot_2025/predictions_2025.parquet`
(181,863 rows × 14 cols incl. every model's score, joint F/p/q, stratum flag,
label column).

**§11 caveat (D11), attached to every number below:** all metrics are
computed against the OBSERVED label Y_obs; spec §11 names observed-label
evaluation as penalizing the censoring correction by construction.

## Protocol facts

- Eval universe: the hash-pinned S2 frames' season-2025 rows (RP0: pre-Oct-1-2025
  by construction), 181,863 rows, 8,897 label_c positives. D9 asserted: eval
  slice seasons == {2025}; contacted once.
- Scoring set (all sha256-asserted at load): rpilot_joint_seed42.pt (cfg 2009,
  u*=25, E*=8; F/p/q from the bundle's own design/scaler, scored in the
  torch-only subprocess, bbl alignment hard-asserted), rpilot_b4 risk score
  (both B4 stages hash+tree-asserted, 90/332 trees), rpilot_b5 (307 trees),
  B3 as-is (343-tree assertion PASS, D10), B0–B2 recomputed from frozen
  definitions (train/lookback < 2025). The frozen build bundle
  s3b_primary_seed42.pt was NOT scored and NOT touched (Amendment 5(i)).
- Zero-311 stratum (spec §6): zero 311-union events in [2019-06-01,
  2025-10-01) per bbl → 120,631 stratum rows.
- Guard facts: 6 distinct sites, max season ever touched 2025 (the authorized
  contact), **zero ≥2026 firings** — season 2026-27 untouched (Rule 3).

## Results (machine-generated, pasted verbatim from rp2_work/single_shot_2025/rp2_table.md)

**RETROSPECTIVE AND NON-BLIND** — RP2 single_shot table, season 2025-26 (machine-generated).

| Model | AP | p@250 | zero-311 p@250 | any-311 p@250 |
|---|---|---|---|---|
| B0 | 0.2155 | 0.7360 | 0.0280 | 0.7360 |
| B1 | 0.2784 | 0.6320 | 0.0520 | 0.6320 |
| B2 | 0.2734 | 0.8000 | 0.0480 | 0.8000 |
| B3 | 0.4339 | 0.8480 | 0.1240 | 0.8480 |
| B4 | 0.4533 | 0.8560 | 0.1600 | 0.8560 |
| B5 | 0.4528 | 0.8640 | 0.1520 | 0.8640 |
| joint_q | 0.4408 | 0.8280 | 0.1160 | 0.8280 |
| joint_F | 0.4406 | 0.8280 | 0.1160 | 0.8280 |

Criterion-3-style (dual screen, W=30): 
- joint_F: realized n=35, T=-0.0022, sign-test p=0.9996, reject@.05=False (zeros dropped 1)
- B4: realized n=35, T=-0.0004, sign-test p=0.9552, reject@.05=False (zeros dropped 0)
- B5: realized n=35, T=-0.0004, sign-test p=0.9552, reject@.05=False (zeros dropped 0)
- sensitivity 311-only screen: n=36, joint T=-0.0023

Zero-311-stratum p@250 vs B3 on the same stratum and season (Amendment 5(ii)
comparison, recorded as-is): B3 0.1240 · joint_F 0.1160 · B4 0.1600 ·
B5 0.1520.

## Criterion-3-style detail (frozen Amendment-2 / grid-§7 statistic; realized n reported)

HSP waterfall (P3 machinery verbatim; every exclusion counted): 197 distinct
HSP lots → 7,810 HSP-lot class-C events all-time → 1,488 in season 2025-26 →
0 excluded pre-program-start → 0 excluded for W=30 window coverage → 1,488
eligible → **104 silent events under the dual screen (311-union AND
ygpa-z7cr, W=30) across 35 distinct buildings**; 114 / 36 buildings under the
311-only screen. All screened buildings present in the eval universe
(missing = none).

| Screen | Model | realized n | zeros dropped | n sign test | n positive | T = median Δ | one-sided p | reject @ .05 |
|---|---|---|---|---|---|---|---|---|
| dual | joint_F | 35 | 1 | 34 | 8 | −0.002221 | 0.99959 | False |
| dual | B4 | 35 | 0 | 35 | 13 | −0.000352 | 0.95523 | False |
| dual | B5 | 35 | 0 | 35 | 13 | −0.000374 | 0.95523 | False |
| 311-only | joint_F | 36 | 1 | 35 | 8 | −0.002298 | 0.99975 | False |
| 311-only | B4 | 36 | 0 | 36 | 14 | −0.000344 | 0.93375 | False |
| 311-only | B5 | 36 | 0 | 36 | 14 | −0.000330 | 0.93375 | False |

(Δ_b = pct_model(b) − pct_B3(b), average-rank percentile over all 181,863
scored buildings; joint uses the F ranking; B4/B5 are the mechanical
disclosed secondaries; per-building Δ vectors persisted in rp2_stats.json.)

All numbers recorded as-is per Amendment 5(iii) — disclosed in full whichever
direction; no claim, no interpretation here. Adjudication of what the pilot
means is Ayur's, in the pilot result packet; G3's pre-registration is
unaffected.

## Deviations & operational notes

1. Two-process design (torch subprocess for the joint; lightgbm/sklearn in
   the main process) — the RP1 OpenMP incompatibility proven in both
   directions during Phase A; R-AUDIT pre-audited including a 1.19e-07
   score-reproduction check against RP1's persisted scores.
2. Rehearsal (Phase A, season 2024) preceded the shot; rehearsal outputs
   remain under `rp2_work/rehearsal_2024/` labeled REHEARSAL (in-sample for
   the pilot models; machinery validation only).
3. Labels are the frames' audited S2 whitelist `label_c` (class-C restriction
   explicit in the S2 label build; Rule 6) — no label re-derivation.
4. Season-2025 HSP events all postdate their lots' program starts (0
   pre-program exclusions; all cohorts started ≤ 2025-06-11) and 0 window-
   coverage exclusions (stores span the full season + W=30 margins).
5. Sentinel-first semantics: the sentinel was written before compute; a
   mid-shot crash would have burned the contact and escalated to Ayur — it
   completed cleanly instead (exit 0, ~6 min).

**Storage:** data+outputs+imports ≈ 1.4 GB ≤ 2 GB. **Season 2026-27:**
untouched, zero guard firings. **No Rule-9 conditions. No fabrication
events.** → R-AUDIT RP2 post-audit.
