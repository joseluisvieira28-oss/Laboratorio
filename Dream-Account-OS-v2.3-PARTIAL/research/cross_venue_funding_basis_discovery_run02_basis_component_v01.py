"""Authorized Discovery Run 02: frozen boundary basis/price component.

Uses only public Binance USD-M 1h contract klines and Hyperliquid 1h candleSnapshot
at the frozen entry/exit boundaries. No 2026, trading, slippage imputation, APR/APY,
Sharpe, tuning, or full-mechanism classification.
"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.parse
import urllib.request
from decimal import Decimal, getcontext
from pathlib import Path
from typing import Any, Mapping

getcontext().prec = 40

LAB_ID = "CROSS_VENUE_FUNDING_BASIS_LAB_V01"
RUN_ID = "CROSS_VENUE_FUNDING_BASIS_DISCOVERY_RUN02_BASIS_COMPONENT_V01"
ENTRY_MS = 1725148800000  # 2024-09-01T00:00:00Z
EXIT_OPEN_MS = 1767222000000  # 2025-12-31T23:00:00Z
EXIT_END_MS = 1767225599999  # 2025-12-31T23:59:59.999Z
LOCKED_2026_MS = 1767225600000
IMMOBILIZED_CAPITAL = Decimal("1.50")

class DiscoveryFailure(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DiscoveryFailure(message)


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected object: {path}")
    return value


def validate_governance(root: Path) -> None:
    auth = load_json(root / "CROSS_VENUE_FUNDING_BASIS_DISCOVERY_AUTHORIZATION_V01.json")
    contract = load_json(root / "CROSS_VENUE_FUNDING_BASIS_DISCOVERY_CONTRACT_V01.json")
    freeze = load_json(root / "CROSS_VENUE_FUNDING_BASIS_DISCOVERY_BASIS_COMPONENT_FREEZE_V01.json")
    closeout = load_json(root / "CROSS_VENUE_FUNDING_BASIS_DISCOVERY_RUN01_CLOSEOUT_V01.json")
    require(auth.get("status") == "EXPLICIT_DISCOVERY_AUTHORIZED", "Discovery authorization missing")
    require(contract.get("status") == "FROZEN_BEFORE_DISCOVERY_OUTCOMES", "Discovery contract missing")
    require(freeze.get("status") == "FROZEN_BEFORE_BASIS_PRICE_OUTCOMES", "Run02 freeze missing")
    require(closeout.get("status") == "RUN01_CLOSED", "Run01 not closed")
    require(closeout.get("edge_status") == "UNPROVEN", "edge status drift")
    require(closeout.get("tuning_performed") is False, "Run01 tuning detected")
    require(ENTRY_MS < EXIT_OPEN_MS < EXIT_END_MS < LOCKED_2026_MS, "Run02 boundary reaches 2026")


def request_json(req: urllib.request.Request) -> Any:
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_binance_boundary(symbol: str, open_ms: int) -> list[Any]:
    require(symbol in {"BTCUSDT", "ETHUSDT"}, "Binance symbol outside scope")
    require(open_ms < LOCKED_2026_MS, "Binance request reaches 2026")
    params = urllib.parse.urlencode({
        "symbol": symbol,
        "interval": "1h",
        "startTime": open_ms,
        "endTime": open_ms + 3599999,
        "limit": 2,
    })
    req = urllib.request.Request(
        f"https://fapi.binance.com/fapi/v1/klines?{params}",
        headers={"User-Agent": "DreamAccountOS-Research-Discovery/0.2"},
        method="GET",
    )
    rows = request_json(req)
    require(isinstance(rows, list), "unexpected Binance kline response")
    matches = [r for r in rows if isinstance(r, list) and len(r) >= 7 and int(r[0]) == open_ms]
    require(len(matches) == 1, f"Binance boundary candle not unique: {symbol} {open_ms}")
    return matches[0]


def fetch_hl_boundary(coin: str, open_ms: int) -> Mapping[str, Any]:
    require(coin in {"BTC", "ETH"}, "Hyperliquid coin outside scope")
    require(open_ms < LOCKED_2026_MS, "Hyperliquid request reaches 2026")
    payload = json.dumps({
        "type": "candleSnapshot",
        "req": {"coin": coin, "interval": "1h", "startTime": open_ms, "endTime": open_ms + 3599999},
    }, separators=(",", ":")).encode("utf-8")
    req = urllib.request.Request(
        "https://api.hyperliquid.xyz/info",
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "DreamAccountOS-Research-Discovery/0.2"},
        method="POST",
    )
    rows = request_json(req)
    require(isinstance(rows, list), "unexpected Hyperliquid candle response")
    matches = [r for r in rows if isinstance(r, dict) and int(r.get("t", -1)) == open_ms]
    require(len(matches) == 1, f"Hyperliquid boundary candle not unique: {coin} {open_ms}")
    require(int(matches[0].get("T", -1)) < LOCKED_2026_MS, "Hyperliquid candle closes in 2026")
    return matches[0]


def compute_basis_component(b_entry: Decimal, b_exit: Decimal, h_entry: Decimal, h_exit: Decimal) -> dict[str, Any]:
    require(all(x > 0 for x in (b_entry, b_exit, h_entry, h_exit)), "nonpositive boundary price")
    q = Decimal("2") / (b_entry + h_entry)
    b_entry_notional = q * b_entry
    h_entry_notional = q * h_entry
    total_entry_notional = b_entry_notional + h_entry_notional
    capital = total_entry_notional * Decimal("0.75")
    require(abs(total_entry_notional - Decimal("2")) < Decimal("1e-30"), "normalization drift")
    require(abs(capital - IMMOBILIZED_CAPITAL) < Decimal("1e-30"), "capital normalization drift")
    b_pnl = q * (b_exit - b_entry)
    h_pnl = q * (h_entry - h_exit)
    basis_pnl = b_pnl + h_pnl
    return {
        "equal_base_quantity": str(q),
        "binance_entry_notional": str(b_entry_notional),
        "hyperliquid_entry_notional": str(h_entry_notional),
        "total_entry_notional": str(total_entry_notional),
        "normalized_immobilized_capital": str(capital),
        "binance_long_price_pnl": str(b_pnl),
        "hyperliquid_short_price_pnl": str(h_pnl),
        "cross_venue_basis_price_component": str(basis_pnl),
        "basis_component_return_on_immobilized_capital": str(basis_pnl / capital),
        "basis_component_positive": basis_pnl > 0,
    }


def build_run(root: Path) -> dict[str, Any]:
    validate_governance(root)
    assets = {}
    source_hashes = {}
    for asset, b_symbol, h_coin in (("BTC", "BTCUSDT", "BTC"), ("ETH", "ETHUSDT", "ETH")):
        b_in = fetch_binance_boundary(b_symbol, ENTRY_MS)
        b_out = fetch_binance_boundary(b_symbol, EXIT_OPEN_MS)
        h_in = fetch_hl_boundary(h_coin, ENTRY_MS)
        h_out = fetch_hl_boundary(h_coin, EXIT_OPEN_MS)
        source_hashes[asset] = {
            "binance_entry_sha256": canonical_sha256(b_in),
            "binance_exit_sha256": canonical_sha256(b_out),
            "hyperliquid_entry_sha256": canonical_sha256(h_in),
            "hyperliquid_exit_sha256": canonical_sha256(h_out),
        }
        b_entry = Decimal(str(b_in[1]))
        b_exit = Decimal(str(b_out[4]))
        h_entry = Decimal(str(h_in["o"]))
        h_exit = Decimal(str(h_out["c"]))
        component = compute_basis_component(b_entry, b_exit, h_entry, h_exit)
        component.update({
            "binance_entry_price": str(b_entry),
            "binance_exit_price": str(b_exit),
            "hyperliquid_entry_price": str(h_entry),
            "hyperliquid_exit_price": str(h_exit),
            "entry_candle_open_ms": ENTRY_MS,
            "exit_candle_open_ms": EXIT_OPEN_MS,
        })
        assets[asset] = component
    combined = (
        Decimal(assets["BTC"]["basis_component_return_on_immobilized_capital"]) +
        Decimal(assets["ETH"]["basis_component_return_on_immobilized_capital"])
    ) / Decimal("2")
    receipt = {
        "schema_version": "0.1",
        "lab_id": LAB_ID,
        "run_id": RUN_ID,
        "phase": "DISCOVERY",
        "status": "RUN02_COMPLETE",
        "classification": "BASIS_PRICE_COMPONENT_DIAGNOSTIC_ONLY_NOT_FULL_MECHANISM_REPLICATION",
        "window": {"entry_candle_open_ms": ENTRY_MS, "exit_candle_open_ms": EXIT_OPEN_MS},
        "source_boundary_sha256": source_hashes,
        "assets": assets,
        "equal_deployed_capital_50_50_combined_basis_component_return": str(combined),
        "full_mechanism_replication_status": "PENDING_COMPATIBLE_SETTLEMENT_NOTIONAL_PROVENANCE",
        "historical_executable_return_claim_authorized": False,
        "slippage_imputed": False,
        "apr_apy_computed": False,
        "sharpe_sortino_computed": False,
        "reverse_orientation_computed": False,
        "tuning_performed": False,
        "locked_2026_market_data_accessed": False,
        "mexc_2025_accessed": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
        "exchange_mutation_used": False,
        "edge_status": "UNPROVEN",
    }
    receipt["receipt_sha256"] = canonical_sha256(receipt)
    return receipt


def main() -> None:
    here = Path(__file__).resolve().parent
    output = Path(os.environ.get("DISCOVERY_RUN02_RECEIPT", str(here.parent / "CROSS_VENUE_FUNDING_BASIS_DISCOVERY_RUN02_BASIS_COMPONENT_V01_RECEIPT.json")))
    receipt = build_run(here)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "classification": receipt["classification"],
        "BTC": receipt["assets"]["BTC"],
        "ETH": receipt["assets"]["ETH"],
        "combined_basis_component_return": receipt["equal_deployed_capital_50_50_combined_basis_component_return"],
        "full_mechanism_replication_status": receipt["full_mechanism_replication_status"],
        "edge_status": receipt["edge_status"],
        "receipt_sha256": receipt["receipt_sha256"],
    }, sort_keys=True))

if __name__ == "__main__":
    main()
