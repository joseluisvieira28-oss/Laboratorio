"""Independent offline verification of prospective V3 public-quote receipts.

No imports from collector/adapter and NO network, orders, fills or PnL.
This audits quote evidence only, NOT economic edge or contract delivery fees.
"""
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import re
import urllib.parse

UTC = dt.timezone.utc
MONTHS = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")
HOST = "www.deribit.com"


def require(condition, code):
    if not condition:
        raise ValueError(code)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def instant(value):
    t = dt.datetime.fromisoformat(value)
    require(t.tzinfo is not None, "NAIVE_TIME")
    return t.astimezone(UTC)


def finite(value):
    require(not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value), "NONFINITE")
    return value


def url_check(url, method, expected):
    parsed = urllib.parse.urlparse(url)
    require(parsed.scheme == "https" and parsed.netloc == HOST
            and parsed.path == "/api/v2/public/" + method
            and not parsed.fragment and not parsed.params, "SOURCE_URL")
    q = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    require(q == {k: [v] for k, v in expected.items()}, "SOURCE_QUERY")


def book(raw, symbol, received):
    env = json.loads(raw)
    require(env.get("testnet") is False and "error" not in env, "SOURCE_IDENTITY")
    b = env["result"]
    require(b.get("instrument_name") == symbol and b.get("state") == "open",
            "BOOK_IDENTITY")
    timestamp = finite(b["timestamp"])
    age = received.timestamp() * 1000 - timestamp
    require(-3000 <= age <= 10000, "BOOK_AGE")
    prices = {}
    for side, reverse in (("bids", True), ("asks", False)):
        levels = b[side]
        require(isinstance(levels, list) and len(levels) >= 1, "EMPTY_BOOK")
        require(all(isinstance(row, list) and len(row) == 2 and
                    finite(row[0]) > 0 and finite(row[1]) > 0
                    for row in levels), "BOOK_LEVEL")
        ps = [row[0] for row in levels]
        require(len(ps) == len(set(ps)) and ps == sorted(ps, reverse=reverse),
                "BOOK_SORT")
        require(levels[0][1] >= .05, "INSUFFICIENT_DEPTH")
        prices[side] = levels[0]
    require(prices["bids"][0] < prices["asks"][0]
            and finite(b["index_price"]) > 0, "CROSSED_BOOK")
    return {"timestamp_ms": timestamp, "bid": prices["bids"],
            "ask": prices["asks"], "sha256": digest(raw)}


