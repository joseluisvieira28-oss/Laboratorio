import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from state_receipt import build_state_receipt, verify_state_receipt

CORPUS = json.loads(
    (MODULE_DIR / "GOLDEN_SYNTHETIC_CORPUS_V01.json").read_text(encoding="utf-8")
)


class GoldenCorpusTests(unittest.TestCase):
    def test_all_golden_receipt_fingerprints_are_stable(self):
        self.assertGreater(len(CORPUS["cases"]), 0)
        for case in CORPUS["cases"]:
            receipt = build_state_receipt(**case["receipt_args"])
            self.assertTrue(verify_state_receipt(receipt))
            self.assertEqual(
                receipt["receipt_sha256"],
                case["expected_receipt_sha256"],
                case["case_id"],
            )

    def test_corpus_is_explicitly_non_economic(self):
        purpose = CORPUS.get("purpose", "").lower()
        self.assertIn("implementation regression", purpose)
        self.assertIn("no economic interpretation", purpose)


if __name__ == "__main__":
    unittest.main()
