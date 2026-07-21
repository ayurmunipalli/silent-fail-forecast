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

---

**M6 | 2026-07-17 | Stage S3b: primary two-head net complete.**

Dispatch: plan §3 step 8 after G2 + Amendment-3 B5 precondition (HEAD 1d2f3b4).
RESUME-AFTER-SESSION-LOSS context honored: regenerated from scratch per ledger
B68; the killed session's work was never sought, referenced, or reused; frame
hashes re-asserted in code against PROVENANCE (matched).

Read before acting: a-model.md (binding), CLAUDE.md, model_spec.md (frozen +
Amendments 1–3), plan.md, my prior log M1–M5, locked hyperparam_grid.md, S2
feature inventory, audited s3a_baselines.py (machinery precedent).

Execution: src/s3b_primary.py — spec-§3 architecture exactly, locked grid only
(n=60/2,592, sampling seed 42, S3a decode machinery). Open spec-§3 axes
resolved independently and disclosed (A1–A10 in script header + checkpoint):
headline = zero-truncated binomial NLL on label_c=1 ∧ k≥1 rows (42,787),
exposure min(u,u*) shared with the R link, k capped at u (counts reported);
u fallback unitstotal→unitsres→3; Ω₂ column = viol_cnt_prior_cum only, eval-
mode penalty forwards; D=100 design (frozen vocabularies, nan-aware fold
scalers, no imputation beyond post-standardization 0 + indicators).
Pre-flight on scratch dir: double kill/resume BIT-IDENTICAL; Ω₂ nonzero at
init. ~29 bounded invocations, 3 workers/3 torch threads, 321 units, zero
losses; idempotent rerun clean.

Results: winner cfg 2009 (w256/d2/do.15/λ.3/u*25/lr1e-3/μ₁0/μ₂1.0), mean val
AP(F·R) 0.3631 / p@250(F) 0.7488 / zero-311 p@250(F) 0.0912 — TRAILS B4
(.3865/.8096/.1104) and B5 on every observed-label validation mean; recorded
verbatim with the §11 penalizes-correction caveat noted both ways; G3
adjudicates §10.4. Near-tie runner-up (Δ AP 1.4e-5, better tie-break metric)
disclosed; frozen rule applied mechanically. 5-seed spread (42–46, val-based):
AP range .3512–.3653, std .0056. Freeze candidate: s3b_primary_seed42.pt
(93,186 params, E*=10 all-dev refit) + frozen config with both frames' recipe
hashes; fresh-subprocess reload BIT-EXACT (0.0 everywhere). Blind-audit kit:
deterministic 8,125-row fixed batch, per-term float64 at t0/t1/tE, NLL
decomposed into 4 pieces, per-row F/p/R/q/F_pert, all constants; no clamp
binds on the batch. Guards: 15 distinct sites / max season 2025 / zero ≥2026
firings (raw pass count is an append-only cumulative snapshot — see M7).
Storage ≈928 MB. No Rule-9 conditions. Reported to LEAD; idle pending R-AUDIT
S3b blind re-derivation.

**M7 | 2026-07-17 | S3b REJECT cycle 1 resolved (doc-only, as authorized):**
R-AUDIT found the headlined guard pass count 233 non-reconciling with
guards.jsonl (234): fold_tensors(FOLD_ALL) in the fixed-batch capture path
appends a guard line on EVERY invocation including complete idempotent
reruns, so the post-completion verification rerun advanced the count after
stats were written — the raw count is an append-only cumulative, and the B5
62→72 lesson (M5) was not carried into S3b's claims. Fix per LEAD's
authorization: s3b_stats.json guard_assertions restructured to headline the
deterministic facts (15 distinct sites, max season 2025, zero ≥2026 firings)
with the raw count relabeled an append-only cumulative snapshot (234 at
reconciliation) and the drift mechanism stated; matching corrections in
s3b_primary.md and the M6 line above. Deterministic facts re-verified from
guards.jsonl in the reconciliation script (sites and max-season asserted
equal). NO code change (R-AUDIT's guard-idempotency hygiene declined by LEAD
— audited surface unchanged), no re-run, no retraining, nothing else touched.

---

**M8 | 2026-07-21 | Stage RP1 (R-PILOT, Amendment 5(i)): re-selection/re-training at pilot cutoff Oct 1, 2025 — complete. RETROSPECTIVE AND NON-BLIND.**

