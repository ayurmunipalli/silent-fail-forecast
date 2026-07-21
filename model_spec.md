Frozen, July 16, 2026
(G0)

# model_spec.md — silent-fail-forecast — censoring-aware heating-failure risk

Project: silent-fail-forecast (fresh repo; successor to winter-fail-forecast, "WFF").
Author of record: Ayur Munipalli. Spec drafted by lead Claude from Ayur's Step-0
rulings (2026-07-16) and the phase-0 probe verdict (GO, memo 2026-07-16, R-AUDIT-
signed). Status: DRAFT until Ayur writes "FROZEN" + date at top. After freezing,
amendments require a dated, appended note — no silent edits (Rule 8 lineage).

Phase-0 artifacts cited throughout are the four signed-off checkpoints + memo
(commits 0cd8294…758cf00). Numbers are cited, never re-derived here.

---

## 0. Rulings needed AT freeze (Ayur; blank until ruled)

- **R-A — ygpa-z7cr admission.** The merged HPD Complaints-and-Problems dataset is
  live (P3 verification) and was excluded from phase-0 by probe Amendment 1 (probe
  leanness, not a permanent ban). Admitting it would sharpen the reporting-head
  likelihood (apartment identifiers → distinct-units-complaining) and shrink the
  P3 upper-bound caveat on the 377. Cost: one new pull + schema work; risk: HPD's
  internal dedup errors (OSC 2019-N-3) enter as measurement noise. RULE: admit /
  exclude for this project.
- **R-B — success-criteria numbers (§10).** Drafted below from WFF's frozen
  benchmarks; the specific margins are Ayur's to set before freeze.
- **R-C — signature hygiene.** phase0_probe.md foot signature (flagged 3×).

## 1. Task definition

Estimate, per building per heating season, TWO latent quantities using only
information knowable before the season begins:

- **F = P(heating failure)** — the building will experience ≥1 heating/hot-water
  failure of violation-grade severity during the target season, whether or not
  anyone reports it. F is the deployment quantity: the ranking output.
- **R = P(detection | failure)** — a failure, if it occurs, results in a confirmed
  §27-2029/§27-2031 class-C violation (tenant reports → HPD inspects → confirms).

The observed label satisfies **P(Y_obs = 1) = F · R** (censored multiplicative
structure). WFF estimated F·R and called it risk; this project separates the
factors. The equity content is the target definition itself: WFF's own G3 §7C
showed the confirmed-violation label is blind to quiet buildings (0 of 250 flags
from the zero-311 stratum, both test seasons), and the blindness survives feature
ablation because it lives in the label.

- **Unit of analysis:** building (BBL), HPD-registered multiple dwellings — the
  frozen WFF label spine universe (181,863 distinct BBLs), imported read-only (R4).
- **Observed label:** identical to WFF §1 verbatim (frozen whitelist, class C,
  Oct 1–May 31 season windows, season labeled by start year). The B+C superset
  pull with explicit class-C restriction in analysis code is the standing pattern
  (probe deviation 4).
- **Prediction cutoff:** October 1 preceding the target season. No feature may
  encode information generated on or after Oct 1 of the target season year.
  R-LEAK-style audit is a binding stage (§12).

## 2. Data and seasons

- **Sources:** all WFF sources (HPD violations wvxf-dwi5; registrations +
  contacts; PLUTO 64uk-42ks) PLUS complaint-level 311 = union of erm2-nwe9 and
  archive 76ig-c548 (probe Amendment 3; union 1,738,636 rows, 0 dedupes, seam
  audited continuous; floor 2019-06-01). HSP membership: h4mf-f24e (official; 200
  selections, 197 lots; P3 authority ruling) + the four nyc.gov PDF lists as
  cross-check. ACS 2024 5-yr tract income/LEP via Census API (P4 machinery).
  [ygpa-z7cr: per R-A.]
