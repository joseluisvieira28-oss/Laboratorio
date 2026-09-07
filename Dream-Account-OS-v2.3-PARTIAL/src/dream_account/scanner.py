from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import Settings
from .database import Journal
from .engines import classify_regime, pct_change, rvol, score_candidate
from .mexc_client import DataUnavailable, MEXCClient
from .models import Candidate, utc_now


@dataclass
class ScanResult:
    status: str
    observed_at: str
    mode: str
    regime: str | None
    pairs_scanned: int
    fast_pass: int
    deep_pass: int
    candidates: list[Candidate]
    errors: list[str]
    data_coverage_pct: float = 0.0
    api_health: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {**self.__dict__, "candidates": [c.as_dict() for c in self.candidates]}


class Scanner:
    def __init__(self, client: MEXCClient, settings: Settings, journal: Journal):
        self.client, self.settings, self.journal = client, settings, journal

    def live_scan(self) -> ScanResult:
        observed_at = utc_now()
        try:
            exchange = self.client.exchange_info()
            tickers = self.client.tickers_24h()
            symbols = {s["symbol"]: s for s in exchange["symbols"] if s.get("quoteAsset") == "USDT" and s.get("status") in {"ENABLED", "TRADING", "1"}}
            ticker_map = {t["symbol"]: t for t in tickers if t.get("symbol") in symbols}
            fast = []
            for symbol, ticker in ticker_map.items():
                try:
                    price = float(ticker.get("lastPrice", 0))
                    quote_volume = float(ticker.get("quoteVolume", 0))
                    book = self.client.book_ticker(symbol)
                    if quote_volume >= self.settings.min_volume_usd and book.spread_pct <= self.settings.hard_spread_pct:
                        fast.append((symbol, price, quote_volume, book.spread_pct))
                except (ValueError, DataUnavailable):
                    continue
            server_time = self.client.server_time()
            btc15 = self.client.klines("BTCUSDT", "15m")
            btc1h = self.client.klines("BTCUSDT", "60m")
            eth1h = self.client.klines("ETHUSDT", "60m")
            regime, confidence, reason = classify_regime(btc15, btc1h, eth1h)
            candidates = []
            for symbol, price, volume, spread in sorted(fast, key=lambda x: x[2], reverse=True)[: self.settings.deep_scan_limit]:
                candles = self.client.klines(symbol, "15m")
                changes = {"15m": pct_change(candles[-2].close, candles[-1].close), "1h": pct_change(candles[-5].close, candles[-1].close), "24h": float(ticker_map[symbol].get("priceChangePercent", 0))}
                candidate = Candidate(symbol, "SPOT", price, volume, spread, changes, rvol(candles), regime)
                score_candidate(candidate, self.settings)
                candidates.append(candidate)
            coverage = len(ticker_map) / len(symbols) * 100 if symbols else 0
            result = ScanResult("PASS", observed_at, "LIVE", regime, len(ticker_map), len(fast), len([c for c in candidates if not c.rejection_reasons]), candidates, [], round(coverage, 2), self.client.health())
            scan_id = self.journal.record_scan(observed_at, "LIVE", result.status, regime, {"confidence": confidence, "reason": reason})
            for candidate in candidates:
                self.journal.record_candidate(scan_id, candidate.as_dict())
            return result
        except DataUnavailable as exc:
            self.journal.event(observed_at, "ERROR", "DATA_LAYER_FAILURE", str(exc))
            health = self.client.health() if hasattr(self.client, "health") else {}
            result = ScanResult("FAIL_CLOSED", observed_at, "LIVE", None, 0, 0, 0, [], [str(exc)], 0.0, health)
            self.journal.record_scan(observed_at, "LIVE", result.status, None, {"errors": result.errors})
            return result
