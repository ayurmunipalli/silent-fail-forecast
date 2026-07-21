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

## 2026-07-16 — G1 gate-packet audit (LEAD): outputs/checkpoints/g1_packet.md

Gate-packet protocol (numbers traced to checkpoints; no recommendation language).
Sources cross-checked: my S1 section above, `a-data.md`, `s1_stats.json`,
`hyperparam_grid.md` (status PROPOSED — the legitimate source for the grid
section, which presents the proposal for approval), `model_spec.md` Amendment 1,
`process_log.md` ledger, and git.

- **(1) Number tracing — all clear.** §1 S1 figures reproduce my signed-off S1
  section exactly (IDs 7/7; union 93,022+1,645,614=1,738,636, dedupe 0,
  deliverable 1,731,513, range …2026-07-13; spine 181,863 set-equal / 9-of-9;
  pulls 149,585 @2017-10-01, ctx 2,012,740, contacts 782,024, PLUTO 858,602,
  ygpa 1,754,951 in 7 disjoint parts, dup 0; storage 341.6 MB; dup-flag Y
  761,130/43.4%; 0 rows ≥ 2026-10-01). §2 grid figures reproduce
  `hyperparam_grid.md`: net Cartesian 2,592 (3·2·2·4·3·2·3·3 = 2,592, verified),
  randomized n=60 seed 42; B4 6,561 / 59,049; clip-floor {0.02,0.05,0.10};
  180 configs × 5 folds (v ∈ 2021-22…2025-26); batch 8192 / 200 ep / patience
  20; λ, u*, μ₁, μ₂ candidate sets verbatim; criterion-3 T/α/W=30 faithful to
  grid §7. §3 traces to Amendment 1 + ledger B7–B10. Commit `fcbdc81` exists and
  contains S1 artifacts + Amendment 1 + my S1 sign-off (verified via git). Ledger
  B7–B10, B21, B23 all present and support the cited claims.
- **(2) No recommendation language.** Packet states criteria and contents only;
  header explicitly "recommends nothing. Adjudication is Ayur's." No GO/approve
  nudge anywhere. ("audited sound", "verified genuine" report audit-trail status
  of disclosed items, not a gate recommendation — acceptable.)
- **(3) FLAG faithful, non-resolving.** The spec-§12 ("G1 = data/features +
  leakage sign-off") vs plan-§2/§3 (G1 between S1 and S2; leakage gated inside
  S2) conflict is stated accurately; cites spec > plan; says "flagged, not
  resolved"; lays out the plan-sequencing consequence (clears DATA+GRID+R-A)
  while deferring to Ayur ("unless Ayur re-scopes"). Presents the fork, does not
  pick it. The packet's DATA+GRID+R-A scope matches plan §3 step 4's explicit G1
  definition — building on the plan's operative definition while flagging the
  broader spec reading is the correct handling.
- **(4) No threshold misstated.** Criterion-3 pass (T > 0 AND one-sided exact
  sign test, α = 0.05) compressed faithfully. §10 criteria-1/2 margins (1.35×,
  0.90×) are correctly NOT restated (out of G1 scope) — no misstatement risk.
  Storage budget 2 GB correct.
- **(5) Complete.** All three plan §3 step-4 components present: §1 S1 coverage,
  §2 grid proposal, §3 R-A resolution.

**VERDICT: SIGN-OFF.** Every number traces to a signed-off source (or the
PROPOSED grid it is presenting); no recommendation language; the gate-scope
FLAG is faithful and unresolved; no threshold misstated; all three required
components present. The packet is clear to reach Ayur; adjudication is Ayur's.

## 2026-07-16 — S2 audit (A-FEAT): two feature frames

**Materials:** `data/processed/features_b3.parquet` + `features_main.parquet`,
`src/s2_features.py`, `s2_feature_inventory.md`, `s2_stats.json`, `a-feat.md`,
PROVENANCE S2 entry, S1-audited caches, read-only WFF `src/s2_features.py` +
`data/processed/features.parquet` + `data/raw/*` (reference only — nothing
written there). **Method:** every claim re-derived from the parquets; the B3
frame compared cell-by-cell to WFF's frozen frame; family-6/7 windows
recomputed from raw. `.venv/bin/python`, local only.

### Non-leakage checks
- **Frame structure:** both frames 1,624,255 rows, seasons 2017–2025, 0 duplicate
  (bbl,season) keys; B3 columns are exactly the 30 WFF `feature_names` + keys +
  label_c; main = 30 + 11 (c6_) + 8 (c7_) = 49. Family counts reproduce
  (8/10/3/7/2 + 11 + 8).
- **B3 fidelity vs WFF frozen frame:** keys and label_c identical on all
  1,624,255 rows; **26/30 feature columns bit-exact on every row.** The 4
  differences are all on **one building (BBL 1012410023)**: `ctx_c_prior1`
  (season 2022), `ctx_c_cum` (2022–25), and the two `ctx_total_*` that contain
  them — the exact prior1/cum season signature of one added class-C source row
  in the calendar-2021 bucket. Recipe matches WFF `s2_features.py` line-for-line
  (families 1–5, `season_of`/`norm_txt` verbatim); WFF's own violations cache
  also floors at 2017-10-01, so `viol_cnt_*` legitimately match.
- **Idempotency:** reran `s2_features.py`; both frames + `s2_stats.json`
  reproduce the recorded sha256 **byte-identically** (`09f8e94d…`, `477d3079…`).
- **Duplicate-flag both-ways:** reproduced from the frame — covered rows
  1,086,842; Σevt_all 1,254,133; Σevt_dedupN 699,747; mean per-building Y-share
  0.1568. No leakage (all inside the pre-cutoff prior-season window); documented
  faithfully; nothing dropped.

### Disclosed deviations D1–D4
- **D1 genuine source accrual, NOT a recipe defect:** our S1 ctx cache holds
  class-C count **8** for (BBL 1012410023, yr 2021); WFF's ctx cache holds **7**.
  The +1 lives in the source aggregate; the recipe faithfully reproduces each
  (our B3 `ctx_c_prior1`@2022 = 8.0, WFF = 7.0). Single row accrued between the
  07-14 and 07-16 pulls. Confirmed genuine.
- **D2 local reproduction of WFF s1d server-side aggregate:** family-3 columns
  (`c311_available/_prior1/_prior_cum`) are among the 26 bit-exact columns vs
  WFF's frame; P311 matrix capped at 2020–2024 so the union's 2019 archive rows
  are structurally excluded. Reproduction is faithful.
- **D3** (ctx `yr`/`n` string-on-disk vs the "Int64" note): coerced with an
  assert on zero parse loss; values identical (fidelity match). Benign.
- **D4** (apartment free-text noise): normalization is UPPER/strip/collapse only,
  no fuzzy merge; `c7_apt_share_ps` left uncapped and visible. A disclosed
  measurement property, not a defect.

### Amendment-1 boundary
- The B3 frame contains **zero** `c6_`/`c7_` columns; ygpa (`hpd_complaints_heat`)
  is read only into the eight `c7_*` columns; the 311 union deliverable is the
  sole complaint source for families 3 and 6. ygpa is structurally confined to
  family-7 features — no path into anything a loss will consume.

---

### TEMPORAL-LEAKAGE SIGN-OFF (binding, Amendment 2; own subsection)

Every feature's timestamp lineage was traced against the Oct-1-`sy` cutoff:

- **Season-indexed (families 1, 5):** read only seasons `s < sy` (end May 31
  `sy` < cutoff); rolling state (`last_pos`, `cum_*`, `own_cum_*`) updates only
  AFTER season `sy` is emitted — verified in code. `portfolio_loo_rate` uses
  prior-season label aggregates with the index building subtracted (LOO, no
  self-leak).
- **Calendar-year (families 2, 3):** read only `yr ≤ sy−1`; the wide matrices
  carry columns **2014–2024 / 2020–2024** — a `yr == sy` (or 2025) read is a
  KeyError, i.e. **structurally impossible, not merely avoided**. Calendar
  `sy−1` ends Dec 31 `sy−1` < cutoff.
- **Timestamp-windowed (families 6, 7):** every slice goes through `win()`,
  which **hard-asserts `hi ≤ cutoff`**; all windows have `hi ∈ {Jun 1 sy,
  cutoff}` ≤ cutoff. Empirically confirmed on the latest dev season 2025: the
  max timestamp entering any window is **2025-09-30 23:57** (c6 t365) /
  **2025-05-31 23:42** (c7 ps) — strictly before the 2025-10-01 cutoff.
- **Masks NULL not zero (spec §2):** per-season checks — masked seasons are
  **all-NaN, zero literal-zeros** (e.g. `c311_prior1`@2020: 180,157 rows all
  NaN; `c6_evt_ps`@2019, `c7_apts_ps`@2019 all NaN); available seasons carry
  **true zeros** for complaint-free buildings (`c311_prior1`@2021: 0 NaN,
  158,015 zeros). Aggregate NULLs reconcile to season arithmetic exactly (fam3
  717,570 = seasons 2017–20; fam6/7 ps 537,413 = 2017–19; t730 717,570).
- **Fam-6/7 unlock one season before fam-3:** reproduced from first-principles
  date arithmetic — fam-3 needs full calendar 2019 (floor 2019-06-01 leaves it
  uncovered → masked through 2020-21), while the prior-season window Oct 2019–May
  2020 is fully covered → fam-6/7 available from 2020-21. Sound.
- **B3-frame values recomputed from raw:** `c6_evt_t365`@2025 agrees with the
  frame on **all 181,863** buildings; `c7_apts_ps`@2025 distinct-apartment counts
  match on spot-checked buildings.
- **Target-season sanctity:** both frames assert `max(season) == 2025`; **0 rows
  ≥ season 2026** in either frame; the spine has no 2026 season. Season 2026-27
  is structurally absent, not merely untouched.
