from __future__ import annotations

from .config import CORE5, Settings
from .evidence import EvidenceStore
from .market import MarketDataError
from .models import MarketSnapshot
from .strategy import StrategyRegistry, enforce_promotion_gate


class RadarEngine:
    def __init__(
        self,
        settings: Settings,
        feed,
        store: EvidenceStore,
        registry: StrategyRegistry,
    ) -> None:
        self.settings = settings
        self.feed = feed
        self.store = store
        self.registry = registry

    def _strategy_symbols(self) -> tuple[str, ...]:
        symbols: list[str] = []
        for adapter in self.registry.adapters:
            for symbol in getattr(adapter, "symbols", ()):
                if symbol not in symbols:
                    symbols.append(symbol)
        return tuple(symbols)

    def _select_universe(
        self, snapshots: dict[str, MarketSnapshot]
    ) -> tuple[str, ...]:
        strategy_symbols = self._strategy_symbols()

        if self.settings.universe_mode == "core5":
            required = tuple(dict.fromkeys((*CORE5, *strategy_symbols)))
            missing = [symbol for symbol in required if symbol not in snapshots]
            if missing:
                raise MarketDataError(f"required universe incomplete: {missing}")
            return required

        if self.settings.universe_mode != "liquid":
            raise RuntimeError("unsupported universe mode")

        eligible = self.feed.eligible_usdt_perpetual_symbols()
        missing_required = [
            symbol
            for symbol in strategy_symbols
            if symbol not in snapshots or symbol not in eligible
        ]
        if missing_required:
            raise MarketDataError(
                f"promoted strategy symbols unavailable: {missing_required}"
            )
        if len(strategy_symbols) > self.settings.max_symbols:
            raise MarketDataError(
                "RADAR_MAX_SYMBOLS smaller than promoted strategy requirements"
            )

        ranked = sorted(
            (
                snap
                for symbol, snap in snapshots.items()
                if symbol in eligible
                and symbol not in strategy_symbols
                and snap.quote_volume_24h >= self.settings.min_quote_volume
            ),
            key=lambda snap: snap.quote_volume_24h,
            reverse=True,
        )
        slots = self.settings.max_symbols - len(strategy_symbols)
        selected = tuple((*strategy_symbols, *(snap.symbol for snap in ranked[:slots])))
        if not selected:
            raise MarketDataError("liquid universe empty after frozen filters")
        return selected

    def run_cycle(self) -> dict:
        snapshots = self.feed.all_market_snapshots()
        universe = self._select_universe(snapshots)
        selected = self.feed.subset(snapshots, universe)
        provider = getattr(self.feed, "provider", "UNKNOWN_PUBLIC_PROVIDER")

        market_payload = {
            "provider": provider,
            "mode": self.settings.universe_mode,
            "symbols": list(universe),
            "snapshots": {k: v.to_dict() for k, v in selected.items()},
        }
        market_receipt = self.store.append("MARKET_SNAPSHOT", market_payload)

        decisions = []
        valid_signals = []
        duplicate_signals = 0

        for adapter in self.registry.adapters:
            targets = tuple(getattr(adapter, "symbols", ())) or universe
            for symbol in targets:
                if symbol not in selected:
                    raise MarketDataError(
                        f"strategy target {symbol} not present in selected universe"
                    )

                decision = enforce_promotion_gate(adapter, selected[symbol])
                item = decision.to_dict()
                item["market_provider"] = provider

                if decision.valid_signal:
                    signal_key = item.get("metadata", {}).get("signal_key")
                    if not signal_key:
                        raise RuntimeError(
                            f"promoted directional strategy {decision.strategy_id} "
                            "must provide immutable metadata.signal_key"
                        )

                    if self.store.signal_key_seen(signal_key):
                        item["duplicate_suppressed"] = True
                        duplicate_signals += 1
                    else:
                        item["duplicate_suppressed"] = False
                        signal_record = {
                            "signal_key": signal_key,
                            "strategy_id": decision.strategy_id,
                            "symbol": decision.symbol,
                            "provider": provider,
                            "direction": decision.direction.value,
                            "decision": item,
                        }
                        signal_receipt = self.store.append(
                            "VALID_SHADOW_SIGNAL", signal_record
                        )
                        item["signal_receipt"] = signal_receipt
                        valid_signals.append(item)

                decisions.append(item)

        decision_receipt = self.store.append(
            "STRATEGY_EVALUATION",
            {
                "market_provider": provider,
                "registered_strategies": [a.strategy_id for a in self.registry.adapters],
                "decision_count": len(decisions),
                "new_valid_signal_count": len(valid_signals),
                "duplicate_signal_count": duplicate_signals,
                "decisions": decisions,
            },
        )

        return {
            "status": "OK",
            "provider": provider,
            "universe": list(universe),
            "registered_strategies": len(self.registry.adapters),
            "valid_signals": valid_signals,
            "duplicate_signal_count": duplicate_signals,
            "market_receipt": market_receipt,
            "decision_receipt": decision_receipt,
        }
