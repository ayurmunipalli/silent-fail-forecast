"""P1 — complaint-granularity pull (phase0_probe.md §2; CLAUDE.md Rules 1,2,5,6,7,8a).

Idempotent, server-side filtered, paged, parquet-cached. Rerun with
`.venv/bin/python src/p1_pull.py` (add --force to re-pull raw). NEVER fabricates:
an empty pull or schema surprise raises and stops (Rules 1, 9).

Sources (all verified live 2026-07-16 against data.cityofnewyork.us, Rule 5):
  erm2-nwe9  311 Service Requests from 2020 to Present   (per-complaint rows, 2020+)
  76ig-c548  311 Service Requests from 2010 to 2019      (archive: 2019-06-01..2019-12-31 tail)
  wvxf-dwi5  Housing Maintenance Code Violations         (fresh pull, frozen whitelist)
  64uk-42ks  Primary Land Use Tax Lot Output (PLUTO)     (bbl + unitstotal)

311 ARCHIVE UNION (phase0_probe.md Amendment 3, APPROVED 2026-07-16): erm2-nwe9 was
re-scoped by NYC OpenData to 2020-01-01+, so the §2 floor created_date >= '2019-06-01'
returns zero 2019 rows from it. Per Amendment 3 the deliverable is the UNION of
76ig-c548 (same whitelist verbatim, same six §2 columns) with erm2-nwe9, restoring
the 2019-06-01 floor, deduplicated on unique_key with the dedupe count logged.

FROZEN VIOLATION WHITELIST — ported VERBATIM from winter-fail-forecast
src/s1_data_pull.py (itself verbatim from cross-season-heat phase0_memo.md §1):
    (novdescription ILIKE '%ADEQUATE SUPPLY OF HEAT%'   -- §27-2029 heat supply failure
     OR novdescription ILIKE '%PROVIDE HOT WATER AT%')   -- §27-2031 hot water failure
    AND class IN ('B','C')
CONFLICT FLAGGED (not resolved here): probe doc §3 gates on class-C rows; the
verbatim whitelist is class IN ('B','C'). We pull the B/C SUPERSET with the
`class` column retained so P2 (A-GATE) applies the §3 class-C restriction
explicitly. No rows are dropped here.
"""
from __future__ import annotations
import sys, json, time, random, urllib.parse, urllib.request, urllib.error
from pathlib import Path

import pandas as pd
from dotenv import dotenv_values

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

FORCE = "--force" in sys.argv
TOKEN = (dotenv_values(REPO / ".env").get("SOCRATA_APP_TOKEN") or "").strip()
HDR = {"X-App-Token": TOKEN} if TOKEN else {}
BASE = "https://data.cityofnewyork.us/resource"
PAGE = 50000
STORAGE_BUDGET_BYTES = 2_000_000_000  # Rule 6
random.seed(42)  # Rule 7 (no sampling occurs in P1; seed set for consistency)

# ---- Frozen filters (SoQL upper()+like is the case-insensitive form of ILIKE) ----
HPD_TEXT = ("(upper(novdescription) like '%ADEQUATE SUPPLY OF HEAT%' "
            "or upper(novdescription) like '%PROVIDE HOT WATER AT%')")
HPD_WHERE = f"{HPD_TEXT} and class in ('B','C') and inspectiondate >= '2019-06-01'"
# 311 whitelist + floor, verbatim from phase0_probe.md §2. No bbl-null filter at pull.
C311_WHERE = ("complaint_type in ('HEAT/HOT WATER','Heat/Hot Water') "
              "and created_date >= '2019-06-01'")


def _get(url: str):
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=180) as r:
                return json.load(r)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            if attempt == 5:
                raise
            time.sleep(2 ** attempt)


def _guard_storage():
    used = sum(f.stat().st_size for f in RAW.rglob("*") if f.is_file())
    if used > STORAGE_BUDGET_BYTES:
        raise RuntimeError(f"STORAGE BREACH: data/raw at {used/1e9:.2f} GB > 2 GB — HALT (Rule 6).")
    return used


def pull(name: str, dataset: str, select: str, where: str | None = None) -> pd.DataFrame:
    """Server-side filtered, paged, parquet-cached pull. Idempotent."""
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
        print(f"  {name}: pulled {len(rows):,} ...", flush=True)
        if len(batch) < PAGE:
            break
    if not rows:
        raise RuntimeError(f"EMPTY PULL for {name} ({dataset}) — HARD STOP, no placeholder (Rule 1).")
    df = pd.DataFrame(rows)
    # normalize column order to the select list (Socrata omits all-null cols per row)
    df = df.reindex(columns=select.split(","))
    df.to_parquet(cache, index=False)
    _guard_storage()
    print(f"[pull] {name}: {len(df):,} rows -> {cache}")
    return df


