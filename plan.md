# plan.md — silent-fail-forecast — phase-0 operational plan

Operationalizes the APPROVED `phase0_probe.md` (incl. Amendments 1–2). This file
carries WHO does WHAT in WHAT ORDER; scientific definitions (probes, thresholds,
gate semantics) live in the probe doc and are not restated here — if anything in
this file conflicts with `phase0_probe.md`, the probe doc wins; flag, don't resolve.
Behavioral rules live in `CLAUDE.md`.

---

## 1. Roster and model binding

| Agent | Role (one task each) | Model | Audited by |
|---|---|---|---|
| **LEAD** | Orchestration only: spawns, sequences, commits, maintains process log, compiles memo. Does NO analysis and writes NO pipeline code. | `claude-fable-5` | R-AUDIT (memo check) |
| **A-PULL** | P1: bootstrap imports (R4 artifacts + sha256) and all data pulls (311 complaint-level, violations, PLUTO). | `claude-fable-5` | R-AUDIT |
| **A-GATE** | P2: incident-association join, gate tables at W=14/W=30, lag distribution. The verdict-bearing computation. | `claude-fable-5` | R-AUDIT (independent re-derivation, binding) |
| **A-AUX** | P3 (HSP cohorts + detectability) and P4 (zero-mass descriptives). | `claude-fable-5` | R-AUDIT |
| **R-AUDIT** | Audits every stage IN ORDER, binding sign-off per stage. Peer instance, isolated context, cross-family model by design (decorrelated blind spots). | `claude-opus-4-8` | — |

**Model binding is enforced by `.claude/agents/` definition files** (lead.md,
a-pull.md, a-gate.md, a-aux.md, r-audit.md). Absence of a definition file causes
silent model flattening (known failure mode, prior repos) — the LEAD verifies all
five files exist and carry the exact model strings above BEFORE spawning anyone,
and halts if any is missing or altered.

## 2. Execution topology

```
                       ┌─> A-GATE (P2) ──[R-AUDIT: re-derivation, BINDING]──┐
A-PULL (P1) ─[R-AUDIT]─┤                                                    ├─> LEAD memo ─[R-AUDIT: memo-vs-thresholds]─> AYUR adjudicates
                       └─> A-AUX (P3, P4) ──[R-AUDIT: P3, then P4]──────────┘
```

- Everything routes through the LEAD: workers never message each other, never
  spawn anyone, never commit. Worker finishes → reports to LEAD → LEAD requests
  the matching R-AUDIT pass → sign-off lands → LEAD commits the stage → LEAD
  dispatches the next task.
- A-GATE and A-AUX run IN PARALLEL after P1 sign-off (P2, P3, P4 all depend only
  on P1's caches; nothing depends on each other).
- R-AUDIT audits stages in completion order, one at a time. Its P2 pass follows
  the blind protocol in `.claude/agents/r-audit.md`: re-derive gate cells from
  the parquets + probe doc FIRST, read A-GATE's checkpoint only after.
- The memo is compiled by the LEAD from signed-off checkpoints, cites thresholds
  VERBATIM from the probe doc, recommends nothing on a HOLD, and is itself
  audited (memo-vs-thresholds check) before reaching Ayur.

## 3. Ordered process (each numbered step = one process-log entry; steps 2–8 each end in one commit)

0. Ayur: manual setup (repo init, `.env`, `<WFF_PATH>` known, files in place).
1. LEAD: verify `.claude/agents/` files + model strings; open `reports/process_log.md`; spawn R-AUDIT (idle) and A-PULL.
2. A-PULL: bootstrap — R4 imports by copy + sha256 → PROVENANCE. LEAD commits.
3. A-PULL: P1 pulls per probe doc §2 (+ fresh violations, PLUTO). → R-AUDIT P1 pass (row counts vs PROVENANCE, ID verification, null-bbl accounting, storage). LEAD commits.
4. LEAD: dispatch A-GATE (P2) and A-AUX (P3) in parallel.
5. A-GATE: P2 per probe doc §3 as amended — both windows, one join; gate evaluated at W=14; HOLD branch semantics; lag table mandatory. → R-AUDIT P2 pass (blind re-derivation + join audit: window bound inclusivity, timezone/date truncation, duplicate violation rows, bbl dtype/leading zeros, unit-count join coverage). BINDING. LEAD commits.
6. A-AUX: P3 per probe doc §4 (HSP lists; unlocatable → `manual_downloads.md` + HALT that sub-branch for Ayur; ≥30-event floor). → R-AUDIT P3 pass. LEAD commits.
7. A-AUX: P4 per probe doc §5 (Census key from `.env`, never printed; descriptive only). → R-AUDIT P4 pass. LEAD commits.
8. LEAD: compile `phase0_memo.md` — verdict per §1 as amended, thresholds cited verbatim, R-AUDIT sign-offs referenced. → R-AUDIT memo pass. LEAD commits.
9. LEAD: announce completion + verdict to Ayur. HALT. Adjudication is Ayur's; nothing further is in scope.

## 4. Handoff protocol (simplicity rules)

- One task per agent at a time; task text = a pointer to the probe-doc section +
  any stage-specific constraints. No task may restate a threshold (drift risk).
- Every handoff (dispatch, completion, sign-off, rejection) is one numbered line
  in `reports/process_log.md`: `NN | timestamp | from → to | action | artifact`.
- R-AUDIT REJECT → LEAD returns the stage to its owner with the defect verbatim;
  fix; re-audit. Two consecutive rejections on the same stage → LEAD halts and
  escalates to Ayur (Rule 9).
- Any CLAUDE.md §9 hard-stop from any agent → LEAD halts the affected branch and
  escalates. Parallel branches unaffected by the stop continue.

## 5. Documentation requirements (meticulous, in order)

1. `reports/process_log.md` — LEAD-maintained numbered ledger; every action, no exceptions. THE ordered record of the run.
2. `reports/agent_logs/{a-pull,a-gate,a-aux,r-audit}.md` — per-agent: decisions, verified IDs, row counts, anomalies. Deliverables, not scratch.
3. `outputs/checkpoints/phase0_p{2,3,4}_*.md` + P1's pull report — per probe doc §7.
4. `data/PROVENANCE.md` — same commit as every stage (Rule 8a).
5. Commit messages: `P<stage>: <one-line summary> [R-AUDIT: signed-off]`.
