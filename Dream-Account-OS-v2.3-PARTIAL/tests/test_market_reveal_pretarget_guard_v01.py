import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"

CODE_FILES = [
    MODULE_DIR / "measurements.py",
    MODULE_DIR / "source_adapters.py",
    MODULE_DIR / "decision_boundary.py",
    MODULE_DIR / "order_book.py",
    MODULE_DIR / "state_reconstruction.py",
    MODULE_DIR / "book_replay.py",
]

PROBE_FILE = MODULE_DIR / "coinbase_level2_local_probe.py"

FORBIDDEN_IDENTIFIERS = {
    "future_return",
    "target_return",
    "pnl",
    "sharpe",
    "profit_factor",
    "position_size",
    "entry_signal",
    "exit_signal",
    "stop_loss",
    "take_profit",
    "acceptance_threshold",
    "rejection_threshold",
}


class PreTargetGuardTests(unittest.TestCase):
    def test_no_target_or_trading_identifiers_in_runtime_code(self):
        seen = set()
        for path in CODE_FILES:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    seen.add(node.id.lower())
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    seen.add(node.name.lower())
        self.assertTrue(
            FORBIDDEN_IDENTIFIERS.isdisjoint(seen),
            f"forbidden identifiers found: {sorted(FORBIDDEN_IDENTIFIERS & seen)}",
        )

    def test_no_network_imports_in_pretarget_runtime(self):
        forbidden_roots = {"requests", "httpx", "aiohttp", "websocket", "websockets"}
        imported = set()
        for path in CODE_FILES:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split(".")[0])
        self.assertTrue(
            forbidden_roots.isdisjoint(imported),
            f"network imports found: {sorted(forbidden_roots & imported)}",
        )

    def test_coinbase_probe_has_no_file_persistence_calls(self):
        tree = ast.parse(PROBE_FILE.read_text(encoding="utf-8"), filename=str(PROBE_FILE))
        dangerous = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "open":
                    dangerous.append("open")
                if isinstance(node.func, ast.Attribute) and node.func.attr in {
                    "write_text",
                    "write_bytes",
                    "write",
                    "writelines",
                }:
                    dangerous.append(node.func.attr)
        self.assertEqual(dangerous, [], f"probe persistence calls found: {dangerous}")

    def test_coinbase_probe_is_public_market_data_only(self):
        source = PROBE_FILE.read_text(encoding="utf-8")
        self.assertIn("wss://advanced-trade-ws.coinbase.com", source)
        self.assertNotIn("advanced-trade-ws-user.coinbase.com", source)
        self.assertNotIn("api.coinbase.com", source)
        self.assertNotIn("os.environ", source)
        self.assertNotIn("API_KEY", source)
        self.assertNotIn("SIGNING_KEY", source)


if __name__ == "__main__":
    unittest.main()
