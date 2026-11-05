"""Read-only replay of pinned V2 archives, including rejected observations.

No probe import and no HTTP. Recalculates rejection economics from original raw
books rather than trusting forward-state or the early-return legacy auditor.
Does not open any new historical/forward outcome or reinterpret abstentions.
"""
import argparse
import datetime as dt
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path
import sys
import urllib.parse
import zipfile

ROOT = Path(__file__).resolve().parents[1] / "deribit_diamante_v2"
sys.path.insert(0, str(ROOT))
import audit_forward as independent

PINNED = {
    "2026-11-03": ("entry-0809.zip", "3cc57caf25cff0673e459a67bbf9256095ca9e2e79ec75b8ada8b5e567e7d8f2"),
    "2026-11-04": ("entry-session.zip", "ae908f42f534656aabeb7c0f6d4d51052ce95547f04d3af0601e5e04f88979e9"),
    "2026-11-05": ("entry-session.zip", "162833ccb20af28e0e5c669dcf04fb0ef1271b433868fdbd6b8d41d39ff4c413"),
}
METHODS = {"instruments": "get_instruments", "summaries": "get_book_summary_by_currency",
           "deliveries": "get_delivery_prices", "index": "get_index_price",
           "atm_call": "get_order_book", "atm_put": "get_order_book"}


def check(ok, code):
    if not ok:
        raise ValueError(code)


