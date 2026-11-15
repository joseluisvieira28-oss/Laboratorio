#!/usr/bin/env python3
import csv
import hashlib
import io
import json
import math
import os
import random
import re
import statistics
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, time as dtime, timedelta, timezone

LAB_ID = "CMM-001-V01"
AUTHORITY = "CMM001_PRE_DISCOVERY_EXECUTION_AUTHORITY_V01"
OUT_DIR = os.path.join(os.path.dirname(__file__), "discovery_results")
os.makedirs(OUT_DIR, exist_ok=True)
UA = "CryptoLab-CMM001-Discovery/0.1 research-only"
UTC = timezone.utc

START = date(2021, 1, 1)
CANDIDATE_START = date(2021, 7, 1)
END = date(2024, 12, 31)
OPTIONS_COVERAGE_END = date(2024, 12, 27)
COST_BPS = 10.0
STRESS_BPS = 20.0
BOOT_SEED = 20260925
BOOT_N = 10000

BLOCKS = {
    "A_DISCOVERY": (date(2021, 7, 1), date(2022, 12, 31)),
    "B_REPLICATION_2023": (date(2023, 1, 1), date(2023, 12, 31)),
    "C_REPLICATION_2024": (date(2024, 1, 1), date(2024, 12, 31)),
}

def iso(d):
    return d.isoformat()

def daterange(a, b):
    d = a
    while d <= b:
        yield d
        d += timedelta(days=1)

def months(a, b):
    y, m = a.year, a.month
    while (y, m) <= (b.year, b.month):
        yield y, m
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1

def get_bytes(url, timeout=60, retries=3):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read(), dict(r.headers), r.status
        except Exception as e:
            last = e
            if attempt + 1 < retries:
                time.sleep(0.5 * (attempt + 1))
    raise last

def get_json(url, timeout=60, retries=3):
    b, h, s = get_bytes(url, timeout, retries)
    return json.loads(b.decode("utf-8")), h, s

def sha256(b):
    return hashlib.sha256(b).hexdigest()

def parse_checksum(b):
    txt = b.decode("utf-8", "replace").strip()
    if not txt:
        return None
    token = txt.split()[0].lower()
    return token if re.fullmatch(r"[0-9a-f]{64}", token) else None

def download_zip_verified(url):
    b, _, status = get_bytes(url)
    cb, _, cs = get_bytes(url + ".CHECKSUM")
    exp = parse_checksum(cb)
    act = sha256(b)
    ok = status == 200 and cs == 200 and exp == act
    if not ok:
        raise RuntimeError(f"checksum failure {url} expected={exp} actual={act} status={status}/{cs}")
    z = zipfile.ZipFile(io.BytesIO(b))
    if z.testzip() is not None:
        raise RuntimeError(f"zip CRC failure {url}")
    return z, {"url": url, "sha256": act, "checksum_ok": True, "members": z.namelist()}

def parse_epoch(v):
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    try:
        x = int(float(s))
        if x > 10**15:
            x = x / 1_000_000
        elif x > 10**12:
            x = x / 1_000
        return datetime.fromtimestamp(x, UTC)
    except Exception:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s[:19] if "H" in fmt else s[:10], fmt)
            return dt.replace(tzinfo=UTC)
        except Exception:
            pass
    return None

def percentile_linear(values, q):
    xs = sorted(float(x) for x in values)
    if not xs:
        return None
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return xs[lo]
    w = pos - lo
    return xs[lo] * (1 - w) + xs[hi] * w

def profit_factor(vals):
    pos = sum(x for x in vals if x > 0)
    neg = -sum(x for x in vals if x < 0)
    if neg == 0:
        return float("inf") if pos > 0 else 0.0
    return pos / neg

def safe_mean(xs):
    return statistics.fmean(xs) if xs else None

def safe_median(xs):
    return statistics.median(xs) if xs else None

def robust_z(current, hist):
    if current is None or len(hist) < 180:
        return None
    ref = list(hist)[-180:]
    center = statistics.median(ref)
    dev = [abs(x - center) for x in ref]
    mad = statistics.median(dev)
    scale = 1.4826 * mad
    if not math.isfinite(scale) or scale <= 0:
        return None
    z = (current - center) / scale
    return max(-5.0, min(5.0, z))

def block_for(d):
    for name, (a, b) in BLOCKS.items():
        if a <= d <= b:
            return name
    return None

# -----------------------------
# 1. BINANCE SPOT 1H — SOURCE
# -----------------------------
spot_open = {}
spot_receipts = []
spot_errors = []
spot_urls = []

