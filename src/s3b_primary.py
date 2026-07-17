"""S3b — primary two-head net per spec §3 EXACTLY (plan §3 step 8; grid LOCKED at
G2 per Amendment 2/3). Idempotent + RESUMABLE at EPOCH granularity: every
(config, fold, seed) unit checkpoints a resume state every epoch under
outputs/checkpoints/s3b_work/units/; an external kill loses at most one epoch of
one in-flight unit per worker. Seed 42 primary; 5-seed VALIDATION spread 42-46.
No network. Written for checkability: R-AUDIT blind-re-derives the likelihood
from spec §3 alone and must reproduce the fixed-batch per-term values persisted
by this script (s3b_work/fixed_batch/*).

REGENERATED FROM SCRATCH after the ledger-B68 removal of a killed session's
unhashed partial S3b outputs. Nothing from that session is referenced or reused.

Reads ONLY:
  data/processed/features_main.parquet  (49 feats, S2-audited; sha256 asserted
                                          against PROVENANCE at load)
  data/processed/features_b3.parquet    (hash asserted only — recipe-hash bundle)
  data/raw/c311_heat_complaints.parquet (311 union deliverable — NLL counts,
                                          zero-311 stratum flags; the SOLE
                                          complaint source of the loss,
                                          Amendment-1 boundary)

TEST-SEASON SANCTITY (spec §4, Rule 3): season 2026-27 is structurally absent
(spine ends start-year 2025, asserted at load); assert_no_test_contact() runs at
every load, fold build, refit, and scoring pass; every pass is appended to
s3b_work/guards.jsonl.

ARCHITECTURE — spec §3 verbatim, hyperparameters ONLY from the locked grid
(outputs/checkpoints/hyperparam_grid.md §2-§4, §6):
  shared MLP encoder over the standardized inputs; head F = Linear(width,1)+
  sigmoid; head p = Linear(width,1)+sigmoid; R = 1 - (1-p)^min(u, u*);
  L = BCE(Y_obs, F*R) + lam * NLL(complaint counts | head p, building-season)
      + Omega1 + Omega2   (the two grid-§4 penalty forms).
  Grid: width{64,128,256} x depth{2,3} x dropout{0,0.15} x lam{.1,.3,1,3} x
  u*{25,50,100} x lr{3e-4,1e-3} x mu1{0,.01,.1} x mu2{0,.1,1} = 2,592; sampled
  n=60 without replacement, sampling seed 42, same decode/sample machinery as
  the audited S3a scripts. AdamW wd=1e-5, cosine LR to 0 over 200 epochs, batch
  8192, ES patience 20 on fold-v TOTAL validation loss (all four terms, eval
  mode, train-fold constants), max 200 epochs. No class reweighting.

RESOLVED IMPLEMENTATION AXES (spec §3 / grid text leave these open; each is
resolved HERE, independently of any prior session, and disclosed in
outputs/checkpoints/s3b_primary.md — the blind-audit comparison is on the
persisted per-term fixed-batch values):

 A1. NLL form = ZERO-TRUNCATED BINOMIAL at building-season grain.
     Eligible rows: label_c == 1 AND k_raw >= 1 ("confirmed-incident exposure"
     read as: a confirmed incident creates the exposure-to-reporting;
     "on complaint-positive building-seasons" per grid §3 / spec §3(i)).
     Exposure n_i = u_i = min(u_raw_i, u*)   (same capped u as the R link —
       keeps head p on one scale in both terms).
     Count k_i = min(k_raw_i, u_i), k_raw = in-season (Oct 1-May 31, label
       build's own season_of) 311-UNION heat complaint events for the
       building-season. The cap count is reported (events can exceed units).
     nll_i = -[ logC(u_i,k_i) + k_i*log(p_i) + (u_i-k_i)*log(1-p_i)
                - log(1 - (1-p_i)^{u_i}) ]
     logC(u,k) = lgamma(u+1) - lgamma(k+1) - lgamma(u-k+1) (constant in the
     parameters; INCLUDED so persisted values are the full likelihood). The
     truncation term conditions on k >= 1 (its normalizer is exactly R with
     u = u_i). NLL term of the loss = mean of nll_i over eligible rows in the
     batch (0 if none); L adds lam * that mean. Per-term persistence decomposes
     nll into (comb, k*log p, (u-k)*log(1-p), -log R) so any reading divergence
     is isolable.
 A2. u_raw = unitstotal if finite & >= 1, else unitsres if finite & >= 1,
     else 3 (spine = HPD-registered multiple dwellings, legally >= 3 units).
     Fallback counts reported.
 A3. Omega1 (grid §4.1) is averaged over ALL batch rows (its purpose is the
     zero-311 mass); pbar = sum(k_i)/sum(u_i) over the TRAIN-fold eligible rows
     (capped k and u, so pbar depends on (fold, u*)); computed at prep, cached,
     persisted.
 A4. Omega2 (grid §4.2): perturbed-column list = the family-1 cumulative-count
     column, exactly {viol_cnt_prior_cum} (grid §4: "family-1 cumulative-count
     columns only"; it is the only such column in the frozen S2 list). delta =
     +0.5 in STANDARDIZED units. Per-batch subsample = the first
     min(2048, batch) rows of each shuffled batch (deterministic given the
     epoch permutation). Validation and fixed-batch Omega2 use ALL rows (no
     subsample; deterministic). The two penalty forwards (F(x), F(x+delta))
     run in EVAL mode even during training — with dropout active the two
     passes would draw different masks and the hinge would penalize dropout
     noise, not the perturbation response; LayerNorm has no batch state, so
     eval-mode forwards are exact. Gradient flows through both.
 A5. Inputs: the 49 frozen feature columns (labels/keys excluded). The two
     categoricals one-hot with their frozen vocabularies (24 + 5); a missing
     categorical is the all-zeros row (the one-hots are exhaustive, so
     all-zeros uniquely encodes missing — no extra indicator). Numeric columns
     whose dev-universe non-null values are within {0,1} are passed as
     indicators (unstandardized) per the grid-§2 mask language; all other
     numeric columns are standardized with mean/std fit on TRAIN-FOLD rows
     only (nan-aware). Every NUMERIC column with any NULL in the dev universe
     gets a 0/1 missingness-indicator column; NULLs become 0 AFTER
     standardization (= train mean). NO other imputation. Exact design-column
     list persisted in s3b_work/design_meta.json.
 A6. Encoder block order: Linear -> LayerNorm -> ReLU -> Dropout (grid fixes
     the pieces, not the order). Init = PyTorch Linear defaults re-implemented
     with an explicit torch.Generator: W ~ U(-b,b), b = 1/sqrt(fan_in); bias
     likewise (documented so init is reproducible from this text).
 A7. Total VALIDATION loss for ES = BCE + lam*NLL + Omega1 + Omega2 on fold v,
     eval mode (dropout off), train-fold pbar/scaler, Omega2 over all val rows.
 A8. Numeric clamps (persisted with the fixed batch; binding counts reported):
     p and q = F*R clamped to [1e-7, 1-1e-7] inside logs; the truncation
     normalizer clamped to >= 1e-12 before log. Training float32 (CPU,
     TRAIN_THREADS=3 fixed for determinism); fixed-batch persistence recomputed
     in float64 from the float32 weights.
 A9. Refit convention (WFF/B4 analog): after selection, refit on ALL dev
     seasons, seed 42, epochs E* = round(mean over folds of the winner's best
     epoch), cosine schedule still defined over 200 epochs (identical LR
     trajectory as validation training, stopped at E*), no ES.
 A10. Seed semantics: seed s drives init, per-epoch shuffle, dropout stream,
     and (via the shuffle) the Omega2 subsample; epoch seeds =
     SeedSequence([s, fold_code, epoch]) (fold_code = v, or 0 for the all-dev
     refit) so a resumed unit continues bit-identically at epoch boundaries.
     Config index deliberately does NOT enter seeding (all configs see the same
     draw, LightGBM-precedent). Seeds 43-46 appear ONLY in the validation
     spread of the frozen winner config; every other number is seed 42.

SELECTION (pre-registered, grid §1): mean over the 5 folds of validation AP of
the observed-label prediction q = F*R vs Y_obs; tie-break mean zero-311-stratum
p@250 of the deployment ranking F; then config index. Zero-311 stratum per spec
§6: zero 311-union events in [2019-06-01, Oct 1 v).

FIXED BATCH for the blind re-derivation (s3b_work/fixed_batch/): rows of the
all-dev refit universe in frame order (sorted season, bbl_n): the first 4096
rows UNION the first 4096 NLL-eligible rows, order-preserving, duplicates
dropped (exact keys persisted). Per-term values + per-row (F, p, R, q, F_pert)
in float64 at three points of the seed-42 refit: t0 = after init before any
step; t1 = after epoch 1; tE = final. Plus all constants (lam, u*, mu1, mu2,
pbar, delta, clamps) and per-row (y, u, k, eligible).
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
PROC = REPO / "data" / "processed"
RAW = REPO / "data" / "raw"
CKPT = REPO / "outputs" / "checkpoints"
WORK = CKPT / "s3b_work"
UNITS = WORK / "units"
FIXED = WORK / "fixed_batch"
MODELS = REPO / "outputs" / "models"

SEED = 42
SPREAD_SEEDS = [42, 43, 44, 45, 46]
DEV_SEASONS = list(range(2019, 2026))
LAG_SEASONS = [2017, 2018]
VAL_SEASONS = [2021, 2022, 2023, 2024, 2025]
FORBIDDEN_FROM = 2026
KS = [100, 250, 500, 1000, 2500]
N_SAMPLED = 60
KEYS = ("bbl_n", "season", "label_c", "label_bc")

# S2-audited frame hashes (PROVENANCE; re-verified by LEAD post-incident) —
# asserted at prep so this stage can never run on a drifted frame.
SHA_MAIN = "477d3079fae0a4a76ee5507739c6f790448caa258c11ea78776583f2e4734090"
SHA_B3 = "09f8e94df5c51fa66778e17cc2d9bbba0eceb0aeef2453b411d7662ef324fa09"

# ---- LOCKED grid §2-§4, §6 (dims in the grid-§6 listing order) ----
NET_DIMS = [
    ("width", [64, 128, 256]),
    ("depth", [2, 3]),
    ("dropout", [0.0, 0.15]),
    ("lam", [0.1, 0.3, 1.0, 3.0]),
    ("ustar", [25, 50, 100]),
    ("lr", [3e-4, 1e-3]),
    ("mu1", [0.0, 0.01, 0.1]),
    ("mu2", [0.0, 0.1, 1.0]),
]
WEIGHT_DECAY = 1e-5          # fixed (grid §3)
BATCH = 8192                 # fixed (grid §3)
MAX_EPOCHS = 200             # ceiling (grid §3)
PATIENCE = 20                # fixed (grid §3)
TRAIN_THREADS = 3            # fixed for determinism across invocations/workers
CLAMP_EPS = 1e-7             # A8
TRUNC_EPS = 1e-12            # A8
DELTA_STD = 0.5              # fixed (grid §4.2)
OMEGA2_SUB = 2048            # A4
PERTURB_COLS = ["viol_cnt_prior_cum"]   # A4
U_FALLBACK = 3.0             # A2

FOLD_ALL = "all"             # refit universe key


# ------------------------- small utilities -------------------------

def atomic_write(path: Path, text: str):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def atomic_save_torch(obj, path: Path):
    import torch
    tmp = path.with_suffix(path.suffix + ".tmp")
    torch.save(obj, tmp)
    os.replace(tmp, path)


def stable_seed(*parts) -> int:
    """Deterministic 32-bit seed from integer parts (A10)."""
    return int(np.random.SeedSequence(list(parts)).generate_state(1)[0])


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def season_of(dt):
    """NYC heat season (Oct 1 - May 31); same fn as the label build / S3a."""
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
    """HARD STOP on any season >= 2026 or outside the allowed set (Rule 3/9).
    Same pattern as the audited S3a scripts; S3b logs to its OWN guards file."""
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


# ------------------------- metrics (S3a-identical helpers) -------------------------

def precision_at_k(y_true, order, k):
    if k > len(order):
        return None
    return float(y_true[order[:k]].sum()) / k


def stable_rank_order(score, rng_key):
    return np.lexsort((rng_key, -score))


def eval_ranking(y_true, score, rng_key) -> dict:
    from sklearn.metrics import average_precision_score, roc_auc_score
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
    res = eval_ranking(y, score, tie)
    for name, m in (("zero311", zero_mask), ("any311", ~zero_mask)):
        res[name] = eval_ranking(y[m], score[m], tie[m])
    return res


# ------------------------- grid machinery (S3a-identical) -------------------------

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
    size = space_size(dims)
    rng = np.random.default_rng(SEED)
    idxs = sorted(int(i) for i in rng.choice(size, size=N_SAMPLED, replace=False))
    return [(i, decode(i, dims)) for i in idxs]


def boundary_status(cfg: dict, dims) -> dict:
    out = {}
    for name, vals in dims:
        pos = vals.index(cfg[name])
        out[name] = "interior" if 0 < pos < len(vals) - 1 else \
            ("low-edge" if pos == 0 else "high-edge")
    return out


# ------------------------- prep: design matrix + loss ingredients -------------------------

def prep_design():
    """One-time cache build (idempotent): raw design matrix (float32, NaN kept),
    design_meta.json, per-fold scalers, per-row loss ingredients (y, u, k,
    eligible), zero-311 masks, pbar table, and the frame-hash assertions."""
    meta_path = WORK / "design_meta.json"
    if meta_path.exists():
        return
    WORK.mkdir(parents=True, exist_ok=True)

    hashes = {"features_main.parquet": sha256_file(PROC / "features_main.parquet"),
              "features_b3.parquet": sha256_file(PROC / "features_b3.parquet")}
    assert hashes["features_main.parquet"] == SHA_MAIN, \
        f"features_main.parquet hash drift: {hashes['features_main.parquet']} (Rule 9)"
    assert hashes["features_b3.parquet"] == SHA_B3, \
        f"features_b3.parquet hash drift: {hashes['features_b3.parquet']} (Rule 9)"

    f = pd.read_parquet(PROC / "features_main.parquet")
    assert int(f["season"].max()) == 2025, "spine must end at start-year 2025"
    assert_no_test_contact(f["season"], "s3b features_main load",
                           allowed=LAG_SEASONS + DEV_SEASONS)
    dev = f[f["season"].isin(DEV_SEASONS)].copy()
    assert_no_test_contact(dev["season"], "s3b dev universe", DEV_SEASONS)
    dev = dev.sort_values(["season", "bbl_n"], kind="mergesort").reset_index(drop=True)
    rng = np.random.default_rng(SEED)
    tiekey = rng.permutation(len(dev))

    # ---- 311 union tables (regenerated locally; Amendment-1: sole loss source)
    c = pd.read_parquet(RAW / "c311_heat_complaints.parquet",
                        columns=["bbl", "created_date"])
    c["bbl_n"] = norm_bbl(c["bbl"])
    c["created_date"] = pd.to_datetime(c["created_date"], errors="coerce")
    c = c[c["bbl_n"].notna() & c["created_date"].notna()]
    assert len(c) > 0, "empty 311 union pull (Rule 1/9)"
    first = c.groupby("bbl_n")["created_date"].min().rename("first311")
    cs = c["created_date"].map(season_of)
    ins = c[cs.notna()].copy()
    ins["season"] = cs[cs.notna()].astype(int)
    ins = ins[ins["season"].isin(DEV_SEASONS)]
    assert_no_test_contact(ins["season"], "s3b in-season 311 counts (NLL)", DEV_SEASONS)
    cnt = ins.groupby(["bbl_n", "season"]).size().rename("n311")

    # ---- per-row loss ingredients (A1/A2)
    k_raw = pd.MultiIndex.from_frame(dev[["bbl_n", "season"]]).map(cnt)
    k_raw = pd.Series(k_raw, dtype="float64").fillna(0.0).to_numpy()
    ut = dev["unitstotal"].astype(float).to_numpy()
    ur = dev["unitsres"].astype(float).to_numpy()
    u_raw = np.where(np.isfinite(ut) & (ut >= 1), ut,
                     np.where(np.isfinite(ur) & (ur >= 1), ur, U_FALLBACK))
    u_src = np.where(np.isfinite(ut) & (ut >= 1), 0,
                     np.where(np.isfinite(ur) & (ur >= 1), 1, 2))
    y = dev["label_c"].astype(int).to_numpy()
    eligible = (y == 1) & (k_raw >= 1)

    # ---- zero-311 stratum masks per fold (spec §6; S3a-identical construction)
    zmasks = {}
    fmap = dev["bbl_n"].map(first)
    for v in VAL_SEASONS:
        cutoff = pd.Timestamp(v, 10, 1)
        rows = dev["season"] == v
        m = fmap[rows]
        zmasks[str(v)] = (~(m.notna() & (m < cutoff))).to_numpy()

    # ---- design matrix (A5)
    feat_cols = [c_ for c_ in dev.columns if c_ not in KEYS]
    cat_cols = [c_ for c_ in feat_cols if str(dev[c_].dtype) == "category"]
    num_cols = [c_ for c_ in feat_cols if c_ not in cat_cols]
    is_binary, has_nan = {}, {}
    for c_ in num_cols:
        col = dev[c_].astype(float)
        has_nan[c_] = bool(col.isna().any())
        vals = pd.unique(col.dropna())
        is_binary[c_] = bool(np.isin(vals, [0.0, 1.0]).all())
    std_cols = [c_ for c_ in num_cols if not is_binary[c_]]
    bin_cols = [c_ for c_ in num_cols if is_binary[c_]]
    isna_cols = [c_ for c_ in num_cols if has_nan[c_]]
    onehot = {c_: [str(x) for x in dev[c_].cat.categories] for c_ in cat_cols}
    for c_ in cat_cols:
        has_nan[c_] = bool(dev[c_].isna().any())

    design_cols, blocks = [], []
    for c_ in std_cols + bin_cols:
        design_cols.append(c_)
        blocks.append(dev[c_].astype(float).to_numpy(dtype=np.float32)[:, None])
    for c_ in isna_cols:
        design_cols.append(f"{c_}__isna")
        blocks.append(dev[c_].isna().to_numpy(dtype=np.float32)[:, None])
    for c_ in cat_cols:
        s = dev[c_].astype(object)
        for lvl in onehot[c_]:
            design_cols.append(f"{c_}=={lvl}")
            blocks.append((s == lvl).to_numpy(dtype=np.float32)[:, None])
    X = np.hstack(blocks).astype(np.float32)
    np.save(WORK / "design.npy", X)

    # ---- per-fold nan-aware scalers on the std block only (A5) + pbar (A3)
    n_std = len(std_cols)
    season_arr = dev["season"].to_numpy()
    scalers, pbar = {}, {}
    fold_keys = [str(v) for v in VAL_SEASONS] + [FOLD_ALL]
    for fk in fold_keys:
        tr = season_arr < int(fk) if fk != FOLD_ALL else np.ones(len(dev), bool)
        assert_no_test_contact(season_arr[tr], f"s3b scaler/pbar fold={fk}", DEV_SEASONS)
        sub = X[tr, :n_std].astype(np.float64)
        m = np.nanmean(sub, axis=0)
        s = np.nanstd(sub, axis=0)
        m = np.where(np.isfinite(m), m, 0.0)
        s = np.where(np.isfinite(s) & (s > 1e-12), s, 1.0)
        scalers[fk] = {"mean": m.tolist(), "std": s.tolist()}
        el = tr & eligible
        for ustar in NET_DIMS[4][1]:
            u_c = np.minimum(u_raw[el], float(ustar))
            k_c = np.minimum(k_raw[el], u_c)
            pbar[f"{fk}|{ustar}"] = float(k_c.sum() / u_c.sum())

    meta = {
        "n_rows": int(len(dev)), "n_design_cols": len(design_cols),
        "design_cols": design_cols, "std_cols": std_cols, "bin_cols": bin_cols,
        "isna_cols": isna_cols, "onehot": onehot,
        "perturb_design_idx": [design_cols.index(c_) for c_ in PERTURB_COLS],
        "frame_hashes": hashes,
        "u_source_counts": {"unitstotal": int((u_src == 0).sum()),
                            "unitsres_fallback": int((u_src == 1).sum()),
                            "const3_fallback": int((u_src == 2).sum())},
        "n_eligible": int(eligible.sum()),
        "n_labelc1": int((y == 1).sum()),
        "k_exceeds_u_by_ustar": {str(us): int((eligible & (
            k_raw > np.minimum(u_raw, float(us)))).sum()) for us in NET_DIMS[4][1]},
        "pbar": pbar,
        "constants": {"clamp_eps": CLAMP_EPS, "trunc_eps": TRUNC_EPS,
                      "delta_std": DELTA_STD, "omega2_subsample": OMEGA2_SUB,
                      "u_fallback": U_FALLBACK, "batch": BATCH,
                      "max_epochs": MAX_EPOCHS, "patience": PATIENCE,
                      "weight_decay": WEIGHT_DECAY, "train_threads": TRAIN_THREADS},
    }
    atomic_write(meta_path, json.dumps(meta, indent=2))
    atomic_write(WORK / "scalers.json", json.dumps(scalers))
    np.savez_compressed(
        WORK / "aux.npz", y=y.astype(np.int8), season=season_arr.astype(np.int16),
        bbl=dev["bbl_n"].astype(np.int64).to_numpy(), tiekey=tiekey,
        k_raw=k_raw, u_raw=u_raw, eligible=eligible,
        **{f"zero311_{v}": zmasks[str(v)] for v in VAL_SEASONS})
    print(f"  prep: design {X.shape}, eligible NLL rows {int(eligible.sum()):,} "
          f"of {int((y == 1).sum()):,} label_c=1; hashes asserted")


# ------------------------- model + loss (torch) -------------------------

def build_model(cfg: dict, d_in: int, seed: int, fold_code: int):
    """Two-head net per spec §3; deterministic init via explicit generator (A6)."""
    import torch
    import torch.nn as nn

    class TwoHead(nn.Module):
        def __init__(self):
            super().__init__()
            layers, din = [], d_in
            for _ in range(cfg["depth"]):
                layers += [nn.Linear(din, cfg["width"]), nn.LayerNorm(cfg["width"]),
                           nn.ReLU(), nn.Dropout(cfg["dropout"])]
                din = cfg["width"]
            self.encoder = nn.Sequential(*layers)
            self.head_F = nn.Linear(cfg["width"], 1)
            self.head_p = nn.Linear(cfg["width"], 1)

        def forward(self, x):
            h = self.encoder(x)
            return (torch.sigmoid(self.head_F(h)).squeeze(-1),
                    torch.sigmoid(self.head_p(h)).squeeze(-1))

    model = TwoHead()
    g = torch.Generator().manual_seed(stable_seed(seed, fold_code, 0, 1))
    with torch.no_grad():
        for mod in list(model.encoder) + [model.head_F, model.head_p]:
            if isinstance(mod, nn.Linear):
                b = 1.0 / math.sqrt(mod.in_features)
                mod.weight.copy_((torch.rand(mod.weight.shape, generator=g) * 2 - 1) * b)
                mod.bias.copy_((torch.rand(mod.bias.shape, generator=g) * 2 - 1) * b)
    return model


def loss_terms(model, x, y, u, k, elig, cfg, pbar, train: bool,
               omega2_idx=None, decompose: bool = False):
    """The spec-§3 loss, term by term. All clamps per A8. Returns dict of terms
    (torch scalars). x standardized; u,k already capped at this cfg's u*."""
    import torch
    F, p = model(x)
    p_c = p.clamp(CLAMP_EPS, 1 - CLAMP_EPS)
    R = 1 - (1 - p_c) ** u
    q = (F * R).clamp(CLAMP_EPS, 1 - CLAMP_EPS)
    bce = -(y * torch.log(q) + (1 - y) * torch.log(1 - q)).mean()

    out = {"bce": bce}
    n_el = int(elig.sum())
    if n_el > 0:
        pe, ue, ke = p_c[elig], u[elig], k[elig]
        comb = (torch.lgamma(ue + 1) - torch.lgamma(ke + 1)
                - torch.lgamma(ue - ke + 1))
        klogp = ke * torch.log(pe)
        uklog = (ue - ke) * torch.log(1 - pe)
        logR = torch.log((1 - (1 - pe) ** ue).clamp_min(TRUNC_EPS))
        nll = -(comb + klogp + uklog - logR).mean()
        if decompose:
            out.update({"nll_comb_mean": comb.mean(), "nll_klogp_mean": klogp.mean(),
                        "nll_uklog1mp_mean": uklog.mean(), "nll_logR_mean": logR.mean(),
                        "nll_no_trunc_mean": -(comb + klogp + uklog).mean()})
    else:
        nll = bce * 0.0
    out["nll_mean"] = nll
    out["n_eligible"] = n_el

    logit_pbar = math.log(pbar / (1 - pbar))
    om1_raw = ((torch.log(p_c) - torch.log(1 - p_c)) - logit_pbar).pow(2).mean()
    out["omega1_raw"] = om1_raw

    if cfg["mu2"] > 0 or decompose:
        if train and omega2_idx is not None:
            xs = x[omega2_idx]
        else:
            xs = x
        xp = xs.clone()
        for j in PERT_IDX:
            xp[:, j] = xp[:, j] + DELTA_STD
        was_training = model.training
        model.eval()          # A4: penalty forwards in eval mode (no dropout
        F0, _ = model(xs)     # noise between the paired passes); grads flow.
        Fp, _ = model(xp)
        if was_training:
            model.train()
        om2_raw = torch.relu(F0 - Fp).pow(2).mean()
    else:
        om2_raw = bce * 0.0
    out["omega2_raw"] = om2_raw

    out["total"] = (bce + cfg["lam"] * nll + cfg["mu1"] * om1_raw
                    + cfg["mu2"] * om2_raw)
    if decompose:
        out.update({"F": F, "p": p, "R": R, "q": q})
    return out