- **C1/C2 ruling (flagged for R-AUDIT):** the current-vintage PLUTO (family 4)
  and registration/owner (family 5 `portfolio_size`) snapshots of slowly-varying
  STRUCTURAL/ownership attributes are **ACCEPTED**, consistent with WFF's
  R-LEAK precedent — they encode no post-cutoff EVENT information; the
  event/label-derived signals (`portfolio_loo_rate`) are properly time-indexed.

**LEAKAGE VERDICT: SIGN-OFF.** No Oct-1 violation on any feature; target-season
reads are structurally impossible; masks are NULL-not-zero; the bright line
(season 2026-27) is structurally absent from both frames.

**S2 VERDICT: SIGN-OFF.** Fidelity 26/30 with the residual proven to be genuine
source accrual; both frames idempotent byte-identical; Amendment-1 boundary
structurally held; D1–D4 accurate; duplicate-flag both-ways faithful; leakage
sign-off (above) clean. No fabrication, no silent edits, no Rule-9 condition.

## 2026-07-16 — S3a audit (A-MODEL): baselines B0–B4 — **REJECT**

**Materials:** `src/s3a_baselines.py`, `s3a_baselines.md`, `s3a_stats.json`,
`s3a_work/*` (300 s1_prop + 300 s2_risk checkpoints, 5 rhat npz, guards.jsonl,
winners), `outputs/models/b4_*`, `a-model.md` M2, PROVENANCE, frozen
`hyperparam_grid.md`, WFF read-only `src/s3_baselines.py`. Method: every metric
re-derived from persisted data / from scratch; nothing on faith.

### Everything below is VERIFIED CLEAN (sign-off quality)
- **Baselines-before-primary:** NO S3b/primary code exists anywhere in the repo
  — `src/` holds only p1–p4, s1, s2, s3a; grep for encoder/two-head/torch/
  thinning returns nothing. Confirmed current repo state.
- **B3 tree-count:** 343 = 343 (assertion in code + re-derived from the loaded
  booster).
- **B3 fold metrics re-derived FROM SCRATCH** (frozen booster → predict on the
  B3 frame → AP via `average_precision_score`, p@250 via the seed-42 tie-key):
  all 5 folds match the checkpoint EXACTLY (AP to 6 dp; p@250 exact). Mean AP
  0.382286 reproduced.
- **B2 fold re-derived** (trailing-3 class-C, v=2025): p@250 0.808 and AP
  0.273389 both match.
- **Metric definitions consistent:** `average_precision_score` for pr_auc,
  LightGBM `average_precision` for internal AP/ES; **no trapezoidal PR-AUC**
  (no `auc()`/`trapz`/`precision_recall_curve` anywhere).
- **B0/B1/B2 port fidelity vs WFF `s3_baselines.py`:** `season_of`, metric
  helpers, B2 trailing-3, B1 logistic, B0 score all faithful; disclosed
  adaptations (dev window 2019+, explicit sort before tie-key, pandas-3
  categorical-safe MISSING fill, explicit allowed-set guard) are mechanics, not
  semantics. VAL {2021..2025} correct (2024/25 are DEVELOPMENT per spec §2;
  2026-27 is the held-out line).
- **B4 effort genuine:** stage-1 space 6,561 / stage-2 59,049; `sampled_configs`
  determinism reproduced (seed 42 → winners cfg 5411 ∈ prop sample, cfg 21485 ∈
  risk sample); 60×5 = 300 checkpoints present per stage. **Winners re-derived
  from the checkpoint files:** prop cfg 5411 mean AP 0.970318 (runner-up
  0.970312); risk cfg 21485 mean AP 0.386460 (runner-up 0.386295) — matches the
  reported near-ties; selection/tie-break logic reproduced. B4 artifacts:
  propensity 95 trees, risk 282 trees (both match).
- **B4 effort adjudication (edge-heavy winners on a FROZEN grid):** ACCEPTED.
  The grid is the Amendment-2 pre-registration (locked at G1); selection ran the
  full pre-registered search with genuine, checkpointed evidence, and picked the
  best config by the pre-registered metric. A pre-registered frozen grid with
  edge winners satisfies the effort check — the alternative (re-opening the grid
  toward the winners) would be post-hoc and is correctly refused. The n_estimators
  "edges" are non-binding (ES stopped at 51–162 / 163–433 ≪ the 400/1500
  ceilings). Re-scoping the grid, if wanted, is a dated Ayur decision at G2.
- **Stage-1 propensity proxy (grid §5 / Amendment 1):** target y_dup =
  1{in-season 311-union events ≥ 2} on label_c==1 rows — re-derived
  train_dup_rate 0.875032 matches; source is the **311 union** deliverable
  (via `insea311.parquet`), **no ygpa in the target path**. The B4 feature set
  DOES include the eight `c7_*` columns — this is Amendment-1 (i) (ygpa admitted
  AS feature family 7); the boundary constrains the propensity SIGNAL/target and
  the two-head loss, both 311-union-only here. Consistent, not a violation.
- **Clip-floor inertness:** per-fold train-R̂ mins 0.28–0.51; final-refit R̂ min
  **0.2366 > 0.10** → share_below_clip 0.0 (no weight ever clipped) — reproduced
  by reloading `b4_propensity_lgbm.txt` and predicting on dev.
- **B3 in-sample caveat fairly stated:** v∈{2021,2022,2023} correctly labeled
  WFF training seasons; out-of-sample folds (2024/25) cited with correct numbers;
  language stays descriptive; the binding comparison is deferred to G3. No
  cross-model claim exceeds validation-descriptive language.
- **ES-watches-v deviation:** the frozen `hyperparam_grid.md` §5 text does say
  "early stopping 50 on fold v"; honoring it over WFF's v−1 convention is a
  faithful reading of the pre-registration, disclosed, and applies equally to
  every tuned arm. lightgbm **4.6.0 = WFF's B3 version** (WFF
  `frozen_model_config.json` records 4.6.0) — verified.
- **Test-season sanctity:** 50 guard passes over 36 sites, min touched 2017 /
  max 2025, **0 guards touching ≥2026**; both frames assert max season 2025.

### DEFECT (the REJECT)
**`s3a_baselines.md` results table — "mean any-311 p@250" column does not
reconcile with the machine-generated `s3a_stats.json` (or the fold data I
re-derived from it).** The other three columns (mean AP, mean p@250, mean
zero-311 p@250) reconcile EXACTLY for all five baselines; only this column is
wrong, on every row:

| Baseline | md any-311 | correct (stats.json / re-derived) |
|---|---|---|
| B0 | 0.6608 | **0.6392** |
| B1 | 0.5936 | **0.5744** |
| B2 | 0.6736 | **0.6768** |
| B3 | 0.8368 | **0.8304** |
| B4 | 0.8224 | **0.8096** |

The code and `s3a_stats.json` are CORRECT (the `stage_report` docstring notes
the md is "authored separately from these numbers" — this is a hand-transcription
error in the checkpoint, not a modeling bug). But a checkpoint deliverable that
feeds the G2 packet must reconcile with its source; five non-tracing cells fail
that bar. **Fix:** correct the five any-311 cells in `s3a_baselines.md` to the
stats.json values above (no code change; no re-run needed). Then re-audit is a
one-column recheck.

### Minor note (fix in the same cycle; not the basis for the REJECT)
- The checkpoint's "IPW weights ran 1.0–4.2" slightly overstates the top: the
  max weight actually APPLIED (over positives) is **3.97** (min positive R̂
  0.2518). The 4.2 = 1/min(all-row R̂ 0.2366), but that minimum is a
  non-positive row that is never weighted. Tighten to ~1.0–4.0. The material
  inertness claim (no weight clipped) is unaffected and verified.

**S3a VERDICT: REJECT** — single documentation defect (any-311 column
mis-transcribed vs source) + one minor descriptive imprecision (IPW upper
bound). All modeling, search, winners, criterion-relevant metrics, ports,
guards, and Amendment-1 boundary are verified correct. No fabrication; the
machine source is right; the fix is a five-number correction to the checkpoint.

## 2026-07-16 — S3a re-audit (REJECT cycle 1 → **SIGN-OFF**)

A-MODEL applied the correction (M3). Re-verified per the stated re-audit scope:

- **Corrected column reconciles:** `s3a_baselines.md` any-311 cells now read
  B0 0.6392 / B1 0.5744 / B2 0.6768 / B3 0.8304 / B4 0.8096 — **exactly** the
  `s3a_stats.json` `mean_any311_p@250` values (and my prior from-fold
  re-derivation). The three headline columns are unchanged and still correct.
- **IPW wording tightened:** now "~1.0–4.0 (max applied weight over positives
  3.97)" — matches my re-derivation; the mislabeled 4.2 is gone.
- **Source integrity (not taken on trust — I had no recorded sha of
  `s3a_stats.json`):** the stats file is internally self-consistent
  (`per_season` → `summary_means` reproduced for every baseline × all four
  metrics), a fresh from-scratch B3 fold re-derivation off the frozen booster
  still matches `per_season` exactly (mean AP 0.382286), and both B4 winners
  still re-derive from the checkpoints (cfg 5411 / cfg 21485). The source was
  not altered — the fix corrected the doc to the source, the right direction.
- **No out-of-scope diffs:** all non-corrected checkpoint content preserved
  (343 assertion, winners, 0.9703/0.3865, 95/282 trees, guard 50/36, in-sample
  caveat numbers 0.4395/0.4216/0.4543/0.4339, clip-floor min 0.2366 / share 0).
  None of the old wrong values (0.6608/0.5936/0.8368/0.8224/"1.0–4.2") remain in
  the md, PROVENANCE, or process_log. Change is confined to the 5 md cells + IPW
  wording + the a-model.md M3 note.

**S3a VERDICT (post-correction): SIGN-OFF.** The sole defect is fixed and the
correction introduced nothing else; everything verified clean in the first pass
(baselines-before-primary, B3/B2 re-derivation, B4 effort + winners,
Amendment-1 boundary, clip-floor inertness, ports, guards, metric definitions)
stands. S3a clears.

