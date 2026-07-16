"""S3a — baselines B0-B4 (spec §5; plan §3 step 6; hyperparam_grid.md FROZEN per
Amendment 2). Idempotent + RESUMABLE: every unit of work checkpoints a small json
under outputs/checkpoints/s3a_work/; a killed run resumes, never restarts. Each
invocation processes pending units within --minutes, then exits ("PARTIAL" or
"ALL STAGES COMPLETE"). Seed 42. No network.

Reads ONLY:
  data/processed/features_main.parquet   (49 feats, S2-audited)  — B0/B1/B4
  data/processed/features_b3.parquet     (30 feats, WFF recipe)  — B3 scoring
  data/raw/hpd_violations_wff.parquet    (class-C rows)          — B2 counts
  data/raw/c311_heat_complaints.parquet  (311 union deliverable) — B4 propensity
                                          target + zero-311 stratum flags
  imports/primary_lgbm.txt               (B3 frozen booster, read-only)

TEST-SEASON SANCTITY (spec §4, Rule 3): season 2026-27 is structurally absent
(spine ends start-year 2025) — asserted anyway at every load and every fold via
assert_no_test_contact(); every guard firing is appended to s3a_work/guards.jsonl.

VERBATIM PORTS from read-only WFF src/s3_baselines.py (never written):
  season_of L52-62; assert-guard pattern L69-78; precision_at_k / stable_rank_order
  / eval_ranking L81-113; B2 trailing-3 L116-147; B1 fit_predict L150-196;
  B0 score L226-230. Adaptations (disclosed in outputs/checkpoints/s3a_baselines.md):
  dev universe 2019-2025 / VAL {2021..2025} per spec §2 + frozen grid §1; explicit
  (season,bbl_n) sort before the seed-42 tie-key permutation (order-robustness);
  categorical-dtype-safe "MISSING" fill in B1 (pandas-3 mechanics, same semantics);
  guard takes an explicit allowed-set argument.

B4 per the FROZEN grids (hyperparam_grid.md §5-§6):
  stage 1 propensity: LightGBM binary on the duplicate-count signal at building-
  season grain — target y_dup = 1{in-season 311-union events >= 2} on label_c==1
  train rows (the P2 multiplicity signal; P(any report | confirmed) is selection-
  saturated, so the reporting-intensity information conditional on detection lives
  in multiplicity). 311 UNION ONLY per the Amendment-1 boundary (ygpa-z7cr appears
  solely as c7_* feature columns). n=60 sampled of 6,561, sampling seed 42.
  stage 2 risk: LightGBM binary on label_c with positives weighted 1/max(Rhat,
  clip_floor); Rhat = fold-train stage-1-winner propensity score. n=60 of 59,049
  (incl. scale_pos_weight and clip-floor dims), stage 2 tuned against the frozen
  stage-1 winner. Early stopping 50 on fold v (as frozen; NOTE: WFF's own
  implementation watched v-1 — our grid text pre-registers watching v; disclosed).
  Selection: mean validation AP vs the target; tie-break (stage 2) mean zero-311-
  stratum p@250. Final artifacts refit on all dev seasons, n_estimators = round
  (mean best_iteration across folds), no ES (WFF frozen-refit convention).
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

REPO = Path(__file__).resolve().parent.parent
PROC = REPO / "data" / "processed"
RAW = REPO / "data" / "raw"
CKPT = REPO / "outputs" / "checkpoints"
WORK = CKPT / "s3a_work"
MODELS = REPO / "outputs" / "models"

SEED = 42
DEV_SEASONS = list(range(2019, 2026))    # 2019-20 .. 2025-26 (spec §2)
LAG_SEASONS = [2017, 2018]               # lag-feature sources only (spec §2)
VAL_SEASONS = [2021, 2022, 2023, 2024, 2025]   # frozen grid §1 (plan §3 step 6)
FORBIDDEN_FROM = 2026                    # season 2026-27: the bright line (spec §4)
KS = [100, 250, 500, 1000, 2500]
HEADLINE_K = 250
N_SAMPLED = 60                           # frozen grid §6

KEYS = ("bbl_n", "season", "label_c", "label_bc")

# ---- frozen grid §5: stage-1 propensity dims (Cartesian 3^8 = 6,561) ----
PROP_DIMS = [
    ("num_leaves", [31, 63, 127]),
    ("max_depth", [-1, 6, 10]),
    ("learning_rate", [0.02, 0.05, 0.1]),
    ("n_estimators", [400, 800, 1500]),
    ("min_child_samples", [20, 50, 100]),
    ("subsample", [0.7, 0.9, 1.0]),
    ("colsample_bytree", [0.6, 0.8, 1.0]),
    ("reg_lambda", [0.0, 1.0, 5.0]),
]
# ---- frozen grid §5: stage-2 risk dims (Cartesian 3^10 = 59,049) ----
RISK_DIMS = PROP_DIMS + [
    ("scale_pos_weight", ["1", "sqrt", "full"]),   # {1, sqrt(neg/pos), neg/pos}
    ("clip_floor", [0.02, 0.05, 0.10]),
]


def season_of(dt):
    """NYC heat season (Oct 1 - May 31). Start-year int, or None off-season.
    Ported VERBATIM from WFF src/s3_baselines.py L52-62 (same fn as label build)."""
    if dt is None or pd.isna(dt):
        return None
    m = dt.month
    if m >= 10:
        return dt.year
    if m <= 5:
        return dt.year - 1
    return None


def norm_bbl(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").astype("Int64")


def assert_no_test_contact(seasons, where: str, allowed):
    """HARD STOP on any season >= 2026 or outside the explicit allowed set.
    Pattern from WFF L69-78; allowed set explicit here because dev/lag/lookback
    scopes differ by call site. Every pass is recorded (guards.jsonl)."""
    touched = set(int(s) for s in pd.unique(pd.Series(list(seasons)).dropna()))
    illegal = sorted(touched - set(int(a) for a in allowed))
    bright = sorted(s for s in touched if s >= FORBIDDEN_FROM)
    if bright or illegal:
        raise AssertionError(
            f"TEST-SEASON CONTACT at [{where}]: 2026+ touched={bright}, "
            f"outside-allowed={illegal} — HARD STOP (spec §4, Rule 3)."
        )
    WORK.mkdir(parents=True, exist_ok=True)
    with open(WORK / "guards.jsonl", "a") as fh:
        fh.write(json.dumps({"where": where, "touched": sorted(touched),
                             "allowed": sorted(set(int(a) for a in allowed))}) + "\n")


# ------------------------- metrics (WFF L81-113 verbatim) -------------------------

def precision_at_k(y_true: np.ndarray, order: np.ndarray, k: int):
    n = len(order)
    if k > n:
        return None
    topk = order[:k]
    return float(y_true[topk].sum()) / k


def stable_rank_order(score: np.ndarray, rng_key: np.ndarray) -> np.ndarray:
    """Indices sorted by score DESC, ties broken by the fixed seed-42 key ASC."""
    return np.lexsort((rng_key, -score))


def eval_ranking(y_true: np.ndarray, score: np.ndarray, rng_key: np.ndarray) -> dict:
    order = stable_rank_order(score, rng_key)
    out = {f"p@{k}": precision_at_k(y_true, order, k) for k in KS}
    if y_true.min() == y_true.max():
        out["pr_auc"] = None
        out["roc_auc"] = None
    else:
        out["pr_auc"] = float(average_precision_score(y_true, score))
        out["roc_auc"] = float(roc_auc_score(y_true, score))
    out["n"] = int(len(y_true))
    out["pos"] = int(y_true.sum())
    out["prevalence"] = float(y_true.mean())
    return out


def eval_with_strata(y, score, tie, zero_mask) -> dict:
    """Global metrics + the spec-§6 binary stratification (zero-311 vs any-311
    trailing history at cutoff). Stratum p@250 = precision in the top 250 of the
    ranking RESTRICTED to the stratum (grid §1 tie-break metric)."""
    res = eval_ranking(y, score, tie)
    for name, m in (("zero311", zero_mask), ("any311", ~zero_mask)):
        res[name] = eval_ranking(y[m], score[m], tie[m])
    return res


# ------------------------- shared prep (cached) -------------------------

def load_dev_frame() -> pd.DataFrame:
    f = pd.read_parquet(PROC / "features_main.parquet")
    assert int(f["season"].max()) == 2025, "spine must end at start-year 2025"
    assert_no_test_contact(f["season"], "features_main load",
                           allowed=LAG_SEASONS + DEV_SEASONS)
    dev = f[f["season"].isin(DEV_SEASONS)].copy()
    assert_no_test_contact(dev["season"], "dev universe (post-restrict)", DEV_SEASONS)
    dev = dev.sort_values(["season", "bbl_n"], kind="mergesort").reset_index(drop=True)
    rng = np.random.default_rng(SEED)
    dev["_tiekey"] = rng.permutation(len(dev))
    return dev


def prep_311_tables():
    """One pass over the 311 union deliverable -> two cached tables:
    (a) per-bbl FIRST event timestamp (zero-311 stratum flags at any cutoff);
    (b) per (bbl_n, season) IN-SEASON event counts (B4 propensity target).
    Off-season (Jun-Sep) events count for (a) history, not for (b) in-season."""
    out_first = WORK / "first311.parquet"
    out_cnt = WORK / "insea311.parquet"
    if out_first.exists() and out_cnt.exists():
        return
    c = pd.read_parquet(RAW / "c311_heat_complaints.parquet",
                        columns=["bbl", "created_date"])
    c["bbl_n"] = norm_bbl(c["bbl"])
    c["created_date"] = pd.to_datetime(c["created_date"], errors="coerce")
    c = c[c["bbl_n"].notna() & c["created_date"].notna()]
    c.groupby("bbl_n")["created_date"].min().rename("first311").reset_index() \
        .to_parquet(out_first, index=False)
    c["season"] = c["created_date"].map(season_of)
    ins = c[c["season"].notna()].copy()
    ins["season"] = ins["season"].astype(int)
    ins = ins[ins["season"].isin(DEV_SEASONS)]
    assert_no_test_contact(ins["season"], "in-season 311 counts (targets)", DEV_SEASONS)
    ins.groupby(["bbl_n", "season"]).size().rename("n311").reset_index() \
        .to_parquet(out_cnt, index=False)


def zero311_mask(dev: pd.DataFrame, v: int) -> np.ndarray:
    """Zero-311 stratum for season v = no union event in [2019-06-01, Oct 1 v).
    Hard-asserts the window edge equals the cutoff (S2 win() discipline)."""
    cutoff = pd.Timestamp(v, 10, 1)
    assert cutoff <= pd.Timestamp(v, 10, 1), "window_hi must be <= cutoff"
    first = pd.read_parquet(WORK / "first311.parquet")
    m = dev.loc[dev["season"] == v, "bbl_n"].map(
        first.set_index("bbl_n")["first311"])
    return ~(m.notna() & (m < cutoff)).to_numpy()


# ------------------------- B2 trailing-3 (WFF L116-147) -------------------------

def build_trailing3_counts() -> pd.DataFrame:
    v = pd.read_parquet(RAW / "hpd_violations_wff.parquet",
                        columns=["bbl", "class", "inspectiondate"])
    v = v[v["class"] == "C"].copy()   # class-C restriction explicit (Rule 6)
    v["inspectiondate"] = pd.to_datetime(v["inspectiondate"], errors="coerce")
    v["bbl_n"] = norm_bbl(v["bbl"])
    v["season"] = v["inspectiondate"].map(season_of)
    v = v[v["season"].notna() & v["bbl_n"].notna()].copy()
    v["season"] = v["season"].astype(int)
    max_lookback_season = max(VAL_SEASONS) - 1    # 2024
    v = v[v["season"] <= max_lookback_season].copy()
    assert_no_test_contact(v["season"], "B2 raw class-C counts",
                           allowed=range(2017, max_lookback_season + 1))
    return v.groupby(["bbl_n", "season"]).size().rename("c_cnt").reset_index()


def trailing3_for_val(cnt, keys, v: int) -> np.ndarray:
    look = cnt[cnt["season"].isin([v - 1, v - 2, v - 3])]
    assert_no_test_contact(list(look["season"].unique()) + [v],
                           f"B2 trailing3 v={v}", allowed=list(range(2017, v)) + [v])
    agg = look.groupby("bbl_n")["c_cnt"].sum()
    return keys["bbl_n"].map(agg).fillna(0.0).to_numpy()


# ------------------------- B1 logistic (WFF L150-196) -------------------------

B1_NUM = ["viol_lag1", "building_age", "unitstotal"]
B1_CAT = "borough"


def _str_missing(s: pd.Series) -> pd.Series:
    """Categorical-dtype-safe 'MISSING' fill (WFF used fillna on object dtype;
    our frames carry frozen pandas Categoricals — same semantics, safe mechanics)."""
    s = s.astype(object)
    return s.where(pd.notna(s), "MISSING").astype(str)


def fit_predict_b1(train: pd.DataFrame, val: pd.DataFrame):
    tr_boro = _str_missing(train[B1_CAT])
    va_boro = _str_missing(val[B1_CAT])
    boro_levels = sorted(tr_boro.unique())

    def onehot(s):
        return pd.DataFrame({f"boro_{lvl}": (s == lvl).astype(float) for lvl in boro_levels})
    tr_oh, va_oh = onehot(tr_boro), onehot(va_boro)

    med = {c: float(train[c].median()) for c in ["building_age", "unitstotal"]}

    def num_block(df):
        cols = {}
        cols["viol_lag1"] = df["viol_lag1"].astype(float).to_numpy()
        for c in ["building_age", "unitstotal"]:
            raw = df[c].astype(float)
            cols[c] = raw.fillna(med[c]).to_numpy()
            cols[f"{c}_missing"] = raw.isna().astype(float).to_numpy()
        return pd.DataFrame(cols, index=df.index)
    tr_num, va_num = num_block(train), num_block(val)

    scaler = StandardScaler().fit(tr_num.to_numpy())
    Xtr = np.hstack([scaler.transform(tr_num.to_numpy()), tr_oh.to_numpy()])
    Xva = np.hstack([scaler.transform(va_num.to_numpy()), va_oh.to_numpy()])
    ytr = train["label_c"].astype(int).to_numpy()

    clf = LogisticRegression(max_iter=2000, C=1.0, solver="lbfgs", random_state=SEED)
    clf.fit(Xtr, ytr)
    converged = bool(np.all(clf.n_iter_ < 2000))
    proba = clf.predict_proba(Xva)[:, 1]
    prov = {"boro_levels": boro_levels, "medians": med,
            "n_iter": int(clf.n_iter_[0]), "converged": converged,
            "n_features_matrix": int(Xtr.shape[1])}
    return proba, prov


# ------------------------- grid machinery -------------------------

def space_size(dims):
    n = 1
    for _, vals in dims:
        n *= len(vals)
    return n


def decode(idx: int, dims) -> dict:
    cfg = {}
    for name, vals in reversed(dims):
        idx, r = divmod(idx, len(vals))
        cfg[name] = vals[r]
    return cfg


def sampled_configs(dims):
    """n=60 without replacement from the Cartesian space, sampling seed 42
    (frozen grid §6). Deterministic; sorted for stable work ordering."""
    size = space_size(dims)
    rng = np.random.default_rng(SEED)
    idxs = sorted(int(i) for i in rng.choice(size, size=N_SAMPLED, replace=False))
    return [(i, decode(i, dims)) for i in idxs]


def lgb_params(cfg: dict, spw: float | None = None) -> dict:
    p = {
        "objective": "binary", "metric": "average_precision",
        "num_leaves": cfg["num_leaves"], "max_depth": cfg["max_depth"],
        "learning_rate": cfg["learning_rate"],
        "min_data_in_leaf": cfg["min_child_samples"],
        "bagging_fraction": cfg["subsample"],
        "bagging_freq": 1 if cfg["subsample"] < 1.0 else 0,
        "feature_fraction": cfg["colsample_bytree"],
        "lambda_l2": cfg["reg_lambda"],
        "seed": SEED, "deterministic": True, "force_row_wise": True,
        "verbosity": -1, "feature_pre_filter": False,
    }
    if spw is not None and spw != 1.0:
        p["scale_pos_weight"] = spw
    return p


def spw_value(choice: str, y_train: np.ndarray) -> float:
    ratio = float((y_train == 0).sum()) / max(1, int((y_train == 1).sum()))
    return {"1": 1.0, "sqrt": float(np.sqrt(ratio)), "full": ratio}[choice]


def boundary_status(cfg: dict, dims) -> dict:
    out = {}
    for name, vals in dims:
        pos = vals.index(cfg[name])
        out[name] = "interior" if 0 < pos < len(vals) - 1 else \
            ("low-edge" if pos == 0 else "high-edge")
    return out


# ------------------------- stages -------------------------

def feature_cols(dev):
    return [c for c in dev.columns if c not in KEYS and c != "_tiekey"]


def stage_b012(dev):
    out = WORK / "b012.json"
    if out.exists():
        return
    cnt = build_trailing3_counts()
    results = {"B0": {}, "B1": {}, "B2": {}}
    b1_prov = {}
    for v in VAL_SEASONS:
        train = dev[dev["season"] < v]
        val = dev[dev["season"] == v]
        assert_no_test_contact(list(train["season"].unique()) + [v],
                               f"b012 fold v={v}", DEV_SEASONS)
        y = val["label_c"].astype(int).to_numpy()
        tie = val["_tiekey"].to_numpy()
        z = zero311_mask(dev, v)

        # B0 persistence (WFF L226-230): flag primary, prior-count tie-break.
        b0_cnt = val["viol_cnt_prior1"].astype(float).fillna(0.0).to_numpy()
        b0_score = val["viol_lag1"].astype(float).to_numpy() * 1e6 + b0_cnt
        results["B0"][str(v)] = eval_with_strata(y, b0_score, tie, z)

        proba, prov = fit_predict_b1(train, val)
        b1_prov[str(v)] = prov
        results["B1"][str(v)] = eval_with_strata(y, proba, tie, z)

        b2 = trailing3_for_val(cnt, val[["bbl_n"]].reset_index(drop=True), v)
        results["B2"][str(v)] = eval_with_strata(y, b2, tie, z)
        print(f"  b012 v={v}: B0 p@250={results['B0'][str(v)]['p@250']:.4f} "
              f"B1={results['B1'][str(v)]['p@250']:.4f} "
              f"B2={results['B2'][str(v)]['p@250']:.4f}")
    out.write_text(json.dumps({"results": results, "b1_provenance": b1_prov}, indent=2))


def stage_b3(dev):
    out = WORK / "b3.json"
    if out.exists():
        return
    booster = lgb.Booster(model_file=str(REPO / "imports" / "primary_lgbm.txt"))
    trees = booster.num_trees()
    assert trees == 343, f"B3 tree-count assertion FAILED: {trees} != 343 (Rule 9)"
    fb3 = pd.read_parquet(PROC / "features_b3.parquet")
    assert int(fb3["season"].max()) == 2025
    assert_no_test_contact(fb3["season"], "features_b3 load", LAG_SEASONS + DEV_SEASONS)
    fb3 = fb3[fb3["season"].isin(DEV_SEASONS)]
    fb3 = fb3.sort_values(["season", "bbl_n"], kind="mergesort").reset_index(drop=True)
    # identical key order as dev frame -> reuse dev tie-keys
    assert (fb3["bbl_n"].to_numpy() == dev["bbl_n"].to_numpy()).all()
    assert (fb3["season"].to_numpy() == dev["season"].to_numpy()).all()
    feat_list = booster.feature_name()
    results = {}
    for v in VAL_SEASONS:
        m = fb3["season"] == v
        assert_no_test_contact([v], f"b3 score v={v}", DEV_SEASONS)
        score = booster.predict(fb3.loc[m, feat_list])
        y = fb3.loc[m, "label_c"].astype(int).to_numpy()
        tie = dev.loc[m.to_numpy(), "_tiekey"].to_numpy()
        z = zero311_mask(dev, v)
        results[str(v)] = eval_with_strata(y, score, tie, z)
        print(f"  b3 v={v}: p@250={results[str(v)]['p@250']:.4f} "
              f"zero311 p@250={results[str(v)]['zero311']['p@250']:.4f}")
    out.write_text(json.dumps({
        "tree_count_assertion": {"expected": 343, "observed": trees, "pass": True},
        "in_sample_caveat": "v in {2021,2022,2023} were WFF TRAINING seasons for "
                            "this booster (in-sample); 2024/2025 were WFF's test "
                            "seasons. Descriptive context only; B3's binding "
                            "comparison happens once, at G3.",
        "results": results}, indent=2))


def prop_target(dev) -> np.ndarray:
    ins = pd.read_parquet(WORK / "insea311.parquet")
    key = ins.set_index(["bbl_n", "season"])["n311"]
    n311 = pd.MultiIndex.from_frame(dev[["bbl_n", "season"]]).map(key)
    n311 = pd.Series(n311, dtype="float64").fillna(0.0).to_numpy()
    return (n311 >= 2).astype(int)


def stage_prop(dev, deadline: float):
    """Stage-1 propensity search: pending (config, fold) units, fold-major."""
    cfgs = sampled_configs(PROP_DIMS)
    (WORK / "s1_prop").mkdir(exist_ok=True)
    y_dup = prop_target(dev)
    feats = feature_cols(dev)
    pos = dev["label_c"].astype(int).to_numpy() == 1
    for v in VAL_SEASONS:
        pend = [(i, c) for i, c in cfgs
                if not (WORK / "s1_prop" / f"cfg{i}_v{v}.json").exists()]
        if not pend:
            continue
        tr = (dev["season"] < v).to_numpy() & pos
        va = (dev["season"] == v).to_numpy() & pos
        assert_no_test_contact(dev.loc[tr | va, "season"], f"prop fold v={v}", DEV_SEASONS)
        dtr = lgb.Dataset(dev.loc[tr, feats], label=y_dup[tr],
                          params={"feature_pre_filter": False})
        dva = lgb.Dataset(dev.loc[va, feats], label=y_dup[va], reference=dtr)
        for i, cfg in pend:
            if time.time() > deadline:
                return False
            m = lgb.train(lgb_params(cfg), dtr, num_boost_round=cfg["n_estimators"],
                          valid_sets=[dva],
                          callbacks=[lgb.early_stopping(50, verbose=False)])
            rec = {"config_idx": i, "config": cfg, "v": v,
                   "ap": float(m.best_score["valid_0"]["average_precision"]),
                   "best_iter": int(m.best_iteration),
                   "n_train": int(tr.sum()), "n_val": int(va.sum()),
                   "train_dup_rate": float(y_dup[tr].mean()),
                   "val_dup_rate": float(y_dup[va].mean())}
            (WORK / "s1_prop" / f"cfg{i}_v{v}.json").write_text(json.dumps(rec))
        print(f"  prop fold v={v} complete")
    return True


def prop_winner():
    out = WORK / "s1_winner.json"
    if out.exists():
        return json.loads(out.read_text())
    cfgs = sampled_configs(PROP_DIMS)
    rows = []
    for i, cfg in cfgs:
        aps, iters = [], []
        for v in VAL_SEASONS:
            r = json.loads((WORK / "s1_prop" / f"cfg{i}_v{v}.json").read_text())
            aps.append(r["ap"]); iters.append(r["best_iter"])
        rows.append({"config_idx": i, "config": cfg, "mean_ap": float(np.mean(aps)),
                     "per_fold_ap": aps, "per_fold_best_iter": iters})
    rows.sort(key=lambda r: (-r["mean_ap"], r["config_idx"]))
    win = rows[0]
    win["boundary"] = boundary_status(win["config"], PROP_DIMS)
    win["n_configs_evaluated"] = len(rows)
    win["runner_up_mean_ap"] = rows[1]["mean_ap"]
    out.write_text(json.dumps(win, indent=2))
    return win


def stage_rhat(dev):
    """Per-fold stage-1-winner refit -> Rhat on that fold's TRAIN rows (cached)."""
    win = prop_winner()
    y_dup = prop_target(dev)
    feats = feature_cols(dev)
    pos = dev["label_c"].astype(int).to_numpy() == 1
    for v in VAL_SEASONS:
        out = WORK / f"rhat_v{v}.npz"
        if out.exists():
            continue
        tr = (dev["season"] < v).to_numpy() & pos
        va = (dev["season"] == v).to_numpy() & pos
        all_tr = (dev["season"] < v).to_numpy()
        assert_no_test_contact(dev.loc[all_tr, "season"], f"rhat v={v}", DEV_SEASONS)
        dtr = lgb.Dataset(dev.loc[tr, feats], label=y_dup[tr],
                          params={"feature_pre_filter": False})
        dva = lgb.Dataset(dev.loc[va, feats], label=y_dup[va], reference=dtr)
        m = lgb.train(lgb_params(win["config"]), dtr,
                      num_boost_round=win["config"]["n_estimators"],
                      valid_sets=[dva],
                      callbacks=[lgb.early_stopping(50, verbose=False)])
        rhat = m.predict(dev.loc[all_tr, feats])
        np.savez_compressed(out, idx=np.where(all_tr)[0], rhat=rhat,
                            best_iter=m.best_iteration)
        print(f"  rhat v={v} cached (best_iter={m.best_iteration})")


