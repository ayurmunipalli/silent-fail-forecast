"""P4 — zero-mass structure, DESCRIPTIVE ONLY (phase0_probe.md §5; gates nothing).

Idempotent: rerun with `.venv/bin/python src/p4_zeromass.py` (--force re-pulls raw).
Writes outputs/checkpoints/phase0_p4_zeromass.md + data/p4_stats.json +
outputs/figures/phase0_p4_zeromass.svg (vector — nothing raster touches disk).
Seed 42 (Rule 7; no sampling occurs). Never fabricates: empty pull or schema
surprise raises and stops (Rules 1, 9). Exclusions are LOGGED, never imputed.

This probe answers §5's question ON RECORD as DESCRIPTION: does the zero-311 mass
have covariate support overlapping the complaint-positive mass, or is it disjoint?
No verdict language appears here; nothing in P4 gates anything.

UNIVERSE: the 181,863 distinct buildings (bbl) of the frozen winter-fail-forecast
label spine (`imports/building_season_labels.parquet`, R4 artifact, read-only) —
the same universe behind WFF's "~70% zero-311" measurement. Zero mass = spine
buildings with ZERO whitelisted heat/hot-water 311 complaints in the P1
complaint-level deliverable (full coverage 2019-06-01…2026-07-13);
complaint-positive mass = >= 1. (WFF's ~70% was measured on its own 311 window;
the share measured here on this window is reported alongside, not reconciled.)

SOURCES (verified live 2026-07-16, Rule 5):
  64uk-42ks  PLUTO — supplementary P4 pull: bbl,cd,bct2020 (geo for CD income +
             tract LEP; the s3d geo pull ported to this repo, pulled FRESH).
  api.census.gov/data/2024/acs/acs5 — ACS 2020-2024 5-year, tract level, NYC's
             five counties. Verified live 2026-07-16 with key (HTTP 200, all
             seven variables resolve). Census requires a key for ALL queries
             (since 2026-05-12, per WFF PROVENANCE); key from `.env`, NEVER
             printed (Rule 2). Keyless probe returns an HTML "Missing Key" page
             (recorded).

CD-INCOME MACHINERY ported from winter-fail-forecast src/s3d_income_equity.py
(read-only reference; identical semantics):
  - building -> CD directly from PLUTO `cd`;
  - CD median household income = household-weighted mean of its tracts' ACS
    B19013 medians (B11001 households as weights), tracts assigned to CD by
    dominant residential-lot count in PLUTO;
  - income tercile = building-level rank qcut(3) on CD income (rank method
    "first" after a deterministic sort — seed-42-stable and identical in
    semantics to s3d/s3c).

TRACT LEP SHARE (new here; §5 names the quantity, the variable is fixed as):
  ACS table C16002 (household language by limited-English-speaking status):
  LEP share = (C16002_004E + 007E + 010E + 013E) / C16002_001E
  = share of limited-English-speaking HOUSEHOLDS in the tract. Tracts with
  C16002_001E == 0 have undefined LEP share -> excluded from LEP strata, counted.

FIXED DECISIONS:
1. Borough from the bbl's leading digit (1=MN,2=BX,3=BK,4=QN,5=SI) — complete,
   no join loss.
2. Unit counts from the P1 `pluto_units` cache with P2's exact hygiene
   (conflicting-unitstotal bbls excluded and counted, never defaulted).
3. Unit classes: the §3 bins {2-5, 6-19, 20-49, 50+} plus "<2" and "unmatched"
   accounting rows (spine buildings outside the bins are shown, not dropped).
4. SUPPORT-OVERLAP DESCRIPTIVE: cells = unit-class x borough x income-tercile x
   LEP-tercile over buildings with complete covariates; report the share of
   zero-mass buildings whose cell also contains >=1 (and >=10) complaint-positive
   buildings, and the reverse. This is a description of common support, not a test.
5. All strata terciles computed over the covered universe (both masses pooled),
   so the two masses are placed on one common scale.
"""
from __future__ import annotations

