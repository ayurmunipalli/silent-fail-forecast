# Hyperparameter grid proposal — silent-fail-forecast — posted for G1 approval

**Status: PROPOSED (A-MODEL, 2026-07-16). Not locked until Ayur approves at G1.**
Per spec §8: grid frozen before any 2026-27 contact is possible, i.e., before the
Oct 1 model freeze. No data was used to produce this proposal beyond the signed-off
S1 scale numbers (s1_stats.json, process_log B21/B23) and phase-0 descriptives
already cited in the frozen spec. Precedent cited throughout: WFF's G1-locked grid
(`<WFF>/outputs/checkpoints/hyperparam_grid.md`) and frozen config
(`frozen_model_config.json`), read-only.

**Frozen constraints this grid honors (spec §3/§4/§8; CLAUDE.md):**
- Selection on **forward-chaining validation ONLY** — never random K-fold; never
  any 2026-27 contact (structurally impossible: the season does not exist in any
  frame, and an assert-no-test guard runs in every S3 script regardless).
- **Seed 42** for all primary numbers; the 5-seed spread (seeds 42–46, hyperparams
  fixed) is **VALIDATION-based** (spec §8, settled doctrine).
- The §3 two-head net is the ONLY DL architecture; nothing here explores beyond it.
- λ, u*, penalty weights, and the criterion-3 statistic are frozen WITH this grid.
- Family 7 (ygpa-z7cr, Amendment 1) is **features/criterion-3-screen only, never
  the loss** — no hyperparameter in this grid touches that boundary; the auxiliary
  NLL's complaint counts come solely from the §2 311 union.

---

## 1. Forward-chaining validation protocol (applies to every tuned model here)

- Development seasons 2019-20…2025-26 (spec §2); 2017-18/2018-19 contribute lag
  features only.
- Validation seasons **v ∈ {2021-22, 2022-23, 2023-24, 2024-25, 2025-26}** (plan §3
  step 6: per mask coverage — the 311-availability mask needs ≥2 seasons of
  complaint history behind the earliest v). Fold: train on development seasons < v,
  validate on v. Five folds, expanding window.
- **Selection metric (pre-registered here):** primary = mean across folds of
  average precision (PR-AUC) of the observed-label prediction (F·R for the net;
  the IPW risk score × propensity composition is NOT used — B4's risk stage is
  selected on its own observed-label AP, see §5) against Y_obs on v; tie-break =
  mean **zero-311-stratum precision@250** of the deployment ranking (F for the
  net, risk score for B4) on v. Rationale: AP against Y_obs is the only
  label-consistent fit measure; the tie-break aligns selection pressure with §10
  criterion 1 without touching any test season. Both metrics computed by one
  shared function, logged per fold.
- After selection, the frozen config is refit on all development seasons
  (2019-20…2025-26) to produce the freeze candidate (WFF refit precedent).

## 2. Two-head net — shared encoder (spec §3)

MLP over the §7 feature families 1–6 (+7 per Amendment 1), exact feature list
frozen at the S2 checkpoint. Inputs standardized (fit on train folds only);
availability masks enter as indicator columns per the WFF §3 pattern (NULL-masked,
never zero-filled).

| Hyperparameter | Candidate values |
|---|---|
| encoder width (units per hidden layer) | {64, 128, 256} |
| encoder depth (hidden layers) | {2, 3} |
| dropout (all hidden layers) | {0.0, 0.15} |
| activation | ReLU (fixed) |
| hidden-layer norm | LayerNorm (fixed) |
| head F | Linear(width→1) + sigmoid (fixed, spec §3) |
| head p | Linear(width→1) + sigmoid → per-unit p ∈ (0,1) (fixed, spec §3) |

## 3. Two-head net — loss, link, and optimization

Loss exactly as spec §3: `L = BCE(Y_obs, F·R) + λ·NLL(complaint counts | head p,
building-season) + shape penalties`, with `R = 1 − (1−p)^min(u, u*)`. The NLL is
the binomial likelihood of observed distinct complaint events against
confirmed-incident exposure at building-season grain on complaint-positive
building-seasons (grain per spec §3; per-incident is diagnostics only). Counts
source: §2 311 union ONLY (Amendment-1 boundary).

