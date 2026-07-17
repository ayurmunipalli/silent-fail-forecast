"""S3a appendix — baseline B5, uncorrected retrained LightGBM (spec Amendment 3).

The uncorrected twin of B4's risk stage: plain binary objective on label_c,
NO propensity stage, NO IPW. Identical 49-feature frame, identical forward-
chaining folds, and THE SAME 60 sampled configs as B4 stage 2 (sampling seed
42), with the clip-floor dimension carried as INERT metadata — handling stated
in outputs/checkpoints/s3a_baselines.md (B5 appendix) BEFORE any training and
flagged to LEAD; verified zero collisions when the 60 configs are projected
onto the 9 operative dimensions.

Separate file by design: the signed-off src/s3a_baselines.py is IMPORTED, never
modified. Same discipline: idempotent + resumable (per-unit checkpoints in
outputs/checkpoints/s3a_work/b5_risk/), bounded invocations (--minutes), seed
42, guards asserted and recorded to the same guards.jsonl.

Selection (pre-registered, grid §1): mean validation AP vs Y_obs; tie-break
mean zero-311-stratum p@250. Final artifact refit on all dev seasons with
n_estimators = round(mean fold best_iter), no ES (WFF frozen-refit convention)
-> outputs/models/b5_lgbm.txt + b5_frozen_config.json.

Outputs are MACHINE-GENERATED into s3a_stats.json (additive "b5_*" keys; no
S3a-audited key is altered) and outputs/checkpoints/s3a_work/b5_table.md (the
markdown table appended verbatim to the checkpoint — no hand transcription).
"""
from __future__ import annotations

import argparse
import json
import time

import lightgbm as lgb
import numpy as np

from s3a_baselines import (
    CKPT, DEV_SEASONS, MODELS, RISK_DIMS, SEED, VAL_SEASONS, WORK,
    assert_no_test_contact, boundary_status, eval_with_strata, feature_cols,
    lgb_params, load_dev_frame, sampled_configs, spw_value, zero311_mask,
)

B5_WORK = WORK / "b5_risk"
OPERATIVE_DIMS = [(n, v) for n, v in RISK_DIMS if n != "clip_floor"]


def b5_configs():
    """THE B4 stage-2 sample, verbatim (same indices, same seed-42 draw);
    clip_floor retained in the record as inert metadata."""
    cfgs = sampled_configs(RISK_DIMS)
    proj = {}
    for i, c in cfgs:
        key = tuple(sorted((k, v) for k, v in c.items() if k != "clip_floor"))
        proj.setdefault(key, []).append(i)
    dups = {k: v for k, v in proj.items() if len(v) > 1}
    assert not dups, f"operative-dim collision would need dedup handling: {dups}"
    return cfgs


def stage_b5(dev, deadline: float):
    cfgs = b5_configs()
    B5_WORK.mkdir(parents=True, exist_ok=True)
    feats = feature_cols(dev)
    y_all = dev["label_c"].astype(int).to_numpy()
    for v in VAL_SEASONS:
        pend = [(i, c) for i, c in cfgs
                if not (B5_WORK / f"cfg{i}_v{v}.json").exists()]
        if not pend:
            continue
        tr = (dev["season"] < v).to_numpy()
        va = (dev["season"] == v).to_numpy()
        assert_no_test_contact(dev.loc[tr | va, "season"], f"B5 fold v={v}", DEV_SEASONS)
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
            rec = {"config_idx": i, "config": cfg, "v": v,
                   "clip_floor_inert": True,
                   "ap": float(m.best_score["valid_0"]["average_precision"]),
                   "best_iter": int(m.best_iteration),
                   "metrics": eval_with_strata(yva, score, tie, zmask),
                   "spw_value": spw_value(cfg["scale_pos_weight"], ytr)}
            (B5_WORK / f"cfg{i}_v{v}.json").write_text(json.dumps(rec))
        print(f"  b5 fold v={v} complete")
    return True


def b5_winner():
    out = WORK / "b5_winner.json"
    if out.exists():
        return json.loads(out.read_text())
    rows = []
    for i, cfg in b5_configs():
        recs = [json.loads((B5_WORK / f"cfg{i}_v{v}.json").read_text())
                for v in VAL_SEASONS]
        rows.append({"config_idx": i, "config": cfg,
                     "mean_ap": float(np.mean([r["ap"] for r in recs])),
                     "mean_zero311_p250": float(np.mean(
                         [r["metrics"]["zero311"]["p@250"] for r in recs])),
                     "per_fold_ap": [r["ap"] for r in recs],
                     "per_fold_best_iter": [r["best_iter"] for r in recs]})
    rows.sort(key=lambda r: (-r["mean_ap"], -r["mean_zero311_p250"], r["config_idx"]))
    win = rows[0]
    win["boundary"] = boundary_status(win["config"], OPERATIVE_DIMS)
    win["clip_floor_metadata"] = win["config"]["clip_floor"]
    win["n_configs_evaluated"] = len(rows)
    win["runner_up_mean_ap"] = rows[1]["mean_ap"]
    out.write_text(json.dumps(win, indent=2))
    return win


