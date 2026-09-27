#!/usr/bin/env python3
import csv, hashlib, io, json, math, os, re, sys, time, urllib.parse, urllib.request, zipfile
from datetime import datetime, timezone

OUT_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(OUT_DIR, exist_ok=True)

UA = "CryptoLab-CMM001-SourceGate/0.2 research-only"

def get_bytes(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), dict(r.headers), r.status

def get_json(url, timeout=45):
    b, h, s = get_bytes(url, timeout)
    return json.loads(b.decode("utf-8")), h, s

def ts_ms(date_str, end=False):
    dt = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
    if end:
        dt = dt.replace(hour=23, minute=59, second=59, microsecond=999000)
    return int(dt.timestamp() * 1000)

result = {
    "lab_id": "CMM-001",
    "source_gate_version": "V0.2_TRANSPORT_REMEDIATION",
    "run_type": "SOURCE_GATE_ONLY",
    "protected_outcomes_opened": False,
    "period_touched": "2021-2024 source/provenance only",
    "sources": {},
    "optional_exclusions": {},
}

# A — DERIBIT OPTIONS HISTORY
probe_dates = [
    "2021-01-11","2021-07-12",
    "2022-01-10","2022-07-11",
    "2023-01-09","2023-07-10",
    "2024-01-08","2024-07-08",
]
d_windows = []
for d in probe_dates:
    q = urllib.parse.urlencode({
        "currency":"BTC","kind":"option",
        "start_timestamp":ts_ms(d),
        "end_timestamp":ts_ms(d, end=True),
        "count":1000,"include_old":"true","sorting":"asc",
    })
    url = "https://history.deribit.com/api/v2/public/get_last_trades_by_currency_and_time?" + q
    rec = {"date": d, "url": url, "ok": False}
    try:
        data, _, status = get_json(url, 60)
        trades = data.get("result", {}).get("trades", [])
        valid = [x for x in trades if x.get("iv") is not None and x.get("index_price") is not None and x.get("instrument_name")]
        calls = sum(1 for x in valid if str(x.get("instrument_name","")).endswith("-C"))
        puts = sum(1 for x in valid if str(x.get("instrument_name","")).endswith("-P"))
        rec.update(status=status, trade_count=len(trades), iv_valid=len(valid), calls=calls, puts=puts)
        rec["ok"] = status == 200 and len(valid) >= 20 and calls >= 5 and puts >= 5
    except Exception as e:
        rec["error"] = repr(e)
    d_windows.append(rec)
    time.sleep(0.15)

deribit_pass_windows = sum(1 for x in d_windows if x["ok"])
result["sources"]["options_deribit"] = {
    "status": "PASS" if deribit_pass_windows >= 6 else "FAIL",
    "rule": ">=6/8 deterministic pre-2025 daily probes have >=20 IV-valid trades and >=5 calls + >=5 puts",
    "pass_windows": deribit_pass_windows,
    "total_windows": len(d_windows),
    "windows": d_windows,
    "source_role": "trade-implied IV source only; no historical order-book claim",
}

# B — FRED DGS2
fred_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS2&cosd=2021-01-01&coed=2024-12-31"
try:
    b, _, status = get_bytes(fred_url, 60)
    rows = list(csv.DictReader(io.StringIO(b.decode("utf-8-sig"))))
    numeric = []
    for r in rows:
        v = r.get("DGS2")
        try:
            if v not in (None, "", "."):
                numeric.append((r.get("DATE") or r.get("observation_date"), float(v)))
        except Exception:
            pass
    fred_pass = status == 200 and len(numeric) >= 900
    result["sources"]["rates_fred_dgs2"] = {
        "status": "PASS" if fred_pass else "FAIL",
        "url": fred_url, "http_status": status,
        "numeric_observations": len(numeric),
        "rule": ">=900 numeric daily observations across 2021-2024",
        "first": numeric[0][0] if numeric else None,
        "last": numeric[-1][0] if numeric else None,
    }