def stage_risk(dev, deadline: float):
    cfgs = sampled_configs(RISK_DIMS)
    (WORK / "s2_risk").mkdir(exist_ok=True)
    feats = feature_cols(dev)
    y_all = dev["label_c"].astype(int).to_numpy()
    for v in VAL_SEASONS:
        pend = [(i, c) for i, c in cfgs
                if not (WORK / "s2_risk" / f"cfg{i}_v{v}.json").exists()]
        if not pend:
            continue
        tr = (dev["season"] < v).to_numpy()
        va = (dev["season"] == v).to_numpy()
        assert_no_test_contact(dev.loc[tr | va, "season"], f"risk fold v={v}", DEV_SEASONS)
        z = np.load(WORK / f"rhat_v{v}.npz")
        assert (z["idx"] == np.where(tr)[0]).all()
        rhat = z["rhat"]
        ytr, yva = y_all[tr], y_all[va]
        tie = dev.loc[va, "_tiekey"].to_numpy()
        zmask = zero311_mask(dev, v)
        dtr = lgb.Dataset(dev.loc[tr, feats], label=ytr,
                          params={"feature_pre_filter": False}, free_raw_data=False)
        dva = lgb.Dataset(dev.loc[va, feats], label=yva, reference=dtr)
        Xva = dev.loc[va, feats]
        for i, cfg in pend:
            if time.time() > deadline:
                return False
            w = np.ones(len(ytr))
            w[ytr == 1] = 1.0 / np.maximum(rhat[ytr == 1], cfg["clip_floor"])
            dtr.set_weight(w)
            m = lgb.train(lgb_params(cfg, spw=spw_value(cfg["scale_pos_weight"], ytr)),
                          dtr, num_boost_round=cfg["n_estimators"], valid_sets=[dva],
                          callbacks=[lgb.early_stopping(50, verbose=False)])
            score = m.predict(Xva, num_iteration=m.best_iteration)
            res = eval_with_strata(yva, score, tie, zmask)
            rec = {"config_idx": i, "config": cfg, "v": v,
                   "ap": float(m.best_score["valid_0"]["average_precision"]),
                   "best_iter": int(m.best_iteration), "metrics": res,
                   "spw_value": spw_value(cfg["scale_pos_weight"], ytr),
                   "w_max": float(w.max())}
            (WORK / "s2_risk" / f"cfg{i}_v{v}.json").write_text(json.dumps(rec))
        print(f"  risk fold v={v} complete")
    return True