import http.client
import json
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from dotenv import dotenv_values

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "data" / "raw"
CKPT = REPO / "outputs" / "checkpoints" / "phase0_p4_zeromass.md"
FIG = REPO / "outputs" / "figures" / "phase0_p4_zeromass.svg"
STATS = REPO / "data" / "p4_stats.json"

FORCE = "--force" in sys.argv
ENV = dotenv_values(REPO / ".env")
TOKEN = (ENV.get("SOCRATA_APP_TOKEN") or "").strip()
HDR = {"X-App-Token": TOKEN} if TOKEN else {}
BASE = "https://data.cityofnewyork.us/resource"
PAGE = 50000
STORAGE_BUDGET_BYTES = 2_000_000_000  # Rule 6

random.seed(42)
np.random.seed(42)  # Rule 7 — no sampling occurs; set for consistency

ACS_YEAR = 2024
NYC_COUNTIES = ["005", "047", "061", "081", "085"]  # BX, BK, MN, QN, SI (state 36)
BORO_TO_COUNTY = {"1": "061", "2": "005", "3": "047", "4": "081", "5": "085"}
BORO_NAME = {1: "MN", 2: "BX", 3: "BK", 4: "QN", 5: "SI"}
ACS_VARS = ["B19013_001E", "B11001_001E", "C16002_001E",
            "C16002_004E", "C16002_007E", "C16002_010E", "C16002_013E"]
UNIT_BINS = [(2, 5), (6, 19), (20, 49), (50, None)]  # §3 classes
TERC_LABELS = ["T1_low", "T2_mid", "T3_high"]


def _get(url: str, hdr: dict | None = None):
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers=hdr if hdr is not None else HDR)
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.load(r)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
                http.client.IncompleteRead, json.JSONDecodeError):
            if attempt == 5:
                raise
            time.sleep(2 ** attempt)


def _guard_storage():
    used = sum(f.stat().st_size for f in RAW.rglob("*") if f.is_file())
    if used > STORAGE_BUDGET_BYTES:
        raise RuntimeError(f"STORAGE BREACH: data/raw at {used/1e9:.2f} GB > 2 GB — HALT (Rule 6).")
    return used


def pull(name: str, dataset: str, select: str, where: str | None = None) -> pd.DataFrame:
    cache = RAW / f"{name}.parquet"
    if cache.exists() and not FORCE:
        df = pd.read_parquet(cache)
        print(f"[cache] {name}: {len(df):,} rows  ({cache})")
        return df
    expected_cols = set(select.split(","))
    rows, offset = [], 0
    while True:
        params = {"$select": select, "$limit": PAGE, "$offset": offset, "$order": ":id"}
        if where:
            params["$where"] = where
        batch = _get(f"{BASE}/{dataset}.json?" + urllib.parse.urlencode(params))
        if batch and not set(batch[0]).issubset(expected_cols):
            raise RuntimeError(f"SCHEMA SURPRISE for {name}: got {sorted(batch[0])} — HARD STOP (Rule 9).")
        if not batch:
            break
        rows.extend(batch)
        offset += PAGE
        if len(batch) < PAGE:
            break
    if not rows:
        raise RuntimeError(f"EMPTY PULL for {name} ({dataset}) — HARD STOP, no placeholder (Rule 1).")
    df = pd.DataFrame(rows).reindex(columns=select.split(","))
    df.to_parquet(cache, index=False)
    _guard_storage()
    print(f"[pull] {name}: {len(df):,} rows -> {cache}")
    return df


