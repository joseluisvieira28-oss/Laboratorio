from __future__ import annotations

from .config import Settings
from .data_contract import CollectionBatch, DataQuality
from .engines import score_candidate
from .models import Candidate


class DreamAccountEngine:
    """Consumes normalized data only; deliberately has no HTTP or execution methods."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def evaluate(self, batch: CollectionBatch, regime: str) -> list[Candidate]:
        if not batch.gate_passed:
            return []
        output = []
        for row in batch.verified:
            if row.data_quality is not DataQuality.VERIFIED:
                continue
            if row.volume_24h is None or row.spread_pct is None:
                continue
            if row.volume_24h < self.settings.min_volume_usd or row.spread_pct > self.settings.hard_spread_pct:
                continue
            candidate = Candidate(row.symbol, row.market_type, row.price or 0.0, row.volume_24h,
                                  row.spread_pct, {}, 0.0, regime)
            score_candidate(candidate, self.settings)
            output.append(candidate)
        return sorted(output, key=lambda x: x.score, reverse=True)
