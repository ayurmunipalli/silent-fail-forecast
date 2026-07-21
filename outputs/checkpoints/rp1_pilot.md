# RP1 checkpoint — R-PILOT re-selection/re-training at pilot cutoff Oct 1, 2025 (A-MODEL)

**RETROSPECTIVE AND NON-BLIND** (model_spec.md Amendment 5(iii)): the project's
conception and the frozen spec postdate season 2025-26; nothing here has
prospective standing, carries any weight at G3, or modifies anything in the
frozen G3 pre-registration. This label is stamped in every RP1 artifact,
per-unit checkpoint record, config, table, and stats file (D8).

**Stage:** RP1 (Amendment 5(i)). **Date:** 2026-07-21. **Spec refs:** §3, §5,
§8, Amendment 4(i) (frozen NLL axes A1–A10), Amendment 5; locked grid
`hyperparam_grid.md`; RP0 sign-off assertions D1–D8 (r-audit.md) binding.
**Reproduce:** `.venv/bin/python src/rp1_pilot.py` — idempotent + resumable
(net units at EPOCH granularity, the S3b pattern; per-unit jsons under
`outputs/checkpoints/rp1_work/`); rerun after completion recomputes nothing and
prints ALL STAGES COMPLETE (verified twice). **Seed 42**; seeds 43–46 only in
the validation spread. Full numbers: `outputs/checkpoints/rp1_work/rp1_stats.json`.

## Protocol (mechanical re-execution, nothing re-interpreted)

Pilot cutoff Oct 1, 2025. Forward-chaining folds **v ∈ {2021, 2022, 2023,
2024}** only, train = seasons 2019…(v−1) (dev floor 2019); dev universe
2019–2024, `dev.season.max()==2024` asserted, season 2025 never enters any RP1
dev structure (D2/D3). Hash-pinned S2 frames reused, sha256 asserted at load
(D1); no new pull, no frame regeneration. Same locked grids, same n=60 seed-42
samples (identical decode/sample machinery ⇒ identical 60 config indices as
build — verified), same pre-registered selection rules, same Amendment-4(i)
axes A1–A10, ES patience 20 on fold-v total val loss, refit-E* analog on all
pilot dev (P4). Machinery imported from the audited `s3a_baselines.py` /
`s3b_primary.py` wherever importable; season-hard-coded orchestration
line-mirrored with pilot constants (each mirror labeled with source lines in
`src/rp1_pilot.py`; pilot-specific mechanical resolutions P1–P7 in its header).

**Test-season sanctity (D4):** the ≥2026 hard-stop guard pattern unchanged;
guard events in `rp1_work/guards.jsonl`. Deterministic facts: **44 distinct
call sites, max season ever touched = 2025 (full-frame load/assert sites only;
all dev-side sites ≤ 2024), zero ≥2026 firings ever.** Raw pass count (390) is
an append-only cumulative snapshot, not a stage statistic (M5/M7 lineage).
**D7:** preflight sha256 snapshot of all 10 pre-existing `outputs/models/` +
`imports/` artifacts re-verified UNCHANGED at report time; all pilot artifacts
live in the distinct `rpilot_*` namespace.

## Results (machine-generated table below, pasted verbatim from rp1_work/rp1_table.md)

**RETROSPECTIVE AND NON-BLIND** — RP1 pilot validation table (machine-generated — no hand transcription). Means over the 4 pilot folds v = 2021..2024.

| Model | mean AP | mean p@250 | mean zero-311 p@250 | mean any-311 p@250 |
|---|---|---|---|---|
| B0 | 0.1476 | 0.6210 | 0.0180 | 0.6200 |
| B1 | 0.2104 | 0.5550 | 0.0410 | 0.5600 |
| B2 | 0.1913 | 0.6360 | 0.0390 | 0.6430 |
| B3 | 0.3694 | 0.8260 | 0.1170 | 0.8260 |
| B4 | 0.3695 | 0.8050 | 0.0980 | 0.8050 |
| B5 | 0.3701 | 0.8020 | 0.0850 | 0.8020 |
| joint (q=F*R) | 0.3434 | 0.7250 | 0.0830 | 0.7390 |
| joint (F ranking) | 0.3433 | 0.7240 | 0.0830 | 0.7350 |

