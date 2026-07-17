# S3a checkpoint — baselines B0–B4 (A-MODEL)

**Stage:** S3a (plan §3 step 6). **Date:** 2026-07-16. **Spec refs:** §4, §5, §8;
frozen grid `hyperparam_grid.md` (pre-registration per Amendment 2).
**Reproduce:** `.venv/bin/python src/s3a_baselines.py` — idempotent + resumable
(per-unit checkpoints in `outputs/checkpoints/s3a_work/`; a killed run resumes);
rerun after completion re-derives nothing and prints ALL STAGES COMPLETE.
**Seed 42.** Full numbers: `outputs/checkpoints/s3a_stats.json`.
**No S3b code exists** — this commit precedes any primary-model code (plan §3
step 6 sequencing; auditable in git history).

## Protocol (as frozen)

Forward-chaining validation only: v ∈ {2021-22 … 2025-26}, train = development
seasons 2019-20…(v−1); selection = mean validation AP vs `label_c`, tie-break
mean zero-311-stratum p@250 (grid §1). Zero-311 stratum per spec §6: zero
311-union heat events in [2019-06-01, Oct 1 v). Early stopping 50 watches fold
v, **as the frozen grid text specifies** — note: WFF's own implementation
watched v−1 to keep v unseen by ES; our pre-registered text says fold v, so
fold v it is (mild optimism shared equally by every tuned arm; disclosed, not
silently "fixed").

**Test-season guard:** season 2026-27 is structurally absent (both frames
assert max season = 2025 at load) AND `assert_no_test_contact()` ran at every
load, fold, lookback, and refit: **50 recorded passes across 36 distinct call
sites, max season ever touched = 2025** (`s3a_work/guards.jsonl`).

## Results — mean over the 5 validation folds

| Baseline | mean AP | mean p@250 | mean zero-311 p@250 | mean any-311 p@250 |
|---|---|---|---|---|
| B0 persistence | 0.1612 | 0.6400 | 0.0200 | 0.6392 |
| B1 logistic-4 | 0.2240 | 0.5704 | 0.0432 | 0.5744 |
| B2 trailing-3 count | 0.2077 | 0.6704 | 0.0416 | 0.6768 |
| B3 frozen WFF primary | 0.3823 | 0.8304 | 0.1184 | 0.8304 |
| B4 two-stage GBM | 0.3865 | 0.8096 | 0.1104 | 0.8096 |

Per-fold p@250 (v = 2021…2025):
B0 .516/.576/.660/.712/.736 · B1 .460/.528/.616/.616/.632 ·
B2 .528/.624/.676/.716/.808 · B3 .704/.820/.896/.884/.848 ·
B4 .680/.784/.848/.872/.864. Per-fold AP and full p@k/stratum tables in the
stats json. B1 converged all folds. Zero-311 stratum size ≈ 108–121k rows,
874 positives at v=2025 — small-count metrics; read with that in mind.

**B3 in-sample caveat (binding on interpretation):** v ∈ {2021, 2022, 2023}
were TRAINING seasons of the frozen WFF booster — its numbers there are
in-sample and inflated. On the two folds where B3 is out-of-sample (2024,
2025), B4 has the higher AP (0.4395 vs 0.4216; 0.4543 vs 0.4339) and splits
p@250 (0.872 vs 0.884; 0.864 vs 0.848); zero-311 p@250 at v=2025: B4 0.164 vs
B3 0.124. Descriptive validation context only — the pre-registered B3
comparison happens once, at G3, per §10. No claim is made here.

## B0/B1/B2 — verbatim ports

From read-only WFF `src/s3_baselines.py`: `season_of` L52–62; guard pattern
L69–78; metric helpers L81–113; B2 trailing-3 L116–147; B1 L150–196; B0 score
L226–230. Disclosed adaptations (mechanics, not semantics): dev universe
2019-2025 with VAL {2021…2025} per spec §2 + frozen grid §1 (WFF trained from
2017; our censored-model dev window starts 2019-20 — B1's train folds
therefore start at 2019); explicit (season, bbl_n) sort before the seed-42
tie-key permutation (order-robust determinism; WFF used file order); pandas-3
categorical-safe "MISSING" fill in B1; guard takes an explicit allowed-set.
B2's class-C restriction is explicit in code (Rule 6); its lookback caps at
season 2024 (= max(v)−1) so nothing later is ever counted.

## B3 — frozen booster

`imports/primary_lgbm.txt` loaded read-only; **tree-count assertion: observed
343 = expected 343, PASS.** Scored with the booster's own `feature_name()`
order on the S2 B3-recipe frame (frozen vocabularies). Never retrained; no
artifact of it written.

