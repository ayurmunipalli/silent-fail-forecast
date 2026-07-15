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

---

### 2026-07-16 — P2 audit (A-GATE) — **SIGN-OFF (binding)** — BLIND protocol

Strict blind order followed. **Step 1** (independent re-derivation from ONLY the P1
parquets + probe §3/Amdt 1/Amdt 3, my own code `scratchpad/audit_p2.py`, BEFORE
reading any A-GATE output). **Step 2** read A-GATE's checkpoint, `p2_gate.py`,
`p2_stats.json`, `a-gate.md` and compared. **Step 3** verified branch mechanics.

**Step-1 blind cells (my first pass):** W=14 ≥10u median **3**, W=30 median **4**,
n=84,173 → PASS@14 → GO.
**A-GATE cells:** W=14 ≥10u median **4**, W=30 median **6**, n=76,217 → PASS@14 → GO.

**Fork identified & resolved.** The magnitude gap traced to two A-GATE decisions my
first blind pass had not applied — both stated in A-GATE's docstring + checkpoint:
1. **Off-season (Jun–Sep) exclusion (dominant driver).** A-GATE restricts P2 to the
   seven listed heat seasons (Oct–May, start-year label), using `season_of` ported
   in-semantics from the frozen winter-fail-forecast label spine; Jun–Sep = no
   season → excluded (13,253). Grounded in §3 ("stratified by season 2019-20 …
   2025-26") + Amendment 3 item 2 ("seasons outside the list remain out of P2").
2. **Literal `bbl=0` exclusion** (12 violations / 331 complaints) — negligible for
   the gate (zero-bbl violations never match PLUTO, so never enter the ≥10-unit cell).

**Reproduction under A-GATE's STATED method (`scratchpad/audit_p2b.py`): MAX ABS
DIFF = 0 on every cell** — waterfall 128,121→114,344 (−C1 −dup0 −bbl197 −covL303/R23
−off13,253); unit join 114,151 (99.83%); gate n(≥10u)=76,217; median W14=4, W30=6;
unit-class medians 2/2/3/5 (W14) & 2/3/5/8 (W30); pairs W30=1,142,293; lag pooled
9/19/26; zero-complaint 4.94/3.56. A-GATE's code faithfully executes its stated method.

**Join-mechanics audit (all clean):**
- *Window inclusivity:* [inspd−W, inspd] inclusive both ends on calendar dates via
  searchsorted left/right — replicated exactly. Same-day complaints counted; disclosed.
- *Timezone/date truncation:* both sides truncated to naive-local calendar date;
  inspectiondate midnight-stamped (lossless); created_date time-of-day dropped
  (widens upper bound in the inclusive direction) — documented choice.
- *Duplicate violation rows:* 0 exact-dup violationid; multiple violations per
  (bbl,day) retained per §3 (unit = violation row) — verified.
- *bbl dtype/leading zeros:* numeric→int64 (BBL ≤ ~5.1e9, exact in float64; no
  leading-zero loss — borough digit 1–5); decimal-suffixed PLUTO parsed; zero-bbl
  excluded and counted — join reproduces.
- *Unit-join coverage/unmatched:* 99.83% matched; 193 unmatched excluded from
  gate/strata, retained in season margins; PLUTO conflicting-units excluded (0),
  never defaulted — verified.

**Class-C carry-forward (from my P1 audit): RESOLVED.** A-GATE removed exactly the
1 non-C row (128,121→128,120) as the first waterfall filter, explicitly. Confirmed.

**Branch mechanics (step 3):** gate14 = 4 ≥ 2 → **PASS@14 → GO on channel (a)**
follows mechanically under Amendment 1. A-GATE states the branch, does not adjudicate.

**FLAG for LEAD/Ayur (transparency, does NOT block sign-off — I do not adjudicate):**
the heat-season scoping is a documented interpretation that changes the reported cell
MAGNITUDE (median 4 heat-season-only vs 3 all-months) but NOT the gate OUTCOME. The
W=14 ≥10-unit median is ≥ 2 under every interpretation I tried (heat-season-only=4,
all-months date-level=3, all-months timestamp-level=3) → **the PASS@14 → GO verdict is
robust to the season-definition fork.** A-GATE's choice is well-grounded in §3 +
Amendment 3 and transparently documented; surfaced for Ayur's awareness, not as a defect.

**VERDICT: SIGN-OFF.** Gate cell and full waterfall reproduce with max abs diff 0
under A-GATE's stated, documented, doc-consistent method; branch follows mechanically;
join mechanics clean; class-C restriction applied; outcome robust to the one
interpretation fork, which I have flagged for Ayur.

---

### 2026-07-16 — P3 audit (A-AUX) — **SIGN-OFF (binding)**

Standard P3 protocol (not blind): cohort resolution spot-check, ≥30-floor arithmetic,
HPD-complaints dataset-ID verification-logged check, plus LEAD's asks — reproduce 377
from the parquets, assess the h4mf-f24e authority deviation (binding call), check the
version-choice logic. Independent re-derivation in `scratchpad/audit_p3.py`.

**377 re-derived from parquets — EXACT match, every cell:** HSP 200 rows (4×50, all
Active, 0 discharges, 197 distinct lots / 199 BINs); waterfall class-C→in-HSP **7,810**
→ −3,944 before program_start → −0/0 coverage → −233 off-season → **3,633 eligible**;
**zero-311 @W30 = 377** (10.38%, 95 distinct lots); Oct–Jan subset 223/2,214;
(bbl,day)-dedupe 244. Association = P2 rule (W=30, inclusive, calendar-date, int64 bbl,
class-C), Amendment-3 coverage eligibility applied (0 exclusions — HSP inspections sit
well inside coverage). Membership from the authority dataset's earliest program_start
per lot; my re-derivation used the same and matched.

**Floor arithmetic:** §4 floor = 30. 377 ≥ 30 → **PASS** follows mechanically. Robust:
both sensitivity readings clear it (Oct–Jan cadence 223 ≥ 30; (bbl,insp)-dedupe 244 ≥
30) — the PASS side does not depend on the "program seasons" interpretation.

**HPD-complaints dataset-ID verification — LOGGED (protocol requirement met):**
PROVENANCE P3 section records all three candidate IDs with live status —
`uwyv-629c` and `a2nx-4u46` login-walled/retired, `ygpa-z7cr` LIVE (2026-07-15) but
excluded by Amendment 1 item 2 — explicitly noted "logged BEFORE choosing the version."

**Version-choice logic — CORRECT.** Amendment 1 item 2 excludes the merged HPD
Complaints-and-Problems dataset (ygpa-z7cr) from phase-0 use regardless of liveness;
A-AUX verified it live but did NOT pull it — exclusion APPLIED, not reinterpreted. With
two legacy IDs retired and the merged one amendment-excluded, "no HPD complaints dataset
usable in phase-0" holds → §4's 311-only branch runs, labeled, with the correct
upper-bound caveat (events may carry an HPD-direct trail invisible to 311). Sound.

**DEVIATION RULING (binding) — h4mf-f24e as membership/BBL authority: CONFORMANT-WITH-
DISCLOSURE, not a defect.** §4 named PDFs only; A-AUX (a) downloaded + parsed all four
nyc.gov PDFs (the §4-named source, 50 rows each), (b) ran the §4 address→BBL-via-PLUTO
resolution independently and REPORTED its rate (171/200 = 85.5%), (c) cross-checked PDF
↔ dataset membership (199/200 exact; the 1 miss a CLAREDON/CLARENDON spelling variant of
the same building), (d) used the official same-publisher machine-readable dataset as the
BBL authority only where validated — where both the PLUTO resolver and the dataset give a
BBL they agree 171/171 (0 disagreements), and all 200 final BBLs exist in the P1 PLUTO
lot universe. This STRENGTHENS §4 (raises BBL coverage 85.5%→100% with zero conflict and
an official cross-validated source) rather than circumventing it; fabricates nothing
(Rule 1); dataset verified live + logged (Rule 5); deviation disclosed in checkpoint,
PROVENANCE, and agent log. The lower independent resolution rate is transparently
reported, not hidden behind the 100% dataset coverage. Ruled conformant.

**Storage:** data/raw = 90.7 MB ≪ 2 GB (Rule 6) ✓.

**VERDICT: SIGN-OFF.** 377 and the full waterfall reproduce exactly; floor PASS is
mechanical and robust; HPD verification logged; version-choice logic sound; the one
deviation (h4mf-f24e authority) ruled conformant-with-disclosure.

---

### 2026-07-16 — P4 audit (A-AUX) — **SIGN-OFF (binding)**

P4 protocol: (1) no gating language; (2) Census key never printed anywhere;
(3) exclusions logged not imputed. Plus raster check and a no-fabrication
reproduction (`scratchpad/audit_p4.py`). P4 gates nothing (§5 descriptive).

**(1) No gating language — PASS.** The only `verdict`/`gate` tokens in the checkpoint
are the two disclaimers ("Descriptive only — this probe gates nothing; no verdict
appears here"). Grep for GO/GO-DEGRADED/KILL/HOLD/PASS/FAIL/DEGRADE/threshold/kill-gate
applied as a decision → none. §5's question is answered explicitly "as DESCRIPTION,"
with "No conclusion about extrapolation feasibility is drawn here — that belongs to the
spec phase." Conforms.

**(2) Census key never printed — PASS (definitive).** Code review: key read from `.env`
via dotenv, used only inside ACS URL params passed to `_get` (which never prints); no
print/log statement emits it; credential-failure message names the variable, not the
value. Value-scan (sandbox disabled so dotenv could load the real 40-char key + 25-char
Socrata token): NEITHER value appears anywhere in the repo (excl .env/.venv/.git) —
checked checkpoint, code, stats, SVG, all agent logs, process_log, PROVENANCE, and every
data/ file including the ACS parquet cache. Literal `key=` absent from every artifact.
No leak.

**(3) Exclusions logged not imputed — PASS.** Income Census sentinel −666666666 → NaN
(not imputed); zero-household tracts → LEP undefined → excluded; buildings without
geo/income/LEP → labeled "(uncovered)" and COUNTED (excl_no_pluto_geo 1,209 /
excl_no_cd_income 0 / excl_no_lep 14); unit-join unmatched → "unmatched" label, counted
(1,043); conflicting-unitstotal bbls excluded + counted (0). Terciles computed only over
covered rows; uncovered rows get a label, never a fabricated tercile. The only `fillna(0)`
is the definitional zero-complaint count (a bbl absent from 311 truly has 0), not
imputation. No covariate value is invented.

**Raster check (Rule 6) — PASS.** No raster files anywhere under outputs/ or data/
(png/jpg/tif/gif/bmp/webp). Figure is a genuine vector SVG (`file` confirms;
936×288pt), with ZERO embedded raster (no data:image / <image> / base64). Nothing
raster touches disk.

**No-fabrication reproduction (Rule 1) — EXACT:** universe 181,863; zero 114,890
(63.2%); positive 66,973; 311-bbls-outside-spine 26,921; conflicting-units 0;
units-unmatched 1,043; no-PLUTO-geo 1,209 — all reproduce from the parquets. Overlap
stats internally consistent (cells_both 146 + zero_only 1 + pos_only 1 = 148 = occupied;
zero 106,231/106,232 → the 1 zero-only building; pos 65,508/65,513 → 5 in the pos-only
cell). The 63.2%-this-window vs WFF ~70%-own-window comparison is framed "reported, not
reconciled" — descriptive, no reconciliation claim, no causal language.

**VERDICT: SIGN-OFF.** No gating language; Census key provably never printed; exclusions
logged not imputed; no raster on disk; headline numbers reproduce exactly. This is the
last probe stage; the memo pass follows.
