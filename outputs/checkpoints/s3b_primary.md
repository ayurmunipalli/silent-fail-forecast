# S3b checkpoint — primary two-head net (A-MODEL)

**Stage:** S3b (plan §3 step 8), dispatched after G2 approval + Amendment 3's B5
precondition (commit 4959795). **Date:** 2026-07-17. **Spec refs:** §3, §4, §8;
locked grid `hyperparam_grid.md` (Amendment 2 pre-registration; locked at G2).
**Reproduce:** `.venv/bin/python src/s3b_primary.py` — idempotent + resumable at
EPOCH granularity (per-unit checkpoints + per-epoch resume states in
`outputs/checkpoints/s3b_work/units/`; a kill loses at most one epoch of an
in-flight unit); rerun after completion recomputes nothing and prints
ALL STAGES COMPLETE (verified). **Seed 42** primary; seeds 43–46 appear ONLY in
the validation spread. Full numbers: `outputs/checkpoints/s3b_stats.json`.

**Session-loss provenance:** this stage was REGENERATED FROM SCRATCH after the
ledger-B68 removal of a killed session's unhashed partial S3b outputs. Nothing
from that session was sought, referenced, or reused; every resolved
implementation axis below is this session's independent reading of spec §3.
Input safety: `features_main.parquet` / `features_b3.parquet` sha256 are
re-computed at prep and hard-asserted against the PROVENANCE values (matched).

## Architecture and loss (spec §3 exactly; grid values only)

Shared MLP encoder (Linear → LayerNorm → ReLU → Dropout per hidden layer);
head F = Linear(width,1)+sigmoid; head p = Linear(width,1)+sigmoid;
**R = 1 − (1−p)^min(u, u\*)** (monotonicity in u structural).
**L = BCE(Y_obs, F·R) + λ·NLL(complaint counts | head p, building-season)
+ Ω₁ + Ω₂** (the two grid-§4 penalty forms). AdamW wd 1e-5, cosine LR over 200
epochs, batch 8192, ES patience 20 on fold-v TOTAL validation loss, max 200
epochs, no class reweighting — all as frozen. Search: n=60 of the 2,592-point
grid, sampling seed 42, decode/sample machinery identical to the audited S3a
scripts (hand-verified decode). No config outside the locked space was trained.

## Resolved implementation axes (spec §3 leaves these open; A1–A10 in the
`src/s3b_primary.py` header are the binding statements — summary here)

1. **NLL = zero-truncated binomial** at building-season grain. Eligible rows:
   `label_c==1 AND k_raw≥1` — "confirmed-incident exposure" read as: the
   confirmed incident creates the exposure-to-reporting; restriction to
   complaint-positive rows per grid §3 / spec §3(i); the truncation term
   (−log(1−(1−p)^u), exactly −log R) is the proper conditioning on ≥1 event.
   **42,787 eligible rows** of 43,554 label_c=1. Exposure n = u = min(u_raw,u*)
   (same capped u as the R link — one scale for head p); count k =
   min(k_raw, u), k_raw = in-season 311-UNION events (Amendment-1 boundary:
   union only; ygpa-z7cr appears solely as c7_* features). Events can exceed
   units: k capped on 14,309 / 11,298 / 10,358 eligible rows at u* = 25/50/100
   (reported, not hidden — a consequence of the frozen binomial form). log-
   binomial-coefficient INCLUDED (persisted values are the full likelihood);
   NLL term = mean over eligible rows in batch; L adds λ·mean.
2. **u_raw** = unitstotal if ≥1, else unitsres if ≥1, else 3 (multiple-dwelling
   legal floor): 1,254,587 rows unitstotal; 0 unitsres; 12,022 constant-3.
3. **Ω₁** averaged over ALL rows (its purpose is the zero-311 mass);
   p̄ = Σk/Σu over TRAIN-fold eligible rows (capped) — depends on (fold, u*),
   cached and persisted (all-dev, u*=25: p̄ = 0.5904).
4. **Ω₂** perturbed column = `viol_cnt_prior_cum` ONLY (the single family-1
   cumulative-count column in the frozen S2 list, per grid §4); δ = +0.5
   standardized; per-batch subsample = first 2048 rows of the shuffled batch;
   validation/fixed-batch Ω₂ uses all rows. Penalty forwards run in EVAL mode
   (paired passes must not differ by dropout masks; LayerNorm has no batch
   state, so this is exact); gradient flows through both.
5. **Inputs (D=100):** 37 standardized numeric + 10 binary indicators
   (dev-universe {0,1}-valued, unstandardized per the grid-§2 mask language) +
   24 numeric missingness indicators + 29 frozen-vocabulary one-hots
   (24 bldgclass_1 + 5 borough; missing categorical = all-zeros row).
   Standardization fit on TRAIN-FOLD rows only, nan-aware; NULLs → 0 AFTER
   standardization; no other imputation. Exact column list:
   `s3b_work/design_meta.json`. Note: for the earliest fold (v=2021, train
   2019–20) the t730-window and family-3 columns are ALL-NULL in training
   (availability masks; scaler guard → 0, indicator carries the signal) — the
   honest masked protocol, same situation B4 faced.
