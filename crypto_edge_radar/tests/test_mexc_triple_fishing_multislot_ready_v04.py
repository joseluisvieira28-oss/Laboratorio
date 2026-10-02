from __future__ import annotations

from dataclasses import dataclass
import unittest

from scripts.mexc_triple_fishing_multislot_ready_v04 import evaluate_public_contracts


@dataclass
class Snap:
    ask_price: float


class FakePublic:
    def __init__(self):
        self._px={
            "BTCUSDT":85000.0,
            "BNBUSDT":760.0,
            "ETHUSDT":2700.0,
            "SOLUSDT":118.0,
            "XRPUSDT":1.34,
            "DOGEUSDT":0.095,
        }
        self._size={
            "BTC_USDT":0.0001,
            "BNB_USDT":0.01,
            "ETH_USDT":0.01,
            "SOL_USDT":0.1,
            "XRP_USDT":1.0,
            "DOGE_USDT":100.0,
        }

    def all_market_snapshots(self):
        return {k:Snap(v) for k,v in self._px.items()}

    def contract_row(self,symbol):
        return {
            "symbol":symbol,
            "contractSize":self._size[symbol],
            "minVol":1,
            "volUnit":1,
            "apiAllowed":True,
            "state":0,
            "futureType":1,
        }


class MultislotReadinessV04Tests(unittest.TestCase):
    def test_small_fish_cap_keeps_three_distinct_routes_possible(self):
        out=evaluate_public_contracts(public=FakePublic(),lane_cap_usdt=10)
        self.assertTrue(out["minimum_three_distinct_route_capacity_feasible"])
        self.assertTrue(out["symbols"]["BTC_USDT"]["fits_lane_cap"])
        self.assertTrue(out["symbols"]["BNB_USDT"]["fits_lane_cap"])
        self.assertTrue(out["symbols"]["XRP_USDT"]["fits_lane_cap"])
        self.assertFalse(out["symbols"]["ETH_USDT"]["fits_lane_cap"])
        self.assertFalse(out["symbols"]["SOL_USDT"]["fits_lane_cap"])

    def test_cap_too_small_blocks_minimum_three_route_feasibility(self):
        out=evaluate_public_contracts(public=FakePublic(),lane_cap_usdt=1)
        self.assertFalse(out["minimum_three_distinct_route_capacity_feasible"])


if __name__=="__main__":
    unittest.main()
