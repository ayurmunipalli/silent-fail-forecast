APPROVED July 16, 2026, Amendments 1-2

# phase0_probe.md — silent-fail-forecast — feasibility probe design (PRE-G0)

**Status:** DRAFT until Ayur writes "APPROVED" + date at top. Runs BEFORE any spec is
drafted: this probe decides whether the project's identification strategy is live.
Kill thresholds are pre-committed in this document, before any code runs, so the kill
gate cannot quietly become negotiable after results are seen (Rule 8 lineage).

**Project:** silent-fail-forecast (fresh repo; successor to winter-fail-forecast).
**Author of record:** Ayur Munipalli. Probe design drafted by lead Claude from Ayur's
Step-0 rulings of 2026-07-16.

---

## 0. Step-0 rulings on record (2026-07-16)

- **R1 — Test protocol = OPTION B (prospective).** Development + validation on seasons
  2017-18 … 2025-26; single pre-registered prospective evaluation on season 2026-27,
  scored once after season close (~June–July 2027, allowing entry lag). Seasons
  2024-25/2025-26 are NOT reused as held-out test: winter-fail-forecast's G3 results on
  those seasons motivated this project's conception (documented in that repo's
  g3_miss_analysis_311_binary.csv), so treating them as untouched test would be circular.
  They enter DEVELOPMENT here, with that provenance disclosed.
- **R2 — DL authorization (delegated by Ayur to lead; decision recorded, ratified at
  G0 freeze).** One authorized architecture: joint two-head model (shared MLP encoder;
  heads P(failure), P(report | failure)) on the censored multiplicative likelihood
  P(observed) = P(fail) · P(report | fail). No transformers, no GNNs, no ensembles.
  Mandatory baselines the joint model must beat on pre-registered criteria:
  B0–B2 (ported), B3 = frozen winter-fail-forecast `primary_lgbm.txt` loaded read-only
  and scored on new seasons (no old-repo test-label contact), B4 = two-stage GBM
  (propensity model → IPW risk model). Joint ≤ B4 ships as the finding.
- **R3 — Name:** silent-fail-forecast.
- **R4 — Old repo = read-only frozen artifact source.** Imported verbatim, never
  retrained, never edited: `outputs/models/primary_lgbm.txt` (343 trees, seed 42),
  `data/processed/building_season_labels.parquet` (frozen label spine),
  `outputs/test_predictions.parquet` (static comparison artifact only). Import = copy +
  sha256 recorded in PROVENANCE.md; originals untouched.

---

## 1. What this probe decides

The project's premise: reporting propensity P(report | failure) is identifiable at the
building level from (a) duplicate-complaint rates per confirmed incident and/or
(b) complaint-independent inspection outcomes (Heat Sensors Program). winter-fail-forecast
already proved the propensity is NOT recoverable from covariates alone (the no-311
ablation kept the blind spot). If neither (a) nor (b) survives this probe, the project
dies here — before a spec, before agents, before sunk cost.

Probe outputs → `phase0_memo.md` with exactly one of:
- **GO** — at least channel (a) passes; spec drafting proceeds.
- **GO-DEGRADED** — (a) passes, (b) fails → validation-channel loss disclosed; spec §
  on external validation is rewritten before freeze.
- **HOLD** — (a) fails at W=14 but passes at W=30 (Amendment 1): Ayur adjudicates with
  the lag distribution; resolves to GO / GO-DEGRADED / KILL, nothing else.
- **KILL** — (a) fails. (b) alone cannot carry identification (n too small to train on;
  it is a validation set, not a training signal). Project killed or redesigned from
  scratch; no "soft pivot" inside this repo.

## 2. Probe P1 — complaint-granularity pull

**Purpose:** the existing 311 layer (winter-fail-forecast `s1d`) is (bbl, year) COUNT
aggregates; identification needs per-complaint rows.

- **Source:** Socrata `erm2-nwe9` (verify live per Rule 5 before pull).
- **Select:** `unique_key, created_date, closed_date, bbl, complaint_type, status`.
- **Where:** `complaint_type in ('HEAT/HOT WATER','Heat/Hot Water') and
  created_date >= '2019-06-01'`. Do NOT filter `bbl IS NOT NULL` at pull time — null-bbl
  rows are pulled and COUNTED (expected ~0.4% per prior docstring), then excluded with
  the exclusion logged. Coverage accounting, not silent drops.