6. **Init** = PyTorch Linear defaults re-implemented with an explicit seeded
   generator (documented in-code, reproducible from the text).
7. **Validation total loss for ES** = all four terms on fold v, eval mode,
   train-fold constants.
8. **Clamps:** p, F·R ∈ [1e-7, 1−1e-7] inside logs; truncation normalizer
   ≥ 1e-12. On the fixed batch NO clamp ever binds (counts persisted = 0), so
   clamp handling cannot cause blind-re-derivation divergence.
9. **Refit** (WFF/B4 analog): all dev seasons, seed 42, E* = round(mean
   per-fold best epoch) = round(mean(2,12,10,6,18)) = **10**, cosine schedule
   still over 200 (identical LR trajectory as validation training, stopped at
   E*), no ES.
10. **Seeding:** seed drives init/shuffle/dropout/Ω₂-subsample; per-epoch seeds
    from SeedSequence([seed, fold, epoch]) so resume is bit-identical (verified
    pre-flight: unit output BIT-IDENTICAL across two forced kill/resume
    cycles, scratch dir, deleted). Config index does not enter seeding.

## Selection (pre-registered, grid §1) and winner

Mean over 5 folds of validation AP of q = F·R vs Y_obs; tie-break mean
zero-311-stratum p@250 of the F ranking; then config index.

**Winner: cfg 2009** — width 256, depth 2, dropout 0.15, λ 0.3, u* 25,
lr 1e-3, μ₁ 0, μ₂ 1.0. Mean AP(q) 0.36314; per-fold 0.2231 / 0.3186 / 0.4087 /
0.4234 / 0.4420; per-fold best epochs 2/12/10/6/18. Boundary status: λ
interior; width/dropout/lr/μ₂ high-edge, depth/u*/μ₁ low-edge (edge-heavy
winner reported as-is; the grid is locked and not re-opened).
**Near-tie disclosure:** runner-up cfg 1961 mean AP 0.36313 (margin 1.4e-5)
with HIGHER zero-311 p@250 (0.0952 vs 0.0912). The pre-registered rule invokes
the tie-break only on exact AP ties, so the AP winner stands — recorded
because a reasonable reader might have preferred the runner-up under a fuzzier
rule; the rule as frozen was applied mechanically.

**ES behavior (disclosed):** total validation loss is NLL-dominated at higher
λ, and best epochs are small (median 10). That is the pre-registered ES metric
operating as written; no post-hoc metric surgery.

## Results — winner, 5-fold validation means (machine-generated table below)

Baseline context from the audited S3a/B5 checkpoint (same folds, same metric
code): B3 AP .3823 / p@250 .8304 / zero-311 p@250 .1184 (in-sample on
2021–23); B4 .3865 / .8096 / .1104; B5 .3870 / .8136 / .1136.
**The net: AP(F·R) .3631 / p@250(F) .7488 / zero-311 p@250(F) .0912 — it
TRAILS B4/B5 on every observed-label validation mean.** Recorded as-is, no
softening: if the joint model does not beat B4 on the §10 criteria at G3, the
two-stage result ships as the paper's finding (spec §5/§10.4). Two facts
belong next to that sentence, neither of which rescues it: (i) the binding
comparison is the G3 single-shot on 2026-27, not these validation means;
(ii) every metric above is computed against Y_obs, and spec §11 names
observed-label evaluation as penalizing the correction by construction — the
same caveat applied when B5 edged B4. The weak fold is 2021 (AP .2231,
p@250 .44; earliest fold, best epoch 2, all-NULL t730/fam-3 training columns);
later folds are close to B4 (p@250 .856/.876/.848 vs B4 .848/.872/.864; AP
.4234/.4420 vs .4395/.4543). No claim either direction; G3 adjudicates.

## 5-seed VALIDATION spread (spec §8, Rule 10; hyperparams fixed)

Seeds 42–46, same folds: mean AP(q) range 0.3512–0.3653 (std 0.0056);
zero-311 p@250(F) range 0.0792–0.0912 (std 0.0041). Seed-42 rows are the
search units themselves (bit-identical rerun; reuse disclosed). Full per-seed
table below and in the stats json. Validation-based only — no test contact.

## Freeze-candidate bundle

- `outputs/models/s3b_primary_seed42.pt` — state_dict (93,186 params) +
  config + all-dev scaler + design columns.
  sha256 `bb4016b836d148766f95d17e45bbb127b874e22f3e5d33b43e39a9c8b5c27126`.
- `outputs/models/s3b_frozen_config.json` — architecture/loss/config/selection
  + BOTH frames' recipe hashes (features_main 477d3079…, features_b3
  09f8e94d…). sha256 `904356165858091f3d05c57fb2b0593c0efe9ff0b2070412ded23300b0e5b2e0`.
- Full-dev F/p scores persisted (`s3b_work/final_scores.npz`) for the reload
  check and later G3 tooling.
- **Reload verification (fresh subprocess): BIT-EXACT** — max abs diff 0.0 on
  full-dev F and p and on every fixed-batch per-term value
  (`s3b_work/reload_verification.json`; torch 2.13.0, 3 threads, CPU).

