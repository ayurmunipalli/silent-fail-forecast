# G1 gate packet — silent-fail-forecast build phase

Compiled by LEAD 2026-07-16 from signed-off artifacts only. States what the
pre-committed criteria say; recommends nothing. Adjudication is Ayur's.

## What plan §3 step 4 says G1 requires
"S1 coverage report + grid proposal + R-A resolution. HALT until approval."
All three components exist; each is cited below to its signed-off source.

## FLAG — spec §12 vs plan §2/§3 gate-scope conflict (unresolved, Ayur's)
Spec §12: "G1 = data/features + leakage sign-off." Plan §2/§3 sequence G1
BETWEEN S1 (data) and S2 (features + binding leakage audit), so under the plan
the leakage sign-off occurs after G1, gated instead inside S2's R-AUDIT pass
before S3a. Spec > plan; per CLAUDE.md the conflict is flagged, not resolved.
G1 adjudication under the plan's sequencing therefore clears DATA + GRID + R-A
only; the features/leakage sign-off would reach Ayur's eyes at G2 rather than
at a gate of its own, unless Ayur re-scopes.

## 1. S1 coverage (source: R-AUDIT S1 SIGN-OFF, r-audit.md build §S1; ledger B21/B23; commit fcbdc81, pushed)
- 7/7 dataset IDs live-verified 2026-07-16; all sha256s match bootstrap records.
- 311 union: 93,022 + 1,645,614 = 1,738,636; dedupes 0; deliverable 1,731,513
  rows (2019-06-01…2026-07-13); seam A identical to phase-0; seam B clean
  (0 late, 0 disappeared).
- Spine: registrations distinct-BBL = frozen 181,863 universe (set equality);
  per-season rows AND label-C positives = WFF frozen labels, 9/9 seasons.
- Pulls: violations 149,585 @2017-10-01 floor (disclosed addition, audited
  sound; dual-floor comparison on record); context 2,012,740 groups;
  contacts 782,024; PLUTO full 858,602; ygpa-z7cr 1,754,951 in 7 disjoint
  parts (per-part = live probes exactly; cross-part dup problem_id 0).
- Storage 341.6 MB / 2 GB. Idempotency byte-identical. 2026-27 structurally
  untouched (0 rows ≥ 2026-10-01).
- Anomalies on record (all disclosed, all audited): two external background-
  task kills → Ayur ruling (b) → 7-part foreground mechanic; unsandboxed .env
  mechanic (token value verified absent from repo); seam-B zero-accrual
  verified genuine. S2 flag standing: ygpa problem_duplicate_flag Y = 761,130
  (43.4%) — routed to A-FEAT under the leakage/feature protocols.

## 2. Grid proposal (source: outputs/checkpoints/hyperparam_grid.md, status PROPOSED; a-model.md M1)
- Net: width{64,128,256}×depth{2,3}×dropout{0,0.15}×λ{0.1,0.3,1.0,3.0}×
  u*{25,50,100}×LR{3e-4,1e-3}×μ₁{0,.01,.1}×μ₂{0,.1,1} = 2,592; randomized
  n=60, sampling seed 42; AdamW+cosine, batch 8192, 200 epochs, patience 20.
- Shape penalties (each grid includes 0): Ω₁ logit-p ridge to pooled train-fold
  reporting rate; Ω₂ monotone hinge on F under +0.5-SD chronic-history
  perturbation. R-monotonicity in u structural via the link, no penalty.
- B4: propensity LGBM 6,561 Cartesian n=60; IPW risk LGBM 59,049 Cartesian
  n=60 (incl. scale_pos_weight, R̂ clip-floor {0.02,0.05,0.10}), tuned against
  frozen stage-1 winner. B0–B2 hyperparameter-free; B3 frozen/untouched.
- Budget: 180 trained configs × 5 forward-chaining folds (v ∈ 2021-22…2025-26).
- Pre-registered selection: mean validation AP vs Y_obs; tie-break mean
  zero-311-stratum p@250 of the deployment ranking; refit on all dev seasons.
- §10-criterion-3 statistic (to freeze with the grid): T = median over distinct
  silent-screened HSP buildings (zero 311 AND zero ygpa heat complaints at
  W=30; screen per Amendment 1) of pct_F − pct_B3 over the full scored 2026-27
  universe; pass = T > 0, one-sided exact sign test, α = 0.05, computed once
  at G3.

## 3. R-A resolution (source: model_spec.md Amendment 1; ledger B7–B10)
Ruled ADMIT non-load-bearing by Ayur 2026-07-16; Amendment 1 drafted, approved
verbatim, appended, committed in fcbdc81. Boundary: family 7 + criterion-3
screen only; never the loss. Family-7 raw data pulled and audited at S1.

## What clearing G1 authorizes (plan §3 step 5)
Dispatch A-FEAT S2 (both feature frames) → R-AUDIT S2 incl. binding temporal-
leakage protocol → S3a. The grid LOCKS at G2 per spec §12; approval here is
of the proposal as the frozen search space.

## Calendar
2026-07-16, week 1. G1 target ~end July: ahead. FREEZE target early-to-mid
Sept; hard line Oct 1; Sep-15 escalation trigger armed.
