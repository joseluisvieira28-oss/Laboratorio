#!/usr/bin/env python3
"""One-shot Discovery runner for BTC-FEE-PRESSURE-001 V0.5."""
from __future__ import annotations

import concurrent.futures
import csv
import datetime as dt
import hashlib
import io
import json
import math
import os
import pathlib
import random
import statistics
import sys
import time
import urllib.error
import urllib.request
import zipfile

LAB = "BTC-FEE-PRESSURE-001"
MVE = "BFP-TOTALFEES-7D-001"
BASE = "https://data.binance.vision/data/spot/daily/klines/BTCUSDT/1d"
START_DAY = dt.date(2021, 1, 1)
END_DAY = dt.date(2024, 12, 31)
SEED = 20260914
BOOT_N = 10000
ROOT = pathlib.Path(os.environ.get("BFP_SELECTION_ROOT", "selection_artifact"))
OUT = pathlib.Path(os.environ.get("BFP_DISCOVERY_OUT", "bfp_v05_discovery"))
OUT.mkdir(parents=True, exist_ok=True)
RAW = OUT / "market_raw"
RAW.mkdir(exist_ok=True)

market_access_started = False
market_outcomes_opened = False


def fail(status: str, reason: str, extra: dict | None = None):
    payload = {
        "lab": LAB, "mve": MVE, "status": status, "reason": reason,
        "market_access_started": market_access_started,
        "market_outcomes_opened": market_outcomes_opened,
        "access_2025": False, "access_2026": False,
        "live_trading": False, "exchange_mutation": False,
    }
    if extra:
        payload.update(extra)
    (OUT / "verdict.json").write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")
    (OUT / "verdict.txt").write_text(status + "\n")
    print(json.dumps(payload, sort_keys=True))
    raise SystemExit(0)


def get(url: str, retries: int = 4) -> tuple[int, dict[str, str], bytes]:
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Laboratorio-Research-Discovery/0.5", "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.status, dict(r.headers.items()), r.read()
        except urllib.error.HTTPError as e:
            body = e.read()
            if e.code == 429 or e.code >= 500:
                last = (e.code, dict(e.headers.items()), body)
                time.sleep(min(8, 2 ** attempt))
                continue
            return e.code, dict(e.headers.items()), body
        except Exception as e:
            last = e
            time.sleep(min(8, 2 ** attempt))
    raise RuntimeError(repr(last))


def type7(xs: list[float], p: float) -> float:
    ys = sorted(xs)
    if not ys:
        raise ValueError("empty")
    h = (len(ys) - 1) * p
    lo = math.floor(h)
    hi = math.ceil(h)
    if lo == hi:
        return float(ys[lo])
    w = h - lo
    return float(ys[lo] * (1 - w) + ys[hi] * w)


# -------- pre-outcome binding --------
sel_files = list(ROOT.rglob("selected_trades.json"))
sha_files = list(ROOT.rglob("selected_trades.sha256"))
man_files = list(ROOT.rglob("selection_manifest.json"))
if len(sel_files) != 1 or len(sha_files) != 1 or len(man_files) != 1:
    fail("TECHNICAL_FAILURE_PREOUTCOME", "selection_artifact_shape")

selected_bytes = sel_files[0].read_bytes()
selected_sha = hashlib.sha256(selected_bytes).hexdigest()
sha_token = sha_files[0].read_text().strip().split()[0]
if selected_sha != sha_token:
    fail("PROVENANCE_FAILURE", "selected_trade_hash_mismatch")
try:
    selection_manifest = json.loads(man_files[0].read_text())
    trades = json.loads(selected_bytes)
except Exception as e:
    fail("DATA_FAILURE", f"selection_decode:{type(e).__name__}")
if selection_manifest.get("stage") != "OUTCOME_BLIND_SELECTION_FROZEN":
    fail("PROVENANCE_FAILURE", "selection_stage")
if selection_manifest.get("selected_trades_sha256") != selected_sha:
    fail("PROVENANCE_FAILURE", "selection_manifest_hash_binding")
if selection_manifest.get("market_outcomes_opened") is not False or selection_manifest.get("btc_price_values_opened") is not False:
    fail("PROVENANCE_FAILURE", "selection_was_not_outcome_blind")
