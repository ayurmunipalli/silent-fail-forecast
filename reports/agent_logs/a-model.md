# A-MODEL agent log — build phase

Numbered entries, appended only. Binding file: `.claude/agents/a-model.md`.

---

**M1 | 2026-07-16 | Step 3: hyperparameter grid proposal written.**

Dispatch: plan §3 step 3 ONLY (grid proposal for G1). No model code written, no
baseline work started — hard sequencing honored (S3a awaits G1 + dispatch; S3b
awaits G2).

Read in full before acting: a-model.md (binding), CLAUDE.md, model_spec.md
§3/§4/§5/§8/§10 + Amendment 1, plan.md §3 steps 3/6/8. Scale context read (not
analyzed): data/s1_stats.json, data/PROVENANCE.md, process_log B21/B23. WFF
read-only precedent consulted: `outputs/checkpoints/hyperparam_grid.md` (G1-locked
grid shape, randomized-n≈60 convention) and `frozen_model_config.json` (B3's 343
trees, 30-feature recipe, refit convention). Nothing written to the WFF repo.

Deliverable: `outputs/checkpoints/hyperparam_grid.md`. Contents:

- Forward-chaining protocol pre-registered: v ∈ {2021-22…2025-26}, train < v,
  selection = mean validation AP of the observed-label prediction vs Y_obs,
  tie-break = mean zero-311-stratum p@250 of the deployment ranking.
- Net grid: width {64,128,256} × depth {2,3} × dropout {0,0.15} × λ {0.1,0.3,1,3}
  × u* {25,50,100} × lr {3e-4,1e-3} × μ₁ {0,0.01,0.1} × μ₂ {0,0.1,1} = 2,592
  configs; randomized n=60, sampling seed 42. Optimizer/schedule/batch/epochs
  fixed (AdamW, cosine, 8192, 200 + ES patience 20). No class reweighting
  (calibration of F·R preserved).
- Two penalty forms proposed per spec §3: Ω₁ logit-p ridge toward the pooled
  train-fold reporting rate (identification anchor in the zero-311 mass); Ω₂
  monotone hinge on F under +0.5-SD chronic-history perturbation. Both grids
  include 0. R-monotonicity in u needs no penalty (structural link).
- B4: two full LightGBM grids mirroring the WFF locked-grid shape — propensity
  stage (6,561 Cartesian) and IPW risk stage (59,049 Cartesian incl.
  scale_pos_weight and the R̂ clip floor {0.02,0.05,0.10}); randomized n=60 each,
  stage 2 tuned against the frozen stage-1 winner. B0–B2 no hyperparameters;
  B3 frozen, untouched.
- §10 criterion-3 exact statistic: distinct-BBL median rank-percentile
  improvement T = median(pct_F − pct_B3) over the 2026-27 HSP silent-event
  buildings (dual W=30 screen: 311 union AND ygpa-z7cr per Amendment 1, screen
  only); pass = T > 0 AND one-sided exact sign test α = 0.05; 311-only-screen
  sensitivity line reported as-is.
- Amendment-1 boundary restated in the document: ygpa-z7cr never enters the
  loss; the auxiliary NLL counts come solely from the §2 311 union.

No data touched beyond the permitted scale reads. Season 2026-27: untouched
(criterion-3 statistic is a definition, computed only at G3). No Rule-9
conditions encountered. Reported to LEAD via SendMessage; idle pending G1.

---

**M2 | 2026-07-16 | Stage S3a: baselines B0–B4 complete.**

Dispatch: plan §3 step 6, after G1 clearance + Amendment 2 (grid ratified as
pre-registration) + S2 sign-off (commit 2712d65). Hard sequencing honored: NO
S3b code exists — no encoder, no two-head anything; this stage precedes all
primary-model code, auditable in git history.

