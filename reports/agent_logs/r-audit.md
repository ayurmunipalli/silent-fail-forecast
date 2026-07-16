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

---

### 2026-07-16 — MEMO audit (LEAD) — **SIGN-OFF (binding)** — final stage

Memo protocol: thresholds quoted verbatim; verdict consistent with signed-off cells;
no recommendation/adjudication language; cites only signed-off content; sign-off/commit
table vs git + my records; deviations list vs the record.

**Thresholds VERBATIM — PASS (character-level, programmatic).** All six quoted blocks
are exact substrings of `phase0_probe.md` (whitespace-normalized for line wrapping):
§1 GO ("at least channel (a) passes; spec drafting proceeds."); GO-DEGRADED fragment
("(a) passes, (b) fails"); the full KILL-THRESHOLD block ("the gate evaluates at
**W = 14**: … the duplicate channel fails at the gate."); Amendment-1 escalation
("FAIL@14 ∧ PASS@30 → **HOLD**"; "FAIL@both → KILL. PASS@14 → GO on channel (a)."), with
the elided parenthetical honestly marked "[...]"; §4 floor ("channel (b) is usable …
iff ≥ **30** … cohort-seasons combined."). No restatement or adjustment.

**Verdict consistency — PASS.** GO follows mechanically from the signed-off cells:
channel (a) PASS@14 (median 4 ≥ 2, n=76,217) AND channel (b) PASS (377 ≥ 30) → GO
(not GO-DEGRADED, which needs (b) to fail; not HOLD/KILL, ruled out by PASS@14). All
cited cells (gate 4/6/76,217; lag 9/19/26; 377 with 223/244 robustness; P4 148/146,
106,231/106,232, 63.2%, medians 3/8, income $85,263/$79,943) match the signed-off P2/
P3/P4 checkpoints exactly. Nothing newly computed; no unsigned source.

**No recommendation/adjudication language — PASS.** The memo states the branch and
repeatedly reserves adjudication to Ayur (header lines 7–8; closing 105–108: "recommends
nothing beyond stating the pre-committed branch that fired … its adjudication (including
whether spec drafting proceeds) is Ayur's alone"). "spec drafting proceeds" appears only
inside the verbatim §1 quote, not as the memo's own recommendation. Stating GO is the
memo's required deliverable (probe §7 #5); the GO branch is mechanical (no adjudication
needed to select it), and final adjudication is explicitly Ayur's. Conforms.

**Sign-off / commit table — PASS.** db4e24d (P1) / ce97efe (P2) / eb48b48 (P3) /
f75fb13 (P4) all match the git log and my ledger; per-stage result descriptions
(SIGN-OFF, blind max-abs-diff 0 for P2, etc.) accurate. Bootstrap folded into the P1 row
is correct — my single P1 sign-off covered the recomputed bootstrap sha256s + the pull.

**Deviations list — PASS, matches the record.** Items 1–4 (Amendment 3; heat-season
scoping non-blocking flag with median 4↔3; h4mf-f24e conformant-with-disclosure; class
B+C superset) are exactly my logged flags/rulings. Item 5 (blank signature block vs
APPROVED header) is my READY flag AND its clause "Ayur has stated he will initial it" is
backed by the record — process_log entry 25 (AYUR → LEAD, 2026-07-16 04:05): "Ayur to
initial signature block." No unbacked attribution.

**VERDICT: SIGN-OFF.** Thresholds verbatim; GO consistent with the signed-off cells and
mechanically derived; no recommendation/adjudication overreach; table matches git + my
records; deviations match the record. The memo is clear to commit; adjudication is
Ayur's alone. This closes the phase-0 R-AUDIT chain (P1, P2, P3, P4, memo — all SIGN-OFF).

---

# BUILD PHASE

## 2026-07-16 — S1 audit (A-DATA): all pulls, 311 union refresh, spine verification

**Materials audited:** `reports/agent_logs/a-data.md`, `data/PROVENANCE.md`
(S1 + continuation entries), `data/s1_stats.json`, `src/s1_pull.py`, the raw
caches in `data/raw/`, the read-only R4 imports. **Method:** every number
re-derived by me from the parquets (`.venv/bin/python`); no a-data figure taken
on faith. Live network checks run unsandboxed (metadata API + count probes are
not on the sandbox allowlist); the `.env` read is the recorded phase-0 mechanic.
Token never printed.

### Base S1 protocol

- **Live ID re-verification (Rule 5):** all 7 IDs hit live independently —
  `erm2-nwe9`, `76ig-c548`, `wvxf-dwi5`, `tesw-yqqr`, `feu5-w2e2`, `64uk-42ks`,
  `ygpa-z7cr` — live names all contain the expected keyword; `rowsUpdatedAt`
  reproduced (erm2-nwe9 2026-07-16, 76ig 2025-12-24, wvxf 2026-07-15, tesw/feu5
  2026-06-01, pluto 2026-05-28, ygpa 2026-07-15).
- **311 union arithmetic + dedupe:** current 1,645,614 + archive 93,022 =
  1,738,636; dedupe on `unique_key` = **0**; null-bbl 7,123 (0.4097%); deliverable
  1,731,513 — and the on-disk deliverable is exactly 1,731,513. Range
  2019-06-01 00:17:18 … 2026-07-13 23:43:26. All reproduced from the caches.
- **Both seam diagnostics:** Seam A (2019-12-25..2020-01-07) reproduced daily,
  identical to the recorded values; no gap/pileup. Seam B (refresh edge)
  reproduced: late arrivals 0, disappeared 0, old-pull rows = new-pull rows
  (1,645,614 = 1,645,614).
- **Spine coverage vs WFF committed report:** import sha256
  `1c9be931…74eb` matches; schema `[bbl_n, season, label_c, label_bc]` exact;
  1,624,255 rows / 181,863 BBLs / seasons 2017–2025; per-season (rows, pos_c)
  match WFF's `_s1b_frozen_labels.json` **9/9**, all recomputed.
- **sha256s:** all three R4 imports match the bootstrap PROVENANCE entry.

### Five disclosed ledger items — all cleared

1. **Violations floor 2017-10-01.** Cache floor is exactly 2017-10-01
   (max 2026-07-14); 149,585 rows, class B=2/C=149,583, other-class 0, null-bbl
   209; **all 149,585 rows match the frozen text whitelist, 0 violating.**
   Dual-floor comparison confirmed: phase-0 cache holds 128,121 rows at floor
   2019-06-01. Justification sound — WFF family-1 `s2_features.py` consumes
   whitelisted violation rows from 2017-10-01; the narrower phase-0 cache cannot
   feed the WFF-recipe frame. Acquisition-only judgment, disclosed.
2. **ygpa-z7cr 7-part date split.** Disjoint (cross-part duplicate `problem_id`
   = **0**; every part's `received_date` verified inside its half-open bound);
   exhaustive (part sum 1,754,951 = deliverable = **live server total**);
   per-part counts = **live server-side year probes exactly** (re-probed now,
   zero drift incl. the 2026 bucket); assembly deterministic (deliverable
   rebuilds byte-identically from the parts); whitelist = all HEAT/HOT WATER.
   Amendment-1 boundary documented in the script docstring + PROVENANCE; at S1
   this is a raw cache only — no likelihood contact is structurally possible.
3. **Two external kills.** No partial/corrupt artifacts: no `.tmp/.part/.lock`
   files, all 22 raw parquets open and report row counts, 7 ygpa parts +
   deliverable all intact. Pulls write parquet only on completion — consistent
   with the clean disk state.
4. **Unsandboxed `.env` mechanic (Rule 2).** Socrata token present (len 25);
   its literal value appears in **no** repo file — code, logs, `s1_stats.json`,
   PROVENANCE, agent logs — nor in any binary data file. Census key (len 40)
   likewise absent. Script loads via `dotenv_values`, injects only as a header,
   never prints. Token not printed anywhere in this audit.
5. **Seam-B zero-accrual.** The current-side refresh contains **0** rows with
   `created_date` after 2026-07-13; old/new counts identical every day
   2026-06-30..07-13; late arrivals 0, disappeared 0. The diagnostic genuinely
   supports "erm2's 07-15 update added no heat rows after 07-13" (July
   off-season). Reported as-is, correctly.

### Additional checks

- **Storage vs 2 GB:** live total data/+imports/ = 341,566,718 B (341.6 MB) ≪
  2 GB. The 4,065-B delta vs the recorded 341,562,653 is the disclosed benign
  self-count artifact (`s1_stats.json`, 5,325 B, counting itself; guard measures
  before the file is written). Not a defect.
- **Idempotency:** both regenerated deliverables (`c311_heat_complaints`,
  `hpd_complaints_heat`) rebuild **byte-identically** (sha256) from their source
  caches by the script's own assembly semantics.
- **Registrations distinct-BBL = frozen spine universe:** verified as **set
  equality** — 181,863 = 181,863, 0 in reg∖spine, 0 in spine∖reg.
- **Season 2026-27 sanctity (Rule 3, spec §4):** structurally clean — ygpa has
  **0** rows with `received_date ≥ 2026-10-01`; every pull ends pre-season
  (max created 2026-07-13, max received 2026-07-15, max inspection 2026-07-14);
  no 2026-27 window in any filter. The bright line is intact.

### Observational note (not a defect)
- `a-data.md`'s ID table records `erm2-nwe9` rows-updated as 2026-07-15;
  `s1_stats.json` and the live API show 2026-07-16 — a one-day tick of the
  dataset's server-side metadata between log authoring and the stats write.
  Zero effect on pulled data (max created 2026-07-13; seam-B zero accrual).

**VERDICT: SIGN-OFF.** Every number re-derived and reconciled; live IDs and
live ygpa year-probes re-verified; all five ledger items cleared; storage,
idempotency, set-level spine/registration identity, credential hygiene, and
2026-27 sanctity all pass. No fabrication, no silent edits, no Rule-9 condition.