if not isinstance(trades, list) or len(trades) != selection_manifest.get("accepted_trade_count"):
    fail("DATA_FAILURE", "trade_selection_count")

last_exit = None
required_days: set[dt.date] = set()
for row in trades:
    try:
        s = dt.date.fromisoformat(row["signal_day"])
        e = dt.date.fromisoformat(row["entry_day"])
        x = dt.date.fromisoformat(row["exit_day"])
    except Exception as exc:
        fail("DATA_FAILURE", f"trade_date_schema:{exc}")
    if e != s + dt.timedelta(days=1) or x != s + dt.timedelta(days=8):
        fail("PROVENANCE_FAILURE", f"timing_mutation:{s}")
    if not (START_DAY <= e <= END_DAY and START_DAY <= x <= END_DAY):
        fail("PROVENANCE_FAILURE", f"protected_period_trade:{s}")
    if last_exit is not None and e < last_exit:
        fail("PROVENANCE_FAILURE", f"overlap_mutation:{s}")
    last_exit = x
    required_days.add(e)
    required_days.add(x)

# -------- market acquisition --------
market_access_started = True

def fetch_day(day: dt.date):
    ds = day.isoformat()
    if day.year not in (2021, 2022, 2023, 2024):
        return {"day": ds, "kind": "PROVENANCE_FAILURE", "reason": "protected_market_date"}
    name = f"BTCUSDT-1d-{ds}.zip"
    zip_url = f"{BASE}/{name}"
    checksum_url = zip_url + ".CHECKSUM"
    try:
        cs_status, cs_headers, cs_body = get(checksum_url)
        z_status, z_headers, z_body = get(zip_url)
    except Exception as e:
        return {"day": ds, "kind": "TECHNICAL_FAILURE_POSTOUTCOME", "reason": f"transport:{type(e).__name__}:{e}"}
    if cs_status != 200 or z_status != 200:
        if cs_status in (404, 410) or z_status in (404, 410):
            return {"day": ds, "kind": "DATA_FAILURE", "reason": f"market_http:checksum={cs_status},zip={z_status}"}
        return {"day": ds, "kind": "TECHNICAL_FAILURE_POSTOUTCOME", "reason": f"market_http:checksum={cs_status},zip={z_status}"}
    try:
        checksum_text = cs_body.decode("utf-8", errors="strict").strip()
        expected = checksum_text.split()[0].lower()
        if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
            raise ValueError("checksum_schema")
        observed = hashlib.sha256(z_body).hexdigest()
        if observed != expected:
            return {"day": ds, "kind": "PROVENANCE_FAILURE", "reason": "checksum_mismatch", "expected": expected, "observed": observed}
        with zipfile.ZipFile(io.BytesIO(z_body), "r") as zf:
            files = [n for n in zf.namelist() if not n.endswith("/")]
            if len(files) != 1:
                raise ValueError(f"zip_members:{files}")
            csv_bytes = zf.read(files[0])
        rows = list(csv.reader(io.StringIO(csv_bytes.decode("utf-8", errors="strict"))))
        if len(rows) != 1 or len(rows[0]) < 2:
            raise ValueError(f"row_shape:{len(rows)}")
        open_time = int(rows[0][0])
        open_price = float(rows[0][1])
        if not math.isfinite(open_price) or open_price <= 0:
            raise ValueError("open_price")
        stamp = dt.datetime.fromtimestamp(open_time / 1000.0, tz=dt.timezone.utc)
        if stamp.date() != day or stamp.time() != dt.time(0, 0):
            return {"day": ds, "kind": "PROVENANCE_FAILURE", "reason": f"open_time_mismatch:{stamp.isoformat()}"}
        return {
            "day": ds, "kind": "PASS", "open": open_price, "open_time": open_time,
            "zip_sha256": observed, "checksum_sha256": hashlib.sha256(cs_body).hexdigest(),
            "zip_bytes": z_body, "checksum_bytes": cs_body,
            "zip_headers": z_headers, "checksum_headers": cs_headers,
        }
    except (zipfile.BadZipFile, UnicodeDecodeError, ValueError, KeyError, IndexError) as e:
        return {"day": ds, "kind": "DATA_FAILURE", "reason": f"market_schema:{type(e).__name__}:{e}"}

