import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "research" / "market_reveal_confirmation_reaction_v01" / "h02_source_coverage_probe.py"
LAUNCHER = ROOT / "research" / "market_reveal_confirmation_reaction_v01" / "Run_MRCR_H02_Source_Coverage.cmd"


class H02SourceCoverageHygieneTests(unittest.TestCase):
    def test_probe_exact_frozen_scope(self):
        text = PROBE.read_text(encoding="utf-8")
        for token in ("BTCUSDT", "ETHUSDT", "BTC-USD", "ETH-USD"):
            self.assertIn(token, text)
        self.assertIn("wss://data-stream.binance.vision", text)
        self.assertIn("wss://advanced-trade-ws.coinbase.com", text)
        self.assertIn('"aggTrade"', text)
        self.assertIn('"market_trades"', text)
        self.assertIn('"level2"', text)

    def test_probe_is_public_and_non_target_output_only(self):
        text = PROBE.read_text(encoding="utf-8").lower()
        self.assertIn("proxy=none", text)
        self.assertIn("max_size=16_000_000", text)
        self.assertIn('"raw_payloads_persisted": false', text)
        self.assertIn('"authentication_used": false', text)
        self.assertIn('"account_endpoints_used": false', text)
        self.assertIn('"outcomes_computed": false', text)
        self.assertIn('"orders_enabled": false', text)

        forbidden = (
            "api_key",
            "api-secret",
            "private_key",
            "client_order_id",
            "/accounts",
            "/orders",
            "create_order",
            "place_order",
        )
        for token in forbidden:
            self.assertNotIn(token, text)

    def test_launcher_uses_pinned_websockets(self):
        text = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("websockets==15.0.1", text)
        self.assertIn("h02_source_coverage_probe.py", text)


if __name__ == "__main__":
    unittest.main()