except Exception as e:
    result["sources"]["rates_fred_dgs2"] = {"status":"FAIL","url":fred_url,"error":repr(e)}

# C — DEFILLAMA STABLECOIN HISTORY
llama_url = "https://stablecoins.llama.fi/stablecoincharts/all"
try:
    data, _, status = get_json(llama_url, 60)
    pts = data if isinstance(data, list) else data.get("data", [])
    in_range = []
    for x in pts:
        raw = x.get("date") if isinstance(x, dict) else None
        try:
            dt = datetime.fromtimestamp(int(raw), tz=timezone.utc)
            if datetime(2021,1,1,tzinfo=timezone.utc) <= dt < datetime(2025,1,1,tzinfo=timezone.utc):
                in_range.append(x)
        except Exception:
            pass
    llama_pass = status == 200 and len(in_range) >= 1400
    result["sources"]["stablecoin_defillama"] = {
        "status": "PASS" if llama_pass else "FAIL",
        "url": llama_url, "http_status": status,
        "observations_2021_2024": len(in_range),
        "rule": ">=1400 dated observations in 2021-2024",
    }
except Exception as e:
    result["sources"]["stablecoin_defillama"] = {"status":"FAIL","url":llama_url,"error":repr(e)}

# D — BINANCE FUNDING HISTORY
# V0.2 transport-only remediation:
# REST transport returned HTTP 451 from GitHub Actions in V0.1.
# The frozen variable, symbol, month probes and >=80-record rule are unchanged.
# Official Binance Data Vision monthly archives + provider CHECKSUM files are used instead.
funding_probes = []
for y in (2021, 2022, 2023, 2024):
    stamp = f"{y}-01"
    fn = f"BTCUSDT-fundingRate-{stamp}.zip"
    url = f"https://data.binance.vision/data/futures/um/monthly/fundingRate/BTCUSDT/{fn}"
    checksum_url = url + ".CHECKSUM"
    rec = {
        "year": y,
        "url": url,
        "checksum_url": checksum_url,
        "transport": "BINANCE_DATA_VISION_MONTHLY_ARCHIVE",
        "ok": False,
    }
    try:
        b, _, status = get_bytes(url, 60)
        cb, _, cstatus = get_bytes(checksum_url, 60)
        checksum_text = cb.decode("utf-8", "replace").strip()
        expected_sha = checksum_text.split()[0].lower() if checksum_text else ""
        actual_sha = hashlib.sha256(b).hexdigest().lower()
        checksum_ok = len(expected_sha) == 64 and actual_sha == expected_sha

        z = zipfile.ZipFile(io.BytesIO(b))
        members = [n for n in z.namelist() if not n.endswith("/")]
        if len(members) != 1:
            raise RuntimeError(f"expected exactly one CSV member, got {members}")
        raw = z.read(members[0]).decode("utf-8-sig", "replace")
        rows = list(csv.DictReader(io.StringIO(raw)))

        # Archive schemas have used calc_time / fundingTime and
        # last_funding_rate / fundingRate naming. The gate accepts either
        # provider-native spelling but does not synthesize missing values.
        valid = 0
        for row in rows:
            time_v = row.get("calc_time") or row.get("fundingTime") or row.get("funding_time")
            rate_v = row.get("last_funding_rate") or row.get("fundingRate") or row.get("funding_rate")
            if time_v not in (None, "") and rate_v not in (None, ""):
                try:
                    float(rate_v)
                    valid += 1
                except Exception:
                    pass

        rec.update(
            http_status=status,
            checksum_http_status=cstatus,
            expected_sha256=expected_sha,
            actual_sha256=actual_sha,
            checksum_ok=checksum_ok,
            zip_members=members,
            records=len(rows),
            valid_records=valid,
        )
        rec["ok"] = status == 200 and cstatus == 200 and checksum_ok and len(rows) >= 80 and valid >= 80
    except Exception as e:
        rec["error"] = repr(e)
    funding_probes.append(rec)
    time.sleep(0.15)

