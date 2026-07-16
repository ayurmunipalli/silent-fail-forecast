# A-FEAT log — S2 features (build phase)

Binding: `.claude/agents/a-feat.md`. Read in full before acting: CLAUDE.md,
model_spec.md §1/§2/§3/§7 + Amendments 1–2, plan.md §3 step 5, WFF
`src/s2_features.py` (read-only reference; NOTHING written to the WFF repo).

## 2026-07-16 — S2 execution record

1. **Inputs verified on disk** (all S1-audited): frozen spine
   `imports/building_season_labels.parquet` (1,624,255 × 4, seasons 2017–2025);
   `c311_heat_complaints.parquet` (1,731,513); `hpd_violations_wff.parquet`
   (149,585; class C 149,583 / B 2); `hpd_viol_context_by_year.parquet`
   (2,012,740 groups); `hpd_registrations.parquet` (203,236);
   `hpd_registration_contacts.parquet` (782,024); `pluto_full.parquet` (858,602,
   bbl unique); `hpd_complaints_heat.parquet` (1,754,951, problem_id unique).
   Schema observation: ALL caches string-typed on disk; ctx `yr`/`n` str vs the
   PROVENANCE "Int64" note — coerced with asserted zero parse loss (inventory D3).
   Not a Rule-9 schema surprise: values parse exactly; flagged, proceeded.
2. **Frozen-model contract extracted** from `imports/primary_lgbm.txt` header/footer:
   30 `feature_names` (order adopted for the B3 frame), categorical features 26/27
   with `pandas_categorical` vocabularies (24 bldgclass letters; BK/BX/MN/QN/SI) —
   vocabularies hard-coded into the build and conformance asserted (0 novel values).
3. **WFF recipe re-implementation** (`src/s2_features.py`, this repo): line-range
   citations per family in the inventory checkpoint. `season_of`/`norm_txt` copied
   verbatim (WFF L46–62). Cache-name mapping and the family-3 local aggregation
   (replicating WFF s1d L47–51 server-side recipe) documented as D2.
4. **Families 6–7 design decisions** (mine to make per dispatch, documented for
   R-AUDIT): windows ps/t365/t730 with left-edge-≥-floor availability rule;
   `win()` guard asserts window_hi ≤ cutoff on EVERY timestamp slice (structural
   impossibility, not discipline); family-7 apartment rule
   (`unit_type=='APARTMENT'` ∧ apt ∉ {'', 'BLDG'}); duplicate-flag ruling =
   both-ways (inventory §family-7): distinct-apt counts flag-invariant by
   construction, event counts carried all-rows AND flag-N, Y-share exposed as its
   own feature. ygpa touches ONLY `c7_*` columns (Amendment-1 boundary).
5. **Build runs:** two foreground runs (~70 s each; no background tasks, per
   session guidance). Run 2 **byte-identical** to run 1: features_b3
   `09f8e94d…24fa09`, features_main `477d3079…734090`, s2_stats.json identical.
6. **Fidelity verification (beyond the brief):** B3 frame aligned key-for-key
   against WFF's own frozen `features.parquet` — 26/30 columns exactly equal on
   all 1,624,255 rows; residual = 1 building's ctx_c accrual (5 cells; D1).
   Every family-1–5 NULL-audit count matches WFF's committed S2 report exactly.
7. **Leakage self-checks passed:** spine max season asserted 2025 at load; frame
   max season asserted 2025 pre-write; year matrices capped at 2024; all family-6/7
   slices through `win()`; label join verbatim + completeness asserted; zero
   duplicate (bbl, season) keys. Season 2026-27: no contact anywhere.
8. **Deliverables:** `data/processed/features_b3.parquet` (30 feats),
   `data/processed/features_main.parquet` (49 feats: 8/10/3/7/2 + 11 + 8),
   `outputs/checkpoints/s2_feature_inventory.md`,
   `outputs/checkpoints/s2_stats.json`, PROVENANCE S2 entry, this log.
   Storage: data/ + imports/ = 388 MB ≤ 2 GB. Seed 42 (no sampling occurs).
9. **Rule-9 conditions encountered:** none. Reported to LEAD via SendMessage.