| Hyperparameter | Candidate values | Notes |
|---|---|---|
| **λ** (auxiliary NLL weight) | {0.1, 0.3, 1.0, 3.0} | log-spaced; frozen with grid before any test contact (spec §3) |
| **u\*** (unit cap in the thinning link) | {25, 50, 100} | brackets the P4 gradient knee (78.4% zero-311 at 2–5 units vs 16.8% at 50+); u from PLUTO unitstotal |
| learning rate (Adam) | {3e-4, 1e-3} | AdamW, β defaults |
| LR schedule | cosine decay to 0 over max epochs (fixed) | |
| weight decay | 1e-5 (fixed) | |
| batch size | 8192 (fixed) | ~180k rows/season; full dev set fits in memory |
| max epochs | 200, early stopping patience 20 on fold-v total validation loss (fixed) | epoch count is a ceiling, not a tuned dim |
| class reweighting | NONE (fixed) | BCE unweighted so F·R stays calibrated to observed prevalence; ranking metrics don't need reweighting |
| seed | 42 (fixed) | 5-seed validation spread (42–46) after selection, hyperparams fixed |

## 4. Shape/monotonicity penalties (spec §3 "monotone/shape penalties per grid")

Monotonicity of R in u is **structural** (the thinning link), not penalized — no
penalty needed or proposed for it. Two penalty forms are proposed; each grid
includes 0 so validation can drop them:

1. **Ω₁ — identification shrinkage on head p:**
   `Ω₁ = μ₁ · mean_batch[(logit p_i − logit p̄)²]`, where p̄ is the training-fold
   pooled per-unit reporting rate (a constant computed from train folds only).
   Purpose: anchors head p in the zero-311 mass where the likelihood is silent —
   the §3 identification statement's "shared-support extrapolation" made explicit
   as a ridge toward the pooled rate rather than an unconstrained extrapolation.
   **μ₁ ∈ {0, 0.01, 0.1}.**
2. **Ω₂ — F-smoothness under history perturbation (monotone hinge):**
   for a per-batch subsample of buildings, perturb the family-1 chronic-history
   inputs (`viol_cnt_prior_cum`-analogue, post-standardization) by +δ (δ = 0.5 SD,
   fixed) and penalize decreases:
   `Ω₂ = μ₂ · mean[max(0, F(x) − F(x⁺δ))²]`.
   Purpose: soft monotonicity of failure risk in chronic violation history — the
   one direction with unambiguous domain sign. **μ₂ ∈ {0, 0.1, 1.0}.**

No other penalties. Exact perturbed-column list is fixed at S2 when the feature
list freezes (family-1 cumulative-count columns only), before S3b begins.

## 5. B4 — two-stage LightGBM (spec §5; the bar, not a strawman)

Both stages LightGBM 4.x, `random_state=42`, tuned with the same effort and the
same forward-chaining protocol as the net. Stage grids mirror the WFF locked-grid
shape (legitimate precedent — same data family, same scale).

**Stage 1 — propensity model** (duplicate-count signal at building-season grain →
detection propensity R̂; trained on complaint-positive building-seasons, predicted
over all):

| Hyperparameter | Candidate values |
|---|---|
| objective | `binary` on the detection proxy (fixed; proxy construction is S3a code, R-AUDIT-checked) |
| metric | `average_precision` (fixed) |
| num_leaves | {31, 63, 127} |
| max_depth | {-1, 6, 10} |
| learning_rate | {0.02, 0.05, 0.1} |
| n_estimators | {400, 800, 1500} ceiling, early stopping 50 on fold v |
| min_child_samples | {20, 50, 100} |
| subsample | {0.7, 0.9, 1.0} |
| colsample_bytree | {0.6, 0.8, 1.0} |
| reg_lambda | {0.0, 1.0, 5.0} |

**Stage 2 — IPW risk model** (observed label Y_obs, sample weight 1/R̂ from stage 1):