- **Volume estimate:** ~1.65M rows × 6 narrow cols — well under the 2 GB budget.
- **Mechanics:** server-side filtered, paged, parquet-cached, idempotent, storage-guarded
  — the `s1d` skeleton with the groupby removed.

## 3. Probe P2 — duplicates-per-incident (identification channel a) — THE KILL GATE

**Incident association rule (fixed here):** for each confirmed §27-2029/§27-2031
class-C violation row (frozen whitelist, verbatim), associate complaints in the same
building (bbl) with `created_date` in `[inspectiondate − W, inspectiondate]`.
Primary window **W = 30 days**; sensitivity at **W = 14** reported alongside.
A complaint may associate to multiple violations within W; report the multiplicity rate
rather than deduplicating silently.

**Report:** distribution (median, p25, p75, mean, % with ≥2) of associated complaints
per confirmed violation, stratified by PLUTO unit-count class {2–5, 6–19, 20–49, 50+}
and by season (2019-20 … 2025-26; the 311 floor truncates the first).

**KILL THRESHOLD (pre-committed; gate window amended — see Amendment 1):** the gate
evaluates at **W = 14**: if the median confirmed violation in buildings with ≥10 units
has **< 2** associated complaints at W = 14, the duplicate channel fails at the gate.
**Escalation rule (pre-committed):** FAIL at W=14 but PASS at W=30 → verdict is **HOLD**,
not KILL — the memo ships the complaint→inspection lag distribution (median, p75, p90,
per season and pooled) alongside, and Ayur adjudicates. FAIL at both windows → KILL,
no adjudication. PASS at W=14 → GO on this channel, strongest evidence. No other
threshold or window may gate.