def stage_final(dev):
    cfg_out = MODELS / "b5_frozen_config.json"
    if cfg_out.exists():
        return
    win = b5_winner()
    feats = feature_cols(dev)
    y_all = dev["label_c"].astype(int).to_numpy()
    assert_no_test_contact(dev["season"], "B5 final refit (all dev)", DEV_SEASONS)
    n = int(round(np.mean(win["per_fold_best_iter"])))
    p = lgb_params(win["config"], spw=spw_value(win["config"]["scale_pos_weight"], y_all))
    p.pop("feature_pre_filter")
    m = lgb.train(p, lgb.Dataset(dev[feats], label=y_all), num_boost_round=n)
    m.save_model(str(MODELS / "b5_lgbm.txt"))
    cfg_out.write_text(json.dumps({
        "library": "lightgbm", "version": lgb.__version__, "seed": SEED,
        "baseline": "B5 uncorrected retrained LightGBM (spec Amendment 3)",
        "config": win["config"], "clip_floor_inert_metadata": True,
        "frozen_n_estimators": n,
        "train": "all dev rows, plain binary objective on label_c — no "
                 "propensity stage, no IPW, no sample weights",
        "protocol": "identical folds/frame/grid-sample/selection as B4 stage 2 "
                    "(hyperparam_grid.md §5-§6; ES-50 watching v); refit "
                    "all-dev with fixed n_estimators",
        "dev_seasons": DEV_SEASONS, "val_seasons": VAL_SEASONS,
    }, indent=2))
    print(f"  final B5 artifact written (n={n} trees)")


def stage_report(dev):
    """Additive update of s3a_stats.json (b5_* keys) + machine-generated
    markdown fragments (summary table row + per-fold line + B4 deltas)."""
    win = b5_winner()
    per = {str(v): json.loads((B5_WORK / f"cfg{win['config_idx']}_v{v}.json").read_text())
           for v in VAL_SEASONS}
    metrics = {sv: r["metrics"] for sv, r in per.items()}

    def mean_over(path):
        vals = []
        for v in VAL_SEASONS:
            node = metrics[str(v)]
            for k in path:
                node = node[k]
            vals.append(node)
        return float(np.mean(vals))

    summary = {"mean_pr_auc": mean_over(["pr_auc"]),
               "mean_p@250": mean_over(["p@250"]),
               "mean_zero311_p@250": mean_over(["zero311", "p@250"]),
               "mean_any311_p@250": mean_over(["any311", "p@250"])}

    stats = json.loads((CKPT / "s3a_stats.json").read_text())
    b4 = stats["summary_means"]["B4"]
    guards = [json.loads(l) for l in
              (WORK / "guards.jsonl").read_text().splitlines() if l.strip()]
    stats["b5_summary_means"] = summary
    stats["b5_per_season"] = metrics
    stats["b5_winner"] = win
    stats["b5_vs_b4_deltas"] = {k: summary[k] - b4[k] for k in summary}
    stats["b5_note"] = ("Amendment-3 baseline; additive keys only — no S3a-"
                        "audited key altered. Same 60 seed-42 configs as B4 "
                        "stage 2; clip_floor inert (zero projection collisions).")
    stats["b5_guard_assertions"] = {
        "n_recorded_passes_total": len(guards),
        "distinct_sites_total": len({g["where"] for g in guards}),
        "max_season_ever_touched": max(max(g["touched"]) for g in guards)}
    (CKPT / "s3a_stats.json").write_text(json.dumps(stats, indent=2))

    fmt = lambda x: f"{x:.4f}"
    lines = [
        "| Model | mean AP | mean p@250 | mean zero-311 p@250 | mean any-311 p@250 |",
        "|---|---|---|---|---|",
        "| B4 two-stage GBM (corrected) | " + " | ".join(
            fmt(b4[k]) for k in ("mean_pr_auc", "mean_p@250",
                                 "mean_zero311_p@250", "mean_any311_p@250")) + " |",
        "| B5 uncorrected twin | " + " | ".join(
            fmt(summary[k]) for k in ("mean_pr_auc", "mean_p@250",
                                      "mean_zero311_p@250", "mean_any311_p@250")) + " |",
        "| Δ (B5 − B4) | " + " | ".join(
            f"{stats['b5_vs_b4_deltas'][k]:+.4f}" for k in
            ("mean_pr_auc", "mean_p@250", "mean_zero311_p@250",
             "mean_any311_p@250")) + " |",
        "",
        "Per-fold B5 p@250 (v = 2021…2025): " + " / ".join(
            fmt(metrics[str(v)]["p@250"]) for v in VAL_SEASONS) + ".",
        "Per-fold B5 AP: " + " / ".join(
            fmt(metrics[str(v)]["pr_auc"]) for v in VAL_SEASONS) + ".",
        "Per-fold B5 zero-311 p@250: " + " / ".join(
            fmt(metrics[str(v)]["zero311"]["p@250"]) for v in VAL_SEASONS) + ".",
    ]
    (WORK / "b5_table.md").write_text("\n".join(lines) + "\n")
    print("  wrote b5 keys into s3a_stats.json + s3a_work/b5_table.md")
    print(f"  B5: mean AP={summary['mean_pr_auc']:.4f} "
          f"p@250={summary['mean_p@250']:.4f} "
          f"zero311={summary['mean_zero311_p@250']:.4f} "
          f"any311={summary['mean_any311_p@250']:.4f}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=8.5)
    args = ap.parse_args()
    deadline = time.time() + args.minutes * 60
    print(f"=== S3a appendix: B5 (Amendment 3) — seed {SEED} ===")
    dev = load_dev_frame()
    if not stage_b5(dev, deadline):
        print("PARTIAL: B5 search pending — rerun to resume")
        return 0
    b5_winner()
    stage_final(dev)
    stage_report(dev)
    print("B5 COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