- **Seasons:** violation-history features from 2017-18 (spine). Complaint-level
  311 exists 2019-06-01+; the reporting-head likelihood and any 311-derived
  feature carry an availability mask (WFF §3 pattern): NULL-masked, never
  zero-filled, for lookbacks predating coverage.
- **Development seasons:** 2019-20 … 2025-26 for the censored model (2017-18 and
  2018-19 contribute lag features only). **Prospective test season: 2026-27**
  (Step-0 ruling R1) — does not exist yet; scored once, summer 2027 (§9).
- Storage ≤ 2 GB tabular; no rasters, ever. Seed 42 everywhere.

## 3. Model (primary) — authorized architecture, Step-0 ruling R2

Joint two-head network, the ONLY authorized DL architecture (no transformers,
no GNNs, no ensembles):

- **Shared encoder:** MLP over the tabular feature families (§7). Width/depth in
  the frozen grid (§8).
- **Head F:** sigmoid, P(failure) per building-season.
- **Head p:** per-unit, per-season reporting intensity p ∈ (0,1). Building-level
  detection uses the structural thinning link **R = 1 − (1 − p)^u** (u = units,
  capped at u* per grid) — motivated by P4's monotone zero-311 gradient (78.4% of
  2–5-unit buildings zero-311 vs 16.8% of 50+) and the P2 complaints-per-unit
  shape. Monotonicity of R in u is structural, not learned.

**Likelihood (the loss IS the contribution):**
L = BCE(Y_obs, F·R)
  + λ · NLL of observed complaint counts under head p, at **BUILDING-SEASON
    grain** — complaint events vs confirmed-incident exposure per building-season.
    Grain choice is a probe-driven decision: per-incident assignment double-counts
    (P2 multiplicity 46.8% @W=14, 52.2% @W=30; 25.4% of building-days carry ≥2
    violation rows) and is demoted to diagnostics.
  + monotone/shape penalties per grid.
λ frozen in the grid before any test contact.

**Identification statement (honest, in the paper):** F and R are separated by
(i) the auxiliary duplicate-count likelihood on complaint-positive
building-seasons, (ii) the structural u-link, (iii) shared-support extrapolation
into the zero-311 mass — P4: 146/148 covariate cells shared; 106,231/106,232
zero-mass buildings in cells containing complaint-positive buildings, i.e.
interpolation, not speculation, but still model-based. External check: HSP (§10).

## 4. Train/validation/test protocol — the bright line

- **Prospective single-shot test:** season 2026-27, scored ONCE (~June–July 2027
  after an entry-lag check against prior-season volume). One omnibus event, G3
  semantics verbatim from WFF: run once, reported as-is, predictions persisted
  per-building for later re-slicing without re-contact.
- **Model freeze deadline: before Oct 1, 2026** — the frozen artifact predates
  the season it predicts. This is the paper's headline design property.
- **Development:** forward-chaining validation within 2019-20…2025-26 (train
  ⊆ seasons < v; never random K-fold). Seasons 2024-25/2025-26 are development
  here, with the WFF-conception provenance disclosed (Step-0 R1).