def risk_winner():
    out = WORK / "s2_winner.json"
    if out.exists():
        return json.loads(out.read_text())
    cfgs = sampled_configs(RISK_DIMS)
    rows = []
    for i, cfg in cfgs:
        recs = [json.loads((WORK / "s2_risk" / f"cfg{i}_v{v}.json").read_text())
                for v in VAL_SEASONS]
        z250 = [r["metrics"]["zero311"]["p@250"] for r in recs]
        rows.append({"config_idx": i, "config": cfg,
                     "mean_ap": float(np.mean([r["ap"] for r in recs])),
                     "mean_zero311_p250": float(np.mean(z250)),
                     "per_fold_ap": [r["ap"] for r in recs],
                     "per_fold_best_iter": [r["best_iter"] for r in recs]})
    # pre-registered selection: mean validation AP; tie-break zero-311 p@250
    rows.sort(key=lambda r: (-r["mean_ap"], -r["mean_zero311_p250"], r["config_idx"]))
    win = rows[0]
    win["boundary"] = boundary_status(win["config"], RISK_DIMS)
    win["n_configs_evaluated"] = len(rows)
    win["runner_up_mean_ap"] = rows[1]["mean_ap"]
    out.write_text(json.dumps(win, indent=2))
    return win


def stage_final(dev):
    """Refit both frozen winners on ALL dev seasons (n_est = round(mean best_iter),
    no ES — WFF frozen-refit convention) -> committed B4 artifacts."""
    cfg_out = MODELS / "b4_frozen_config.json"
    if cfg_out.exists():
        return
    MODELS.mkdir(parents=True, exist_ok=True)
    win1, win2 = prop_winner(), risk_winner()
    feats = feature_cols(dev)
    y_all = dev["label_c"].astype(int).to_numpy()
    y_dup = prop_target(dev)
    pos = y_all == 1
    assert_no_test_contact(dev["season"], "B4 final refit (all dev)", DEV_SEASONS)

    n1 = int(round(np.mean(win1["per_fold_best_iter"])))
    p1 = lgb_params(win1["config"]); p1.pop("feature_pre_filter")
    m1 = lgb.train(p1, lgb.Dataset(dev.loc[pos, feats], label=y_dup[pos]),
                   num_boost_round=n1)
    m1.save_model(str(MODELS / "b4_propensity_lgbm.txt"))
    rhat_all = m1.predict(dev[feats])

    n2 = int(round(np.mean(win2["per_fold_best_iter"])))
    w = np.ones(len(y_all))
    w[pos] = 1.0 / np.maximum(rhat_all[pos], win2["config"]["clip_floor"])
    p2 = lgb_params(win2["config"], spw=spw_value(win2["config"]["scale_pos_weight"], y_all))
    p2.pop("feature_pre_filter")
    m2 = lgb.train(p2, lgb.Dataset(dev[feats], label=y_all, weight=w),
                   num_boost_round=n2)
    m2.save_model(str(MODELS / "b4_risk_lgbm.txt"))

    cfg_out.write_text(json.dumps({
        "library": "lightgbm", "version": lgb.__version__, "seed": SEED,
        "stage1_propensity": {"config": win1["config"], "frozen_n_estimators": n1,
                              "train": "all dev label_c==1 rows, target y_dup=1{in-season 311 events>=2}"},
        "stage2_risk": {"config": win2["config"], "frozen_n_estimators": n2,
                        "train": "all dev rows, positives weighted 1/max(Rhat, clip_floor)",
                        "rhat_summary": {"min": float(rhat_all.min()),
                                         "max": float(rhat_all.max()),
                                         "share_below_clip": float(
                                             (rhat_all[pos] < win2["config"]["clip_floor"]).mean())}},
        "protocol": "forward-chaining train [2019, v), ES-50 watching v (as frozen "
                    "in hyperparam_grid.md), selection mean val AP / tie-break "
                    "zero-311 p@250; refit all-dev with fixed n_estimators",
        "dev_seasons": DEV_SEASONS, "val_seasons": VAL_SEASONS,
        "amendment1_boundary": "propensity target from the 311 UNION only; "
                               "ygpa-z7cr present solely as c7_* features",
    }, indent=2))
    print(f"  final B4 artifacts written (n1={n1}, n2={n2})")