Dispatch: LEAD, RP1, after RP0 sign-off (assertions D1–D8 binding). Read before
acting: CLAUDE.md, model_spec.md through Amendment 5, plan.md, locked
hyperparam_grid.md, s3a_baselines.md, s3b_primary.md, r-audit.md RP0 section,
this log. Everything mechanical: same locked grids, same n=60 seed-42 samples
(verified identical config indices as build), same pre-registered selection
rules, Amendment-4(i) axes A1–A10 verbatim, folds v ∈ {2021..2024} only, dev
2019–2024 (D2 asserted; season 2025 never in any dev structure — its rows are
materialized solely by the whole-file D1-hash/D4-max-season assertions at load
and dropped on the next statement).

Script: src/rp1_pilot.py — imports the audited S3a/S3b machinery (metrics,
grid decode/sample, lgb params, loss_terms/build_model/eval_pass/seeding);
line-mirrors only season-hard-coded orchestration with pilot constants
(labeled MIRROR with source lines; pilot resolutions P1–P7 in header).
Idempotent, epoch-resumable, torch 3 threads, D7 preflight sha256 snapshot of
all pre-existing models/imports re-verified unchanged at report; D8 label
stamped everywhere.

Results (4-fold means; machine table in rp1_work/rp1_table.md, pasted verbatim
into outputs/checkpoints/rp1_pilot.md; full numbers rp1_work/rp1_stats.json):
B0 .1476/.6210/.0180 · B1 .2104/.5550/.0410 · B2 .1913/.6360/.0390 ·
B3 .3694/.8260/.1170 (in-sample v=2021–23; no 2025 row scored, P7) ·
B4 .3695/.8050/.0980 · B5 .3701/.8020/.0850 · joint(q) .3434/.7250/.0830.
Joint trails B4/B5 on every observed-label mean again (§11 caveat attached;
RP2 adjudicates the pilot question). Winners: joint cfg 2009 (same index as
build; per-fold APs/best-epochs for shared folds reproduce build exactly —
determinism identity disclosed in checkpoint; E*=8); B4 s1 cfg 5411 (same as
build; runner-up cfg 1080, margin 1.9e-5 [corrected from 3.2e-5 after R-AUDIT
RP1 reject 1 — traces to rp1_stats.json]); B4 s2 cfg 13411 (runner-up = build
winner 21485, margin 3.3e-5 near-tie); B5 cfg 13411 (runner-up = build winner
20928, margin 1.3e-4 near-tie [corrected from 1.4e-4 after R-AUDIT RP1 reject
1 — traces to rp1_stats.json]; same operative config as B4 s2). Joint runner-up 1961
margin 1.7e-3, higher zero-311 tie-break metric (rule fired on exact ties
only, as frozen). 5-seed spread (42–46, pilot folds): AP .3283–.3465
(std .0072), zero-311 p@250 .074–.083 (std .0030). Artifacts: rpilot_joint_
seed42.pt + config, rpilot_b4_* (90/332 trees), rpilot_b5_* (307 trees).

Incidents (all operational, none touching numerics; full detail in checkpoint
deviations): (i) Monitor-tool misfire logged by LEAD as harness mechanic
(ledger B102); (ii) background loop externally detached/killed by the harness
3× — mid-run Rule-1 state report delivered to LEAD, training halted on LEAD's
freeze, resumed on authorization; epoch-level resume clean (257/257 units,
zero losses/errors/leftovers); (iii) spawn workers segfaulted (SIGSEGV) via
duplicate OpenMP runtime — lightgbm's libomp loading before torch's in
children re-executing rp1_pilot as __mp_main__ (s3b never faced this: no
lightgbm import); isolated by controlled A/B; fixed by order-critical torch-
first import + replacing the queue mirror with static shards + hard child
exit-code checks (the old bare except had swallowed the crashes silently).
Crashed children died pre-training; zero files ever written by them.
(iv) B0/B2 3rd-decimal shifts vs build = tie-key permutation over the pilot
universe (AP tie-key-free, unaffected). Guards: 44 distinct sites, max season
touched 2025 (load sites only), zero ≥2026 firings (raw 390 = append-only
snapshot). Storage 1.443 GB ≤ 2 GB. No Rule-9 conditions. No commits (LEAD's).
Reported to LEAD; idle pending R-AUDIT RP1 / RP2 dispatch.