PERT_IDX: list = []   # set at fold-tensor build from design_meta


# ------------------------- fold tensors -------------------------

_FOLD_CACHE: dict = {}


def fold_tensors(fk: str, cfg_ustar: float | None = None):
    """Standardized tensors for fold key fk ('2021'..'2025' or 'all').
    Cached per fk (u-capping is done per-config, cheaply, outside the cache)."""
    import torch
    global PERT_IDX
    if fk in _FOLD_CACHE:
        return _FOLD_CACHE[fk]
    meta = json.loads((WORK / "design_meta.json").read_text())
    scal = json.loads((WORK / "scalers.json").read_text())[fk]
    aux = np.load(WORK / "aux.npz")
    PERT_IDX = meta["perturb_design_idx"]
    X = np.load(WORK / "design.npy", mmap_mode="r")
    season = aux["season"]
    n_std = len(meta["std_cols"])

    def block(rows):
        assert_no_test_contact(season[rows], f"s3b fold tensors fk={fk}", DEV_SEASONS)
        A = np.asarray(X[rows], dtype=np.float32).copy()
        A[:, :n_std] = (A[:, :n_std] - np.asarray(scal["mean"], np.float32)) \
            / np.asarray(scal["std"], np.float32)
        A[~np.isfinite(A)] = 0.0
        return {"x": torch.from_numpy(A),
                "y": torch.from_numpy(aux["y"][rows].astype(np.float32)),
                "u_raw": torch.from_numpy(aux["u_raw"][rows].astype(np.float32)),
                "k_raw": torch.from_numpy(aux["k_raw"][rows].astype(np.float32)),
                "elig": torch.from_numpy(aux["eligible"][rows]),
                "rows": np.where(rows)[0]}

    if fk == FOLD_ALL:
        out = {"train": block(np.ones(len(season), bool)), "val": None, "v": None}
    else:
        v = int(fk)
        out = {"train": block(season < v), "val": block(season == v), "v": v,
               "tie_val": aux["tiekey"][season == v],
               "zero311_val": aux[f"zero311_{v}"]}
    _FOLD_CACHE.clear()          # hold at most one fold in memory
    _FOLD_CACHE[fk] = out
    return out


