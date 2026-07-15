# phase0_memo.md — silent-fail-forecast — phase-0 probe verdict

**Compiled by:** LEAD, 2026-07-16, from the four R-AUDIT-signed-off checkpoints only
(P1 pull report; `outputs/checkpoints/phase0_p2_duplicates.md`;
`outputs/checkpoints/phase0_p3_hsp.md`; `outputs/checkpoints/phase0_p4_zeromass.md`).
Governing text: `phase0_probe.md` (APPROVED 2026-07-16, Amendments 1–3). Thresholds are
CITED VERBATIM below, never restated or adjusted. **Adjudication of this verdict is
Ayur's alone and is not delegated by anything in this memo.**

---

## Verdict (pre-committed semantics, probe doc §1 as amended)

# **GO**

Probe doc §1, verbatim: *"**GO** — at least channel (a) passes; spec drafting proceeds."*

Channel (a) passed at the gate window (strongest pre-committed evidence class); channel
(b) independently passed its validation-power floor, so the GO-DEGRADED branch
(*"(a) passes, (b) fails"*) does not apply. The HOLD and KILL branches did not fire.

## Channel (a) — duplicates-per-incident (P2, THE KILL GATE)

Pre-committed threshold, probe doc §3, verbatim:

> **KILL THRESHOLD (pre-committed; gate window amended — see Amendment 1):** the gate
> evaluates at **W = 14**: if the median confirmed violation in buildings with ≥10 units
> has **< 2** associated complaints at W = 14, the duplicate channel fails at the gate.

Escalation semantics, Amendment 1, verbatim:

> FAIL@14 ∧ PASS@30 → **HOLD** [...] FAIL@both → KILL. PASS@14 → GO on channel (a).

Signed-off gate cells (P2 checkpoint; eligible, PLUTO-matched, unitstotal ≥ 10,
n = 76,217, pooled seasons 2019-20…2025-26):

| cell | value |
|---|---|
| median associated complaints @ W=14 | **4** |
| median associated complaints @ W=30 | **6** |

4 ≥ 2 at W = 14 → **PASS@14 → GO on channel (a)** — the branch follows mechanically;
R-AUDIT verified this mechanically in its binding P2 sign-off. Medians are ≥ 2 in every
unit-count class at both windows. The mandatory complaint→inspection lag distribution
shipped with the checkpoint regardless of branch (pair-level @ W=30, pooled: median 9,
p75 19, p90 26 days; per season in the checkpoint). The HOLD branch did not fire, so no
adjudication of it is required.

## Channel (b) — HSP ground truth (P3)

Pre-committed floor, probe doc §4, verbatim:

> **PASS/DEGRADE (pre-committed):** channel (b) is usable for external validation iff
> ≥ **30** complaint-independent confirmed failure events exist across all HSP
> cohort-seasons combined.

Signed-off count (P3 checkpoint): **377** complaint-independent confirmed failure events
(zero associated 311 complaints at W = 30, P2 rule) across all HSP cohort-seasons —
377 ≥ 30 → **PASS**. All four cohort lists (2020/2022/2024/2025; 200 buildings, 197
distinct lots) were located and resolved; 311-only version of the heuristic ran because
no HPD complaints dataset is usable in phase-0 (two candidates retired behind login
walls; the live merged dataset `ygpa-z7cr` is excluded by Amendment 1 item 2). Per §4's
own labeling requirement, the checkpoint states the count is an upper bound on
311-independent events under the 311-only version. Robustness stated in the checkpoint:
the floor is also cleared under the narrower Oct–Jan cadence reading (223) and under
(bbl, inspectiondate) dedupe (244).

## P4 — zero-mass structure (descriptive; gates nothing)

Per §5, reported as figure + table; no gate, no conclusion. Signed-off description: over
171,745 complete-covariate spine buildings in 148 occupied covariate cells, 146 cells
contain both masses; 106,231/106,232 zero-mass buildings sit in cells that also contain
complaint-positive buildings. The masses differ in composition (median 3 vs 8 units;
zero-311 share 78.4% → 16.8% from 2–5-unit to 50+ classes; median CD income $85,263 vs
$79,943; LEP shares nearly identical). Zero-311 mass = 63.2% of the spine universe on
this window (WFF's ~70% was measured on its own window; reported alongside, not
reconciled). Feeds spec §identification.

## R-AUDIT sign-offs (binding, opus 4.8, per stage)

| stage | protocol | result | commit |
|---|---|---|---|
| P1 (+bootstrap sha256s) | IDs re-verified live; counts; union arithmetic; seam continuity | SIGN-OFF, no defects | `db4e24d` |
| P2 | BLIND re-derivation before reading A-GATE; every cell reproduced, max abs diff 0 | SIGN-OFF | `ce97efe` |
| P3 | 377 reproduced exactly; floor arithmetic; version-choice logic | SIGN-OFF | `eb48b48` |
| P4 | no gating language; credential value-scan clean; exclusions logged | SIGN-OFF | `f75fb13` |
| memo | memo-vs-thresholds pass | see r-audit.md | — |

## Deviations and flags on record for Ayur (none affect the branch that fired)

1. **Amendment 3 (Ayur-authorized, appended)**: NYC re-scoped `erm2-nwe9` to 2020+;
   archive `76ig-c548` unioned to restore the 2019-06-01 floor (dedupes = 0; seam
   audited continuous); window-coverage eligibility codified for P2.
2. **Heat-season scoping (R-AUDIT flag, non-blocking)**: P2 cells are computed over the
   §3-listed heat seasons; an all-months computation moves the W=14 gate median from 4
   to 3 but the branch is PASS@14 under every interpretation R-AUDIT tried.
3. **P3 membership authority (R-AUDIT-ruled conformant-with-disclosure)**: official HPD
   dataset `h4mf-f24e` used as membership/BBL authority, §4's PDFs as cross-check
   (199/200 exact; 1 spelling variant; 0 BBL disagreements).
4. **Whitelist superset**: frozen whitelist is class B+C (1 B row); §3's class-C
   restriction applied explicitly in P2/P3 code (audited).
5. **Probe doc signature block** at document foot remains blank while the header line
   asserts APPROVED 2026-07-16; Ayur has stated he will initial it.

Per the standing rule, this memo recommends nothing beyond stating the pre-committed
branch that fired; on a HOLD it would present the lag table and recommend nothing — the
verdict here is GO, and its adjudication (including whether spec drafting proceeds) is
Ayur's alone.
