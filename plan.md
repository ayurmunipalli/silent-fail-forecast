# plan.md — silent-fail-forecast — BUILD PHASE operational plan

Operationalizes the FROZEN `model_spec.md`. Scientific definitions live in the
spec; if this file conflicts with it, the spec wins — flag, don't resolve.
Behavioral rules live in `CLAUDE.md` (build-phase version). Supersedes the
phase-0 plan.md (archived in git history; phase-0 is closed, verdict GO).

**The build-phase deadline is structural: the primary model artifact is FROZEN
and committed BEFORE OCT 1, 2026 (spec §4). Every stage below serves that date.**

---

## 1. Roster and model binding

| Agent | Role (one lane each) | Model | Audited by |
|---|---|---|---|
| **LEAD** | Orchestration only (delegate mode): spawn, sequence, commit, process log, gate packets for Ayur. No analysis, no code. | `claude-fable-5` | R-AUDIT (gate packets) |
| **A-DATA** | S1: all pulls (refresh 311 union; registrations + contacts; HPD context; full PLUTO attributes; [ygpa-z7cr per R-A]); spine verification. | `claude-fable-5` | R-AUDIT |
| **A-FEAT** | S2: TWO feature frames — (a) WFF-recipe 30-feature frame for B3 scoring, re-implemented from the read-only WFF `s2_features.py`; (b) this project's families 1–6 (+7 per R-A) with availability masks. | `claude-fable-5` | R-AUDIT (incl. the binding TEMPORAL-LEAKAGE protocol, spec §1/§7/§12) |
| **A-MODEL** | S3a: baselines B0–B4 + grid proposal. S3b (only after G2): two-head net per spec §3, forward-chaining validation, 5-seed validation spread, freeze candidate. | `claude-fable-5` | R-AUDIT (incl. BLIND re-derivation of the censored-likelihood implementation) |
| **R-AUDIT** | Binding per-stage sign-offs, in order. Cross-family by design. | `claude-opus-4-8` | — |

`.claude/agents/` files bind the models; LEAD verifies all five files + exact
model strings before spawning, halts on any mismatch (silent-flattening guard).

## 2. Topology

```
A-DATA(S1) ─[R-AUDIT]─[G1: Ayur]─> A-FEAT(S2) ─[R-AUDIT+LEAK]─> A-MODEL(S3a: B0–B4)
   grid proposal posted at G1 ┘                                        │
                                             ─[R-AUDIT]─[G2: Ayur]─> S3b: primary net
                                                                        │
                                        ─[R-AUDIT blind-loss]─[FREEZE gate: Ayur, pre-Oct-1]─> HALT until G3 (summer 2027)
```
All communication through LEAD; workers never commit, spawn, or cross-talk.
No parallel worker lanes this phase — the pipeline is linear by dependency;
parallelism would add coordination cost, not speed (simplicity ruling).

## 3. Ordered process (one commit + process-log entries per step)

1. LEAD: verify agent files/model strings; open process_log; spawn team.
   **R-A CHECK:** if spec §0 R-A (ygpa-z7cr admit/exclude) is unruled, dispatch
   S1 WITHOUT that branch and raise a standing stop for Ayur's one-word ruling;
   the branch (one pull + family 7) merges in whenever the ruling lands, and G1
   cannot clear without it.
2. A-DATA S1: verify every dataset ID live (Rule 5); refresh the 311 union to
   the current date (Amendment-3 arithmetic + seam check re-run); pull
   registrations, contacts, HPD context classes, full PLUTO attributes;
   verify the imported R4 spine covers 2017-18…2025-26. → R-AUDIT S1 pass.
3. A-MODEL: grid proposal posted (`outputs/checkpoints/hyperparam_grid.md`) —
   encoder width/depth, λ, u*, LR, B4 grids, the §10-criterion-3 statistic.
4. **G1 (Ayur):** S1 coverage report + grid proposal + R-A resolution. HALT until approval.
5. A-FEAT S2: both feature frames; masks; null audit; byte-identical rerun
   check. → R-AUDIT S2 pass INCLUDING the temporal-leakage protocol (every
   feature's timestamp lineage vs the Oct-1 rule; binding; its own section of
   the sign-off).
6. A-MODEL S3a: B0, B1, B2 ported verbatim; B3 = frozen booster loaded (tree-count
   assertion) scored on the WFF-recipe frame; B4 two-stage GBM built with full
   effort (it is the bar, not a strawman). Forward-chaining validation only,
   v ∈ {2021-22…2025-26 per mask coverage}; committed BEFORE any primary code
   exists. → R-AUDIT S3a pass.
7. **G2 (Ayur):** baselines committed + grid locked. HALT until approval.
8. A-MODEL S3b: two-head net per spec §3 exactly; selection on validation only;
   5-seed VALIDATION spread (seeds 42–46, hyperparams fixed); freeze candidate
   = seed-42 artifact + config + feature recipe hashes. → R-AUDIT S3b pass
   INCLUDING blind loss re-derivation: from spec §3 alone, R-AUDIT independently
   implements the likelihood and reproduces training-set loss values on a fixed
   batch before reading A-MODEL's code.
9. **FREEZE gate (Ayur, hard deadline pre-Oct-1):** frozen artifacts committed;
   PROVENANCE freeze entry; repo enters dormancy. LEAD announces and HALTS.
10. G3 (summer 2027) is NOT part of this run. Nothing may touch season 2026-27.

## 4. Handoff, documentation, escalation

Identical to phase-0 conventions: numbered process_log line per action; task
text = spec-section pointers, thresholds never restated; per-agent logs are
deliverables; PROVENANCE.md in the same commit as every stage; REJECT → back
through LEAD with the defect verbatim; two consecutive rejections on one
stage, or any Rule-9 condition → HALT and escalate to Ayur (async from phone;
idle at the stop). Commit format: `S<stage>: <summary> [R-AUDIT: signed-off]`. **Every stage
commit is immediately pushed to origin** — external timestamps are part of
the pre-registration evidence (the FREEZE commit especially: its pushed
timestamp is the proof it predates Oct 1). A failed push is a Rule-9 stop,
not a shrug.

## 5. Calendar (agent-time; Ayur's involvement = G1, G2, FREEZE approvals + R-A)

S1+grid ≈ days 1–3 → G1 ≈ end of July → S2 ≈ days 4–8 → S3a ≈ days 8–12 →
G2 ≈ mid-August → S3b ≈ 2–3 weeks incl. audit cycles → FREEZE target
**early-to-mid September** (buffer ≥ 2 weeks before the Oct 1 line for a
rejection cycle). Ayur's paper writing (separate track) is untouched by this
calendar except the three approvals.