def cap_uk(t, ustar: float):
    import torch
    u = torch.minimum(t["u_raw"], torch.tensor(float(ustar)))
    k = torch.minimum(t["k_raw"], u)
    return u, k


# ------------------------- unit training (resumable) -------------------------

def eval_pass(model, t, cfg, pbar, chunk=65536, decompose=False):
    """Eval-mode full pass: total val loss terms + F, p arrays (float32)."""
    import torch
    model.eval()
    u, k = cap_uk(t, cfg["ustar"])
    Fs, ps = [], []
    terms_acc = None
    n = len(t["y"])
    with torch.no_grad():
        # loss terms need global means -> accumulate sums
        sums = {"bce": 0.0, "nll": 0.0, "om1": 0.0, "om2": 0.0, "n_el": 0}
        for i in range(0, n, chunk):
            sl = slice(i, i + chunk)
            o = loss_terms(model, t["x"][sl], t["y"][sl], u[sl], k[sl],
                           t["elig"][sl], cfg, pbar, train=False)
            m = sl.stop is None and n or min(i + chunk, n)
            w = m - i
            sums["bce"] += float(o["bce"]) * w
            sums["om1"] += float(o["omega1_raw"]) * w
            sums["om2"] += float(o["omega2_raw"]) * w
            sums["nll"] += float(o["nll_mean"]) * o["n_eligible"]
            sums["n_el"] += o["n_eligible"]
            F, p = model(t["x"][sl])
            Fs.append(F.numpy().copy()); ps.append(p.numpy().copy())
        bce = sums["bce"] / n
        nll = sums["nll"] / max(1, sums["n_el"])
        om1 = sums["om1"] / n
        om2 = sums["om2"] / n
        total = bce + cfg["lam"] * nll + cfg["mu1"] * om1 + cfg["mu2"] * om2
    model.train()
    return {"bce": bce, "nll_mean": nll, "omega1_raw": om1, "omega2_raw": om2,
            "total": total, "n_eligible": sums["n_el"]}, \
        np.concatenate(Fs), np.concatenate(ps)