AP for the joint rows: q=F·R vs Y_obs (selection metric) and the F ranking respectively; p@250 columns use each row's own score.
B3 row: frozen booster, folds ≤2024 only; v∈{2021,2022,2023} in-sample (WFF training seasons); no season-2025 row scored in RP1.

| Seed | mean AP (F·R) | mean p@250 (F) | mean zero-311 p@250 (F) |
|---|---|---|---|
| 42 | 0.3434 | 0.7240 | 0.0830 |
| 43 | 0.3465 | 0.7660 | 0.0740 |
| 44 | 0.3283 | 0.6880 | 0.0770 |
| 45 | 0.3347 | 0.7100 | 0.0790 |
| 46 | 0.3299 | 0.7200 | 0.0770 |

Per-fold joint winner AP (F·R), v=2021..2024: 0.2231 / 0.3186 / 0.4087 / 0.4234
Per-fold B4 AP: 0.2849 / 0.3374 / 0.4169 / 0.4390
Per-fold B5 AP: 0.2846 / 0.3375 / 0.4187 / 0.4398

Every number above is an observed-label (Y_obs) validation metric; the spec-§11
caveat (observed-label evaluation penalizes the correction by construction)
attaches to each. Recorded as-is; RP2's single 2025-26 shot is the pilot's
evaluation event; no claim either direction here.

## Winners (selection rules re-executed mechanically over the 4 pilot folds)

- **Joint: cfg 2009** (w256 / d2 / dropout .15 / λ .3 / u* 25 / lr 1e-3 / μ₁ 0 /
  μ₂ 1.0) — the SAME config index as the build-phase winner. Mean AP(q)
  0.34344; per-fold 0.2231/0.3186/0.4087/0.4234; best epochs 2/12/10/6;
  boundary status unchanged from build (edge-heavy, grid locked, not
  re-opened). Runner-up cfg 1961, mean AP 0.34176 (margin 1.7e-3 — not a
  near-tie) with HIGHER zero-311 p@250 (0.088 vs 0.083); the frozen rule
  invokes the tie-break on exact AP ties only, disclosed as in build (M6).
  **E\* = round(mean(2,12,10,6)) = 8**; all-pilot-dev refit, seed 42, cosine
  over 200 stopped at 8, no ES.
- **B4 stage 1: cfg 5411** (same index as build) — mean AP 0.96846; runner-up
  cfg 1080 at 0.96844 (**near-tie, margin 1.9e-5**). [Margin corrected from
  3.2e-5 after R-AUDIT RP1 reject 1 — traces to rp1_stats.json:
  0.9684620257 − 0.9684428770 = 1.9149e-5.]
- **B4 stage 2: cfg 13411** (num_leaves 31, max_depth 10, lr 0.02,
  n_estimators 400, min_child 50, subsample 0.7, colsample 0.8, reg_lambda
  5.0, spw 1, clip_floor 0.05) — mean AP 0.36953. Runner-up = **cfg 21485,
  the build-phase winner**, at 0.36949 (**near-tie, margin 3.3e-5**;
  tie-break metrics 0.098 vs 0.097 recorded for both). The 4-fold selection
  flipped this near-tie relative to build's 5-fold one.
- **B5: cfg 13411** — the SAME operative config as B4 stage 2 this time —
  mean AP 0.37013. Runner-up = **cfg 20928, the build-phase winner**, at
  0.36999 (**near-tie, margin 1.3e-4**) with higher zero-311 p@250 (0.101 vs
  0.085); AP rule applied as frozen. [Margin corrected from 1.4e-4 after
  R-AUDIT RP1 reject 1 — traces to rp1_stats.json: 0.3701259218 −
  0.3699977400 = 1.282e-4.] clip_floor inert metadata; zero
  projection collisions re-verified.
- Refit artifacts (all-pilot-dev, fixed n_estimators = round(mean fold
  best_iter), no ES): B4 propensity 90 trees, B4 risk 332 trees, B5 307 trees.

## Determinism identity (disclosed)

