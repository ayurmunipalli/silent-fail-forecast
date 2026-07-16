# CLAUDE.md — silent-fail-forecast — BUILD PHASE

Binding rules for every agent. Source of scientific truth: `model_spec.md`
(FROZEN). Operational truth: `plan.md` (build phase). Spec > plan > this file's
examples; conflicts are flagged, never silently resolved. Phase-0 is closed
(verdict GO, memo 2026-07-16); its artifacts are read-only history.

## Scope fence
In scope: plan.md §3 steps 1–9 — data, features, baselines B0–B4, the §3
two-head primary, validation, the pre-Oct-1 freeze. OUT of scope, even when
idle: ANY contact with season 2026-27 (it is the prospective test; it barely
exists yet and is already sacred); paper prose (the paper is Ayur's; agents
compile sources only); WFF edits or retraining (read-only, permanently);
architectures beyond spec §3; dashboards/alerting/other cities; G3 (summer
2027, a separate future event). Idle time is not license to expand scope.

## Rules (lineage numbering)
1. **No fabrication, ever.** Empty pull, schema surprise, non-reconciling
   merge, diverging loss → stop the branch, report the exact state. An ugly
   validation number is a finding; a fabricated clean one is misconduct.
2. **Credentials in `.env`**, never hardcoded, never printed. `.venv/bin/python`
   (3.12). `.env`, `.venv/`, `data/raw/` gitignored.
3. **Test-season sanctity — THE bright line (spec §4).** Season 2026-27 is
   held out absolutely and prospectively: no feature, no validation fold, no
   human decision touches it. The freeze precedes the season. G3 is a single
   event in summer 2027 and is not part of this phase.
4. **Temporal cutoff — Oct 1 (spec §1, §7).** No feature encodes information
   from on/after Oct 1 of its target season. R-AUDIT's temporal-leakage
   protocol at S2 is binding.
5. **Verify before you pull** (live ID checks logged to PROVENANCE).
6. **Label discipline:** frozen whitelist verbatim; B+C superset pulled,
   class-C restriction explicit in analysis code (standing pattern). 311 is
   never a label. The reporting-head likelihood grain is BUILDING-SEASON
   (spec §3 — probe-driven; per-incident association is diagnostics only).
7. **The paper is Ayur's.** No agent drafts prose. No "first" claims pre-M2′.
8. **Provenance / no silent edits.** Spec amendments = dated appended notes,
   Ayur-authored. PROVENANCE.md in the same commit as every stage (8a).
9. **Hard stops:** credential failure, ID mismatch, schema surprise, empty
   pull, storage breach (≤2 GB, no rasters), unruled R-A at G1, loss
   re-derivation mismatch, any unanticipated condition → halt branch,
   escalate to Ayur, never proceed on assumption.
10. **Seed 42 everywhere**; 5-seed spread is VALIDATION-based (spec §8), never
    test-based — settled doctrine, not open for reinterpretation.

## Team conventions
Roster/binding/order in plan.md. LEAD orchestrates in delegate mode and never
analyzes; workers never commit/spawn/cross-talk; all routes through LEAD.
R-AUDIT (opus 4.8) sign-offs binding per stage; blind protocols: S2 leakage
lineage; S3b loss re-derivation (implement the spec-§3 likelihood
independently BEFORE reading A-MODEL's code; reproduce fixed-batch loss).
process_log.md numbered per action; agent logs are deliverables.

## Architecture
```
silent-fail-forecast/
  model_spec.md      # FROZEN — source of truth
  plan.md            # build phase (this run)
  CLAUDE.md          # this file
  phase0_probe.md    # closed; historical
  .claude/agents/    # lead, a-data, a-feat, a-model (fable-5), r-audit (opus-4.8)
  imports/           # R4 frozen artifacts (sha256s in PROVENANCE)
  data/{raw,processed}/ + PROVENANCE.md
  src/               # one idempotent script per stage
  outputs/{checkpoints,models,tables,figures}/
  reports/agent_logs/ + reports/process_log.md
```
