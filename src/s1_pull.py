"""S1 — build-phase data acquisition + verification (A-DATA).

Binding docs: CLAUDE.md (Rules 1,2,3,5,6,8a,9,10), model_spec.md §2, plan.md §3 step 2,
.claude/agents/a-data.md. Acquisition and verification ONLY — no analysis, no modeling.

Idempotent, server-side filtered, paged, parquet-cached, storage-guarded.
Rerun: `.venv/bin/python src/s1_pull.py` (add --force to re-pull raw caches).
NEVER fabricates: empty pull / schema surprise / ID mismatch / spine mismatch raises
and stops the branch (Rules 1, 9).

Scope of this stage:
  1. Verify every dataset ID live (Rule 5), incl. ygpa-z7cr per R-A = ADMIT
     (model_spec.md Amendment 1, 2026-07-16, relayed by LEAD mid-stage).
  2. Refresh the 311 union (erm2-nwe9 + 76ig-c548) per phase0_probe.md Amendment 3:
     verbatim whitelist, six §2 columns, floor created_date >= 2019-06-01, dedupe on
     unique_key with count logged, seam diagnostics at BOTH the 2019-12-31/2020-01-01
     archive boundary AND the old/new refresh edge (phase-0 pull ended 2026-07-13).
     Phase-0 raw caches are preserved untouched; the current-side refresh goes to a
     NEW cache and the deliverable c311_heat_complaints.parquet is regenerated
     deterministically from the two caches (its standing semantics).
  3. New pulls, mirroring the read-only WFF recipe so A-FEAT can re-implement
     s2_features.py exactly (spec §7 families; plan.md §3 step 2):
       - hpd_violations_wff:    wvxf-dwi5, frozen whitelist VERBATIM, floor 2017-10-01,
                                WFF s1_data_pull.py column set (family 1 + spine checks).
                                DISCLOSED ADDITION beyond the enumerated a-data.md pull
                                list: WFF family 1 consumes whitelisted violation ROWS
                                from 2017-10-01; the phase-0 cache (floor 2019-06-01,
                                narrower columns) cannot feed the WFF-recipe frame.
       - hpd_viol_context_by_year: wvxf-dwi5 server-side aggregate (bbl,class,yr),
                                floor 2014-06-01 — WFF s1c verbatim (family 2).
       - hpd_registrations:     tesw-yqqr, WFF column set (family 5 + universe).
       - hpd_registration_contacts: feu5-w2e2, WFF column set (family 5).
       - pluto_full:            64uk-42ks, WFF 11-column attribute set (family 4:
                                age/units/class/floors/borough — not the phase-0 pair).
       - hpd_complaints_heat:   ygpa-z7cr (R-A = ADMIT, spec Amendment 1), heat/
                                hot-water problem rows with apartment identifiers,
                                floor 2019-06-01. Family 7 + §10 criterion-3 screen
                                ONLY; never the reporting-head likelihood.
  4. Verify the imported R4 spine (imports/building_season_labels.parquet, read-only):
     sha256 vs PROVENANCE, season coverage 2017-18..2025-26, per-season row counts and
     positives vs WFF's committed report (outputs/checkpoints/_s1b_frozen_labels.json,
     values hardcoded below as the comparison target). Any mismatch -> HARD STOP.

FROZEN VIOLATION WHITELIST — ported VERBATIM from winter-fail-forecast
src/s1_data_pull.py (itself verbatim from cross-season-heat phase0_memo.md §1):
    (novdescription ILIKE '%ADEQUATE SUPPLY OF HEAT%'
     OR novdescription ILIKE '%PROVIDE HOT WATER AT%')
    AND class IN ('B','C')
B+C superset pulled; class-C restriction is applied explicitly in ANALYSIS code
downstream, never here (Rule 6 standing pattern).

Season 2026-27 is never touched (Rule 3): every dated filter here ends at pull time
(2026-07-16, pre-season); no 2026-27 label exists or is constructed.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd
from dotenv import dotenv_values

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "data" / "raw"
IMPORTS = REPO / "imports"
RAW.mkdir(parents=True, exist_ok=True)

FORCE = "--force" in sys.argv
TODAY = "2026-07-16"  # session date (deterministic; no wall-clock in pipeline)
TOKEN = (dotenv_values(REPO / ".env").get("SOCRATA_APP_TOKEN") or "").strip()
HDR = {"X-App-Token": TOKEN} if TOKEN else {}
BASE = "https://data.cityofnewyork.us/resource"
META = "https://data.cityofnewyork.us/api/views"
PAGE = 50000
STORAGE_BUDGET_BYTES = 2_000_000_000  # Rule 9: repo tabular total <= 2 GB
random.seed(42)  # Rule 10 (no sampling occurs in S1; seed set for consistency)

# ---- Frozen filters (SoQL upper()+like is the case-insensitive form of ILIKE) ----
HPD_TEXT = ("(upper(novdescription) like '%ADEQUATE SUPPLY OF HEAT%' "
            "or upper(novdescription) like '%PROVIDE HOT WATER AT%')")
HPD_WHERE_WFF = f"{HPD_TEXT} and class in ('B','C') and inspectiondate >= '2017-10-01'"
C311_WHERE = ("complaint_type in ('HEAT/HOT WATER','Heat/Hot Water') "
              "and created_date >= '2019-06-01'")

# ---- Rule 5: dataset IDs to verify live (name keyword must appear in live name) ----
DATASETS = {
    "erm2-nwe9": "311 Service Requests from 2020",
    "76ig-c548": "311 Service Requests from 2010 to 2019",
    "wvxf-dwi5": "Housing Maintenance Code Violations",
    "tesw-yqqr": "Multiple Dwelling Registrations",
    "feu5-w2e2": "Registration Contacts",
    "64uk-42ks": "Primary Land Use Tax Lot Output",
    # R-A = ADMIT (model_spec.md Amendment 1, 2026-07-16; relayed by LEAD):
    "ygpa-z7cr": "Housing Maintenance Code Complaints and Problems",
}

# ---- Spine comparison target: WFF committed report, outputs/checkpoints/
# _s1b_frozen_labels.json in the read-only WFF repo (frozen denominator ruling,
# G1 2026-07-14). Values transcribed verbatim; any divergence of the imported
# artifact from these numbers is a Rule-9 stop.
WFF_SPINE_EXPECT = {
    "grid_rows": 1_624_255,
    "n_universe": 181_863,
    "per_season": {  # season start year -> (denom rows, label_c positives)
        2017: (178_503, 4_725), 2018: (179_143, 4_647), 2019: (179_767, 4_013),
        2020: (180_157, 4_072), 2021: (180_547, 5_057), 2022: (181_087, 6_021),
        2023: (181_470, 7_764), 2024: (181_718, 7_730), 2025: (181_863, 8_897),
    },
}
SPINE_SHA256 = "1c9be931c222fa852aeeb7dbaa1a3ef6dad996e0deac899069c1143b573974eb"


def _get(url: str):
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=180) as r:
                return json.load(r)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            if attempt == 5:
                raise
            time.sleep(2 ** attempt)


def _guard_storage() -> int:
    tab = sum(f.stat().st_size for d in (REPO / "data", IMPORTS)
              for f in d.rglob("*") if f.is_file())
    if tab > STORAGE_BUDGET_BYTES:
        raise RuntimeError(f"STORAGE BREACH: data/+imports/ at {tab/1e9:.2f} GB > 2 GB — HALT (Rule 9).")
    return tab


def verify_ids() -> dict:
    """Rule 5: live metadata check per dataset ID. Name-keyword mismatch = HARD STOP."""
    out = {}
    for ds, expect in DATASETS.items():
        meta = _get(f"{META}/{ds}.json")
        name = meta.get("name", "")
        if expect.lower() not in name.lower():
            raise RuntimeError(f"ID MISMATCH for {ds}: live name {name!r} lacks "
                               f"{expect!r} — HARD STOP (Rule 9).")
        upd = meta.get("rowsUpdatedAt")
        upd_dt = (pd.Timestamp(upd, unit="s", tz="UTC").date().isoformat()
                  if isinstance(upd, (int, float)) else None)
        out[ds] = dict(name=name, rows_updated=upd_dt, verified=TODAY)
        print(f"[verify] {ds}: {name!r} (rows updated {upd_dt}) OK")
    return out


def pull(name: str, dataset: str, select: str, where: str | None = None,
         group: str | None = None, order: str = ":id") -> pd.DataFrame:
    """Server-side filtered, paged, parquet-cached pull. Idempotent."""
    cache = RAW / f"{name}.parquet"
    if cache.exists() and not FORCE:
        df = pd.read_parquet(cache)
        print(f"[cache] {name}: {len(df):,} rows  ({cache})")
        return df
    expected_cols = {c.strip().split(" as ")[-1].strip() for c in select.lower().split(",")}
    rows, offset = [], 0
    while True:
        params = {"$select": select, "$limit": PAGE, "$offset": offset, "$order": order}
        if where:
            params["$where"] = where
        if group:
            params["$group"] = group
        batch = _get(f"{BASE}/{dataset}.json?" + urllib.parse.urlencode(params))
        if batch and not {c.lower() for c in batch[0]}.issubset(expected_cols):
            raise RuntimeError(f"SCHEMA SURPRISE for {name}: got {sorted(batch[0])} — "
                               f"HARD STOP (Rule 9).")
        if not batch:
            break
        rows.extend(batch)
        offset += PAGE
        print(f"  {name}: pulled {len(rows):,} ...", flush=True)
        if len(rows) * 200 > STORAGE_BUDGET_BYTES:  # coarse in-flight projection guard
            raise RuntimeError(f"STORAGE GUARD: {name} projects over 2 GB — HARD STOP (Rule 9).")
        if len(batch) < PAGE:
            break
    if not rows:
        raise RuntimeError(f"EMPTY PULL for {name} ({dataset}) — HARD STOP, no placeholder (Rule 1).")
    df = pd.DataFrame(rows)
    df = df.reindex(columns=[c.strip().split(" as ")[-1].strip() for c in select.split(",")])
    df.to_parquet(cache, index=False)
    _guard_storage()
    print(f"[pull] {name}: {len(df):,} rows -> {cache}")
    return df


def refresh_311_union() -> dict:
    """Amendment-3 union, refreshed to pull date, with BOTH seam diagnostics."""
    C311_SELECT = "unique_key,created_date,closed_date,bbl,complaint_type,status"
    cur = pull("c311_current_refresh", "erm2-nwe9", C311_SELECT, C311_WHERE)
    arc = pull("c311_heat_complaints_archive_2019", "76ig-c548", C311_SELECT, C311_WHERE)

    full = pd.concat([arc, cur], ignore_index=True)
    n_pre = len(full)
    full = (full.drop_duplicates(subset="unique_key", keep="first")
            .sort_values(["created_date", "unique_key"], kind="mergesort")
            .reset_index(drop=True))
    n_dedupe = n_pre - len(full)
    print(f"[union] archive {len(arc):,} + current {len(cur):,} = {n_pre:,}; "
          f"duplicates on unique_key removed: {n_dedupe:,}; union rows: {len(full):,}")

    null_bbl = full["bbl"].isna() | (full["bbl"].astype(str).str.strip() == "")
    n_null = int(null_bbl.sum())
    pct_null = 100.0 * n_null / len(full)
    print(f"[null-bbl] {n_null:,} of {len(full):,} union rows ({pct_null:.3f}%) null/empty bbl "
          f"-> EXCLUDED from deliverable (exclusion logged; raw caches retained).")
    deliv = RAW / "c311_heat_complaints.parquet"
    full[~null_bbl].reset_index(drop=True).to_parquet(deliv, index=False)

    day = pd.to_datetime(full["created_date"], errors="coerce").dt.date.astype(str)

    # Seam A — archive boundary (2019-12-31 -> 2020-01-01), reported never smoothed.
    seam_a = day[(day >= "2019-12-25") & (day <= "2020-01-07")].value_counts().sort_index()
    print("[seam A] daily union counts 2019-12-25..2020-01-07:")
    for d, n in seam_a.items():
        print(f"  {d}: {n}")

    # Seam B — old/new refresh edge: refreshed erm2-nwe9 pull vs the untouched
    # phase-0 erm2-nwe9 pull (same dataset, same filter; archive rows are out of
    # scope here — the phase-0 pull starts 2020-01-01 by dataset re-scope).
    old = pd.read_parquet(RAW / "c311_heat_complaints_full.parquet")
    old_max = pd.to_datetime(old["created_date"], errors="coerce").max()
    edge_lo = (old_max - pd.Timedelta(days=13)).date().isoformat()
    old_day = pd.to_datetime(old["created_date"], errors="coerce").dt.date.astype(str)
    cur_day = pd.to_datetime(cur["created_date"], errors="coerce").dt.date.astype(str)
    new_win = cur_day[(cur_day >= edge_lo)].value_counts().sort_index()
    old_win = old_day[(old_day >= edge_lo)].value_counts().sort_index()
    edge = pd.DataFrame({"old_pull": old_win, "new_pull": new_win}).fillna(0).astype(int)
    print(f"[seam B] daily counts from {edge_lo} (phase-0 pull max created {old_max}):")
    print(edge.to_string())
    old_keys = set(old["unique_key"])
    new_keys_le = set(cur.loc[(cur_day <= old_max.date().isoformat()).values, "unique_key"])
    late_arrivals = len(new_keys_le - old_keys)
    disappeared = len(old_keys - set(cur["unique_key"]))
    print(f"[seam B] rows <= old max date new-not-in-old (late arrivals): {late_arrivals:,}; "
          f"old-not-in-new (disappeared): {disappeared:,}")
    if disappeared > 0.01 * len(old):
        raise RuntimeError(f"REFRESH SURPRISE: {disappeared:,} previously pulled rows vanished "
                           f"(>1% of phase-0 pull) — HARD STOP (Rule 9).")

    dts = pd.to_datetime(full["created_date"], errors="coerce")
    return dict(
        current_rows=len(cur), archive_rows=len(arc), pre_dedupe=n_pre,
        dedupe_removed=int(n_dedupe), union_rows=len(full),
        null_bbl=n_null, null_bbl_pct=round(pct_null, 4),
        deliverable_rows=int((~null_bbl).sum()),
        min_created=str(dts.min()), max_created=str(dts.max()),
        seam_archive_daily={k: int(v) for k, v in seam_a.items()},
        seam_refresh_daily={k: {"old": int(edge.loc[k, "old_pull"]),
                                "new": int(edge.loc[k, "new_pull"])} for k in edge.index},
        refresh_late_arrivals=late_arrivals, refresh_disappeared=disappeared,
        phase0_pull_max_created=str(old_max),
    )


# ---- ygpa-z7cr (R-A = ADMIT, spec Amendment 1): HPD Complaints and Problems,
# heat/hot-water problems only, floor aligned with the §2 311 union floor.
# Capacities: feature family 7 (distinct-apartments-complaining, masked) +
# the §10 criterion-3 HSP screen. NEVER the reporting-head likelihood
# (Amendment-1 non-load-bearing boundary — binds downstream consumers; this is
# a raw cache only). Single live heat major verified 2026-07-16:
# 'HEAT/HOT WATER' (case-robust upper() match used as the whitelist).
#
# OPERATIONAL SPLIT (Rule-9-driven mechanic, NOT a data decision — Ayur ruling
# (b) relayed by LEAD 2026-07-16 after two external background-task kills):
# the pull runs FOREGROUND in bounded date-split parts on received_date
# (half-open intervals, jointly exhaustive over the floor..present range,
# mutually disjoint by construction). Each part is parquet-cached on
# completion (resumable); the deliverable cache is assembled deterministically
# from the parts. Part sizing fits the 600-second foreground call ceiling at
# measured throughput (~66k rows/min) — server-side year counts probed
# 2026-07-16: 2019=96,409 / 2020=164,644 / 2021=200,169 / 2022=270,629 /
# 2023=230,610 / 2024=267,542 / 2025=318,652 / 2026=206,296, total 1,754,951.
HPDC_SELECT = ("unique_key,problem_id,complaint_id,building_id,bbl,borough,block,lot,"
               "apartment,unit_type,space_type,type,major_category,minor_category,"
               "problem_code,complaint_status,problem_status,received_date,"
               "problem_status_date,problem_duplicate_flag,complaint_anonymous_flag")
HPDC_BASE_WHERE = "upper(major_category) = 'HEAT/HOT WATER'"
HPDC_PARTS = [  # (part, lo inclusive, hi exclusive; hi=None -> open-ended)
    (1, "2019-06-01", "2021-01-01"),
    (2, "2021-01-01", "2022-01-01"),
    (3, "2022-01-01", "2023-01-01"),
    (4, "2023-01-01", "2024-01-01"),
    (5, "2024-01-01", "2025-01-01"),
    (6, "2025-01-01", "2026-01-01"),
    (7, "2026-01-01", None),
]


def pull_hpdc_part(part: int) -> pd.DataFrame:
    n, lo, hi = HPDC_PARTS[part - 1]
    assert n == part
    where = f"{HPDC_BASE_WHERE} and received_date >= '{lo}'"
    if hi:
        where += f" and received_date < '{hi}'"
    return pull(f"hpd_complaints_heat_part{part}", "ygpa-z7cr", HPDC_SELECT, where)


def pull_hpdc_parts() -> pd.DataFrame:
    """Assemble the ygpa-z7cr deliverable cache from the part caches.
    All parts must already exist (pulled via --hpdc-part N bounded calls) or be
    pullable within this run; the deliverable is rebuilt deterministically."""
    parts = [pull_hpdc_part(p) for p, _, _ in HPDC_PARTS]
    hpdc = pd.concat(parts, ignore_index=True)
    n_dupe = int(hpdc.duplicated(subset="problem_id").sum())
    print(f"[hpdc] parts {'+'.join(str(len(p)) for p in parts)} = {len(hpdc):,}; "
          f"duplicate problem_id across parts: {n_dupe:,} (disjoint intervals -> expect 0)")
    if n_dupe:
        raise RuntimeError(f"HPDC PART OVERLAP: {n_dupe:,} duplicate problem_id across "
                           f"supposedly disjoint date parts — HARD STOP (Rule 9).")
    hpdc = (hpdc.sort_values(["received_date", "problem_id"], kind="mergesort")
            .reset_index(drop=True))
    hpdc.to_parquet(RAW / "hpd_complaints_heat.parquet", index=False)
    _guard_storage()
    print(f"[hpdc] deliverable hpd_complaints_heat.parquet: {len(hpdc):,} rows "
          f"(assembled from {len(HPDC_PARTS)} part caches)")
    return hpdc


def verify_spine() -> dict:
    """R4 spine (read-only import): sha256 + season coverage vs WFF committed report."""
    p = IMPORTS / "building_season_labels.parquet"
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    if sha != SPINE_SHA256:
        raise RuntimeError(f"SPINE INTEGRITY: sha256 {sha} != PROVENANCE {SPINE_SHA256} — "
                           f"HARD STOP (Rule 9).")
    spine = pd.read_parquet(p)
    if list(spine.columns) != ["bbl_n", "season", "label_c", "label_bc"]:
        raise RuntimeError(f"SPINE SCHEMA SURPRISE: {list(spine.columns)} — HARD STOP (Rule 9).")
    seasons = sorted(spine["season"].unique().tolist())
    if seasons != list(range(2017, 2026)):
        raise RuntimeError(f"SPINE SEASON COVERAGE: {seasons} != 2017..2025 — HARD STOP (Rule 9).")
    if len(spine) != WFF_SPINE_EXPECT["grid_rows"]:
        raise RuntimeError(f"SPINE ROWS: {len(spine):,} != committed "
                           f"{WFF_SPINE_EXPECT['grid_rows']:,} — HARD STOP (Rule 9).")
    per, mismatches = {}, []
    for sy, (denom_exp, pos_exp) in WFF_SPINE_EXPECT["per_season"].items():
        sub = spine[spine["season"] == sy]
        denom, pos = len(sub), int(sub["label_c"].sum())
        per[f"{sy}-{str(sy+1)[2:]}"] = dict(rows=denom, pos_c=pos,
                                            expected_rows=denom_exp, expected_pos=pos_exp,
                                            match=(denom == denom_exp and pos == pos_exp))
        if not (denom == denom_exp and pos == pos_exp):
            mismatches.append(sy)
        print(f"[spine] {sy}-{str(sy+1)[2:]}: rows {denom:,} (exp {denom_exp:,}), "
              f"pos_c {pos:,} (exp {pos_exp:,}) "
              f"{'OK' if denom == denom_exp and pos == pos_exp else 'MISMATCH'}")
    if mismatches:
        raise RuntimeError(f"SPINE MISMATCH vs WFF committed report for seasons {mismatches} — "
                           f"HARD STOP (Rule 9).")
    n_bbl = int(spine["bbl_n"].nunique())
    print(f"[spine] sha256 OK; {len(spine):,} rows; {n_bbl:,} distinct BBLs; "
          f"seasons 2017-18..2025-26 all match the committed report.")
    return dict(sha256_ok=True, rows=len(spine), distinct_bbl=n_bbl, per_season=per)


def main() -> int:
    # Bounded-call mode (Ayur ruling (b)): pull exactly one ygpa-z7cr date part,
    # then exit. Used to keep each foreground call inside the 600 s ceiling.
    if "--hpdc-part" in sys.argv:
        part = int(sys.argv[sys.argv.index("--hpdc-part") + 1])
        print(f"=== S1 pull ({TODAY}) — hpdc part {part} only ===")
        pull_hpdc_part(part)
        return 0

    print(f"=== S1 pull ({TODAY}) ===")
    ids = verify_ids()

    union = refresh_311_union()

    viol = pull("hpd_violations_wff", "wvxf-dwi5",
                "violationid,buildingid,registrationid,bbl,boroid,block,lot,class,"
                "novdescription,inspectiondate,approveddate,novissueddate,currentstatus",
                HPD_WHERE_WFF)
    ctx = pull("hpd_viol_context_by_year", "wvxf-dwi5",
               "bbl,class,date_extract_y(inspectiondate) as yr,count(1) as n",
               where="inspectiondate >= '2014-06-01' AND bbl IS NOT NULL",
               group="bbl,class,date_extract_y(inspectiondate)", order="bbl,class,yr")
    if ctx["yr"].dtype == object or ctx["n"].dtype == object:  # mirror WFF s1c dtypes
        ctx["yr"] = pd.to_numeric(ctx["yr"], errors="coerce").astype("Int64")
        ctx["n"] = pd.to_numeric(ctx["n"], errors="coerce").astype("Int64")
        ctx.to_parquet(RAW / "hpd_viol_context_by_year.parquet", index=False)
    reg = pull("hpd_registrations", "tesw-yqqr",
               "registrationid,buildingid,boroid,boro,block,lot,bin,housenumber,streetname,"
               "zip,lastregistrationdate,registrationenddate")
    con = pull("hpd_registration_contacts", "feu5-w2e2",
               "registrationcontactid,registrationid,type,contactdescription,"
               "corporationname,firstname,lastname,businesshousenumber,"
               "businessstreetname,businesszip")
    pluto = pull("pluto_full", "64uk-42ks",
                 "bbl,borough,block,lot,yearbuilt,numfloors,unitsres,unitstotal,"
                 "bldgclass,landuse,zipcode")

    hpdc = pull_hpdc_parts()

    spine = verify_spine()

    # ---- summary stats ----
    viol_dt = pd.to_datetime(viol["inspectiondate"], errors="coerce")
    reg_bbl = pd.to_numeric(
        pd.to_numeric(reg["boroid"], errors="coerce").astype("Int64").astype(str)
        + pd.to_numeric(reg["block"], errors="coerce").astype("Int64").astype(str).str.zfill(5)
        + pd.to_numeric(reg["lot"], errors="coerce").astype("Int64").astype(str).str.zfill(4),
        errors="coerce")
    tab_bytes = _guard_storage()
    stats = dict(
        pull_date=TODAY, dataset_ids=ids, c311_union=union,
        viol_wff_rows=len(viol),
        viol_wff_class_B=int((viol["class"] == "B").sum()),
        viol_wff_class_C=int((viol["class"] == "C").sum()),
        viol_wff_null_bbl=int((viol["bbl"].isna()
                               | (viol["bbl"].astype(str).str.strip() == "")).sum()),
        viol_wff_min_insp=str(viol_dt.min()), viol_wff_max_insp=str(viol_dt.max()),
        ctx_groups=len(ctx),
        ctx_classes=sorted(ctx["class"].dropna().unique().tolist()),
        ctx_yr_min=int(pd.to_numeric(ctx["yr"]).min()),
        ctx_yr_max=int(pd.to_numeric(ctx["yr"]).max()),
        reg_rows=len(reg), reg_distinct_bbl=int(reg_bbl.nunique()),
        contacts_rows=len(con), pluto_rows=len(pluto),
        hpdc_rows=len(hpdc),
        hpdc_null_bbl=int((hpdc["bbl"].isna()
                           | (hpdc["bbl"].astype(str).str.strip() == "")).sum()),
        hpdc_null_apartment=int((hpdc["apartment"].isna()
                                 | (hpdc["apartment"].astype(str).str.strip() == "")).sum()),
        hpdc_dup_flag_counts={str(k): int(v) for k, v in
                              hpdc["problem_duplicate_flag"].value_counts(dropna=False).items()},
        hpdc_min_received=str(pd.to_datetime(hpdc["received_date"], errors="coerce").min()),
        hpdc_max_received=str(pd.to_datetime(hpdc["received_date"], errors="coerce").max()),
        pluto_null=dict((c, int(pluto[c].isna().sum()))
                        for c in ("yearbuilt", "numfloors", "unitstotal", "bldgclass", "borough")),
        spine=spine, tabular_bytes=tab_bytes, tabular_mb=round(tab_bytes / 1e6, 1),
    )
    (REPO / "data" / "s1_stats.json").write_text(json.dumps(stats, indent=2))
    print("\n[done] stats -> data/s1_stats.json")
    print(json.dumps({k: v for k, v in stats.items()
                      if k not in ("dataset_ids", "c311_union", "spine")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