- No decision may touch 2026-27 labels before the single event, trivially now
  (they don't exist) and bindingly next summer.

## 5. Baselines (mandatory, reported regardless of outcome)

- **B0 persistence, B1 logistic-4, B2 trailing-3 count** — ported verbatim from
  WFF §6, computed on 2026-27 at G3.
- **B3 — frozen WFF primary** (`imports/primary_lgbm.txt`, sha256 in PROVENANCE,
  343 trees): loaded read-only, scored on 2026-27 features built to WFF's frozen
  30-feature recipe. Never retrained. B3 is the uncorrected state of the art and
  the paper's central comparison.
- **B4 — two-stage GBM:** LightGBM propensity model (same duplicate-count signal,
  same grain) → inverse-propensity-weighted LightGBM risk model. The honest
  non-DL implementation of the same idea. **If the joint model does not beat B4
  on the §10 criteria, that ships as the finding** (Step-0 R2).

## 6. Pre-registered analysis of the zero-311 stratum

Stratification for all equity reporting: **binary zero-311 vs any-311** (trailing
complaint history at cutoff) — the partition WFF's tercile diagnosis validated;
rank-qcut terciles are barred (known degeneracy under the zero mass). Miss
analysis (§7C pattern) reported for F-ranking vs B3-ranking, both seasons'
strata, regardless of direction.

## 7. Features (families; exact list frozen at the features checkpoint)

WFF families 1–5 verbatim (violation history; HPD context; 311 history masked;
PLUTO structure; owner/portfolio LOO) PLUS family 6: complaint-granularity
signals from the union pull — per-building trailing complaint-event counts,
inter-complaint gap stats, prior-season duplicate intensity, all strictly
pre-cutoff, all availability-masked. [Family 7, unit-level distinct-apartment
counts: only under R-A admit.] No satellite. Binding temporal-leakage review
before modeling (§12).

## 8. Hyperparameters

Grid (encoder width/depth, λ, u*, learning rate, B4 grids) proposed by the
modeling agent, approved by Ayur, FROZEN before any 2026-27 contact is possible
— i.e., before the Oct 1 model freeze. Selection on forward-chaining validation
only. Single seed 42 for primary numbers; 5-seed VALIDATION spread appendix
(WFF Amendment-1 semantics adopted verbatim from the start — no §5/§4 ambiguity
this time).

## 9. G3 (prospective) mechanics

Summer 2027: verify 2025-26-comparable label volume for 2026-27 (entry-lag
check; P2 shows 2025-26 = 27,316 whitelisted events); build features at the
Oct 1, 2026 cutoff from data as-of the freeze; score all models once; persist
predictions; report as-is. The §10 criteria are evaluated in that single event.

## 10. Falsifiable success criteria (numbers are R-B, Ayur rules at freeze)

Evaluated once, at G3, against pre-registered thresholds:

1. **Silent-stratum gain:** within the zero-311 stratum, F-ranking p@250 ≥
   **1.35×** B3's p@250 on the same stratum and season. (WFF anchor: B3 scored
   0.252 on its own test's zero-311 stratum; observed-label metrics understate
   the corrected model by construction — named limitation, §11.)
2. **Overall non-inferiority:** global p@250 ≥ **0.90×** B3's.
3. **HSP silent-failure check (confirmatory external):** among HSP-lot violation
   events in 2026-27 with zero associated 311 at W=30 (the P3 heuristic, 377
   historical events, ~10.4% of eligible in-program events), the corrected model
   ranks the involved buildings above B3's ranking at a pre-registered margin
   (median rank-percentile improvement > 0; exact statistic frozen with the grid).
4. **Joint > B4** on criteria 1–3, else the two-stage result is the paper.

Reported secondaries (not pass/fail; P4 demoted these from criteria): partial
correlation of estimated p with tract LEP share conditional on unit class;
income-tercile slices (P4 machinery). P4 showed near-identical marginal LEP
(0.101 vs 0.105) and HIGHER zero-mass median income ($85,263 vs $79,943) —
the compositional story is small-building-driven; any propensity-equity claim
must be conditional, and the paper says so either way.

Any criterion failing ships as the finding.

## 11. Claims discipline

Allowed: "a censoring-aware, prospectively evaluated pre-season ranking of
heating-failure risk; separates failure risk from reporting propensity;
performance vs the uncorrected frozen predecessor = X." Named limitations,
verbatim in the paper: observed-label evaluation penalizes correction by
construction; 377 is an upper bound (311-only heuristic); identification is
model-based over shared support. Forbidden: "first" claims before Ayur's M2′;
any causal claim; any health claim. Priors to position against (verified):
Boxer/Hong/Kontokosta/Neill AoAS 2025; Liu/Bhandaram/Garg NatCompSci 2024;
Kontokosta/Hong/Korsberg 2017; Potash et al. KDD 2015; WFF itself.

