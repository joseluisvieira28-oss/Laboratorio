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

    def _select_universe(
        self, snapshots: dict[str, MarketSnapshot]
    ) -> tuple[str, ...]:
        if self.settings.universe_mode == "core5":
            missing = [symbol for symbol in CORE5 if symbol not in snapshots]
            if missing:
                raise MarketDataError(f"core universe incomplete: {missing}")
            return CORE5

        if self.settings.universe_mode != "liquid":
            raise RuntimeError("unsupported universe mode")

        eligible = self.feed.eligible_usdt_perpetual_symbols()
        ranked = sorted(
            (
                snap
                for symbol, snap in snapshots.items()
                if symbol in eligible and snap.quote_volume_24h >= self.settings.min_quote_volume
            ),
            key=lambda snap: snap.quote_volume_24h,
            reverse=True,
        )
        selected = tuple(snap.symbol for snap in ranked[: self.settings.max_symbols])
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
        for adapter in self.registry.adapters:
            for symbol in universe:
                decision = enforce_promotion_gate(adapter, selected[symbol])
                item = decision.to_dict()
                item["market_provider"] = provider
                decisions.append(item)
                if decision.valid_signal:
                    valid_signals.append(item)

        decision_receipt = self.store.append(
            "STRATEGY_EVALUATION",
            {
                "market_provider": provider,
                "registered_strategies": [a.strategy_id for a in self.registry.adapters],
                "decision_count": len(decisions),
                "valid_signal_count": len(valid_signals),
                "decisions": decisions,
            },
        )

        return {
            "status": "OK",
            "provider": provider,
            "universe": list(universe),
            "registered_strategies": len(self.registry.adapters),
            "valid_signals": valid_signals,
            "market_receipt": market_receipt,
            "decision_receipt": decision_receipt,
        }
