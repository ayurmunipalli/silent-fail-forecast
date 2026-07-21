"""RP1 — R-PILOT re-selection/re-training at pilot cutoff Oct 1, 2025
(model_spec.md Amendment 5(i); RP0 sign-off assertions D1-D8 BINDING).

*** RETROSPECTIVE AND NON-BLIND (Amendment 5(iii)) ***
The project's conception and the frozen spec postdate season 2025-26; nothing
produced here has prospective standing, carries any weight at G3, or modifies
anything in the frozen G3 pre-registration.

Everything MECHANICAL, nothing re-interpreted: the SAME locked grid
(hyperparam_grid.md, Amendment-2 pre-registration), the same n=60 seed-42
samples, the same pre-registered selection rules, the same Amendment-4(i)
frozen NLL-interpretation axes A1-A10 (src/s3b_primary.py header, binding) —
re-executed over pilot folds v in {2021, 2022, 2023, 2024} only.

MACHINERY REUSE (mandate: do not re-derive audited machinery):
  imported from the S3a-audited src/s3a_baselines.py:
    season_of, norm_bbl, precision_at_k/stable_rank_order/eval_ranking/
    eval_with_strata (metrics), space_size/decode/sampled_configs (grid),
    lgb_params, spw_value, boundary_status, feature_cols, fit_predict_b1,
    PROP_DIMS, RISK_DIMS, KEYS
  imported from the S3b-audited src/s3b_primary.py:
    NET_DIMS, build_model, loss_terms, eval_pass, cap_uk, stable_seed,
    atomic_write, atomic_save_torch, sha256_file, SHA_MAIN, SHA_B3, and the
    fixed loss/optimizer constants (BATCH, MAX_EPOCHS, PATIENCE, WEIGHT_DECAY,
    TRAIN_THREADS, CLAMP_EPS, OMEGA2_SUB, U_FALLBACK, DELTA_STD).
  MIRRORED here (orchestration that hard-codes build-phase season sets/paths
  and therefore cannot be imported): dev-frame load + design-matrix prep
  (s3b prep_design, axis A5 verbatim), fold-tensor build, the epoch-resumable
  training loop (s3b train_unit, A9/A10 verbatim: per-epoch seeds
  SeedSequence([seed, fold_code, epoch]), cosine LR over 200, ES patience 20
  on fold-v total val loss), worker pool, B0/B1/B2/B3 stages and the B4/B5
  search/refit stages (s3a_baselines.py / s3a_b5.py) — logic line-mirrored,
  only PILOT season constants, PILOT work dir, and rpilot_* artifact names
  differ. Every mirror is labeled "MIRROR:" with its source lines.

RP0 BINDING ASSERTIONS carried (r-audit.md RP0 section):
  D1  frame-hash pin: sha256(features_main)==477d3079..., (features_b3)==
      09f8e94d... asserted at prep; no frame regeneration, no new pull.
  D2  dev max-season guard: dev.season.max()==2024 AND 2025 not in dev —
      season-2025 rows never enter any RP1 dev structure. (The parquet read
      necessarily materializes the frame's 2025 rows for the D1/D4 whole-file
      hash + max-season assertions; they are dropped on the next statement and
      never enter any fold, scaler, target, mask, design row, or artifact.)
  D3  folds exactly v in {2021,2022,2023,2024}, forward-chaining train
      subset-of seasons < v (dev floor 2019); never random K-fold.
  D4  bright-line hard stop UNCHANGED: guard fires on any season >= 2026;
      frame load asserts max(season)==2025. Guard events -> rp1_work/guards.jsonl.
  D5  locked selection unchanged: same 2,592-config grid n=60 seed-42 sample
      (identical decode/sample machinery, therefore identical 60 config
      indices as build S3b); joint rule = mean val AP of q=F*R vs Y_obs,
      tie-break mean zero-311-stratum p@250 of the F ranking, then config
      index; refit-E* = round(mean per-fold best epoch); B4/B5 per their
      pre-registered S3a rules; B0-B2 recomputed from frozen definitions.
  D6  seed 42 everywhere; 5-seed spread (42-46) VALIDATION-based over the
      pilot folds <= 2024 only.
  D7  frozen/committed artifacts READ-ONLY: pilot artifacts live in the
      distinct rpilot_* namespace; a preflight sha256 snapshot of every
      pre-existing outputs/models/ + imports/ file is re-asserted unchanged
      at report time.
  D8  the literal label "RETROSPECTIVE AND NON-BLIND" is stamped in every
      pilot artifact, per-unit checkpoint record, config, table, and stats file.

PILOT-SPECIFIC MECHANICAL RESOLUTIONS (analogs, not reinterpretations;
disclosed in outputs/checkpoints/rp1_pilot.md):
  P1  load-site guard allowed-set = the frame universe {2017..2025} (the frame
      contains 2025 rows by construction and D4 requires asserting so); every
      downstream guard's allowed-set is the pilot dev universe {2019..2024}.
  P2  design-matrix column typing (binary/missingness, axis A5) is re-derived
      on the PILOT dev universe (<=2024) — the mechanical re-execution of A5
      at the pilot cutoff; realized counts reported in rp1_stats.json.
  P3  B2's lookback cap = max(pilot v) - 1 = 2023 (build-phase analog: 2024).
  P4  E* and refit: all-pilot-dev (2019-2024) refit at E* = round(mean of the
      4 per-fold best epochs), cosine schedule still over 200 (A9 analog).
  P5  pbar / scalers / zero-311 masks / GBM targets: identical construction,
      pilot folds and pilot dev universe only.
  P6  no fixed-batch blind-derivation kit at RP1 (none mandated; R-AUDIT
      re-audits this script per RP0(d)).
  P7  B3 is NOT retrained and NOT selected: the frozen booster (343-tree
      assertion) is scored on pilot validation folds <=2024 only — no
      season-2025 row is ever scored in RP1 (B3's 2025 scoring is RP2's
      single shot). v in {2021,2022,2023} remain B3's WFF TRAINING seasons
      (in-sample caveat travels with the number).

Idempotent + resumable: per-unit json checkpoints under
outputs/checkpoints/rp1_work/ (net units resume at EPOCH granularity, the S3b
pattern); a rerun after completion recomputes nothing and prints
ALL STAGES COMPLETE. torch threads fixed at 3. No network. Seed 42.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

# torch MUST be imported before lightgbm in THIS module (operational fix,
# disclosed in the checkpoint): both bundle an OpenMP runtime on macOS, and a
# spawn worker child re-executing this module as __mp_main__ with
# lightgbm-first order segfaults (SIGSEGV) at the first heavy torch op
# (reproduced + isolated 2026-07-21; torch-first order verified clean).
# Import order does not enter numerics: lightgbm runs deterministic=True /
# force_row_wise / fixed seed, torch thread count is pinned separately.
# Build-phase s3b_primary.py never faced this (it imports no lightgbm).
import torch  # noqa: E402,F401  (order-critical; see note above)

import lightgbm as lgb  # noqa: E402

import s3b_primary as s3b  # noqa: E402  (audited module; constants + machinery)
from s3a_baselines import (  # noqa: E402  (audited machinery, imported not re-derived)
    KEYS, PROP_DIMS, RISK_DIMS, boundary_status, eval_with_strata, feature_cols,
    fit_predict_b1, lgb_params, norm_bbl, sampled_configs, season_of, spw_value,
)
from s3b_primary import (  # noqa: E402
    BATCH, CLAMP_EPS, MAX_EPOCHS, NET_DIMS, OMEGA2_SUB, PATIENCE, SHA_B3,
    SHA_MAIN, TRAIN_THREADS, U_FALLBACK, WEIGHT_DECAY, atomic_save_torch,
    atomic_write, build_model, cap_uk, eval_pass, sha256_file, stable_seed,
)

PILOT_LABEL = "RETROSPECTIVE AND NON-BLIND"          # D8, Amendment 5(iii)

REPO = Path(__file__).resolve().parent.parent
PROC = REPO / "data" / "processed"
RAW = REPO / "data" / "raw"
CKPT = REPO / "outputs" / "checkpoints"
WORK = CKPT / "rp1_work"                             # distinct pilot namespace
UNITS = WORK / "units"
MODELS = REPO / "outputs" / "models"
IMPORTS = REPO / "imports"

SEED = 42
SPREAD_SEEDS = [42, 43, 44, 45, 46]                  # D6
LAG_SEASONS = [2017, 2018]
PILOT_DEV = list(range(2019, 2025))                  # 2019..2024 (D2/D3)
PILOT_VAL = [2021, 2022, 2023, 2024]                 # D3
FRAME_SEASONS = LAG_SEASONS + list(range(2019, 2026))  # load-site only (P1)
FORBIDDEN_FROM = 2026                                # D4 bright line
FOLD_ALL = "all"                                     # refit universe: all pilot dev

# rpilot_* artifact names (D7 distinct namespace)
ART_B4_PROP = MODELS / "rpilot_b4_propensity_lgbm.txt"
ART_B4_RISK = MODELS / "rpilot_b4_risk_lgbm.txt"
ART_B4_CFG = MODELS / "rpilot_b4_config.json"
ART_B5 = MODELS / "rpilot_b5_lgbm.txt"
ART_B5_CFG = MODELS / "rpilot_b5_config.json"
ART_JOINT = MODELS / "rpilot_joint_seed42.pt"
ART_JOINT_CFG = MODELS / "rpilot_joint_config.json"
PILOT_ARTIFACTS = {ART_B4_PROP, ART_B4_RISK, ART_B4_CFG, ART_B5, ART_B5_CFG,
                   ART_JOINT, ART_JOINT_CFG}


def guard(seasons, where: str, allowed):
    """MIRROR: s3a_baselines.assert_no_test_contact L111-126 / s3b L238-252
    (D4: the identical hard-stop pattern; only the guards file differs)."""
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


# ------------------------- D7 preflight -------------------------

def stage_preflight():
    """sha256 snapshot of every PRE-EXISTING outputs/models/ + imports/ file;
    re-asserted unchanged at report (D7)."""
    out = WORK / "models_preflight.json"
    if out.exists():
        return
    WORK.mkdir(parents=True, exist_ok=True)
    snap = {}
    for d in (MODELS, IMPORTS):
        for p in sorted(d.iterdir()):
            if p.is_file() and p not in PILOT_ARTIFACTS:
                snap[str(p.relative_to(REPO))] = sha256_file(p)
    atomic_write(out, json.dumps({"label": PILOT_LABEL, "sha256": snap}, indent=2))
    print(f"  preflight: {len(snap)} pre-existing artifacts hashed (D7)")


def assert_preflight_unchanged() -> dict:
    snap = json.loads((WORK / "models_preflight.json").read_text())["sha256"]
    for rel, h in snap.items():
        now = sha256_file(REPO / rel)
        assert now == h, f"D7 VIOLATION: {rel} changed ({h} -> {now}) — HARD STOP"
    return {"n_files": len(snap), "all_unchanged": True}


# ------------------------- pilot dev frame -------------------------

def load_pilot_dev() -> pd.DataFrame:
    """MIRROR: s3a_baselines.load_dev_frame L171-181, pilot seasons (D1/D2/D4/P1)."""
    fm = PROC / "features_main.parquet"
    assert sha256_file(fm) == SHA_MAIN, "features_main.parquet hash drift (D1/Rule 9)"
    f = pd.read_parquet(fm)
    assert int(f["season"].max()) == 2025, "spine must end at start-year 2025 (D4)"
    guard(f["season"], "rp1 features_main load (full frame; 2025 dropped next stmt)",
          FRAME_SEASONS)
    dev = f[f["season"].isin(PILOT_DEV)].copy()
    del f
    assert int(dev["season"].max()) == 2024, "D2: pilot dev max season must be 2024"
    assert 2025 not in set(int(s) for s in dev["season"].unique()), \
        "D2: season 2025 must never enter the RP1 dev universe"
    guard(dev["season"], "rp1 pilot dev universe", PILOT_DEV)
    dev = dev.sort_values(["season", "bbl_n"], kind="mergesort").reset_index(drop=True)
    rng = np.random.default_rng(SEED)
    dev["_tiekey"] = rng.permutation(len(dev))
    return dev


def prep_311_tables():
    """MIRROR: s3a_baselines.prep_311_tables L184-206, pilot dev seasons (P5)."""
    out_first = WORK / "first311.parquet"
    out_cnt = WORK / "insea311.parquet"
    if out_first.exists() and out_cnt.exists():
        return
    c = pd.read_parquet(RAW / "c311_heat_complaints.parquet",
                        columns=["bbl", "created_date"])
    c["bbl_n"] = norm_bbl(c["bbl"])
    c["created_date"] = pd.to_datetime(c["created_date"], errors="coerce")
    c = c[c["bbl_n"].notna() & c["created_date"].notna()]
    assert len(c) > 0, "empty 311 union pull (Rule 1/9)"
    c.groupby("bbl_n")["created_date"].min().rename("first311").reset_index() \
        .to_parquet(out_first, index=False)
    c["season"] = c["created_date"].map(season_of)
    ins = c[c["season"].notna()].copy()
    ins["season"] = ins["season"].astype(int)
    ins = ins[ins["season"].isin(PILOT_DEV)]
    guard(ins["season"], "rp1 in-season 311 counts (NLL/B4 targets)", PILOT_DEV)
    ins.groupby(["bbl_n", "season"]).size().rename("n311").reset_index() \
        .to_parquet(out_cnt, index=False)


def zero311_mask(dev: pd.DataFrame, v: int) -> np.ndarray:
    """MIRROR: s3a_baselines.zero311_mask L209-217 (spec §6)."""
    cutoff = pd.Timestamp(v, 10, 1)
    assert cutoff <= pd.Timestamp(v, 10, 1), "window_hi must be <= cutoff"
    first = pd.read_parquet(WORK / "first311.parquet")
    m = dev.loc[dev["season"] == v, "bbl_n"].map(
        first.set_index("bbl_n")["first311"])
    return ~(m.notna() & (m < cutoff)).to_numpy()


# ------------------------- prep: design + loss ingredients -------------------------

def prep_design():
    """MIRROR: s3b_primary.prep_design L325-467 — axis A5 verbatim, pilot dev
    universe (P2), pilot folds + FOLD_ALL=all-pilot-dev scalers/pbar (P4/P5)."""
    meta_path = WORK / "design_meta.json"
    if meta_path.exists():
        return
    WORK.mkdir(parents=True, exist_ok=True)
    assert sha256_file(PROC / "features_b3.parquet") == SHA_B3, \
        "features_b3.parquet hash drift (D1/Rule 9)"
    dev = load_pilot_dev()
    tiekey = dev["_tiekey"].to_numpy()
    prep_311_tables()

    cnt = pd.read_parquet(WORK / "insea311.parquet").set_index(
        ["bbl_n", "season"])["n311"]
    k_raw = pd.MultiIndex.from_frame(dev[["bbl_n", "season"]]).map(cnt)
    k_raw = pd.Series(k_raw, dtype="float64").fillna(0.0).to_numpy()
    ut = dev["unitstotal"].astype(float).to_numpy()
    ur = dev["unitsres"].astype(float).to_numpy()
    u_raw = np.where(np.isfinite(ut) & (ut >= 1), ut,
                     np.where(np.isfinite(ur) & (ur >= 1), ur, U_FALLBACK))
    u_src = np.where(np.isfinite(ut) & (ut >= 1), 0,
                     np.where(np.isfinite(ur) & (ur >= 1), 1, 2))
    y = dev["label_c"].astype(int).to_numpy()
    eligible = (y == 1) & (k_raw >= 1)          # A1 eligibility, unchanged

    zmasks = {str(v): zero311_mask(dev, v) for v in PILOT_VAL}

    # ---- design matrix (A5 verbatim; typing on the PILOT dev universe, P2)
    feat_cols_ = [c_ for c_ in dev.columns if c_ not in KEYS and c_ != "_tiekey"]
    cat_cols = [c_ for c_ in feat_cols_ if str(dev[c_].dtype) == "category"]
    num_cols = [c_ for c_ in feat_cols_ if c_ not in cat_cols]
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

    # ---- per-fold nan-aware scalers + pbar (A3), pilot folds only
    n_std = len(std_cols)
    season_arr = dev["season"].to_numpy()
    scalers, pbar = {}, {}
    fold_keys = [str(v) for v in PILOT_VAL] + [FOLD_ALL]
    for fk in fold_keys:
        tr = season_arr < int(fk) if fk != FOLD_ALL else np.ones(len(dev), bool)
        guard(season_arr[tr], f"rp1 scaler/pbar fold={fk}", PILOT_DEV)
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
        "label": PILOT_LABEL,
        "n_rows": int(len(dev)), "n_design_cols": len(design_cols),
        "design_cols": design_cols, "std_cols": std_cols, "bin_cols": bin_cols,
        "isna_cols": isna_cols, "onehot": onehot,
        "perturb_design_idx": [design_cols.index(c_) for c_ in s3b.PERTURB_COLS],
        "frame_hashes": {"features_main.parquet": SHA_MAIN,
                         "features_b3.parquet": SHA_B3},
        "u_source_counts": {"unitstotal": int((u_src == 0).sum()),
                            "unitsres_fallback": int((u_src == 1).sum()),
                            "const3_fallback": int((u_src == 2).sum())},
        "n_eligible": int(eligible.sum()),
        "n_labelc1": int((y == 1).sum()),
        "k_exceeds_u_by_ustar": {str(us): int((eligible & (
            k_raw > np.minimum(u_raw, float(us)))).sum()) for us in NET_DIMS[4][1]},
        "pbar": pbar,
        "pilot": {"dev_seasons": PILOT_DEV, "val_seasons": PILOT_VAL,
                  "cutoff": "2025-10-01"},
    }
    atomic_write(meta_path, json.dumps(meta, indent=2))
    atomic_write(WORK / "scalers.json", json.dumps(scalers))
    np.savez_compressed(
        WORK / "aux.npz", y=y.astype(np.int8), season=season_arr.astype(np.int16),
        bbl=dev["bbl_n"].astype(np.int64).to_numpy(), tiekey=tiekey,
        k_raw=k_raw, u_raw=u_raw, eligible=eligible,
        **{f"zero311_{v}": zmasks[str(v)] for v in PILOT_VAL})
    print(f"  prep: design {X.shape}, eligible NLL rows {int(eligible.sum()):,} "
          f"of {int((y == 1).sum()):,} label_c=1; hashes asserted (D1)")


# ------------------------- fold tensors -------------------------

_FOLD_CACHE: dict = {}


def fold_tensors(fk: str):
    """MIRROR: s3b_primary.fold_tensors L573-610 (pilot folds; sets the
    audited module's PERT_IDX so the imported loss_terms perturbs A4's column)."""
    import torch
    if fk in _FOLD_CACHE:
        return _FOLD_CACHE[fk]
    meta = json.loads((WORK / "design_meta.json").read_text())
    scal = json.loads((WORK / "scalers.json").read_text())[fk]
    aux = np.load(WORK / "aux.npz")
    s3b.PERT_IDX = meta["perturb_design_idx"]
    X = np.load(WORK / "design.npy", mmap_mode="r")
    season = aux["season"]
    n_std = len(meta["std_cols"])

    def block(rows):
        guard(season[rows], f"rp1 fold tensors fk={fk}", PILOT_DEV)
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


# ------------------------- net unit training (resumable) -------------------------

def train_unit(cfg_idx: int, cfg: dict, fk: str, seed: int, deadline: float,
               epochs_override: int | None = None) -> str:
    """MIRROR: s3b_primary.train_unit L657-776 — A9/A10 verbatim (per-epoch
    seeds SeedSequence([seed, fold_code, epoch]); cosine over MAX_EPOCHS; ES
    patience on fold-v total val loss; epoch-level resume). Pilot paths, no
    fixed-batch capture (P6), D8 label in every record."""
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
            sub = torch.arange(min(OMEGA2_SUB, len(idx)))  # A4
            o = s3b.loss_terms(model, tr["x"][idx], tr["y"][idx], u_tr[idx],
                               k_tr[idx], tr["elig"][idx], cfg, pbar,
                               train=True, omega2_idx=sub)
            opt.zero_grad()
            o["total"].backward()
            opt.step()
            tot = float(o["total"].detach())
            if not math.isfinite(tot):
                raise AssertionError(
                    f"NON-FINITE LOSS unit={uid} epoch={ep}: {tot} (Rule 1/9)")

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

    # ---- completion (MIRROR s3b L741-776)
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
            "label": PILOT_LABEL,
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
        rec = {"label": PILOT_LABEL,
               "unit": uid, "config_idx": cfg_idx, "config": cfg, "fold": fk,
               "seed": seed, "epochs_run": ep, "pbar": pbar, "n_train": int(n),
               "n_nll_train": int(tr["elig"].sum().item())}
        atomic_write(done_path, json.dumps(rec))
        atomic_save_torch({"state_dict": model.state_dict()},
                          UNITS / f"{uid}.model.pt")
        res_path.unlink(missing_ok=True)
    return "done"


# ------------------------- worker pool -------------------------
# MIRROR of s3b_primary run_pool/_worker L781-829 with ONE mechanical change
# (disclosed, checkpoint operational note): work is distributed as STATIC
# round-robin shards passed to each spawn child as an argument, instead of a
# multiprocessing.Queue. Rationale: under this harness's background-task
# context the spawn Queue handoff failed silently (children start, the
# queue get raises, s3b's bare `except: return` swallowed it -> 0 units,
# clean exit). Sharding removes the queue/semaphore dependency entirely and
# the bare except with it: child failures now surface as error.json files +
# nonzero exit codes, both hard-checked by the parent (Rule 1/9). The
# per-unit training function is untouched.

def _worker(shard, deadline):
    import torch
    torch.set_num_threads(TRAIN_THREADS)
    for cfg_idx, cfg, fk, seed in shard:
        if time.time() > deadline:
            return
        try:
            train_unit(cfg_idx, cfg, fk, seed, deadline)
        except AssertionError:
            raise
        except Exception as e:  # persist the exact failure state (Rule 1)
            atomic_write(UNITS / f"cfg{cfg_idx}_v{fk}_s{seed}.error.json",
                         json.dumps({"error": repr(e)}))
            raise


def run_pool(units, deadline, n_workers) -> bool:
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
        shards = [pending[w::n_workers] for w in range(n_workers)]
        procs = [ctx.Process(target=_worker, args=(sh, deadline))
                 for sh in shards if sh]
        for p_ in procs:
            p_.start()
        for p_ in procs:
            p_.join()
        errs = list(UNITS.glob("*.error.json"))
        if errs:
            raise AssertionError(f"worker unit errors (Rule 9): "
                                 f"{[e.name for e in errs]}")
        bad = [p_.exitcode for p_ in procs if p_.exitcode != 0]
        if bad:
            raise AssertionError(
                f"worker processes exited nonzero (Rule 9): {bad}")
    return all((UNITS / f"cfg{i}_v{fk}_s{s}.json").exists()
               for (i, c, fk, s) in pending)


# ------------------------- B0/B1/B2 (frozen definitions) -------------------------

def build_trailing3_counts() -> pd.DataFrame:
    """MIRROR: s3a_baselines.build_trailing3_counts L222-235; pilot cap (P3)."""
    v = pd.read_parquet(RAW / "hpd_violations_wff.parquet",
                        columns=["bbl", "class", "inspectiondate"])
    v = v[v["class"] == "C"].copy()   # class-C restriction explicit (Rule 6)
    v["inspectiondate"] = pd.to_datetime(v["inspectiondate"], errors="coerce")
    v["bbl_n"] = norm_bbl(v["bbl"])
    v["season"] = v["inspectiondate"].map(season_of)
    v = v[v["season"].notna() & v["bbl_n"].notna()].copy()
    v["season"] = v["season"].astype(int)
    max_lookback_season = max(PILOT_VAL) - 1    # 2023 (P3)
    v = v[v["season"] <= max_lookback_season].copy()
    guard(v["season"], "rp1 B2 raw class-C counts",
          allowed=range(2017, max_lookback_season + 1))
    return v.groupby(["bbl_n", "season"]).size().rename("c_cnt").reset_index()


def trailing3_for_val(cnt, keys, v: int) -> np.ndarray:
    """MIRROR: s3a_baselines.trailing3_for_val L238-243."""
    look = cnt[cnt["season"].isin([v - 1, v - 2, v - 3])]
    guard(list(look["season"].unique()) + [v],
          f"rp1 B2 trailing3 v={v}", allowed=list(range(2017, v)) + [v])
    agg = look.groupby("bbl_n")["c_cnt"].sum()
    return keys["bbl_n"].map(agg).fillna(0.0).to_numpy()


def stage_b012(dev):
    """MIRROR: s3a_baselines.stage_b012 L359-389, pilot folds."""
    out = WORK / "b012.json"
    if out.exists():
        return
    cnt = build_trailing3_counts()
    results = {"B0": {}, "B1": {}, "B2": {}}
    b1_prov = {}
    for v in PILOT_VAL:
        train = dev[dev["season"] < v]
        val = dev[dev["season"] == v]
        guard(list(train["season"].unique()) + [v], f"rp1 b012 fold v={v}", PILOT_DEV)
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
    atomic_write(out, json.dumps({"label": PILOT_LABEL, "results": results,
                                  "b1_provenance": b1_prov}, indent=2))


# ------------------------- B3 (frozen booster, folds <= 2024 only; P7) -------------------------

def stage_b3(dev):
    """MIRROR: s3a_baselines.stage_b3 L392-425 restricted to pilot folds.
    NO season-2025 row is scored (P7; 2025 scoring is RP2's single shot)."""
    out = WORK / "b3.json"
    if out.exists():
        return
    booster = lgb.Booster(model_file=str(IMPORTS / "primary_lgbm.txt"))
    trees = booster.num_trees()
    assert trees == 343, f"B3 tree-count assertion FAILED: {trees} != 343 (Rule 9)"
    fb3 = pd.read_parquet(PROC / "features_b3.parquet")
    assert int(fb3["season"].max()) == 2025
    guard(fb3["season"], "rp1 features_b3 load (full frame; 2025 dropped next stmt)",
          FRAME_SEASONS)
    fb3 = fb3[fb3["season"].isin(PILOT_DEV)]
    assert int(fb3["season"].max()) == 2024          # D2 analog on the B3 frame
    fb3 = fb3.sort_values(["season", "bbl_n"], kind="mergesort").reset_index(drop=True)
    assert (fb3["bbl_n"].to_numpy() == dev["bbl_n"].to_numpy()).all()
    assert (fb3["season"].to_numpy() == dev["season"].to_numpy()).all()
    feat_list = booster.feature_name()
    results = {}
    for v in PILOT_VAL:
        m = fb3["season"] == v
        guard([v], f"rp1 b3 score v={v}", PILOT_DEV)
        score = booster.predict(fb3.loc[m, feat_list])
        y = fb3.loc[m, "label_c"].astype(int).to_numpy()
        tie = dev.loc[m.to_numpy(), "_tiekey"].to_numpy()
        z = zero311_mask(dev, v)
        results[str(v)] = eval_with_strata(y, score, tie, z)
        print(f"  b3 v={v}: p@250={results[str(v)]['p@250']:.4f} "
              f"zero311 p@250={results[str(v)]['zero311']['p@250']:.4f}")
    atomic_write(out, json.dumps({
        "label": PILOT_LABEL,
        "tree_count_assertion": {"expected": 343, "observed": trees, "pass": True},
        "in_sample_caveat": "v in {2021,2022,2023} were WFF TRAINING seasons for "
                            "this booster (in-sample); 2024 was a WFF test "
                            "season. Not retrained, not selected (P7); no "
                            "season-2025 row scored in RP1.",
        "results": results}, indent=2))


# ------------------------- B4 twin (two-stage IPW, pilot folds) -------------------------

def prop_target(dev) -> np.ndarray:
    """MIRROR: s3a_baselines.prop_target L428-433 (pilot insea311 cache)."""
    ins = pd.read_parquet(WORK / "insea311.parquet")
    key = ins.set_index(["bbl_n", "season"])["n311"]
    n311 = pd.MultiIndex.from_frame(dev[["bbl_n", "season"]]).map(key)
    n311 = pd.Series(n311, dtype="float64").fillna(0.0).to_numpy()
    return (n311 >= 2).astype(int)


def stage_prop(dev, deadline: float):
    """MIRROR: s3a_baselines.stage_prop L436-468, pilot folds."""
    cfgs = sampled_configs(PROP_DIMS)
    (WORK / "b4_prop").mkdir(parents=True, exist_ok=True)
    y_dup = prop_target(dev)
    feats = feature_cols(dev)
    pos = dev["label_c"].astype(int).to_numpy() == 1
    for v in PILOT_VAL:
        pend = [(i, c) for i, c in cfgs
                if not (WORK / "b4_prop" / f"cfg{i}_v{v}.json").exists()]
        if not pend:
            continue
        tr = (dev["season"] < v).to_numpy() & pos
        va = (dev["season"] == v).to_numpy() & pos
        guard(dev.loc[tr | va, "season"], f"rp1 prop fold v={v}", PILOT_DEV)
        dtr = lgb.Dataset(dev.loc[tr, feats], label=y_dup[tr],
                          params={"feature_pre_filter": False})
        dva = lgb.Dataset(dev.loc[va, feats], label=y_dup[va], reference=dtr)
        for i, cfg in pend:
            if time.time() > deadline:
                return False
            m = lgb.train(lgb_params(cfg), dtr, num_boost_round=cfg["n_estimators"],
                          valid_sets=[dva],
                          callbacks=[lgb.early_stopping(50, verbose=False)])
            rec = {"label": PILOT_LABEL, "config_idx": i, "config": cfg, "v": v,
                   "ap": float(m.best_score["valid_0"]["average_precision"]),
                   "best_iter": int(m.best_iteration),
                   "n_train": int(tr.sum()), "n_val": int(va.sum()),
                   "train_dup_rate": float(y_dup[tr].mean()),
                   "val_dup_rate": float(y_dup[va].mean())}
            atomic_write(WORK / "b4_prop" / f"cfg{i}_v{v}.json", json.dumps(rec))
        print(f"  prop fold v={v} complete")
    return True


def prop_winner():
    """MIRROR: s3a_baselines.prop_winner L471-490 (pre-registered rule:
    mean val AP, then config index)."""
    out = WORK / "b4_prop_winner.json"
    if out.exists():
        return json.loads(out.read_text())
    cfgs = sampled_configs(PROP_DIMS)
    rows = []
    for i, cfg in cfgs:
        aps, iters = [], []
        for v in PILOT_VAL:
            r = json.loads((WORK / "b4_prop" / f"cfg{i}_v{v}.json").read_text())
            aps.append(r["ap"]); iters.append(r["best_iter"])
        rows.append({"config_idx": i, "config": cfg, "mean_ap": float(np.mean(aps)),
                     "per_fold_ap": aps, "per_fold_best_iter": iters})
    rows.sort(key=lambda r: (-r["mean_ap"], r["config_idx"]))
    win = rows[0]
    win["label"] = PILOT_LABEL
    win["boundary"] = boundary_status(win["config"], PROP_DIMS)
    win["n_configs_evaluated"] = len(rows)
    win["runner_up"] = {"config_idx": rows[1]["config_idx"],
                        "mean_ap": rows[1]["mean_ap"]}
    atomic_write(out, json.dumps(win, indent=2))
    return win


def stage_rhat(dev):
    """MIRROR: s3a_baselines.stage_rhat L493-517, pilot folds."""
    win = prop_winner()
    y_dup = prop_target(dev)
    feats = feature_cols(dev)
    pos = dev["label_c"].astype(int).to_numpy() == 1
    for v in PILOT_VAL:
        out = WORK / f"rhat_v{v}.npz"
        if out.exists():
            continue
        tr = (dev["season"] < v).to_numpy() & pos
        va = (dev["season"] == v).to_numpy() & pos
        all_tr = (dev["season"] < v).to_numpy()
        guard(dev.loc[all_tr, "season"], f"rp1 rhat v={v}", PILOT_DEV)
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
    """MIRROR: s3a_baselines.stage_risk L520-561, pilot folds."""
    cfgs = sampled_configs(RISK_DIMS)
    (WORK / "b4_risk").mkdir(parents=True, exist_ok=True)
    feats = feature_cols(dev)
    y_all = dev["label_c"].astype(int).to_numpy()
    for v in PILOT_VAL:
        pend = [(i, c) for i, c in cfgs
                if not (WORK / "b4_risk" / f"cfg{i}_v{v}.json").exists()]
        if not pend:
            continue
        tr = (dev["season"] < v).to_numpy()
        va = (dev["season"] == v).to_numpy()
        guard(dev.loc[tr | va, "season"], f"rp1 risk fold v={v}", PILOT_DEV)
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
            rec = {"label": PILOT_LABEL, "config_idx": i, "config": cfg, "v": v,
                   "ap": float(m.best_score["valid_0"]["average_precision"]),
                   "best_iter": int(m.best_iteration), "metrics": res,
                   "spw_value": spw_value(cfg["scale_pos_weight"], ytr),
                   "w_max": float(w.max()),
                   "share_below_clip": float(
                       (rhat[ytr == 1] < cfg["clip_floor"]).mean())}
            atomic_write(WORK / "b4_risk" / f"cfg{i}_v{v}.json", json.dumps(rec))
        print(f"  risk fold v={v} complete")
    return True


def risk_winner():
    """MIRROR: s3a_baselines.risk_winner L564-586 (pre-registered rule: mean
    val AP, tie-break mean zero-311 p@250, then config index)."""
    out = WORK / "b4_risk_winner.json"
    if out.exists():
        return json.loads(out.read_text())
    cfgs = sampled_configs(RISK_DIMS)
    rows = []
    for i, cfg in cfgs:
        recs = [json.loads((WORK / "b4_risk" / f"cfg{i}_v{v}.json").read_text())
                for v in PILOT_VAL]
        z250 = [r["metrics"]["zero311"]["p@250"] for r in recs]
        rows.append({"config_idx": i, "config": cfg,
                     "mean_ap": float(np.mean([r["ap"] for r in recs])),
                     "mean_zero311_p250": float(np.mean(z250)),
                     "per_fold_ap": [r["ap"] for r in recs],
                     "per_fold_best_iter": [r["best_iter"] for r in recs]})
    rows.sort(key=lambda r: (-r["mean_ap"], -r["mean_zero311_p250"], r["config_idx"]))
    win = rows[0]
    win["label"] = PILOT_LABEL
    win["boundary"] = boundary_status(win["config"], RISK_DIMS)
    win["n_configs_evaluated"] = len(rows)
    win["runner_up"] = {k: rows[1][k] for k in
                        ("config_idx", "mean_ap", "mean_zero311_p250")}
    atomic_write(out, json.dumps(win, indent=2))
    return win


# ------------------------- B5 twin (uncorrected, Amendment 3) -------------------------

def b5_configs():
    """MIRROR: s3a_b5.b5_configs L44-54 — B4 stage-2's exact 60 seed-42
    configs; clip_floor inert metadata; zero-collision assertion."""
    cfgs = sampled_configs(RISK_DIMS)
    proj = {}
    for i, c in cfgs:
        key = tuple(sorted((k, v) for k, v in c.items() if k != "clip_floor"))
        proj.setdefault(key, []).append(i)
    dups = {k: v for k, v in proj.items() if len(v) > 1}
    assert not dups, f"operative-dim collision would need dedup handling: {dups}"
    return cfgs


B5_OPERATIVE_DIMS = [(n, v) for n, v in RISK_DIMS if n != "clip_floor"]


def stage_b5(dev, deadline: float):
    """MIRROR: s3a_b5.stage_b5 L57-93, pilot folds."""
    cfgs = b5_configs()
    (WORK / "b5_risk").mkdir(parents=True, exist_ok=True)
    feats = feature_cols(dev)
    y_all = dev["label_c"].astype(int).to_numpy()
    for v in PILOT_VAL:
        pend = [(i, c) for i, c in cfgs
                if not (WORK / "b5_risk" / f"cfg{i}_v{v}.json").exists()]
        if not pend:
            continue
        tr = (dev["season"] < v).to_numpy()
        va = (dev["season"] == v).to_numpy()
        guard(dev.loc[tr | va, "season"], f"rp1 B5 fold v={v}", PILOT_DEV)
        ytr, yva = y_all[tr], y_all[va]
        tie = dev.loc[va, "_tiekey"].to_numpy()
        zmask = zero311_mask(dev, v)
        dtr = lgb.Dataset(dev.loc[tr, feats], label=ytr,
                          params={"feature_pre_filter": False})
        dva = lgb.Dataset(dev.loc[va, feats], label=yva, reference=dtr)
        Xva = dev.loc[va, feats]
        for i, cfg in pend:
            if time.time() > deadline:
                return False
            # NO weights, NO clip: plain BCE on Y_obs (Amendment 3).
            m = lgb.train(lgb_params(cfg, spw=spw_value(cfg["scale_pos_weight"], ytr)),
                          dtr, num_boost_round=cfg["n_estimators"], valid_sets=[dva],
                          callbacks=[lgb.early_stopping(50, verbose=False)])
            score = m.predict(Xva, num_iteration=m.best_iteration)
            rec = {"label": PILOT_LABEL, "config_idx": i, "config": cfg, "v": v,
                   "clip_floor_inert": True,
                   "ap": float(m.best_score["valid_0"]["average_precision"]),
                   "best_iter": int(m.best_iteration),
                   "metrics": eval_with_strata(yva, score, tie, zmask),
                   "spw_value": spw_value(cfg["scale_pos_weight"], ytr)}
            atomic_write(WORK / "b5_risk" / f"cfg{i}_v{v}.json", json.dumps(rec))
        print(f"  b5 fold v={v} complete")
    return True


def b5_winner():
    """MIRROR: s3a_b5.b5_winner L96-117."""
    out = WORK / "b5_winner.json"
    if out.exists():
        return json.loads(out.read_text())
    rows = []
    for i, cfg in b5_configs():
        recs = [json.loads((WORK / "b5_risk" / f"cfg{i}_v{v}.json").read_text())
                for v in PILOT_VAL]
        rows.append({"config_idx": i, "config": cfg,
                     "mean_ap": float(np.mean([r["ap"] for r in recs])),
                     "mean_zero311_p250": float(np.mean(
                         [r["metrics"]["zero311"]["p@250"] for r in recs])),
                     "per_fold_ap": [r["ap"] for r in recs],
                     "per_fold_best_iter": [r["best_iter"] for r in recs]})
    rows.sort(key=lambda r: (-r["mean_ap"], -r["mean_zero311_p250"], r["config_idx"]))
    win = rows[0]
    win["label"] = PILOT_LABEL
    win["boundary"] = boundary_status(win["config"], B5_OPERATIVE_DIMS)
    win["clip_floor_metadata"] = win["config"]["clip_floor"]
    win["n_configs_evaluated"] = len(rows)
    win["runner_up"] = {k: rows[1][k] for k in
                        ("config_idx", "mean_ap", "mean_zero311_p250")}
    atomic_write(out, json.dumps(win, indent=2))
    return win


# ------------------------- GBM final refits (rpilot_* artifacts) -------------------------

def stage_gbm_final(dev):
    """MIRROR: s3a_baselines.stage_final L589-636 + s3a_b5.stage_final
    L120-145 — all-PILOT-dev refits, fixed n_estimators = round(mean fold
    best_iter), no ES (WFF frozen-refit convention); rpilot_* names (D7)."""
    if ART_B4_CFG.exists() and ART_B5_CFG.exists():
        return
    MODELS.mkdir(parents=True, exist_ok=True)
    win1, win2, win5 = prop_winner(), risk_winner(), b5_winner()
    feats = feature_cols(dev)
    y_all = dev["label_c"].astype(int).to_numpy()
    y_dup = prop_target(dev)
    pos = y_all == 1
    guard(dev["season"], "rp1 B4/B5 final refit (all pilot dev)", PILOT_DEV)

    if not ART_B4_CFG.exists():
        n1 = int(round(np.mean(win1["per_fold_best_iter"])))
        p1 = lgb_params(win1["config"]); p1.pop("feature_pre_filter")
        m1 = lgb.train(p1, lgb.Dataset(dev.loc[pos, feats], label=y_dup[pos]),
                       num_boost_round=n1)
        m1.save_model(str(ART_B4_PROP))
        rhat_all = m1.predict(dev[feats])

        n2 = int(round(np.mean(win2["per_fold_best_iter"])))
        w = np.ones(len(y_all))
        w[pos] = 1.0 / np.maximum(rhat_all[pos], win2["config"]["clip_floor"])
        p2 = lgb_params(win2["config"],
                        spw=spw_value(win2["config"]["scale_pos_weight"], y_all))
        p2.pop("feature_pre_filter")
        m2 = lgb.train(p2, lgb.Dataset(dev[feats], label=y_all, weight=w),
                       num_boost_round=n2)
        m2.save_model(str(ART_B4_RISK))
        atomic_write(ART_B4_CFG, json.dumps({
            "label": PILOT_LABEL,
            "pilot": "RP1 (Amendment 5(i)); cutoff 2025-10-01; folds v in "
                     "{2021,2022,2023,2024}; dev 2019-2024",
            "library": "lightgbm", "version": lgb.__version__, "seed": SEED,
            "stage1_propensity": {"config": win1["config"],
                                  "config_idx": win1["config_idx"],
                                  "mean_val_ap": win1["mean_ap"],
                                  "frozen_n_estimators": n1,
                                  "train": "all pilot-dev label_c==1 rows, target "
                                           "y_dup=1{in-season 311 events>=2}"},
            "stage2_risk": {"config": win2["config"],
                            "config_idx": win2["config_idx"],
                            "mean_val_ap": win2["mean_ap"],
                            "frozen_n_estimators": n2,
                            "train": "all pilot-dev rows, positives weighted "
                                     "1/max(Rhat, clip_floor)",
                            "rhat_summary": {"min": float(rhat_all.min()),
                                             "max": float(rhat_all.max()),
                                             "share_below_clip": float(
                                                 (rhat_all[pos] <
                                                  win2["config"]["clip_floor"]).mean())}},
            "protocol": "forward-chaining train [2019, v), ES-50 watching v (as "
                        "frozen in hyperparam_grid.md), selection mean val AP / "
                        "tie-break zero-311 p@250; refit all-pilot-dev with fixed "
                        "n_estimators",
            "dev_seasons": PILOT_DEV, "val_seasons": PILOT_VAL,
            "amendment1_boundary": "propensity target from the 311 UNION only; "
                                   "ygpa-z7cr present solely as c7_* features",
        }, indent=2))
        print(f"  rpilot B4 artifacts written (n1={n1}, n2={n2})")

    if not ART_B5_CFG.exists():
        n5 = int(round(np.mean(win5["per_fold_best_iter"])))
        p5 = lgb_params(win5["config"],
                        spw=spw_value(win5["config"]["scale_pos_weight"], y_all))
        p5.pop("feature_pre_filter")
        m5 = lgb.train(p5, lgb.Dataset(dev[feats], label=y_all),
                       num_boost_round=n5)
        m5.save_model(str(ART_B5))
        atomic_write(ART_B5_CFG, json.dumps({
            "label": PILOT_LABEL,
            "pilot": "RP1 (Amendment 5(i)); cutoff 2025-10-01; folds v in "
                     "{2021,2022,2023,2024}; dev 2019-2024",
            "library": "lightgbm", "version": lgb.__version__, "seed": SEED,
            "baseline": "B5 uncorrected retrained LightGBM (spec Amendment 3)",
            "config": win5["config"], "config_idx": win5["config_idx"],
            "mean_val_ap": win5["mean_ap"],
            "clip_floor_inert_metadata": True,
            "frozen_n_estimators": n5,
            "train": "all pilot-dev rows, plain binary objective on label_c — no "
                     "propensity stage, no IPW, no sample weights",
            "protocol": "identical folds/frame/grid-sample/selection as B4 stage 2 "
                        "(hyperparam_grid.md §5-§6; ES-50 watching v); refit "
                        "all-pilot-dev with fixed n_estimators",
            "dev_seasons": PILOT_DEV, "val_seasons": PILOT_VAL,
        }, indent=2))
        print(f"  rpilot B5 artifact written (n={n5} trees)")


# ------------------------- joint model stages -------------------------

def search_units():
    cfgs = sampled_configs(NET_DIMS)     # identical 60 indices as build S3b (D5)
    return [(i, c, str(v), SEED) for v in PILOT_VAL for (i, c) in cfgs]


def joint_winner():
    """MIRROR: s3b_primary.stage_winner L839-866 (pre-registered rule D5)."""
    out = WORK / "joint_winner.json"
    if out.exists():
        return json.loads(out.read_text())
    cfgs = sampled_configs(NET_DIMS)
    rows = []
    for i, cfg in cfgs:
        recs = [json.loads((UNITS / f"cfg{i}_v{v}_s{SEED}.json").read_text())
                for v in PILOT_VAL]
        rows.append({
            "config_idx": i, "config": cfg,
            "mean_ap_q": float(np.mean([r["ap_q"] for r in recs])),
            "mean_zero311_p250_F": float(np.mean([r["zero311_p250_F"] for r in recs])),
            "per_fold_ap_q": [r["ap_q"] for r in recs],
            "per_fold_best_epoch": [r["best_epoch"] for r in recs],
        })
    rows.sort(key=lambda r: (-r["mean_ap_q"], -r["mean_zero311_p250_F"],
                             r["config_idx"]))
    win = rows[0]
    win["label"] = PILOT_LABEL
    win["boundary"] = boundary_status(win["config"], NET_DIMS)
    win["n_configs_evaluated"] = len(rows)
    win["runner_up"] = {k_: rows[1][k_] for k_ in
                        ("config_idx", "mean_ap_q", "mean_zero311_p250_F")}
    win["selection_rule"] = ("mean val AP of F*R vs Y_obs over pilot folds "
                             "{2021,2022,2023,2024}; tie-break mean zero-311-"
                             "stratum p@250 of F; then config_idx")
    atomic_write(out, json.dumps(win, indent=2))
    return win


def spread_units(win):
    return [(win["config_idx"], win["config"], str(v), s)
            for s in SPREAD_SEEDS if s != SEED for v in PILOT_VAL]


def stage_spread_report(win):
    """MIRROR: s3b_primary.stage_spread_report L874-900, pilot folds (D6)."""
    out = WORK / "seed_spread.json"
    if out.exists():
        return
    per_seed = {}
    for s in SPREAD_SEEDS:
        recs = [json.loads((UNITS / f"cfg{win['config_idx']}_v{v}_s{s}.json")
                           .read_text()) for v in PILOT_VAL]
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
        "label": PILOT_LABEL,
        "note": "VALIDATION-based spread over pilot folds <=2024 only (D6; spec "
                "§8, Rule 10); winning hyperparams fixed; seed 42 rows are the "
                "search units themselves (deterministic identity, disclosed).",
        "per_seed": per_seed,
        "spread_mean_ap_q": {"min": min(aps), "max": max(aps),
                             "std": float(np.std(aps)), "range": max(aps) - min(aps)},
        "spread_zero311_p250_F": {"min": min(z), "max": max(z),
                                  "std": float(np.std(z)), "range": max(z) - min(z)},
    }, indent=2))


