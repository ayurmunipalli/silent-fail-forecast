# R-PILOT result packet — silent-fail-forecast — for Ayur

**RETROSPECTIVE AND NON-BLIND** (Amendment 5(iii), attached to every number
below): the project's conception and the frozen spec postdate season
2025-26; nothing here has prospective standing or carries any weight at G3.
The frozen G3 pre-registration — §10 and its margins, the frozen bundle,
the Amendment-4 freeze entry, the 2026-27 bright line — is untouched
(byte-identical re-hash at RP2 post-audit). Compiled by LEAD from
signed-off sources only: `rp1_pilot.md`, `rp2_eval.md`,
`rp1_work/rp1_stats.json`, `rp2_work/single_shot_2025/rp2_stats.json`,
`r-audit.md` RP0–RP2 sections, PROVENANCE RP1/RP2 entries, ledger
B95–B118. No number is re-derived here; no recommendation is made. The
§11 caveat applies throughout: observed-label evaluation penalizes the
censoring correction by construction.

## 1. What ran (Amendment 5, commits 54bf690 → c8f10d9 → d273bd5)

- **RP0** (r-audit): temporal-leakage review at the pilot cutoff Oct 1,
  2025 — sign-off; frames-reused clause verified structurally; binding
  code assertions D1–D11 enumerated before any pilot code existed.
- **RP1** (a-model): selection/training re-executed at the pilot cutoff —
  locked grid (n=60, seed 42), pre-registered rules, folds v ∈ 2021…2024,
  Amendment-4(i) axes unchanged; joint + B4/B5 twins re-selected, B0–B2
  recomputed; frozen cfg-2009 build artifact not reused per Amendment
  5(i). R-AUDIT sign-off after 1 doc-only reject cycle (two prose
  runner-up margins; corrected with bracketed audit notes).
- **RP2** (a-model): the one authorized season-2025-26 contact, under a
  LEAD-imposed heightened protocol — script rehearsed on season 2024 and
  R-AUDIT-pre-audited before the shot; spend-once sentinel written before
  compute. **Executed exactly once, 2026-07-21T06:52:14, exit 0.**
  R-AUDIT post-audit: sign-off, zero defects (every number re-derived to
  0.0 from the persisted predictions; all six sign-test cells reconciled
  independently from the raw stores).

## 2. RP1 — pilot re-selection (validation, folds 2021-22…2024-25)

| Model | winner | mean val AP | notes |
|---|---|---|---|
| Joint two-head | **cfg 2009 — same index as build** | .3434 | E*=8; shared-fold units reproduce build to 0.00e+00 (determinism identity); runner-up 1961 (margin 1.7e-3, higher zero-311 — same pattern as build) |
| B4 (IPW two-stage) | s1 cfg 5411 (= build); s2 cfg 13411 | .3695 | runner-up = build winner 21485, margin 3.3e-5 (near-tie) |
| B5 (uncorrected twin) | cfg 13411 | .3701 | runner-up = build winner 20928, margin 1.3e-4 (near-tie, higher tie-break; frozen exact-tie rule correctly not invoked) |

B3 folds-≤2024 row: .3694/.8260/.1170 (in-sample v=2021–23 caveat).
5-seed validation spread (joint): AP .3283–.3465, std .0072. The joint
pilot model trails B4/B5 on every validation mean — same direction as the
build phase.

## 3. RP2 — the single shot (season 2025-26; observed-label; recorded as-is)

Eval universe 181,863 building-seasons, 8,897 whitelist positives,
zero-311 stratum 120,631 (§6 definition, set-identity verified).

| Model | AP | p@250 | zero-311 p@250 |
|---|---|---|---|
| B0 | .2155 | .7360 | .0280 |
| B1 | .2784 | .6320 | .0520 |
| B2 | .2734 | .8000 | .0480 |
| **B3 (as-is, the incumbent)** | **.4339** | **.8480** | **.1240** |
| **B4 pilot** | **.4533** | **.8560** | **.1600** |
| **B5 pilot** | **.4528** | **.8640** | **.1520** |
| **Joint pilot (q = F·R)** | **.4408** | **.8280** | **.1160** |
| Joint pilot (F ranking) | .4406 | .8280 | .1160 |