## B4 — two-stage LightGBM (the bar; full effort inside the frozen grids)

**Stage-1 propensity target (S3a construction, per grid §5 "proxy construction
is S3a code, R-AUDIT-checked"):** y_dup = 1{in-season 311-union events ≥ 2} on
label_c = 1 rows — the P2 multiplicity signal at building-season grain.
Rationale: P(any report | confirmed violation) is selection-saturated
(confirmation is itself complaint-triggered), so the reporting-intensity
information conditional on detection lives in the duplicate/multiplicity
margin. **311 union ONLY** (Amendment-1 boundary: ygpa-z7cr appears solely as
c7_* feature columns; it contributes no target, count, exposure, or weight).
In-season = Oct 1–May 31 via the label build's own `season_of`.

- Search: n=60 of 6,561 (sampling seed 42), 5 folds each, per-unit checkpointed.
- Winner (cfg 5411): num_leaves 127, max_depth 6, lr 0.05, n_estimators ceiling
  400 (ES actual 51–162), min_child_samples 100, subsample 0.9, colsample 0.6,
  reg_lambda 5.0. Mean AP **0.9703** — read against target prevalence ≈ 0.88
  (train_dup_rate 0.875, val 0.903 at v=2025): given detection, multiplicity is
  near-universal; the model's margin over base rate is real but the signal is
  concentrated. Runner-up 0.97031 (near-tie).
- Boundary status: num_leaves/min_child_samples/reg_lambda high-edge, colsample
  low-edge, n_estimators low-edge (non-binding — ES stopped at 51–162 ≪ 400);
  max_depth/lr/subsample interior.

**Stage 2 (IPW risk):** positives weighted 1/max(R̂, clip_floor), R̂ from the
frozen stage-1 winner refit per fold (train rows only; cached, resumable).

- Search: n=60 of 59,049 (sampling seed 42), stage 2 tuned against the frozen
  stage-1 winner per grid §6.
- Winner (cfg 21485): num_leaves 63, max_depth −1, lr 0.02, n_estimators
  ceiling 1500 (ES actual 163–433, ceiling non-binding), min_child_samples 50,
  subsample 0.9, colsample 0.6, reg_lambda 5.0, scale_pos_weight 1,
  clip_floor 0.10. Mean AP 0.3865; runner-up 0.3863 (near-tie; tie-break
  metric recorded for both).
- Boundary status: max_depth/lr/scale_pos_weight low-edge, n_estimators/
  reg_lambda/clip_floor high-edge, colsample low-edge; num_leaves/
  min_child_samples/subsample interior. NOTE the clip-floor dimension is
  **inert in practice**: min R̂ over all dev rows = 0.2366 > 0.10, so no weight
  was ever clipped (share_below_clip = 0) and all three floor values are
  equivalent here — applied IPW weights ran ~1.0–4.0 (max applied weight over
  positives 3.97). The mild correction is itself a
  finding: conditional on detection, predicted duplicate-propensity never
  drops low enough to up-weight anyone strongly.
- Edge-heavy winners are reported as-is; the grid is frozen (Amendment 2) and
  is not re-opened here. If Ayur wants a grid amendment at G2, that is a dated
  spec/grid decision, not ours.

**Frozen B4 artifacts (refit on all dev seasons, fixed n_estimators = round
(mean fold best_iter), no ES — WFF frozen-refit convention):**
`outputs/models/b4_propensity_lgbm.txt` (95 trees),
`outputs/models/b4_risk_lgbm.txt` (282 trees),
`outputs/models/b4_frozen_config.json` (configs + R̂ summary + protocol).
LightGBM 4.6.0 (recorded; installed this stage with scikit-learn 1.9.0).

## Deviations & operational notes (all disclosed above in place)

1. ES watches fold v per the frozen grid text (WFF watched v−1) — pre-registered
   wording honored over WFF convention.
2. Dev-window adaptation of the verbatim ports (2019+ train folds) per spec §2.
3. Explicit sort + pandas-3 dtype mechanics in the ports (semantics unchanged).
4. Stage-1 target construction decision recorded here for R-AUDIT (the grid
   deliberately deferred it to S3a code).
5. Clip-floor inertness (no weight clipped anywhere) — grid dimension reported
   as evaluated but non-operative at these R̂ values.
6. Two pip installs this stage (lightgbm, scikit-learn) — first modeling stage;
   versions pinned in the stats json and b4_frozen_config.json.

**Storage:** repo tabular+outputs ≈ 418 MB ≤ 2 GB. **Season 2026-27:**
untouched, asserted 50×. **No Rule-9 conditions.** → R-AUDIT S3a.

---

# B5 appendix — uncorrected retrained LightGBM (Amendment 3)

**Added 2026-07-17 under the S3a protocol (Amendment 3, commit aa27494); G2
approved; S3b still barred until this section is committed and audited.**
Script: `src/s3a_b5.py` (separate file — the signed-off `s3a_baselines.py` is
not modified; B5 imports its audited functions: frame loader, guards, metrics,
grid machinery, fold protocol). Same operational discipline: bounded runs,
per-unit checkpoints in `s3a_work/b5_risk/`, resumable, seed 42.

## Clip-floor handling (stated BEFORE training, per LEAD's dispatch)

Amendment 3 sets B5's grid = B4's stage-2 grid VERBATIM (n=60, sampling seed
42). The clip-floor dimension exists only through IPW, which B5 omits. Ruling
adopted here: the **sample is inseparable** — B5 trains THE SAME 60 configs the
seed-42 draw produced for B4 stage 2 (indices identical), with `clip_floor`
carried as **inert metadata** (it touches no weight, no parameter, no code path
in B5). Verified before training: projecting the 60 configs onto the remaining
9 dimensions yields **60 distinct configs, zero collisions** — no dedup needed,
and every B5 config is the exact uncorrected twin of its B4 stage-2 counterpart
(same index, same 9 operative values), which is precisely the like-for-like
attribution Amendment 3 asks for. `scale_pos_weight` remains operative (it is
an objective-level knob, not an IPW artifact). Flagged to LEAD before training.

## B5 protocol and results (machine-generated table below)

Identical folds, frame, ES/selection rule, and per-unit resume discipline as
B4 stage 2; plain binary objective on `label_c`, no weights of any kind. All
300 (config, fold) units completed and checkpointed; idempotent rerun clean
(B5 COMPLETE, zero recomputation). Guards recorded to the same guards.jsonl.
Numbers below are copied verbatim from `s3a_work/b5_table.md`, which
`src/s3a_b5.py stage_report()` generates from the fold jsons (no hand
transcription; s3a_stats.json carries the same values under `b5_*` keys,
added additively — no S3a-audited key altered).

| Model | mean AP | mean p@250 | mean zero-311 p@250 | mean any-311 p@250 |
|---|---|---|---|---|
| B4 two-stage GBM (corrected) | 0.3865 | 0.8096 | 0.1104 | 0.8096 |
| B5 uncorrected twin | 0.3870 | 0.8136 | 0.1136 | 0.8136 |
| Δ (B5 − B4) | +0.0006 | +0.0040 | +0.0032 | +0.0040 |

Per-fold B5 p@250 (v = 2021…2025): 0.6800 / 0.7800 / 0.8520 / 0.8920 / 0.8640.
Per-fold B5 AP: 0.2826 / 0.3376 / 0.4203 / 0.4395 / 0.4551.
Per-fold B5 zero-311 p@250: 0.1040 / 0.0880 / 0.1120 / 0.1000 / 0.1640.

**Winner (cfg 20928, the same index in B4's stage-2 sample):** num_leaves 63
(interior), max_depth −1 (low-edge), lr 0.02 (low-edge), n_estimators ceiling
800 (interior; ES actual 236–578), min_child_samples 100 (high-edge),
subsample 0.7 (low-edge), colsample 0.8 (interior), reg_lambda 0.0 (low-edge),
scale_pos_weight sqrt (interior); clip_floor 0.02 carried as inert metadata.
Mean AP 0.38702, runner-up 0.38679. Note the operative winner DIFFERS from
B4 stage 2's (cfg 21485): removing IPW moved the optimum.

**Attribution reading (descriptive, per Amendment 3's purpose):** B5 − B4
deltas are ≈ 0 to slightly positive on every observed-label mean (+0.0006 AP,
+0.0040 p@250, +0.0032 zero-311 p@250). Like-for-like, the IPW censoring
correction does not improve — and marginally trails — observed-label
validation metrics. This is the spec-§11 named limitation operating as
predicted (observed-label evaluation penalizes correction by construction:
the corrected model deliberately re-ranks toward failures the observed label
under-counts), not evidence the correction is worthless — that adjudication
is exactly what the §10 criteria and the HSP external check exist for, at G3,
against B3. Recorded as-is; no claim either direction.

**Frozen B5 artifact:** `outputs/models/b5_lgbm.txt` (405 trees, refit all dev
seasons, fixed n_estimators = round(mean fold best_iter), no ES) +
`b5_frozen_config.json`. Storage after B5: repo ≈ 422 MB ≤ 2 GB. Season
2026-27 untouched (guards: every fold/refit asserted; cumulative log in
guards.jsonl). No S3b/primary code exists. No Rule-9 conditions. → R-AUDIT.
