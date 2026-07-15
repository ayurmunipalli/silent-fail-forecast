"""P2 — duplicates-per-incident, THE KILL GATE (phase0_probe.md §3 + Amendments 1 & 3).

Idempotent: rerun with `.venv/bin/python src/p2_gate.py`; reads only the P1 caches,
writes outputs/checkpoints/phase0_p2_duplicates.md + data/p2_stats.json. Seed 42
(Rule 7; no sampling occurs). Never fabricates: empty join or schema surprise raises
and stops (Rules 1, 9).

FIXED DECISIONS (stated here and in the checkpoint so R-AUDIT can re-derive blind):

1. CLASS-C RESTRICTION (probe doc §3): the P1 violations cache is the verbatim
   frozen-whitelist B+C SUPERSET (flagged in P1 audit). We apply `class == 'C'`
   EXPLICITLY here, first filter in the waterfall.
2. ASSOCIATION RULE (§3): complaints in the same bbl with created_date in
   [inspectiondate - W, inspectiondate], BOTH BOUNDS INCLUSIVE, W in {14, 30},
   both windows computed in one pass over the same join structure.
3. DATE/TIMEZONE: Socrata timestamps are naive local NYC time; both created_date
   and inspectiondate are truncated to CALENDAR DATE (day precision) before
   comparison. inspectiondate is midnight-stamped in the source, so truncation is
   lossless there. A complaint created on the inspection calendar day counts as
   associated (inclusive upper bound); day-precision data cannot resolve intraday
   order, and this is stated rather than guessed.
4. BBL DTYPE: 311/violations carry bbl as 10-digit strings; PLUTO carries
   decimal-strings ("2054800111.00000000"). All three normalized to int64
   (values <= ~5.1e9, exact in float64 en route). Unparsable / <=0 bbl rows are
   counted and excluded, never defaulted.
5. WINDOW-COVERAGE ELIGIBILITY (Amendment 3 item 2): a violation enters the
   distributions and the gate only if its FULL W=30 window lies inside 311
   coverage, where coverage = [min, max] created_date calendar dates actually
   present in the P1 311 deliverable. Exclusions counted left/right edge,
   reported, never silently dropped.
6. SEASONS: NYC heat season Oct 1 - May 31, labeled by start year — definition
   ported from winter-fail-forecast src/s1_data_pull.py season_of() (read-only
   reference), consistent with the frozen label spine. P2 seasons are
   2019-20 .. 2025-26 (§3); off-season (Jun-Sep) and out-of-list-season rows are
   counted and excluded.
7. DEDUPE: exact duplicate violationid rows would be dropped (count reported;
   observed count is in the stats). NO dedupe of multiple violations per
   (bbl, inspectiondate) — §3's unit is the violation ROW; rows-per-(bbl,day)
   is reported as a diagnostic instead. Complaint-to-multiple-violation
   multiplicity is REPORTED, never deduped (§3).
8. UNIT-COUNT JOIN: PLUTO bbl -> unitstotal. PLUTO rows with null unitstotal
   excluded; duplicate PLUTO bbls with a single distinct unitstotal collapsed,
   with CONFLICTING unitstotal excluded entirely (counted, never defaulted).
   Violations unmatched to a usable unitstotal are excluded from unit-class
   strata and the gate cell, counted; they remain in season-margin tables.
9. GATE (Amendment 1, semantics verbatim from the probe doc): evaluated at W=14
   on the median associated complaints per eligible violation in buildings with
   unitstotal >= 10, pooled across P2 seasons. This script STATES which
   pre-committed branch fired; it does not adjudicate.
10. LAG (Amendment 1, mandatory): complaint->inspection lag in days,
    lag = inspectiondate - created_date, over all associated PAIRS at W=30
    (primary, stated), plus per-complaint lag to its FIRST associated inspection
    within 30 days (secondary). median/p75/p90, per season (of the violation)
    and pooled. Percentiles: numpy default linear interpolation.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "data" / "raw"
CKPT = REPO / "outputs" / "checkpoints" / "phase0_p2_duplicates.md"
STATS = REPO / "data" / "p2_stats.json"

random.seed(42)
np.random.seed(42)  # Rule 7 — no sampling occurs; set for consistency

SEASONS = list(range(2019, 2026))  # start years: 2019-20 .. 2025-26 (§3)
DAY_MOD = 100_000  # composite key stride: day index < 100k, bbl*1e5 + day fits int64
UNIT_BINS = [(2, 5), (6, 19), (20, 49), (50, None)]  # §3 unit-count classes


def season_of_days(days: np.ndarray) -> np.ndarray:
    """NYC heat season start year (Oct 1 - May 31); -1 for Jun-Sep off-season.
    Ported verbatim in semantics from winter-fail-forecast s1_data_pull.season_of."""
    ts = pd.to_datetime(days, unit="D")
    month, year = ts.month.values, ts.year.values
    out = np.where(month >= 10, year, np.where(month <= 5, year - 1, -1))
    return out


def to_bbl_int(s: pd.Series) -> pd.Series:
    """Normalize bbl strings (plain or decimal-suffixed) to int64; NaN if unparsable."""
    v = pd.to_numeric(s, errors="coerce")
    v = v.where(v > 0)
    return v.round().astype("Int64")


def to_days(s: pd.Series) -> pd.Series:
    """ISO timestamp string -> integer days since 1970-01-01 (calendar-date truncation)."""
    dt = pd.to_datetime(s, errors="coerce")
    days = pd.Series(dt.values.astype("datetime64[D]").astype("float64"), index=s.index)
    return days.where(dt.notna().values).astype("Int64")


def dist_stats(x: np.ndarray) -> dict:
    if len(x) == 0:
        return dict(n=0, median=None, p25=None, p75=None, mean=None, pct_ge2=None)
    return dict(
        n=int(len(x)),
        median=float(np.median(x)),
        p25=float(np.percentile(x, 25)),
        p75=float(np.percentile(x, 75)),
        mean=float(np.mean(x)),
        pct_ge2=float(100.0 * np.mean(x >= 2)),
    )


def lag_stats(x: np.ndarray) -> dict:
    if len(x) == 0:
        return dict(n=0, median=None, p75=None, p90=None)
    return dict(n=int(len(x)), median=float(np.median(x)),
                p75=float(np.percentile(x, 75)), p90=float(np.percentile(x, 90)))


def fmt(v, nd=2):
    return "—" if v is None else (f"{v:,.0f}" if isinstance(v, int) else f"{v:,.{nd}f}")


def season_label(sy: int) -> str:
    return f"{sy}-{str(sy + 1)[-2:]}"


def md_table(header: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join(["---"] * len(header)) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def main() -> int:
    S: dict = {}  # audit stats, dumped to data/p2_stats.json

    # ---------------- 311 complaints (P1 deliverable; null-bbl already excluded) ----
    c311 = pd.read_parquet(RAW / "c311_heat_complaints.parquet")
    S["c311_rows_in"] = len(c311)
    c_bbl = to_bbl_int(c311["bbl"])
    c_day = to_days(c311["created_date"])
    bad_c = int((c_bbl.isna() | c_day.isna()).sum())
    S["c311_excluded_unparsable_bbl_or_date"] = bad_c
    keep = c_bbl.notna() & c_day.notna()
    c_bbl = c_bbl[keep].astype("int64").to_numpy()
    c_day = c_day[keep].astype("int64").to_numpy()
    S["c311_rows_used"] = int(len(c_bbl))

    # 311 coverage bounds = actual calendar dates present (Amendment 3 eligibility)
    cov_lo, cov_hi = int(c_day.min()), int(c_day.max())
    S["c311_coverage"] = [str(np.datetime64(cov_lo, "D")), str(np.datetime64(cov_hi, "D"))]

    # sorted composite key for the window join (bbl * 1e5 + day; day << 1e5)
    ckey = c_bbl * DAY_MOD + c_day
    order = np.argsort(ckey, kind="stable")
    ckey_sorted = ckey[order]
    cday_sorted = c_day[order]

    # ---------------- violations waterfall --------------------------------------
    viol = pd.read_parquet(RAW / "hpd_violations_heat.parquet")
    S["viol_rows_in"] = len(viol)

    # (1) EXPLICIT class-C restriction (§3) on the B+C superset cache
    n_b = int((viol["class"] != "C").sum())
    viol = viol[viol["class"] == "C"].copy()
    S["viol_excluded_not_class_C"] = n_b
    S["viol_class_C"] = len(viol)

    # (2) exact duplicate violationid rows
    n_dup = int(viol.duplicated(subset="violationid").sum())
    viol = viol.drop_duplicates(subset="violationid", keep="first")
    S["viol_excluded_duplicate_violationid"] = n_dup

    # (3) bbl / inspectiondate parseability
    v_bbl = to_bbl_int(viol["bbl"])
    v_day = to_days(viol["inspectiondate"])
    S["viol_excluded_null_or_bad_bbl"] = int(v_bbl.isna().sum())
    S["viol_excluded_bad_inspectiondate"] = int((v_bbl.notna() & v_day.isna()).sum())
    keep = v_bbl.notna() & v_day.notna()
    viol = viol[keep]
    v_bbl = v_bbl[keep].astype("int64").to_numpy()
    v_day = v_day[keep].astype("int64").to_numpy()

    # (4) Amendment 3 window-coverage eligibility at the wider W=30:
    #     [inspectiondate-30, inspectiondate] must lie inside [cov_lo, cov_hi]
    left_edge = (v_day - 30) < cov_lo
    right_edge = v_day > cov_hi
    S["viol_excluded_coverage_left_edge"] = int(left_edge.sum())
    S["viol_excluded_coverage_right_edge"] = int(right_edge.sum())
    keep = ~(left_edge | right_edge)
    viol, v_bbl, v_day = viol[keep], v_bbl[keep], v_day[keep]

    # (5) season restriction: 2019-20 .. 2025-26, Oct-May only
    v_season = season_of_days(v_day)
    off = v_season == -1
    out_list = (~off) & ~np.isin(v_season, SEASONS)
    S["viol_excluded_offseason_jun_sep"] = int(off.sum())
    S["viol_excluded_season_out_of_list"] = int(out_list.sum())
    keep = (~off) & (~out_list)
    viol, v_bbl, v_day, v_season = viol[keep], v_bbl[keep], v_day[keep], v_season[keep]
    n_elig = len(viol)
    S["viol_eligible"] = int(n_elig)
    if n_elig == 0:
        raise RuntimeError("EMPTY eligible violation set — HARD STOP (Rules 1, 9).")

    # rows-per-(bbl, inspectiondate) diagnostic (NOT deduped — §3 unit is the row)
    grp = pd.Series(1, index=pd.MultiIndex.from_arrays([v_bbl, v_day])).groupby(level=[0, 1]).size()
    S["incident_rows_per_bbl_day"] = {
        "n_bbl_days": int(len(grp)), "mean": round(float(grp.mean()), 4),
        "pct_bbl_days_ge2_rows": round(float(100 * (grp >= 2).mean()), 2),
        "max": int(grp.max()),
    }

    # ---------------- PLUTO unit counts ------------------------------------------
    pluto = pd.read_parquet(RAW / "pluto_units.parquet")
    S["pluto_rows_in"] = len(pluto)
    p_bbl = to_bbl_int(pluto["bbl"])
    p_units = pd.to_numeric(pluto["unitstotal"], errors="coerce")
    pl = pd.DataFrame({"bbl": p_bbl, "units": p_units}).dropna()
    S["pluto_excluded_null_bbl_or_units"] = int(len(pluto) - len(pl))
    pl["bbl"] = pl["bbl"].astype("int64")
    nun = pl.groupby("bbl")["units"].nunique()
    conflict = set(nun[nun > 1].index)
    S["pluto_bbl_conflicting_units_excluded"] = int(len(conflict))
    pl = pl[~pl["bbl"].isin(conflict)].drop_duplicates(subset="bbl")
    S["pluto_usable_bbls"] = int(len(pl))
    units_map = pd.Series(pl["units"].to_numpy(), index=pl["bbl"].to_numpy())

    v_units = units_map.reindex(v_bbl).to_numpy()  # NaN where unmatched
    matched = ~np.isnan(v_units)
    S["unit_join_matched"] = int(matched.sum())
    S["unit_join_match_rate_pct"] = round(float(100 * matched.mean()), 2)
    S["unit_join_unmatched_excluded_from_class_strata_and_gate"] = int((~matched).sum())

    # ---------------- association counts, BOTH windows in one join ----------------
    counts = {}
    for W in (14, 30):
        lo = np.searchsorted(ckey_sorted, v_bbl * DAY_MOD + (v_day - W), side="left")
        hi = np.searchsorted(ckey_sorted, v_bbl * DAY_MOD + v_day, side="right")
        counts[W] = (hi - lo).astype("int64")
    lo30 = np.searchsorted(ckey_sorted, v_bbl * DAY_MOD + (v_day - 30), side="left")
    hi30 = np.searchsorted(ckey_sorted, v_bbl * DAY_MOD + v_day, side="right")

    # complaint-side association over the SAME eligible violation set (multiplicity)
    vkey = v_bbl * DAY_MOD + v_day
    vorder = np.argsort(vkey, kind="stable")
    vkey_sorted = vkey[vorder]
    vday_sorted = v_day[vorder]
    mult = {}
    for W in (14, 30):
        clo = np.searchsorted(vkey_sorted, c_bbl * DAY_MOD + c_day, side="left")
        chi = np.searchsorted(vkey_sorted, c_bbl * DAY_MOD + (c_day + W), side="right")
        m = chi - clo
        # consistency check: total pairs must match from both sides
        assert int(m.sum()) == int(counts[W].sum()), f"pair-sum mismatch at W={W}"
        mult[W] = dict(
            complaints_assoc_ge1=int((m >= 1).sum()),
            complaints_assoc_ge2=int((m >= 2).sum()),
            multiplicity_rate_pct=round(float(100 * (m >= 2).sum() / max((m >= 1).sum(), 1)), 2),
            total_pairs=int(m.sum()),
        )
        if W == 30:
            has = m >= 1
            c_first_lag = vday_sorted[clo[has]] - c_day[has]  # first inspection >= created
    S["multiplicity"] = mult

    # pair-level lags at W=30 (primary, mandatory for HOLD)
    lens = (hi30 - lo30)
    tot = int(lens.sum())
    S["pairs_w30"] = tot
    if tot == 0:
        raise RuntimeError("ZERO associated pairs at W=30 — schema-level surprise, HARD STOP (Rule 9).")
    starts_rep = np.repeat(lo30, lens)
    within = np.arange(tot) - np.repeat(np.cumsum(lens) - lens, lens)
    pair_lag = np.repeat(v_day, lens) - cday_sorted[starts_rep + within]
    pair_season = np.repeat(v_season, lens)

    # ---------------- tables -------------------------------------------------------
    unit_class = np.full(n_elig, "", dtype=object)
    for lo_u, hi_u in UNIT_BINS:
        lab = f"{lo_u}-{hi_u}" if hi_u else f"{lo_u}+"
        sel = matched & (v_units >= lo_u) & (v_units <= (hi_u or np.inf))
        unit_class[sel] = lab
    S["viol_matched_units_lt2_outside_class_bins"] = int((matched & (v_units < 2)).sum())

    by_class = {W: {} for W in (14, 30)}
    for W in (14, 30):
        for lo_u, hi_u in UNIT_BINS:
            lab = f"{lo_u}-{hi_u}" if hi_u else f"{lo_u}+"
            by_class[W][lab] = dist_stats(counts[W][unit_class == lab])
    by_season = {W: {season_label(sy): dist_stats(counts[W][v_season == sy])
                     for sy in SEASONS} for W in (14, 30)}
    cross = {W: {season_label(sy): {lab: dist_stats(
        counts[W][(v_season == sy) & (unit_class == lab)])
        for lab in [f"{a}-{b}" if b else f"{a}+" for a, b in UNIT_BINS]}
        for sy in SEASONS} for W in (14, 30)}
    S["dist_by_class"] = by_class
    S["dist_by_season"] = by_season

    # zero-complaint diagnostic
    zero = {W: dict(pooled=round(float(100 * (counts[W] == 0).mean()), 2),
                    by_season={season_label(sy): round(float(100 * (counts[W][v_season == sy] == 0).mean()), 2)
                               for sy in SEASONS})
            for W in (14, 30)}
    S["pct_zero_complaints"] = zero

    # THE GATE (Amendment 1): median at W=14, buildings with unitstotal >= 10, pooled
    ge10 = matched & (v_units >= 10)
    S["gate_n_ge10"] = int(ge10.sum())
    gate14 = float(np.median(counts[14][ge10]))
    gate30 = float(np.median(counts[30][ge10]))
    S["gate_median_w14_ge10units"] = gate14
    S["gate_median_w30_ge10units"] = gate30
    if gate14 >= 2:
        branch = "PASS@14 → GO on channel (a)"
    elif gate30 >= 2:
        branch = "FAIL@14 ∧ PASS@30 → HOLD (Ayur adjudicates with the lag distribution)"
    else:
        branch = "FAIL@14 ∧ FAIL@30 → KILL"
    S["gate_branch"] = branch

    # lag distributions (median/p75/p90, per season + pooled)
    lag_pair = {"pooled": lag_stats(pair_lag)}
    lag_pair.update({season_label(sy): lag_stats(pair_lag[pair_season == sy]) for sy in SEASONS})
    lag_first = lag_stats(c_first_lag)
    S["lag_pair_w30"] = lag_pair
    S["lag_first_inspection_w30_pooled"] = lag_first

    # complaints-per-unit vs unit count (secondary §3 diagnostic; complaint-positive
    # buildings only — the zero mass is P4's domain)
    cb = pd.Series(c_bbl).value_counts()
    cb_units = units_map.reindex(cb.index)
    ok = cb_units.notna() & (cb_units >= 2)
    S["cpu_match_rate_pct"] = round(float(100 * cb_units.notna().mean()), 2)
    cpu = (cb[ok] / cb_units[ok]).to_numpy()
    cu = cb_units[ok].to_numpy()
    cpu_tbl = {}
    for lo_u, hi_u in UNIT_BINS:
        lab = f"{lo_u}-{hi_u}" if hi_u else f"{lo_u}+"
        sel = (cu >= lo_u) & (cu <= (hi_u or np.inf))
        cpu_tbl[lab] = dict(n_buildings=int(sel.sum()),
                            median=round(float(np.median(cpu[sel])), 3),
                            mean=round(float(np.mean(cpu[sel])), 3))
    S["complaints_per_unit_by_class"] = cpu_tbl

    # ---------------- checkpoint markdown ------------------------------------------
    classes = [f"{a}-{b}" if b else f"{a}+" for a, b in UNIT_BINS]

    def stats_rows(d):
        return [[k, fmt(v["n"], 0), fmt(v["median"]), fmt(v["p25"]), fmt(v["p75"]),
                 fmt(v["mean"]), fmt(v["pct_ge2"])] for k, v in d.items()]

    hdr = ["stratum", "n violations", "median", "p25", "p75", "mean", "% ≥2"]
    lines = [
        "# phase0_p2_duplicates.md — P2 kill-gate checkpoint (A-GATE)",
        "",
        "Generated by `src/p2_gate.py` (idempotent, seed 42). Inputs: the three P1",
        "caches (sha-stable parquets, PROVENANCE 2026-07-16). Governing text:",
        "phase0_probe.md §3 + Amendment 1 (W=14 gate, HOLD branch, 311-only",
        "association) + Amendment 3 item 2 (window-coverage eligibility).",
        "",
        "## Method statements (checkable; R-AUDIT re-derives blind)",
        "",
        "- **Class-C restriction applied explicitly**: the P1 cache is the verbatim",
        f"  frozen-whitelist B+C superset; {S['viol_excluded_not_class_C']} non-class-C row(s) removed here",
        f"  ({S['viol_rows_in']:,} → {S['viol_class_C']:,}). This resolves the P1-audit flag in-code, as required.",
        "- **Window bounds INCLUSIVE both ends**: complaint associated iff same bbl and",
        "  `inspectiondate − W ≤ created_date ≤ inspectiondate` on CALENDAR DATES",
        "  (naive local NYC time truncated to day; inspectiondate is midnight-stamped",
        "  so truncation is lossless there). Same-day complaints count as associated;",
        "  day precision cannot resolve intraday order.",
        "- **bbl dtype**: all three sources normalized to int64 (PLUTO decimal-string",
        "  form parsed numerically); unparsable/≤0 excluded and counted below.",
        "- **No silent dedupe**: violation rows are the §3 unit (multiple rows per",
        "  (bbl, inspectiondate) retained; diagnostic below). Complaint→multi-violation",
        "  multiplicity reported, not deduped.",
        "- **Percentiles**: numpy linear interpolation; medians on integer counts.",
        "- Seasons: NYC heat season Oct 1–May 31 labeled by start year (definition",
        "  identical to the frozen label spine's); P2 list 2019-20 … 2025-26.",
        "",
        "## Eligibility waterfall (every exclusion counted; Amendment 3)",
        "",
        f"- Violations cache in: **{S['viol_rows_in']:,}**",
        f"- − not class C (explicit §3 restriction): **{S['viol_excluded_not_class_C']}** → {S['viol_class_C']:,}",
        f"- − exact duplicate violationid rows: **{S['viol_excluded_duplicate_violationid']}**",
        f"- − null/unparsable/zero bbl: **{S['viol_excluded_null_or_bad_bbl']}** (185 null/empty per",
        "  PROVENANCE + 12 literal `bbl='0'` placeholder rows; zero-BBLs would spuriously",
        "  cross-match each other, so they are unusable, counted, excluded)",
        f"- − unparsable inspectiondate: **{S['viol_excluded_bad_inspectiondate']}**",
        f"- − **coverage-excluded (Amendment 3, full W=30 window must lie in 311 coverage",
        f"  {S['c311_coverage'][0]} … {S['c311_coverage'][1]})**: left edge **{S['viol_excluded_coverage_left_edge']:,}**,",
        f"  right edge **{S['viol_excluded_coverage_right_edge']:,}**",
        f"- − off-season (Jun–Sep): **{S['viol_excluded_offseason_jun_sep']:,}**;"
        f" out-of-list season: **{S['viol_excluded_season_out_of_list']:,}**",
        f"- **Eligible violations entering distributions/gate: {S['viol_eligible']:,}**",
        "",
        f"311 deliverable rows used: {S['c311_rows_used']:,} of {S['c311_rows_in']:,}",
        f"(excluded: {S['c311_excluded_unparsable_bbl_or_date']} rows, all literal `bbl='0000000000'`",
        "placeholders — null-bbl rows were already excluded in P1; zero is not a real BBL).",
        "",
        "## Unit-count join (PLUTO)",
        "",
        f"- PLUTO usable bbls: {S['pluto_usable_bbls']:,} (excluded null bbl/units:",
        f"  {S['pluto_excluded_null_bbl_or_units']}; conflicting-units bbls excluded:",
        f"  {S['pluto_bbl_conflicting_units_excluded']} — never defaulted).",
        f"- **Match rate on eligible violations: {S['unit_join_match_rate_pct']}%**",
        f"  ({S['unit_join_matched']:,} matched; {S['unit_join_unmatched_excluded_from_class_strata_and_gate']:,}",
        "  unmatched → excluded from unit-class strata and the gate cell, retained in",
        "  season margins).",
        f"- Matched with unitstotal < 2 (outside §3 class bins): {S['viol_matched_units_lt2_outside_class_bins']:,}.",
        "",
        "## THE GATE (Amendment 1 — evaluated at W=14; ≥10-unit buildings, pooled seasons)",
        "",
        f"- n (eligible, matched, unitstotal ≥ 10): **{S['gate_n_ge10']:,}**",
        f"- **median associated complaints @ W=14: {gate14:g}**",
        f"- **median associated complaints @ W=30: {gate30:g}**",
        f"- Pre-committed branch fired: **{branch}**",
        "",
        "(A-GATE states the branch; adjudication of HOLD and the memo verdict is",
        "Ayur's alone. Thresholds cited from phase0_probe.md §3 + Amendment 1,",
        "not restated.)",
        "",
        "## Distribution: associated complaints per eligible violation",
        "",
        "### By unit-count class (pooled seasons) — W=14",
        md_table(hdr, stats_rows(by_class[14])),
        "",
        "### By unit-count class (pooled seasons) — W=30",
        md_table(hdr, stats_rows(by_class[30])),
        "",
        "### By season (all eligible violations incl. PLUTO-unmatched) — W=14",
        md_table(hdr, stats_rows(by_season[14])),
        "",
        "### By season — W=30",
        md_table(hdr, stats_rows(by_season[30])),
        "",
        "### Season × unit-class medians (compact cross-tab)",
        md_table(["season"] + [f"{c} @14" for c in classes] + [f"{c} @30" for c in classes],
                 [[season_label(sy)]
                  + [fmt(cross[14][season_label(sy)][c]["median"]) for c in classes]
                  + [fmt(cross[30][season_label(sy)][c]["median"]) for c in classes]
                  for sy in SEASONS]),
        "",
        "## Multiplicity (complaint → multiple violations; reported, never deduped)",
        "",
        md_table(["W", "complaints w/ ≥1 assoc", "w/ ≥2", "multiplicity rate %", "total pairs"],
                 [[str(W), f"{mult[W]['complaints_assoc_ge1']:,}", f"{mult[W]['complaints_assoc_ge2']:,}",
                   f"{mult[W]['multiplicity_rate_pct']}", f"{mult[W]['total_pairs']:,}"]
                  for W in (14, 30)]),
        "",
        "Pair totals cross-checked: violation-side and complaint-side sums match",
        "exactly at both windows (asserted in-code).",
        "",
        "## Zero-complaint violations (candidate proactive events — feeds P3)",
        "",
        md_table(["W", "pooled %zero"] + [season_label(sy) for sy in SEASONS],
                 [[str(W), fmt(zero[W]["pooled"])] +
                  [fmt(zero[W]["by_season"][season_label(sy)]) for sy in SEASONS]
                  for W in (14, 30)]),
        "",
        "## Complaint→inspection lag (MANDATORY — the HOLD branch consumes this)",
        "",
        "Primary: lag in days over all associated PAIRS at W=30, season = season of",
        "the violation. Secondary: per-complaint lag to its FIRST associated",
        "inspection within 30 days (pooled).",
        "",
        md_table(["stratum", "n", "median", "p75", "p90"],
                 [[k, f"{v['n']:,}", fmt(v["median"]), fmt(v["p75"]), fmt(v["p90"])]
                  for k, v in lag_pair.items()]),
        "",
        f"Per-complaint first-inspection lag (pooled): n={lag_first['n']:,},",
        f"median={fmt(lag_first['median'])}, p75={fmt(lag_first['p75'])}, p90={fmt(lag_first['p90'])}.",
        "",
        "## Secondary: complaints-per-unit vs unit count (raw propensity shape)",
        "",
        "Building-level: total in-scope 311 complaints (full coverage window) ÷",
        "unitstotal, complaint-positive buildings with units ≥ 2 only (the zero-311",
        f"mass is P4's domain). PLUTO match rate on complaint bbls: {S['cpu_match_rate_pct']}%.",
        "",
        md_table(["unit class", "n buildings", "median complaints/unit", "mean"],
                 [[lab, f"{d['n_buildings']:,}", fmt(d["median"], 3), fmt(d["mean"], 3)]
                  for lab, d in cpu_tbl.items()]),
        "",
        "## Diagnostics / anomalies",
        "",
        f"- Violation rows per (bbl, inspectiondate): {S['incident_rows_per_bbl_day']['n_bbl_days']:,}",
        f"  building-days; mean {S['incident_rows_per_bbl_day']['mean']} rows;",
        f"  {S['incident_rows_per_bbl_day']['pct_bbl_days_ge2_rows']}% of building-days carry ≥2 rows",
        f"  (max {S['incident_rows_per_bbl_day']['max']}). Rows NOT collapsed — §3's unit is the violation row.",
        "",
        "Full machine-readable stats: `data/p2_stats.json`.",
    ]
    CKPT.parent.mkdir(parents=True, exist_ok=True)
    CKPT.write_text("\n".join(lines) + "\n")
    STATS.write_text(json.dumps(S, indent=2, default=str))
    print(f"[p2] eligible={n_elig:,}  gate n(>=10u)={S['gate_n_ge10']:,}  "
          f"median@14={gate14:g}  median@30={gate30:g}")
    print(f"[p2] branch: {branch}")
    print(f"[p2] wrote {CKPT} and {STATS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