def train_unit(cfg_idx: int, cfg: dict, fk: str, seed: int, deadline: float,
               epochs_override: int | None = None,
               capture_fixed=None) -> str:
    """Train one (config, fold, seed) unit with epoch-level resume.
    Returns 'done' | 'partial'. Writes UNITS/<uid>.json on completion."""
    import torch
    torch.set_num_threads(TRAIN_THREADS)
    uid = f"cfg{cfg_idx}_v{fk}_s{seed}"
    done_path = UNITS / f"{uid}.json"
    if done_path.exists():
        return "done"
    res_path = UNITS / f"{uid}.resume.pt"
    UNITS.mkdir(parents=True, exist_ok=True)

    t = fold_tensors(fk)
    tr, va = t["train"], t["val"]
    meta = json.loads((WORK / "design_meta.json").read_text())
    pbar = meta["pbar"][f"{fk}|{cfg['ustar']}"]
    fold_code = 0 if fk == FOLD_ALL else int(fk)
    max_ep = epochs_override if epochs_override is not None else MAX_EPOCHS

    model = build_model(cfg, tr["x"].shape[1], seed, fold_code)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["lr"],
                            weight_decay=WEIGHT_DECAY)
    start_ep, best = 1, {"epoch": 0, "val_total": float("inf"), "state": None}
    val_hist = []
    if res_path.exists():
        st = torch.load(res_path, weights_only=False)
        model.load_state_dict(st["model"])
        opt.load_state_dict(st["opt"])
        start_ep = st["epoch_done"] + 1
        best = st["best"]
        val_hist = st["val_hist"]

    if capture_fixed is not None and start_ep == 1:
        capture_fixed(model, "t0_init")

    u_tr, k_tr = cap_uk(tr, cfg["ustar"])
    n = len(tr["y"])
    model.train()
    ep = start_ep - 1
    for ep in range(start_ep, max_ep + 1):
        es = stable_seed(seed, fold_code, ep)
        torch.manual_seed(es)                       # dropout stream (A10)
        g = torch.Generator().manual_seed(es + 1)   # shuffle
        perm = torch.randperm(n, generator=g)
        lr_t = cfg["lr"] * 0.5 * (1 + math.cos(math.pi * (ep - 1) / MAX_EPOCHS))
        for pg in opt.param_groups:
            pg["lr"] = lr_t
        for i in range(0, n, BATCH):
            idx = perm[i:i + BATCH]
            sub = torch.arange(min(OMEGA2_SUB, len(idx)))  # A4: first rows of batch
            o = loss_terms(model, tr["x"][idx], tr["y"][idx], u_tr[idx], k_tr[idx],
                           tr["elig"][idx], cfg, pbar, train=True, omega2_idx=sub)
            opt.zero_grad()
            o["total"].backward()
            opt.step()
            tot = float(o["total"].detach())
            if not math.isfinite(tot):
                raise AssertionError(
                    f"NON-FINITE LOSS unit={uid} epoch={ep}: {tot} (Rule 1/9)")
        if capture_fixed is not None and ep == 1:
            capture_fixed(model, "t1_epoch1")

        if va is not None:
            vterms, _, _ = eval_pass(model, va, cfg, pbar)
            if not math.isfinite(vterms["total"]):
                raise AssertionError(
                    f"NON-FINITE VAL LOSS unit={uid} epoch={ep} (Rule 1/9)")
            val_hist.append({"epoch": ep, **vterms, "lr": lr_t})
            if vterms["total"] < best["val_total"]:
                best = {"epoch": ep, "val_total": vterms["total"],
                        "state": copy.deepcopy(model.state_dict())}
            stop = ep - best["epoch"] >= PATIENCE
        else:
            stop = False
        atomic_save_torch({"epoch_done": ep, "model": model.state_dict(),
                           "opt": opt.state_dict(), "best": best,
                           "val_hist": val_hist}, res_path)
        if stop:
            break
        if time.time() > deadline and ep < max_ep:
            return "partial"

    # ---- completion
    if va is not None:
        model.load_state_dict(best["state"])
        vterms, Fv, pv = eval_pass(model, va, cfg, pbar)
        u_va, _ = cap_uk(va, cfg["ustar"])
        q = Fv * (1 - (1 - np.clip(pv, CLAMP_EPS, 1 - CLAMP_EPS))
                  ** u_va.numpy())
        yv = va["y"].numpy().astype(int)
        tie, z = t["tie_val"], t["zero311_val"]
        metrics_q = eval_with_strata(yv, q, tie, z)
        metrics_F = eval_with_strata(yv, Fv, tie, z)
        rec = {
            "unit": uid, "config_idx": cfg_idx, "config": cfg, "fold": fk,
            "seed": seed, "best_epoch": best["epoch"], "epochs_run": ep,
            "val_terms_at_best": {k_: v_ for k_, v_ in vterms.items()},
            "metrics_q": metrics_q,
            "metrics_F": metrics_F,
            "ap_q": metrics_q["pr_auc"],
            "zero311_p250_F": metrics_F["zero311"]["p@250"],
            "pbar": pbar, "n_train": int(n), "n_val": int(len(yv)),
            "n_nll_train": int(tr["elig"].sum().item()),
            "n_nll_val": int(va["elig"].sum().item()),
            "val_hist": val_hist,
        }
        atomic_write(done_path, json.dumps(rec))
        res_path.unlink(missing_ok=True)
    else:
        # refit unit: persist artifact instead of metrics
        rec = {"unit": uid, "config_idx": cfg_idx, "config": cfg, "fold": fk,
               "seed": seed, "epochs_run": ep, "pbar": pbar, "n_train": int(n),
               "n_nll_train": int(tr["elig"].sum().item())}
        atomic_write(done_path, json.dumps(rec))
        atomic_save_torch({"state_dict": model.state_dict()},
                          UNITS / f"{uid}.model.pt")
        res_path.unlink(missing_ok=True)
    return "done"