def main() -> int:
    print("=== P1 pull ===")
    # ---------- 311 per-complaint rows (probe doc §2 + Amendment 3 union) ----------
    C311_SELECT = "unique_key,created_date,closed_date,bbl,complaint_type,status"
    c311_cur = pull("c311_heat_complaints_full", "erm2-nwe9", C311_SELECT, C311_WHERE)
    c311_arc = pull("c311_heat_complaints_archive_2019", "76ig-c548", C311_SELECT, C311_WHERE)

    # Union, dedupe on unique_key (Amendment 3: dedupe count LOGGED), deterministic order.
    c311_full = pd.concat([c311_arc, c311_cur], ignore_index=True)
    n_pre_dedupe = len(c311_full)
    c311_full = (c311_full.drop_duplicates(subset="unique_key", keep="first")
                 .sort_values(["created_date", "unique_key"], kind="mergesort")
                 .reset_index(drop=True))
    n_dedupe = n_pre_dedupe - len(c311_full)
    print(f"[union] archive {len(c311_arc):,} + current {len(c311_cur):,} = {n_pre_dedupe:,}; "
          f"duplicates on unique_key removed: {n_dedupe:,}; union rows: {len(c311_full):,}")

    # Null-bbl accounting (§2: pull, COUNT, log, then exclude with the exclusion logged)
    null_bbl = c311_full["bbl"].isna() | (c311_full["bbl"].astype(str).str.strip() == "")
    n_null = int(null_bbl.sum())
    pct_null = 100.0 * n_null / len(c311_full)
    print(f"[null-bbl] {n_null:,} of {len(c311_full):,} union rows ({pct_null:.3f}%) have null/empty "
          f"bbl -> EXCLUDED from c311_heat_complaints.parquet (exclusion logged; raw pulls retained).")
    deliv = RAW / "c311_heat_complaints.parquet"
    # deliverable is always rebuilt deterministically from the cached pulls (idempotent)
    c311_full[~null_bbl].reset_index(drop=True).to_parquet(deliv, index=False)
    c311 = pd.read_parquet(deliv)

    # Seam continuity diagnostic (reported, never smoothed): daily counts around the
    # 2019-12-31 -> 2020-01-01 archive/current boundary.
    d = pd.to_datetime(c311_full["created_date"], errors="coerce").dt.date.astype(str)
    seam = d[(d >= "2019-12-25") & (d <= "2020-01-07")].value_counts().sort_index()
    print("[seam] daily union counts 2019-12-25..2020-01-07:")
    for day, n in seam.items():
        print(f"  {day}: {n}")

    # ---------- HPD violations, frozen whitelist verbatim (fresh pull) ----------
    viol = pull("hpd_violations_heat", "wvxf-dwi5",
                "violationid,bbl,class,novdescription,inspectiondate,"
                "novissueddate,approveddate,currentstatus",
                HPD_WHERE)

    # ---------- PLUTO: bbl + unitstotal ----------
    pluto = pull("pluto_units", "64uk-42ks", "bbl,unitstotal")

    # ---------- stats ----------
    used = _guard_storage()
    c311_dates = pd.to_datetime(c311_full["created_date"], errors="coerce")
    viol_dates = pd.to_datetime(viol["inspectiondate"], errors="coerce")
    stats = dict(
        c311_current_rows=len(c311_cur), c311_archive_rows=len(c311_arc),
        c311_dedupe_removed=int(n_dedupe),
        c311_seam_daily={k: int(v) for k, v in seam.items()},
        c311_full_rows=len(c311_full), c311_null_bbl=n_null,
        c311_null_bbl_pct=round(pct_null, 4), c311_deliverable_rows=len(c311),
        c311_min_created=str(c311_dates.min()), c311_max_created=str(c311_dates.max()),
        viol_rows=len(viol),
        viol_class_B=int((viol["class"] == "B").sum()),
        viol_class_C=int((viol["class"] == "C").sum()),
        viol_null_bbl=int((viol["bbl"].isna() | (viol["bbl"].astype(str).str.strip() == "")).sum()),
        viol_min_insp=str(viol_dates.min()), viol_max_insp=str(viol_dates.max()),
        pluto_rows=len(pluto),
        pluto_null_unitstotal=int(pluto["unitstotal"].isna().sum()),
        raw_bytes=used, raw_mb=round(used / 1e6, 1),
    )
    (RAW.parent / "p1_stats.json").write_text(json.dumps(stats, indent=2))
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