## Fixed batch for the blind loss re-derivation (`s3b_work/fixed_batch/`)

Deterministic construction (documented in `batch_construction.md`): first 4096
all-dev rows ∪ first 4096 NLL-eligible rows, frame order, duplicate keys
dropped → **8,125 rows, 4,096 eligible**. Persisted: per-row y, u_raw, k_raw,
u_capped, k_capped, eligibility, standardized float64 design matrix, all
constants (λ, u*, μ₁, μ₂, p̄, δ, clamp values), and — at t0 (post-init,
pre-step), t1 (after epoch 1), tE (final, E*=10) of the seed-42 refit —
per-row F, p, R, q, F_pert and per-term float64 values with the NLL
decomposed into its four pieces (comb, k·log p, (u−k)·log(1−p), −log R, plus
the no-truncation variant), so any divergence in R-AUDIT's independent
implementation is isolable to a specific term and a specific reading.
tE totals: BCE 1.46916…, NLL mean 4.94773…, Ω₁ raw 0.58760…, Ω₂ raw 4.77e-7,
total 2.95348… (full precision in `fixed_batch/tE_final.json`; the fixed batch
is a probe batch — ~50% positives by construction — not a metric).

## Test-season sanctity and operations

- Season 2026-27 structurally absent (both frames end at start-year 2025,
  asserted); `assert_no_test_contact()` at every load, fold build, scaler fit,
  refit, and scoring pass. Deterministic guard facts: **15 distinct call
  sites, max season ever touched = 2025, zero ≥2026 firings ever** (a guard
  failure is a hard stop, not a log line). The raw pass count in
  `s3b_work/guards.jsonl` (234 at reconciliation, 2026-07-17) is an
  APPEND-ONLY CUMULATIVE snapshot, not a stable stage statistic: the
  fixed-batch capture path re-asserts (and appends) on every invocation,
  including fully-complete idempotent reruns, so the count drifts upward by a
  few lines per rerun — same B5-lineage caveat (M5). [Reconciled after
  R-AUDIT S3b reject 1: an earlier draft headlined the snapshot value 233,
  which a post-stats verification rerun had already advanced to 234.]
- Execution: ~29 bounded foreground invocations (≤9 min each), 3 worker
  processes, torch pinned to 3 threads everywhere for determinism; 321
  training units total (300 search + 20 spread + 1 refit), all per-unit
  checkpointed, zero unit losses, zero error files, zero leftover resume
  files. Non-finite loss anywhere is a hard AssertionError (none occurred).
- torch 2.13.0 was found already installed in `.venv` (presumably the killed
  B64 session's setup; no install performed this session); versions pinned in
  the stats json (numpy 2.5.1, pandas 3.0.3, sklearn 1.9.0, python 3.12.13).
- Storage: repo data+outputs+imports ≈ 928 MB ≤ 2 GB. `s3b_work/design.npy`
  (483 MB) is a regenerable cache (deterministic from hash-asserted inputs);
  kept for R-AUDIT convenience, deletable at freeze.
- **No Rule-9 conditions. No fabrication events. Season 2026-27 untouched.**

## Deviations & disclosures (consolidated)

1. All resolved axes 1–10 above (the killed session's readings were never
   consulted; these are independent).
2. Near-tie winner (margin 1.4e-5; runner-up better on the tie-break metric;
   frozen rule applied as written).
3. Net trails B4/B5 on observed-label validation means — reported verbatim,
   G3 is the binding test.
4. Seed-42 spread rows reused from search units (deterministic identity).
5. Ω₂ penalty forwards in eval mode (dropout-noise removal; disclosed above).
6. Fold-2021 all-NULL masked training columns (structural availability, not
   missingness handling error).
7. ES watches fold v per the frozen grid text (same disclosure lineage as S3a).

→ R-AUDIT S3b, including the blind likelihood re-derivation (protocol: derive
from spec §3 BEFORE reading `src/s3b_primary.py`; the fixed-batch kit is
sufficient without the code).

---

# S3b results table (machine-generated — no hand transcription)

| Metric (5-fold val means, winner cfg 2009, seed 42) | value |
|---|---|
| mean_ap_q | 0.3631 |
| mean_p@250_q | 0.7496 |
| mean_p@250_F | 0.7488 |
| mean_zero311_p@250_F | 0.0912 |
| mean_zero311_p@250_q | 0.0920 |
| mean_any311_p@250_F | 0.7576 |

| Seed | mean AP (F·R) | mean p@250 (F) | mean zero-311 p@250 (F) |
|---|---|---|---|
| 42 | 0.3631 | 0.7488 | 0.0912 |
| 43 | 0.3653 | 0.7784 | 0.0792 |
| 44 | 0.3512 | 0.7200 | 0.0824 |
| 45 | 0.3566 | 0.7360 | 0.0816 |
| 46 | 0.3527 | 0.7456 | 0.0824 |

Per-fold winner AP (F·R), v=2021..2025: 0.2231 / 0.3186 / 0.4087 / 0.4234 / 0.4420
