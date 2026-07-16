"""S2 — feature engineering (A-FEAT, spec §1/§2/§3/§7 + Amendments 1-2). TWO frames:

(a) B3-scoring frame  -> data/processed/features_b3.parquet
    WFF's 30-feature recipe re-implemented FAITHFULLY from the read-only WFF repo
    (<WFF>/src/s2_features.py; line ranges cited inline below). Fidelity over
    improvement: B3 (imports/primary_lgbm.txt, frozen) is meaningless without its
    exact input format. Categorical dtypes are fixed to the frozen model's
    pandas_categorical footer lists so scoring alignment is structural.

(b) main frame        -> data/processed/features_main.parquet
    families 1-5 (WFF semantics, identical 30 columns) + family 6
    (complaint-granularity from the 311 union deliverable, complaint-level,
    floor 2019-06-01) + family 7 (ygpa-z7cr distinct-apartments per spec
    Amendment 1). Families 6-7 are availability-MASKED: NULL when the lookback
    window is not fully covered by the 2019-06-01 complaint floor — never
    zero-filled (spec §2).

BRIGHT LINE (spec §1 Oct-1 rule; CLAUDE.md Rule 4; audited by R-AUDIT S2 protocol):
every feature for target season `sy` uses ONLY data timestamped strictly BEFORE
Oct 1 `sy`. Season-indexed reads use seasons < sy; calendar-year reads use
yr <= sy-1 with wide matrices whose columns are capped at 2024, so a target-year
read is impossible, not merely avoided. Families 6-7 slice timestamps ONLY through
`win()`, which hard-asserts window_hi <= cutoff. Season 2026-27 (Rule 3): the spine
ends at season 2025; both frames assert max(season) == 2025.

Amendment-1 boundary: ygpa-z7cr feeds family 7 FEATURES only — nothing here
touches the loss; the union deliverable is the sole 311 complaint source for
families 3 and 6.

Labels: joined verbatim from the frozen R4 spine (imports/, read-only). Never
modified, never read by any feature computation for its own season.

Idempotent; reads ONLY local parquet caches (no network); deterministic (seed 42
set for the record — no sampling occurs). Rerun is byte-identical (sha256 printed).
Run: .venv/bin/python src/s2_features.py
Outputs: data/processed/features_b3.parquet, data/processed/features_main.parquet
Stats:   outputs/checkpoints/s2_stats.json
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "data" / "raw"
IMP = REPO / "imports"
PROC = REPO / "data" / "processed"
CKPT = REPO / "outputs" / "checkpoints"

SY = list(range(2017, 2026))          # spine seasons 2017-18 .. 2025-26 (start years)
PANEL_START = 2017                    # WFF s2_features.py L39
CTX_YR_MIN = 2014                     # WFF s2_features.py L40 (context pull floor 2014-06-01)
C311_YR_MIN = 2020                    # WFF s2_features.py L41 (family-3 year floor; B3 fidelity)
C_FLOOR = pd.Timestamp("2019-06-01")  # complaint-level floor (spec §2; families 6-7 masks)

# Frozen B3 categorical vocabularies — verbatim from imports/primary_lgbm.txt
# `pandas_categorical` footer (features 26 bldgclass_1, 27 borough).
B3_BLDGCLASS_CATS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "M",
                     "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "Y", "Z"]
B3_BOROUGH_CATS = ["BK", "BX", "MN", "QN", "SI"]

B3_COLS = [  # exact order = frozen model `feature_names` header line
    "viol_lag1", "viol_lag2", "viol_lag3", "hist_horizon", "viol_recency",
    "viol_chronicity", "viol_cnt_prior1", "viol_cnt_prior_cum",
    "ctx_a_prior1", "ctx_a_cum", "ctx_b_prior1", "ctx_b_cum",
    "ctx_c_prior1", "ctx_c_cum", "ctx_i_prior1", "ctx_i_cum",
    "ctx_total_prior1", "ctx_total_cum",
    "c311_available", "c311_prior1", "c311_prior_cum",
    "building_age", "prewar", "unitsres", "unitstotal", "numfloors",
    "bldgclass_1", "borough", "portfolio_size", "portfolio_loo_rate",
]


def season_of(dt):
    """NYC heat season (Oct 1 - May 31). Start-year int, or None off-season.
    Copied VERBATIM from WFF src/s2_features.py L46-57 (same as the label build)."""
    if dt is None or pd.isna(dt):
        return None
    m = dt.month
    if m >= 10:
        return dt.year
    if m <= 5:
        return dt.year - 1
    return None


def norm_txt(s: pd.Series) -> pd.Series:
    """WFF s2_features.py L59-62 verbatim."""
    return (s.astype("string").fillna("").str.upper().str.strip()
            .str.replace(r"\s+", " ", regex=True))


def to_int_bbl(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype("Int64")


def win(df: pd.DataFrame, col: str, lo: pd.Timestamp, hi: pd.Timestamp,
        cutoff: pd.Timestamp) -> pd.DataFrame:
    """The ONLY timestamp slicer for families 6-7. Half-open [lo, hi).
    Structural leakage guard: a window ending after the season cutoff is an
    assertion failure, not a data bug to find later."""
    assert hi <= cutoff, f"LEAKAGE GUARD: window hi {hi} > cutoff {cutoff}"
    assert lo < hi
    return df[(df[col] >= lo) & (df[col] < hi)]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    np.random.seed(42)  # no sampling occurs; set for the record (Rule 10)
    PROC.mkdir(parents=True, exist_ok=True)

    print("=== S2 feature build (silent-fail-forecast) ===")
    # ---------------- frozen spine (read-only import; WFF s2 L71-82) ----------------
    spine = pd.read_parquet(IMP / "building_season_labels.parquet")
    assert list(spine.columns) == ["bbl_n", "season", "label_c", "label_bc"]
    n_spine = len(spine)
    assert int(spine.season.max()) == 2025, "season 2026-27 contact — STOP (Rule 3)"
    print(f"spine: {n_spine:,} rows, seasons {spine.season.min()}-{spine.season.max()}, "
          f"{spine.bbl_n.nunique():,} buildings")

    bidx = pd.Index(np.sort(spine["bbl_n"].unique()), name="bbl_n")
    W = spine.pivot(index="bbl_n", columns="season", values="label_c").reindex(bidx)
    present = W.notna()
    W0 = W.fillna(0.0)

    # ---------- Family 1 source B: whitelisted violation rows (WFF s2 L84-94) ----------
    # cache name maps hpd_violations.parquet -> hpd_violations_wff.parquet (S1, same
    # 13-col contract, floor 2017-10-01). Class-C restriction EXPLICIT (Rule 6).
    viol = pd.read_parquet(RAW / "hpd_violations_wff.parquet")
    viol["inspectiondate"] = pd.to_datetime(viol["inspectiondate"], errors="coerce")
    viol["bbl_n"] = to_int_bbl(viol["bbl"])
    viol["vseason"] = viol["inspectiondate"].map(season_of)
    vc = viol[(viol["class"] == "C") & viol["bbl_n"].notna() & viol["vseason"].notna()]
    vc = vc[vc["vseason"].isin(SY)]
    vcnt = (vc.groupby(["bbl_n", "vseason"]).size().unstack(fill_value=0)
            .reindex(index=bidx, columns=SY, fill_value=0).astype("float64"))
    n_vc_rows = int(len(vc))

    # ---------- Family 2 source: HPD context by (bbl, class, year) (WFF s2 L96-106) ----------
    ctx = pd.read_parquet(RAW / "hpd_viol_context_by_year.parquet")
    ctx["bbl_n"] = to_int_bbl(ctx["bbl"])
    ctx["yr"] = pd.to_numeric(ctx["yr"], errors="coerce")
    ctx["n"] = pd.to_numeric(ctx["n"], errors="coerce")
    assert ctx["yr"].notna().all() and ctx["n"].notna().all(), "ctx coercion loss — STOP"
    ctx = ctx[ctx["bbl_n"].isin(bidx) & ctx["class"].isin(["A", "B", "C", "I"]) & ctx["yr"].notna()]
    ctx_yrs = list(range(CTX_YR_MIN, max(SY)))   # 2014..2024 — yr == sy never in the matrix
    CTXM = {}
    for cl in ["A", "B", "C", "I"]:
        m = (ctx[ctx["class"] == cl].groupby(["bbl_n", "yr"])["n"].sum().unstack()
             .reindex(index=bidx, columns=ctx_yrs).fillna(0.0).astype("float64"))
        CTXM[cl] = m
    n_ctx_rows = int(len(ctx))

    # ---------- Family 3 + 6 source: the 311 union deliverable (complaint level) ----------
    # WFF read a server-side aggregate cache c311_heat_by_building_year.parquet
    # (WFF s1d_pull_311_by_building.py L47-51: count by (bbl, calendar year), same
    # whitelist, bbl non-null). We hold the complaint-level union deliverable
    # (S1-audited) and reproduce that aggregate in-memory. B3 semantics preserved
    # exactly: the P311 matrix columns are 2020..2024 (WFF s2 L108-115), so union
    # rows from 2019 (archive side) can never enter family 3.
    c311 = pd.read_parquet(RAW / "c311_heat_complaints.parquet",
                           columns=["created_date", "bbl"])
    c311["created"] = pd.to_datetime(c311["created_date"], errors="coerce")
    c311["bbl_n"] = to_int_bbl(c311["bbl"])
    assert c311["created"].notna().all(), "311 union created_date coercion loss — STOP"
    n_union_rows = int(len(c311))
    c311 = c311[c311["bbl_n"].isin(bidx)][["bbl_n", "created"]]
    n_union_spine_rows = int(len(c311))
    c311 = c311.sort_values(["bbl_n", "created"], kind="mergesort").reset_index(drop=True)
    c311["yr"] = c311["created"].dt.year
    c311_yrs = list(range(C311_YR_MIN, max(SY)))  # 2020..2024
    P311 = (c311.groupby(["bbl_n", "yr"]).size().unstack()
            .reindex(index=bidx, columns=c311_yrs).fillna(0.0).astype("float64"))
    c311["cday"] = c311["created"].dt.normalize()

    # ---------- Family 4 source: PLUTO (WFF s2 L117-130; cache pluto_full.parquet) ----------
    pluto = pd.read_parquet(RAW / "pluto_full.parquet")
    pluto["bbl_n"] = to_int_bbl(pluto["bbl"])
    for col in ["yearbuilt", "numfloors", "unitsres", "unitstotal"]:
        pluto[col] = pd.to_numeric(pluto[col], errors="coerce")
    assert pluto["bbl_n"].is_unique, "PLUTO bbl duplicates — STOP and report"
    P = pluto.set_index("bbl_n").reindex(bidx)
    pluto_linked = int(bidx.isin(pluto["bbl_n"]).sum())
    bldgclass_1 = P["bldgclass"].astype("string").str.strip().str[:1]
    bldgclass_1 = bldgclass_1.where(bldgclass_1.fillna("") != "", other=pd.NA)
    borough = P["borough"].astype("string").str.strip()
    borough = borough.where(borough.fillna("") != "", other=pd.NA)
    yearbuilt = P["yearbuilt"].where(P["yearbuilt"] > 0)
    prewar = ((P["yearbuilt"] > 0) & (P["yearbuilt"] < 1940)).astype("int64")
    # B3 categorical-vocabulary conformance (frozen model footer): novel values
    # would silently misalign codes at scoring — assert none exist.
    bad_bc = int((~bldgclass_1.dropna().isin(B3_BLDGCLASS_CATS)).sum())
    bad_bo = int((~borough.dropna().isin(B3_BOROUGH_CATS)).sum())
    assert bad_bc == 0 and bad_bo == 0, f"novel categoricals vs frozen B3 vocab: {bad_bc}/{bad_bo} — STOP"

    # ---------- Family 5 source: registrations + contacts -> owner key (WFF s2 L132-172) ----------
    reg = pd.read_parquet(RAW / "hpd_registrations.parquet")
    reg["bbl_n"] = to_int_bbl(
        pd.to_numeric(reg["boroid"], errors="coerce").astype("Int64").astype(str)
        + pd.to_numeric(reg["block"], errors="coerce").astype("Int64").astype(str).str.zfill(5)
        + pd.to_numeric(reg["lot"], errors="coerce").astype("Int64").astype(str).str.zfill(4))
    reg["lastreg"] = pd.to_datetime(reg["lastregistrationdate"], errors="coerce")
    reg = reg[reg["bbl_n"].notna()]
    reg["_rid"] = pd.to_numeric(reg["registrationid"], errors="coerce")
    reg = (reg.sort_values(["bbl_n", "lastreg", "_rid"], ascending=[True, False, False])
           .drop_duplicates("bbl_n", keep="first"))

    con = pd.read_parquet(RAW / "hpd_registration_contacts.parquet")
    OWNER_TYPES = {"CorporateOwner": 0, "IndividualOwner": 1, "JointOwner": 2}
    con = con[con["type"].isin(OWNER_TYPES)].copy()
    hn, st, zp = (norm_txt(con["businesshousenumber"]), norm_txt(con["businessstreetname"]),
                  norm_txt(con["businesszip"]))
    corp = norm_txt(con["corporationname"])
    addr_key = ("ADDR:" + hn + "|" + st + "|" + zp).where(st != "", other=pd.NA)
    corp_key = ("CORP:" + corp).where(corp != "", other=pd.NA)
    con["owner_key"] = addr_key.fillna(corp_key)
    n_con_owner = int(len(con))
    n_con_keyless = int(con["owner_key"].isna().sum())
    con = con[con["owner_key"].notna()]
    con["_prio"] = con["type"].map(OWNER_TYPES)
    con["registrationid"] = pd.to_numeric(con["registrationid"], errors="coerce")
    reg["registrationid"] = pd.to_numeric(reg["registrationid"], errors="coerce")
    con = (con.sort_values(["registrationid", "_prio", "owner_key"])
           .drop_duplicates("registrationid", keep="first"))
    bo = reg[["bbl_n", "registrationid"]].merge(
        con[["registrationid", "owner_key"]], on="registrationid", how="left")
    owner_of = bo.set_index("bbl_n")["owner_key"].reindex(bidx)
    n_bbl_with_owner = int(owner_of.notna().sum())
    psize = owner_of.dropna().groupby(owner_of.dropna()).size()
    portfolio_size = owner_of.map(psize).astype("float64")

    sp = spine.merge(owner_of.rename("owner_key"), left_on="bbl_n", right_index=True, how="left")
    osg = sp[sp["owner_key"].notna()].groupby(["owner_key", "season"])["label_c"].agg(["size", "sum"])
    ON = osg["size"].unstack().reindex(columns=SY).fillna(0.0)
    OP = osg["sum"].unstack().reindex(columns=SY).fillna(0.0)

    # ---------- Family 7 source: ygpa-z7cr deliverable (spec Amendment 1) ----------
    hpdc = pd.read_parquet(RAW / "hpd_complaints_heat.parquet",
                           columns=["bbl", "received_date", "apartment", "unit_type",
                                    "problem_duplicate_flag"])
    hpdc["received"] = pd.to_datetime(hpdc["received_date"], errors="coerce")
    hpdc["bbl_n"] = to_int_bbl(hpdc["bbl"])
    assert hpdc["received"].notna().all(), "ygpa received_date coercion loss — STOP"
    n_hpdc_rows = int(len(hpdc))
    hpdc = hpdc[hpdc["bbl_n"].notna() & hpdc["bbl_n"].isin(bidx)]
    n_hpdc_spine_rows = int(len(hpdc))
    apt_key = norm_txt(hpdc["apartment"])
    # apartment-complaining row := HPD says APARTMENT unit AND a usable non-building
    # apartment string. 'BLDG' appears as an apartment value on building-wide problems.
    hpdc["is_apt"] = (norm_txt(hpdc["unit_type"]) == "APARTMENT") & (~apt_key.isin(["", "BLDG"]))
    hpdc["apt_key"] = apt_key
    flag = hpdc["problem_duplicate_flag"].astype("string").fillna("")
    assert set(flag.unique()) <= {"Y", "N"}, "unexpected problem_duplicate_flag value — STOP"
    hpdc["is_flag_n"] = (flag == "N")
    hpdc = hpdc[["bbl_n", "received", "apt_key", "is_apt", "is_flag_n"]].sort_values(
        ["bbl_n", "received"], kind="mergesort").reset_index(drop=True)
    n_hpdc_apt_rows = int(hpdc["is_apt"].sum())

    # ---------------- assemble per season (WFF s2 L174-261 pattern) ----------------
    out_parts = []
    last_pos = pd.Series(np.nan, index=bidx)
    cum_pos = pd.Series(0.0, index=bidx)
    cum_cnt = pd.Series(0.0, index=bidx)
    own_cum_n = pd.Series(0.0, index=ON.index)
    own_cum_p = pd.Series(0.0, index=ON.index)
    mask_cov = []

    for sy in SY:
        rows = spine.loc[spine["season"] == sy, ["bbl_n"]].copy()
        b = pd.Index(rows["bbl_n"].values)
        f = pd.DataFrame(index=b)
        f.index.name = "bbl_n"

        # --- family 1 (WFF s2 L189-203) ---
        for k in (1, 2, 3):
            s = sy - k
            f[f"viol_lag{k}"] = (W0[s].reindex(b).values if s in W0.columns else 0.0)
        f["hist_horizon"] = float(sy - PANEL_START)
        f["viol_recency"] = (sy - last_pos.reindex(b)).values
        cc = cum_cnt.reindex(b)
        f["viol_chronicity"] = (cum_pos.reindex(b) / cc.where(cc > 0)).values
        if sy > PANEL_START:
            f["viol_cnt_prior1"] = vcnt[sy - 1].reindex(b).values
            f["viol_cnt_prior_cum"] = vcnt[[s for s in SY if s < sy]].sum(axis=1).reindex(b).values
        else:
            f["viol_cnt_prior1"] = np.nan
            f["viol_cnt_prior_cum"] = np.nan

        # --- family 2 (WFF s2 L205-218): years <= sy-1 ONLY ---
        cum_yrs = [y for y in ctx_yrs if y <= sy - 1]
        tot1 = pd.Series(0.0, index=bidx)
        totc = pd.Series(0.0, index=bidx)
        for cl in ["A", "B", "C", "I"]:
            m = CTXM[cl]
            p1 = m[sy - 1]
            pc = m[cum_yrs].sum(axis=1)
            f[f"ctx_{cl.lower()}_prior1"] = p1.reindex(b).values
            f[f"ctx_{cl.lower()}_cum"] = pc.reindex(b).values
            tot1 += p1
            totc += pc
        f["ctx_total_prior1"] = tot1.reindex(b).values
        f["ctx_total_cum"] = totc.reindex(b).values

        # --- family 3 (WFF s2 L220-231): years <= sy-1, floor 2020, MASKED ---
        avail3 = int(sy - 1 >= C311_YR_MIN)
        f["c311_available"] = avail3
        if avail3:
            f["c311_prior1"] = P311[sy - 1].reindex(b).values
            f["c311_prior_cum"] = P311[[y for y in c311_yrs if y <= sy - 1]].sum(axis=1).reindex(b).values
        else:
            f["c311_prior1"] = np.nan
            f["c311_prior_cum"] = np.nan

        # --- family 4 (WFF s2 L233-239) ---
        f["building_age"] = (sy - yearbuilt.reindex(b)).values
        f["prewar"] = prewar.reindex(b).values
        f["unitsres"] = P["unitsres"].reindex(b).values
        f["unitstotal"] = P["unitstotal"].reindex(b).values
        f["numfloors"] = P["numfloors"].reindex(b).values
        f["bldgclass_1"] = bldgclass_1.reindex(b).values
        f["borough"] = borough.reindex(b).values

        # --- family 5 (WFF s2 L241-249): exact LOO, prior seasons only ---
        f["portfolio_size"] = portfolio_size.reindex(b).values
        ok = owner_of.reindex(b)
        loo_den = own_cum_n.reindex(ok.values).values - cum_cnt.reindex(b).values
        loo_num = own_cum_p.reindex(ok.values).values - cum_pos.reindex(b).values
        with np.errstate(invalid="ignore", divide="ignore"):
            rate = np.where(loo_den > 0, loo_num / loo_den, np.nan)
        rate[ok.isna().values] = np.nan
        f["portfolio_loo_rate"] = rate

        # --- families 6-7: complaint-level windows, strictly pre-cutoff, MASKED ---
        cutoff = pd.Timestamp(sy, 10, 1)
        ps_lo, ps_hi = pd.Timestamp(sy - 1, 10, 1), pd.Timestamp(sy, 6, 1)  # prior season
        t365_lo = cutoff - pd.Timedelta(days=365)
        t730_lo = cutoff - pd.Timedelta(days=730)
        av_ps = int(ps_lo >= C_FLOOR)
        av_365 = int(t365_lo >= C_FLOOR)
        av_730 = int(t730_lo >= C_FLOOR)

        # family 6 — union deliverable
        f["c6_available_ps"] = av_ps
        f["c6_available_t365"] = av_365
        f["c6_available_t730"] = av_730
        if av_ps:
            e = win(c311, "created", ps_lo, ps_hi, cutoff)
            evt = e.groupby("bbl_n").size().reindex(b).fillna(0.0)
            days = (e.drop_duplicates(["bbl_n", "cday"]).groupby("bbl_n").size()
                    .reindex(b).fillna(0.0))
            f["c6_evt_ps"] = evt.astype("float64").values
            f["c6_days_ps"] = days.astype("float64").values
            f["c6_dup_intensity_ps"] = (evt / days.where(days > 0)).values
        else:
            f["c6_evt_ps"] = np.nan
            f["c6_days_ps"] = np.nan
            f["c6_dup_intensity_ps"] = np.nan
        f["c6_evt_t365"] = (win(c311, "created", t365_lo, cutoff, cutoff)
                            .groupby("bbl_n").size().reindex(b).fillna(0.0)
                            .astype("float64").values if av_365 else np.nan)
        if av_730:
            e = win(c311, "created", t730_lo, cutoff, cutoff).copy()
            f["c6_evt_t730"] = (e.groupby("bbl_n").size().reindex(b).fillna(0.0)
                                .astype("float64").values)
            gap = e["created"].diff().dt.total_seconds() / 86400.0
            gap[e["bbl_n"].ne(e["bbl_n"].shift())] = np.nan   # cross-building diffs void
            e["gap"] = gap
            g = e.dropna(subset=["gap"]).groupby("bbl_n")["gap"]
            f["c6_gap_median_t730"] = g.median().reindex(b).values
            f["c6_gap_min_t730"] = g.min().reindex(b).values
            last = e.groupby("bbl_n")["created"].max().reindex(b)
            f["c6_days_since_last_t730"] = ((cutoff - last).dt.total_seconds() / 86400.0).values
        else:
            for c in ["c6_evt_t730", "c6_gap_median_t730", "c6_gap_min_t730",
                      "c6_days_since_last_t730"]:
                f[c] = np.nan

        # family 7 — ygpa-z7cr (features ONLY; Amendment-1 boundary)
        f["c7_available_ps"] = av_ps
        f["c7_available_t730"] = av_730
        if av_ps:
            e = win(hpdc, "received", ps_lo, ps_hi, cutoff)
            ea = e[e["is_apt"]]
            apts = (ea.drop_duplicates(["bbl_n", "apt_key"]).groupby("bbl_n").size()
                    .reindex(b).fillna(0.0))
            evt_all = e.groupby("bbl_n").size().reindex(b).fillna(0.0)
            evt_n = e[e["is_flag_n"]].groupby("bbl_n").size().reindex(b).fillna(0.0)
            f["c7_apts_ps"] = apts.astype("float64").values
            ut = P["unitstotal"].reindex(b)
            f["c7_apt_share_ps"] = (apts.values / ut.where(ut > 0).values)
            f["c7_evt_all_ps"] = evt_all.astype("float64").values
            f["c7_evt_dedupN_ps"] = evt_n.astype("float64").values
            f["c7_dupflag_share_ps"] = (1.0 - evt_n / evt_all.where(evt_all > 0)).values
        else:
            for c in ["c7_apts_ps", "c7_apt_share_ps", "c7_evt_all_ps",
                      "c7_evt_dedupN_ps", "c7_dupflag_share_ps"]:
                f[c] = np.nan
        if av_730:
            ea = win(hpdc, "received", t730_lo, cutoff, cutoff)
            ea = ea[ea["is_apt"]]
            f["c7_apts_t730"] = (ea.drop_duplicates(["bbl_n", "apt_key"])
                                 .groupby("bbl_n").size().reindex(b).fillna(0.0)
                                 .astype("float64").values)
        else:
            f["c7_apts_t730"] = np.nan

        mask_cov.append(dict(season=sy, c311_available=avail3, avail_ps=av_ps,
                             avail_t365=av_365, avail_t730=av_730, rows=len(b)))

        f["season"] = sy
        out_parts.append(f.reset_index())

        # roll state AFTER emitting sy (WFF s2 L254-261) — sy becomes prior for sy+1
        pos_now = W0[sy]
        newly = (pos_now == 1)
        last_pos = last_pos.where(~newly, other=float(sy))
        cum_pos = cum_pos + pos_now
        cum_cnt = cum_cnt + present[sy].astype(float)
        own_cum_n = own_cum_n + ON[sy]
        own_cum_p = own_cum_p + OP[sy]
        print(f"  season {sy}-{(sy + 1) % 100:02d}: {len(b):,} rows "
              f"(masks ps/365/730 = {av_ps}/{av_365}/{av_730})")

    feats = pd.concat(out_parts, ignore_index=True)
    feats = feats.merge(spine[["bbl_n", "season", "label_c", "label_bc"]],
                        on=["bbl_n", "season"], how="left")
    assert len(feats) == n_spine, f"row mismatch: {len(feats)} vs spine {n_spine}"
    assert feats["label_c"].notna().all() and feats["label_bc"].notna().all(), "label join failed — STOP"
    assert feats.duplicated(["bbl_n", "season"]).sum() == 0, "duplicate (bbl,season) keys — STOP"
    assert int(feats["season"].max()) == 2025 and set(feats["season"].unique()) <= set(SY), \
        "out-of-scope season in frame — STOP (Rule 3)"

    # fixed categorical vocabularies (frozen B3 footer) in BOTH frames
    feats["bldgclass_1"] = pd.Categorical(feats["bldgclass_1"], categories=B3_BLDGCLASS_CATS)
    feats["borough"] = pd.Categorical(feats["borough"], categories=B3_BOROUGH_CATS)

    fam67_cols = [c for c in feats.columns if c.startswith(("c6_", "c7_"))]
    main_cols = B3_COLS + fam67_cols
    feats = feats.sort_values(["season", "bbl_n"]).reset_index(drop=True)

    b3 = feats[["bbl_n", "season"] + B3_COLS + ["label_c"]]
    main = feats[["bbl_n", "season"] + main_cols + ["label_c", "label_bc"]]

    p_b3 = PROC / "features_b3.parquet"
    p_main = PROC / "features_main.parquet"
    b3.to_parquet(p_b3, index=False)
    main.to_parquet(p_main, index=False)
    h_b3, h_main = sha256(p_b3), sha256(p_main)

    # ---------------- audits ----------------
    def null_audit(df, cols):
        return {c: dict(n=int(df[c].isna().sum()),
                        pct=round(100 * df[c].isna().mean(), 3)) for c in cols}

    dup_cov = main[main["c7_available_ps"] == 1]
    stats = dict(
        spine_rows=n_spine, n_buildings=int(len(bidx)),
        b3_frame=dict(rows=len(b3), n_features=len(B3_COLS), path=str(p_b3.relative_to(REPO)),
                      sha256=h_b3, mb=round(p_b3.stat().st_size / 1e6, 1),
                      feature_cols=B3_COLS),
        main_frame=dict(rows=len(main), n_features=len(main_cols),
                        path=str(p_main.relative_to(REPO)), sha256=h_main,
                        mb=round(p_main.stat().st_size / 1e6, 1),
                        family_counts={"1_viol_hist": 8, "2_hpd_context": 10,
                                       "3_311_masked": 3, "4_pluto": 7, "5_owner": 2,
                                       "6_complaint_gran": len([c for c in fam67_cols if c.startswith("c6_")]),
                                       "7_distinct_apts": len([c for c in fam67_cols if c.startswith("c7_")])},
                        feature_cols=main_cols),
        sources=dict(viol_rows_used=n_vc_rows, ctx_rows_used=n_ctx_rows,
                     union_rows=n_union_rows, union_rows_on_spine=n_union_spine_rows,
                     ygpa_rows=n_hpdc_rows, ygpa_rows_on_spine=n_hpdc_spine_rows,
                     ygpa_apartment_rows=n_hpdc_apt_rows,
                     pluto_linked_bbl=pluto_linked,
                     owner_contacts_ownertype_rows=n_con_owner,
                     owner_contacts_keyless=n_con_keyless,
                     bbl_with_owner_key=n_bbl_with_owner,
                     bbl_owner_coverage_pct=round(100 * n_bbl_with_owner / len(bidx), 2)),
        b3_categorical_vocab_novel=dict(bldgclass_1=bad_bc, borough=bad_bo),
        mask_coverage=mask_cov,
        dupflag_bothways=dict(
            covered_rows=int(len(dup_cov)),
            evt_all_sum=float(dup_cov["c7_evt_all_ps"].sum()),
            evt_dedupN_sum=float(dup_cov["c7_evt_dedupN_ps"].sum()),
            mean_dup_share_where_defined=round(float(dup_cov["c7_dupflag_share_ps"].mean()), 4)),
        null_audit_b3=null_audit(b3, B3_COLS),
        null_audit_main_fam67=null_audit(main, fam67_cols),
    )
    (CKPT / "s2_stats.json").write_text(json.dumps(stats, indent=2))

    print(f"\n[done] B3 frame   -> {p_b3} ({stats['b3_frame']['mb']} MB) sha256={h_b3[:16]}…")
    print(f"[done] main frame -> {p_main} ({stats['main_frame']['mb']} MB) sha256={h_main[:16]}…")
    print(f"[done] stats -> {CKPT / 's2_stats.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