## 2026-07-16 — G2 gate-packet audit: outputs/checkpoints/g2_packet.md

Gate-packet protocol. Cross-checked vs my r-audit.md S2/S3a sections,
`s3a_stats.json`, `hyperparam_grid.md`, `model_spec.md` Amendment 2, the ledger,
and git.

- **(1) §1 leakage subsection VERBATIM:** extracted my r-audit.md S2
  TEMPORAL-LEAKAGE subsection and the packet's quoted block, stripped the
  blockquote prefixes, and diffed — **character-identical, 43/43 lines, nothing
  elided.**
- **(2) §2 numbers trace:** the baseline table (AP / p@250 / zero-311 p@250)
  reproduces `s3a_stats.json` `summary_means` for all five baselines (rounded).
  The in-sample-caveat numbers (B4 0.440 vs 0.422 / 0.454 vs 0.434; zero-311
  0.164 vs 0.124) round correctly from my re-derived 0.4395/0.4216/0.4543/0.4339/
  0.164/0.124. Effort/clip-floor/guards/Amendment-1/sequencing all match my S3a
  section. Commit `07df605` exists, contains the S3a artifacts, its committed
  `s3a_baselines.md` carries the CORRECTED any-311 column, and its tree holds no
  S3b/primary code (src/ = p1–p4,s1,s2,s3a). Ledger B42–B48 all present and
  support the claims.
- **(3) §3 grid-lock matches Amendment 2:** the packet's "approved at G1 +
  ratified as pre-registration by Amendment 2 (commit 9eafc29) + G2 LOCKS it"
  matches Amendment 2 ("grid ... as posted at G1 and approved ... now the
  pre-registration"; "G2 = ... grid lock") and the grid doc's own §8 (G1
  approval freezes the candidate sets; winning configs additionally frozen at
  G2). Commit 9eafc29 verified.
- **(4) No recommendation language:** only the disclaimer "recommends nothing.
  Adjudication is Ayur's." No GO/approve/proceed nudge.
- **(5) Complete:** all three Amendment-2 G2 components present — §1 leakage
  sign-off, §2 baselines committed, §3 grid lock.
- **(6) Reject cycle accurate:** §2's "1 REJECT (5 hand-transcribed cells;
  code/stats correct) → corrected → re-audit SIGN-OFF with source-integrity
  re-verification; counter closed at 1" matches ledger B44–B48 and my r-audit
  record — neither hidden nor overstated.

**Observation (non-blocking, not a packet defect):** `hyperparam_grid.md` still
carries the stale status header "Status: PROPOSED … Not locked until Ayur
approves at G1," even though G1 approval landed via Amendment 2 / commit 9eafc29.
The packet does NOT propagate this — it accurately states the grid was approved
at G1 and locks at G2 — and the grid doc's substantive §8 agrees. Suggest LEAD/
A-MODEL refresh that one header line so Ayur isn't confused if he opens the doc
during G2 review. Does not affect the packet or the gate decision.

**G2 PACKET VERDICT: SIGN-OFF.** Leakage subsection is a character-faithful
verbatim copy; every §2 number traces; §3 grid-lock matches Amendment 2; no
recommendation language; all three components present; the reject cycle is
represented accurately. Clear to reach Ayur; adjudication is Ayur's alone.

## 2026-07-17 — B5 audit (A-MODEL): uncorrected retrained LightGBM (Amendment 3) — **SIGN-OFF**

**Materials:** `src/s3a_b5.py`, B5 appendix in `s3a_baselines.md`, additive
`b5_*` keys in `s3a_stats.json`, `b5_lgbm.txt` + `b5_frozen_config.json`,
`s3a_work/b5_risk/` (300 units) + `b5_winner.json` + `b5_table.md`, PROVENANCE
B5, a-model.md M5. Audited under the S3a protocol. Every number re-derived.

- **(1) Amendment-3 conformance (code path, not the claim):** `stage_b5` calls
  `lgb.train` on a plain `lgb.Dataset` with **no `set_weight`, no R̂, no IPW**;
  fold records carry no weight key. Objective is binary on `label_c`.
  `scale_pos_weight` is retained as an objective-level grid dim (part of B4's
  stage-2 grid), NOT propensity weighting — consistent with Amendment 3. Same
  frame (`features_main`), same folds (v∈2021–2025), same selection (mean AP /
  tie-break zero-311 p@250).
- **(2) Twin-by-index:** `b5_configs()` = `sampled_configs(RISK_DIMS)` — the B4
  stage-2 seed-42 draw, indices identical; I reproduced it: 60 configs, **cfg
  20928 present, zero operative-dim (9-dim) collisions**. clip_floor carried as
  inert metadata only (no code path). The pre-training statement exists in the
  checkpoint ("Clip-floor handling (stated BEFORE training)"). Matches ledger
  B59 approval.
- **(3) S3a surface integrity:** `s3a_baselines.py` **untouched** (no diff vs
  07df605); `s3a_stats.json` adds only `b5_*` keys — **no pre-existing key
  changed** (verified by key-level json diff); `guards.jsonl` is **append-only**
  (first 50 lines byte-identical to the committed version).