**Amendment-5(ii) stratum comparison, as-is:** joint_F .1160 vs B3 .1240;
B4 .1600; B5 .1520.

**Criterion-3-style (frozen grid-§7 statistic; realized n reported;
zeros dropped counted):** HSP waterfall 197 lots → 1,488 in-season
class-C events → 104 silent (dual 311+ygpa screen, W=30) across **n = 35
buildings**.

| Screen | Model | n | T = median Δ | one-sided p | reject @ .05 |
|---|---|---|---|---|---|
| dual | joint_F | 35 | −0.0022 | 0.9996 | False |
| dual | B4 | 35 | −0.0004 | 0.9552 | False |
| dual | B5 | 35 | −0.0004 | 0.9552 | False |
| 311-only | joint_F | 36 | −0.0023 | 0.9997 | False |
| 311-only | B4 | 36 | −0.0003 | 0.9337 | False |
| 311-only | B5 | 36 | −0.0003 | 0.9337 | False |

## 4. Directional summary (facts only, both directions, per Amendment 5(iii))

- The joint pilot model **beats B3 on overall AP** (.4408 vs .4339) and
  **trails B3 on the zero-311-stratum p@250** (.1160 vs .1240) — the
  stratum the correction targets.
- **B4 and B5 beat both** B3 and the joint model on AP and on the stratum.
- **No model rejects** in any criterion-3-style cell (all T < 0: every
  model's median silent-HSP rank percentile sits below B3's).
- B4-vs-B5 (the Amendment-3 attribution pair): AP .4533 vs .4528; stratum
  .1600 vs .1520 (as-is; no claim).
- Contextual anchor from the spec (not a criterion here): §10.1's G3
  margin is stratum ≥ 1.35× B3; the pilot joint/B3 stratum ratio is 0.94
  (.1160/.1240). §10 is evaluated only at G3, on 2026-27, against the
  frozen bundle — not this pilot artifact.

## 5. Integrity and disclosures

- **One-shot discipline:** sentinel-first semantics; single ~8 s
  execution; no recompute traces; rehearsal outputs predate the shot.
- **Sanctity:** 2026-27 untouched across the entire pilot (RP1 guards
  44 sites / RP2 guards 6 sites; zero ≥2026 firings anywhere; frozen G3
  scoring set byte-identical).
- **Blind-status labeling:** RETROSPECTIVE AND NON-BLIND on every
  artifact, table, config, and all 181,863 parquet rows.
- **Operational episodes (zero numeric impact, all audited):** (i) macOS
  duplicate-OpenMP clash — torch and lightgbm cannot co-execute in one
  process; RP1 fixed import order + worker pool (determinism identity
  0.00e+00 proves invariance), RP2 used a two-process design (pre-audit
  reproduced scores to 1.19e-07); (ii) the s3b-mirror pool's bare-except
  had silently swallowed worker deaths — audited: no build-phase impact
  (300/300 + 20/20 complete); (iii) LATENT, disclosure-only: committed
  `rp1_pilot.py` would segfault on its GBM stages on a from-scratch rerun
  (import order); RP1's committed results are unaffected; no mid-pilot
  patch (LEAD ruling, B111); (iv) harness background-task notification
  losses required LEAD ground-state verification twice (B102, B115) —
  disk state, not agent reports, was the resolution authority both times.
- **Audit trail:** RP0 sign-off; RP1 sign-off after 1 doc-only reject;
  RP2 pre + post sign-offs, zero defects. Full evidence in
  `reports/agent_logs/r-audit.md`.

## 6. Pre-commitments honored (Amendment 5(iii))

Disclosed in full, both directions, no selective emphasis; labeled
retrospective/non-blind everywhere; G3 pre-registration untouched.
Interpretation of what the pilot means — including what, if anything, it
suggests about the two-stage-vs-joint question ahead of G3 — is Ayur's
alone. Per §10.4, the G3 fallback structure is already pre-registered and
is not altered by this pilot.
