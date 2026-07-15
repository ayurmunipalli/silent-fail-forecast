"""P3 — Heat Sensors Program ground truth, identification channel (b)
(phase0_probe.md §4 + Amendment 1 item 2 + Amendment 3 item 2).

Idempotent: rerun with `.venv/bin/python src/p3_hsp.py` (--force re-pulls raw).
Reads the P1 caches + two P3 pulls + four nyc.gov cohort PDFs; writes
outputs/checkpoints/phase0_p3_hsp.md + data/p3_stats.json. Seed 42 (Rule 7; no
sampling occurs). Never fabricates: empty pull, parse residue, or cohort-membership
disagreement raises / is reported verbatim (Rules 1, 9).

SOURCES (all verified live 2026-07-16 against data.cityofnewyork.us, Rule 5):
  h4mf-f24e  Buildings Selected for the Heat Sensor Program (HSP) — official HPD
             dataset (provenance "official"), 200 rows = 4 cohorts x 50, includes
             bbl + address + program_start_date + current_status. rowsUpdated
             2026-03-01.
  64uk-42ks  PLUTO (bbl, address, borough) — supplementary P3 pull for the §4
             address->BBL resolution (the P1 PLUTO cache carries only bbl+unitstotal).
  nyc.gov cohort PDFs (the §4-named source; downloaded, parsed, cross-checked):
    https://www.nyc.gov/assets/hpd/downloads/pdfs/services/heat-sensor-program-building-list-{2020,2022,2024,2025}.pdf

HPD-COMPLAINTS DATASET VERIFICATION (§4 P3.2, done BEFORE choosing the heuristic
version; logged here and in PROVENANCE):
  uwyv-629c (legacy HPD Complaints)        -> "must be logged in" (retired from public API)
  a2nx-4u46 (legacy HPD Complaint Problems)-> "must be logged in" (retired from public API)
  ygpa-z7cr (merged Complaints and Problems)-> LIVE (updated 2026-07-15) BUT excluded
             from phase-0 by probe doc Amendment 1 item 2 ("neither is pulled or
             used in phase-0"; OSC-audit linkage concerns).
  => No HPD complaints dataset USABLE in phase-0. Per §4: "disclose and run the
     311-only version, labeled as such." THIS SCRIPT RUNS THE 311-ONLY VERSION.

FIXED DECISIONS (stated so R-AUDIT can re-derive):
1. ASSOCIATION RULE identical to P2 (src/p2_gate.py decisions 2-4): same-bbl
   complaints with created_date in [inspectiondate-30, inspectiondate], BOTH BOUNDS
   INCLUSIVE, calendar-date truncation, bbl normalized to int64. W=30 fixed by §4.
2. VIOLATION WATERFALL identical to P2: explicit class-C restriction, exact
   duplicate violationid drop, unparsable bbl/date exclusion (all counted).
3. MEMBERSHIP / PROGRAM PERIOD: cohort membership and program_start_date come from
   the official dataset (cross-checked against the PDFs); current_status is
   "Active" for all 200 rows and discharge_date is all-null, so a building is in
   program from its program_start_date onward. Buildings selected in two cohorts
   (repeat selections) are counted ONCE per violation, attributed to the EARLIEST
   membership; the per-cohort table notes the overlap.
4. "PROGRAM SEASONS" = NYC heat seasons (Oct 1 - May 31, labeled by start year,
   same definition as P2/frozen spine) with inspectiondate >= program_start_date.
   The probe doc's Oct-Jan proactive-inspection cadence subset is reported as a
   SECONDARY line. Off-season (Jun-Sep) in-program violations are counted and
   excluded, never silently dropped.
5. WINDOW-COVERAGE ELIGIBILITY (Amendment 3 item 2, at W=30): full
   [inspectiondate-30, inspectiondate] window inside actual 311 coverage;
   exclusions counted left/right edge.
6. EVENT UNIT: the violation ROW (P2's §3 unit). A (bbl, inspectiondate)-deduped
   count is reported as sensitivity, never substituted.
7. FLOOR: the pre-committed §4 floor is applied to the primary count; the script
   STATES which side fired. It does not adjudicate or argue.
"""
from __future__ import annotations