# ------------------------- worker pool -------------------------

def _worker(unit_q, deadline):
    import torch
    torch.set_num_threads(TRAIN_THREADS)
    while time.time() < deadline:
        try:
            item = unit_q.get_nowait()
        except Exception:
            return
        cfg_idx, cfg, fk, seed = item
        try:
            train_unit(cfg_idx, cfg, fk, seed, deadline)
        except AssertionError:
            raise
        except Exception as e:  # persist the exact failure state (Rule 1)
            atomic_write(UNITS / f"cfg{cfg_idx}_v{fk}_s{seed}.error.json",
                         json.dumps({"error": repr(e)}))
            raise


def run_pool(units, deadline, n_workers) -> bool:
    """Run pending units until done or deadline. True iff all units complete."""
    import multiprocessing as mp
    pending = [(i, c, fk, s) for (i, c, fk, s) in units
               if not (UNITS / f"cfg{i}_v{fk}_s{s}.json").exists()]
    if not pending:
        return True
    UNITS.mkdir(parents=True, exist_ok=True)
    if n_workers <= 1:
        for it in pending:
            if time.time() > deadline:
                break
            train_unit(it[0], it[1], it[2], it[3], deadline)
    else:
        ctx = mp.get_context("spawn")
        q = ctx.Queue()
        for it in pending:
            q.put(it)
        procs = [ctx.Process(target=_worker, args=(q, deadline))
                 for _ in range(n_workers)]
        for p_ in procs:
            p_.start()
        for p_ in procs:
            p_.join()
        errs = list(UNITS.glob("*.error.json"))
        if errs:
            raise AssertionError(f"worker unit errors (Rule 9): "
                                 f"{[e.name for e in errs]}")
    return all((UNITS / f"cfg{i}_v{fk}_s{s}.json").exists()
               for (i, c, fk, s) in pending)


# ------------------------- stages -------------------------