## 12. Team topology, gates, out-of-scope

Topology per plan.md at spawn (Amendment-2 pattern: fable-5 workers, opus-4.8
binding audit; blind re-derivation for the loss implementation and the G3
event). Gates: G0 = this freeze; G1 = data/features + leakage sign-off; G2 =
baselines B0–B4 committed + grid locked, before any primary training; G3 =
the single prospective evaluation (summer 2027). Out of scope: dashboards,
live pipelines, tenant alerting, other cities, deep-learning architectures
beyond §3, any WFF re-analysis or retraining, any 2026-27 contact before G3.

---

## Amendments (appended, dated — never in-place edits)

**Amendment 1 — R-A resolved: ygpa-z7cr ADMITTED, non-load-bearing.**
Dated 2026-07-16. Author of record: Ayur Munipalli.

§0 R-A is ruled: **ADMIT**. The merged HPD Complaints-and-Problems dataset
(`ygpa-z7cr`) is admitted to this project in exactly two capacities:

(i) **Feature family 7** (§7): distinct-apartments-complaining signals,
availability-masked, building-season grain, strictly pre-cutoff — the §1
Oct-1 rule and §12 leakage review apply unchanged;

(ii) **a screen sharpening the §10 criterion-3 HSP heuristic** (the
zero-associated-311 upper-bound caveat on the 377; the exact criterion-3
statistic remains frozen with the grid per §10).

**Non-load-bearing boundary:** the 311 union (§2) remains the SOLE source of
the reporting-head likelihood (§3). ygpa-z7cr never enters the loss — not as
counts, not as exposure, not as a mask, not as a weight. The §3
identification statement is unchanged.

**Rationale on record:** OSC audit 2019-N-3 documents HPD's internal dedup
errors; the dataset informs features, it does not carry identification.

**Amendment 2 — G1 adjudication: gate-scope clarification; R-B ratified.**
Dated 2026-07-16. Author of record: Ayur Munipalli.

**Gate-scope clarification (§12 CLARIFIED, not changed):**

