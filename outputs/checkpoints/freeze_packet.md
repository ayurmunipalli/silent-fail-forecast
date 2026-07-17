# FREEZE gate packet — silent-fail-forecast — for Ayur's adjudication

Compiled by LEAD from signed-off sources only (plan.md §3 step 9; spec §4).
Cited documents: `outputs/checkpoints/s3b_primary.md` (signed-off), `s3b_stats.json`,
`hyperparam_grid.md` (locked), `s3a_baselines.md` (signed-off incl. B5),
`reports/agent_logs/r-audit.md` (S3b steps 1–3 + re-audit), `data/PROVENANCE.md`,
ledger B64–B85. No number below is re-derived; no recommendation is made.

## 1. What is being frozen

- **Artifact:** `outputs/models/s3b_primary_seed42.pt` — spec-§3 two-head net,
  winner cfg 2009 (width 256 / depth 2 / dropout .15 / λ .3 / u* 25 / lr 1e-3 /
  μ₁ 0 / μ₂ 1.0), 93,186 params, E*=10 all-dev refit, seed 42.
  sha256 `bb4016b8…` (full value in PROVENANCE).
- **Config + recipe binding:** `outputs/models/s3b_frozen_config.json`
  (sha256 `90435616…`) pins both feature-frame recipe hashes
  (features_main `477d3079…`, features_b3 `09f8e94d…`).
- **Reload verification:** fresh-subprocess reload BIT-EXACT (0.0 max abs diff on
  full-dev F/p and every fixed-batch term); independently reproduced by R-AUDIT
  via a numpy forward pass from the state_dict (≤2.2e-16). [s3b_primary.md §reload;
  r-audit.md step 3(f)]
- **Committed + pushed:** 054f136 (2026-07-17) — the external timestamp
  predates Oct 1, 2026 by ~2.5 months.

## 2. Selection provenance

Locked grid only (n=60 of 2,592, sampling seed 42; decode verified against S3a
machinery by R-AUDIT). Pre-registered selection rule applied mechanically: mean
forward-chaining validation AP of F·R; winner re-derived independently by R-AUDIT
(.3631432); near-tie runner-up cfg 1961 (Δ AP 1.416e-5, better tie-break metric)
disclosed — tie-break correctly NOT invoked (rule fires on exact ties only).
[s3b_primary.md; r-audit.md step 3(c,d)]

## 3. Validation results, recorded as-is (observed-label; spec §11 caveat applies)

| Model | mean val AP | p@250 | zero-311 p@250 |
|---|---|---|---|
| B3 (frozen WFF; in-sample caveat, G2 packet) | .3823 | .8304 | .1184 |
| B4 (two-stage IPW GBM) | .3865 | .8096 | .1104 |
| B5 (uncorrected retrained twin) | .3870 | .8136 | .1136 |
| **S3b joint two-head (freeze candidate)** | **.3631** | **.7488** | **.0912** |

The joint model TRAILS B4/B5 on every observed-label validation mean. Recorded
with no directional claim: spec §11 names observed-label evaluation as penalizing
correction by construction; the binding §10 comparison is the single G3 event vs
B3; §10 criterion 4 pre-registers that if the joint model does not beat B4 on
criteria 1–3 at G3, the two-stage result ships as the finding. Weak fold is
2021-22 (earliest; all-NULL masked fam-3/t730 training columns). 5-seed
VALIDATION spread (seeds 42–46, hyperparams fixed): AP .3512–.3653, std .0056.
[s3b_primary.md; s3b_stats.json]

## 4. Blind loss re-derivation (plan §3 step 8 protocol) — outcome

- Step 1 (pre-committed 1d2f3b4, BEFORE any S3b code): independent spec-§3
  likelihood implementation, sha256 `52f678da…`.
- Step 2 (spec + fixed-batch kit only): every spec-pinned term reproduced to
  machine tolerance (≤1.8e-15) at all three training points + reload.
- **One divergence, exactly where spec §3 is silent** — see item 5A below.
- Step 3: full protocol audit; SIGN-OFF after 1 reject cycle (doc-only defect:
  guard-count reconciliation; no code/model change). [r-audit.md; ledger B77–B84]

## 5. Items for Ayur's adjudication at this gate

**A. Aux-NLL truncation reading (the step-2 finding).** A-MODEL implemented the
auxiliary likelihood as a ZERO-TRUNCATED binomial — NLL = −log[Binom(k;u,p)/R],
normalizer P(k≥1) = R (the u-link resurfacing as conditioning constant), on
rows with label_c=1 ∧ ≥1 in-season union event. Spec §3's text ("NLL … under
head p") does not determine this; A-MODEL disclosed it (axes A1–A10,
s3b_primary.md) and R-AUDIT identified it blind to 3.5e-18. Related: R-AUDIT's
pre-committed checkability finding that §3's aux NLL is underdetermined on six
axes A–F (B66, corrected B72). ADJUDICATE: whether the zero-truncated reading
is accepted as the frozen interpretation of spec §3 (dated amendment per Rule 8
if so ruled).

**B. Hand-reconciled stats structure (surfaced by R-AUDIT, accepted-consequence
class).** The committed `s3b_stats.json` guard block is a LEAD-authorized
doc-only hand-reconciliation whose structure the code's stage_report would not
regenerate on a from-scratch rerun (it early-returns when stats exist; the
divergence itself proved the fix was doc-only). [B79–B84]

**C. Reject-cycle disclosure.** One REJECT on S3b: guard-pass count 233 vs
source 234 — append-only cumulative drift on idempotent reruns (B5-lineage
failure mode). Doc-only fix across four surfaces; deterministic sanctity facts
(15 sites / max season touched 2025 / zero ≥2026 firings) verified unaffected.

**D. Session-loss lineage.** The killed session's untracked S3b partials were
never trusted: quarantined per Rule 1 and regenerated from scratch; blindness
and sequencing survived structurally in git history. [B67–B70; r-audit step 3(b)]

## 6. On approval

PROVENANCE freeze entry + dormancy announcement + LEAD HALT (no further work;
G3 summer 2027 is a separate event, out of this run's scope). Season 2026-27
remains untouched: guards recorded zero ≥2026 firings; 2026-27 structurally
absent from both frames (asserted in code).
