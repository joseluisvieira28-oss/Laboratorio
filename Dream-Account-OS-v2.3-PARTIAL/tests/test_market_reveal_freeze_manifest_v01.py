import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from freeze_manifest import (
    build_implementation_manifest,
    verify_implementation_manifest,
)


class FreezeManifestTests(unittest.TestCase):
    def test_manifest_verifies_and_detects_byte_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("alpha", encoding="utf-8")
            (root / "b.txt").write_text("beta", encoding="utf-8")

            manifest = build_implementation_manifest(
                root=root,
                relative_paths=["b.txt", "a.txt", "a.txt"],
                implementation_head_sha="abcdef1",
            )
            self.assertTrue(
                verify_implementation_manifest(
                    root=root,
                    manifest=manifest,
                )
            )
            self.assertEqual(
                [row["path"] for row in manifest["files"]],
                ["a.txt", "b.txt"],
            )

            (root / "a.txt").write_text("ALPHA", encoding="utf-8")
            self.assertFalse(
                verify_implementation_manifest(
                    root=root,
                    manifest=manifest,
                )
            )

    def test_missing_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(FileNotFoundError):
                build_implementation_manifest(
                    root=root,
                    relative_paths=["missing.txt"],
                    implementation_head_sha="abcdef1",
                )


if __name__ == "__main__":
    unittest.main()