- **G1** = data coverage + grid approval + §0 resolutions.
- The **temporal-leakage sign-off** is a BINDING condition of stage S2
(R-AUDIT's S2 protocol); its result is reviewed by Ayur within the G2 packet.
- **G2** = S2 leakage sign-off + baselines B0–B4 committed + grid lock.
- **No stage proceeds past a leakage REJECT, regardless of gate timing.**

**R-B ratified (§0, §10):** the grid proposal
(`outputs/checkpoints/hyperparam_grid.md`, as posted at G1 and approved) and
the §10 margins as drafted — criterion 1: ≥ 1.35× B3 zero-311-stratum p@250;
criterion 2: global p@250 ≥ 0.90× B3's; criterion 3: T = median rank-percentile
improvement (pct_F − pct_B3) over silent-screened HSP buildings at W=30, pass
= T > 0 by one-sided exact sign test at α = 0.05, computed once at G3 —
are now the pre-registration.

**Pre-registered addition:** the G3 packet must report the realized n for
criterion 3 (the count of silent-screened HSP buildings entering the sign
test) alongside the test result.

**Amendment 3 — G2 adjudication: G2 APPROVED; baseline B5 added (§5) for attribution.**
Ruled 2026-07-16, appended 2026-07-17. Author of record: Ayur Munipalli.

**G2 is adjudicated APPROVED** (Amendment-2 components: S2 leakage sign-off,
baselines B0–B4 committed, grid locked). S3b is authorized subject to the
addition below being executed first.

**§5 gains baseline B5 — uncorrected retrained LightGBM:**

- Identical 49-feature frame (`features_main.parquet`) and identical
forward-chaining folds (v ∈ 2021-22…2025-26) as B4.
- Plain BCE objective on Y_obs: NO propensity stage, NO inverse-propensity
weighting — the uncorrected twin of B4's risk stage.
- Grid = B4's stage-2 grid VERBATIM (n=60 sampled, seed 42); same
pre-registered selection rule (mean validation AP vs Y_obs; tie-break
zero-311-stratum p@250 of the deployment ranking).
- B5 is committed and audited under the S3a protocol BEFORE any primary
(S3b) code exists — the baselines-before-primary property is preserved.

**Rationale on record:** B3 is frozen on ≤2023 data, so B4-vs-B3 confounds
the censoring correction with training recency; B5 isolates the correction
effect (B5 vs B4, like-for-like frame, folds, grid, and selection).

**§10 criteria UNCHANGED:** still measured against B3 — the deployed
incumbent is the deployment comparison. B5 is for attribution, not pass/fail.

**Amendment 4 — FREEZE adjudication: FREEZE APPROVED; §3 aux-NLL interpretation frozen; §9 clarified; freeze-entry mandate.**
Ruled 2026-07-18, appended 2026-07-20. Author of record: Ayur Munipalli.

**The FREEZE gate is adjudicated APPROVED** (packet of 2026-07-17, commit
01e912b), subject to the three parts below. The frozen artifact is
`outputs/models/s3b_primary_seed42.pt` with `s3b_frozen_config.json`, exactly
as identified in the packet and PROVENANCE.

**(i) §3 aux-NLL interpretation FROZEN (packet item A ratified).**
A-MODEL's disclosed reading of §3's auxiliary likelihood is ratified as the
frozen interpretation of §3:

- **Zero-truncated binomial** at building-season grain: NLL =
  −log[Binom(k; u, p) / R], with normalizer P(k≥1) = R = 1−(1−p)^u — the
  u-link resurfacing as the conditioning constant;
- **Eligible rows:** `label_c==1 AND k_raw≥1` (confirmed-incident exposure;
  complaint-positive per grid §3 / §3(i)); exposure n = u = min(u_raw, u*),
  count k = min(k_raw, u); k_raw = in-season **311-union** events only
  (Amendment-1 boundary unchanged);
- together with **ALL resolved implementation axes A1–A10** as disclosed in
  the `src/s3b_primary.py` header (binding statements) and summarized in
  `outputs/checkpoints/s3b_primary.md` — including log-binomial-coefficient
  inclusion, mean-over-eligible reduction, u_raw fallback ladder, Ω₁/Ω₂ forms
  and constants, design construction, init, ES loss, clamps, E*=10 refit, and
  seeding.

**Basis on record:** R-AUDIT's blind re-derivation converged on this reading
independently (agreement 3.5e-18) from spec + fixed-batch kit alone; the
single blind divergence sat exactly where §3 was silent. This amendment
closes that silence per Rule 8. The underdetermined axes A–F (ledger B66,
corrected B72) are resolved by this ratification.

**(ii) §9 CLARIFIED, not changed — G3 scoring-data semantics.**
§9's "build features at the Oct 1, 2026 cutoff from data as-of the freeze" is
clarified to deployment semantics: G3 scoring features for season 2026-27 are
built **at G3 (summer 2027) from a fresh pull whose feature windows are
hard-bounded < Oct 1, 2026** — pre-cutoff by WINDOW, not by pull date. The §1
temporal cutoff, the availability-mask discipline, the sanctity guards, and
the bright line (Rule 3) are unchanged; no 2026-27 contact occurs before G3.
G3 pull provenance (dataset IDs, pull timestamps, row counts, window
assertions) is recorded in PROVENANCE at G3, not now.

**(iii) PROVENANCE freeze-entry mandate.**
The freeze entry written under this amendment enumerates the **complete G3
scoring set**, such that summer 2027 requires zero interpretation:

- **primary bundle:** `s3b_primary_seed42.pt` + `s3b_frozen_config.json`
  (sha256s) + both feature-frame recipe hashes (features_main, features_b3);
- **B3:** the imported frozen WFF artifact + the B3-frame recipe;
- **B4/B5:** committed artifacts as audited under S3a;
- **B0–B2:** their frozen definitions;
- **§10 criteria as amended** (Amendment-2 pre-registration; criterion-3
  realized-n reporting; §10.4 fallback).

**Packet items B, C, D:** acknowledged as disclosed (hand-reconciled stats
structure; one doc-only reject cycle; session-loss lineage). No action; on
record via the packet and ledger.

**Amendment 5 — R-PILOT authorized: retrospective 2025-26 pilot; dormancy-exempt as one scoped phase.**
Dated 2026-07-21. Author of record: Ayur Munipalli.

**(i) Retrospective pilot phase ("R-PILOT") is AUTHORIZED**, to run after
the freeze entry, as a single scoped exemption from build-phase dormancy —
everything else in the dormancy stands, and dormancy resumes when the
R-PILOT result packet is delivered.

- **Cutoff:** everything re-executed as-of **Oct 1, 2025**. Dev/validation
  folds **strictly ≤ season 2024-25**; season 2025-26 is contacted exactly
  once, at the (ii) evaluation.
- **Re-selection, not reuse:** the frozen cfg-2009 artifact is **NOT
  reused** — its selection saw 2025-26 validation folds. The joint model and
  both twins are re-selected and re-trained at the pilot cutoff: the **SAME
  locked grid** (`hyperparam_grid.md`, n=60 sample, seed 42) and the **same
  pre-registered selection rules** re-executed mechanically over folds
  v ∈ 2021-22 … 2024-25, with refit-E* and all frozen interpretation axes
  (Amendment 4(i)) unchanged — for the §3 joint model, **B4** (two-stage
  IPW), and **B5** (uncorrected twin). B0–B2 recomputed from their frozen
  definitions.
- **B3 scores as-is** (trained ≤2023; no retraining — WFF remains
  read-only).
- **Frames:** the hash-pinned S2 frames (`features_main` `477d3079…`,
  `features_b3` `09f8e94d…`) are reused; by the §1 per-target-season rule
  their season-2025 rows already encode nothing from on/after Oct 1, 2025.
  No new pulls; no frame regeneration.
- **The frozen bundle stays untouched:** `s3b_primary_seed42.pt` +
  `s3b_frozen_config.json` are read-only throughout; no pilot artifact
  overwrites, shadows, or renames any frozen or committed artifact.

**(ii) Single-shot evaluation on season 2025-26 — ONE event,
R-AUDIT-audited.** Scored once, persisted, reported as-is: observed-label
metrics (AP, p@250); **zero-311-stratum p@250 vs B3** on the same stratum
and season; and the **criterion-3-style sign test** on 2025-26
silent-screened HSP events (W=30 screen, median rank-percentile
improvement, one-sided exact sign test α = 0.05, **realized n reported**).
Standing audit protocols bind: R-AUDIT temporal-leakage review at the pilot
cutoff before any training; per-stage sign-offs; the §11 observed-label
caveat attaches to every number.

**(iii) PRE-COMMITTED, before any pilot code runs:**

- The result is **disclosed in full whichever direction it lands** — any
  criterion-style comparison failing ships as the finding.
- Every pilot artifact, table, and log carries the label **RETROSPECTIVE
  AND NON-BLIND**: the project's conception and this spec postdate season
  2025-26; the pilot has no prospective standing.
- The pilot **modifies NOTHING in the frozen G3 pre-registration**: §10 and
  its margins, the frozen bundle, the Amendment-4 freeze entry, and the
  2026-27 bright line (Rule 3) are untouched. R-PILOT results carry no
  weight at G3 and are reported separately from it.