def pull_acs() -> pd.DataFrame:
    """ACS 2020-2024 5-year, tract level, all P4 variables, NYC counties.
    Key from .env, NEVER printed. Cached, idempotent."""
    cache = RAW / f"acs_tract_{ACS_YEAR}.parquet"
    if cache.exists() and not FORCE:
        df = pd.read_parquet(cache)
        print(f"[cache] acs_tract_{ACS_YEAR}: {len(df):,} tracts  ({cache})")
        return df
    key = (ENV.get("CENSUS_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("CREDENTIAL FAILURE: CENSUS_API_KEY missing/empty — HARD STOP (Rule 9), no placeholder.")
    frames = []
    for county in NYC_COUNTIES:
        params = {"get": ",".join(ACS_VARS), "for": "tract:*",
                  "in": f"state:36 county:{county}", "key": key}
        url = f"https://api.census.gov/data/{ACS_YEAR}/acs/acs5?" + urllib.parse.urlencode(params)
        data = _get(url, hdr={})
        cols, rows = data[0], data[1:]
        frames.append(pd.DataFrame(rows, columns=cols))
    df = pd.concat(frames, ignore_index=True)
    if df.empty:
        raise RuntimeError("EMPTY ACS pull — HARD STOP (Rule 1).")
    for v in ACS_VARS:
        df[v] = pd.to_numeric(df[v], errors="coerce")
    df.loc[df["B19013_001E"] < 0, "B19013_001E"] = np.nan  # Census null sentinels (-666666666)
    df["tract6"] = df["tract"].astype(str).str.zfill(6)
    df["county"] = df["county"].astype(str).str.zfill(3)
    df.to_parquet(cache, index=False)
    _guard_storage()
    print(f"[pull] acs_tract_{ACS_YEAR}: {len(df):,} tracts -> {cache} "
          f"(median-income non-null {df['B19013_001E'].notna().mean():.1%})")
    return df


def to_bbl_int(s: pd.Series) -> pd.Series:
    v = pd.to_numeric(s, errors="coerce")
    v = v.where(v > 0)
    return v.round().astype("Int64")


def rank_tercile(x: pd.Series) -> pd.Series:
    """Building-level rank qcut(3) — s3d's tercile method (rank 'first' over a
    deterministically ordered frame; stable, seed-independent)."""
    return pd.qcut(x.rank(method="first"), 3, labels=TERC_LABELS).astype(str)


def md_table(header: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join(["---"] * len(header)) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def pct(x, n) -> str:
    return f"{100.0 * x / n:.1f}%" if n else "—"


def main() -> int:
    S: dict = {}

    # ---------------- universe: frozen spine (R4), zero vs positive mass ----------
    spine = pd.read_parquet(REPO / "imports" / "building_season_labels.parquet",
                            columns=["bbl_n"])
    uni = pd.DataFrame({"bbl": np.sort(spine["bbl_n"].unique())})
    S["universe_buildings"] = int(len(uni))

    c311 = pd.read_parquet(RAW / "c311_heat_complaints.parquet", columns=["bbl", "created_date"])
    cb = to_bbl_int(c311["bbl"]).dropna().astype("int64")
    ccounts = cb.value_counts()
    S["c311_coverage"] = [str(pd.to_datetime(c311["created_date"]).min().date()),
                          str(pd.to_datetime(c311["created_date"]).max().date())]
    uni["n_c311"] = uni["bbl"].map(ccounts).fillna(0).astype(int)
    uni["mass"] = np.where(uni["n_c311"] == 0, "zero", "positive")
    S["zero_buildings"] = int((uni["mass"] == "zero").sum())
    S["positive_buildings"] = int((uni["mass"] == "positive").sum())
    S["zero_share_pct"] = round(100 * S["zero_buildings"] / S["universe_buildings"], 1)
    S["c311_bbls_outside_spine"] = int((~pd.Index(ccounts.index).isin(uni["bbl"])).sum())

    # ---------------- covariate 1: unit counts (P1 cache, P2 hygiene) -------------
    pluto_u = pd.read_parquet(RAW / "pluto_units.parquet")
    p_bbl = to_bbl_int(pluto_u["bbl"])
    p_units = pd.to_numeric(pluto_u["unitstotal"], errors="coerce")
    pl = pd.DataFrame({"bbl": p_bbl, "units": p_units}).dropna()
    pl["bbl"] = pl["bbl"].astype("int64")
    nun = pl.groupby("bbl")["units"].nunique()
    conflict = set(nun[nun > 1].index)
    S["pluto_bbl_conflicting_units_excluded"] = int(len(conflict))
    pl = pl[~pl["bbl"].isin(conflict)].drop_duplicates(subset="bbl")
    uni = uni.merge(pl, on="bbl", how="left")
    S["units_unmatched"] = int(uni["units"].isna().sum())

    def unit_class(u):
        if np.isnan(u):
            return "unmatched"
        if u < 2:
            return "<2"
        for lo, hi in UNIT_BINS:
            if u >= lo and (hi is None or u <= hi):
                return f"{lo}-{hi}" if hi else f"{lo}+"
        return "unmatched"

    uni["unit_class"] = [unit_class(u) for u in uni["units"].to_numpy(dtype=float)]

    # ---------------- covariate 2: borough (bbl leading digit; complete) ----------
    uni["borough"] = (uni["bbl"] // 1_000_000_000).map(BORO_NAME)
    S["borough_unmapped"] = int(uni["borough"].isna().sum())

    # ---------------- covariates 3+4: CD income tercile + tract LEP share ---------
    geo = pull("pluto_geo", "64uk-42ks", "bbl,cd,bct2020")
    geo = geo.assign(bbl_i=to_bbl_int(geo["bbl"])).dropna(subset=["bbl_i"])
    geo["bbl_i"] = geo["bbl_i"].astype("int64")
    geo["boro_digit"] = geo["bct2020"].astype(str).str[0]
    geo["county"] = geo["boro_digit"].map(BORO_TO_COUNTY)
    geo["tract6"] = geo["bct2020"].astype(str).str[1:7]
    geo = geo.drop_duplicates(subset="bbl_i")

    acs = pull_acs()
    acs["lep_share"] = np.where(
        acs["C16002_001E"] > 0,
        (acs["C16002_004E"] + acs["C16002_007E"] + acs["C16002_010E"] + acs["C16002_013E"])
        / acs["C16002_001E"], np.nan)
    S["acs_tracts"] = int(len(acs))
    S["acs_tracts_income_nonnull"] = int(acs["B19013_001E"].notna().sum())
    S["acs_tracts_lep_defined"] = int(acs["lep_share"].notna().sum())

    # CD income: household-weighted mean of tract medians; tract->CD by dominant lot count
    g_ok = geo[geo["county"].notna() & geo["cd"].notna() & (geo["tract6"].str.len() == 6)]
    tract_cd = (g_ok.groupby(["county", "tract6", "cd"]).size().reset_index(name="lots")
                .sort_values(["lots", "cd"]).drop_duplicates(["county", "tract6"], keep="last")
                [["county", "tract6", "cd"]])
    a = acs.merge(tract_cd, on=["county", "tract6"], how="inner")
    a_inc = a[a["B19013_001E"].notna() & (a["B11001_001E"] > 0)].copy()
    a_inc["wi"] = a_inc["B19013_001E"] * a_inc["B11001_001E"]
    cd_inc = a_inc.groupby("cd").agg(wi=("wi", "sum"), hh=("B11001_001E", "sum"))
    cd_inc["cd_medinc"] = cd_inc["wi"] / cd_inc["hh"]
    cd_inc = cd_inc.reset_index()[["cd", "cd_medinc"]]
    S["n_cds_with_income"] = int(len(cd_inc))

    uni = uni.merge(geo[["bbl_i", "cd", "county", "tract6"]].rename(columns={"bbl_i": "bbl"}),
                    on="bbl", how="left")
    uni = uni.merge(cd_inc, on="cd", how="left")
    uni = uni.merge(acs[["county", "tract6", "lep_share"]], on=["county", "tract6"], how="left")
    S["excl_no_pluto_geo"] = int(uni["cd"].isna().sum())
    S["excl_no_cd_income"] = int((uni["cd"].notna() & uni["cd_medinc"].isna()).sum())
    S["excl_no_lep"] = int((uni["cd"].notna() & uni["lep_share"].isna()).sum())

    # terciles over the covered universe (both masses pooled -> one common scale)
    uni = uni.sort_values("bbl").reset_index(drop=True)  # deterministic rank base
    inc_ok = uni["cd_medinc"].notna()
    lep_ok = uni["lep_share"].notna()
    uni.loc[inc_ok, "income_tercile"] = rank_tercile(uni.loc[inc_ok, "cd_medinc"])
    uni.loc[lep_ok, "lep_tercile"] = rank_tercile(uni.loc[lep_ok, "lep_share"])
    S["income_tercile_bands"] = {
        t: [round(float(uni.loc[uni["income_tercile"] == t, "cd_medinc"].min()), 0),
            round(float(uni.loc[uni["income_tercile"] == t, "cd_medinc"].max()), 0)]
        for t in TERC_LABELS}
    S["lep_tercile_bands"] = {
        t: [round(float(uni.loc[uni["lep_tercile"] == t, "lep_share"].min()), 4),
            round(float(uni.loc[uni["lep_tercile"] == t, "lep_share"].max()), 4)]
        for t in TERC_LABELS}

    # ---------------- distribution tables (zero vs positive) ----------------------
    zero = uni[uni["mass"] == "zero"]
    pos = uni[uni["mass"] == "positive"]
    n_z, n_p = len(zero), len(pos)

    def share_rows(col, order):
        rows = []
        for lvl in order:
            rows.append([lvl,
                         f"{int((zero[col] == lvl).sum()):,}", pct(int((zero[col] == lvl).sum()), n_z),
                         f"{int((pos[col] == lvl).sum()):,}", pct(int((pos[col] == lvl).sum()), n_p)])
        return rows

    unit_order = ["<2", "2-5", "6-19", "20-49", "50+", "unmatched"]
    boro_order = ["MN", "BX", "BK", "QN", "SI"]
    terc_order = TERC_LABELS + ["(uncovered)"]
    uni["income_tercile"] = uni["income_tercile"].fillna("(uncovered)")
    uni["lep_tercile"] = uni["lep_tercile"].fillna("(uncovered)")
    zero = uni[uni["mass"] == "zero"]
    pos = uni[uni["mass"] == "positive"]

    S["dist_unit_class"] = {m: d["unit_class"].value_counts().to_dict()
                            for m, d in [("zero", zero), ("positive", pos)]}
    S["units_median"] = {"zero": float(zero["units"].median()),
                         "positive": float(pos["units"].median())}
    S["units_p25_p75"] = {"zero": [float(zero["units"].quantile(q)) for q in (0.25, 0.75)],
                          "positive": [float(pos["units"].quantile(q)) for q in (0.25, 0.75)]}
    S["lep_median"] = {"zero": round(float(zero["lep_share"].median()), 4),
                       "positive": round(float(pos["lep_share"].median()), 4)}
    S["cd_medinc_median"] = {"zero": round(float(zero["cd_medinc"].median()), 0),
                             "positive": round(float(pos["cd_medinc"].median()), 0)}

    # ---------------- support-overlap descriptive (decision 4) --------------------
    complete = uni[(uni["unit_class"].isin(["2-5", "6-19", "20-49", "50+"]))
                   & (uni["income_tercile"].isin(TERC_LABELS))
                   & (uni["lep_tercile"].isin(TERC_LABELS))].copy()
    S["complete_covariate_buildings"] = int(len(complete))
    S["complete_zero"] = int((complete["mass"] == "zero").sum())
    S["complete_positive"] = int((complete["mass"] == "positive").sum())
    cell_cols = ["unit_class", "borough", "income_tercile", "lep_tercile"]
    cells = (complete.groupby(cell_cols + ["mass"]).size().unstack("mass", fill_value=0)
             .rename(columns={"zero": "n_zero", "positive": "n_pos"}).reset_index())
    for c in ("n_zero", "n_pos"):
        if c not in cells:
            cells[c] = 0
    S["n_cells_occupied"] = int(len(cells))
    z_tot = int(cells["n_zero"].sum())
    p_tot = int(cells["n_pos"].sum())
    S["overlap"] = dict(
        zero_in_cells_with_ge1_pos_n=int(cells.loc[cells["n_pos"] >= 1, "n_zero"].sum()),
        pos_in_cells_with_ge1_zero_n=int(cells.loc[cells["n_zero"] >= 1, "n_pos"].sum()),
        zero_in_cells_with_ge1_pos_pct=round(100 * cells.loc[cells["n_pos"] >= 1, "n_zero"].sum() / z_tot, 1),
        zero_in_cells_with_ge10_pos_pct=round(100 * cells.loc[cells["n_pos"] >= 10, "n_zero"].sum() / z_tot, 1),
        pos_in_cells_with_ge1_zero_pct=round(100 * cells.loc[cells["n_zero"] >= 1, "n_pos"].sum() / p_tot, 1),
        pos_in_cells_with_ge10_zero_pct=round(100 * cells.loc[cells["n_zero"] >= 10, "n_pos"].sum() / p_tot, 1),
        cells_zero_only=int(((cells["n_zero"] > 0) & (cells["n_pos"] == 0)).sum()),
        cells_pos_only=int(((cells["n_pos"] > 0) & (cells["n_zero"] == 0)).sum()),
        cells_both=int(((cells["n_pos"] > 0) & (cells["n_zero"] > 0)).sum()),
    )
    zero_only = cells[(cells["n_zero"] > 0) & (cells["n_pos"] == 0)]
    S["zero_only_cells_buildings"] = int(zero_only["n_zero"].sum())
    S["zero_only_cells_top"] = [
        dict(cell="|".join(str(r[c]) for c in cell_cols), n_zero=int(r["n_zero"]))
        for _, r in zero_only.nlargest(5, "n_zero").iterrows()]

    # share of zero mass by unit class (the propensity-relevant margin), for figure
    zshare_by_unit = (uni[uni["unit_class"].isin(["2-5", "6-19", "20-49", "50+"])]
                      .groupby("unit_class")["mass"].apply(lambda m: float((m == "zero").mean()))
                      .reindex(["2-5", "6-19", "20-49", "50+"]))
    S["zero_share_by_unit_class_pct"] = {k: round(100 * v, 1) for k, v in zshare_by_unit.items()}

    # ---------------- figure (SVG, vector) ----------------------------------------
    FIG.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    bins = np.logspace(0, np.log10(max(uni["units"].max(), 10)), 40)
    for m, color in [("zero", "#4477aa"), ("positive", "#cc6677")]:
        u = uni.loc[(uni["mass"] == m) & uni["units"].notna() & (uni["units"] >= 1), "units"]
        axes[0].hist(u, bins=bins, density=True, histtype="step", lw=1.6, label=m, color=color)
    axes[0].set_xscale("log")
    axes[0].set_xlabel("PLUTO unitstotal (log)")
    axes[0].set_ylabel("density")
    axes[0].set_title("Unit-count distribution by mass")
    axes[0].legend()

    x = np.arange(4)
    axes[1].bar(x, [zshare_by_unit.iloc[i] * 100 for i in range(4)], color="#4477aa")
    axes[1].set_xticks(x, ["2-5", "6-19", "20-49", "50+"])
    axes[1].set_ylabel("% of buildings with zero 311")
    axes[1].set_title("Zero-311 share by unit class")

    for m, color in [("zero", "#4477aa"), ("positive", "#cc6677")]:
        l = uni.loc[(uni["mass"] == m) & uni["lep_share"].notna(), "lep_share"]
        axes[2].hist(l, bins=40, density=True, histtype="step", lw=1.6, label=m, color=color)
    axes[2].set_xlabel("tract LEP household share (C16002)")
    axes[2].set_ylabel("density")
    axes[2].set_title("Tract LEP share by mass")
    axes[2].legend()
    fig.suptitle("P4 zero-mass structure (descriptive; gates nothing)", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG, format="svg")
    plt.close(fig)

    # ---------------- checkpoint ----------------------------------------------------
    ov = S["overlap"]
    lines = [
        "# phase0_p4_zeromass.md — P4 zero-mass descriptives (A-AUX)",
        "",
        "Generated by `src/p4_zeromass.py` (idempotent, seed 42). Governing text:",
        "phase0_probe.md §5. **Descriptive only — this probe gates nothing; no",
        "verdict appears here.** CD-income machinery ported from the read-only",
        "winter-fail-forecast `src/s3d_income_equity.py` (repo untouched).",
        "",
        "## Universe and masses",
        "",
        f"- Universe: **{S['universe_buildings']:,}** distinct buildings from the frozen",
        "  R4 label spine (`imports/building_season_labels.parquet`).",
        f"- Zero-311 mass (0 whitelisted heat/hot-water complaints,",
        f"  {S['c311_coverage'][0]}…{S['c311_coverage'][1]}): **{S['zero_buildings']:,}**",
        f"  (**{S['zero_share_pct']}%**). Complaint-positive: {S['positive_buildings']:,}.",
        f"- WFF's reference measurement was \"~70%\" on its own 311 window; the share",
        "  on this window is as stated above (reported, not reconciled).",
        f"- 311 bbls outside the spine universe: {S['c311_bbls_outside_spine']:,}",
        "  (non-spine lots; not part of §5's question).",
        "",
        "## Data and exclusions (logged, never imputed)",
        "",
        f"- ACS {ACS_YEAR} 5-year, tract level, five NYC counties: {S['acs_tracts']:,} tracts",
        f"  (income non-null {S['acs_tracts_income_nonnull']:,}; LEP defined {S['acs_tracts_lep_defined']:,};",
        "  Census sentinel -666666666 → null, zero-household tracts → LEP undefined).",
        f"- PLUTO geo (fresh `pluto_geo` pull): spine buildings without a PLUTO geo",
        f"  match: {S['excl_no_pluto_geo']:,}; with CD but no ACS income: {S['excl_no_cd_income']:,};",
        f"  without defined tract LEP: {S['excl_no_lep']:,}. Unit-count join: {S['units_unmatched']:,}",
        f"  unmatched; {S['pluto_bbl_conflicting_units_excluded']} conflicting-units bbls excluded.",
        f"- CD income covers {S['n_cds_with_income']} CDs (household-weighted tract-median",
        "  mean; dominant-lot tract→CD crosswalk — s3d method).",
        f"- Income tercile bands (CD $): {S['income_tercile_bands']}",
        f"- LEP tercile bands (share): {S['lep_tercile_bands']}",
        "",
        "## Distributions by mass (zero vs complaint-positive)",
        "",
        "### Unit-count class",
        "",
        md_table(["class", "zero n", "zero %", "positive n", "positive %"],
                 share_rows("unit_class", unit_order)),
        "",
        f"Median unitstotal: zero {S['units_median']['zero']:g} "
        f"(IQR {S['units_p25_p75']['zero'][0]:g}–{S['units_p25_p75']['zero'][1]:g}), "
        f"positive {S['units_median']['positive']:g} "
        f"(IQR {S['units_p25_p75']['positive'][0]:g}–{S['units_p25_p75']['positive'][1]:g}).",
        "",
        "### Borough",
        "",
        md_table(["borough", "zero n", "zero %", "positive n", "positive %"],
                 share_rows("borough", boro_order)),
        "",
        "### CD income tercile (common scale, both masses pooled)",
        "",
        md_table(["tercile", "zero n", "zero %", "positive n", "positive %"],
                 share_rows("income_tercile", terc_order)),
        "",
        f"Median CD income: zero ${S['cd_medinc_median']['zero']:,.0f},",
        f"positive ${S['cd_medinc_median']['positive']:,.0f}.",
        "",
        "### Tract LEP-share tercile",
        "",
        md_table(["tercile", "zero n", "zero %", "positive n", "positive %"],
                 share_rows("lep_tercile", terc_order)),
        "",
        f"Median tract LEP share: zero {S['lep_median']['zero']:.3f},",
        f"positive {S['lep_median']['positive']:.3f}.",
        "",
        f"Zero-311 share by unit class: " + ", ".join(
            f"{k}: {v}%" for k, v in S["zero_share_by_unit_class_pct"].items()) + ".",
        "",
        "## §5's question on record — answered as DESCRIPTION",
        "",
        "*\"Does the zero-complaint mass have covariate support overlapping the",
        "complaint-positive mass (propensity extrapolation feasible), or is it a",
        "disjoint population (extrapolation = assumption, to be stated in the spec)?\"*",
        "",
        f"Over the {S['complete_covariate_buildings']:,} buildings with complete covariates",
        f"({S['complete_zero']:,} zero, {S['complete_positive']:,} positive), in",
        f"{S['n_cells_occupied']} occupied cells of unit-class × borough × income-tercile ×",
        "LEP-tercile:",
        "",
        f"- **{ov['zero_in_cells_with_ge1_pos_pct']}%** of zero-mass buildings",
        f"  ({ov['zero_in_cells_with_ge1_pos_n']:,}/{S['complete_zero']:,} exactly) sit in cells that",
        f"  also contain ≥1 complaint-positive building; **{ov['zero_in_cells_with_ge10_pos_pct']}%**",
        "  in cells with ≥10.",
        f"- Conversely {ov['pos_in_cells_with_ge1_zero_pct']}% of positive-mass buildings",
        f"  ({ov['pos_in_cells_with_ge1_zero_n']:,}/{S['complete_positive']:,} exactly) sit in",
        f"  cells with ≥1 zero-mass building ({ov['pos_in_cells_with_ge10_zero_pct']}% with ≥10).",
        f"- Cells occupied by both masses: {ov['cells_both']}; zero-only cells:",
        f"  {ov['cells_zero_only']} (holding {S['zero_only_cells_buildings']:,} building(s));",
        f"  positive-only cells: {ov['cells_pos_only']}.",
        "",
        "These are descriptive support facts for the spec's §identification; the",
        "distributional differences visible above (unit counts, borough mix, income",
        "and LEP gradients) are likewise stated as description. No conclusion about",
        "extrapolation feasibility is drawn here — that belongs to the spec phase.",
        "",
        f"Figure: `outputs/figures/phase0_p4_zeromass.svg` (vector; no raster on disk).",
        "Full machine-readable stats: `data/p4_stats.json`.",
    ]
    CKPT.parent.mkdir(parents=True, exist_ok=True)
    CKPT.write_text("\n".join(lines) + "\n")
    STATS.write_text(json.dumps(S, indent=2, default=str))
    used = _guard_storage()
    print(f"[p4] universe={S['universe_buildings']:,}  zero={S['zero_buildings']:,} "
          f"({S['zero_share_pct']}%)  overlap(zero in >=1-pos cells)="
          f"{ov['zero_in_cells_with_ge1_pos_pct']}%")
    print(f"[p4] storage data/raw = {used/1e6:.1f} MB")
    print(f"[p4] wrote {CKPT}, {STATS}, {FIG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
