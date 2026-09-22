from __future__ import annotations

import ast
from pathlib import Path
from unittest import TestCase


ROOT = Path(__file__).resolve().parents[1]
V02 = ROOT / "tests" / "fixtures" / "ced1d_0031_prospective_shadow_collector_v02_reference.py.txt"
V03 = ROOT / "radar" / "ced1d_render_shadow_collector_v03.py"


def functions(path: Path) -> dict[str, str]:
    source = path.read_text()
    tree = ast.parse(source)
    lines = source.splitlines()
    out = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            segment = "\n".join(lines[node.lineno - 1 : node.end_lineno])
            out[node.name] = segment
    return out


class CED1DRenderMigrationEquivalenceTests(TestCase):
    def test_all_scientific_mechanics_functions_are_source_identical_to_v02(self):
        a = functions(V02)
        b = functions(V03)
        self.assertEqual(set(a), set(b))
        allowed_changed = {"public_funding", "main"}
        for name in sorted(set(a) - allowed_changed):
            self.assertEqual(a[name], b[name], f"unexpected V0.3 function drift: {name}")

    def test_only_authorized_functions_changed(self):
        a = functions(V02)
        b = functions(V03)
        changed = {name for name in a if a[name] != b[name]}
        self.assertEqual(changed, {"public_funding", "main"})

    def test_main_changes_are_boundary_and_receipt_metadata_only(self):
        a = functions(V02)["main"]
        b = functions(V03)["main"]
        normalized = b
        normalized = normalized.replace("2026-09-23T00:00:00Z", "2026-09-19T00:00:00Z")
        normalized = normalized.replace(
            "CED1D_0031_RENDER_SHADOW_RECEIPT_V0.3",
            "CED1D_0031_PROSPECTIVE_SHADOW_RECEIPT_V0.2",
        )
        normalized = normalized.replace(
            "CED1D_0031_RENDER_SHADOW_LEDGER_V0.3.csv",
            "CED1D_0031_PROSPECTIVE_SHADOW_LEDGER.csv",
        )
        self.assertEqual(a, normalized)

    def test_public_funding_only_adds_exact_schema_validation_and_official_host_constant_handles_route(self):
        a = functions(V02)["public_funding"]
        b = functions(V03)["public_funding"]
        # Core output rows remain fundingTime + fundingRate only.
        self.assertIn('out.append({"fundingTime":ft,"fundingRate":rate})', a)
        self.assertIn('out.append({"fundingTime":ft,"fundingRate":rate})', b)
        self.assertIn('"markPrice" not in r', b)
        self.assertIn("FUNDING_MARKPRICE_NUMERIC", b)


if __name__ == "__main__":
    import unittest
    unittest.main()
