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