results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
    futs = {ex.submit(fetch_day, d): d for d in sorted(required_days)}
    for fut in concurrent.futures.as_completed(futs):
        results.append(fut.result())

bad = [r for r in results if r.get("kind") != "PASS"]
if bad:
    order = {"PROVENANCE_FAILURE": 0, "TECHNICAL_FAILURE_POSTOUTCOME": 1, "DATA_FAILURE": 2}
    bad.sort(key=lambda r: order.get(r.get("kind"), 9))
    fail(bad[0]["kind"], bad[0]["reason"], {"market_failures": [{k: v for k, v in r.items() if k not in ("zip_bytes", "checksum_bytes", "zip_headers", "checksum_headers")} for r in bad[:20]]})

opens = {}
market_receipts = []
for r in sorted(results, key=lambda x: x["day"]):
    market_outcomes_opened = True
    day_dir = RAW / r["day"]
    day_dir.mkdir(parents=True, exist_ok=True)
    name = f"BTCUSDT-1d-{r['day']}.zip"
    (day_dir / name).write_bytes(r["zip_bytes"])
    (day_dir / (name + ".CHECKSUM")).write_bytes(r["checksum_bytes"])
    (day_dir / "headers.json").write_text(json.dumps({"zip": r["zip_headers"], "checksum": r["checksum_headers"]}, sort_keys=True, indent=2) + "\n")
    opens[r["day"]] = r["open"]
    market_receipts.append({
        "day": r["day"], "open_time": r["open_time"], "open": r["open"],
        "zip_sha256": r["zip_sha256"], "checksum_sha256": r["checksum_sha256"],
    })

# -------- returns --------
trade_rows = []
for row in trades:
    ep = opens.get(row["entry_day"])
    xp = opens.get(row["exit_day"])
    if ep is None or xp is None:
        fail("DATA_FAILURE", f"missing_market_open:{row['signal_day']}")
    raw_ret = xp / ep - 1.0
    gross_bps = 10000.0 * raw_ret
    net10 = gross_bps - 10.0
    net20 = gross_bps - 20.0
    trade_rows.append({
        **row,
        "entry_open": ep,
        "exit_open": xp,
        "raw_return": raw_ret,
        "gross_bps": gross_bps,
        "net10_bps": net10,
        "net20_bps": net20,
        "year": int(row["entry_day"][:4]),
    })

N = len(trade_rows)
if N == 0:
    fail("DISCOVERY_FAIL_NO_PROMOTION", "zero_trades", {"N": 0})
gross = [r["gross_bps"] for r in trade_rows]
net10s = [r["net10_bps"] for r in trade_rows]
net20s = [r["net20_bps"] for r in trade_rows]
mean_gross = statistics.fmean(gross)
median_gross = statistics.median(gross)
mean_net10 = statistics.fmean(net10s)
mean_net20 = statistics.fmean(net20s)
pos_sum = sum(x for x in net10s if x > 0)
neg_sum = -sum(x for x in net10s if x < 0)
pf10 = math.inf if neg_sum == 0 and pos_sum > 0 else (pos_sum / neg_sum if neg_sum > 0 else 0.0)
win10 = sum(1 for x in net10s if x > 0) / N

years = {}
for y in (2021, 2022, 2023, 2024):
    ys = [r for r in trade_rows if r["year"] == y]
    years[str(y)] = {
        "N": len(ys),
        "mean_net10_bps": statistics.fmean([r["net10_bps"] for r in ys]) if ys else None,
        "gross_sum_bps": sum(r["gross_bps"] for r in ys),
    }
nonnegative_years = sum(1 for y in years.values() if y["N"] > 0 and y["mean_net10_bps"] is not None and y["mean_net10_bps"] >= 0)
positive_gross_year_sums = [y["gross_sum_bps"] for y in years.values() if y["gross_sum_bps"] > 0]
if positive_gross_year_sums:
    concentration = max(positive_gross_year_sums) / sum(positive_gross_year_sums)
else:
    concentration = 1.0

rng = random.Random(SEED)
boot = []
for _ in range(BOOT_N):
    sample = [net10s[rng.randrange(N)] for __ in range(N)]
    boot.append(statistics.fmean(sample))