- **(4) Self-caught guard correction:** I counted `guards.jsonl` directly = **72
  passes / 42 distinct sites**, max season 2025, **0 firings ≥2026** —
  `b5_guard_assertions` states 72/42 (measured truth). The 62→72/42 correction
  is honestly recorded in PROVENANCE and M5 ("first draft hand-estimated 62,
  caught and corrected pre-commit — same lesson as the M3 transcription
  defect"); the count is an append-only cumulative (incl. idempotency reruns),
  disclosed via a `snapshot_note`.
- **(5) Machine-generated table:** `b5_table.md` appears **verbatim** inside the
  checkpoint appendix, and its values equal `s3a_stats.json` `b5_*` on every
  column (AP/p@250/zero-311/any-311 and all three per-fold lines). No hand
  transcription — the S3a transcription failure mode is structurally avoided.
- **(6) Winner re-derived from the 300 checkpoints:** cfg **20928**, mean AP
  **0.387016**, runner-up cfg 13411 AP 0.386791 (gap 0.00023) — matches
  `b5_winner.json` and the appendix. `frozen_n_estimators` = round(mean best_iter
  405.4) = 405; `b5_lgbm.txt` = **405 trees**; ES max 578 < the 800 ceiling
  (stopped short, ceiling non-binding). Boundary statuses as reported.
- **(7) Sequencing:** src/ = p1–p4, s1, s2, s3a_baselines, s3a_b5 — **no
  S3b/primary code exists**. Baselines-before-primary preserved.
- **(8) Delta reading within §11:** the B5−B4 deltas (+0.0006 AP / +0.0040
  p@250 / +0.0032 zero-311 / +0.0040 any-311, all re-derived to match)
  are read in the appendix and M5 as the spec-§11 named limitation
  (observed-label evaluation penalizes correction) "operating as predicted …
  no claim either direction (G3/§10 adjudicates against B3)." Stays
  validation-descriptive; no directional claim. Metric discipline intact
  (`average_precision_score` via the audited helpers; no trapezoidal).

**B5 VERDICT: SIGN-OFF.** Amendment-3-conformant (plain BCE, no IPW in the code
path); twin-by-index construction exact with zero collisions; the signed-off
S3a surface is untouched and the new keys are additive; the guard mis-estimate
was self-caught and honestly corrected to the measured truth; tables are
machine-generated and reconcile; winner and artifacts re-derive; no primary
code; delta reading stays within §11. No fabrication, no Rule-9 condition.

## 2026-07-17 — S3b blind loss re-derivation, STEP 1 (BLIND; pre-dispatch)

Per the S3b protocol step 1, timed before A-MODEL's S3b code exists.
**Structural blindness proof:** at this write there is no `src/s3b_primary.py`
(nor any s3b file tracked in git) — my implementation provably predates the
audited code. I have NOT read A-MODEL's S3b code, checkpoints, or log M6+.

**Artifact:** `reports/agent_logs/r_audit_blind_loss.py`
**sha256:** `52f678dac7ce1624e78788c01a6dbca8f63f901c40040f3cd41569676b5d37c8`
Implemented from `model_spec.md` §3 + locked `hyperparam_grid.md` §3/§4 ALONE.
Runs (synthetic self-test executes): BCE(Y,F·R) with R=1−(1−p)^min(u,u*);
λ·binomial-NLL(counts | head p, building-season, complaint-positive rows);
Ω₁=μ₁·mean[(logit p−logit p̄)²]; Ω₂=μ₂·mean[max(0,F(x)−F(x+δ))²]. All terms
parameterized over the open axes so STEP 2 can identify which reading
reproduces A-MODEL's persisted per-term values.

**Spec-underdetermination flagged in the artifact (a checkability finding for
Ayur at FREEZE regardless of agreement):**
- **(A) central:** the auxiliary binomial's success parameter is not pinned —
  θ=R (building detection via the u-link; my PRIMARY) vs θ=p (literal "under
  head p"). On synthetic inputs the NLL term differs ~4× between the two, so
  this is material, not cosmetic.
- **(B)** successes/trials roles + k>n: complaint multiplicity (the very signal
  identification-(i) invokes) routinely gives distinct-complaints > confirmed
  incidents, for which Binomial(n,·) is undefined; a plain binomial isn't
  reconstructible from the text (clip vs raw-k exposed).
- **(C)** binomial coefficient (constant in θ but not in the reported scalar),
  **(D)** mean vs sum reductions per term, **(E)** log/logit clamp ε — all
  exposed and defaulted, none spec-pinned.
- **(F)** p̄, u, and the Ω₂ subsample selection are not spec formulas — taken as
  inputs from A-MODEL's batch (their definitions being outside the spec is
  itself noted).

STEP 2 (reproduction on A-MODEL's fixed batch) and STEP 3 (code audit) await
LEAD's dispatch. Idle until then.

## 2026-07-17 — Session resume after external kill — READY, IDLE

Re-read `.claude/agents/r-audit.md`, `CLAUDE.md`, `model_spec.md` (FROZEN +
Amendments 1–3), `plan.md`, and this log in full before any action.

**Blindness re-verified at resume (not asserted — checked):**
- `reports/agent_logs/r_audit_blind_loss.py` sha256 recomputed =
  `52f678dac7ce1624e78788c01a6dbca8f63f901c40040f3cd41569676b5d37c8` — exact
  match to the STEP-1 ledger entry above; artifact unaltered by the kill.
- Its commit `1d2f3b4` stands in git history — the implementation provably
  predates any S3b code A-MODEL is now regenerating. Blindness remains
  structural, not merely procedural.
- I have read NO S3b artifact: not `src/s3b_primary.py`, not
  `outputs/checkpoints/s3b_work/`, not A-MODEL's log beyond M5. This holds
  across the session boundary; the kill destroyed no blindness property.

The written-in-advance checkability finding (auxiliary-NLL underdetermination,
axes A–F) stands as logged, unchanged, for the FREEZE packet. Note that A-MODEL
regenerating S3b from scratch does not weaken it: the finding is about the
SPEC's underdetermination, and it was committed before either S3b attempt.

STEP 2 and STEP 3 remain GATED on explicit LEAD dispatch. Idle.

## 2026-07-17 — S3b blind loss re-derivation, STEP 2 (fixed-batch reproduction)

Dispatched by LEAD (ledger B76). Authorized inputs ONLY: `model_spec.md` §3
(+Amendments) and `outputs/checkpoints/s3b_work/fixed_batch/`. STILL FENCED and
NOT read: `src/s3b_primary.py`, `s3b_primary.md`, `s3b_stats.json`, a-model.md
M6+, process_log B73+. Driver `scratchpad/audit_s3b_step2.py` LOADS the kit and
SELECTS among the pre-committed parameterizations of the committed artifact
`r_audit_blind_loss.py` (sha `52f678da…`, re-verified this session). No term of
the implementation was modified, extended, or reimplemented.

**Kit:** deterministic batch n=8125 (4096 NLL-eligible = label_c==1 ∧ k_raw≥1),
u*=25, λ=0.3, μ₁=0, μ₂=1, three training tags (t0_init, t1_epoch1, tE_final) +
tE_reload. Per-term float64, per-row F/p/R/q/F_pert persisted.

### Reproduced to float tolerance (every training point)
| Quantity | max |diff| | axis resolved |
|---|---|---|
| R = 1−(1−p)^min(u,u*) vs kit R | 1.1e-16 | structural link exact (u_raw≡u_capped here) |
| q = F·R vs kit q | 0.0 | — |
| **BCE(Y, F·R)** | **0.0** (all 3 pts) | **D: reduction = MEAN** (sum off by ~1e4) |
| Ω₁ raw over ALL batch rows | 1.1e-16 | **F: p̄ over full batch**, not eligible-only (elig-only off ~0.01–0.17) |
| Ω₂ raw over ALL batch rows | 3e-21 | **F: Ω₂ subsample = full batch** (elig-only off) |
| aux NLL **no-trunc** decomposition | 1.8e-15 | **C: binomial coeff INCLUDED**; mass success-prob = **p**; k=k_capped, n=u_capped, mean |
| kit `nll_logR_mean` vs my mean(log R)[elig] | 3.5e-18 | (diagnostic, see below) |
| kit `total` arithmetic identity | 0.0 | bce+λ·nll_mean+μ₂·Ω₂ internally exact |

Self-corrections vs my STEP-1 PRIMARY guesses (pre-committed, both among my
swept parameterizations, so selection — not a fix): **C** resolved to
include_coeff=**True** (I'd primaried False); **A** resolved as below (I'd
primaried θ=R).

### DIVERGENCE (reported verbatim per dispatch) — the operative NLL
The NLL that actually enters `total` is `nll_mean`, and **my committed
implementation cannot reproduce it under ANY of its pre-committed
parameterizations.** My closest (nll_no_trunc, exact) falls short of `nll_mean`
by exactly the kit's `nll_logR_mean` at every point:

| tag | my nll_no_trunc | kit nll_mean | gap | = kit nll_logR_mean |
|---|---|---|---|---|
| t0_init | 6.015399332260967 | 5.977159714749588 | −0.03824 | −0.038239617511381 |
| t1_epoch1 | 5.301005857691215 | 5.279236234614322 | −0.02177 | −0.021769623076895 |
| tE_final | 4.964091630115034 | 4.947727911874010 | −0.01636 | −0.016363718241025 |

Consequence: my independent `total` (using no-trunc NLL) exceeds kit `total` by
exactly λ·(−logR) = 0.01147 / 0.00653 / 0.00491 at t0/t1/tE. So `total` is
likewise not independently reproducible under my committed parameterizations.

### Divergence fully characterized (diagnostic, computed OUTSIDE my committed
### parameterizations — flagged as such, not a change to the implementation)
`nll_logR_mean` = mean over eligible rows of **log R**, R = 1−(1−p)^u, to
3.5e-18. Therefore A-MODEL's aux likelihood is a **ZERO-TRUNCATED BINOMIAL**:
NLL = −log[ Binom(k; u, p) / (1−(1−p)^u) ] = (−log Binom, my no-trunc) + log R.
The truncation normalizer P(k≥1) is exactly R — the u-link resurfaces as the
conditioning constant. Complaint-positive eligibility (k≥1 by construction)
makes conditioning on k≥1 the principled choice.

**This vindicates my STEP-1 checkability finding (axes A/B), it does not refute
it.** My axis-A binary (θ=R OR θ=p) was itself under-specified: the truth uses
BOTH — p as the per-unit mass parameter, R as the zero-truncation normalizer —
a third structure the spec §3 phrase "λ · NLL of observed complaint counts under
head p" does not pin down. The spec determines every term I could reproduce
(BCE, penalties, the binomial mass, coeff, grain, reductions) and is silent on
exactly the one place my implementation and A-MODEL's diverge (truncation). That
is the finding: the reported loss is spec-determined up to the truncation choice,
which is implementation-defined.

**In A-MODEL's favor (noted, not adjudicated):** the truncation was not hidden —
the kit persists `nll_logR_mean` and the full `nll_no_trunc`/`nll` decomposition
as separate terms, i.e. the choice is transparently exposed, and its arithmetic
is internally exact (decomposition + total identities close to ≤1e-15). Whether
the zero-truncated reading is the intended one is Ayur's to adjudicate at FREEZE.

**Also observed (relevant later, not the step-2 deliverable):** clamp-binding
counts all 0 (no p/q/trunc clamp fired); tE_reload term values are
byte-identical to tE_final — reload determinism holds on this batch (full freeze
bundle reloadability is a STEP-3 item).

STEP 3 (code read + full S3a-style protocol audit) awaits LEAD dispatch. Idle.

## 2026-07-17 — S3b blind loss re-derivation STEP 3 + full protocol audit — **REJECT**

Dispatched by LEAD (ledger B78); all fences lifted. Read: `src/s3b_primary.py`
(full), `outputs/checkpoints/s3b_primary.md`, `s3b_stats.json`, a-model.md M6,
PROVENANCE S3b, process_log B73–B78, the freeze bundle, the 300+21 unit
checkpoints, guards.jsonl. Every number re-derived independently
(`.venv/bin/python`, `scratchpad/audit_s3b_step2.py` + ad-hoc); nothing on faith.

### VERIFIED CLEAN (sign-off quality)
- **(a) Axes A1–A10 vs code + kit, disclosure completeness.** Step-2's
  zero-truncated-binomial finding is disclosed **in substance**: checkpoint
  axis 1 + loss line ("NLL = zero-truncated binomial", "−log(1−(1−p)^u), exactly
  −log R … proper conditioning on ≥1 event"), code `loss_terms` line 524–525
  (`logR = log((1−(1−p)^ue).clamp_min)`, `nll = −(comb+klogp+uklog − logR)`).
  The truncation I identified blind is explicitly the documented design, not an
  undisclosed choice. A2 u-source (1,254,587/0/12,022), n_eligible 42,787,
  k_exceeds-u by u* (14,309/11,298/10,358), pbar(all-dev,u*25)=0.5904 all
  re-derived EXACT. A3/A4 (Ω₁, Ω₂ over all rows; pbar=Σk/Σu train-eligible) and
  A8 (clamps, 0 binding on batch) confirmed by the step-2 reproduction.
- **(b) Sequencing.** src/s3b_primary.py is UNCOMMITTED (HEAD 1d2f3b4 = my blind
  step-1); at 07df605 (S3a) and 4959795 (B5) `git ls-tree` shows no s3b in src/
  — baselines-before-primary preserved in history. Only "killed session"
  reference in the code is the B68 regeneration provenance note (disclosure, not
  reuse). torch-2.13.0 reuse is a PyPI package, not killed-session work product.
- **(c) Locked-grid conformance.** space 2,592; n=60 seed-42 `rng.choice`
  reproduced; 60 unique idxs; winner cfg 2009 and runner-up 1961 both ∈ sample;
  decode of both matches. No off-grid config trained.
- **(d) Selection + near-tie.** Winner re-derived from the 300 search units:
  cfg 2009 mean AP(q) 0.3631432, runner-up 1961 0.3631290, margin **1.416e-5**.
  Rule = mean AP(q) primary, tie-break zero-311 p@250(F) only on EXACT AP tie,
  then idx. 2009's AP strictly exceeds 1961's → primary decides; tie-break never
  invoked though 1961 has higher zero-311 (0.0952>0.0912). Mechanically correct;
  honestly disclosed. E*=round(mean(2,12,10,6,18))=round(9.6)=**10** re-derived.
- **(e) 5-seed spread.** `spread_units` varies ONLY the winner config over seeds
  43–46 (no re-search); seed 42 = the search units themselves (disclosed reuse).
  Per-seed means re-derived EXACT for all five (AP range .3512–.3653, std .0056);
  VALIDATION-based, hyperparams fixed — spec §8 / Rule 10 honored, no test contact.
- **(f) Freeze bundle + INDEPENDENT reload.** Bundle sha256 bb4016b8… and
  frozen_config 90435616… match the checkpoint. **Independent numpy forward**
  from the state_dict (my own MLP/LayerNorm/sigmoid, NOT A-MODEL's torch code)
  on the fixed batch reproduces the persisted tE_final per-row F/p to **1.7e-16 /
  2.2e-16** → the bundle genuinely reloads to identical validation predictions.
  (A-MODEL's own float32 reload_verification = 0.0; the float32↔float64 gap to
  final_scores is ~1.3e-7, expected.)
- **(g)/(h) Sanctity + frame hashes.** guards.jsonl: **0 bright-line firings
  (≥2026)**, max season touched **2025**, **15 distinct sites** — all
  deterministic and correct. Both frame sha256s (477d3079…, 09f8e94d…) match the
  live files AND PROVENANCE; asserted in-code at prep (Rule-9 drift guard).
  Season 2026-27 structurally absent (spine ends 2025, asserted at load).
- **(i) torch 2.13.0** disclosed in checkpoint + a-model.md + stats versions;
  reuse ruled acceptable (package, not quarantined output); determinism
  self-proven by bit-exact reload.
- **(j) Storage.** data 355 MB + outputs 541 MB + imports 32 MB ≈ 928 MB ≤ 2 GB;
  design.npy 506,643,728 B (483 MB) regenerable-cache characterization accurate
  (deterministic from hash-asserted inputs), disclosed deletable at freeze.
- **(k) Machine-generated table.** `s3b_work/s3b_table.md` is written by
  `stage_report` from `summary`/`spread` and appears verbatim in the checkpoint;
  every cell equals `s3b_stats.json` — no hand transcription (S3a failure mode
  structurally avoided here).
- **(l) Trailing-B4 language.** Net trails B4/B5 on every observed-label
  validation mean, reported verbatim; §11 penalizes-correction caveat stated
  both ways; G3 named as the binding §10 comparison; no directional claim. Clean.

### DEFECT (the REJECT) — guard-pass count does not reconcile with its source
`s3b_stats.json` `guard_assertions.n_recorded_passes` = **233** (echoed in the
checkpoint line 164 "233 recorded passes … counts measured from the file
post-rerun" and a-model.md M6). The source `s3b_work/guards.jsonl` currently
holds **234** non-blank guard records. The committed deliverable does not
reconcile with its own source.

**Root cause (mechanical, in the code):** `make_capture()` (src/s3b_primary.py
line 922) calls `fold_tensors(FOLD_ALL)` unconditionally, and `stage_refit`
(line 1030) calls `make_capture` on EVERY `main()` invocation — including a
fully-complete idempotent rerun. `fold_tensors → block() → assert_no_test_contact`
**appends** a guard line each time. So guards.jsonl is append-mutated on rerun;
the count was 233 when `stage_report` first wrote `s3b_stats.json`, and A-MODEL's
own post-completion "idempotent rerun (ALL STAGES COMPLETE, verified)" appended
the 234th AFTER — which `stage_report` cannot pick up (it early-returns once
stats.json exists). I did NOT run the training pipeline this session; the drift
is entirely within A-MODEL's own runs.

**Two consequences, both stated inaccurately in the deliverables:**
1. The headline count 233 is stale vs the file (234) — a committed, packet-bound
   number that disagrees with its source (the S3a bar: deliverables must
   reconcile with their machine source).
2. The "idempotent rerun … recomputes nothing" / "counts measured from the file
   post-rerun" claims are inaccurate: guards.jsonl **is** mutated on every rerun,
   so the raw pass count is a non-reproducible append-only cumulative that will
   drift on any future rerun (including a fix rerun) — an exact committed value
   is structurally unkeepable.

A-MODEL hit this identical append-only-guard failure mode at B5 (62→72) and there
disclosed it with a "cumulative … post-rerun" snapshot caveat; that caveat was
**not** carried into S3b, and the number is already stale.

**Substance is unaffected:** the meaningful, deterministic sanctity facts — 15
distinct sites, max season 2025, **zero** ≥2026 firings — are all correct and
reproducible. This is a documentation/reconciliation defect on a non-load-bearing
count, NOT a modeling, selection, or sanctity breach. No retraining, no model
change.

**Fix (documentation + trivial hygiene; no re-run of training):** report the
deterministic guard facts (distinct sites / max season / bright-line firing
count) as the headline, and either (i) drop the raw cumulative pass count, or
(ii) label it explicitly an append-only cumulative snapshot (B5 pattern) and
reconcile the stated figure to the file — across s3b_stats.json, s3b_primary.md,
and a-model.md M6. Optionally make guards idempotent (dedupe on read, or stop
make_capture's unconditional re-touch) so the count stops drifting. Re-audit is a
one-item recheck.

### STEP-2 FINDING CARRIED FORWARD (not a defect; FREEZE-packet item)
The auxiliary-NLL truncation reading (zero-truncated binomial, normalizer R) that
my blind implementation could not reach is a resolution of a spec-§3
underdetermination (step-1 axes A/B). Per LEAD B78 it carries into the FREEZE
packet as a written finding for **Ayur's** adjudication (is zero-truncated the
intended likelihood?). A-MODEL disclosed it transparently; it is NOT a defect for
A-MODEL to change, and no code change is authorized by it.

**S3b VERDICT: REJECT** — single documentation/reconciliation defect (guard-pass
count 233 vs source 234; append-only-on-rerun not caveated; "idempotent
recomputes nothing" inaccurate for guards.jsonl). All modeling, loss
implementation (spec-pinned terms reproduced to float tolerance at step 2), grid
conformance, selection + near-tie mechanics, 5-seed validation-spread semantics,
freeze-bundle reloadability (independently re-verified to 1e-16), frame-hash
guards, storage, machine-generated tables, and §10/§11-bounded language are
verified correct. No fabrication; the machine pipeline is right; the fix is
doc-level. Step-2 truncation finding carries to FREEZE for Ayur.

## 2026-07-17 — S3b re-audit (REJECT cycle 1 → **SIGN-OFF**)

One-item re-audit per LEAD B83. Current source truth re-computed fresh from
`guards.jsonl`: **234 records, 15 distinct sites, max season 2025, 0 ≥2026
firings** (it did not drift further — the fix was applied by hand/doc, not a
training rerun).

- **(1) Four surfaces reconcile with the source.** s3b_stats.json
  (`n_recorded_passes_cumulative_snapshot.value` = 234; `n_distinct_sites` 15;
  `max_season_ever_touched` 2025; `n_2026plus_firings` 0), s3b_primary.md
  (L164–173), a-model.md M6 (L162–163) + M7 (L167–181), and PROVENANCE.md S3b
  (L532–539) all now headline 15 sites / max 2025 / zero ≥2026 firings with the
  raw count relabeled a 234-at-reconciliation append-only snapshot. All four
  match my fresh computation. The 4th-surface (PROVENANCE) echo of stale 233 that
  A-MODEL flagged was relabeled under the same LEAD-authorized doc-only correction
  (B81–B82), verified present.
- **(2) Snapshot semantics accurate.** All four surfaces state the mechanism
  correctly: `fold_tensors(FOLD_ALL)` in the fixed-batch capture path
  (`make_capture`, s3b_primary.py L922, called by `stage_refit` L1030) re-asserts
  and APPENDS on every `main()` invocation incl. fully-complete idempotent
  reruns → the raw count drifts upward; B5-lineage caveat (M5) cited. Matches the
  root cause I found at step 3.
- **(3) Deterministic facts assertion-derived/correct.** 15 / 2025 / 0 equal my
  independent fresh derivation from guards.jsonl exactly; the code's
  `stage_report` (L1207–1209) derives distinct-sites (sorted set) and max-season
  (max) by assertion, and those values match. NIT (not blocking): the
  "reconciliation script" M7 references is not persisted in the repo — but I
  assertion-derived the three facts myself from the source and they reconcile, so
  the claim's substance holds regardless.
- **(4) No out-of-scope diffs.**
  - `s3b_primary.py` UNCHANGED: its `stage_report` still emits the ORIGINAL
    guard_assertions structure (`n_recorded_passes: len(guards)`, `distinct_sites`,
    `max_season_ever_touched`) — which now DISAGREES in structure with the
    hand-reconciled stats.json. Had the code been edited to produce the new
    structure, they would agree; the divergence PROVES the fix was doc-only and
    the audited code surface is untouched. (Consequence, surfaced for
    LEAD/Ayur: a delete+rerun of stats.json would regenerate the OLD structure
    with a fresh drifted count, not the corrected snapshot; since `stage_report`
    early-returns when stats.json exists, the corrected hand-reconciled file
    persists. Accepted property of a LEAD-authorized doc-only edit of an
    uncommitted deliverable.)
  - Freeze bundle + config sha256 IDENTICAL (bb4016b8… / 90435616…).
  - Fixed-batch KIT byte-identical: re-ran my step-2 driver — bce-diff 0.0,
    nll_no_trunc exact, total-identity 0.0, R-link 1.1e-16 at t0/t1/tE + reload,
    same as the step-2 read.
  - winner.json unchanged (cfg 2009, mean AP 0.3631432).
  - Collateral check: committed B5 artifacts (`b5_lgbm.txt`,
    `b5_frozen_config.json`, `s3a_b5.py`) all UNCHANGED vs HEAD — the fix touched
    nothing beyond the four authorized doc surfaces.

**S3b VERDICT (post-correction): SIGN-OFF.** The sole reject-1 defect (guard-count
non-reconciliation) is fixed doc-only across all four surfaces with accurate
append-only-snapshot semantics and correct deterministic facts; the correction
introduced no code, model, or kit change (all byte-verified); everything verified
clean at the step-3 first pass stands. The step-2 auxiliary-NLL truncation
(zero-truncated binomial, normalizer R) carries forward as a written FREEZE-packet
finding for Ayur's adjudication — not a defect. S3b clears.

## 2026-07-17 — FREEZE gate-packet audit: outputs/checkpoints/freeze_packet.md — **SIGN-OFF**

Gate-packet protocol (numbers/shas traced to signed-off sources; no
recommendation language; nothing pre-resolved that is Ayur's). Cross-checked vs
s3b_primary.md, s3b_stats.json, s3a_stats.json, my own r-audit.md S3b sections,
PROVENANCE, ledger B77–B86, git.

- **(1) Freeze identity/shas trace.** cfg 2009 (w256/d2/do.15/λ.3/u*25/lr1e-3/
  μ₁0/μ₂1.0), 93,186 params, E*=10, seed 42; bundle sha `bb4016b8…`, config
  `90435616…`, recipe hashes `477d3079…`/`09f8e94d…` — all match my step-3
  re-verification. Reload claim faithful: A-MODEL float32 bit-exact 0.0 AND my
  independent numpy forward "≤2.2e-16" (my max was dp 2.22e-16) — both stated and
  distinguished correctly. Commit **054f136** exists, contains the 4 S3b files,
  and is on **origin/main** (pushed); "~2.5 months before Oct 1" correct for
  2026-07-17.
- **(2) Selection provenance.** n=60/2,592 seed-42; winner AP .3631432; runner-up
  1961 Δ 1.416e-5, tie-break correctly not invoked — all match my step-3
  re-derivation. No recommendation.
- **(3) Validation table vs signed-off records.** B4 .3865/.8096/.1104, B5
  .3870/.8136/.1136, S3b .3631/.7488/.0912 all reconcile with s3a_stats.json
  (`b5_summary_means` .387/.8136/.1136) and s3b_stats.json. B3 .3823/.830/.118
  rounds from source .3823/.8304/.1184; in-sample caveat carried (row label +
  "observed-label; spec §11 caveat applies"). §10.4 "two-stage ships if joint
  doesn't beat B4 at G3" is a faithful restatement of spec, not a recommendation.
  Spread .3512–.3653 / std .0056 matches. Weak-fold 2021-22 attribution correct.
- **(4) Blind-protocol summary accurate.** Step 1 1d2f3b4 / `52f678da…` pre-dates
  S3b code ✓. Step 2 "spec-pinned terms ≤1.8e-15" — accurate (my loosest was
  nll_no_trunc 1.8e-15; the rest tighter). "One divergence where §3 is silent" ✓.
  Step 3 "SIGN-OFF after 1 reject cycle (doc-only; no code/model change)" ✓.
- **(5) Adjudication items A–D, no recommendation / nothing pre-resolved.**
  A (truncation): states the zero-truncated reading, disclosure, my blind 3.5e-18
  match, and the A–F underdetermination lineage with the **B72 correction of
  B66's A–E** stated correctly; asks Ayur to rule whether it is the frozen §3
  interpretation (dated amendment per Rule 8 if so) — leaves the ruling open,
  does not declare it accepted. B (hand-reconciled stats structure): surfaced as
  the accepted-consequence class exactly as I logged it — a LEAD-lane operational
  call on an uncommitted file, presented for awareness, not forcing a ruling.
  C (reject cycle): 233-vs-234 append-only drift, doc-only four-surface fix,
  deterministic facts 15/2025/0 unaffected — matches my re-audit exactly.
  D (session-loss lineage): quarantine + regeneration + structural blindness/
  sequencing survival — matches B67–B70 and my step-3(b). None of A–D resolves a
  scientific/gate question reserved to Ayur.
- **No recommendation language:** header "no recommendation is made"; §6 states
  on-approval mechanics conditionally ("On approval"), no GO/approve nudge.

**Non-blocking cosmetic observation (NOT a defect):** the §3 table shows the B3
row at 3 dp (.830 / .118, carried at G2-packet precision) while B4/B5/S3b are at
4 dp (.8096 / .1104 …). No value is misstated (B3 source .8304/.1184 rounds
correctly and appears at full precision in s3b_primary.md / G2 packet), and the
direction is not obscured — B3 remains the strongest observed-label baseline
either way. Suggest uniform precision if edited; does not affect the packet or
the gate.

**FREEZE PACKET VERDICT: SIGN-OFF.** Every number and sha fragment traces to a
signed-off/committed source; the baseline+S3b table matches records with the B3
in-sample caveat carried; the blind-protocol summary states steps 1–3 accurately
incl. the step-2 divergence and the A–F/B72 axes lineage; adjudication items A–D
carry no recommendation language and pre-resolve nothing reserved to Ayur; the
reject cycle is disclosed accurately. Clear to reach Ayur; adjudication is
Ayur's alone.

---

# R-PILOT PHASE

## 2026-07-21 — RP0 audit: standing S2-class temporal-leakage protocol re-run at PILOT cutoff Oct 1, 2025 (Amendment 5) — **SIGN-OFF (binding)**

Dispatched by LEAD. Amendment 5 read in full before auditing. This is the S2
leakage protocol re-executed at the pilot cutoff; Amendment 5 pins that the
hash-pinned S2 frames are REUSED, so the audit re-verifies the load-bearing
lines rather than re-litigating the whole S2 (my 2026-07-16 TEMPORAL-LEAKAGE
SIGN-OFF stands as the base). Every check re-derived live with `.venv/bin/python`.

### Hash pins re-verified on disk (all four MATCH exact)
- `features_main.parquet` sha256 `477d3079…4734090` (35,404,008 B) ✓
- `features_b3.parquet`   sha256 `09f8e94d…f324fa09` (27,524,818 B) ✓
- `s3b_primary_seed42.pt`  sha256 `bb4016b8…c5c27126` (383,035 B) ✓ (frozen bundle untouched)
- `s3b_frozen_config.json` sha256 `90435616…0b0e5b2e0` (1,255 B) ✓ (frozen bundle untouched)

Frozen bundle committed at 054f136; both files git-tracked, unmodified. The
frames are BYTE-IDENTICAL to the S2 deliverables I signed off — so every S2
leakage property I established transfers unchanged; only the load-bearing
season-2025 lines are re-verified below at the pilot cutoff.

### (a) Frames-reused clause — season-2025 rows encode nothing on/after Oct 1, 2025 — **VERIFIED**
The pivotal pilot fact: the PILOT cutoff for the LATEST season (2025) is
Oct 1, 2025 — which is EXACTLY the build-phase per-target-season cutoff
`cutoff = pd.Timestamp(sy,10,1)` for sy=2025 (s2_features.py L345). The frames
are per-target-season by construction, so season-2025 rows were already built
to the Oct-1-2025 boundary. Re-verified per family:
- **Families 1, 5 (season-indexed):** for sy=2025 read seasons `s < 2025`
  (viol_lag1=season 2024 ends 2025-05-31 < cutoff; viol_cnt_prior*, ctx cum,
  portfolio_loo over `s ≤ 2024`). Rolling state (`last_pos`, `cum_*`,
  `own_cum_*`) rolls AFTER emit (L424–431) → prior seasons only; LOO subtracts
  the index building. No self/target read.
- **Families 2, 3 (calendar-year):** load-bearing lines L157/L182 build the
  matrices with `range(·, max(SY))` where max(SY)=2025 → **columns cap at 2024,
  no 2025 column exists**. For sy=2025 the reads are `m[2024]` / `P311[2024]`
  and cum over `y ≤ 2024`. A target-year (2025) read is a **KeyError —
  structurally impossible, not merely avoided**. Calendar 2024 ends 2024-12-31
  < 2025-10-01. Re-derived live: ctx_yrs max=2024, c311_yrs max=2024.
- **Families 6, 7 (timestamp-windowed):** every slice passes through `win()`,
  which hard-asserts `hi ≤ cutoff` (L106). For sy=2025 all window his ∈
  {2025-06-01 (ps), 2025-10-01 (t365/t730)} ≤ 2025-10-01. **Empirical live
  re-derivation from raw:** max `created` entering any season-2025 311-union
  window = **2025-09-30 23:57:03**; max `received` entering any ygpa window =
  **2025-09-30 23:55:56** — both strictly < 2025-10-01 (reproduces my S2
  finding exactly). The raw caches DO hold **347,061** 311-union and **350,512**
  ygpa rows dated ≥ 2025-10-01 (pulled in 2026); **all are structurally excluded**
  by the `win()` guard — the pilot-relevant proof that later-vintage data cannot
  reach a season-2025 feature. Masks NULL-not-zero unchanged (avail codes per
  season from s2_stats mask_coverage; season 2025 fully covered ps/365/730=1/1/1).
- **Availability masks:** target-season reads impossible by the column-cap +
  `win()` guard jointly; no NULL is a disguised zero (S2 finding, frames
  identical).
- **C1/C2 structural-snapshot ruling (family 4 PLUTO, family 5 portfolio_size):**
  current-vintage snapshots of slowly-varying structural/ownership attributes.
  My S2 ruling ACCEPTED these (no post-cutoff EVENT info; WFF R-LEAK precedent).
  It applies to the pilot UNCHANGED — the pilot alters only the fold plan, not
  feature construction, and season-2025's cutoff is identical to build-phase.
  **(a) VERDICT: PASS.**

### (b) Fold plan — selection/training has ZERO contact with season 2025 — **VERIFIED**
Re-executing the locked-grid selection over forward-chaining folds
v ∈ {2021,2022,2023,2024} (train ⊆ seasons < v, validate on v; never random
K-fold). Exact season sets (model-row dev floor = 2019 per spec §2; 2017-18/
2018-19 rows serve as lag-feature history ONLY, not training rows):
- **v=2021:** train {2019, 2020} · validate 2021
- **v=2022:** train {2019, 2020, 2021} · validate 2022
- **v=2023:** train {2019, 2020, 2021, 2022} · validate 2023
- **v=2024:** train {2019, 2020, 2021, 2022, 2023} · validate 2024

Max validation fold = **2024**; the union of all train∪validate seasons across
the four folds = {2019…2024}. **Season 2025 (=2025-26) is never loaded** in any
RP1 selection/training fold — held out for the single RP2 shot. This is the one
substantive delta from build-phase (which ran v up to 2025); the pilot simply
drops the v=2025 fold. Masked families 6/7 on train seasons 2019/2020 are
NULL-masked exactly as build-phase B4/B5 handled them — no leakage.
**(b) VERDICT: PASS.**

### (c) B3-as-is on season-2025 rows — no leakage — **VERIFIED**
`imports/primary_lgbm.txt` (frozen WFF booster, 343 trees, trained ≤2023 — never
retrained; WFF read-only). Scoring season-2025 rows introduces no leakage on
two independent grounds: (i) the booster parameters are frozen on ≤2023 data —
season 2025 did not exist as data at its training, so no target-season
information can reside in the model; season 2025 is genuinely OUT-of-sample for
B3 (build-phase noted 2024/2025 out-of-sample vs WFF training seasons 2021-23).
(ii) the B3-frame feature columns for season-2025 rows are pre-cutoff by item
(a). No path for on/after-Oct-1-2025 information into a B3 season-2025 score.
**(c) VERDICT: PASS.**

### (d) Binding assertions the RP1/RP2 pilot scripts MUST carry
No pilot code exists yet (src/ = p1–p4, s1, s2, s3a_baselines, s3a_b5,
s3b_primary — clean slate). The following are the guard assertions the pilot
scripts must carry for this sign-off to hold in execution:

**RP1 (re-selection + re-training, folds ≤ 2024):**
- **D1 — frame-hash pin (Amendment 5 REUSE + Rule-9 drift guard, the S3b
  pattern):** at load assert sha256(features_main)==`477d3079…` AND
  sha256(features_b3)==`09f8e94d…`. No frame regeneration, no new pull.
- **D2 — dev max-season guard:** `assert dev.season.max() == 2024` AND
  `2025 not in set(dev.season.unique())` — season-2025 rows never enter RP1.
- **D3 — fold plan:** folds exactly v ∈ {2021,2022,2023,2024}, `max(v)==2024`,
  forward-chaining train ⊆ seasons < v (never random K-fold).
- **D4 — bright-line hard-stop UNCHANGED:** existing `assert_no_test_contact`
  guard fires on any season ≥ 2026; frame load asserts `max(season)==2025`.
  Season 2026-27 absolutely untouched (Rule 3).
- **D5 — locked selection unchanged:** same 2,592-config grid, n=60 seed-42
  sample; pre-registered rule (mean val AP(q), tie-break zero-311-stratum p@250);
  refit-E*; Amendment-4(i) frozen NLL-interpretation axes — for the §3 joint,
  B4, and B5. B0-B2 recomputed from frozen definitions.
- **D6 — seed 42 (Rule 10); 5-seed spread (seeds 42–46) VALIDATION-based over
  folds ≤ 2024**, never season-2025-based (spec §8, Rule 10 — settled doctrine).
- **D7 — frozen/committed artifacts read-only:** no pilot artifact overwrites,
  shadows, or renames `s3b_primary_seed42.pt`, `s3b_frozen_config.json`, or any
  committed baseline artifact; pilot outputs live in a distinct namespace.
- **D8 — RETROSPECTIVE AND NON-BLIND label (Amendment 5(iii))** stamped in
  every pilot artifact, table, and log.

**RP2 (single-shot evaluation on season 2025-26):**
- **D9 — season 2025 loaded ONLY in the RP2 script:** `assert` the eval slice's
  seasons == {2025}; contacted exactly once; predictions persisted; reported
  as-is.
- **D10 — B3 scored as-is:** frozen booster, 343-tree assertion, no WFF
  retraining; bright-line guard (≥2026) still active.
- **D11 — §11 observed-label caveat attached to every number;** result disclosed
  whichever direction it lands (Amendment 5(iii)); the frozen G3 pre-registration
  (§10 margins, frozen bundle, Amendment-4 freeze entry, 2026-27 bright line)
  is UNTOUCHED and reported separately — R-PILOT carries no G3 weight.

### Rule-9 / anomalies
None. No fabrication, no schema surprise, no unanticipated condition. The pilot
touches season 2026-27 in no way (frames end at 2025 by construction; Rule 3
intact). My own review touched no 2026-27 data.

**RP0 VERDICT: SIGN-OFF (binding).** (a) frames-reused clause holds — season-2025
rows encode nothing on/after Oct 1, 2025 (calendar-year target read structurally
impossible; windowed max 2025-09-30 23:57 < cutoff; later-vintage raw rows
structurally excluded); (b) fold plan v∈{2021–2024} gives selection/training
zero contact with season 2025; (c) B3-as-is on season-2025 rows introduces no
leakage; (d) the eleven binding assertions above must appear in RP1/RP2 code.
Frames + frozen bundle hash-verified untouched. Pilot training may begin subject
to the RP1/RP2 scripts carrying D1–D11 (I re-audit them at RP1/RP2 per the
standing per-stage protocol).

## 2026-07-21 — RP1 audit (A-MODEL): re-selection/re-training at pilot cutoff — **REJECT** (cycle 1)

Dispatched by LEAD (standing per-stage protocol; verify implementation vs the
RP0 assertions D1–D11). Materials: `src/rp1_pilot.py`, `outputs/checkpoints/
rp1_pilot.md`, `rp1_work/rp1_stats.json` + `rp1_table.md` + all unit jsons +
guards.jsonl + models_preflight.json, the rpilot_* artifacts, `a-model.md` M8,
process_log B103/B104, and the build `s3b_work/` units for the determinism
identity. Every number re-derived independently (`.venv/bin/python`); nothing on
faith. Ten dispatched items below.

### VERIFIED CLEAN (sign-off quality)
- **(1) D1–D8 carried in substance.** D1 frame-hash pin: `load_pilot_dev`
  asserts sha256(features_main)==SHA_MAIN (L208), `prep_design` asserts
  sha256(features_b3)==SHA_B3 (L267); no regeneration/pull. D2: `dev.season.max()
  ==2024` AND `2025 not in dev` asserted (L215–217); the full-frame read
  materializes 2025 rows ONLY for the D1 whole-file hash + D4 max-season assert,
  dropped on the next statement (disclosed P1). D3: PILOT_VAL={2021,2022,2023,
  2024}, forward-chaining `season < v` (dev floor 2019). D4: `guard()` (L160)
  is the s3a/s3b hard-stop pattern verbatim, `FORBIDDEN_FROM=2026`, raises
  AssertionError on any ≥2026 or outside-allowed; frame load asserts
  max(season)==2025. D5: `sampled_configs(NET_DIMS/PROP_DIMS/RISK_DIMS)` reused
  from the audited modules (identical 60 indices — verified below); pre-registered
  rules re-executed; Amendment-4(i) axes A1–A10 imported from `s3b_primary`
  (loss_terms, cap_uk, eval_pass) unchanged; refit-E*=round(mean per-fold best
  epoch). D6: seed 42; spread seeds 43–46 over pilot folds ≤2024 only. D7:
  preflight namespace + re-verify (below). D8: label in every artifact (below).
- **(2) Selection re-derived independently, all three lanes — winners match.**
  From the persisted unit jsons: **Joint** cfg **2009** mean AP(q)
  0.3434365565, runner-up cfg 1961 0.3417637782 → margin **1.673e-3** (not a
  near-tie); runner-up has HIGHER zero-311 (0.088 vs 0.083) but the frozen rule
  is mean-AP-primary and 2009's AP strictly exceeds 1961's, so the zero-311
  tie-break is correctly **NOT invoked** (fires on exact AP ties only) — winner
  stands on AP. E*=round(mean(2,12,10,6))=**8**. **B4 stage-1** cfg **5411**
  mean AP 0.9684620257 (runner cfg 1080 0.9684428770). **B4 stage-2** cfg
  **13411** mean AP 0.3695269707, runner-up cfg **21485 (the build winner)**
  0.3694936701 → margin **3.330e-5**; tie-break not needed. **B5** cfg **13411**
  mean AP 0.3701259218, runner-up cfg **20928 (the build winner)** 0.3699977400
  → margin **1.282e-4**; runner-up higher zero-311 (0.101 vs 0.085) but AP rule
  frozen — winner AP strictly greater, applied mechanically. All four winners
  and their per-fold vectors reproduce exactly. (Two runner-up **margin prose
  figures** are the REJECT defect — see below; the winners themselves are
  correct.)
- **(3) Determinism identity EXACT.** All **240** shared-fold joint units
  (60 cfgs × folds {2021,2022,2023,2024}, seed 42) reproduce the build-phase
  `s3b_work` units to **max |ap_q diff| = 0.00e+00**, with **0** best-epoch
  mismatches — despite the entirely different worker pool (static shards vs the
  build's Queue). Strongest possible evidence that (i) pilot design typing came
  out identical (100 cols, confirming P2), (ii) per-fold scalers/pbar are
  train-fold-only, and (iii) seeding carries no universe/pool dependence.
  A-MODEL's identity claim verified, not asserted.
- **(4) Segfault episode — shard/pool-invariance verified + disclosure
  accurate.** `stable_seed(*parts)=SeedSequence([seed,fold_code,epoch])`
  (s3b L209–211); `build_model(cfg,d_in,seed,fold_code)` seeds init from
  (seed,fold_code) only; `train_unit(cfg_idx,cfg,fk,seed)` takes no worker/shard/
  pid identity; `_worker` merely iterates its shard. Unit values depend only on
  (cfg,fold,seed,epoch) — shard assignment changes *which* child computes a unit,
  never its value; item-3's exact identity is the empirical proof. Disclosure
  (checkpoint deviation 2; torch-before-lightgbm L113/L115; duplicate-OpenMP
  `__mp_main__` root cause) reconciles with the code; the bare-except swallow is
  genuinely removed — `_worker` re-raises AssertionError and persists
  `*.error.json` + re-raises other exceptions, and `run_pool` hard-checks both
  the error-file glob AND nonzero child exit codes (L583–590). Complete + accurate.
- **(5) Build-phase silent-swallow implication — none, confirmed from persisted
  completeness.** Build `s3b_work/units` holds **0 of 300** search units missing
  and **0 of 20** spread units missing; winner selection reads all 300 (a missing
  unit is a FileNotFoundError) and the freeze proceeded. The latent Queue+bare-
  except defect had zero build-phase impact. A-MODEL's assessment correct.
- **(6) D7 — 10/10 pre-existing artifacts hash-unchanged.** `models_preflight.json`
  snapshots 10 files (imports/ ×3 + outputs/models/ b4×3, b5×2, s3b×2); I
  recomputed all 10 live → **all match**, including the **frozen bundle
  `s3b_primary_seed42.pt` / `s3b_frozen_config.json` which additionally match
  PROVENANCE (bb4016b8… / 90435616…)**. No `rpilot_*` file is in the snapshot
  (correctly excluded via `PILOT_ARTIFACTS`); all 7 pilot outputs live only under
  `outputs/models/rpilot_*` and `outputs/checkpoints/rp1_work/` — distinct
  namespace, nothing frozen/committed overwritten or shadowed.
- **(7) Guard facts reconcile with guards.jsonl.** Fresh from the file: **390**
  raw records (append-only cumulative snapshot), **44** distinct sites, **max
  season ever touched = 2025** occurring **only** at the two full-frame
  load/assert sites, **zero** dev-side sites touching >2024, **zero** ≥2026 in
  any record. stats.json guard_assertions (44 / 2025 / 0 / 390) match exactly.
- **(8) Full table trace exact.** summary_means reproduce from per_season
  (no mismatches); per_season for joint(q), B4(cfg13411), B5(cfg13411) reproduce
  from the winner-config unit jsons to **max |diff| 0.0**; all 8 `rp1_table.md`
  rows appear **verbatim** as computed from summary_means (4 dp). B3 row
  0.3694/0.826/0.117 with the zero-season-2025 property enforced (`stage_b3`
  restricts to PILOT_DEV, asserts max(season)==2024 before scoring). Machine-
  generated, no hand transcription.
- **(9) Label coverage complete.** "RETROSPECTIVE AND NON-BLIND" present in all
  12 rp1_work stats/tables/winners/meta files, all 3 rpilot_* JSON configs, and
  **all 257 per-unit jsons** (0 missing) incl. refit + spread units; the joint
  .pt embeds it in its config payload. D8 satisfied.
- **(10) Tie-key mechanism verified.** design n_rows = **1,084,746** (pilot
  universe, seasons 2019–2024), so the seed-42 `rng.permutation` tie-key is drawn
  over a different row count than build → B0/B2 (and any p@k under heavy score
  ties) shift in the 3rd decimal, while AP (`average_precision_score`) is
  tie-key-free and reproduces build exactly on shared folds (item 3). Mechanism
  sound; no trapezoidal PR-AUC. Refit tree counts reconcile: prop
  round(mean[51,82,162,66])=90, risk round(mean[400,242,287,400])=332, B5
  round(mean[340,212,275,400])=307.

### DEFECT (the REJECT) — a runner-up margin figure does not reconcile with its machine source
**`rp1_pilot.md` L89 (echoed in `a-model.md` L214) states the B4 stage-1
runner-up margin as "3.2e-5". The machine source does not support it:** winner
cfg 5411 mean AP **0.9684620257**, runner-up cfg 1080 mean AP **0.9684428770**
→ margin **1.9149e-5**. Stage-1 selection is by mean AP alone, so there is no
alternative reading; and even the checkpoint's own displayed rounded means give
0.96846 − 0.96844 = **2.0e-5**, not 3.2e-5. The stated figure reconciles with
neither the precise source nor its own rounded display — a committed deliverable
number that fails to trace to its source (the identical bar behind the S3a
five-cell REJECT and the S3b guard-count REJECT). `rp1_stats.json` (machine
source) is CORRECT and stores no wrong derived margin; this is prose-only, not a
modeling/selection error — the winner (cfg 5411, = build) and both displayed
means are right.

**Secondary imprecision (same-cycle fix, not the basis for the REJECT):** the B5
runner-up margin "1.4e-4" (`rp1_pilot.md` L98, `a-model.md` L216, `process_log`
B104) is the difference of 5-dp-rounded means (0.37013 − 0.36999); the precise
margin is **1.282e-4** (rounds to 1.3e-4). Reconcile to the precise value or
label it a rounded-display difference.

**Fix (documentation only; no code/model/selection/artifact change; one-item
re-audit):** correct the B4 stage-1 margin to ≈1.9e-5 and the B5 margin to
≈1.3e-4 across `rp1_pilot.md`, `a-model.md`, and (B5) `process_log` B104, so the
stated margins trace to `rp1_stats.json`.

### Substance unaffected
All selection outcomes (four winners, matching build indices where applicable),
the exact determinism identity, the segfault fix + shard-invariance, build-phase
no-silent-swallow, D7 10/10 incl. frozen-bundle-vs-PROVENANCE, guard sanctity
(44/2025/0, zero ≥2026 firings), the machine-generated table trace, label
coverage, and the tie-key mechanism are all verified correct. Season 2025 never
enters any RP1 dev structure; season 2026-27 untouched. No fabrication, no
Rule-9 condition. The defect is a doc-level non-reconciling margin figure.

**RP1 VERDICT: REJECT** (cycle 1) — single documentation defect (B4 stage-1
runner-up margin 3.2e-5 does not reconcile with the machine source 1.9e-5;
rp1_pilot.md L89 / a-model.md L214) plus one secondary margin imprecision (B5
1.4e-4 vs 1.282e-4). All ten dispatched audit items are otherwise verified clean,
including the exact determinism identity and full number tracing. Fix is
doc-only; re-audit is a two-figure recheck. RP2 remains gated on the corrected
sign-off.

## 2026-07-21 — RP1 re-audit (REJECT cycle 1 → **SIGN-OFF**)

Two-figure recheck per LEAD (ledger B106) after A-MODEL applied the doc-only
corrections. Both touched surfaces re-read; machine source, code, and artifacts
re-verified untouched.

- **(1) B4 stage-1 margin corrected + traces to source.** `rp1_pilot.md` L89 now
  "**margin 1.9e-5**" with a bracketed trace (L90–91): "corrected from 3.2e-5 …
  0.9684620257 − 0.9684428770 = 1.9149e-5", cfg 1080 named. `a-model.md` L214
  matches ("margin 1.9e-5 [corrected from 3.2e-5…]"). My independent re-derivation
  from `rp1_stats.json`: winner 0.9684620257 − runner 0.9684428770 = **1.9149e-5**
  → the stated 1.9e-5 reconciles.
- **(2) B5 margin corrected + traces to source.** `rp1_pilot.md` L100 now
  "**margin 1.3e-4**" with bracket (L101–103): "corrected from 1.4e-4 …
  0.3701259218 − 0.3699977400 = 1.282e-4". `a-model.md` L217 matches. Re-derived
  margin **1.2818e-4** → rounds to 1.3e-4 (2 s.f.); exact 1.282e-4 in the bracket.
  Reconciles. (A first-pass rounding check of mine flagged this falsely by
  rounding to 4 dp instead of 2 s.f.; the doc value is correct.)
- **(3) B4 stage-2 margin untouched + still correct.** `rp1_pilot.md` L95 /
  `a-model.md` L216 retain "3.3e-5"; re-derived 3.3301e-5 → correct, as required.
- **(4) Old figures survive ONLY as provenance.** Every residual "3.2e-5" /
  "1.4e-4" string in the two files sits inside a bracketed "corrected from …"
  audit-trail note — no stale LIVE margin remains. Proper Rule-8-style disclosure
  of the change, not a lingering error.
- **(5) No out-of-scope diffs.** `rp1_pilot.md` winners section (L77–106)
  re-read: only the two margin lines + their provenance brackets changed; joint
  (cfg 2009, margin 1.7e-3, E*=8), B4-s2 (cfg 13411, 3.3e-5), B5 (cfg 13411),
  and refit trees (90/332/307) identical to the reject-pass audit. `a-model.md`
  edits are confined to the two margin figures within M8. **Machine source and
  build products untouched:** `rp1_stats.json` and `rp1_table.md` mtimes predate
  the md edits (not rewritten); stats winners (2009/5411/13411/13411) and all
  three margins re-verified from it; `src/rp1_pilot.py` unchanged; **D7 preflight
  10/10 artifacts still hash-unchanged, frozen bundle still matches PROVENANCE
  (bb4016b8… / 90435616…)**; rpilot_* artifacts unchanged.

Everything verified clean at the reject-pass first read (D1–D8 implementation,
independent selection of all three lanes, the EXACT determinism identity — 240
shared-fold units to 0.00e+00, segfault fix + shard-invariance, build-phase
no-silent-swallow, guard sanctity 44/2025/0/zero-≥2026, full machine-generated
table trace, label coverage on all 257 units + artifacts, tie-key mechanism)
stands unchanged.

**RP1 VERDICT (post-correction): SIGN-OFF.** The sole reject-1 defect (B4
stage-1 margin non-reconciling) is fixed and now traces to `rp1_stats.json`; the
secondary B5 imprecision is corrected; the untouched B4-s2 margin remains correct;
the corrections are doc-only across the two authorized surfaces with accurate
provenance and introduced no code/model/selection/artifact change (mtimes +
hashes verified). Counter closed at 1. RP1 clears. RP2 (the single-shot 2025-26
evaluation) may proceed under the standing audit protocols; the §11 observed-label
caveat and the RETROSPECTIVE AND NON-BLIND label attach to every RP2 number, and
the frozen G3 pre-registration remains untouched.
