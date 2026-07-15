# r-audit.md — R-AUDIT agent log (silent-fail-forecast phase-0)

**Role:** Binding auditor for all phase-0 stages, audited IN ORDER, one at a time.
Cross-family model by design (opus 4.8 vs. fable-5 workers) for decorrelated blind
spots. I never fix code — defects route back through the LEAD. I never adjudicate the
verdict; semantics are pre-committed and adjudication is Ayur's alone.

**Model binding:** claude-opus-4-8 (spawned as such; confirmed).
**Spawn date:** 2026-07-16. Spawned IDLE per plan.md §3 step 1. No audit requested yet.

**Documents read in full (in order), 2026-07-16:**
1. `.claude/agents/r-audit.md` — my binding role definition (adopted completely).
2. `CLAUDE.md` — phase-0 scope fence + behavioral rules.
3. `phase0_probe.md` — APPROVED 2026-07-16, incl. Amendments 1–2 (scientific source of truth).
4. `plan.md` — roster, model binding, execution order, handoff protocol (Amendment 2 topology).

**Binding rules that apply to me identically:** Rule 1 (no fabrication — the kill gate
exists to be allowed to fire), Rule 2 (creds in `.env`, never printed; `.venv/bin/python`
3.12), Rule 7 (seed 42), Rule 9 (hard stops → halt, escalate via LEAD).

---

## Per-stage audit protocols I will apply (from r-audit.md)

**P1 (A-PULL):** re-verify dataset IDs live; row counts vs PROVENANCE; null-bbl
accounting arithmetic; storage within 2 GB budget; recompute imports' sha256 vs recorded.

**P2 (A-GATE) — BLIND, strict order:**
1. Read ONLY the cached parquets + `phase0_probe.md` §3 as amended. Re-derive in my own
   code the gate cells — median associated complaints per confirmed violation, buildings
   ≥10 units, at W=14 AND W=30 — plus the lag median/p75/p90. I do NOT read
   `reports/agent_logs/a-gate.md` or A-GATE's checkpoint/code until step 2.
2. Then read A-GATE's checkpoint + code. Compare (max abs diff per cell). Audit: window
   bound inclusivity, timezone/date truncation, duplicate violation rows, bbl dtype/leading
   zeros, unit-count join coverage and unmatched-row handling.
3. Verify the stated gate branch (GO/HOLD/KILL) follows mechanically from the cells under
   Amendment 1 semantics (gate at W=14; FAIL@14∧PASS@30→HOLD; FAIL@both→KILL; PASS@14→GO).

**P3 (A-AUX):** cohort resolution-rate spot check; ≥30-floor arithmetic; confirm the HPD
complaints dataset-ID verification was logged (present or absent both fine — unlogged is not).

**P4 (A-AUX):** no gating language crept in; Census key never printed; exclusions logged
not imputed.

**Memo (LEAD):** every threshold quoted VERBATIM against `phase0_probe.md`; verdict
consistent with signed-off checkpoints; on HOLD, zero recommendation language.

---

## Audit ledger

_(binding SIGN-OFF / REJECT entries land here, one per stage, in the order the LEAD
requests. None yet — spawned idle.)_

- 2026-07-16 — Initialized. READY, idle. Awaiting first audit dispatch from LEAD.
