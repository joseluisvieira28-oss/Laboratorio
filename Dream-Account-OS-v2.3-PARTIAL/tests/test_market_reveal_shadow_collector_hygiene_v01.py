import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"

COLLECTOR = MODULE_DIR / "coinbase_l2_shadow_collector.py"
JOURNAL = MODULE_DIR / "shadow_journal.py"
RECOVERY = MODULE_DIR / "shadow_recovery.py"
VERIFIER = MODULE_DIR / "verify_shadow_journal.py"


class ShadowCollectorHygieneTests(unittest.TestCase):
    def test_collector_uses_public_market_data_endpoint_only(self):
        source = COLLECTOR.read_text(encoding="utf-8")
        self.assertIn("wss://advanced-trade-ws.coinbase.com", source)
        self.assertNotIn("advanced-trade-ws-user.coinbase.com", source)
        self.assertNotIn("api.coinbase.com", source)

    def test_no_credentials_or_account_mutation_tokens(self):
        source = "\n".join(
            p.read_text(encoding="utf-8")
            for p in (COLLECTOR, JOURNAL, RECOVERY, VERIFIER)
        ).lower()
        for forbidden in (
            "api_key",
            "signing_key",
            "secret_key",
            "private_key",
            "create_order",
            "cancel_order",
            "account_id",
            "portfolio_id",
            "/orders",
            "/accounts",
        ):
            self.assertNotIn(forbidden, source, forbidden)

    def test_no_scientific_outcome_or_execution_identifiers(self):
        forbidden = {
            "future_return",
            "target_return",
            "pnl",
            "sharpe",
            "profit_factor",
            "entry_signal",
            "exit_signal",
            "position_size",
            "stop_loss",
            "take_profit",
            "acceptance_threshold",
            "rejection_threshold",
        }
        seen = set()
        for path in (COLLECTOR, JOURNAL, RECOVERY, VERIFIER):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    seen.add(node.id.lower())
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    seen.add(node.name.lower())
        self.assertTrue(
            forbidden.isdisjoint(seen),
            f"forbidden runtime identifiers: {sorted(forbidden & seen)}",
        )

    def test_only_collector_has_network_import(self):
        forbidden_roots = {"requests", "httpx", "aiohttp", "websocket", "websockets"}
        for path in (JOURNAL, RECOVERY, VERIFIER):
            imported = set()
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split(".")[0])
            self.assertTrue(
                forbidden_roots.isdisjoint(imported),
                f"network import in offline component {path.name}: {imported}",
            )

        collector_tree = ast.parse(
            COLLECTOR.read_text(encoding="utf-8"),
            filename=str(COLLECTOR),
        )
        collector_imports = set()
        for node in ast.walk(collector_tree):
            if isinstance(node, ast.Import):
                collector_imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                collector_imports.add(node.module.split(".")[0])
        self.assertIn("websockets", collector_imports)


if __name__ == "__main__":
    unittest.main()