def search_units():
    cfgs = sampled_configs(NET_DIMS)
    return [(i, c, str(v), SEED) for v in VAL_SEASONS for (i, c) in cfgs]


def stage_winner():
    out = WORK / "winner.json"
    if out.exists():
        return json.loads(out.read_text())
    cfgs = sampled_configs(NET_DIMS)
    rows = []
    for i, cfg in cfgs:
        recs = [json.loads((UNITS / f"cfg{i}_v{v}_s{SEED}.json").read_text())
                for v in VAL_SEASONS]
        rows.append({
            "config_idx": i, "config": cfg,
            "mean_ap_q": float(np.mean([r["ap_q"] for r in recs])),
            "mean_zero311_p250_F": float(np.mean([r["zero311_p250_F"] for r in recs])),
            "per_fold_ap_q": [r["ap_q"] for r in recs],
            "per_fold_best_epoch": [r["best_epoch"] for r in recs],
        })
    # pre-registered: mean val AP of q=F*R; tie-break zero-311 p@250 of F; then idx
    rows.sort(key=lambda r: (-r["mean_ap_q"], -r["mean_zero311_p250_F"],
                             r["config_idx"]))
    win = rows[0]
    win["boundary"] = boundary_status(win["config"], NET_DIMS)
    win["n_configs_evaluated"] = len(rows)
    win["runner_up"] = {k_: rows[1][k_] for k_ in
                        ("config_idx", "mean_ap_q", "mean_zero311_p250_F")}
    win["selection_rule"] = ("mean val AP of F*R vs Y_obs; tie-break mean "
                             "zero-311-stratum p@250 of F; then config_idx")
    atomic_write(out, json.dumps(win, indent=2))
    return win


def spread_units(win):
    return [(win["config_idx"], win["config"], str(v), s)
            for s in SPREAD_SEEDS if s != SEED for v in VAL_SEASONS]


def stage_spread_report(win):
    out = WORK / "seed_spread.json"
    if out.exists():
        return
    per_seed = {}
    for s in SPREAD_SEEDS:
        recs = [json.loads((UNITS / f"cfg{win['config_idx']}_v{v}_s{s}.json")
                           .read_text()) for v in VAL_SEASONS]
        per_seed[str(s)] = {
            "mean_ap_q": float(np.mean([r["ap_q"] for r in recs])),
            "mean_p250_q": float(np.mean([r["metrics_q"]["p@250"] for r in recs])),
            "mean_p250_F": float(np.mean([r["metrics_F"]["p@250"] for r in recs])),
            "mean_zero311_p250_F": float(np.mean([r["zero311_p250_F"] for r in recs])),
            "per_fold_ap_q": [r["ap_q"] for r in recs],
        }
    aps = [per_seed[str(s)]["mean_ap_q"] for s in SPREAD_SEEDS]
    z = [per_seed[str(s)]["mean_zero311_p250_F"] for s in SPREAD_SEEDS]
    atomic_write(out, json.dumps({
        "note": "VALIDATION-based spread (spec §8, Rule 10); winning hyperparams "
                "fixed; seed 42 rows are the search units themselves "
                "(bit-identical rerun; reuse disclosed).",
        "per_seed": per_seed,
        "spread_mean_ap_q": {"min": min(aps), "max": max(aps),
                             "std": float(np.std(aps)), "range": max(aps) - min(aps)},
        "spread_zero311_p250_F": {"min": min(z), "max": max(z),
                                  "std": float(np.std(z)), "range": max(z) - min(z)},
    }, indent=2))


def fixed_batch_rows():
    """A deterministic fixed batch (docstring header): first 4096 all-dev rows
    UNION first 4096 NLL-eligible rows, frame order, dup keys dropped."""
    aux = np.load(WORK / "aux.npz")
    el_idx = np.where(aux["eligible"])[0]
    idx = list(range(4096)) + [int(i) for i in el_idx[:4096]]
    seen, keep = set(), []
    for i in idx:
        if i not in seen:
            seen.add(i)
            keep.append(i)
    return np.array(keep, dtype=np.int64)


def make_capture(cfg, rows):
    """Returns capture(model, tag): float64 per-term + per-row persistence on
    the fixed batch, computed from a double-cast copy of the float32 weights."""
    import torch
    FIXED.mkdir(parents=True, exist_ok=True)
    t = fold_tensors(FOLD_ALL)["train"]
    pos = {int(r): j for j, r in enumerate(t["rows"])}
    sel = np.array([pos[int(r)] for r in rows])
    x = t["x"][sel].double()
    y = t["y"][sel].double()
    elig = t["elig"][sel]
    u, k = cap_uk({"u_raw": t["u_raw"][sel], "k_raw": t["k_raw"][sel]},
                  cfg["ustar"])
    u, k = u.double(), k.double()
    meta = json.loads((WORK / "design_meta.json").read_text())
    pbar = meta["pbar"][f"{FOLD_ALL}|{cfg['ustar']}"]

    def capture(model, tag):
        path = FIXED / f"{tag}.json"
        if path.exists():
            return
        md = copy.deepcopy(model).double().eval()
        with torch.no_grad():
            o = loss_terms(md, x, y, u, k, elig, cfg, pbar, train=False,
                           decompose=True)
            F, p, R, q = o["F"], o["p"], o["R"], o["q"]
            xp = x.clone()
            for j in PERT_IDX:
                xp[:, j] = xp[:, j] + DELTA_STD
            Fp, _ = md(xp)
            clamp_counts = {
                "p_low": int((p < CLAMP_EPS).sum()), "p_high": int((p > 1 - CLAMP_EPS).sum()),
                "q_low": int((F * R < CLAMP_EPS).sum()),
                "q_high": int((F * R > 1 - CLAMP_EPS).sum()),
                "trunc": int(((1 - (1 - p.clamp(CLAMP_EPS, 1 - CLAMP_EPS))
                               ** u) < TRUNC_EPS)[elig].sum()),
            }
        terms = {k_: float(v_) for k_, v_ in o.items()
                 if k_ not in ("F", "p", "R", "q") and not hasattr(v_, "shape")}
        terms.update({k_: float(v_) for k_, v_ in o.items()
                      if hasattr(v_, "shape") and v_.dim() == 0})
        payload = {
            "tag": tag, "n_rows": int(len(rows)), "n_eligible": int(elig.sum()),
            "constants": {"lam": cfg["lam"], "ustar": cfg["ustar"],
                          "mu1": cfg["mu1"], "mu2": cfg["mu2"], "pbar": pbar,
                          "logit_pbar": math.log(pbar / (1 - pbar)),
                          "delta_std": DELTA_STD, "clamp_eps": CLAMP_EPS,
                          "trunc_eps": TRUNC_EPS,
                          "perturb_cols": PERTURB_COLS},
            "terms": {k_: repr(v_) for k_, v_ in terms.items()},
            "terms_float": terms,
            "loss_identity": "total = bce + lam*nll_mean + mu1*omega1_raw + mu2*omega2_raw",
            "clamp_binding_counts": clamp_counts,
            "precision": "float64 eval-mode recomputation from float32 weights",
        }
        atomic_write(path, json.dumps(payload, indent=2))
        np.savez_compressed(FIXED / f"{tag}_rows.npz",
                            F=F.numpy(), p=p.numpy(), R=R.numpy(), q=q.numpy(),
                            F_pert=Fp.numpy())
        print(f"  fixed-batch capture: {tag} (total={terms['total']!r})")
    return capture