def fetch_spot_month(ym):
    y, m = ym
    stamp = f"{y:04d}-{m:02d}"
    url = f"https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-{stamp}.zip"
    z, rec = download_zip_verified(url)
    rows_out = []
    for member in z.namelist():
        if member.endswith("/"):
            continue
        raw = z.read(member).decode("utf-8-sig", "replace")
        for row in csv.reader(io.StringIO(raw)):
            if len(row) < 2:
                continue
            try:
                ts = int(row[0])
                if ts > 10**15:
                    ts = ts // 1000
                px = float(row[1])
                dt = datetime.fromtimestamp(ts / 1000.0, UTC)
                rows_out.append((dt, px))
            except Exception:
                continue
    return rec, rows_out

with ThreadPoolExecutor(max_workers=8) as ex:
    futs = {ex.submit(fetch_spot_month, ym): ym for ym in months(START, END)}
    for fut in as_completed(futs):
        ym = futs[fut]
        try:
            rec, rows = fut.result()
            spot_receipts.append(rec)
            spot_urls.append(rec["url"])
            for dt, px in rows:
                if START <= dt.date() <= END:
                    spot_open[dt] = px
        except Exception as e:
            spot_errors.append({"month": f"{ym[0]:04d}-{ym[1]:02d}", "error": repr(e)})

# ------------------------------------
# 2. BINANCE FUNDING — DIAGNOSTIC ONLY
# ------------------------------------
funding_daily = {}
funding_receipts = []
funding_errors = []

def fetch_funding_month(ym):
    y, m = ym
    stamp = f"{y:04d}-{m:02d}"
    url = f"https://data.binance.vision/data/futures/um/monthly/fundingRate/BTCUSDT/BTCUSDT-fundingRate-{stamp}.zip"
    z, rec = download_zip_verified(url)
    vals = []
    for member in z.namelist():
        if member.endswith("/"):
            continue
        raw = z.read(member).decode("utf-8-sig", "replace")
        rows = list(csv.DictReader(io.StringIO(raw)))
        for r in rows:
            tv = r.get("calc_time") or r.get("fundingTime") or r.get("funding_time")
            rv = r.get("last_funding_rate") or r.get("fundingRate") or r.get("funding_rate")
            dt = parse_epoch(tv)
            try:
                rate = float(rv)
            except Exception:
                continue
            if dt and START <= dt.date() <= END and dt.time() <= dtime(17, 5):
                vals.append((dt, rate))
    return rec, vals

with ThreadPoolExecutor(max_workers=8) as ex:
    futs = {ex.submit(fetch_funding_month, ym): ym for ym in months(START, END)}
    for fut in as_completed(futs):
        ym = futs[fut]
        try:
            rec, vals = fut.result()
            funding_receipts.append(rec)
            for dt, rate in vals:
                funding_daily.setdefault(dt.date(), []).append(rate)
        except Exception as e:
            funding_errors.append({"month": f"{ym[0]:04d}-{ym[1]:02d}", "error": repr(e)})
funding_raw = {d: statistics.fmean(vs) for d, vs in funding_daily.items() if vs}

# -----------------------
# 3. FRED DGS2 — CORE
# -----------------------
fred_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS2&cosd=2021-01-01&coed=2024-12-31"
fred_bytes, _, fred_status = get_bytes(fred_url)
fred_rows = []
for r in csv.DictReader(io.StringIO(fred_bytes.decode("utf-8-sig"))):
    ds = r.get("DATE") or r.get("observation_date")
    v = r.get("DGS2")
    try:
        fred_rows.append((date.fromisoformat(ds), float(v)))
    except Exception:
        pass
fred_rows.sort()
fred_dates = [x[0] for x in fred_rows]
fred_vals = [x[1] for x in fred_rows]

def fred_index_latest_leq(cut):
    lo, hi, ans = 0, len(fred_dates)-1, None
    while lo <= hi:
        mid = (lo + hi)//2
        if fred_dates[mid] <= cut:
            ans = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return ans

rates_raw = {}
for d in daterange(START, END):
    idx = fred_index_latest_leq(d - timedelta(days=1))
    if idx is not None and idx >= 5:
        rates_raw[d] = -(fred_vals[idx] - fred_vals[idx-5])