Execution: `src/s3a_baselines.py`, 6 bounded foreground invocations (LEAD's
kill-resilience instruction), per-unit resume checkpoints; final rerun
confirmed idempotent (ALL STAGES COMPLETE with zero recomputation). Installed
lightgbm 4.6.0 (= WFF's B3 version) + scikit-learn 1.9.0 into .venv — one
sandbox SSL retry on pip (recorded harness mechanic, same class as the S1/P4
.env note; resolved unsandboxed against pypi, no Rule-9 condition).

Results (5-fold means; full tables in outputs/checkpoints/s3a_stats.json):
B0 AP .1612 / p@250 .6400 / zero-311 p@250 .0200; B1 .2240/.5704/.0432;
B2 .2077/.6704/.0416; B3 .3823/.8304/.1184 (IN-SAMPLE on v=2021–23, its WFF
training seasons — caveat stated in checkpoint); B4 .3865/.8096/.1104. On
B3's two out-of-sample folds B4 wins AP (0.4395 vs 0.4216; 0.4543 vs 0.4339),
splits p@250, and takes zero-311 p@250 at v=2025 (.164 vs .124). Descriptive
only; binding comparison is G3.

Key stage facts: B3 tree-count assertion 343=343 PASS. Guard assertions: 50
recorded passes, 36 sites, max season ever touched 2025. B0/B1/B2 ported
verbatim (WFF s3_baselines.py line ranges cited in checkpoint; adaptations
disclosed: dev window 2019+, explicit sort for tie-key, pandas-3 dtype
mechanics). B4 stage-1 target = 1{in-season 311-union events ≥ 2} on
label_c=1 rows (P2 multiplicity signal; construction rationale + Amendment-1
boundary in checkpoint); winner mean AP .9703 against prevalence ≈ .88.
Stage-2 winner mean AP .3865 (runner-up .3863); several dims at grid edges
(reported; grid frozen, not re-opened); clip floor INERT (min R̂ .2366 > .10,
share clipped 0). Frozen artifacts: b4_propensity_lgbm.txt (95 trees),
b4_risk_lgbm.txt (282 trees), b4_frozen_config.json.

Deliverables: src/s3a_baselines.py, outputs/checkpoints/s3a_baselines.md,
s3a_stats.json, s3a_work/* (evidence trail), outputs/models/b4_*, PROVENANCE
entry. Storage ≈ 418 MB. 2026-27 untouched. No Rule-9 conditions. Reported to
LEAD; idle pending R-AUDIT S3a / G2.

**M3 | 2026-07-16 | S3a REJECT cycle 1 resolved:** corrected the 5 hand-transcribed "mean any-311 p@250" cells in s3a_baselines.md to the s3a_stats.json values (B0 .6392, B1 .5744, B2 .6768, B3 .8304, B4 .8096; re-verified against stats.json before editing) and tightened the IPW-weight range to ~1.0–4.0 (max applied weight over positives 3.97). Documentation-only; no code change, no re-run, nothing else touched.

**M4 | 2026-07-16 | Clerical:** hyperparam_grid.md status header updated from stale "PROPOSED / not locked until G1" to "APPROVED at G1 by Ayur (2026-07-16), ratified as pre-registration by Amendment 2 (commit 9eafc29); LOCKS at G2." Header line only; no other content changed.

---

**M5 | 2026-07-17 | S3a appendix: baseline B5 (Amendment 3) complete.**

Dispatch after G2 approval; S3b remains barred and NO S3b/primary code exists.
Pre-training obligations met first: clip-floor handling stated in the
checkpoint BEFORE any training and flagged to LEAD (sample judged inseparable
— B4 stage-2's exact 60 seed-42 configs, clip_floor inert metadata; zero
projection collisions verified, so every B5 config is its B4 twin).

Execution: src/s3a_b5.py (separate file, imports the signed-off
s3a_baselines.py unmodified — disclosed choice), 5 bounded invocations +
idempotent rerun, 300 units checkpointed. Results table machine-generated
(s3a_work/b5_table.md) and appended verbatim — no hand transcription this
time; s3a_stats.json extended with additive b5_* keys only.

Results (5-fold means): AP 0.3870 / p@250 0.8136 / zero-311 p@250 0.1136 /
any-311 0.8136. B5−B4: +0.0006 / +0.0040 / +0.0032 / +0.0040 — uncorrected
twin marginally edges the corrected model on every observed-label mean; the
spec-§11 penalizes-correction-by-construction limitation operating as
predicted; recorded as-is, no claim either direction (G3/§10 adjudicates).
Winner cfg 20928 (differs from B4's 21485): num_leaves 63(int), max_depth
−1(low), lr 0.02(low), ceiling 800(int, ES 236–578), min_child 100(high),
subsample 0.7(low), colsample 0.8(int), reg_lambda 0(low), spw sqrt(int).
Artifact b5_lgbm.txt 405 trees + b5_frozen_config.json. Guards cumulative 72
passes / 42 sites (measured from guards.jsonl post-rerun; first draft
hand-estimated 62, caught and corrected pre-commit — same lesson as the M3
transcription defect), max season 2025. Storage ≈422 MB. No Rule-9 conditions. Reported to
LEAD; idle pending R-AUDIT.