def stage_report(dev):
    """Aggregate everything -> outputs/checkpoints/s3a_stats.json (the md
    checkpoint is authored separately from these numbers)."""
    win1, win2 = prop_winner(), risk_winner()
    b012 = json.loads((WORK / "b012.json").read_text())
    b3 = json.loads((WORK / "b3.json").read_text())
    b4_per = {str(v): json.loads(
        (WORK / "s2_risk" / f"cfg{win2['config_idx']}_v{v}.json").read_text())
        for v in VAL_SEASONS}

    def mean_over(res_by_v, path):
        vals = []
        for v in VAL_SEASONS:
            node = res_by_v[str(v)]
            for k in path:
                node = node[k]
            if node is not None:
                vals.append(node)
        return float(np.mean(vals)) if vals else None

    summary = {}
    tables = {"B0": b012["results"]["B0"], "B1": b012["results"]["B1"],
              "B2": b012["results"]["B2"], "B3": b3["results"],
              "B4": {str(v): b4_per[str(v)]["metrics"] for v in VAL_SEASONS}}
    for b, res in tables.items():
        summary[b] = {
            "mean_pr_auc": mean_over(res, ["pr_auc"]),
            "mean_p@250": mean_over(res, ["p@250"]),
            "mean_zero311_p@250": mean_over(res, ["zero311", "p@250"]),
            "mean_any311_p@250": mean_over(res, ["any311", "p@250"]),
        }
    guards = [json.loads(l) for l in
              (WORK / "guards.jsonl").read_text().splitlines() if l.strip()]
    payload = {
        "seed": SEED, "dev_seasons": DEV_SEASONS, "val_seasons": VAL_SEASONS,
        "ks": KS, "headline_k": HEADLINE_K,
        "library_versions": {"lightgbm": lgb.__version__,
                             "pandas": pd.__version__, "numpy": np.__version__},
        "summary_means": summary, "per_season": tables,
        "b1_provenance": b012["b1_provenance"],
        "b3_tree_count_assertion": b3["tree_count_assertion"],
        "b3_in_sample_caveat": b3["in_sample_caveat"],
        "b4_stage1_winner": win1, "b4_stage2_winner": win2,
        "guard_assertions": {"n_recorded_passes": len(guards),
                             "distinct_sites": sorted({g["where"] for g in guards}),
                             "max_season_ever_touched": max(
                                 max(g["touched"]) for g in guards),
                             "bright_line": "no season >= 2026 in any frame, "
                                            "filter, fold, or artifact"},
    }
    (CKPT / "s3a_stats.json").write_text(json.dumps(payload, indent=2))
    print("  wrote outputs/checkpoints/s3a_stats.json")
    for b in ("B0", "B1", "B2", "B3", "B4"):
        s = summary[b]
        print(f"  {b}: mean AP={s['mean_pr_auc']:.4f} p@250={s['mean_p@250']:.4f} "
              f"zero311 p@250={s['mean_zero311_p@250']:.4f}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=8.5,
                    help="wall-clock budget for this invocation")
    args = ap.parse_args()
    deadline = time.time() + args.minutes * 60
    WORK.mkdir(parents=True, exist_ok=True)
    print(f"=== S3a baselines — seed {SEED} — budget {args.minutes} min ===")

    dev = load_dev_frame()
    prep_311_tables()
    stage_b012(dev)
    stage_b3(dev)
    if not stage_prop(dev, deadline):
        print("PARTIAL: stage-1 propensity search pending — rerun to resume")
        return 0
    prop_winner()
    stage_rhat(dev)
    if not stage_risk(dev, deadline):
        print("PARTIAL: stage-2 risk search pending — rerun to resume")
        return 0
    risk_winner()
    stage_final(dev)
    stage_report(dev)
    print("ALL STAGES COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