**Secondary diagnostics (reported, not gated):** complaints-per-unit vs unit count
(the propensity signal's raw shape); % of confirmed violations with ZERO associated
complaints (candidate proactive/HP-court-initiated events — feeds P3's heuristic).

## 4. Probe P3 — Heat Sensors Program ground truth (identification channel b)

**Purpose:** HSP buildings receive proactive inspections ≥2×/month Oct–Jan regardless
of complaints (LL18/2020 as amended by LL70/2023) — potential complaint-independent
failure labels.

- **P3.1 — Cohort lists:** locate + download HSP building lists for cohorts 2020, 2022,
  2024, 2025 (nyc.gov PDFs; 2020 list URL known from prior search; others UNVERIFIED —
  locate or record absence). Resolve addresses → BBL via PLUTO; report resolution rate.
  Expected universe: ~200 buildings cumulative.
- **P3.2 — Proactive-detectability heuristic:** within HSP buildings during program
  seasons, count violation events with zero associated 311 complaints (P2 rule, W = 30)
  AND zero HPD-complaint-dataset entries in the same window (dataset ID for HPD
  complaints — distinct from 311 — UNVERIFIED; verify per Rule 5; if no usable HPD
  complaints dataset exists, disclose and run the 311-only version, labeled as such).
  These are the candidate "complaint-independent confirmed failures."
- **PASS/DEGRADE (pre-committed):** channel (b) is usable for external validation iff
  ≥ **30** complaint-independent confirmed failure events exist across all HSP
  cohort-seasons combined. Below 30, the channel is DEGRADED (anecdotal only; spec's
  validation section rewritten accordingly). This is a validation-power floor, not a
  training requirement — HSP data never trains the model either way.

## 5. Probe P4 — zero-mass structure (descriptive; no gate)

Among the ~70% zero-311 buildings (winter-fail-forecast measurement): distribution of
unit counts, borough, CD income tercile (machinery imported from `s3d`), and tract LEP
share (ACS via existing Census plumbing, `CENSUS_API_KEY` in `.env`). Question on
record: does the zero-complaint mass have covariate support overlapping the
complaint-positive mass (propensity extrapolation feasible), or is it a disjoint
population (extrapolation = assumption, to be stated in the spec)? Reported as a
figure + table; informs spec §identification, gates nothing.

## 6. Rules in force during phase-0

Ported from winter-fail-forecast CLAUDE.md, binding from the first commit:
no fabrication (empty pull = stop + report); credentials in `.env`, never printed;
verify every dataset ID live before pull, log to PROVENANCE.md; server-side filtered,
parquet-cached, idempotent pulls; ≤ 2 GB tabular, no rasters, ever; seed 42;
PROVENANCE.md updated in the same commit as every stage; frozen documents amended by
dated appended notes only. The winter-fail-forecast repo is READ-ONLY throughout (R4).

## 7. Deliverables

1. `data/raw/c311_heat_complaints.parquet` (P1 cache) + pull log.
2. `outputs/checkpoints/phase0_p2_duplicates.md` — the kill-gate table, W=30 and W=14.
3. `outputs/checkpoints/phase0_p3_hsp.md` — cohort resolution + detectability counts.
4. `outputs/checkpoints/phase0_p4_zeromass.md` — descriptive support analysis.
5. `phase0_memo.md` — GO / GO-DEGRADED / KILL, citing the pre-committed thresholds in
   this document verbatim. The memo does not restate thresholds; it cites them.
6. PROVENANCE.md — from the very first pull.

**Estimated effort:** P1+P2 ≈ 1–2 agent-days; P3 ≈ 1–2 days (PDF wrangling dominates);
P4 ≈ half a day. Single agent + one reviewer pass is sufficient at this scale — full
team topology is a G0 concern, not a phase-0 one.

---

## Amendments (appended, dated — never in-place edits; Rule 8 lineage)

### Amendment 1 — 2026-07-16 — gate window = W=14 with HOLD branch; 311-only association
**Author of record: Ayur Munipalli** (ruling delivered in session, 2026-07-16).

1. **Gate window.** The P2 kill gate evaluates at **W = 14** (Ayur's ruling), replacing
   the drafted W=30 gate. Pre-committed escalation branch: FAIL@14 ∧ PASS@30 → **HOLD**
   (Ayur adjudicates with the complaint→inspection lag distribution in hand — the OSC
   2019-N-3 audit documents 3+-day response lags for 31–49% of complaints, so a 14-day
   window can truncate real duplicates during inspection-queue surges; the lag table
   determines whether a 14-day fail reflects tenant silence or the queue). FAIL@both →
   KILL. PASS@14 → GO on channel (a). This branch is recorded BEFORE any data is pulled;
   it is pre-registration with a condition, not threshold shopping. Verdict set in §1
   gains **HOLD** as a fourth outcome, resolvable only by Ayur to GO/GO-DEGRADED/KILL.
2. **311-only incident association (simplification, Ayur's ruling).** Considered and
   dropped for probe scope: (i) the 311 scope descriptor (entire-building vs
   apartment-only) — tenant-declared, and its error is plausibly correlated with
   reporting propensity itself (connected buildings both know outages are building-wide
   and report more), so it may not be used as an association FILTER; (ii) the merged HPD
   Complaints-and-Problems dataset (apartment identifiers; possible administrative
   duplicate linkage per OSC audit — linkage known to be error-prone). Both remain
   candidate FEATURES/diagnostics for the spec phase; neither is pulled or used in
   phase-0. P2 counts all whitelisted 311 heat/hot-water complaints per building-window,
   both scopes, undifferentiated.
3. Episode-gap segmentation and duration-adaptive endpoints (discussed in session)
   are likewise deferred to the spec phase — reported diagnostics at most, never gates.

### Amendment 2 — 2026-07-16 — phase-0 team topology (supersedes §7 sizing note)
**Author of record: Ayur Munipalli** (ruling delivered in session, 2026-07-16).
§7's "single agent + one reviewer pass" sizing is replaced by a lead-coordinated
team: LEAD (fable 5) orchestrating three worker agents (fable 5), all work audited
by one reviewer (opus 4.8, binding sign-offs). Roster, model binding, execution
order, handoff protocol, and documentation requirements live in `plan.md`;
behavioral rules remain in `CLAUDE.md`. The scientific content of this document —
probes P1–P4, all thresholds, the W=14/HOLD gate (Amendment 1), verdict semantics —
is UNCHANGED. Ayur's adjudication of the verdict remains non-delegatable.

APPROVED: ____________  DATE: ____________