p_nonpos = sum(1 for x in boot if x <= 0) / BOOT_N
ci_low = type7(boot, 0.025)
ci_high = type7(boot, 0.975)

cum = 0.0
peak = 0.0
max_dd = 0.0
for x in net10s:
    cum += x
    peak = max(peak, cum)
    max_dd = min(max_dd, cum - peak)

gates = {
    "N_ge_50": N >= 50,
    "mean_NET10_gt_0": mean_net10 > 0,
    "PF10_gt_1": pf10 > 1.0,
    "years_nonnegative_ge_3": nonnegative_years >= 3,
    "bootstrap_p_le_0_20": p_nonpos <= 0.20,
    "positive_year_concentration_le_0_70": concentration <= 0.70,
    "source_binding_pass": selection_manifest.get("source_manifest_sha256") == "4af2e98ac18aaf28686f7f80580ece5a7a34461f20e1955ad562e0a7328c9093",
    "selection_hash_pass": selection_manifest.get("selected_trades_sha256") == selected_sha,
    "market_checksum_pass": all(r.get("kind") == "PASS" for r in results),
    "timing_overlap_pass": True,
    "protected_period_pass": True,
}
verdict = "DISCOVERY_PASS_CANDIDATE" if all(gates.values()) else "DISCOVERY_FAIL_NO_PROMOTION"

summary = {
    "lab": LAB, "mve": MVE, "run_id": os.environ.get("GITHUB_RUN_ID", "local"),
    "verdict": verdict,
    "candidate_signal_count": selection_manifest.get("candidate_signal_count"),
    "accepted_trade_count": N,
    "suppressed_overlap_count": selection_manifest.get("suppressed_overlap_count"),
    "mean_gross_bps": mean_gross,
    "median_gross_bps": median_gross,
    "mean_NET10_bps": mean_net10,
    "mean_NET20_bps": mean_net20,
    "PF_NET10": pf10,
    "win_rate_NET10": win10,
    "years": years,
    "nonnegative_year_count": nonnegative_years,
    "bootstrap_seed": SEED,
    "bootstrap_resamples": BOOT_N,
    "bootstrap_p_mean_NET10_le_0": p_nonpos,
    "bootstrap_ci95_NET10_bps": [ci_low, ci_high],
    "max_positive_year_gross_contribution_share": concentration,
    "cumulative_NET10_bps": cum,
    "max_drawdown_NET10_bps": max_dd,
    "gates": gates,
    "selected_trades_sha256": selected_sha,
    "market_required_day_count": len(required_days),
    "market_receipt_count": len(market_receipts),
    "market_source": "Binance Public Data Vision SPOT daily BTCUSDT 1d",
    "market_access_started": True,
    "market_outcomes_opened": True,
    "returns_computed": True,
    "performance_statistics_computed": True,
    "access_2025": False,
    "access_2026": False,
    "live_trading": False,
    "exchange_mutation": False,
}
(OUT / "trades.json").write_text(json.dumps(trade_rows, sort_keys=True, indent=2) + "\n")
(OUT / "market_receipts.json").write_text(json.dumps(market_receipts, sort_keys=True, indent=2) + "\n")
(OUT / "discovery_summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2, allow_nan=False) + "\n")
(OUT / "verdict.txt").write_text(verdict + "\n")
for fn in ("trades.json", "market_receipts.json", "discovery_summary.json"):
    p = OUT / fn
    (OUT / (fn + ".sha256")).write_text(hashlib.sha256(p.read_bytes()).hexdigest() + f"  {fn}\n")
print(json.dumps({k: summary[k] for k in (
    "verdict", "candidate_signal_count", "accepted_trade_count", "suppressed_overlap_count",
    "mean_gross_bps", "median_gross_bps", "mean_NET10_bps", "mean_NET20_bps",
    "PF_NET10", "win_rate_NET10", "nonnegative_year_count",
    "bootstrap_p_mean_NET10_le_0", "bootstrap_ci95_NET10_bps",
    "max_positive_year_gross_contribution_share", "cumulative_NET10_bps",
    "max_drawdown_NET10_bps", "gates"
)}, sort_keys=True, allow_nan=False))
sys.exit(0)