# --------------------------------
# 4. DEFILLAMA STABLECOINS — CORE
# --------------------------------
llama_url = "https://stablecoins.llama.fi/stablecoincharts/all"
llama, _, llama_status = get_json(llama_url)
stable_rows = []
for x in llama if isinstance(llama, list) else []:
    try:
        d = datetime.fromtimestamp(int(x["date"]), UTC).date()
        supply = float(x["totalCirculatingUSD"]["peggedUSD"])
        if math.isfinite(supply) and supply > 0 and START <= d <= END:
            stable_rows.append((d, supply))
    except Exception:
        pass
stable_rows.sort()
stable_dates = [x[0] for x in stable_rows]
stable_vals = [x[1] for x in stable_rows]

def stable_latest_leq(cut):
    lo, hi, ans = 0, len(stable_dates)-1, None
    while lo <= hi:
        mid = (lo + hi)//2
        if stable_dates[mid] <= cut:
            ans = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return ans

liquidity_raw = {}
for d in daterange(START, END):
    i1 = stable_latest_leq(d - timedelta(days=1))
    i0 = stable_latest_leq(d - timedelta(days=31))
    if i1 is not None and i0 is not None and stable_vals[i1] > 0 and stable_vals[i0] > 0:
        liquidity_raw[d] = math.log(stable_vals[i1] / stable_vals[i0])

# ----------------------------
# 5. DERIBIT OPTIONS — CORE
# ----------------------------
inst_re = re.compile(r"^BTC-(\d{1,2}[A-Z]{3}\d{2})-([0-9]+(?:\.[0-9]+)?)-([CP])$")
option_raw = {}
option_meta = {}
option_errors = []
option_truncated = []

def fetch_option_day(d):
    start_dt = datetime.combine(d, dtime(15, 0), UTC)
    end_dt = datetime.combine(d, dtime(17, 0), UTC) - timedelta(milliseconds=1)
    q = urllib.parse.urlencode({
        "currency": "BTC",
        "kind": "option",
        "start_timestamp": int(start_dt.timestamp()*1000),
        "end_timestamp": int(end_dt.timestamp()*1000),
        "count": 10000,
        "include_old": "true",
        "sorting": "asc",
    })
    url = "https://history.deribit.com/api/v2/public/get_last_trades_by_currency_and_time?" + q
    data, _, status = get_json(url, timeout=75, retries=4)
    result = data.get("result", {})
    trades = result.get("trades", [])
    has_more = bool(result.get("has_more", False))
    calls, puts = [], []
    valid_all = 0
    for t in trades:
        try:
            name = str(t.get("instrument_name", ""))
            m = inst_re.match(name)
            if not m:
                continue
            trade_ts = datetime.fromtimestamp(int(t["timestamp"])/1000.0, UTC)
            expiry = datetime.strptime(m.group(1), "%d%b%y").replace(tzinfo=UTC, hour=8)
            strike = float(m.group(2))
            cp = m.group(3)
            idx = float(t["index_price"])
            iv = float(t["iv"])
            dte = (expiry - trade_ts).total_seconds() / 86400.0
            if not (7.0 <= dte <= 45.0) or idx <= 0 or not math.isfinite(iv):
                continue
            ratio = strike / idx
            valid_all += 1
            if cp == "C" and 1.05 <= ratio <= 1.20:
                calls.append(iv)
            elif cp == "P" and 0.80 <= ratio <= 0.95:
                puts.append(iv)
        except Exception:
            continue
    raw = None
    if len(calls) >= 5 and len(puts) >= 5:
        raw_skew = statistics.median(puts) - statistics.median(calls)
        raw = -raw_skew
    return d, raw, {
        "http_status": status,
        "trades": len(trades),
        "eligible_any": valid_all,
        "eligible_calls": len(calls),
        "eligible_puts": len(puts),
        "has_more": has_more,
    }

option_days = list(daterange(START, END))
with ThreadPoolExecutor(max_workers=6) as ex:
    futs = {ex.submit(fetch_option_day, d): d for d in option_days}
    completed = 0
    for fut in as_completed(futs):
        d = futs[fut]
        try:
            dd, raw, meta = fut.result()
            option_meta[dd] = meta
            if meta["has_more"]:
                option_truncated.append(iso(dd))
            if raw is not None:
                option_raw[dd] = raw
        except Exception as e:
            option_errors.append({"date": iso(d), "error": repr(e)})
        completed += 1
        if completed % 200 == 0:
            print(f"OPTIONS_PROGRESS {completed}/{len(option_days)}", flush=True)

# ----------------------------
# 6. CFTC TFF — DIAGNOSTIC ONLY
# ----------------------------
cftc_receipts = []
cftc_errors = []
cftc_weekly_raw = []