def stage_refit(win, deadline) -> str:
    """MIRROR: s3b_primary.stage_refit L1020-1045 (A9 analog P4): all-pilot-dev
    refit at E* = round(mean of the 4 per-fold best epochs), no fixed batch."""
    uid = f"cfg{win['config_idx']}_v{FOLD_ALL}_s{SEED}"
    e_star = int(round(np.mean(win["per_fold_best_epoch"])))
    atomic_write(WORK / "refit_meta.json", json.dumps(
        {"label": PILOT_LABEL, "e_star": e_star,
         "rule": "round(mean per-fold best_epoch of winner) over pilot folds",
         "per_fold_best_epoch": win["per_fold_best_epoch"]}))
    if not (UNITS / f"{uid}.json").exists():
        status = train_unit(win["config_idx"], win["config"], FOLD_ALL, SEED,
                            deadline, epochs_override=e_star)
        if status != "done":
            return status
    if not ART_JOINT.exists():
        _finalize_joint(win, e_star)
    return "done"


def _finalize_joint(win, e_star):
    """MIRROR: s3b_primary._finalize_artifact L1048-1093, rpilot_* names (D7)."""
    import torch
    MODELS.mkdir(parents=True, exist_ok=True)
    uid = f"cfg{win['config_idx']}_v{FOLD_ALL}_s{SEED}"
    state = torch.load(UNITS / f"{uid}.model.pt", weights_only=False)["state_dict"]
    meta = json.loads((WORK / "design_meta.json").read_text())
    scal = json.loads((WORK / "scalers.json").read_text())[FOLD_ALL]

    t = fold_tensors(FOLD_ALL)["train"]
    model = build_model(win["config"], t["x"].shape[1], SEED, 0)
    model.load_state_dict(state)
    _, F_all, p_all = eval_pass(model, t, win["config"],
                                meta["pbar"][f"{FOLD_ALL}|{win['config']['ustar']}"])
    aux = np.load(WORK / "aux.npz")
    np.savez_compressed(WORK / "pilot_dev_scores.npz", bbl=aux["bbl"],
                        season=aux["season"], F=F_all, p=p_all)

    cfg_payload = {
        "label": PILOT_LABEL,
        "pilot": "RP1 (Amendment 5(i)); cutoff 2025-10-01; folds v in "
                 "{2021,2022,2023,2024}; dev 2019-2024; the frozen build-phase "
                 "bundle s3b_primary_seed42.pt is untouched (D7)",
        "architecture": "spec §3 two-head net: shared MLP encoder (Linear-"
                        "LayerNorm-ReLU-Dropout blocks), head F sigmoid, head p "
                        "sigmoid, R = 1-(1-p)^min(u,u*)",
        "config": win["config"], "config_idx": win["config_idx"],
        "mean_val_ap_q": win["mean_ap_q"],
        "seed": SEED, "e_star_epochs": e_star,
        "refit": "all pilot-dev seasons 2019-2024, cosine LR over 200 epochs "
                 "stopped at e_star, no ES (A9 analog)",
        "selection": win["selection_rule"],
        "loss": "L = BCE(Y_obs, F*R) + lam*NLL_zero-trunc-binomial(k|u,p) "
                "+ mu1*Omega1 + mu2*Omega2 (Amendment-4(i) frozen axes A1-A10, "
                "src/s3b_primary.py header)",
        "pbar_all_pilot_dev": meta["pbar"][f"{FOLD_ALL}|{win['config']['ustar']}"],
        "design": {"n_cols": meta["n_design_cols"],
                   "meta": "outputs/checkpoints/rp1_work/design_meta.json"},
        "feature_recipe_hashes": meta["frame_hashes"],
        "library_versions": _versions(),
        "train_threads": TRAIN_THREADS,
    }
    atomic_save_torch({"state_dict": state, "config": cfg_payload,
                       "scaler_all": scal,
                       "design_cols": meta["design_cols"],
                       "std_cols": meta["std_cols"]}, ART_JOINT)
    atomic_write(ART_JOINT_CFG, json.dumps(cfg_payload, indent=2))
    print(f"  rpilot joint artifact written: {ART_JOINT.name} (E*={e_star})")


