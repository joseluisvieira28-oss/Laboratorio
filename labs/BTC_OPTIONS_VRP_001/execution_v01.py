#!/usr/bin/env python3
import hashlib
import json
import math
import random
import re
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

LAB = "BTC-OPTIONS-VRP-001"
MVE = "OVRP-EXEC-ATM30-7D-STATICDELTA-001"
AUTH_PATH = Path("labs/BTC_OPTIONS_VRP_001/EXECUTION_AUTHORITY_V0.1.json")
OUT = Path("artifacts/btc_options_vrp_execution_v01")
OUT.mkdir(parents=True, exist_ok=True)
HISTORY = "https://history.deribit.com/api/v2/public"
PUBLIC = "https://www.deribit.com/api/v2/public"
PROTECTED_MS = int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
MONTHS = {m: i for i, m in enumerate(["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"], 1)}
OPT_RE = re.compile(r"^BTC-(\d{1,2})([A-Z]{3})(\d{2})-([0-9]+(?:\.[0-9]+)?)-([CP])$")


def ms(dt):
    return int(dt.timestamp() * 1000)


def iso(msv):
    return datetime.fromtimestamp(int(msv) / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def sha256b(b):
    return hashlib.sha256(b).hexdigest()


def get_json(base, endpoint, params, timeout=60, retries=3):
    url = base + endpoint + "?" + urllib.parse.urlencode(params)
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SRC-Crypto-Lab/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
            obj = json.loads(raw.decode("utf-8"))
            if "error" in obj:
                raise RuntimeError(f"Deribit API error {endpoint}: {obj['error']}")
            time.sleep(0.01)
            return obj.get("result"), sha256b(raw)
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 429 or 500 <= e.code < 600:
                time.sleep(1.0 * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
            time.sleep(1.0 * (attempt + 1))
    raise RuntimeError(f"Network retries exhausted for {endpoint}: {last!r}")


def trade_list(payload):
    if isinstance(payload, dict) and isinstance(payload.get("trades"), list):
        return payload["trades"], bool(payload.get("has_more"))
    if isinstance(payload, list):
        return payload, False
    raise RuntimeError("Unexpected trade response shape")


def is_valid_screen_trade(t):
    if not isinstance(t, dict):
        return False
    for k in ("block_trade_id", "block_rfq_quote_id", "combo_id", "combo_trade_id"):
        if t.get(k):
            return False
    try:
        return int(t.get("timestamp", -1)) > 0 and float(t.get("price", 0)) > 0 and float(t.get("amount", 0)) > 0
    except Exception:
        return False


def fetch_trades_currency(start_ms, end_ms, count=5000, max_pages=8):
    all_rows, hashes, seen = [], [], set()
    cursor = start_ms
    for _ in range(max_pages):
        payload, h = get_json(HISTORY, "/get_last_trades_by_currency_and_time", {
            "currency": "BTC", "kind": "option", "start_timestamp": cursor,
            "end_timestamp": end_ms, "count": count, "sorting": "asc", "include_old": "true"
        })
        hashes.append(h)
        rows, has_more = trade_list(payload)
        new = 0
        last_ts = None
        for t in rows:
            ts = int(t.get("timestamp", -1))
            tid = str(t.get("trade_id", ""))
            key = (ts, tid, str(t.get("instrument_name", "")), str(t.get("price", "")), str(t.get("amount", "")))
            if key not in seen:
                seen.add(key); all_rows.append(t); new += 1
            if last_ts is None or ts > last_ts:
                last_ts = ts
        if not has_more or not rows:
            break
        if last_ts is None or last_ts >= end_ms:
            break
        next_cursor = last_ts
        if next_cursor <= cursor and new == 0:
            next_cursor = cursor + 1
        cursor = next_cursor
    else:
        raise RuntimeError("Option trade pagination exceeded max_pages")
    return sorted(all_rows, key=lambda x: (int(x.get("timestamp", -1)), str(x.get("trade_id", "")))), hashes


def fetch_trades_instrument(instrument, start_ms, end_ms, count=1000, max_pages=5):
    all_rows, hashes, seen = [], [], set()
    cursor = start_ms
    for _ in range(max_pages):
        payload, h = get_json(HISTORY, "/get_last_trades_by_instrument_and_time", {
            "instrument_name": instrument, "start_timestamp": cursor,
            "end_timestamp": end_ms, "count": count, "sorting": "asc", "include_old": "true"
        })
        hashes.append(h)
        rows, has_more = trade_list(payload)
        new = 0
        last_ts = None
        for t in rows:
            ts = int(t.get("timestamp", -1))
            tid = str(t.get("trade_id", ""))
            key = (ts, tid, str(t.get("price", "")), str(t.get("amount", "")))
            if key not in seen:
                seen.add(key); all_rows.append(t); new += 1
            if last_ts is None or ts > last_ts:
                last_ts = ts
        if not has_more or not rows:
            break
        if last_ts is None or last_ts >= end_ms:
            break
        next_cursor = last_ts
        if next_cursor <= cursor and new == 0:
            next_cursor = cursor + 1
        cursor = next_cursor
    else:
        raise RuntimeError(f"Trade pagination exceeded max_pages for {instrument}")
    return sorted(all_rows, key=lambda x: (int(x.get("timestamp", -1)), str(x.get("trade_id", "")))), hashes


def parse_option(name):
    m = OPT_RE.match(name or "")
    if not m:
        return None
    day, mon, yy, strike, side = m.groups()
    if mon not in MONTHS:
        return None
    exp = datetime(2000 + int(yy), MONTHS[mon], int(day), 8, 0, 0, tzinfo=timezone.utc)
    return exp, float(strike), side


def first_direction(rows, direction, start_ms, end_ms):
    for t in rows:
        ts = int(t.get("timestamp", -1))
        if start_ms <= ts <= end_ms and t.get("direction") == direction and is_valid_screen_trade(t):
            if ts >= PROTECTED_MS:
                raise RuntimeError("Protected-period trade encountered")
            return t
    return None


def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def option_fee(price, amount, multiplier=1.0):
    return min(0.0003, 0.125 * price) * amount * multiplier


def option_tick(price):
    return 0.0001 if price <= 0.0050 else 0.0005


def profit_factor(xs):
    pos = sum(x for x in xs if x > 0)
    neg = -sum(x for x in xs if x < 0)
    if neg == 0:
        return float("inf") if pos > 0 else 0.0
    return pos / neg


def moving_block_ci(xs, reps=5000, block=4, seed=230911):
    n = len(xs)
    if n == 0:
        return [None, None]
    rng = random.Random(seed)
    starts = list(range(max(1, n - block + 1)))
    means = []
    for _ in range(reps):
        sample = []
        while len(sample) < n:
            s = rng.choice(starts)
            sample.extend(xs[s:s+block])
        sample = sample[:n]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int(0.025 * (reps - 1))]
    hi = means[int(0.975 * (reps - 1))]
    return [lo, hi]


def max_drawdown_additive(xs, start_equity=1.0):
    eq = start_equity
    peak = eq
    mdd = 0.0
    for x in xs:
        eq += x
        peak = max(peak, eq)
        if peak > 0:
            mdd = max(mdd, (peak - eq) / peak)
        elif eq < peak:
            return float("inf")
    return mdd


def percentile(xs, p):
    if not xs:
        return None
    ys = sorted(xs)
    if len(ys) == 1:
        return ys[0]
    pos = (len(ys) - 1) * p
    lo = int(math.floor(pos)); hi = int(math.ceil(pos))
    if lo == hi:
        return ys[lo]
    w = pos - lo
    return ys[lo] * (1 - w) + ys[hi] * w


auth = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
assert auth["mve_id"] == MVE
assert auth["strategy_outcomes_authorized"] is True
assert auth["access_2025_authorized"] is False
assert auth["access_2026_authorized"] is False
assert auth["live_trading_authorized"] is False
assert auth["exchange_mutation_authorized"] is False
assert auth["merge_to_main_authorized"] is False

anchors = []
d = datetime(2021, 4, 1, 8, 0, 0, tzinfo=timezone.utc)
last = datetime(2024, 11, 28, 8, 0, 0, tzinfo=timezone.utc)
while d <= last:
    anchors.append(d)
    d += timedelta(days=7)
assert len(anchors) == 192

result = {
    "lab_id": LAB,
    "mve_id": MVE,
    "classification": None,
    "access_2025": False,
    "access_2026": False,
    "live_trading": False,
    "exchange_mutation": False,
    "anchors": len(anchors),
    "executable_n": 0,
    "exclusions": defaultdict(int),
    "source_failure": None,
    "performance": None,
}
episodes = []
selected_manifest = []
source_abort = None

for idx, anchor in enumerate(anchors, 1):
    a_ms = ms(anchor)
    entry_end = ms(anchor + timedelta(hours=4)) - 1
    if entry_end >= PROTECTED_MS:
        result["access_2025"] = True; source_abort = "PROTECTED_ENTRY_QUERY"; break
    try:
        entry_rows, entry_hashes = fetch_trades_currency(a_ms, entry_end)
        valid = [t for t in entry_rows if is_valid_screen_trade(t) and a_ms <= int(t["timestamp"]) <= entry_end]
        if any(int(t["timestamp"]) >= PROTECTED_MS for t in valid):
            result["access_2025"] = True; raise RuntimeError("Protected option row")
        ref_trade = next((t for t in valid if t.get("index_price") is not None and float(t["index_price"]) > 0), None)
        if ref_trade is None:
            result["exclusions"]["no_reference_index"] += 1; continue
        ref_index = float(ref_trade["index_price"])

        first_sell = {}
        meta = {}
        for t in valid:
            if t.get("direction") != "sell":
                continue
            name = str(t.get("instrument_name", ""))
            parsed = parse_option(name)
            if parsed is None:
                continue
            exp, strike, side = parsed
            if ms(exp) >= PROTECTED_MS:
                continue
            dte = (exp - anchor).total_seconds() / 86400.0
            if not (auth["dte_min_days"] <= dte <= auth["dte_max_days"]):
                continue
            if name not in first_sell:
                first_sell[name] = t
                meta[name] = (exp, strike, side, dte)

        pairs = {}
        for name, t in first_sell.items():
            exp, strike, side, dte = meta[name]
            key = (ms(exp), strike)
            pairs.setdefault(key, {})[side] = name
        candidates = []
        for (exp_ms, strike), sides in pairs.items():
            if "C" in sides and "P" in sides:
                exp = datetime.fromtimestamp(exp_ms / 1000, tz=timezone.utc)
                dte = (exp - anchor).total_seconds() / 86400.0
                candidates.append((abs(dte - auth["target_dte_days"]), exp_ms, abs(strike - ref_index), strike, sides["C"], sides["P"]))
        if not candidates:
            result["exclusions"]["no_eligible_sell_pair"] += 1; continue
        candidates.sort(key=lambda x: (x[0], x[1], x[2], x[3]))
        _, exp_ms, _, strike, call_name, put_name = candidates[0]
        call_in = first_sell[call_name]; put_in = first_sell[put_name]
        try:
            call_iv = float(call_in["iv"]); put_iv = float(put_in["iv"])
            call_idx = float(call_in["index_price"]); put_idx = float(put_in["index_price"])
            if not all(math.isfinite(x) and x > 0 for x in [call_iv, put_iv, call_idx, put_idx]):
                raise ValueError
        except Exception:
            result["exclusions"]["invalid_entry_iv_or_index"] += 1; continue

        exit_anchor = anchor + timedelta(days=auth["hold_days"])
        exit_start = ms(exit_anchor)
        exit_end = ms(exit_anchor + timedelta(hours=auth["option_exit_window_hours"])) - 1
        if exit_end >= PROTECTED_MS:
            result["access_2025"] = True; source_abort = "PROTECTED_EXIT_QUERY"; break

        call_rows, call_exit_hashes = fetch_trades_instrument(call_name, exit_start, exit_end)
        put_rows, put_exit_hashes = fetch_trades_instrument(put_name, exit_start, exit_end)
        call_out = first_direction(call_rows, "buy", exit_start, exit_end)
        put_out = first_direction(put_rows, "buy", exit_start, exit_end)
        if call_out is None or put_out is None:
            result["exclusions"]["no_buyback_fill_pair"] += 1; continue

        q = float(auth["option_amount_per_leg"])
        sigma = ((call_iv + put_iv) / 2.0) / 100.0
        S = (call_idx + put_idx) / 2.0
        expiry = datetime.fromtimestamp(exp_ms / 1000, tz=timezone.utc)
        T = (expiry - anchor).total_seconds() / (365.0 * 86400.0)
        if not (sigma > 0 and T > 0 and S > 0 and strike > 0):
            result["exclusions"]["invalid_delta_inputs"] += 1; continue
        d1 = (math.log(S / strike) + 0.5 * sigma * sigma * T) / (sigma * math.sqrt(T))
        long_straddle_delta = q * (2.0 * norm_cdf(d1) - 1.0)
        target_btc = long_straddle_delta

        hedge_n = 0.0; perp_in = None; perp_out = None; funding_rows = []; funding_hash = None
        perp_entry_hashes = []; perp_exit_hashes = []
        if abs(target_btc) > 0:
            hstart = max(int(call_in["timestamp"]), int(put_in["timestamp"]))
            hend = hstart + int(auth["static_delta"]["hedge_window_minutes"] * 60 * 1000)
            hdir = "buy" if target_btc > 0 else "sell"
            perp_rows, perp_entry_hashes = fetch_trades_instrument("BTC-PERPETUAL", hstart, hend)
            perp_in = first_direction(perp_rows, hdir, hstart, hend)
            if perp_in is None:
                result["exclusions"]["no_hedge_entry_fill"] += 1; continue
            p0 = float(perp_in["price"])
            raw_n = target_btc * p0
            unit = float(auth["static_delta"]["round_usd_notional"])
            rounded_abs = math.floor(abs(raw_n) / unit + 0.5) * unit
            hedge_n = math.copysign(rounded_abs, raw_n) if rounded_abs > 0 else 0.0

        if hedge_n != 0:
            hstart2 = max(int(call_out["timestamp"]), int(put_out["timestamp"]))
            hend2 = hstart2 + int(auth["static_delta"]["hedge_window_minutes"] * 60 * 1000)
            hdir2 = "sell" if hedge_n > 0 else "buy"
            perp_rows2, perp_exit_hashes = fetch_trades_instrument("BTC-PERPETUAL", hstart2, hend2)
            perp_out = first_direction(perp_rows2, hdir2, hstart2, hend2)
            if perp_out is None:
                result["exclusions"]["no_hedge_exit_fill"] += 1; continue
            fstart = int(perp_in["timestamp"]); fend = int(perp_out["timestamp"])
            if fend >= PROTECTED_MS:
                result["access_2025"] = True; raise RuntimeError("Protected funding boundary")
            fpayload, funding_hash = get_json(PUBLIC, "/get_funding_rate_history", {
                "instrument_name": "BTC-PERPETUAL", "start_timestamp": fstart, "end_timestamp": fend
            })
            if not isinstance(fpayload, list) or not fpayload:
                source_abort = "FUNDING_SOURCE_EMPTY"; break
            for r in fpayload:
                ts = int(r.get("timestamp", -1))
                if ts >= PROTECTED_MS:
                    result["access_2025"] = True; raise RuntimeError("Protected funding row")
                ir = float(r.get("interest_1h")); ip = float(r.get("index_price"))
                if not (math.isfinite(ir) and math.isfinite(ip) and ip > 0):
                    source_abort = "FUNDING_SOURCE_INVALID"; break
                if fstart <= ts <= fend:
                    funding_rows.append((ts, ir, ip))
            if source_abort:
                break
            if not funding_rows:
                source_abort = "FUNDING_SOURCE_NO_INRANGE_ROWS"; break

        ci, pi, co, po = [float(x["price"]) for x in [call_in, put_in, call_out, put_out]]
        option_gross = q * (ci - co + pi - po)
        option_fees = sum(option_fee(p, q, 1.0) for p in [ci, pi, co, po])
        perp_pnl = 0.0; perp_fees = 0.0; funding_pnl = 0.0
        if hedge_n != 0:
            p0 = float(perp_in["price"]); p1 = float(perp_out["price"])
            perp_pnl = hedge_n * (1.0 / p0 - 1.0 / p1)
            perp_fees = auth["fees"]["perpetual_taker_rate"] * abs(hedge_n) / p0 + auth["fees"]["perpetual_taker_rate"] * abs(hedge_n) / p1
            sgn = 1.0 if hedge_n > 0 else -1.0
            funding_pnl = sum(-sgn * abs(hedge_n) / ip * ir for _, ir, ip in funding_rows)
        base_net = option_gross + perp_pnl + funding_pnl - option_fees - perp_fees

        ci_s = max(0.0, ci - option_tick(ci)); pi_s = max(0.0, pi - option_tick(pi))
        co_s = co + option_tick(co); po_s = po + option_tick(po)
        option_gross_s = q * (ci_s - co_s + pi_s - po_s)
        fm = float(auth["stress"]["fee_multiplier"])
        option_fees_s = sum(option_fee(p, q, fm) for p in [ci_s, pi_s, co_s, po_s])
        perp_pnl_s = 0.0; perp_fees_s = 0.0
        if hedge_n != 0:
            slip = auth["stress"]["perpetual_adverse_slippage_bps_each_side"] / 10000.0
            p0 = float(perp_in["price"]); p1 = float(perp_out["price"])
            if hedge_n > 0:
                p0s, p1s = p0 * (1 + slip), p1 * (1 - slip)
            else:
                p0s, p1s = p0 * (1 - slip), p1 * (1 + slip)
            perp_pnl_s = hedge_n * (1.0 / p0s - 1.0 / p1s)
            rate = auth["fees"]["perpetual_taker_rate"] * fm
            perp_fees_s = rate * abs(hedge_n) / p0s + rate * abs(hedge_n) / p1s
        stress_net = option_gross_s + perp_pnl_s + funding_pnl - option_fees_s - perp_fees_s

        ep = {
            "anchor": anchor.date().isoformat(), "year": anchor.year,
            "expiry": iso(exp_ms), "strike": strike,
            "call": call_name, "put": put_name,
            "call_entry_ts": iso(call_in["timestamp"]), "put_entry_ts": iso(put_in["timestamp"]),
            "call_exit_ts": iso(call_out["timestamp"]), "put_exit_ts": iso(put_out["timestamp"]),
            "call_entry": ci, "put_entry": pi, "call_exit": co, "put_exit": po,
            "entry_iv_mean": (call_iv + put_iv) / 2.0, "entry_index_mean": S,
            "model_d1": d1, "target_hedge_btc": target_btc, "hedge_usd_notional": hedge_n,
            "perp_entry_ts": iso(perp_in["timestamp"]) if perp_in else None,
            "perp_exit_ts": iso(perp_out["timestamp"]) if perp_out else None,
            "perp_entry": float(perp_in["price"]) if perp_in else None,
            "perp_exit": float(perp_out["price"]) if perp_out else None,
            "funding_rows": len(funding_rows),
            "option_gross_btc": option_gross, "option_fees_btc": option_fees,
            "perp_pnl_btc": perp_pnl, "perp_fees_btc": perp_fees,
            "funding_pnl_btc": funding_pnl,
            "base_net_btc": base_net, "base_return": base_net / auth["collateral_btc"],
            "stress_net_btc": stress_net, "stress_return": stress_net / auth["collateral_btc"],
        }
        episodes.append(ep)
        selected_manifest.append({
            "anchor": ep["anchor"], "entry_option_payload_sha256": entry_hashes,
            "call_exit_payload_sha256": call_exit_hashes, "put_exit_payload_sha256": put_exit_hashes,
            "perp_entry_payload_sha256": perp_entry_hashes, "perp_exit_payload_sha256": perp_exit_hashes,
            "funding_payload_sha256": funding_hash,
            "call_trade_id": call_in.get("trade_id"), "put_trade_id": put_in.get("trade_id"),
            "call_exit_trade_id": call_out.get("trade_id"), "put_exit_trade_id": put_out.get("trade_id"),
            "perp_entry_trade_id": perp_in.get("trade_id") if perp_in else None,
            "perp_exit_trade_id": perp_out.get("trade_id") if perp_out else None,
        })
    except Exception as e:
        text = repr(e)
        if "Protected" in text:
            result["access_2025"] = True
            source_abort = "PROVENANCE_FAILURE:" + text
            break
        source_abort = "SOURCE_ACQUISITION_TECHNICAL_FAILURE:" + text
        break

result["executable_n"] = len(episodes)
result["exclusions"] = dict(result["exclusions"])

if result["access_2025"] or result["access_2026"]:
    result["classification"] = "PROVENANCE_FAILURE"
elif source_abort:
    result["classification"] = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
    result["source_failure"] = source_abort
elif len(episodes) < auth["minimum_executable_n"]:
    result["classification"] = "EXECUTION_DATA_LIQUIDITY_INSUFFICIENT"
else:
    base = [e["base_net_btc"] for e in episodes]
    stress = [e["stress_net_btc"] for e in episodes]
    base_returns = [e["base_return"] for e in episodes]
    stress_returns = [e["stress_return"] for e in episodes]
    by_year = defaultdict(list); by_year_s = defaultdict(list)
    for e in episodes:
        by_year[e["year"]].append(e["base_net_btc"]); by_year_s[e["year"]].append(e["stress_net_btc"])
    year_mean = {str(y): sum(v)/len(v) for y,v in sorted(by_year.items())}
    year_total = {str(y): sum(v) for y,v in sorted(by_year.items())}
    year_mean_s = {str(y): sum(v)/len(v) for y,v in sorted(by_year_s.items())}
    nonneg_years = sum(1 for v in year_mean.values() if v >= 0)
    positives = {y:v for y,v in year_total.items() if v > 0}
    concentration = max(positives.values()) / sum(positives.values()) if positives else 1.0
    ci = moving_block_ci(base, auth["bootstrap"]["replications"], auth["bootstrap"]["block_observations"], auth["bootstrap"]["seed"])
    perf = {
        "n": len(base),
        "mean_base_net_btc": sum(base)/len(base), "median_base_net_btc": statistics.median(base),
        "positive_fraction_base": sum(1 for x in base if x>0)/len(base), "base_profit_factor": profit_factor(base),
        "cumulative_base_return": sum(base_returns), "base_max_drawdown": max_drawdown_additive(base),
        "worst_base_return": min(base_returns), "p05_base_return": percentile(base_returns,0.05),
        "mean_stress_net_btc": sum(stress)/len(stress), "median_stress_net_btc": statistics.median(stress),
        "positive_fraction_stress": sum(1 for x in stress if x>0)/len(stress), "stress_profit_factor": profit_factor(stress),
        "cumulative_stress_return": sum(stress_returns), "stress_max_drawdown": max_drawdown_additive(stress),
        "worst_stress_return": min(stress_returns), "p05_stress_return": percentile(stress_returns,0.05),
        "calendar_year_mean_base_btc": year_mean, "calendar_year_total_base_btc": year_total,
        "calendar_year_mean_stress_btc": year_mean_s,
        "nonnegative_base_year_count": nonneg_years,
        "max_positive_year_contribution_share": concentration,
        "bootstrap": {"replications":auth["bootstrap"]["replications"],"seed":auth["bootstrap"]["seed"],"block_observations":auth["bootstrap"]["block_observations"],"ci_95_mean_base_net_btc":ci}
    }
    gates = {
        "n_gte_120": len(base) >= auth["minimum_executable_n"],
        "mean_base_net_gt_0": perf["mean_base_net_btc"] > 0,
        "base_pf_gt_1": perf["base_profit_factor"] > auth["promotion_gates"]["base_pf_gt"],
        "bootstrap_lower_gt_0": ci[0] is not None and ci[0] > 0,
        "nonnegative_years_gte_3": nonneg_years >= auth["promotion_gates"]["nonnegative_years_gte"],
        "mean_stress_net_gt_0": perf["mean_stress_net_btc"] > 0,
        "stress_pf_gt_1": perf["stress_profit_factor"] > auth["promotion_gates"]["stress_pf_gt"],
        "worst_base_return_gt_minus_10pct": perf["worst_base_return"] > auth["promotion_gates"]["worst_base_return_gt"],
        "base_max_drawdown_lte_20pct": perf["base_max_drawdown"] <= auth["promotion_gates"]["base_max_drawdown_lte"],
        "positive_year_concentration_lte_60pct": concentration <= auth["promotion_gates"]["max_positive_year_contribution_share_lte"],
        "protected_period_clean": not result["access_2025"] and not result["access_2026"],
    }
    perf["gates"] = gates
    result["performance"] = perf
    result["classification"] = "EXECUTION_MVE_PASS_CANDIDATE" if all(gates.values()) else "EXECUTION_FAIL_NO_PROMOTION"

# immutable evidence outputs
for ep in episodes:
    if ep["anchor"] >= "2025-01-01":
        raise RuntimeError("Protected episode detected")
mb = ("\n".join(json.dumps(x, sort_keys=True, separators=(",", ":")) for x in selected_manifest) + "\n").encode("utf-8")
(OUT/"selected_source_manifest.jsonl").write_bytes(mb)
result["selected_source_manifest_sha256"] = sha256b(mb)

eb = ("\n".join(json.dumps(x, sort_keys=True, separators=(",", ":")) for x in episodes) + "\n").encode("utf-8")
(OUT/"episodes.jsonl").write_bytes(eb)
result["episodes_sha256"] = sha256b(eb)
rb = (json.dumps(result, indent=2, sort_keys=True, default=str) + "\n").encode("utf-8")
(OUT/"execution_result.json").write_bytes(rb)
print(rb.decode("utf-8"))

if result["classification"] == "PROVENANCE_FAILURE":
    raise SystemExit(2)