def audit(path, expected, day):
    check(hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, "ARCHIVE_HASH")
    with zipfile.ZipFile(path) as z:
        check(len(z.namelist()) == len(set(z.namelist())), "DUPLICATE_ZIP_NAMES")
        prefix = "raw/" if "raw/receipt.json" in z.namelist() else ""
        read = lambda name: json.loads(z.read(prefix + name + ".json"))
        receipt = read("receipt")
        manifest = receipt["manifest"]
        check(manifest == read("manifest"), "MANIFEST_DISAGREEMENT")
        check(len(manifest) == 6 and {x["name"] for x in manifest} == set(METHODS), "SOURCE_SET")
        check(receipt["freeze"] == independent.FREEZE and receipt["simulation"] is True and
              receipt["orders"] == receipt["private_requests"] == 0 and receipt["mode"] == "entry", "RESEARCH_MODE")
        start = independent.instant(day + "T08:05:00Z")
        end = independent.instant(day + "T08:10:00Z")
        data, sources = {}, {}
        for m in manifest:
            name = m["name"]
            body = z.read(prefix + name + ".json")
            check(hashlib.sha256(body).hexdigest() == m["sha256"], "RAW_HASH")
            check(len(body) == m["bytes"], "RAW_LENGTH")
            env = json.loads(body)
            check(env.get("testnet") is False and "error" not in env, "NOT_PRODUCTION")
            u = urllib.parse.urlparse(m["url"])
            check(u.scheme == "https" and u.netloc == "www.deribit.com" and
                  u.path == "/api/v2/public/" + METHODS[name], "PUBLIC_SOURCE_URL")
            query = urllib.parse.parse_qs(u.query)
            if name in {"index", "deliveries"}:
                check(query.get("index_name") == ["btc_usdc"], "INDEX_URL")
            if name in {"atm_call", "atm_put"}:
                check(query.get("instrument_name") == [receipt["chosen"][name]], "BOOK_URL")
            check(start <= independent.instant(m["started"]) <= independent.instant(m["received"]) < end, "SOURCE_WINDOW")
            data[name] = env["result"]
            sources[name] = m
        check(start <= independent.instant(receipt["observed"]) < end, "OBSERVATION_WINDOW")
        expiry = start.replace(hour=8, minute=0) + dt.timedelta(days=1)
        check(independent.instant(receipt["expiry"]) == expiry, "EXPIRY")
        index = independent.dec(data["index"]["index_price"])
        check(index > 0 and index == independent.dec(receipt["index"]), "INDEX_VALUE")
        pairs = {}
        for meta in data["instruments"]:
            if meta["instrument_name"].startswith("BTC_USDC-") and meta["expiration_timestamp"] == int(expiry.timestamp()*1000):
                pairs.setdefault(independent.dec(meta["strike"]), {})[meta["option_type"]] = meta
        strike = min((k for k, v in pairs.items() if set(v) == {"call", "put"}), key=lambda k: (abs(k-index), k))
        legs = []
        for name, side in (("atm_call", "call"), ("atm_put", "put")):
            meta = pairs[strike][side]
            b = data[name]
            check(receipt["chosen"][name] == b["instrument_name"] == meta["instrument_name"], "DETERMINISTIC_PAIR")
            check(meta["kind"] == "option" and meta["base_currency"] == "BTC" and meta["price_index"] == "btc_usdc"
                  and meta["quote_currency"] == meta["settlement_currency"] == "USDC"
                  and independent.dec(meta["contract_size"]) == 1 and independent.dec(meta["min_trade_amount"]) == D(".01")
                  and independent.dec(meta["taker_commission"]) == D(".0003") and meta["is_active"] is True, "METADATA")
            bid = max(independent.dec(p) for p, q in b["bids"])
            ask = min(independent.dec(p) for p, q in b["asks"])
            depth = min(max(independent.dec(q) for p, q in b["bids"] if independent.dec(p) == bid),
                        max(independent.dec(q) for p, q in b["asks"] if independent.dec(p) == ask))
            age = independent.instant(sources[name]["received"]).timestamp() - b["timestamp"]/1000
            check(b["state"] == "open" and 0 < bid < ask and depth >= D(".05") and -3 <= age <= 10, "BOOK_QUALITY")
            book_index = independent.dec(b["index_price"])
            check(book_index > 0, "BOOK_INDEX")
            legs.append(dict(bid=bid, ask=ask, depth=depth, index=book_index, timestamp=b["timestamp"]))
        times = [x["timestamp"] for x in legs]
        skew = max(times)-min(times)
        # Evaluate each book, not merely the newest book against the index receipt.
        distance = max(abs(t/1000-independent.instant(sources["index"]["received"]).timestamp()) for t in times)
        if receipt["status"] == "SOURCE_BLOCKED":
            check(skew > 1000 or distance > 10, "UNEXPLAINED_SOURCE_REJECTION")
            return dict(date=day, status="SOURCE_BLOCKED_REPRODUCED", raw_hashes=6,
                        book_skew_ms=skew, max_index_distance_seconds=distance, net=None)
        check(skew <= 1000 and distance <= 10, "TIMING_GATE")
        check(receipt["status"] == "ABSTAIN_LIQUIDITY_COST" and receipt.get("control_selected") is False
              and "forecast" not in receipt, "NOT_REJECTION_ONLY")
        check(start <= independent.instant(receipt["decision_at"]) < end and
              max(independent.instant(x["received"]) for x in manifest) <= independent.instant(receipt["decision_at"]), "DECISION_CHRONOLOGY")
        premium = sum(D(".01")*x["ask"] for x in legs)
        spread = sum(D(".01")*(x["ask"]-x["bid"]) for x in legs)
        fees = sum(independent.fee(x["ask"], x["index"]) + independent.fee(x["bid"], x["index"]) for x in legs)
        friction = (spread+fees)/premium*100
        moneyness = abs(strike/index-1)
        check(friction > 8 or moneyness > D(".01"), "UNEXPLAINED_COST_REJECTION")
        econ = receipt["structures"]["straddle"]
        for key, value in (("entry_premium", premium), ("spread", spread), ("roundtrip_loss", spread+fees), ("roundtrip_pct", friction)):
            check(abs(independent.dec(econ[key])-value) < D(".000001"), "RECEIPT_ECONOMICS_"+key)
        return dict(date=day, status="COST_ABSTENTION_REPRODUCED", raw_hashes=6,
                    book_skew_ms=skew, max_index_distance_seconds=distance,
                    premium_usdc=str(premium), spread_usdc=str(spread), four_fees_usdc=str(fees),
                    friction_usdc=str(spread+fees), friction_pct=str(friction), net=None)


def run(root=ROOT):
    observations = [audit(Path(root)/"evidence"/day/name, expected, day) for day, (name, expected) in PINNED.items()]
    return dict(as_of="2026-11-05", source_commit="7a7d58336f68ea483e00a3c7623c4e5777263da5",
                observations=observations, attempted_days=3, accepted_entries=0, settled=0, oos=0,
                pnl=None, expectancy=None, uncertainty=None, live_go=False,
                verdict="NO_GO_LIVE__ECONOMIC_EDGE_NOT_TESTED", market_requests=0)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    a = p.parse_args()
    result = run()
    with Path(a.out).open("x") as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps(result, indent=2))