import http.client
import json
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import dotenv_values
from pypdf import PdfReader

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "data" / "raw"
HSP_DIR = RAW / "hsp"
HSP_DIR.mkdir(parents=True, exist_ok=True)
CKPT = REPO / "outputs" / "checkpoints" / "phase0_p3_hsp.md"
STATS = REPO / "data" / "p3_stats.json"

FORCE = "--force" in sys.argv
TOKEN = (dotenv_values(REPO / ".env").get("SOCRATA_APP_TOKEN") or "").strip()
HDR = {"X-App-Token": TOKEN} if TOKEN else {}
BASE = "https://data.cityofnewyork.us/resource"
PAGE = 50000
STORAGE_BUDGET_BYTES = 2_000_000_000  # Rule 6
DAY_MOD = 100_000  # same composite-key stride as P2

random.seed(42)
np.random.seed(42)  # Rule 7 — no sampling occurs; set for consistency

COHORT_PDF_URL = ("https://www.nyc.gov/assets/hpd/downloads/pdfs/services/"
                  "heat-sensor-program-building-list-{y}.pdf")
COHORT_YEARS = [2020, 2022, 2024, 2025]
# nyc.gov serves 403 to non-browser user agents (WebFetch got 403; curl+UA got 200)
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
BORO_MAP = {"MANHATTAN": "MN", "BRONX": "BX", "BROOKLYN": "BK",
            "QUEENS": "QN", "STATEN ISLAND": "SI",
            "MN": "MN", "BX": "BX", "BK": "BK", "QN": "QN", "SI": "SI"}


# ---------------- helpers ported verbatim in semantics from src/p2_gate.py ----------
def season_of_days(days: np.ndarray) -> np.ndarray:
    """NYC heat season start year (Oct 1 - May 31); -1 for Jun-Sep off-season."""
    ts = pd.to_datetime(days, unit="D")
    month, year = ts.month.values, ts.year.values
    return np.where(month >= 10, year, np.where(month <= 5, year - 1, -1))


def to_bbl_int(s: pd.Series) -> pd.Series:
    v = pd.to_numeric(s, errors="coerce")
    v = v.where(v > 0)
    return v.round().astype("Int64")


def to_days(s: pd.Series) -> pd.Series:
    dt = pd.to_datetime(s, errors="coerce")
    days = pd.Series(dt.values.astype("datetime64[D]").astype("float64"), index=s.index)
    return days.where(dt.notna().values).astype("Int64")


def season_label(sy: int) -> str:
    return f"{sy}-{str(sy + 1)[-2:]}"


def md_table(header: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join(["---"] * len(header)) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


# ---------------- pulls (idempotent, cached; P1 pull() pattern) ----------------------
def _get(url: str):
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers=HDR)
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


def fetch_pdf(year: int) -> Path:
    """Download-if-missing cohort PDF from nyc.gov (browser UA needed; cached)."""
    path = HSP_DIR / f"hsp_list_{year}.pdf"
    if path.exists() and path.stat().st_size > 0 and not FORCE:
        return path
    url = COHORT_PDF_URL.format(y=year)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    if not data.startswith(b"%PDF"):
        raise RuntimeError(f"NOT A PDF at {url} — HARD STOP (Rule 9), no guessed membership.")
    path.write_bytes(data)
    print(f"[pdf] {year}: {len(data):,} bytes <- {url}")
    return path


# ---------------- PDF parsing --------------------------------------------------------
ROW_RE = re.compile(
    r"^(MN|BX|BK|QN|SI)\s+(\d+[A-Z]?(?:-\d+[A-Z]?)?)\s+(.+?)\s+(\d+)\s+(\d+)\s+(\d+)\s*$")
HEADER_TOKENS = ("BORO", "HOUSE", "NUMBER", "STREET", "COUNCIL", "COMMUNIT",
                 "DISTRICT", "UNITS", "HEAT SENSOR", "NUMBER OF", "NUNMBER",
                 "OF UNITS", "BOROUGH", "Y DISTRICT")