The pilot's per-fold joint units for v ≤ 2024 reproduce the build-phase
per-fold results exactly (same APs to 4 d.p., same best epochs): with
train-fold-only scalers, identical design typing (100 columns, P2), and A10
seeding (SeedSequence([seed, fold, epoch]) — no dependence on the dev
universe), the shared folds are the same computation. The pilot's substantive
delta is exactly Amendment 5's intent: fold v=2025 is REMOVED from selection/
aggregation (and E*), nothing else. The same identity holds for B1/B3 fold
scores; B0/B2 (and all p@k under heavy score ties) shift in the 3rd decimal
because the seed-42 tie-key permutation is drawn over the pilot universe
(1,084,746 rows) rather than the build universe — AP is tie-key-free and
unaffected.

## Deviations & operational notes

1. **P1–P7** pilot-specific mechanical resolutions (script header): full-frame
   read materializes season-2025 rows ONLY for the D1 whole-file hash + D4
   max-season assertions, dropped on the next statement (D2 asserted); design
   typing re-derived on the pilot universe (came out identical: 100 cols); B2
   lookback cap 2023; E*/refit on pilot dev; no fixed-batch kit at RP1 (none
   mandated; R-AUDIT re-audits the script per RP0(d)); B3 not retrained, not
   selected, no 2025 row scored.
2. **Worker-pool change from the s3b mirror (operational, no numerics):**
   static round-robin shards + hard child-exit-code checks replace the
   multiprocessing Queue. Reason: under the harness background-task context,
   spawn workers were dying by SIGSEGV and the queue mirror's bare
   `except: return` swallowed it (0 units, clean exit, ~35 loop invocations).
   Root cause isolated by controlled A/B: **duplicate OpenMP runtime** —
   rp1_pilot imports lightgbm (audited GBM machinery) at module top, so spawn
   children re-executing it as `__mp_main__` loaded lightgbm's libomp before
   torch's and segfaulted at the first heavy torch op; build-phase
   s3b_primary.py imports no lightgbm and never faced this. Fix: order-critical
   `import torch` before lightgbm (documented in-code). Crashed children died
   pre-training — zero files written by any of them (units dir empty
   throughout; verified), so no computed number was ever affected. Unit
   training code untouched; unit outputs are seed-determined and
   shard-assignment-free (A10).
3. Background loop invocations were externally killed twice mid-run (harness
   task-reaping mechanic); epoch-level resume continued bit-identically
   (0 lost units, 0 error files, 0 leftover resume files at completion:
   257 units = 240 search + 16 spread + 1 refit).
4. Near-ties as disclosed above; in two of them the build-phase winner is the
   pilot runner-up (B4 stage 2, B5) — the pre-registered AP rule was applied
   mechanically, exact-tie rule never fired.
5. Guard raw pass count = append-only cumulative snapshot (M5/M7 lineage);
   headline guard facts are deterministic and asserted from guards.jsonl.
6. `rp1_work/design.npy` (~434 MB) is a regenerable cache (deterministic from
   hash-asserted inputs), kept for R-AUDIT convenience, deletable.

## Artifacts (rpilot_* namespace, D7; sha256s in rp1_stats.json)

`outputs/models/`: `rpilot_joint_seed42.pt` (E*=8 refit state + config +
all-pilot scaler + design columns), `rpilot_joint_config.json`,
`rpilot_b4_propensity_lgbm.txt`, `rpilot_b4_risk_lgbm.txt`,
`rpilot_b4_config.json`, `rpilot_b5_lgbm.txt`, `rpilot_b5_config.json`.
Frozen build-phase bundle and all committed baselines untouched (D7 re-verify:
10/10 unchanged). Full-pilot-dev F/p scores persisted
(`rp1_work/pilot_dev_scores.npz`) for RP2 tooling.

**Storage:** data+outputs+imports = 1.443 GB ≤ 2 GB. **Season 2025:** never in
any fold/scaler/target/design row (D2). **Season 2026-27:** untouched, zero
guard firings. **No Rule-9 conditions. No fabrication events.** → R-AUDIT RP1
(script re-audit per RP0(d)).