funding_pass = all(x["ok"] for x in funding_probes)
result["sources"]["funding_binance"] = {
    "status": "PASS" if funding_pass else "FAIL",
    "rule": "Jan Data Vision archive in each 2021-2024 year passes provider SHA256 and has >=80 valid funding records",
    "remediation_from_v01": "transport-only: fapi REST HTTP 451 -> official Data Vision archive; frozen variable/years/threshold unchanged",
    "probes": funding_probes,
}

# E — CFTC HISTORICAL TFF
cftc_years = []
for y in (2021, 2022, 2023, 2024):
    url = f"https://www.cftc.gov/files/dea/history/fut_fin_txt_{y}.zip"
    rec = {"year":y,"url":url,"ok":False}
    try:
        b, _, status = get_bytes(url, 60)
        z = zipfile.ZipFile(io.BytesIO(b))
        names = z.namelist()
        text = "\n".join(z.read(n).decode("latin-1","ignore") for n in names if not n.endswith("/"))
        btc_mentions = text.upper().count("BITCOIN - CHICAGO MERCANTILE EXCHANGE")
        code_mentions = text.count("133741")
        rec.update(http_status=status, zip_members=names, btc_name_mentions=btc_mentions, code_133741_mentions=code_mentions)
        rec["ok"] = status == 200 and max(btc_mentions, code_mentions) >= 40
    except Exception as e:
        rec["error"] = repr(e)
    cftc_years.append(rec)
    time.sleep(0.15)

cftc_pass = all(x["ok"] for x in cftc_years)
result["sources"]["positioning_cftc_tff"] = {
    "status": "PASS" if cftc_pass else "FAIL",
    "rule": "each 2021-2024 official annual TFF archive contains >=40 BTC CME weekly records",
    "years": cftc_years,
}

# OPTIONAL / EXCLUDED — HISTORICAL BINANCE OI
# Remains excluded exactly as frozen in V0.1. No new OI archive is inspected here.
result["optional_exclusions"]["binance_open_interest_history"] = {
    "admissible_in_v01": False,
    "reason": "V0.1 pre-Discovery freeze excluded historical OI; no post-freeze expansion of the primary model is allowed in source remediation",
}

core = ["options_deribit","rates_fred_dgs2","stablecoin_defillama","funding_binance","positioning_cftc_tff"]
passes = {k: result["sources"][k]["status"] == "PASS" for k in core}
result["core_pass_map"] = passes
result["source_data_pass"] = all(passes.values())
result["classification"] = "SOURCE_DATA_PASS" if result["source_data_pass"] else "SOURCE_BLOCKED"
result["next_authorized_state"] = "PRE_DISCOVERY_AUTHORITY_MAY_BE_DRAFTED" if result["source_data_pass"] else "REMEDIATE_SOURCE_ONLY"
result["generated_at_utc"] = datetime.now(timezone.utc).isoformat()

json_path = os.path.join(OUT_DIR, "CMM001_SOURCE_GATE_RESULT_V02.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, sort_keys=True)

md = [
    "# CMM-001 — SOURCE GATE RECEIPT V0.2 — TRANSPORT REMEDIATION",
    "",
    f"Generated UTC: {result['generated_at_utc']}",
    f"Classification: **{result['classification']}**",
    "",
    "No BTC forward returns, PnL, 2025 outcomes or 2026 outcomes were opened.",
    "",
    "## Core source states",
]
for k in core:
    md.append(f"- {k}: **{result['sources'][k]['status']}**")
md += [
    "",
    "## Governance",
    "- Source/provenance failure is not NO_EDGE.",
    "- 2025 remains locked.",
    "- 2026 remains locked.",
    "- No live trading, orders, exchange mutation, main merge or deployment authorized.",
    "",
    f"Next state: **{result['next_authorized_state']}**",
]
with open(os.path.join(OUT_DIR, "CMM001_SOURCE_GATE_RECEIPT_V02.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(md) + "\n")

print(json.dumps({"classification":result["classification"],"core_pass_map":passes}, indent=2))
if not result["source_data_pass"]:
    sys.exit(2)