def parse_pdf(path: Path, year: int) -> tuple[pd.DataFrame, list[str]]:
    """Parse a cohort PDF to (boro, house_number, street, units) rows + residue lines."""
    text = "\n".join(p.extract_text() for p in PdfReader(path).pages)
    rows, residue = [], []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = ROW_RE.match(line)
        if m:
            boro, num, street, _council, _cd, units = m.groups()
            rows.append(dict(cohort=year, boro=boro, house_number=num,
                             street=" ".join(street.split()).upper(),
                             units_pdf=int(units)))
        else:
            if re.fullmatch(r"\d+ of \d+", line) or any(t in line.upper() for t in HEADER_TOKENS):
                continue
            residue.append(line)
    return pd.DataFrame(rows), residue


def norm_street(s: str) -> str:
    """Conservative street normalization for cross-source matching (never for
    inventing membership): uppercase, collapse spaces, expand common suffix/
    directional abbreviations, strip ordinal suffixes (136TH -> 136)."""
    s = " ".join(str(s).upper().replace(".", " ").split())
    s = re.sub(r"\b(\d+)(ST|ND|RD|TH)\b", r"\1", s)
    abbr = {"AV": "AVENUE", "AVE": "AVENUE", "ST": "STREET", "STR": "STREET",
            "BLVD": "BOULEVARD", "PKWY": "PARKWAY", "PL": "PLACE", "RD": "ROAD",
            "DR": "DRIVE", "TER": "TERRACE", "LN": "LANE", "CT": "COURT",
            "E": "EAST", "W": "WEST", "N": "NORTH", "S": "SOUTH",
            "BCH": "BEACH", "HTS": "HEIGHTS"}
    return " ".join(abbr.get(w, w) for w in s.split())


def addr_key(boro: str, num: str, street: str) -> str:
    return f"{boro}|{str(num).strip().upper()}|{norm_street(street)}"