| Hyperparameter | Candidate values |
|---|---|
| objective / metric | `binary` / `average_precision` (fixed) |
| num_leaves | {31, 63, 127} |
| max_depth | {-1, 6, 10} |
| learning_rate | {0.02, 0.05, 0.1} |
| n_estimators | {400, 800, 1500} ceiling, early stopping 50 |
| min_child_samples | {20, 50, 100} |
| subsample | {0.7, 0.9, 1.0} |
| colsample_bytree | {0.6, 0.8, 1.0} |
| reg_lambda | {0.0, 1.0, 5.0} |
| scale_pos_weight | {1, √(neg/pos), neg/pos} |
| **R̂ clip floor** (IPW truncation: R̂ ← max(R̂, floor)) | {0.02, 0.05, 0.10} |

The clip floor is a genuine B4 hyperparameter (weight cap 1/floor); it is tuned
jointly with stage 2 and frozen with it. B0/B1/B2 have no hyperparameters (ported
verbatim from WFF `s3_baselines.py`); B3 is the frozen booster
(`imports/primary_lgbm.txt`, 343-tree assertion) — nothing tunable, nothing tuned.

## 6. Search budgets (WFF precedent: randomized n≈60 inside a locked space)

| Model | Cartesian size | Search |
|---|---|---|
| Two-head net (§2–§4 dims: 3·2·2 × 4 × 3 × 2 × 3 × 3) | **2,592** | randomized, **n = 60**, sampling seed 42 |
| B4 stage 1 (3·3·3·3·3·3·3·3) | 6,561 | randomized, **n = 60**, sampling seed 42 |
| B4 stage 2 (stage-1 dims × 3 spw × 3 clip) | 59,049 | randomized, **n = 60**, sampling seed 42 (stage 2 tuned against the frozen stage-1 winner) |

Every sampled config is evaluated on all five forward-chaining folds; selection on
the §1 pre-registered metric. Search happens INSIDE this locked space only — no
config outside it may be trained (net: spec §3 "no architecture exploration beyond
the frozen grid").

## 7. §10 criterion-3 — the EXACT pre-registered rank statistic

Spec §10.3 requires the exact statistic frozen with this grid. Proposed, to be
computed ONCE at G3 (summer 2027) and never before:

- **Event set E:** HSP-lot whitelisted class-C violation events in season 2026-27
  passing the silent screen: zero associated 311 complaints at W=30 (P3 heuristic,
  verbatim association rule: inclusive bounds, calendar-date truncation, int64
  bbl) **AND** zero associated ygpa-z7cr heat complaints at W=30 (the Amendment-1
  sharpening — screen only; both screens applied identically).
- **Unit of analysis:** distinct building (BBL). Multi-event buildings enter once
  (dedupe prevents chronic buildings from dominating the median).
- **Rank-percentile:** for score s and building b,
  `pct_s(b) = 1 − (rank_s(b) − 1) / (N − 1)`, where rank 1 = highest score among
  all N buildings scored for 2026-27 (full universe, both models score the
  identical building set; ties get average rank). Higher pct = ranked riskier.
- **Per-building improvement:** `Δ_b = pct_F(b) − pct_B3(b)`, F = the frozen
  primary's failure head, B3 = the frozen WFF booster on the WFF-recipe frame.
- **Test statistic:** `T = median_b(Δ_b)`.
- **Pre-registered pass margin:** **T > 0 AND one-sided exact sign test of
  H₀: median(Δ) ≤ 0 rejects at α = 0.05** (Δ_b = 0 buildings dropped from the sign
  test per the standard exact procedure; count reported).
- Reported alongside (not pass/fail): full distribution of Δ_b, |E|, and the same
  statistic under the 311-only screen (no ygpa sharpening) as a sensitivity line —
  reported as-is either way.

This statistic is frozen the moment Ayur approves this document; the G3 script
implements it verbatim.

## 8. What locking this document means

Approval at G1 freezes: every candidate set above, the search budgets and
sampling seed, the selection metric and tie-break, the two penalty forms, λ and
u* candidate sets, both B4 grids including the clip floor, and the criterion-3
statistic in §7. Changes after approval require a dated amendment (Rule 8). The
winning configs are additionally frozen at G2 (baselines) and the FREEZE gate
(primary), per plan §3.
