# A-GATE log — P2 duplicates-per-incident kill gate

Agent: A-GATE (claude-fable-5, per `.claude/agents/a-gate.md`). Dispatched by LEAD
2026-07-16 for P2 per phase0_probe.md §3 + Amendment 1 (W=14 gate, HOLD branch,
311-only association) + Amendment 3 item 2 (window-coverage eligibility).

## Inputs (P1 caches, R-AUDIT-signed, read-only to me)

- `data/raw/c311_heat_complaints.parquet` — 1,731,513 rows (union deliverable,
  null-bbl already excluded in P1).
- `data/raw/hpd_violations_heat.parquet` — 128,121 rows, verbatim frozen-whitelist
  B+C superset (P1-audit flag: class-C restriction is MINE to apply).
- `data/raw/pluto_units.parquet` — 858,602 rows, bbl + unitstotal.
- `data/p1_stats.json`, `data/PROVENANCE.md` for cross-checks.

## What I did

1. Read a-gate.md definition, CLAUDE.md, phase0_probe.md in full (incl. Amendments
   1–3). Season definition (Oct 1–May 31, start-year label, Jun–Sep off-season)
   ported in semantics from the READ-ONLY winter-fail-forecast
   `src/s1_data_pull.py::season_of` so P2 strata match the frozen label spine;
   no old-repo file was edited or executed.
2. Wrote `src/p2_gate.py` (idempotent, seed 42; rerun → byte-identical checkpoint
   and stats, verified by sha256 twice). All fixed decisions are stated in the
   script docstring AND the checkpoint: inclusive window bounds
   [inspectiondate−W, inspectiondate] on calendar dates; naive local NYC time,
   day-truncated (inspectiondate midnight-stamped → lossless); bbl normalized to
   int64 in all three sources; class-C restriction applied explicitly (1 B row
   removed, 128,121 → 128,120); no dedupe of violation rows or of
   complaint→multi-violation associations (multiplicity reported instead);
   percentiles = numpy linear interpolation.
3. Both windows (W=14, W=30) computed in one join structure (sorted composite
   bbl×day key, searchsorted); violation-side and complaint-side pair totals
   asserted equal at both windows (internal consistency check passed).
4. Wrote `outputs/checkpoints/phase0_p2_duplicates.md` + `data/p2_stats.json`.

## Eligibility waterfall (Amendment 3 — everything counted, nothing silent)

128,121 → class-C 128,120 → −0 duplicate violationid → −197 bad bbl (185
null/empty per PROVENANCE + 12 literal `bbl='0'`) → −0 bad dates →
−326 coverage-excluded (Amendment 3: full W=30 window must lie in 311 coverage
2019-06-01…2026-07-13; 303 left edge, 23 right edge) → −13,253 off-season
(Jun–Sep) → −0 out-of-list season → **114,344 eligible violations**.
311 side: 331 of 1,731,513 rows excluded (all literal `bbl='0000000000'`
placeholders — zero-BBLs would spuriously cross-match, unusable).

## Results (headline; full tables in the checkpoint)

- **Gate cell (eligible, PLUTO-matched, unitstotal ≥ 10; n = 76,217):
  median associated complaints = 4 @ W=14, 6 @ W=30.**
- **Pre-committed branch fired: PASS@14 → GO on channel (a).** I state the
  branch; I do not adjudicate.
- Unit-count join match rate on eligible violations: 99.83% (193 unmatched →
  excluded from class strata and gate cell, counted; kept in season margins).
  PLUTO: 429 null-unitstotal excluded, 0 conflicting-unit bbls.
- Medians ≥ 2 in every unit class at both windows; monotone in unit count
  (W=14 medians 2/2/3/5 for 2-5/6-19/20-49/50+).
- Zero-complaint violations: 4.94% pooled @14, 3.56% @30 (feeds P3 heuristic).
- Multiplicity (reported, not deduped): 46.80% of associated complaints
  associate to ≥2 eligible violations @14; 52.16% @30.
- Lag (mandatory): pair-level @30 pooled median 9 d, p75 19, p90 26; per-season
  table in checkpoint. Per-complaint first-inspection lag median 4 d, p75 13,
  p90 22.
- Complaints-per-unit falls with building size (median 0.600 → 0.222 from 2-5
  to 50+ units) — the raw propensity shape, associated-with only, no causal claim.

## Anomalies / notes for R-AUDIT

- 12 violation rows and 331 complaint rows carry literal zero BBLs (not null —
  P1's null accounting was correct); excluded with counts stated.
- 25.43% of violation building-days carry ≥2 violation rows (max 21) — rows NOT
  collapsed, §3's unit is the violation row; diagnostic in checkpoint.
- Coverage exclusions (326) fall entirely in Jun 2019 / Jul 2026, so they overlap
  the off-season exclusion set; order of filters (coverage before season) is
  stated so the waterfall is reproducible.
- No Rule 9 condition encountered: no schema surprise, no empty join, storage
  untouched (no new raw data; outputs are two small text files).

## Deliverables

- `src/p2_gate.py`
- `outputs/checkpoints/phase0_p2_duplicates.md` (sha256
  ec63cf7dac5dc18ab97867f94190cf977fcb577114f734a9fc99e15dccf62d00)
- `data/p2_stats.json` (sha256
  7acafb45dfec28194098fec7ff0d8a6d946ab5545ef07c025353edfb803cb4ac)
- this log. I do not commit; handoff to LEAD for R-AUDIT blind re-derivation.
