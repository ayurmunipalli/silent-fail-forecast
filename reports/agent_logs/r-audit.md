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

---

### 2026-07-16 — P1 audit (A-PULL) — **SIGN-OFF (binding)**

Amendment 3 read in full before auditing (archive union restoring 2019-06-01 floor;
P2 window-coverage eligibility codified — the latter is a P2 concern, not a P1
deliverable). Full r-audit.md P1 protocol applied + LEAD's three ruled additions.
All checks re-derived independently in my own code (`scratchpad/audit_p1.py`), read
directly from the parquets — not from A-PULL's stats.

**Dataset IDs — live re-verification (Rule 5), 2026-07-16, api/views/*.json:**
| ID | Live name (matches PROVENANCE) |
|---|---|
| `erm2-nwe9` | "311 Service Requests from 2020 to Present" ✓ (re-scope confirmed — the cause Amendment 3 resolves) |
| `76ig-c548` | "311 Service Requests from 2010 to 2019" ✓ |
| `wvxf-dwi5` | "Housing Maintenance Code Violations" ✓ |
| `64uk-42ks` | "Primary Land Use Tax Lot Output (PLUTO)" ✓ |

**Imports sha256 (recomputed vs PROVENANCE, all 3 exact match):** primary_lgbm.txt,
building_season_labels.parquet, test_predictions.parquet — all identical; sizes match.

**Row counts vs PROVENANCE (all exact):** current 1,645,614; archive 93,022;
violations 128,121 (C=128,120, B=1; whitelist text matches all 128,121 rows);
PLUTO 858,602 (bbl unique, 0 dupes — clean join key).

**Addition 1 — union dedupe arithmetic (from parquets):** 93,022 + 1,645,614 =
1,738,636; unique_key overlap archive∩current = **0**; dedupes removed = **0** (as
reported); deliverable = 1,738,636 − 7,123 null-bbl = **1,731,513**; actual
deliverable parquet = **1,731,513**, residual null-bbl in deliverable = 0. Exact.

**Addition 2 — restored floor:** union min created_date = 2019-06-01 00:17:18,
0 rows before the floor; monthly counts populated every month 2019-06 → 2020-03
(2019-06=3,098 … 2019-11=36,687 … 2020-01=25,711) — **no 2019 hole**.

**Addition 3 — seam continuity 2019-12-31→2020-01-01:** source×side crosstab shows
archive supplies ALL 93,022 pre-2020 rows and current ALL 1,645,614 from-2020 rows,
zero cross-source bleed (consistent with dedupe=0). Weekly counts span the seam
continuously (…2019-12-23/29=3,979 [Christmas dip], 2019-12-30/01-05=4,656,
2020-01-06/12=5,255…) — no coverage gap, no pileup, no duplication beyond the
logged dedupe of 0. Material-departure check (Ayur's standing instruction): none.

**Null-bbl accounting:** 7,123 / 1,738,636 = 0.4097% (~0.4% expected) ✓.
**Storage:** data/raw = 79.17 MB ≪ 2 GB (Rule 6) ✓. Rasters: none ✓.

**Class B/C superset:** whitelist verbatim is class IN ('B','C'); §3 gates class-C.
A-PULL pulled the B/C superset (1 class-B row) with `class` column retained for
A-GATE to apply the §3 restriction explicitly. Conformant for P1 (LEAD noted Ayur
accepted). **Carry-forward for P2 audit:** confirm A-GATE actually restricts to
class C before gating.

**Cosmetic (not a defect):** `c311_heat_complaints_full.parquet` holds only the
erm2-nwe9 current pull despite the "_full" suffix; the union is computed in-memory
and the deliverable is `c311_heat_complaints.parquet`. Clearly documented in
PROVENANCE and code; deliverable is correct.

**VERDICT: SIGN-OFF.** No defects. Every reported figure reconciles exactly with
independent re-derivation; all four IDs verified live; imports intact; floor
restored; seam clean; storage within budget.
