import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"

COLLECTOR = MODULE_DIR / "h02_frozen_scope_shadow_collector.py"
JOURNAL = MODULE_DIR / "h02_scope_journal.py"
RECOVERY = MODULE_DIR / "h02_scope_recovery.py"
VERIFIER = MODULE_DIR / "verify_h02_frozen_scope_shadow.py"
LAUNCHER = MODULE_DIR / "Run_MRCR_H02_Frozen_Scope_Shadow.cmd"


class H02FrozenScopeShadowHygieneTests(unittest.TestCase):
    def test_collector_scope_is_exactly_frozen(self):
        source = COLLECTOR.read_text(encoding="utf-8")
        for token in ("BTCUSDT", "ETHUSDT", "BTC-USD", "ETH-USD"):
            self.assertIn(token, source)
        self.assertIn('BINANCE_SYMBOLS = ("BTCUSDT", "ETHUSDT")', source)
        self.assertIn('COINBASE_PRODUCTS = ("BTC-USD", "ETH-USD")', source)
        self.assertIn("aggTrade", source)
        self.assertIn("depth@100ms", source)
        self.assertIn("level2", source)
        self.assertIn("market_trades", source)

    def test_public_market_data_endpoints_only(self):
        source = COLLECTOR.read_text(encoding="utf-8")
        self.assertIn("wss://data-stream.binance.vision", source)
        self.assertIn("https://data-api.binance.vision/api/v3/depth", source)
        self.assertIn("wss://advanced-trade-ws.coinbase.com", source)
        self.assertNotIn("advanced-trade-ws-user.coinbase.com", source)
        self.assertNotIn("ws-api.binance.com", source)

    def test_no_credentials_accounts_or_orders(self):
        source = "\n".join(
            p.read_text(encoding="utf-8")
            for p in (COLLECTOR, JOURNAL, RECOVERY, VERIFIER)
        ).lower()
        for forbidden in (
            "api_key",
            "api-secret",
            "signing_key",
            "secret_key",
            "private_key",
            "client_order_id",
            "create_order",
            "place_order",
            "cancel_order",
            "/accounts",
            "/orders",
        ):
            self.assertNotIn(forbidden, source, forbidden)

    def test_offline_components_have_no_network_imports(self):
        forbidden_roots = {
            "requests", "httpx", "aiohttp", "websocket", "websockets",
            "urllib", "socket"
        }
        for path in (JOURNAL, RECOVERY, VERIFIER):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split(".")[0])
            self.assertTrue(
                forbidden_roots.isdisjoint(imported),
                f"network import in offline component {path.name}: {imported}",
            )

    def test_collector_is_only_network_component(self):
        tree = ast.parse(COLLECTOR.read_text(encoding="utf-8"), filename=str(COLLECTOR))
        roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".")[0])
        self.assertIn("websockets", roots)
        self.assertIn("urllib", roots)

    def test_fail_closed_boundary_fields_exist(self):
        source = COLLECTOR.read_text(encoding="utf-8").lower()
        for token in (
            '"authentication_used": false',
            '"account_endpoints_used": false',
            '"signals_computed": false',
            '"outcomes_computed": false',
            '"orders_enabled": false',
            '"target_schedule_used": false',
            '"target_observation_authorized": false',
            '"promotion_credit": "none"',
        ):
            self.assertIn(token, source)

    def test_launcher_pins_dependency_and_runs_independent_verifier(self):
        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("websockets==15.0.1", source)
        self.assertIn("h02_frozen_scope_shadow_collector.py", source)
        self.assertIn("verify_h02_frozen_scope_shadow.py", source)
        self.assertIn("MRCR H02 FROZEN-SCOPE SHADOW: PASS", source)


if __name__ == "__main__":
    unittest.main()