def _versions():
    import sklearn
    import torch
    return {"torch": torch.__version__, "numpy": np.__version__,
            "pandas": pd.__version__, "sklearn": sklearn.__version__,
            "lightgbm": lgb.__version__, "python": sys.version.split()[0]}


# ------------------------- report -------------------------

def _tree_size(paths) -> int:
    total = 0
    for root in paths:
        for dirpath, _, files in os.walk(root):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(dirpath, f))
                except OSError:
                    pass
    return total


def stage_report():
    """MIRROR pattern: s3a/s3b stage_report — machine-generated stats + table
    (no hand transcription; M3/M5 lineage)."""
    out = WORK / "rp1_stats.json"
    tbl = WORK / "rp1_table.md"
    if out.exists() and tbl.exists():
        return
    win = joint_winner()
    win1, win2, win5 = prop_winner(), risk_winner(), b5_winner()
    spread = json.loads((WORK / "seed_spread.json").read_text())
    meta = json.loads((WORK / "design_meta.json").read_text())
    refit_meta = json.loads((WORK / "refit_meta.json").read_text())
    b012 = json.loads((WORK / "b012.json").read_text())
    b3 = json.loads((WORK / "b3.json").read_text())
    b4_per = {str(v): json.loads(
        (WORK / "b4_risk" / f"cfg{win2['config_idx']}_v{v}.json").read_text())
        for v in PILOT_VAL}
    b5_per = {str(v): json.loads(
        (WORK / "b5_risk" / f"cfg{win5['config_idx']}_v{v}.json").read_text())
        for v in PILOT_VAL}
    joint_per = {str(v): json.loads(
        (UNITS / f"cfg{win['config_idx']}_v{v}_s{SEED}.json").read_text())
        for v in PILOT_VAL}

    d7 = assert_preflight_unchanged()

    def mean_over(res_by_v, path):
        vals = []
        for v in PILOT_VAL:
            node = res_by_v[str(v)]
            for k in path:
                node = node[k]
            if node is not None:
                vals.append(node)
        return float(np.mean(vals)) if vals else None

    tables = {"B0": b012["results"]["B0"], "B1": b012["results"]["B1"],
              "B2": b012["results"]["B2"], "B3": b3["results"],
              "B4": {str(v): b4_per[str(v)]["metrics"] for v in PILOT_VAL},
              "B5": {str(v): b5_per[str(v)]["metrics"] for v in PILOT_VAL},
              "joint (q=F*R)": {str(v): joint_per[str(v)]["metrics_q"]
                                for v in PILOT_VAL},
              "joint (F ranking)": {str(v): joint_per[str(v)]["metrics_F"]
                                    for v in PILOT_VAL}}
    summary = {}
    for b, res in tables.items():
        summary[b] = {
            "mean_pr_auc": mean_over(res, ["pr_auc"]),
            "mean_p@250": mean_over(res, ["p@250"]),
            "mean_zero311_p@250": mean_over(res, ["zero311", "p@250"]),
            "mean_any311_p@250": mean_over(res, ["any311", "p@250"]),
        }

    guards_ = [json.loads(l) for l in
               (WORK / "guards.jsonl").read_text().splitlines() if l.strip()]
    guard_facts = {
        "distinct_sites": sorted({g["where"] for g in guards_}),
        "n_distinct_sites": len({g["where"] for g in guards_}),
        "max_season_ever_touched": max(max(g["touched"]) for g in guards_),
        "n_2026plus_firings": 0,
        "note": "a >=2026 firing is a hard AssertionError, not a log line; the "
                "raw pass count is an append-only cumulative snapshot "
                "(M5/M7 lineage), headline facts above are deterministic",
        "raw_pass_count_snapshot": len(guards_),
    }
    storage_bytes = _tree_size([REPO / "data", REPO / "outputs", REPO / "imports"])

    payload = {
        "label": PILOT_LABEL,
        "stage": "RP1 (Amendment 5(i)) — re-selection/re-training at pilot "
                 "cutoff 2025-10-01; season 2025 never loaded into any dev "
                 "structure (D2); season 2026-27 untouched (D4)",
        "seed": SEED, "pilot_dev_seasons": PILOT_DEV, "pilot_val_seasons": PILOT_VAL,
        "library_versions": _versions(),
        "design": {k_: meta[k_] for k_ in
                   ("n_rows", "n_design_cols", "n_eligible", "n_labelc1",
                    "u_source_counts", "k_exceeds_u_by_ustar", "frame_hashes")},
        "summary_means": summary,
        "per_season": tables,
        "b1_provenance": b012["b1_provenance"],
        "b3_tree_count_assertion": b3["tree_count_assertion"],
        "b3_in_sample_caveat": b3["in_sample_caveat"],
        "winners": {
            "joint": {k_: win[k_] for k_ in
                      ("config_idx", "config", "boundary", "mean_ap_q",
                       "mean_zero311_p250_F", "per_fold_ap_q",
                       "per_fold_best_epoch", "runner_up", "selection_rule",
                       "n_configs_evaluated")},
            "b4_stage1": {k_: win1[k_] for k_ in
                          ("config_idx", "config", "boundary", "mean_ap",
                           "per_fold_ap", "per_fold_best_iter", "runner_up")},
            "b4_stage2": {k_: win2[k_] for k_ in
                          ("config_idx", "config", "boundary", "mean_ap",
                           "mean_zero311_p250", "per_fold_ap",
                           "per_fold_best_iter", "runner_up")},
            "b5": {k_: win5[k_] for k_ in
                   ("config_idx", "config", "boundary", "mean_ap",
                    "mean_zero311_p250", "per_fold_ap", "per_fold_best_iter",
                    "runner_up", "clip_floor_metadata")},
        },
        "per_season_joint_details": {str(v): {
            "best_epoch": joint_per[str(v)]["best_epoch"],
            "val_terms_at_best": joint_per[str(v)]["val_terms_at_best"]}
            for v in PILOT_VAL},
        "seed_spread_validation": spread,
        "refit": refit_meta,
        "d7_preflight_reverify": d7,
        "guard_assertions": guard_facts,
        "storage_bytes_data_outputs_imports": storage_bytes,
        "storage_gb": round(storage_bytes / 1e9, 3),
        "artifacts": {p.name: sha256_file(p) for p in sorted(PILOT_ARTIFACTS)
                      if p.exists()},
    }
    atomic_write(out, json.dumps(payload, indent=2))

    fmt = lambda x: ("n/a" if x is None else f"{x:.4f}")
    lines = [
        f"**{PILOT_LABEL}** — RP1 pilot validation table (machine-generated — "
        "no hand transcription). Means over the 4 pilot folds v = 2021..2024.",
        "",
        "| Model | mean AP | mean p@250 | mean zero-311 p@250 | mean any-311 p@250 |",
        "|---|---|---|---|---|",
    ]
    for b in ("B0", "B1", "B2", "B3", "B4", "B5", "joint (q=F*R)",
              "joint (F ranking)"):
        s = summary[b]
        lines.append(f"| {b} | " + " | ".join(
            fmt(s[k]) for k in ("mean_pr_auc", "mean_p@250",
                                "mean_zero311_p@250", "mean_any311_p@250")) + " |")
    lines += [
        "",
        "AP for the joint rows: q=F·R vs Y_obs (selection metric) and the F "
        "ranking respectively; p@250 columns use each row's own score.",
        "B3 row: frozen booster, folds ≤2024 only; v∈{2021,2022,2023} in-sample "
        "(WFF training seasons); no season-2025 row scored in RP1.",
        "",
        "| Seed | mean AP (F·R) | mean p@250 (F) | mean zero-311 p@250 (F) |",
        "|---|---|---|---|",
    ]
    for s in SPREAD_SEEDS:
        ps = spread["per_seed"][str(s)]
        lines.append(f"| {s} | {ps['mean_ap_q']:.4f} | {ps['mean_p250_F']:.4f} | "
                     f"{ps['mean_zero311_p250_F']:.4f} |")
    lines += [
        "",
        "Per-fold joint winner AP (F·R), v=2021..2024: " + " / ".join(
            f"{a:.4f}" for a in win["per_fold_ap_q"]),
        "Per-fold B4 AP: " + " / ".join(f"{a:.4f}" for a in win2["per_fold_ap"]),
        "Per-fold B5 AP: " + " / ".join(f"{a:.4f}" for a in win5["per_fold_ap"]),
    ]
    atomic_write(tbl, "\n".join(lines) + "\n")
    print("  wrote rp1_stats.json + rp1_table.md")
    for b in ("B0", "B1", "B2", "B3", "B4", "B5", "joint (q=F*R)"):
        s = summary[b]
        print(f"  {b}: mean AP={fmt(s['mean_pr_auc'])} p@250={fmt(s['mean_p@250'])} "
              f"zero311 p@250={fmt(s['mean_zero311_p@250'])}")