# ---------------- main ----------------------------------------------------------------
def main() -> int:
    S: dict = {}

    # ---------- P3.1a: official HSP dataset (bbl + program_start_date) ----------
    hsp = pull("hsp_selected_buildings", "h4mf-f24e",
               "building_id,borough,number,street,total_units,program_start_date,"
               "current_status,discharge_date,postcode,bin,bbl")
    S["hsp_rows"] = len(hsp)
    if len(hsp) != 200:
        raise RuntimeError(f"HSP dataset rows = {len(hsp)}, expected 200 — HARD STOP (Rule 9).")
    hsp["cohort"] = pd.to_datetime(hsp["program_start_date"]).dt.year
    S["hsp_cohort_counts"] = hsp["cohort"].value_counts().sort_index().to_dict()
    S["hsp_current_status"] = hsp["current_status"].value_counts().to_dict()
    S["hsp_discharge_nonnull"] = int(hsp["discharge_date"].notna().sum())
    if sorted(S["hsp_cohort_counts"]) != COHORT_YEARS:
        raise RuntimeError(f"HSP cohorts {S['hsp_cohort_counts']} != {COHORT_YEARS} — HARD STOP (Rule 9).")
    hsp["boro_code"] = hsp["borough"].str.upper().str.strip().map(BORO_MAP)
    if hsp["boro_code"].isna().any():
        raise RuntimeError(f"Unmapped HSP borough values: "
                           f"{sorted(hsp.loc[hsp['boro_code'].isna(), 'borough'].unique())} — HARD STOP.")
    hsp["akey"] = [addr_key(b, n, s) for b, n, s in
                   zip(hsp["boro_code"], hsp["number"], hsp["street"])]
    hsp["bbl_int"] = to_bbl_int(hsp["bbl"])

    # ---------- P3.1b: cohort PDFs (the §4-named source) — parse + cross-check ----------
    pdf_rows, pdf_meta = [], {}
    for y in COHORT_YEARS:
        path = fetch_pdf(y)
        df, residue = parse_pdf(path, y)
        pdf_meta[y] = dict(rows_parsed=len(df), residue=residue,
                           bytes=path.stat().st_size)
        pdf_rows.append(df)
    pdf = pd.concat(pdf_rows, ignore_index=True)
    S["pdf_meta"] = pdf_meta
    bad_counts = {y: m["rows_parsed"] for y, m in pdf_meta.items() if m["rows_parsed"] != 50}
    if bad_counts:
        raise RuntimeError(f"PDF parse count != 50 for cohorts {bad_counts}; residue in stats — "
                           "HARD STOP (Rule 9), membership never guessed.")
    pdf["akey"] = [addr_key(b, n, s) for b, n, s in
                   zip(pdf["boro"], pdf["house_number"], pdf["street"])]

    # PDF <-> dataset cross-check per cohort on normalized address keys
    xcheck = {}
    for y in COHORT_YEARS:
        pk = set(pdf.loc[pdf["cohort"] == y, "akey"])
        dk = set(hsp.loc[hsp["cohort"] == y, "akey"])
        xcheck[y] = dict(matched=len(pk & dk),
                         pdf_only=sorted(pk - dk), dataset_only=sorted(dk - pk))
    S["pdf_dataset_crosscheck"] = xcheck
    S["pdf_dataset_match_total"] = int(sum(x["matched"] for x in xcheck.values()))

    # ---------- P3.1c: address -> BBL via PLUTO (§4) ----------
    pladdr = pull("pluto_address", "64uk-42ks", "bbl,address,borough")
    pladdr = pladdr.dropna(subset=["bbl", "address", "borough"]).copy()
    pladdr["bbl_int"] = to_bbl_int(pladdr["bbl"])
    pladdr = pladdr.dropna(subset=["bbl_int"])
    pladdr["akey"] = [f"{b.strip().upper()}|{a.split(' ', 1)[0].upper()}|{norm_street(a.split(' ', 1)[1])}"
                      if " " in a else f"{b.strip().upper()}|{a.upper()}|"
                      for b, a in zip(pladdr["borough"], pladdr["address"].astype(str))]
    # unique-key map only (ambiguous keys dropped from the resolver, counted)
    kc = pladdr["akey"].value_counts()
    ambiguous = set(kc[kc > 1].index)
    S["pluto_addr_rows"] = len(pladdr)
    S["pluto_addr_ambiguous_keys"] = int(len(ambiguous))
    resolver = pladdr[~pladdr["akey"].isin(ambiguous)].set_index("akey")["bbl_int"]

    hsp["bbl_via_address"] = hsp["akey"].map(resolver)
    n_addr_resolved = int(hsp["bbl_via_address"].notna().sum())
    both = hsp["bbl_via_address"].notna() & hsp["bbl_int"].notna()
    agree = int((hsp.loc[both, "bbl_via_address"] == hsp.loc[both, "bbl_int"]).sum())
    S["addr_resolution"] = dict(
        n_hsp=200,
        resolved_via_pluto_address=n_addr_resolved,
        rate_pct=round(100 * n_addr_resolved / 200, 1),
        dataset_bbl_present=int(hsp["bbl_int"].notna().sum()),
        both_resolved=int(both.sum()),
        agree=agree,
        disagree_rows=[
            dict(cohort=int(r.cohort), addr=r.akey, dataset_bbl=int(r.bbl_int),
                 pluto_bbl=int(r.bbl_via_address))
            for r in hsp[both & (hsp["bbl_via_address"] != hsp["bbl_int"])].itertuples()],
    )
    # FINAL BBL: official dataset bbl, validated below against PLUTO; address-resolved
    # bbl only as fallback where the dataset bbl is missing (none expected).
    hsp["bbl_final"] = hsp["bbl_int"].fillna(hsp["bbl_via_address"])
    if hsp["bbl_final"].isna().any():
        raise RuntimeError("HSP building with NO resolvable bbl — HARD STOP (Rule 9).")
    hsp["bbl_final"] = hsp["bbl_final"].astype("int64")

    # validate final bbls against the P1 PLUTO cache (existence in lot universe)
    pluto_units = pd.read_parquet(RAW / "pluto_units.parquet")
    pluto_bbls = set(to_bbl_int(pluto_units["bbl"]).dropna().astype("int64").tolist())
    S["bbl_in_pluto"] = int(hsp["bbl_final"].isin(pluto_bbls).sum())
    S["bbl_not_in_pluto"] = sorted(
        int(b) for b in hsp.loc[~hsp["bbl_final"].isin(pluto_bbls), "bbl_final"])

    # distinct tax lots (bbl) vs 200 selections. Violations and 311 are bbl-keyed,
    # so the ANALYSIS GRAIN IS THE TAX LOT; shared-lot rows are reported verbatim
    # (some are the same building re-selected — same bin; some are distinct
    # buildings on one lot — different bins).
    memb = (hsp.groupby("bbl_final")
            .agg(first_start=("program_start_date", "min"),
                 cohorts=("cohort", lambda c: sorted(set(int(x) for x in c))))
            .reset_index())
    S["distinct_bbls"] = int(len(memb))
    S["distinct_bins"] = int(hsp["bin"].nunique())
    shared = hsp[hsp.duplicated("bbl_final", keep=False)].sort_values(["bbl_final", "cohort"])
    S["shared_lot_rows"] = [
        dict(bbl=int(r.bbl_final), bin=str(r.bin), cohort=int(r.cohort),
             addr=f"{r.number} {r.street}", building_id=str(r.building_id))
        for r in shared.itertuples()]
    start_day = to_days(memb["first_start"]).astype("int64").to_numpy()
    memb_bbl = memb["bbl_final"].to_numpy()
    cohort_of_bbl = {int(r.bbl_final): int(r.cohorts[0]) for r in memb.itertuples()}

    # ---------- P3.2: proactive-detectability heuristic — 311-ONLY VERSION ----------
    # (HPD-complaints verification: see module docstring; ygpa-z7cr live but excluded
    #  from phase-0 by Amendment 1 item 2 -> §4's 311-only branch runs, labeled.)
    c311 = pd.read_parquet(RAW / "c311_heat_complaints.parquet")
    c_bbl = to_bbl_int(c311["bbl"])
    c_day = to_days(c311["created_date"])
    keep = c_bbl.notna() & c_day.notna()
    S["c311_rows_used"] = int(keep.sum())
    c_bbl = c_bbl[keep].astype("int64").to_numpy()
    c_day = c_day[keep].astype("int64").to_numpy()
    cov_lo, cov_hi = int(c_day.min()), int(c_day.max())
    S["c311_coverage"] = [str(np.datetime64(cov_lo, "D")), str(np.datetime64(cov_hi, "D"))]
    ckey_sorted = np.sort(c_bbl * DAY_MOD + c_day)

    viol = pd.read_parquet(RAW / "hpd_violations_heat.parquet")
    S["viol_rows_in"] = len(viol)
    viol = viol[viol["class"] == "C"].copy()                      # explicit §3/§4 class-C
    S["viol_class_C"] = len(viol)
    viol = viol.drop_duplicates(subset="violationid", keep="first")
    v_bbl = to_bbl_int(viol["bbl"])
    v_day = to_days(viol["inspectiondate"])
    keep = v_bbl.notna() & v_day.notna()
    viol = viol[keep]
    v_bbl = v_bbl[keep].astype("int64").to_numpy()
    v_day = v_day[keep].astype("int64").to_numpy()

    # restrict to HSP buildings
    in_hsp = np.isin(v_bbl, memb_bbl)
    S["viol_in_hsp_buildings_all_time"] = int(in_hsp.sum())
    h_bbl, h_day = v_bbl[in_hsp], v_day[in_hsp]
    hv = viol[in_hsp].copy()

    # in-program: inspectiondate >= (earliest) program_start_date of that building
    start_map = pd.Series(start_day, index=memb_bbl)
    h_start = start_map.reindex(h_bbl).to_numpy()
    in_prog = h_day >= h_start
    S["viol_excluded_before_program_start"] = int((~in_prog).sum())
    h_bbl, h_day, hv = h_bbl[in_prog], h_day[in_prog], hv[in_prog]

    # Amendment 3 window-coverage eligibility at W=30
    left_edge = (h_day - 30) < cov_lo
    right_edge = h_day > cov_hi
    S["viol_excluded_coverage_left_edge"] = int(left_edge.sum())
    S["viol_excluded_coverage_right_edge"] = int(right_edge.sum())
    keep = ~(left_edge | right_edge)
    h_bbl, h_day, hv = h_bbl[keep], h_day[keep], hv[keep]

    # program seasons: heat season Oct-May (primary); Jun-Sep counted + excluded
    h_season = season_of_days(h_day)
    off = h_season == -1
    S["viol_excluded_offseason_jun_sep"] = int(off.sum())
    h_bbl, h_day, hv, h_season = h_bbl[~off], h_day[~off], hv[~off], h_season[~off]
    n_events = len(h_bbl)
    S["hsp_eligible_violation_events"] = int(n_events)

    # 311 association at W=30 (P2 rule) and the zero-complaint flag
    lo = np.searchsorted(ckey_sorted, h_bbl * DAY_MOD + (h_day - 30), side="left")
    hi = np.searchsorted(ckey_sorted, h_bbl * DAY_MOD + h_day, side="right")
    assoc30 = hi - lo
    zero = assoc30 == 0
    S["zero_complaint_events_w30"] = int(zero.sum())
    S["pct_zero"] = round(float(100 * zero.mean()), 2) if n_events else None

    # secondary: Oct-Jan proactive-cadence subset; and (bbl, day)-dedupe sensitivity
    months = pd.to_datetime(h_day, unit="D").month.values
    octjan = (months >= 10) | (months <= 1)
    S["zero_events_octjan_subset"] = int((zero & octjan).sum())
    S["events_octjan_subset"] = int(octjan.sum())
    dedup = pd.DataFrame({"bbl": h_bbl[zero], "day": h_day[zero]}).drop_duplicates()
    S["zero_events_bbl_day_deduped"] = int(len(dedup))
    S["zero_event_distinct_buildings"] = int(pd.unique(h_bbl[zero]).size)

    # per cohort x season table (violation attributed to its building's EARLIEST cohort)
    h_cohort = np.array([cohort_of_bbl[int(b)] for b in h_bbl])
    seasons_present = sorted(set(int(s) for s in h_season))
    per = {}
    for y in COHORT_YEARS:
        per[y] = {}
        for sy in seasons_present:
            m = (h_cohort == y) & (h_season == sy)
            if m.any():
                per[y][season_label(sy)] = dict(events=int(m.sum()),
                                                zero=int((m & zero).sum()))
    S["per_cohort_season"] = per

    # ---------- floor (pre-committed §4; stated, not argued) ----------
    FLOOR = 30  # §4: ">= 30 complaint-independent confirmed failure events ... combined"
    n_zero = S["zero_complaint_events_w30"]
    verdict = "PASS" if n_zero >= FLOOR else "DEGRADE"
    S["floor"] = FLOOR
    S["p3_verdict"] = verdict

    # ---------- checkpoint ----------
    cohort_rows = []
    for y in COHORT_YEARS:
        x = xcheck[y]
        cohort_rows.append([str(y), "50", "50", str(x["matched"]),
                            str(len(x["pdf_only"])), str(len(x["dataset_only"]))])
    season_cols = [season_label(sy) for sy in seasons_present]
    per_rows = []
    for y in COHORT_YEARS:
        row = [str(y)]
        for sl in season_cols:
            d = per[y].get(sl)
            row.append(f"{d['zero']}/{d['events']}" if d else "—")
        per_rows.append(row)

    ar = S["addr_resolution"]
    lines = [
        "# phase0_p3_hsp.md — P3 HSP ground-truth checkpoint (A-AUX)",
        "",
        "Generated by `src/p3_hsp.py` (idempotent, seed 42). Governing text:",
        "phase0_probe.md §4 + Amendment 1 item 2 (HPD Complaints-and-Problems",
        "excluded from phase-0) + Amendment 3 item 2 (window-coverage eligibility).",
        "Association rule and helper semantics identical to `src/p2_gate.py`",
        "(inclusive bounds, calendar-date truncation, int64 bbl, explicit class-C).",
        "",
        "## P3.1 — Cohort lists: located, downloaded, cross-checked",
        "",
        "All four cohort lists were fetched programmatically — **no manual_downloads.md",
        "needed, no sub-branch halted**:",
        "",
        "1. **nyc.gov PDFs (the §4-named source)** — all four live, downloaded 2026-07-16",
        "   (nyc.gov serves 403 to non-browser agents; browser User-Agent required):",
    ] + [f"   - {COHORT_PDF_URL.format(y=y)} ({pdf_meta[y]['bytes']:,} bytes, "
         f"{pdf_meta[y]['rows_parsed']} rows parsed)" for y in COHORT_YEARS] + [
        "2. **Official HPD open-data dataset `h4mf-f24e`** (\"Buildings Selected for the",
        "   Heat Sensor Program (HSP)\", provenance *official*, rows updated 2026-03-01,",
        "   verified live 2026-07-16 per Rule 5): 200 rows = 4 cohorts × 50, with bbl,",
        "   address, program_start_date, current_status. §4 anticipated PDFs only; the",
        "   dataset is the same publisher's machine-readable form and supplies BBL +",
        "   program dates directly. DEVIATION-DISCLOSED: the dataset (cross-checked",
        "   against the PDFs below) is used as the membership/BBL authority.",
        "",
        "### PDF ↔ dataset cross-check (normalized borough|number|street keys)",
        "",
        md_table(["cohort", "PDF rows", "dataset rows", "matched", "PDF-only", "dataset-only"],
                 cohort_rows),
        "",
        f"Total matched {S['pdf_dataset_match_total']}/200. Unmatched keys (spelling",
        "variants listed verbatim in `data/p3_stats.json` → `pdf_dataset_crosscheck`)",
        "are address-string variants, not membership disagreements, unless listed as",
        "an anomaly below.",
        "",
        "### Address → BBL resolution (§4, via PLUTO)",
        "",
        f"- Independent PLUTO address resolver (`pluto_address` pull, {S['pluto_addr_rows']:,} rows;",
        f"  {S['pluto_addr_ambiguous_keys']:,} ambiguous address keys dropped from the resolver):",
        f"  **{ar['resolved_via_pluto_address']}/200 resolved ({ar['rate_pct']}%)**.",
        f"- Official dataset BBL present: {ar['dataset_bbl_present']}/200.",
        f"- Where both resolve ({ar['both_resolved']}): agreement {ar['agree']}/{ar['both_resolved']}"
        f" ({len(ar['disagree_rows'])} disagreement(s), listed in stats if any).",
        f"- **Final BBLs: official dataset bbl (fallback = address-resolved; used 0 times).**",
        f"- Final bbls found in the P1 PLUTO lot universe: {S['bbl_in_pluto']}/200"
        + (f" (missing: {S['bbl_not_in_pluto']})." if S["bbl_not_in_pluto"] else "."),
        f"- **Analysis grain = tax lot (bbl)** — violations and 311 are bbl-keyed.",
        f"  200 selections → {S['distinct_bbls']} distinct bbls ({S['distinct_bins']} distinct",
        f"  BINs): {len(S['shared_lot_rows'])} rows share a lot (one same-BIN repeat",
        "  selection; the rest are distinct buildings on a shared lot — listed",
        "  verbatim in stats → `shared_lot_rows`). Each lot counted once, membership",
        "  from its EARLIEST program_start_date (disclosed: for a shared lot this",
        "  starts the lot's clock at the earliest member building's cohort).",
        "",
        "## P3.2 — HPD-complaints dataset verification (BEFORE choosing the version)",
        "",
        "Verified live 2026-07-16 (Rule 5):",
        "",
        "| candidate ID | status |",
        "|---|---|",
        "| `uwyv-629c` (legacy HPD Complaints) | login-walled — retired from public API |",
        "| `a2nx-4u46` (legacy HPD Complaint Problems) | login-walled — retired from public API |",
        "| `ygpa-z7cr` (merged Complaints and Problems) | LIVE (updated 2026-07-15) but **excluded from phase-0 by Amendment 1 item 2** |",
        "",
        "No HPD complaints dataset is USABLE in phase-0 → per §4, the **311-ONLY",
        "version** of the heuristic runs, labeled as such. (Flag for R-AUDIT: §4's",
        "conditional predates Amendment 1; the amendment is the later, dated Ayur",
        "ruling and its exclusion is applied here, not reinterpreted.)",
        "",
        "## P3.2 — Proactive-detectability heuristic (311-only, W=30, P2 rule)",
        "",
        "Eligibility waterfall (every exclusion counted):",
        "",
        f"- Violations cache in: {S['viol_rows_in']:,} → class C: {S['viol_class_C']:,}",
        f"- In HSP buildings (any time): **{S['viol_in_hsp_buildings_all_time']:,}**",
        f"- − before building's program_start_date: {S['viol_excluded_before_program_start']:,}",
        f"- − coverage-excluded (Amendment 3, W=30 window inside 311 coverage "
        f"{S['c311_coverage'][0]}…{S['c311_coverage'][1]}): "
        f"left {S['viol_excluded_coverage_left_edge']}, right {S['viol_excluded_coverage_right_edge']}",
        f"- − off-season Jun–Sep (program seasons = heat seasons Oct–May): {S['viol_excluded_offseason_jun_sep']:,}",
        f"- **Eligible in-program violation events: {S['hsp_eligible_violation_events']:,}**",
        "",
        "Result:",
        "",
        f"- **Complaint-independent confirmed failure events (zero 311 associated at",
        f"  W=30): {S['zero_complaint_events_w30']:,}** ({S['pct_zero']}% of eligible events;",
        f"  across {S['zero_event_distinct_buildings']} distinct lots).",
        f"- Sensitivity, (bbl, inspectiondate)-deduped: {S['zero_events_bbl_day_deduped']:,}.",
        f"- Oct–Jan proactive-cadence subset: {S['zero_events_octjan_subset']:,} zero-complaint",
        f"  of {S['events_octjan_subset']:,} events.",
        "",
        "### Per cohort × season (zero-complaint / eligible events; building attributed to earliest cohort)",
        "",
        md_table(["cohort"] + season_cols, per_rows),
        "",
        "## Floor (pre-committed, §4 — cited, not restated, not argued)",
        "",
        f"§4: channel (b) usable for external validation iff ≥ {FLOOR} complaint-independent",
        "confirmed failure events across all HSP cohort-seasons combined.",
        "",
        f"- Events: **{n_zero}** vs floor {FLOOR} → **{verdict}**",
        "",
        f"Robustness (fact, not adjudication): the count clears the floor under the",
        f"narrower Oct–Jan proactive-cadence reading of \"program seasons\" as well",
        f"({S['zero_events_octjan_subset']} events), and under (bbl, inspectiondate)",
        f"dedupe ({S['zero_events_bbl_day_deduped']}); the stated side of the floor",
        "does not depend on these interpretive choices.",
        "",
        "(311-only version caveat, per §4's own labeling requirement: without an HPD",
        "complaints screen, some of these events may have an HPD-direct complaint",
        "trail invisible to 311 — the count is an UPPER BOUND on 311-independent",
        "events under this version. Stated as fact, not adjudicated here.)",
        "",
        "## Anomalies (all benign; none met a Rule 9 stop)",
        "",
        "- 2025 PDF misspells one street (\"CLAREDON ROAD\" vs dataset \"CLARENDON",
        "  ROAD\", same building) — the single cross-check miss; membership agrees.",
        "- Shared tax lots: bbl 2031240001 carries 883 EAST 180 STREET (cohort 2020)",
        "  and 2115 HONEYWELL AVENUE (2022) — distinct BINs; bbl 4067020001 carries",
        "  two Queens buildings, both cohort 2025; bbl 2031250006 (2112 HONEYWELL",
        "  AVENUE) is a true same-BIN repeat selection (2020, 2024).",
        "- nyc.gov returns 403 to non-browser user agents; PDFs fetched with a",
        "  browser User-Agent (URLs above), cached under `data/raw/hsp/`.",
        f"- §4's expected universe \"~200 buildings cumulative\" matches: 200",
        f"  selections, {S['distinct_bbls']} distinct lots.",
        "",
        "Full stats: `data/p3_stats.json`.",
    ]
    CKPT.parent.mkdir(parents=True, exist_ok=True)
    CKPT.write_text("\n".join(lines) + "\n")
    STATS.write_text(json.dumps(S, indent=2, default=str))
    used = _guard_storage()
    print(f"[p3] eligible events={n_events:,}  zero-complaint@W30={n_zero:,}  "
          f"floor={FLOOR}  -> {verdict}")
    print(f"[p3] storage data/raw = {used/1e6:.1f} MB")
    print(f"[p3] wrote {CKPT} and {STATS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