def norm_key(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())

for y in (2021, 2022, 2023, 2024):
    url = f"https://www.cftc.gov/files/dea/history/fut_fin_txt_{y}.zip"
    try:
        b, _, status = get_bytes(url)
        z = zipfile.ZipFile(io.BytesIO(b))
        text = "\n".join(z.read(n).decode("latin-1", "ignore") for n in z.namelist() if not n.endswith("/"))
        code_count = text.count("133741")
        cftc_receipts.append({"year": y, "url": url, "http_status": status, "code_133741_mentions": code_count})
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            nk = {norm_key(k): v for k, v in row.items() if k}
            market = str(nk.get("marketandexchangenames", "")).upper()
            code = str(nk.get("cftccontractmarketcode", ""))
            if "133741" not in code and "BITCOIN - CHICAGO MERCANTILE EXCHANGE" not in market:
                continue
            ds = nk.get("reportdateasyyyymmdd") or nk.get("reportdate")
            try:
                rd = date.fromisoformat(str(ds)[:10])
                oi = float(str(nk.get("openinterestall", "")).replace(",", ""))
                lng = float(str(nk.get("levmoneypositionslongall", "")).replace(",", ""))
                sht = float(str(nk.get("levmoneypositionsshortall", "")).replace(",", ""))
                if oi > 0:
                    eff = rd + timedelta(days=4)
                    cftc_weekly_raw.append((eff, (lng - sht) / oi))
            except Exception:
                continue
    except Exception as e:
        cftc_errors.append({"year": y, "error": repr(e)})

cftc_weekly_raw = sorted(dict(cftc_weekly_raw).items())
cftc_z_effective = {}
c_hist = deque(maxlen=52)
for eff, raw in cftc_weekly_raw:
    if len(c_hist) >= 52:
        ref = list(c_hist)
        med = statistics.median(ref)
        mad = statistics.median([abs(x-med) for x in ref])
        scale = 1.4826 * mad
        if scale > 0:
            cftc_z_effective[eff] = max(-5.0, min(5.0, (raw-med)/scale))
    c_hist.append(raw)

def cftc_z_for(d):
    val = None
    for eff in sorted(cftc_z_effective):
        if eff <= d:
            val = cftc_z_effective[eff]
        else:
            break
    return val

# ----------------------------------------
# 7. BUILD RAW SPOT STATE + SOURCE GATES
# ----------------------------------------
spot_state_raw = {}
for d in daterange(START, END):
    dt = datetime.combine(d, dtime(17, 0), UTC)
    d7 = d - timedelta(days=7)
    dt7 = datetime.combine(d7, dtime(17, 0), UTC)
    if dt in spot_open and dt7 in spot_open and spot_open[dt] > 0 and spot_open[dt7] > 0:
        spot_state_raw[d] = math.log(spot_open[dt] / spot_open[dt7])

candidate_days = list(daterange(CANDIDATE_START, OPTIONS_COVERAGE_END))
spot_required = 0
spot_present = 0
for d in candidate_days:
    for dd, hh in ((d,17),(d,18),(d+timedelta(days=3),18)):
        if dd <= END:
            spot_required += 1
            if datetime.combine(dd, dtime(hh,0), UTC) in spot_open:
                spot_present += 1
spot_avail = spot_present / spot_required if spot_required else 0.0

option_cov_days = [d for d in candidate_days if d in option_raw]
option_coverage = len(option_cov_days) / len(candidate_days) if candidate_days else 0.0

source_gates = {
    "spot_48_months_checksum": len(spot_receipts) == 48 and not spot_errors,
    "spot_exact_hour_availability_ge_99_5pct": spot_avail >= 0.995,
    "deribit_zero_transport_parse_errors": len(option_errors) == 0,
    "deribit_zero_has_more_truncation": len(option_truncated) == 0,
    "deribit_valid_oraw_coverage_ge_75pct": option_coverage >= 0.75,
    "fred_numeric_ge_900": len(fred_rows) >= 900 and fred_status == 200,
    "defillama_dated_ge_1400": len(stable_rows) >= 1400 and llama_status == 200,
    "funding_48_months_checksum": len(funding_receipts) == 48 and not funding_errors,
    "cftc_4_years_code_present": len(cftc_receipts) == 4 and not cftc_errors and all(x["code_133741_mentions"] >= 40 for x in cftc_receipts),
    "protected_2025_2026_not_fetched": all("2025" not in u and "2026" not in u for u in spot_urls),
}