def stage_fixed_batch_static(cfg):
    """Persist the model-independent fixed-batch ingredients once."""
    path = FIXED / "batch_static.npz"
    if path.exists():
        return
    FIXED.mkdir(parents=True, exist_ok=True)
    rows = fixed_batch_rows()
    aux = np.load(WORK / "aux.npz")
    t = fold_tensors(FOLD_ALL)["train"]
    pos = {int(r): j for j, r in enumerate(t["rows"])}
    sel = np.array([pos[int(r)] for r in rows])
    u = np.minimum(aux["u_raw"][rows], float(cfg["ustar"]))
    np.savez_compressed(
        path, row_idx=rows, bbl=aux["bbl"][rows], season=aux["season"][rows],
        y=aux["y"][rows], u_raw=aux["u_raw"][rows], k_raw=aux["k_raw"][rows],
        u_capped=u, k_capped=np.minimum(aux["k_raw"][rows], u),
        eligible=aux["eligible"][rows],
        x_std=t["x"][sel].numpy().astype(np.float64))
    meta = json.loads((WORK / "design_meta.json").read_text())
    atomic_write(FIXED / "batch_construction.md", (
        "# Fixed batch — construction (deterministic)\n\n"
        "Universe: the all-dev refit training frame, frame order = sorted "
        "(season, bbl_n).\nRows: the first 4096 rows UNION the first 4096 "
        "NLL-eligible rows (label_c==1 AND k_raw>=1), order-preserving, "
        f"duplicate keys dropped. Final size: {len(rows)}.\n"
        f"Eligible rows in batch: {int(aux['eligible'][rows].sum())}.\n"
        "batch_static.npz: row_idx (position in the sorted dev frame), bbl, "
        "season, y=label_c, u_raw (A2), k_raw (in-season 311-union events), "
        "u_capped=min(u_raw,u*), k_capped=min(k_raw,u_capped), eligible, and "
        "x_std = the standardized float64 design matrix under the all-dev "
        "scaler (columns per design_meta.json design_cols; standardized block "
        "= std_cols; NULLs are 0 after standardization).\n"
        f"Winner u* used here: {cfg['ustar']}. Perturbed column(s) "
        f"{PERTURB_COLS} at design index {meta['perturb_design_idx']}; "
        f"delta=+{DELTA_STD} standardized.\n"
        "Per-tag files t0_init/t1_epoch1/tE_final: terms (per-term float64 "
        "values incl. NLL decomposition) + <tag>_rows.npz per-row F, p, R, "
        "q=F*R, F_pert (float64).\n"))


def stage_refit(win, deadline) -> str:
    """Seed-42 all-dev refit at E* epochs with fixed-batch captures.
    Every post-training step is idempotent, so a kill between unit completion
    and artifact finalization is recovered on rerun."""
    uid = f"cfg{win['config_idx']}_v{FOLD_ALL}_s{SEED}"
    e_star = int(round(np.mean(win["per_fold_best_epoch"])))
    atomic_write(WORK / "refit_meta.json", json.dumps(
        {"e_star": e_star, "rule": "round(mean per-fold best_epoch of winner)",
         "per_fold_best_epoch": win["per_fold_best_epoch"]}))
    stage_fixed_batch_static(win["config"])
    cap = make_capture(win["config"], fixed_batch_rows())
    if not (UNITS / f"{uid}.json").exists():
        status = train_unit(win["config_idx"], win["config"], FOLD_ALL, SEED,
                            deadline, epochs_override=e_star, capture_fixed=cap)
        if status != "done":
            return status
    if not (FIXED / "tE_final.json").exists() or \
            not (MODELS / "s3b_primary_seed42.pt").exists():
        import torch
        model = build_model(win["config"],
                            fold_tensors(FOLD_ALL)["train"]["x"].shape[1], SEED, 0)
        model.load_state_dict(torch.load(UNITS / f"{uid}.model.pt",
                                         weights_only=False)["state_dict"])
        cap(model, "tE_final")
        _finalize_artifact(win, e_star)
    return "done"


def _finalize_artifact(win, e_star):
    import torch
    out = MODELS / "s3b_primary_seed42.pt"
    if out.exists():
        return
    MODELS.mkdir(parents=True, exist_ok=True)
    uid = f"cfg{win['config_idx']}_v{FOLD_ALL}_s{SEED}"
    state = torch.load(UNITS / f"{uid}.model.pt", weights_only=False)["state_dict"]
    meta = json.loads((WORK / "design_meta.json").read_text())
    scal = json.loads((WORK / "scalers.json").read_text())[FOLD_ALL]

    # full-dev scores persisted for the reload check + later G3 tooling
    t = fold_tensors(FOLD_ALL)["train"]
    model = build_model(win["config"], t["x"].shape[1], SEED, 0)
    model.load_state_dict(state)
    _, F_all, p_all = eval_pass(model, t, win["config"],
                                meta["pbar"][f"{FOLD_ALL}|{win['config']['ustar']}"])
    aux = np.load(WORK / "aux.npz")
    np.savez_compressed(WORK / "final_scores.npz", bbl=aux["bbl"],
                        season=aux["season"], F=F_all, p=p_all)

    cfg_payload = {
        "architecture": "spec §3 two-head net: shared MLP encoder (Linear-"
                        "LayerNorm-ReLU-Dropout blocks), head F sigmoid, head p "
                        "sigmoid, R = 1-(1-p)^min(u,u*)",
        "config": win["config"], "config_idx": win["config_idx"],
        "seed": SEED, "e_star_epochs": e_star,
        "refit": "all dev seasons 2019-2025, cosine LR over 200 epochs stopped "
                 "at e_star, no ES (A9)",
        "selection": win["selection_rule"],
        "loss": "L = BCE(Y_obs, F*R) + lam*NLL_zero-trunc-binomial(k|u,p) "
                "+ mu1*Omega1 + mu2*Omega2 (resolved axes A1-A8 in "
                "src/s3b_primary.py header)",
        "pbar_all_dev": meta["pbar"][f"{FOLD_ALL}|{win['config']['ustar']}"],
        "design": {"n_cols": meta["n_design_cols"],
                   "meta": "outputs/checkpoints/s3b_work/design_meta.json"},
        "feature_recipe_hashes": meta["frame_hashes"],
        "library_versions": _versions(),
        "train_threads": TRAIN_THREADS,
    }
    atomic_save_torch({"state_dict": state, "config": cfg_payload,
                       "scaler_all": scal,
                       "design_cols": meta["design_cols"],
                       "std_cols": meta["std_cols"]}, out)
    atomic_write(MODELS / "s3b_frozen_config.json", json.dumps(cfg_payload, indent=2))
    print(f"  freeze-candidate artifact written: {out.name} (E*={e_star})")


def _versions():
    import sklearn
    import torch
    return {"torch": torch.__version__, "numpy": np.__version__,
            "pandas": pd.__version__, "sklearn": sklearn.__version__,
            "python": sys.version.split()[0]}