def audit(attempt, source_dir=None):
    """Require all primary evidence and re-evaluate frozen quality gates."""
    attempt = Path(attempt)
    source_dir = Path(source_dir) if source_dir else Path(__file__).resolve().parent
    receipt = json.loads((attempt / "receipt.json").read_bytes())
    require(receipt.get("mode") == "prospective"
            and receipt.get("status") == "TECHNICAL_PASS"
            and receipt.get("prospective_v3") is True
            and receipt.get("valid_technical") is True, "NOT_ACCEPTED_FORWARD")
    require(receipt.get("net_pnl") is None and receipt.get("live_go") is False
            and receipt.get("orders") == 0
            and receipt.get("delivery_fee_status") == "UNVERIFIED",
            "TRADING_OR_FEE_CONTAMINATION")

    day = dt.date.fromisoformat(receipt["session_utc"])
    require(attempt.name.startswith(day.isoformat() + "-"), "ATTEMPT_DAY")
    claim = attempt.parent / (day.isoformat() + ".claim")
    require(claim.is_file() and json.loads(claim.read_bytes())["day"] == str(day),
            "MISSING_DAY_CLAIM")
    start = dt.datetime.combine(day, dt.time(8, 5), UTC)
    end = start + dt.timedelta(minutes=5)
    decision = instant(receipt["decision_at"])
    require(start <= decision < end, "DECISION_WINDOW")

    require(receipt.get("precommit_hash") ==
            digest((source_dir / "PRE_REGISTRATION.md").read_bytes()),
            "PRECOMMIT_CHANGED")
    require(receipt.get("collector_hash") ==
            digest((source_dir / "collector.py").read_bytes()),
            "COLLECTOR_CHANGED")

    manifest_raw = (attempt / "manifest.json").read_bytes()
    require(digest(manifest_raw) == receipt["manifest_sha256"], "MANIFEST_HASH")
    manifest = json.loads(manifest_raw)
    require(isinstance(manifest, list) and len(manifest) == 4
            and {m["name"] for m in manifest} ==
            {"instruments", "index", "call", "put"}, "SOURCE_SET")

    sources, envs, raw = {}, {}, {}
    for m in manifest:
        name = m["name"]
        a, b = instant(m["started"]), instant(m["received"])
        require(start <= a <= b <= decision < end, "SOURCE_WINDOW")
        require(m["http_status"] == 200, "HTTP_STATUS")
        body = (attempt / (name + ".json")).read_bytes()
        require(len(body) == m["bytes"] and digest(body) == m["sha256"],
                "RAW_SOURCE_HASH")
        env = json.loads(body)
        require(env.get("testnet") is False and "error" not in env
                and "result" in env, "ENV_IDENTITY")
        sources[name], raw[name], envs[name] = m, body, env["result"]

    url_check(sources["instruments"]["url"], "get_instruments",
              {"currency": "USDC", "kind": "option", "expired": "false"})
    url_check(sources["index"]["url"], "get_index_price",
              {"index_name": "btc_usdc"})

    index = finite(envs["index"]["index_price"])
    require(index > 0 and receipt["spot"] == index, "INDEX_PRICE")
    expiry = dt.datetime.combine(day + dt.timedelta(days=1), dt.time(8), UTC)
    require(instant(receipt["expiry"]) == expiry, "EXPIRY")

    pairs = {}
    for m in envs["instruments"]:
        if (m.get("instrument_name", "").startswith("BTC_USDC-")
                and m.get("expiration_timestamp") == int(expiry.timestamp() * 1000)):
            strike = finite(m["strike"])
            require(strike > 0 and m["option_type"] in ("call", "put"),
                    "INSTRUMENT_METADATA")
            pair = pairs.setdefault(strike, {})
            require(m["option_type"] not in pair, "DUPLICATE_METADATA")
            pair[m["option_type"]] = m
    eligible = [k for k, v in pairs.items() if set(v) == {"call", "put"}]
    require(bool(eligible), "NO_COMPLETE_PAIR")
    strike = min(eligible, key=lambda k: (abs(k - index), k))
    require(abs(strike / index - 1) <= .01, "MONEYNESS")
    month = MONTHS[expiry.month - 1]
    result = {}
    for side, suffix in (("call", "C"), ("put", "P")):
        m = pairs[strike][side]
        symbol = f"BTC_USDC-{expiry.day}{month}{expiry:%y}-{strike:g}-{suffix}"
        require(m["instrument_name"] == symbol, "SYMBOL")
        fields = {"kind": "option", "base_currency": "BTC", "quote_currency": "USDC",
                  "settlement_currency": "USDC", "price_index": "btc_usdc",
                  "contract_size": 1, "min_trade_amount": .01,
                  "taker_commission": .0003, "is_active": True}
        require(all(m.get(k) == v for k, v in fields.items())
                and m.get("instrument_type", "linear") == "linear"
                and finite(m["tick_size"]) > 0, "CONTRACT_TERMS")
        require(receipt["metadata"][side] == m, "SELECTED_METADATA")
        url_check(sources[side]["url"], "get_order_book",
                  {"instrument_name": symbol, "depth": "5"})
        info = book(raw[side], symbol, instant(sources[side]["received"]))
        stored = receipt["legs"][side]
        require(stored["symbol"] == symbol and stored["sha256"] == info["sha256"]
                and stored["bid"] == info["bid"] and stored["ask"] == info["ask"]
                and stored["timestamp"] == info["timestamp_ms"], "RECEIPT_BOOK")
        result[side] = info

    skew = abs(result["call"]["timestamp_ms"] - result["put"]["timestamp_ms"])
    index_time = instant(sources["index"]["received"]).timestamp() * 1000
    distances = [abs(result[s]["timestamp_ms"] - index_time) for s in ("call", "put")]
    require(skew <= 1000 and max(distances) <= 10000, "SYNCHRONIZATION")
    recorded = receipt["synchronization"]
    require(abs(recorded["book_skew_ms"] - skew) < 0.001
            and all(abs(a-b) < 0.001 for a,b in zip(
                recorded["per_book_index_distance_ms"], distances)),
            "RECEIPT_SYNC")
    return {"status": "INDEPENDENT_FORWARD_QUOTE_AUDIT_PASS",
            "day": str(day), "source_hashes": 4,
            "book_skew_ms": skew, "index_distances_ms": distances,
            "prospective_v3": True, "trade_executed": False,
            "net_pnl": None, "live_go": False}


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--attempt", required=True)
    args = p.parse_args()
    print(json.dumps(audit(args.attempt), indent=2, allow_nan=False))
