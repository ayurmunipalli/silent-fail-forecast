"""RP2 — R-PILOT single-shot evaluation on season 2025-26 (Amendment 5(ii))
under LEAD's HEIGHTENED SINGLE-SHOT PROTOCOL: the script is REHEARSED on a dev
season and pre-audited BEFORE the one D9 contact is spent.

*** RETROSPECTIVE AND NON-BLIND (Amendment 5(iii)) ***
No prospective standing; no weight at G3; the frozen G3 pre-registration
(§10 margins, frozen bundle, Amendment-4 freeze entry, 2026-27 bright line)
is untouched. The §11 observed-label caveat attaches to every number (D11).

TWO MODES (D9 gate — structural, not procedural):
  REHEARSAL (default):     eval season V = 2024 (a dev season). Season-2025
    rows are NEVER loaded: frame reads carry pyarrow row filters
    (season <= 2024), every timestamped raw read is truncated at the end of
    season V (2025-05-31 23:59:59), and a hard assertion rejects V == 2025
    without the flag. Outputs -> outputs/checkpoints/rp2_work/rehearsal_2024/,
    every artifact labeled REHEARSAL.
  --the-single-shot:       eval season V = 2025 (2025-26). The ONE Amendment-
    5(ii) contact. D9: the eval slice's seasons are asserted == {2025};
    predictions persisted; reported as-is. A sentinel file is written first;
    if it already exists the script REFUSES to recompute (contacted exactly
    once). Outputs -> outputs/checkpoints/rp2_work/single_shot_2025/.

SCORING SET (committed artifacts ONLY, sha256-asserted at load; the frozen
build-phase bundle s3b_primary_seed42.pt is NOT scored and NOT touched,
Amendment 5(i)):
  - rpilot_joint_seed42.pt  (RP1 E*=8 all-pilot-dev refit): F, p, and
    q = F * (1 - (1-p)^min(u, u*)) with u* and the design/scaler taken from
    the bundle itself; deployment/stratum/criterion-3 ranking = F (grid §1/§7).
  - rpilot_b4_propensity_lgbm.txt + rpilot_b4_risk_lgbm.txt: both loaded and
    hash-asserted; deployment ranking = the RISK model score (grid §1 —
    propensity/IPW is training-time machinery, not a scoring factor).
  - rpilot_b5_lgbm.txt: uncorrected twin score.
  - B3 = imports/primary_lgbm.txt AS-IS (343-tree assertion, D10).
  - B0/B1/B2 recomputed from their frozen definitions (verbatim-audited
    machinery imported from src/s3a_baselines.py) with train/lookback < V.

LABELS: the hash-pinned S2 frames' label_c for season V — the audited build of
the frozen whitelist with the class-C restriction explicit in the S2 label
code (Rule 6); no label re-derivation here.

METRICS on season V (Amendment 5(ii)):
  1. Observed-label AP + p@250 for every model (p@k via the seed-42 tie-key
     permutation over the eval universe; AP is tie-free).
  2. Zero-311-stratum p@250 vs B3 on the same stratum and season. Stratum
     (spec §6): zero 311-union events in [2019-06-01, Oct 1 V) per bbl.
     Joint uses the F ranking; B0-B5 their deployment scores.
  3. Criterion-3-STYLE statistic, frozen Amendment-2 / grid-§7 definition
     executed verbatim with season := V and models := pilot artifacts:
     - Event set E: HSP-lot whitelisted class-C violation events in season V
       passing the SILENT SCREEN = zero associated 311-union complaints at
       W=30 AND zero associated ygpa-z7cr heat complaints at W=30 — the P3
       association rule VERBATIM for both screens (same-bbl, timestamps in
       [inspectiondate-30, inspectiondate], BOTH bounds inclusive,
       calendar-date truncation, int64 bbl; src/p3_hsp.py decisions 1-5:
       class-C explicit, duplicate violationid dropped, HSP membership =
       official h4mf-f24e store, in-program from EARLIEST program_start_date,
       W=30 window-coverage eligibility against each store's actual coverage,
       off-season Jun-Sep excluded). Every waterfall exclusion counted.
     - Unit: distinct building (BBL), multi-event buildings enter once.
     - pct_s(b) = 1 - (rank_s(b) - 1)/(N - 1), rank 1 = highest score among
       all N season-V buildings scored (full universe, identical set for all
       models; ties get average rank).
     - Delta_b = pct_model(b) - pct_B3(b); T = median_b(Delta_b).
     - One-sided exact sign test of H0: median(Delta) <= 0 at alpha = 0.05
       (Delta_b == 0 buildings dropped, count reported); REALIZED N REPORTED.
     - Primary: the joint pilot model (pct_F). Mechanically identical runs
       for B4 and B5 are reported as disclosed secondaries.
     - Sensitivity line: the same statistic under the 311-only screen.
PERSISTENCE: predictions parquet at building-season grain (bbl, season,
label_c, every model's score, joint F/p/q, zero-311 stratum flag) + stats
json + machine table. All labeled RETROSPECTIVE AND NON-BLIND (D8/D11);
rehearsal outputs additionally labeled REHEARSAL.

REHEARSAL CAVEAT (stated wherever rehearsal numbers appear): the pilot
artifacts were trained/refit on ALL pilot dev seasons 2019-2024, so
rehearsal-2024 metrics are IN-SAMPLE for joint/B4/B5 (and B3's 2024 is a WFF
test season). Rehearsal validates MACHINERY, not performance; its numbers
carry no standing of any kind.

TWO-PROCESS DESIGN (RP1 OpenMP lesson, completed): torch and lightgbm each
bundle a libomp on this macOS setup, and WHICHEVER IS IMPORTED SECOND
SEGFAULTS ON ITS FIRST NATIVE CALL — proven in BOTH directions during Phase-A
rehearsal (torch-first: lightgbm Booster.__init__ SIGSEGV even with zero
torch compute; lightgbm-first: first heavy torch op SIGSEGV — controlled A/B,
2026-07-21). One process can therefore never EXECUTE both. Consequently:
  - The MAIN process imports lightgbm/sklearn machinery lazily and NEVER
    imports torch. It runs B0-B5, B3, metrics, stratum, HSP screen, report.
  - The JOINT model scores in a SUBPROCESS (--joint-subprocess) that imports
    torch FIRST and never touches lightgbm; it re-derives the identical eval
    universe (same filtered read, same sort), writes F/p/q + bbl to npz; the
    main process hard-asserts bbl alignment before use.
(The committed rp1_pilot.py carries the mirror-image latent issue for
from-scratch reruns — its GBM stages predate its torch-first fix; disclosed
to LEAD in the Phase-A report, not silently patched.)

No worker pool. No network. Seed 42. Idempotent: outputs skipped if present.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

KEYS = ("bbl_n", "season", "label_c", "label_bc")   # frame key columns (S3a)


def norm_bbl(series: pd.Series) -> pd.Series:
    """Identical to the audited s3a_baselines.norm_bbl (duplicated here so the
    torch subprocess never imports the lightgbm-importing s3a module)."""
    return pd.to_numeric(series, errors="coerce").astype("Int64")


def season_of(dt):
    """Identical to the audited s3a_baselines.season_of (same duplication
    rationale; NYC heat season Oct 1 - May 31, start-year label)."""
    if dt is None or pd.isna(dt):
        return None
    m = dt.month
    if m >= 10:
        return dt.year
    if m <= 5:
        return dt.year - 1
    return None

PILOT_LABEL = "RETROSPECTIVE AND NON-BLIND"

REPO = Path(__file__).resolve().parent.parent
PROC = REPO / "data" / "processed"
RAW = REPO / "data" / "raw"
MODELS = REPO / "outputs" / "models"
IMPORTS = REPO / "imports"
RP2 = REPO / "outputs" / "checkpoints" / "rp2_work"

SEED = 42
FORBIDDEN_FROM = 2026          # D4 bright line, unchanged
TRAIN_THREADS = 3
DAY_MOD = 100_000              # P3/P2 composite-key stride, verbatim
W = 30                         # frozen W=30
ALPHA = 0.05                   # frozen alpha
STRATUM_FLOOR = pd.Timestamp("2019-06-01")   # spec §6 / union coverage floor

# ---- sha256 pins (D1 discipline extended to every scored artifact) ----
SHA = {
    "features_main.parquet":
        "477d3079fae0a4a76ee5507739c6f790448caa258c11ea78776583f2e4734090",
    "features_b3.parquet":
        "09f8e94df5c51fa66778e17cc2d9bbba0eceb0aeef2453b411d7662ef324fa09",
    "rpilot_joint_seed42.pt":
        "93343fbda11d5efd9204b828075359d044f67d825eab89edb3555368cef757b0",
    "rpilot_b4_propensity_lgbm.txt":
        "c79ff723bed43ef5fe1c4ac8fdadc60274bf96d5183d445660bb449145508c07",
    "rpilot_b4_risk_lgbm.txt":
        "6c7f5171d68850f96239f7cde90cc39d9bf4d08f87e50b6302189a9240d9e67a",
    "rpilot_b5_lgbm.txt":
        "a93c9089f22dbc082cb5e1810a214a330a6c99bd8a071c23e0a6a14ba0c5b302",
    "primary_lgbm.txt":
        "cd95a00e692a3d406c1a3aff1cabd1c3a384be227f7accea0dd97db7bdd38c93",
}

MODE = None      # set in main(): "rehearsal" | "single_shot"
V = None         # eval season start year: 2024 | 2025
OUT = None       # output dir
TS_CAP = None    # rehearsal: hard timestamp cap = end of season V


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def assert_sha(path: Path, key: str):
    got = sha256_file(path)
    assert got == SHA[key], f"HASH DRIFT {key}: {got} (Rule 9 HARD STOP)"


def guard(seasons, where: str, allowed):
    """The standing hard-stop pattern (D4): >= 2026 or outside allowed -> stop.
    In rehearsal mode season 2025 is additionally globally illegal."""
    touched = set(int(s) for s in pd.unique(pd.Series(list(seasons)).dropna()))
    illegal = sorted(touched - set(int(a) for a in allowed))
    bright = sorted(s for s in touched if s >= FORBIDDEN_FROM)
    if MODE == "rehearsal" and 2025 in touched:
        raise AssertionError(f"SEASON-2025 CONTACT IN REHEARSAL at [{where}] — "
                             "HARD STOP (Phase A / D9).")
    if bright or illegal:
        raise AssertionError(
            f"TEST-SEASON CONTACT at [{where}]: 2026+ touched={bright}, "
            f"outside-allowed={illegal} — HARD STOP (spec §4, Rule 3).")
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "guards.jsonl", "a") as fh:
        fh.write(json.dumps({"where": where, "mode": MODE,
                             "touched": sorted(touched),
                             "allowed": sorted(set(int(a) for a in allowed))}) + "\n")


def cap_ts(dt: pd.Series, where: str) -> pd.Series:
    """Rehearsal-mode hard truncation of any timestamp column at end of season
    V; single-shot leaves data untouched but still asserts the D4 line for
    season labels derived later. Returns the (possibly filtered) mask."""
    if MODE == "rehearsal":
        m = dt <= TS_CAP
        return m
    return pd.Series(True, index=dt.index)


def to_days(s: pd.Series) -> np.ndarray:
    """P3 to_days semantics: calendar-date truncation to integer days."""
    dt = pd.to_datetime(s, errors="coerce")
    return dt.values.astype("datetime64[D]").astype("float64")


# ------------------------- frame loads (row-filtered) -------------------------

def load_frame(name: str, key: str) -> pd.DataFrame:
    """Hash-asserted frame load with pyarrow row filters: rehearsal reads ONLY
    seasons <= 2024 (season-2025 rows never materialize); single-shot reads
    seasons <= 2025."""
    path = PROC / name
    assert_sha(path, key)
    max_season = 2024 if MODE == "rehearsal" else 2025
    f = pd.read_parquet(path, filters=[("season", "<=", max_season)])
    assert int(f["season"].max()) <= max_season
    guard(f["season"], f"rp2 {name} load (filtered <= {max_season})",
          allowed=range(2017, max_season + 1))
    return f


def eval_universe():
    """Season-V rows of both frames, aligned; tie-key; labels. Cached."""
    fm = load_frame("features_main.parquet", "features_main.parquet")
    ev = fm[fm["season"] == V].copy()
    del fm
    seasons_in_eval = set(int(s) for s in ev["season"].unique())
    assert seasons_in_eval == {V}, \
        f"eval slice seasons {seasons_in_eval} != {{{V}}} (D9)"
    if MODE == "single_shot":
        assert seasons_in_eval == {2025}, "D9: single-shot eval must be {2025}"
    guard(ev["season"], "rp2 eval universe", [V])
    ev = ev.sort_values(["season", "bbl_n"], kind="mergesort").reset_index(drop=True)
    rng = np.random.default_rng(SEED)
    ev["_tiekey"] = rng.permutation(len(ev))

    fb = load_frame("features_b3.parquet", "features_b3.parquet")
    evb = fb[fb["season"] == V].copy()
    del fb
    evb = evb.sort_values(["season", "bbl_n"], kind="mergesort").reset_index(drop=True)
    assert (evb["bbl_n"].to_numpy() == ev["bbl_n"].to_numpy()).all()
    assert (evb["season"].to_numpy() == ev["season"].to_numpy()).all()
    return ev, evb


# ------------------------- scores -------------------------

def score_joint(ev: pd.DataFrame) -> dict:
    """MAIN-process side: run the torch scoring in a fresh subprocess (see the
    two-process design note), then hard-assert bbl alignment with our own
    eval universe before accepting the scores."""
    npz_path = OUT / "joint_scores.npz"
    meta_path = OUT / "joint_scores_meta.json"
    if not (npz_path.exists() and meta_path.exists()):
        cmd = [sys.executable, __file__, "--joint-subprocess"]
        if MODE == "single_shot":
            cmd.append("--the-single-shot")
        r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
        if r.returncode != 0 or not npz_path.exists():
            print(r.stdout)
            print(r.stderr)
            raise AssertionError(
                f"joint scoring subprocess failed rc={r.returncode} (Rule 9)")
    z = np.load(npz_path)
    meta = json.loads(meta_path.read_text())
    assert (z["bbl"] == ev["bbl_n"].astype("int64").to_numpy()).all(), \
        "joint subprocess bbl alignment mismatch (Rule 9)"
    assert int(z["season"][0]) == V and len(set(z["season"].tolist())) == 1
    return {"F": z["F"], "p": z["p"], "q": z["q"], "ustar": meta["ustar"],
            "config_idx": meta["config_idx"], "torch_version": meta["torch"]}


def joint_subprocess_main() -> int:
    """SUBPROCESS: torch imported FIRST; lightgbm NEVER imported or executed
    here. Re-derives the identical eval universe (same hash-asserted filtered
    read, same sort), builds the RP1 design from the bundle's own
    design_cols/std_cols/scaler_all, scores F/p/q, persists npz + meta."""
    import torch
    torch.set_num_threads(TRAIN_THREADS)
    ev, _ = eval_universe()
    path = MODELS / "rpilot_joint_seed42.pt"
    assert_sha(path, "rpilot_joint_seed42.pt")
    bundle = torch.load(path, weights_only=False)
    cfg = bundle["config"]["config"]
    assert bundle["config"]["label"] == PILOT_LABEL
    design_cols, std_cols = bundle["design_cols"], bundle["std_cols"]
    scal = bundle["scaler_all"]
    n_std = len(std_cols)

    cols = []
    for name in design_cols:
        if name.endswith("__isna"):
            base = name[: -len("__isna")]
            cols.append(ev[base].isna().to_numpy(dtype=np.float32))
        elif "==" in name:
            base, lvl = name.split("==", 1)
            cols.append((ev[base].astype(object) == lvl).to_numpy(dtype=np.float32))
        else:
            cols.append(ev[name].astype(float).to_numpy(dtype=np.float32))
    X = np.stack(cols, axis=1)
    X[:, :n_std] = (X[:, :n_std] - np.asarray(scal["mean"], np.float32)) \
        / np.asarray(scal["std"], np.float32)
    X[~np.isfinite(X)] = 0.0

    # rebuild the architecture from config (same shapes as RP1 build_model)
    import torch.nn as nn
    layers, din = [], X.shape[1]
    for _ in range(cfg["depth"]):
        layers += [nn.Linear(din, cfg["width"]), nn.LayerNorm(cfg["width"]),
                   nn.ReLU(), nn.Dropout(cfg["dropout"])]
        din = cfg["width"]

    class TwoHead(nn.Module):
        def __init__(self):
            super().__init__()
            self.encoder = nn.Sequential(*layers)
            self.head_F = nn.Linear(cfg["width"], 1)
            self.head_p = nn.Linear(cfg["width"], 1)

        def forward(self, x):
            h = self.encoder(x)
            return (torch.sigmoid(self.head_F(h)).squeeze(-1),
                    torch.sigmoid(self.head_p(h)).squeeze(-1))

    model = TwoHead()
    model.load_state_dict(bundle["state_dict"])
    model.eval()
    Fs, ps = [], []
    xt = torch.from_numpy(X)
    with torch.no_grad():
        for i in range(0, len(X), 65536):
            F_, p_ = model(xt[i:i + 65536])
            Fs.append(F_.numpy().copy()); ps.append(p_.numpy().copy())
    F = np.concatenate(Fs); p = np.concatenate(ps)

    # u per A2, capped at the bundle's u* (25); q = F * R
    ut = ev["unitstotal"].astype(float).to_numpy()
    ur = ev["unitsres"].astype(float).to_numpy()
    u_raw = np.where(np.isfinite(ut) & (ut >= 1), ut,
                     np.where(np.isfinite(ur) & (ur >= 1), ur, 3.0))
    u = np.minimum(u_raw, float(cfg["ustar"]))
    q = F * (1 - (1 - np.clip(p, 1e-7, 1 - 1e-7)) ** u)
    np.savez_compressed(OUT / "joint_scores.npz",
                        bbl=ev["bbl_n"].astype("int64").to_numpy(),
                        season=ev["season"].astype("int16").to_numpy(),
                        F=F, p=p, q=q)
    (OUT / "joint_scores_meta.json").write_text(json.dumps(
        {"label": PILOT_LABEL, "mode": MODE, "eval_season": V,
         "ustar": cfg["ustar"], "config_idx": bundle["config"]["config_idx"],
         "torch": torch.__version__}))
    print(f"  joint subprocess: scored {len(F):,} rows (F mean {F.mean():.6f})")
    return 0


def score_gbms(ev: pd.DataFrame, evb: pd.DataFrame) -> dict:
    import lightgbm as lgb  # main process only; torch never imported here
    from s3a_baselines import feature_cols  # audited (imports lightgbm too)
    feats = feature_cols(ev)
    out = {}
    assert_sha(MODELS / "rpilot_b4_propensity_lgbm.txt", "rpilot_b4_propensity_lgbm.txt")
    prop = lgb.Booster(model_file=str(MODELS / "rpilot_b4_propensity_lgbm.txt"))
    assert prop.num_trees() == 90, f"B4 propensity trees {prop.num_trees()} != 90"
    assert_sha(MODELS / "rpilot_b4_risk_lgbm.txt", "rpilot_b4_risk_lgbm.txt")
    b4 = lgb.Booster(model_file=str(MODELS / "rpilot_b4_risk_lgbm.txt"))
    assert b4.num_trees() == 332, f"B4 risk trees {b4.num_trees()} != 332"
    out["B4"] = b4.predict(ev[feats])
    assert_sha(MODELS / "rpilot_b5_lgbm.txt", "rpilot_b5_lgbm.txt")
    b5 = lgb.Booster(model_file=str(MODELS / "rpilot_b5_lgbm.txt"))
    assert b5.num_trees() == 307, f"B5 trees {b5.num_trees()} != 307"
    out["B5"] = b5.predict(ev[feats])
    assert_sha(IMPORTS / "primary_lgbm.txt", "primary_lgbm.txt")
    b3 = lgb.Booster(model_file=str(IMPORTS / "primary_lgbm.txt"))
    assert b3.num_trees() == 343, f"B3 tree-count assertion FAILED: {b3.num_trees()} (D10)"
    out["B3"] = b3.predict(evb[b3.feature_name()])
    return out


def score_b012(ev: pd.DataFrame) -> dict:
    """B0/B1/B2 from their frozen definitions, train/lookback < V."""
    from s3a_baselines import fit_predict_b1  # audited; main process only
    out = {}
    b0_cnt = ev["viol_cnt_prior1"].astype(float).fillna(0.0).to_numpy()
    out["B0"] = ev["viol_lag1"].astype(float).to_numpy() * 1e6 + b0_cnt

    fm = load_frame("features_main.parquet", "features_main.parquet")
    train = fm[(fm["season"] >= 2019) & (fm["season"] < V)]
    guard(train["season"], "rp2 B1 train", range(2019, V))
    proba, prov = fit_predict_b1(train, ev)
    out["B1"] = proba
    out["b1_provenance"] = prov
    del fm, train

    vw = pd.read_parquet(RAW / "hpd_violations_wff.parquet",
                         columns=["bbl", "class", "inspectiondate"])
    vw = vw[vw["class"] == "C"].copy()          # class-C explicit (Rule 6)
    vw["inspectiondate"] = pd.to_datetime(vw["inspectiondate"], errors="coerce")
    vw = vw[cap_ts(vw["inspectiondate"], "B2 raw")]
    vw["bbl_n"] = norm_bbl(vw["bbl"])
    vw["season"] = vw["inspectiondate"].map(season_of)
    vw = vw[vw["season"].notna() & vw["bbl_n"].notna()].copy()
    vw["season"] = vw["season"].astype(int)
    vw = vw[vw["season"] <= V - 1]              # lookback cap V-1
    guard(vw["season"], "rp2 B2 raw class-C counts", range(2017, V))
    look = vw[vw["season"].isin([V - 1, V - 2, V - 3])]
    agg = look.groupby("bbl_n").size()
    out["B2"] = ev["bbl_n"].map(agg).fillna(0.0).to_numpy()
    return out


# ------------------------- stratum -------------------------

def zero311_stratum(ev: pd.DataFrame) -> np.ndarray:
    """Spec §6: zero 311-union events in [2019-06-01, Oct 1 V) per bbl.
    Only pre-cutoff rows are read (created < Oct 1 V), so the stratum build
    itself touches no season-V-or-later complaint rows."""
    cutoff = pd.Timestamp(V, 10, 1)
    assert cutoff <= pd.Timestamp(V, 10, 1)
    c = pd.read_parquet(RAW / "c311_heat_complaints.parquet",
                        columns=["bbl", "created_date"])
    c["created_date"] = pd.to_datetime(c["created_date"], errors="coerce")
    c = c[c["created_date"].notna() & (c["created_date"] >= STRATUM_FLOOR)
          & (c["created_date"] < cutoff)]
    c["bbl_n"] = norm_bbl(c["bbl"])
    seen = set(c.loc[c["bbl_n"].notna(), "bbl_n"].astype("int64").tolist())
    return ~ev["bbl_n"].astype("int64").isin(seen).to_numpy()


# ------------------------- criterion-3-style statistic -------------------------

def hsp_events() -> dict:
    """The grid-§7 event set for season V with the P3 waterfall verbatim;
    silent screens at W=30 against BOTH stores. Returns per-building screen
    outcomes + the full waterfall accounting."""
    S = {}
    hsp = pd.read_parquet(RAW / "hsp_selected_buildings.parquet")
    assert len(hsp) == 200, f"HSP store rows {len(hsp)} != 200 (Rule 9)"
    hsp["bbl_int"] = pd.to_numeric(hsp["bbl"], errors="coerce").round().astype("Int64")
    assert hsp["bbl_int"].notna().all(), "HSP bbl unresolvable (Rule 9)"
    memb = (hsp.groupby(hsp["bbl_int"].astype("int64"))
            .agg(first_start=("program_start_date", "min")).reset_index()
            .rename(columns={"bbl_int": "bbl_n"}))
    S["hsp_distinct_bbls"] = int(len(memb))
    memb_bbl = memb["bbl_n"].to_numpy()
    start_day = pd.to_datetime(memb["first_start"]).values \
        .astype("datetime64[D]").astype("float64")

    # violation events (P3 source + waterfall verbatim)
    viol = pd.read_parquet(RAW / "hpd_violations_heat.parquet",
                           columns=["violationid", "bbl", "class", "inspectiondate"])
    S["viol_rows_in"] = int(len(viol))
    viol = viol[viol["class"] == "C"].copy()            # class-C explicit
    viol = viol.drop_duplicates(subset="violationid", keep="first")
    dtins = pd.to_datetime(viol["inspectiondate"], errors="coerce")
    viol = viol[cap_ts(dtins, "hsp viol")]
    v_bbl = norm_bbl(viol["bbl"])
    v_day = to_days(viol["inspectiondate"])
    keep = v_bbl.notna().to_numpy() & np.isfinite(v_day)
    v_bbl = v_bbl[keep].astype("int64").to_numpy()
    v_day = v_day[keep]

    in_hsp = np.isin(v_bbl, memb_bbl)
    h_bbl, h_day = v_bbl[in_hsp], v_day[in_hsp]
    S["viol_in_hsp_all_time"] = int(in_hsp.sum())

    # season V only (heat season labeling; off-season excluded by construction)
    ts = pd.to_datetime(h_day, unit="D")
    seas = np.where(ts.month >= 10, ts.year, np.where(ts.month <= 5, ts.year - 1, -1))
    m_season = seas == V
    S["viol_hsp_offseason_or_other_seasons"] = int((~m_season).sum())
    h_bbl, h_day = h_bbl[m_season], h_day[m_season]
    guard([V] if len(h_bbl) else [], "rp2 hsp events season slice", [V])
    S["viol_hsp_season_V"] = int(len(h_bbl))

    # in-program (earliest program_start_date)
    start_map = pd.Series(start_day, index=memb_bbl)
    in_prog = h_day >= start_map.reindex(h_bbl).to_numpy()
    S["excluded_before_program_start"] = int((~in_prog).sum())
    h_bbl, h_day = h_bbl[in_prog], h_day[in_prog]

    # W=30 screens against both stores (P3 association rule verbatim)
    def screen(store: str, bbl_col: str, date_col: str):
        c = pd.read_parquet(RAW / store, columns=[bbl_col, date_col])
        cdt = pd.to_datetime(c[date_col], errors="coerce")
        c = c[cap_ts(cdt, store)]
        cb = norm_bbl(c[bbl_col])
        cd = to_days(c[date_col])
        k = cb.notna().to_numpy() & np.isfinite(cd)
        cb = cb[k].astype("int64").to_numpy()
        cd = cd[k]
        cov = (float(cd.min()), float(cd.max()))
        ckey = np.sort(cb * DAY_MOD + cd.astype("int64"))
        lo = np.searchsorted(ckey, h_bbl * DAY_MOD + (h_day - W).astype("int64"), "left")
        hi = np.searchsorted(ckey, h_bbl * DAY_MOD + h_day.astype("int64"), "right")
        eligible = ((h_day - W) >= cov[0]) & (h_day <= cov[1])
        return (hi - lo) == 0, eligible, cov

    z311, elig311, cov311 = screen("c311_heat_complaints.parquet", "bbl", "created_date")
    zygpa, eligyg, covyg = screen("hpd_complaints_heat.parquet", "bbl", "received_date")
    eligible = elig311 & eligyg
    S["excluded_window_coverage"] = int((~eligible).sum())
    S["coverage_311_days"] = [str(np.datetime64(int(cov311[0]), "D")),
                              str(np.datetime64(int(cov311[1]), "D"))]
    S["coverage_ygpa_days"] = [str(np.datetime64(int(covyg[0]), "D")),
                               str(np.datetime64(int(covyg[1]), "D"))]
    h_bbl = h_bbl[eligible]
    z311, zygpa = z311[eligible], zygpa[eligible]
    S["eligible_events"] = int(len(h_bbl))
    S["silent_events_dual_screen"] = int((z311 & zygpa).sum())
    S["silent_events_311_only"] = int(z311.sum())
    S["silent_buildings_dual"] = sorted(int(b) for b in np.unique(h_bbl[z311 & zygpa]))
    S["silent_buildings_311only"] = sorted(int(b) for b in np.unique(h_bbl[z311]))
    return S


def rank_pct(score: np.ndarray) -> np.ndarray:
    """pct_s = 1 - (rank-1)/(N-1); rank 1 = highest; ties average (grid §7)."""
    r = pd.Series(score).rank(method="average", ascending=False).to_numpy()
    return 1.0 - (r - 1.0) / (len(score) - 1.0)


def sign_test(delta: np.ndarray) -> dict:
    """One-sided exact sign test of H0: median(delta) <= 0 (grid §7)."""
    from scipy.stats import binomtest
    nz = delta[delta != 0]
    n_pos = int((nz > 0).sum())
    n = int(len(nz))
    res = {"realized_n_buildings": int(len(delta)), "n_dropped_zero": int(len(delta) - n),
           "n_signtest": n, "n_positive": n_pos, "T_median_delta": float(np.median(delta))
           if len(delta) else None}
    if n > 0:
        p = binomtest(n_pos, n, 0.5, alternative="greater").pvalue
        res["signtest_p_one_sided"] = float(p)
        res["reject_H0_at_alpha_0.05"] = bool(p < ALPHA)
    else:
        res["signtest_p_one_sided"] = None
        res["reject_H0_at_alpha_0.05"] = None
    return res


def criterion3_style(ev: pd.DataFrame, scores: dict, hspS: dict) -> dict:
    """Frozen statistic vs B3 for model in {joint(F), B4, B5}; dual screen
    primary + 311-only sensitivity."""
    out = {"waterfall": {k: v for k, v in hspS.items()
                         if not k.startswith("silent_buildings")}}
    bbl = ev["bbl_n"].astype("int64").to_numpy()
    pct = {name: rank_pct(scores[name]) for name in ("joint_F", "B3", "B4", "B5")}
    for screen_name, blds in (("dual_screen", hspS["silent_buildings_dual"]),
                              ("sensitivity_311_only", hspS["silent_buildings_311only"])):
        in_ev = np.isin(bbl, np.array(blds, dtype="int64"))
        idx = np.where(in_ev)[0]
        # one row per building (eval universe is single-season, bbl unique)
        found = {int(b) for b in bbl[idx]}
        missing = sorted(set(blds) - found)
        block = {"n_screen_buildings": len(blds),
                 "n_found_in_eval_universe": len(found),
                 "missing_from_universe": missing}
        for name in ("joint_F", "B4", "B5"):
            delta = pct[name][idx] - pct["B3"][idx]
            block[name] = sign_test(delta)
            block[name]["delta_full"] = [float(d) for d in delta]
        out[screen_name] = block
    return out


# ------------------------- main flow -------------------------

def main() -> int:
    global MODE, V, OUT, TS_CAP
    ap = argparse.ArgumentParser()
    ap.add_argument("--the-single-shot", action="store_true",
                    help="THE one Amendment-5(ii) contact with season 2025-26. "
                         "Default is rehearsal on season 2024.")
    ap.add_argument("--joint-subprocess", action="store_true",
                    help="internal: torch-only joint-scoring subprocess")
    args = ap.parse_args()
    MODE = "single_shot" if args.the_single_shot else "rehearsal"
    V = 2025 if MODE == "single_shot" else 2024
    assert (V == 2025) == (MODE == "single_shot"), \
        "season 2025 is impossible without --the-single-shot (D9)"
    TS_CAP = pd.Timestamp(V + 1, 5, 31, 23, 59, 59) if MODE == "rehearsal" else None
    OUT = RP2 / ("single_shot_2025" if MODE == "single_shot" else "rehearsal_2024")
    OUT.mkdir(parents=True, exist_ok=True)

    if args.joint_subprocess:
        return joint_subprocess_main()

    banner = (f"RP2 {MODE.upper()} — eval season {V}-{str(V+1)[-2:]} — "
              f"{PILOT_LABEL}" + (" — REHEARSAL (machinery validation only; "
              "joint/B4/B5 IN-SAMPLE on 2024)" if MODE == "rehearsal" else
              " — THE SINGLE SHOT (D9)"))
    print(f"=== {banner} ===")

    stats_path = OUT / ("rp2_stats.json" if MODE == "single_shot"
                        else "rehearsal_stats.json")
    sentinel = OUT / "SINGLE_SHOT_SPENT.sentinel"
    if MODE == "single_shot":
        if sentinel.exists():
            print("SINGLE SHOT ALREADY SPENT (sentinel present) — refusing to "
                  "recompute (D9: contacted exactly once). Existing outputs stand.")
            return 0
        sentinel.write_text(json.dumps({"label": PILOT_LABEL,
                                        "spent_at": pd.Timestamp.now().isoformat()}))
    elif stats_path.exists():
        print("rehearsal outputs already present — idempotent, nothing recomputed")
        return 0

    ev, evb = eval_universe()
    y = ev["label_c"].astype(int).to_numpy()
    tie = ev["_tiekey"].to_numpy()
    print(f"  eval universe: {len(ev):,} rows, positives {int(y.sum()):,}")

    joint = score_joint(ev)
    gbms = score_gbms(ev, evb)
    b012 = score_b012(ev)
    zero = zero311_stratum(ev)
    print(f"  scored 7 models; zero-311 stratum {int(zero.sum()):,} rows")

    scores = {"B0": b012["B0"], "B1": b012["B1"], "B2": b012["B2"],
              "B3": gbms["B3"], "B4": gbms["B4"], "B5": gbms["B5"],
              "joint_F": joint["F"], "joint_q": joint["q"]}

    from s3a_baselines import eval_with_strata  # audited; main process only
    metrics = {name: eval_with_strata(y, s, tie, zero)
               for name, s in scores.items()}

    hspS = hsp_events()
    crit3 = criterion3_style(ev, scores, hspS)

    # persist predictions (building-season grain)
    pred = pd.DataFrame({
        "bbl_n": ev["bbl_n"].astype("int64").to_numpy(), "season": V,
        "label_c": y, "zero311_stratum": zero,
        "score_B0": scores["B0"], "score_B1": scores["B1"],
        "score_B2": scores["B2"], "score_B3": scores["B3"],
        "score_B4": scores["B4"], "score_B5": scores["B5"],
        "joint_F": joint["F"], "joint_p": joint["p"], "joint_q": joint["q"],
    })
    pred["label"] = pd.Categorical.from_codes(
        np.zeros(len(pred), dtype="int8"),
        categories=[PILOT_LABEL + (" — REHEARSAL" if MODE == "rehearsal" else "")])
    pred_path = OUT / f"predictions_{V}.parquet"
    pred.to_parquet(pred_path, index=False)

    guards = [json.loads(l) for l in
              (OUT / "guards.jsonl").read_text().splitlines() if l.strip()]
    payload = {
        "label": PILOT_LABEL + (" — REHEARSAL" if MODE == "rehearsal" else ""),
        "mode": MODE, "eval_season": V,
        "rehearsal_caveat": None if MODE == "single_shot" else
            "Season 2024 is INSIDE the pilot training window (joint/B4/B5 refit "
            "on 2019-2024) — all pilot-model numbers are in-sample; machinery "
            "validation only, no standing.",
        "observed_label_caveat": "Every metric is computed against Y_obs; spec "
            "§11: observed-label evaluation penalizes the correction by "
            "construction (D11).",
        "artifact_hashes_asserted": SHA,
        "joint": {"config_idx": joint["config_idx"], "ustar": joint["ustar"]},
        "b1_provenance": b012["b1_provenance"],
        "metrics": metrics,
        "criterion3_style": crit3,
        "n_eval_rows": int(len(ev)), "n_positives": int(y.sum()),
        "zero311_stratum_rows": int(zero.sum()),
        "predictions": str(pred_path.relative_to(REPO)),
        "guard_facts": {"distinct_sites": sorted({g["where"] for g in guards}),
                        "max_season_ever_touched": max(max(g["touched"])
                                                       for g in guards if g["touched"]),
                        "n_2026plus_firings": 0},
        "library_versions": {"torch_subprocess": joint["torch_version"],
                             "lightgbm": __import__("lightgbm").__version__,
                             "numpy": np.__version__, "pandas": pd.__version__,
                             "python": sys.version.split()[0]},
    }
    stats_path.write_text(json.dumps(payload, indent=2))

    # machine table
    fmt = lambda x: ("n/a" if x is None else f"{x:.4f}")
    lines = [f"**{payload['label']}** — RP2 {MODE} table, season {V}-{str(V+1)[-2:]} "
             "(machine-generated).", ""]
    if MODE == "rehearsal":
        lines += ["**REHEARSAL — machinery validation only; joint/B4/B5 are "
                  "IN-SAMPLE on 2024 (trained through 2024); numbers carry no "
                  "standing.**", ""]
    lines += ["| Model | AP | p@250 | zero-311 p@250 | any-311 p@250 |",
              "|---|---|---|---|---|"]
    for name in ("B0", "B1", "B2", "B3", "B4", "B5", "joint_q", "joint_F"):
        m = metrics[name]
        lines.append(f"| {name} | {fmt(m['pr_auc'])} | {fmt(m['p@250'])} | "
                     f"{fmt(m['zero311']['p@250'])} | {fmt(m['any311']['p@250'])} |")
    lines += ["", f"Criterion-3-style (dual screen, W={W}): "]
    d = crit3["dual_screen"]
    for name in ("joint_F", "B4", "B5"):
        r = d[name]
        lines.append(f"- {name}: realized n={r['realized_n_buildings']}, "
                     f"T={fmt(r['T_median_delta'])}, sign-test p="
                     f"{fmt(r['signtest_p_one_sided'])}, "
                     f"reject@.05={r['reject_H0_at_alpha_0.05']} "
                     f"(zeros dropped {r['n_dropped_zero']})")
    lines.append(f"- sensitivity 311-only screen: n="
                 f"{crit3['sensitivity_311_only']['joint_F']['realized_n_buildings']}"
                 f", joint T="
                 f"{fmt(crit3['sensitivity_311_only']['joint_F']['T_median_delta'])}")
    (OUT / "rp2_table.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[-14:]))
    print(f"ALL RP2 {MODE.upper()} STAGES COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