source_report = {
    "lab_id": LAB_ID,
    "authority": AUTHORITY,
    "generated_at_utc": datetime.now(UTC).isoformat(),
    "outcomes_opened": False,
    "source_gates": source_gates,
    "source_pass": all(source_gates.values()),
    "spot": {
        "monthly_receipts": len(spot_receipts),
        "errors": spot_errors,
        "required_exact_hour_points": spot_required,
        "present_exact_hour_points": spot_present,
        "availability": spot_avail,
    },
    "options": {
        "days_requested": len(option_days),
        "transport_parse_errors": option_errors[:50],
        "transport_parse_error_count": len(option_errors),
        "truncated_days": option_truncated[:50],
        "truncated_day_count": len(option_truncated),
        "valid_oraw_days_candidate_window": len(option_cov_days),
        "candidate_days": len(candidate_days),
        "coverage": option_coverage,
        "sample_daily_meta": {iso(d): option_meta[d] for d in sorted(option_meta)[:5]},
    },
    "fred": {"numeric_observations": len(fred_rows), "status": fred_status},
    "stablecoin": {"dated_observations": len(stable_rows), "status": llama_status},
    "funding": {"monthly_receipts": len(funding_receipts), "errors": funding_errors},
    "cftc": {"annual_receipts": cftc_receipts, "errors": cftc_errors, "weekly_raw_count": len(cftc_weekly_raw)},
    "protected_periods": {"2025": "LOCKED_NOT_FETCHED", "2026": "LOCKED_NOT_FETCHED"},
}

source_path = os.path.join(OUT_DIR, "CMM001_DISCOVERY_SOURCE_REPORT_V01.json")
with open(source_path, "w", encoding="utf-8") as f:
    json.dump(source_report, f, indent=2, sort_keys=True, allow_nan=False)

