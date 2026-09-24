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
]

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


if __name__ == "__main__":
    unittest.main()