def stage_reload_verify():
    """Fresh-process artifact reload; bit-exact reproduction of the persisted
    fixed-batch tE terms and full-dev scores (run via --verify-only subprocess)."""
    out = WORK / "reload_verification.json"
    if out.exists():
        return
    import torch
    torch.set_num_threads(TRAIN_THREADS)
    bundle = torch.load(MODELS / "s3b_primary_seed42.pt", weights_only=False)
    win = json.loads((WORK / "winner.json").read_text())
    t = fold_tensors(FOLD_ALL)["train"]
    model = build_model(win["config"], t["x"].shape[1], SEED, 0)
    model.load_state_dict(bundle["state_dict"])
    meta = json.loads((WORK / "design_meta.json").read_text())
    pbar = meta["pbar"][f"{FOLD_ALL}|{win['config']['ustar']}"]
    _, F_all, p_all = eval_pass(model, t, win["config"], pbar)
    ref = np.load(WORK / "final_scores.npz")
    dF = float(np.abs(F_all - ref["F"]).max())
    dp = float(np.abs(p_all - ref["p"]).max())

    cap = make_capture(win["config"], fixed_batch_rows())
    # recompute tE into a scratch tag, then compare
    scratch = FIXED / "tE_reload.json"
    scratch.unlink(missing_ok=True)
    cap(model, "tE_reload")
    a = json.loads((FIXED / "tE_final.json").read_text())["terms_float"]
    b = json.loads(scratch.read_text())["terms_float"]
    diffs = {k_: abs(a[k_] - b[k_]) for k_ in a}
    payload = {
        "artifact": "outputs/models/s3b_primary_seed42.pt",
        "full_dev_scores_max_abs_diff": {"F": dF, "p": dp},
        "fixed_batch_tE_term_max_abs_diff": max(diffs.values()),
        "per_term_abs_diff": diffs,
        "bit_exact": bool(dF == 0.0 and dp == 0.0 and max(diffs.values()) == 0.0),
        "environment": _versions(), "train_threads": TRAIN_THREADS,
    }
    atomic_write(out, json.dumps(payload, indent=2))
    print(f"  reload verification: bit_exact={payload['bit_exact']} "
          f"(dF={dF}, dp={dp})")


def stage_report():
    out = CKPT / "s3b_stats.json"
    tbl = WORK / "s3b_table.md"
    if out.exists() and tbl.exists():
        return
    win = json.loads((WORK / "winner.json").read_text())
    spread = json.loads((WORK / "seed_spread.json").read_text())
    meta = json.loads((WORK / "design_meta.json").read_text())
    reload_v = json.loads((WORK / "reload_verification.json").read_text())
    refit_meta = json.loads((WORK / "refit_meta.json").read_text())
    fixed = {tag: json.loads((FIXED / f"{tag}.json").read_text())
             for tag in ("t0_init", "t1_epoch1", "tE_final")}

    win_recs = {str(v): json.loads(
        (UNITS / f"cfg{win['config_idx']}_v{v}_s{SEED}.json").read_text())
        for v in VAL_SEASONS}

    def mean_of(path_q, key):
        vals = [win_recs[str(v)][path_q][key] for v in VAL_SEASONS]
        vals = [x for x in vals if x is not None]
        return float(np.mean(vals))

    summary = {
        "mean_ap_q": win["mean_ap_q"],
        "mean_p@250_q": mean_of("metrics_q", "p@250"),
        "mean_p@250_F": mean_of("metrics_F", "p@250"),
        "mean_zero311_p@250_F": win["mean_zero311_p250_F"],
        "mean_zero311_p@250_q": float(np.mean(
            [win_recs[str(v)]["metrics_q"]["zero311"]["p@250"] for v in VAL_SEASONS])),
        "mean_any311_p@250_F": float(np.mean(
            [win_recs[str(v)]["metrics_F"]["any311"]["p@250"] for v in VAL_SEASONS])),
    }
    guards = [json.loads(l) for l in
              (WORK / "guards.jsonl").read_text().splitlines() if l.strip()]
    payload = {
        "seed": SEED, "dev_seasons": DEV_SEASONS, "val_seasons": VAL_SEASONS,
        "grid": {"dims": {k_: v_ for k_, v_ in NET_DIMS},
                 "cartesian": space_size(NET_DIMS), "sampled": N_SAMPLED},
        "library_versions": _versions(),
        "design": {k_: meta[k_] for k_ in
                   ("n_rows", "n_design_cols", "n_eligible", "n_labelc1",
                    "u_source_counts", "k_exceeds_u_by_ustar", "frame_hashes")},
        "summary_means_winner": summary,
        "per_season_winner": {str(v): {"q": win_recs[str(v)]["metrics_q"],
                                       "F": win_recs[str(v)]["metrics_F"],
                                       "best_epoch": win_recs[str(v)]["best_epoch"],
                                       "val_terms_at_best":
                                           win_recs[str(v)]["val_terms_at_best"]}
                              for v in VAL_SEASONS},
        "winner": {k_: win[k_] for k_ in ("config_idx", "config", "boundary",
                                          "mean_ap_q", "mean_zero311_p250_F",
                                          "per_fold_ap_q", "per_fold_best_epoch",
                                          "runner_up", "selection_rule",
                                          "n_configs_evaluated")},
        "seed_spread_validation": spread,
        "refit": refit_meta,
        "fixed_batch": {tag: {"terms_float": fixed[tag]["terms_float"],
                              "n_rows": fixed[tag]["n_rows"],
                              "n_eligible": fixed[tag]["n_eligible"],
                              "clamp_binding_counts": fixed[tag]["clamp_binding_counts"]}
                        for tag in fixed},
        "reload_verification": reload_v,
        "guard_assertions": {"n_recorded_passes": len(guards),
                             "distinct_sites": sorted({g["where"] for g in guards}),
                             "max_season_ever_touched": max(
                                 max(g["touched"]) for g in guards),
                             "bright_line": "no season >= 2026 in any frame, "
                                            "filter, fold, or artifact"},
    }
    atomic_write(out, json.dumps(payload, indent=2))

    lines = ["# S3b results table (machine-generated — no hand transcription)",
             "",
             "| Metric (5-fold val means, winner cfg %d, seed 42) | value |"
             % win["config_idx"],
             "|---|---|"]
    for k_, v_ in summary.items():
        lines.append(f"| {k_} | {v_:.4f} |")
    lines.append("")
    lines.append("| Seed | mean AP (F·R) | mean p@250 (F) | mean zero-311 p@250 (F) |")
    lines.append("|---|---|---|---|")
    for s in SPREAD_SEEDS:
        ps = spread["per_seed"][str(s)]
        lines.append(f"| {s} | {ps['mean_ap_q']:.4f} | {ps['mean_p250_F']:.4f} | "
                     f"{ps['mean_zero311_p250_F']:.4f} |")
    lines.append("")
    lines.append(f"Per-fold winner AP (F·R), v=2021..2025: " + " / ".join(
        f"{a:.4f}" for a in win["per_fold_ap_q"]))
    atomic_write(tbl, "\n".join(lines) + "\n")
    print("  wrote s3b_stats.json + s3b_table.md")
    for k_, v_ in summary.items():
        print(f"  {k_}: {v_:.4f}")


# ------------------------- main -------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=9.0)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--verify-only", action="store_true")
    args = ap.parse_args()
    deadline = time.time() + args.minutes * 60
    WORK.mkdir(parents=True, exist_ok=True)

    import torch
    torch.set_num_threads(TRAIN_THREADS)

    if args.verify_only:
        stage_reload_verify()
        return 0

    print(f"=== S3b primary (spec §3) — seed {SEED} — budget {args.minutes} min "
          f"— workers {args.workers} ===")
    prep_design()

    if not run_pool(search_units(), deadline, args.workers):
        n_done = sum((UNITS / f"cfg{i}_v{fk}_s{s}.json").exists()
                     for (i, c, fk, s) in search_units())
        print(f"PARTIAL: search {n_done}/{len(search_units())} units — rerun to resume")
        return 0
    win = stage_winner()

    if not run_pool(spread_units(win), deadline, args.workers):
        print("PARTIAL: seed-spread units pending — rerun to resume")
        return 0
    stage_spread_report(win)

    if stage_refit(win, deadline) != "done":
        print("PARTIAL: refit in progress — rerun to resume")
        return 0

    if not (WORK / "reload_verification.json").exists():
        r = subprocess.run([sys.executable, __file__, "--verify-only"],
                           cwd=REPO, capture_output=True, text=True)
        print(r.stdout, end="")
        if r.returncode != 0:
            print(r.stderr)
            raise AssertionError("reload verification subprocess failed (Rule 9)")

    stage_report()
    print("ALL STAGES COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