if not source_report["source_pass"]:
    close = [
        "# CMM-001 — DISCOVERY V0.1 — SOURCE CLOSEOUT",
        "",
        "**STATE: SOURCE_INADEQUATE / OUTCOMES NOT OPENED**",
        "",
        "The pre-outcome full-corpus source gates did not all pass. No CMM-001 event return, PnL or scientific tier was computed.",
        "",
        "## Gates",
    ]
    close += [f"- {k}: {'PASS' if v else 'FAIL'}" for k,v in source_gates.items()]
    close += [
        "",
        f"Options O_raw coverage: {option_coverage:.4%}",
        f"Options request/parse errors: {len(option_errors)}",
        f"Options truncated days: {len(option_truncated)}",
        f"Spot exact-hour availability: {spot_avail:.4%}",
        "",
        "2025 and 2026 remained locked.",
    ]
    with open(os.path.join(OUT_DIR, "CMM001_DISCOVERY_CLOSEOUT_V01.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(close) + "\n")
    print(json.dumps({"state":"SOURCE_INADEQUATE","source_gates":source_gates,"outcomes_opened":False}, indent=2))
    sys.exit(2)

# -------------------------------------------------
# 8. SOURCE PASSED — BUILD Z STATES AND SIGNALS
# -------------------------------------------------
source_report["outcomes_opened"] = True
with open(source_path, "w", encoding="utf-8") as f:
    json.dump(source_report, f, indent=2, sort_keys=True, allow_nan=False)

hist = {k: deque(maxlen=180) for k in ("S","O","R","L","F")}
g_hist = []
last_entry = None
signals = []

daily_state_rows = []

for d in daterange(START, END):
    raws = {
        "S": spot_state_raw.get(d),
        "O": option_raw.get(d),
        "R": rates_raw.get(d),
        "L": liquidity_raw.get(d),
        "F": funding_raw.get(d),
    }
    zs = {k: robust_z(raws[k], hist[k]) for k in hist}
    nonspot = [zs[k] for k in ("O","R","L") if zs[k] is not None]
    nstate = statistics.median(nonspot) if len(nonspot) >= 2 else None
    g = zs["S"] - nstate if zs["S"] is not None and nstate is not None else None
    q95 = percentile_linear([abs(x) for x in g_hist], 0.95) if len(g_hist) >= 180 else None

    block = block_for(d)
    qualifies = False
    direction = 0
    entry_dt = datetime.combine(d, dtime(18,0), UTC)
    if block and g is not None and q95 is not None and abs(g) > q95:
        if last_entry is None or (entry_dt - last_entry).total_seconds() >= 72*3600:
            direction = -1 if g > 0 else (1 if g < 0 else 0)
            if direction != 0:
                exit_d = d + timedelta(days=3)
                exit_dt = datetime.combine(exit_d, dtime(18,0), UTC)
                if exit_d <= END and entry_dt in spot_open and exit_dt in spot_open:
                    qualifies = True

    daily_state_rows.append({
        "date": iso(d), "block": block or "",
        "S_raw": raws["S"], "O_raw": raws["O"], "R_raw": raws["R"], "L_raw": raws["L"],
        "S_z": zs["S"], "O_z": zs["O"], "R_z": zs["R"], "L_z": zs["L"],
        "N": nstate, "G": g, "q95": q95, "qualifies": qualifies,
    })

    if qualifies:
        signals.append({
            "date": d,
            "block": block,
            "entry_dt": entry_dt,
            "exit_dt": datetime.combine(d+timedelta(days=3), dtime(18,0), UTC),
            "direction": direction,
            "G": g, "q95": q95,
            "S_z": zs["S"], "O_z": zs["O"], "R_z": zs["R"], "L_z": zs["L"],
            "N": nstate,
            "F_z": zs["F"],
            "C_z": cftc_z_for(d),
        })
        last_entry = entry_dt

    if g is not None:
        g_hist.append(g)
    for k in hist:
        if raws[k] is not None and math.isfinite(raws[k]):
            hist[k].append(raws[k])

# ------------------------
# 9. OPEN FROZEN OUTCOMES
# ------------------------
events = []
for s in signals:
    entry = spot_open[s["entry_dt"]]
    exitp = spot_open[s["exit_dt"]]
    gross = s["direction"] * ((exitp / entry) - 1.0) * 10000.0
    net = gross - COST_BPS
    stress = gross - STRESS_BPS
    e = dict(s)
    e.update(entry_price=entry, exit_price=exitp, gross_bps=gross, net10_bps=net, stress20_bps=stress)
    events.append(e)

def metrics(evs):
    vals = [e["net10_bps"] for e in evs]
    stress = [e["stress20_bps"] for e in evs]
    pos = [x for x in vals if x > 0]
    conc = (max(pos)/sum(pos)) if pos and sum(pos) > 0 else None
    return {
        "n": len(vals),
        "mean_net10_bps": safe_mean(vals),
        "median_net10_bps": safe_median(vals),
        "pf_net10": profit_factor(vals),
        "positive_fraction": (sum(1 for x in vals if x > 0)/len(vals)) if vals else None,
        "mean_stress20_bps": safe_mean(stress),
        "largest_positive_net_share": conc,
    }

block_metrics = {}
for b in BLOCKS:
    block_metrics[b] = metrics([e for e in events if e["block"] == b])
pooled = metrics(events)

loo = {}
for omit in BLOCKS:
    evs = [e for e in events if e["block"] != omit]
    loo[omit] = metrics(evs)

vals = [e["net10_bps"] for e in events]
rng = random.Random(BOOT_SEED)
boot = []
if vals:
    n = len(vals)
    for _ in range(BOOT_N):
        sample = [vals[rng.randrange(n)] for _ in range(n)]
        boot.append(statistics.fmean(sample))
boot.sort()
boot_p = (sum(1 for x in boot if x <= 0) / len(boot)) if boot else None
boot5 = percentile_linear(boot, 0.05) if boot else None
boot50 = percentile_linear(boot, 0.50) if boot else None
boot95 = percentile_linear(boot, 0.95) if boot else None

adequate = pooled["n"] >= 30 and all(block_metrics[b]["n"] >= 8 for b in BLOCKS)

def pos_pf(m):
    return m["n"] > 0 and m["mean_net10_bps"] is not None and m["mean_net10_bps"] > 0 and m["pf_net10"] > 1

tier2 = (
    adequate
    and all(pos_pf(block_metrics[b]) for b in BLOCKS)
    and pos_pf(pooled)
    and all(pos_pf(loo[b]) for b in BLOCKS)
    and pooled["largest_positive_net_share"] is not None
    and pooled["largest_positive_net_share"] <= 0.40
)

independent_material_contradiction = any(
    block_metrics[b]["n"] >= 8
    and block_metrics[b]["mean_net10_bps"] is not None
    and block_metrics[b]["mean_net10_bps"] <= -10.0
    and block_metrics[b]["pf_net10"] <= 0.90
    for b in ("B_REPLICATION_2023","C_REPLICATION_2024")
)
pooled_strong_negative = (
    adequate and pooled["mean_net10_bps"] is not None and pooled["mean_net10_bps"] < 0
    and pooled["pf_net10"] < 1 and boot95 is not None and boot95 < 0
)

if not adequate:
    verdict = "INSUFFICIENT_SAMPLE"
    maturity = "M3_DISCOVERY_ATTEMPT"
elif tier2:
    verdict = "TIER2_PROMOTED_CANDIDATE__QUASE_DIAMANTE"
    maturity = "M4_REPLICATION"
elif independent_material_contradiction or pooled_strong_negative:
    verdict = "TIER4_REJECTED"
    maturity = "M4_REPLICATION"
else:
    verdict = "TIER3_WATCHLIST"
    maturity = "M4_REPLICATION"

# Diagnostics: funding/CFTC strata, frozen descriptive only
def diag_stratum(key):
    out = {}
    for label, fn in {
        "EXTREME_POS": lambda z: z is not None and z >= 1.5,
        "EXTREME_NEG": lambda z: z is not None and z <= -1.5,
        "NON_EXTREME": lambda z: z is not None and abs(z) < 1.5,
        "MISSING": lambda z: z is None,
    }.items():
        out[label] = metrics([e for e in events if fn(e.get(key))])
    return out

result = {
    "lab_id": LAB_ID,
    "authority": AUTHORITY,
    "generated_at_utc": datetime.now(UTC).isoformat(),
    "source_pass": True,
    "outcomes_opened": True,
    "protected_periods": {"2025":"LOCKED_NOT_FETCHED","2026":"LOCKED_NOT_FETCHED"},
    "blocks": block_metrics,
    "pooled": pooled,
    "leave_one_block_out": loo,
    "bootstrap": {
        "reps": BOOT_N, "seed": BOOT_SEED,
        "one_sided_p_mean_le_zero": boot_p,
        "p05_mean_net10_bps": boot5,
        "p50_mean_net10_bps": boot50,
        "p95_mean_net10_bps": boot95,
    },
    "sample_adequacy": {
        "pooled_n_ge_30": pooled["n"] >= 30,
        "each_block_n_ge_8": {b:block_metrics[b]["n"] >= 8 for b in BLOCKS},
        "pass": adequate,
    },
    "tier2_gates": {
        "all_blocks_positive_pf_gt_1": all(pos_pf(block_metrics[b]) for b in BLOCKS),
        "pooled_positive_pf_gt_1": pos_pf(pooled),
        "all_loo_positive_pf_gt_1": all(pos_pf(loo[b]) for b in BLOCKS),
        "pooled_largest_positive_share_le_40pct": pooled["largest_positive_net_share"] is not None and pooled["largest_positive_net_share"] <= 0.40,
    },
    "tier4_gates": {
        "independent_material_contradiction": independent_material_contradiction,
        "pooled_strong_negative": pooled_strong_negative,
    },
    "verdict": verdict,
    "maturity": maturity,
    "diagnostics_only": {
        "funding_z_strata": diag_stratum("F_z"),
        "cftc_z_strata": diag_stratum("C_z"),
    },
    "governance": {
        "tier1_possible_from_this_run": False,
        "live_trading_authorized": False,
        "micro_live_authorized": False,
        "main_merge_authorized": False,
        "post_outcome_rescue_authorized": False,
    },
}

# Event ledger
ledger_path = os.path.join(OUT_DIR, "CMM001_EVENT_LEDGER_V01.csv")
fields = [
    "date","block","entry_utc","exit_utc","direction","G","q95","S_z","O_z","R_z","L_z","N",
    "F_z","C_z","entry_price","exit_price","gross_bps","net10_bps","stress20_bps"
]
with open(ledger_path, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for e in events:
        w.writerow({
            "date": iso(e["date"]), "block": e["block"],
            "entry_utc": e["entry_dt"].isoformat(), "exit_utc": e["exit_dt"].isoformat(),
            "direction": "LONG" if e["direction"] == 1 else "SHORT",
            "G": e["G"], "q95": e["q95"], "S_z": e["S_z"], "O_z": e["O_z"],
            "R_z": e["R_z"], "L_z": e["L_z"], "N": e["N"], "F_z": e["F_z"], "C_z": e["C_z"],
            "entry_price": e["entry_price"], "exit_price": e["exit_price"],
            "gross_bps": e["gross_bps"], "net10_bps": e["net10_bps"], "stress20_bps": e["stress20_bps"],
        })

# Daily state ledger (no need for later re-inference)
state_path = os.path.join(OUT_DIR, "CMM001_DAILY_STATE_LEDGER_V01.csv")
state_fields = ["date","block","S_raw","O_raw","R_raw","L_raw","S_z","O_z","R_z","L_z","N","G","q95","qualifies"]
with open(state_path, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=state_fields)
    w.writeheader()
    for r in daily_state_rows:
        w.writerow(r)

result["evidence_hashes"] = {}
for p in (source_path, ledger_path, state_path):
    with open(p, "rb") as f:
        result["evidence_hashes"][os.path.basename(p)] = sha256(f.read())

result_path = os.path.join(OUT_DIR, "CMM001_DISCOVERY_RESULT_V01.json")
with open(result_path, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, sort_keys=True, allow_nan=False)

def fmt(x, nd=4):
    if x is None:
        return "NA"
    if isinstance(x, float) and math.isinf(x):
        return "INF"
    return f"{x:.{nd}f}"

close = [
    "# CMM-001 — DISCOVERY / REPLICATION CLOSEOUT V0.1",
    "",
    f"**VERDICT: {verdict}**",
    f"**MATURITY: {maturity}**",
    "",
    "Source integrity: PASS before outcomes.",
    "2025: LOCKED / NOT FETCHED.",
    "2026: LOCKED / NOT FETCHED.",
    "",
    "## Frozen block economics — BASE NET10",
]
for b in BLOCKS:
    m = block_metrics[b]
    close.append(f"- {b}: N={m['n']} | mean={fmt(m['mean_net10_bps'])} bps | median={fmt(m['median_net10_bps'])} | PF={fmt(m['pf_net10'])} | positive={fmt((m['positive_fraction'] or 0)*100,2)}%")
close += [
    "",
    f"## Pooled",
    f"N={pooled['n']} | mean NET10={fmt(pooled['mean_net10_bps'])} bps | median={fmt(pooled['median_net10_bps'])} | PF={fmt(pooled['pf_net10'])} | positive={fmt((pooled['positive_fraction'] or 0)*100,2)}%",
    f"Mean STRESS20={fmt(pooled['mean_stress20_bps'])} bps",
    f"Largest single positive BASE-net share={fmt((pooled['largest_positive_net_share'] or 0)*100,2)}%",
    "",
    f"Bootstrap 10,000 seed {BOOT_SEED}: p(mean<=0)={fmt(boot_p,4)} | p05={fmt(boot5)} | median={fmt(boot50)} | p95={fmt(boot95)} bps",
    "",
    "## Sample adequacy",
    f"- pooled N>=30: {'PASS' if pooled['n'] >= 30 else 'FAIL'}",
]
for b in BLOCKS:
    close.append(f"- {b} N>=8: {'PASS' if block_metrics[b]['n'] >= 8 else 'FAIL'}")
close += [
    "",
    "## Tier-2 rare-event corpus gates",
    f"- every block positive BASE net and PF>1: {'PASS' if result['tier2_gates']['all_blocks_positive_pf_gt_1'] else 'FAIL'}",
    f"- pooled positive BASE net and PF>1: {'PASS' if result['tier2_gates']['pooled_positive_pf_gt_1'] else 'FAIL'}",
    f"- every leave-one-block-out positive/PF>1: {'PASS' if result['tier2_gates']['all_loo_positive_pf_gt_1'] else 'FAIL'}",
    f"- pooled concentration <=40%: {'PASS' if result['tier2_gates']['pooled_largest_positive_share_le_40pct'] else 'FAIL'}",
    "",
    "## Governance",
    "- Funding/CFTC strata are descriptive only and did not select or rescue the candidate.",
    "- No long-only/short-only, year, threshold, horizon, cost, component or event rescue is authorized.",
    "- Tier 1 is impossible from this run alone.",
    "- No live trading, micro-live, capital, order, exchange mutation, Render deployment or main merge is authorized.",
]
closeout_path = os.path.join(OUT_DIR, "CMM001_DISCOVERY_CLOSEOUT_V01.md")
with open(closeout_path, "w", encoding="utf-8") as f:
    f.write("\n".join(close) + "\n")

with open(closeout_path, "rb") as f:
    close_hash = sha256(f.read())
with open(result_path, "rb") as f:
    result_hash = sha256(f.read())

print(json.dumps({
    "verdict": verdict,
    "maturity": maturity,
    "pooled": pooled,
    "blocks": block_metrics,
    "bootstrap_p": boot_p,
    "result_sha256": result_hash,
    "closeout_sha256": close_hash,
    "protected_2025": "LOCKED_NOT_FETCHED",
    "protected_2026": "LOCKED_NOT_FETCHED",
}, indent=2, allow_nan=False))
