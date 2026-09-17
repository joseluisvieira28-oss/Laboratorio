#!/usr/bin/env python3
"""Outcome-blind Tardis source-feasibility probe for BTC-OPTIONS-VRP-001.

This script only tests whether free first-day-of-month Tardis Deribit samples
contain the historical option-chain and BBO quote structure required to design a
future execution MVE. It never computes returns, strategy PnL, expectancy, PF,
drawdown, or any 2025/2026 outcome.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import requests

ROOT = Path(__file__).resolve().parent
AUTH_PATH = ROOT / "TARDIS_SOURCE_PROBE_AUTHORITY_V0.1.json"
OUT = Path("artifacts/btc_options_vrp_tardis_source_probe_v01")
OUT.mkdir(parents=True, exist_ok=True)

OPTION_RE = re.compile(r"^(BTC)-(\d{1,2}[A-Z]{3}\d{2})-([0-9]+(?:\.[0-9]+)?)-([CP])$")
DATE_FMT = "%d%b%y"
USER_AGENT = "Crypto-Lab-source-feasibility/1.0"

SAFETY = {
    "returns_computed": False,
    "strategy_pnl_computed": False,
    "expectancy_computed": False,
    "profit_factor_computed": False,
    "drawdown_computed": False,
    "paid_subscription_used": False,
    "api_key_used": False,
    "access_2025": False,
    "access_2026": False,
    "live_trading": False,
    "exchange_mutation": False,
    "wallet_access": False,
    "source_values_used_only_for_schema_and_bbo_presence": True,
}


class RouteInsufficient(RuntimeError):
    pass


class AcquisitionFailure(RuntimeError):
    pass


@dataclass
class CountingRaw:
    raw: Any
    n: int = 0

    def read(self, size: int = -1) -> bytes:
        b = self.raw.read(size)
        self.n += len(b or b"")
        return b

    def readinto(self, b: bytearray) -> int:
        n = self.raw.readinto(b)
        if n:
            self.n += n
        return n

    def readable(self) -> bool:
        return True


def stable_sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def pick(row: dict[str, str], names: Iterable[str]) -> str | None:
    for n in names:
        v = row.get(n)
        if v is not None and str(v).strip() != "":
            return str(v).strip()
    return None


def positive_number(v: str | None) -> bool:
    if v is None:
        return False
    try:
        return float(v) > 0
    except Exception:
        return False


def row_symbol(row: dict[str, str]) -> str | None:
    return pick(row, ("symbol", "instrument", "instrument_name", "instrument_id"))


def row_timestamp(row: dict[str, str]) -> str | None:
    return pick(row, ("timestamp", "exchange_timestamp", "ts", "local_timestamp"))


def row_bbo_ok(row: dict[str, str]) -> bool:
    bid = pick(row, ("bid_price", "best_bid_price", "bid_price_0", "bids[0].price"))
    ask = pick(row, ("ask_price", "best_ask_price", "ask_price_0", "asks[0].price"))
    return positive_number(bid) and positive_number(ask)


def parse_option_symbol(symbol: str, sample_day: date) -> tuple[date, float, str, int] | None:
    m = OPTION_RE.match(symbol.upper())
    if not m:
        return None
    try:
        expiry = datetime.strptime(m.group(2), DATE_FMT).date()
        strike = float(m.group(3))
        right = m.group(4)
        dte = (expiry - sample_day).days
        return expiry, strike, right, dte
    except Exception:
        return None


def stream_csv(url: str, connect_timeout: int, read_timeout: int):
    try:
        r = requests.get(
            url,
            stream=True,
            timeout=(connect_timeout, read_timeout),
            headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
            allow_redirects=True,
        )
    except requests.RequestException as exc:
        raise AcquisitionFailure(f"request failed for {url}: {type(exc).__name__}: {exc}") from exc
    if r.status_code != 200:
        body = b""
        try:
            body = r.raw.read(512)
        except Exception:
            pass
        r.close()
        raise RouteInsufficient(f"HTTP {r.status_code} for {url}; body_prefix_sha256={hashlib.sha256(body).hexdigest()}")
    counter = CountingRaw(r.raw)
    try:
        gz = gzip.GzipFile(fileobj=counter)
        text = io.TextIOWrapper(gz, encoding="utf-8", newline="")
        reader = csv.DictReader(text)
        if not reader.fieldnames:
            raise RouteInsufficient(f"missing CSV header for {url}")
        yield r, counter, reader
    finally:
        r.close()


def probe_chain(auth: dict[str, Any], sample: str) -> dict[str, Any]:
    d = date.fromisoformat(sample)
    if d.year >= 2025:
        raise RuntimeError("protected-period access blocked")
    url = f"{auth['source']['base_url']}/deribit/options_chain/{d.year:04d}/{d.month:02d}/{d.day:02d}/OPTIONS.csv.gz"
    max_rows = int(auth["bounded_transport"]["max_options_chain_rows_per_date"])
    cto = int(auth["bounded_transport"]["connect_timeout_seconds"])
    rto = int(auth["bounded_transport"]["read_timeout_seconds"])
    pairs: dict[tuple[str, float], dict[str, Any]] = {}
    rows = btc_rows = bbo_btc_rows = 0
    first_ts = last_ts = None
    header: list[str] = []
    content_length = None

    for response, counter, reader in stream_csv(url, cto, rto):
        header = list(reader.fieldnames or [])
        content_length = response.headers.get("Content-Length")
        symbol_col_present = any(x in header for x in ("symbol", "instrument", "instrument_name", "instrument_id"))
        ts_col_present = any(x in header for x in ("timestamp", "exchange_timestamp", "ts", "local_timestamp"))
        bid_col_present = any(x in header for x in ("bid_price", "best_bid_price", "bid_price_0", "bids[0].price"))
        ask_col_present = any(x in header for x in ("ask_price", "best_ask_price", "ask_price_0", "asks[0].price"))
        if not (symbol_col_present and ts_col_present and bid_col_present and ask_col_present):
            raise RouteInsufficient(f"options_chain schema insufficient: {header}")
        for row in reader:
            rows += 1
            ts = row_timestamp(row)
            if ts is not None:
                first_ts = first_ts or ts
                last_ts = ts
            sym = row_symbol(row)
            if not sym or not sym.upper().startswith("BTC-"):
                if rows >= max_rows:
                    break
                continue
            parsed = parse_option_symbol(sym, d)
            if parsed is None:
                if rows >= max_rows:
                    break
                continue
            expiry, strike, right, dte = parsed
            btc_rows += 1
            if row_bbo_ok(row):
                bbo_btc_rows += 1
            if auth["pair_definition"]["dte_min"] <= dte <= auth["pair_definition"]["dte_max"]:
                key = (expiry.isoformat(), strike)
                p = pairs.setdefault(key, {"expiry": expiry.isoformat(), "strike": strike, "dte": dte, "C": None, "P": None})
                if row_bbo_ok(row) and p[right] is None:
                    p[right] = sym
                if p["C"] and p["P"]:
                    # Deterministic first qualifying same-strike call/put pair in stream order.
                    selected = {"expiry": p["expiry"], "strike": p["strike"], "dte": p["dte"], "call": p["C"], "put": p["P"]}
                    return {
                        "date": sample,
                        "url": url,
                        "http_status": 200,
                        "content_length": content_length,
                        "header": header,
                        "rows_scanned": rows,
                        "compressed_bytes_consumed": counter.n,
                        "btc_option_rows_seen": btc_rows,
                        "btc_rows_with_nonempty_bbo": bbo_btc_rows,
                        "first_timestamp_seen": first_ts,
                        "last_timestamp_seen": last_ts,
                        "selected_pair": selected,
                    }
            if rows >= max_rows:
                break
    raise RouteInsufficient(
        f"no same-strike BTC call/put pair with nonempty chain BBO at 25-35DTE on {sample}; rows={rows}, btc_rows={btc_rows}"
    )


def probe_quotes(auth: dict[str, Any], sample: str, selected_pair: dict[str, Any]) -> dict[str, Any]:
    d = date.fromisoformat(sample)
    if d.year >= 2025:
        raise RuntimeError("protected-period access blocked")
    url = f"{auth['source']['base_url']}/deribit/quotes/{d.year:04d}/{d.month:02d}/{d.day:02d}/OPTIONS.csv.gz"
    max_rows = int(auth["bounded_transport"]["max_quote_rows_per_date"])
    cto = int(auth["bounded_transport"]["connect_timeout_seconds"])
    rto = int(auth["bounded_transport"]["read_timeout_seconds"])
    targets = {selected_pair["call"], selected_pair["put"]}
    found: dict[str, dict[str, Any]] = {}
    rows = 0
    first_ts = last_ts = None
    header: list[str] = []
    content_length = None

    for response, counter, reader in stream_csv(url, cto, rto):
        header = list(reader.fieldnames or [])
        content_length = response.headers.get("Content-Length")
        symbol_col_present = any(x in header for x in ("symbol", "instrument", "instrument_name", "instrument_id"))
        ts_col_present = any(x in header for x in ("timestamp", "exchange_timestamp", "ts", "local_timestamp"))
        bid_col_present = any(x in header for x in ("bid_price", "best_bid_price", "bid_price_0", "bids[0].price"))
        ask_col_present = any(x in header for x in ("ask_price", "best_ask_price", "ask_price_0", "asks[0].price"))
        if not (symbol_col_present and ts_col_present and bid_col_present and ask_col_present):
            raise RouteInsufficient(f"quotes schema insufficient: {header}")
        for row in reader:
            rows += 1
            ts = row_timestamp(row)
            if ts is not None:
                first_ts = first_ts or ts
                last_ts = ts
            sym = row_symbol(row)
            if sym in targets and row_bbo_ok(row) and sym not in found:
                found[sym] = {"timestamp": ts, "bbo_present": True}
                if set(found) == targets:
                    return {
                        "date": sample,
                        "url": url,
                        "http_status": 200,
                        "content_length": content_length,
                        "header": header,
                        "rows_scanned": rows,
                        "compressed_bytes_consumed": counter.n,
                        "first_timestamp_seen": first_ts,
                        "last_timestamp_seen": last_ts,
                        "target_symbols": sorted(targets),
                        "targets_with_nonempty_bbo": found,
                    }
            if rows >= max_rows:
                break
    missing = sorted(targets - set(found))
    raise RouteInsufficient(f"quotes route missing nonempty BBO for selected legs on {sample}: {missing}; rows={rows}")


def main() -> int:
    auth = json.loads(AUTH_PATH.read_text())
    receipt: dict[str, Any] = {
        "lab_id": auth["lab_id"],
        "probe_id": auth["probe_id"],
        "authority_sha256": hashlib.sha256(AUTH_PATH.read_bytes()).hexdigest(),
        "classification": None,
        "dates": [],
        "failure": None,
        "safety": SAFETY,
    }
    try:
        if auth["status"] != "FROZEN_SOURCE_ONLY_OUTCOME_BLIND":
            raise RuntimeError("authority not frozen source-only")
        forbidden_true = [k for k, v in auth["safety"].items() if k.endswith("_authorized") and v]
        if forbidden_true:
            raise RuntimeError(f"unsafe authority flags: {forbidden_true}")
        samples = list(auth["sample_dates"])
        if len(samples) != 4 or {date.fromisoformat(x).year for x in samples} != {2021, 2022, 2023, 2024}:
            raise RuntimeError("sample-date invariant failed")
        for sample in samples:
            chain = probe_chain(auth, sample)
            quotes = probe_quotes(auth, sample, chain["selected_pair"])
            receipt["dates"].append({"date": sample, "options_chain": chain, "quotes": quotes})
        receipt["classification"] = "PAID_SOURCE_ROUTE_FEASIBLE"
    except RouteInsufficient as exc:
        receipt["classification"] = "SOURCE_ROUTE_SCHEMA_INSUFFICIENT"
        receipt["failure"] = f"{type(exc).__name__}: {exc}"
    except AcquisitionFailure as exc:
        receipt["classification"] = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        receipt["failure"] = f"{type(exc).__name__}: {exc}"
    except Exception as exc:
        receipt["classification"] = "PROVENANCE_FAILURE"
        receipt["failure"] = f"{type(exc).__name__}: {exc}"

    receipt["receipt_sha256"] = stable_sha({k: v for k, v in receipt.items() if k != "receipt_sha256"})
    p = OUT / "BTC_OPTIONS_VRP_001_TARDIS_SOURCE_PROBE_RECEIPT_V0_1.json"
    p.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "classification": receipt["classification"],
        "dates_completed": len(receipt["dates"]),
        "failure": receipt["failure"],
        "receipt_sha256": receipt["receipt_sha256"],
        "safety": receipt["safety"],
    }, sort_keys=True))
    return 0 if receipt["classification"] in {"PAID_SOURCE_ROUTE_FEASIBLE", "SOURCE_ROUTE_SCHEMA_INSUFFICIENT"} else 2


if __name__ == "__main__":
    sys.exit(main())