# ------------------------- main -------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=9.0)
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()
    deadline = time.time() + args.minutes * 60
    WORK.mkdir(parents=True, exist_ok=True)

    import torch
    torch.set_num_threads(TRAIN_THREADS)

    print(f"=== RP1 pilot ({PILOT_LABEL}) — cutoff 2025-10-01 — seed {SEED} — "
          f"budget {args.minutes} min — workers {args.workers} ===")
    stage_preflight()
    prep_design()

    # ---- GBM lanes (need the pandas dev frame)
    if not (ART_B4_CFG.exists() and ART_B5_CFG.exists()
            and (WORK / "b012.json").exists() and (WORK / "b3.json").exists()):
        dev = load_pilot_dev()
        stage_b012(dev)
        stage_b3(dev)
        if not stage_prop(dev, deadline):
            print("PARTIAL: B4 stage-1 propensity search pending — rerun to resume")
            return 0
        prop_winner()
        stage_rhat(dev)
        if not stage_risk(dev, deadline):
            print("PARTIAL: B4 stage-2 risk search pending — rerun to resume")
            return 0
        risk_winner()
        if not stage_b5(dev, deadline):
            print("PARTIAL: B5 search pending — rerun to resume")
            return 0
        b5_winner()
        stage_gbm_final(dev)
        del dev

    # ---- joint model lane
    if not run_pool(search_units(), deadline, args.workers):
        n_done = sum((UNITS / f"cfg{i}_v{fk}_s{s}.json").exists()
                     for (i, c, fk, s) in search_units())
        print(f"PARTIAL: joint search {n_done}/{len(search_units())} units — "
              f"rerun to resume")
        return 0
    win = joint_winner()

    if not run_pool(spread_units(win), deadline, args.workers):
        print("PARTIAL: seed-spread units pending — rerun to resume")
        return 0
    stage_spread_report(win)

    if stage_refit(win, deadline) != "done":
        print("PARTIAL: refit in progress — rerun to resume")
        return 0

    stage_report()
    print("ALL STAGES COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
