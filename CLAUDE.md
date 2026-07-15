# CLAUDE.md — silent-fail-forecast — PHASE-0 SCOPE

Binding rules for every agent in this repo during phase-0. The scientific source of
truth for phase-0 is `phase0_probe.md` (APPROVED by Ayur, 2026-07-16, incl. Amendments 1-2).
There is NO model_spec.md yet — spec drafting is gated on the probe verdict and does
not happen in this phase. If any instruction here conflicts with `phase0_probe.md`,
the probe doc wins — flag the conflict, do not resolve it silently.

---

## Phase-0 scope fence (read first)

Phase-0 answers ONE question: is the identification strategy live (probe doc §1)?
In scope: probes P1–P4 and `phase0_memo.md`. OUT of scope — do not start, even if
idle: spec drafting, feature engineering, any model training (including baselines),
team-topology setup, paper/source compilation, any edit to the winter-fail-forecast
repo, any satellite/GEE work. Idle time is not license to expand scope (PROVENANCE
incident, 2026-07-13, standing rule).

## Rules (ported from winter-fail-forecast; same numbering where they carry over)

1. **No fabrication, ever.** No placeholder data, no invented numbers, no guessed
   dataset IDs, no synthetic rows to make a probe "pass." Empty pull, schema surprise,
   unresolvable merge → stop that branch, report the exact state. An ugly number is a
   finding; a fabricated clean one is misconduct. This applies with full force to the
   kill gate: the gate exists to be allowed to fire.

2. **Credentials live in `.env`** (python-dotenv). Never hardcode, never print values.
   All agents run `.venv/bin/python` (3.12). `.env`, `.venv/`, `data/raw/` gitignored.

3. **Verdict sanctity.** The P2 kill thresholds, the W=14 gate, the HOLD branch, and
   the P3 validation-power floor are pre-committed in `phase0_probe.md` and may not be
   reinterpreted, re-windowed, or supplemented with new gates after data is seen.
   `phase0_memo.md` CITES the thresholds verbatim; it does not restate or adjust them.
   HOLD and the final GO/GO-DEGRADED/KILL adjudication are Ayur's alone.

4. **Old repo is READ-ONLY.** winter-fail-forecast is never edited, re-run, or
   retrained. The three R4 frozen artifacts are imported by copy into `imports/` with
   sha256 recorded in PROVENANCE.md in the same commit. Everything else this probe
   needs is pulled FRESH (self-contained provenance): violations via the frozen
   whitelist (verbatim from the probe doc / old repo), PLUTO for unit counts.
   Test-season sanctity note: seasons 2024-25/2025-26 are DEVELOPMENT data in this
   project (probe doc §0 R1) — but season 2026-27 is the future prospective test and
   does not exist yet; no rule can touch it because nothing can.

5. **Verify before you pull.** Confirm every Socrata dataset ID live against
   data.cityofnewyork.us before pulling; log verified IDs + dates to PROVENANCE.md.
   Every pull server-side filtered, parquet-cached, idempotent (rerunnable to the
   same bytes).

6. **Storage ≤ 2 GB tabular. No rasters on disk, ever.** Any stage projecting a
   breach halts and reports.

7. **Seed 42 everywhere** (tie-breaks, any sampling).

8. **Provenance / no silent edits.** `phase0_probe.md` is approved-frozen: changes
   require a dated, appended amendment authored by Ayur — never in-place edits.
   (**8a**) `data/PROVENANCE.md` updated in the SAME commit as every probe stage:
   dataset IDs + verification date, row counts, key decisions, anomalies, deviations.

9. **Hard stops — halt and wait for Ayur (may arrive async from phone):** any
   credential failure, dataset-ID mismatch, schema surprise, empty pull,
   storage-budget breach, HSP cohort lists unlocatable, or any condition the probe
   doc did not anticipate. Never substitute a placeholder; never proceed on assumption.

## Team conventions (phase-0 — Amendment 2 topology)

- Roster, model binding, execution order, handoff protocol, and documentation
  requirements live in **`plan.md`** — spawning anything beyond its roster is scope
  creep, flag it. LEAD (fable 5) orchestrates only and never analyzes; workers
  (fable 5) never commit, never spawn, never message each other — everything routes
  through the LEAD. **R-AUDIT (opus 4.8) sign-offs are binding per stage**; its P2
  pass is blind (independent re-derivation from the parquets + probe doc BEFORE
  reading A-GATE's outputs). `.claude/agents/` definition files bind the models —
  their absence causes silent flattening; the LEAD verifies them before spawning.
- Every agent writes `reports/agent_logs/     # a-pull, a-gate, a-aux, r-audit + LEAD's process_log.md<agent>.md`; the LEAD maintains the
  numbered `reports/process_log.md`. Logs are deliverables, not scratch.
- One commit per signed-off stage, PROVENANCE.md in the same commit.
- Ayur's adjudication of the verdict is non-delegatable.
- One commit per probe stage (P1, P2, P3, P4, memo), clear message, PROVENANCE in
  the same commit.

## Architecture

```
silent-fail-forecast/
  CLAUDE.md              # this file — phase-0 scope
  phase0_probe.md        # APPROVED 2026-07-16 (+ Amendments 1-2) — source of truth
  plan.md                # roster, model binding, ordered process (Amendment 2 topology)
  .claude/agents/        # lead / a-pull / a-gate / a-aux (fable 5) + r-audit (opus 4.8)
                         #   — these BIND the models; absence = silent flattening
  .env                   # SOCRATA_APP_TOKEN, CENSUS_API_KEY
  .venv/                 # python 3.12
  imports/               # R4 read-only frozen artifacts from winter-fail-forecast
                         #   primary_lgbm.txt / building_season_labels.parquet /
                         #   test_predictions.parquet  (+ sha256s in PROVENANCE)
  data/
    raw/                 # gitignored (fresh pulls: 311 complaint-level, violations, PLUTO)
    PROVENANCE.md        # from the very first pull (Rule 8a)
  src/                   # one idempotent script per probe (p1_pull.py, p2_gate.py,
                         #   p3_hsp.py, p4_zeromass.py)
  outputs/checkpoints/   # phase0_p2_duplicates.md, phase0_p3_hsp.md, phase0_p4_zeromass.md
  reports/agent_logs/
  phase0_memo.md         # the verdict — written LAST, cites thresholds verbatim
```
