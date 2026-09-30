from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.build_options_v21_pnl_correction_overlay_v01 import (
    CorrectionOverlayError,
    build_overlay,
)


class BuildOptionsCorrectionOverlayTests(unittest.TestCase):
    def fixture(self, root: Path):
        session=root/"session"
        session.mkdir()
        recon={
            "signal_identity":"OPTIONS-SPOTPERP-001:V2.1:2026-09-28",
            "closed_at_utc":"2026-09-30T00:00:06Z",
            "realized_net_pnl_usdt":-0.01696,
        }
        (session/"POST_TRADE_RECONCILIATION.json").write_text(
            json.dumps(recon,sort_keys=True),encoding="utf-8"
        )
        (session/"FILL_RECEIPT.json").write_text(
            json.dumps({"order":{"orderId":"111"}}),encoding="utf-8"
        )
        (session/"EXIT_EXCHANGE_ACK_1.json").write_text(
            json.dumps({"exchange_ack":{"orderId":"222"}}),encoding="utf-8"
        )
        catalog={
            "catalog_id":"X",
            "source_commit":"abc",
            "source_evidence_git_blob_sha":"def",
            "entries":[{
                "signal_identity":recon["signal_identity"],
                "entry_order_id":"111",
                "exit_order_id":"222",
                "stored_net_pnl_usdt":-0.01696,
                "corrected_realized_net_pnl_usdt":-0.03032779,
                "entry_fee_usdt":0.00667659,
                "exit_fee_usdt":0.0066912,
            }],
        }
        catalog_path=root/"catalog.json"
        catalog_path.write_text(json.dumps(catalog),encoding="utf-8")
        return catalog_path, session/"POST_TRADE_RECONCILIATION.json"

    def test_overlay_is_bound_to_receipt_hash_and_order_identity(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            catalog,recon=self.fixture(root)
            before=recon.read_bytes()
            out=build_overlay(catalog_path=catalog,receipt_root=root)
            self.assertEqual(out["entry_count"],1)
            row=out["entries"][0]
            self.assertEqual(row["entry_order_id"],"111")
            self.assertEqual(row["exit_order_id"],"222")
            self.assertEqual(len(row["original_receipt_sha256"]),64)
            self.assertAlmostEqual(row["corrected_realized_net_pnl_usdt"],-0.03032779)
            self.assertEqual(recon.read_bytes(),before)

    def test_wrong_exit_identity_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            catalog,_=self.fixture(root)
            payload=json.loads(catalog.read_text(encoding="utf-8"))
            payload["entries"][0]["exit_order_id"]="999"
            catalog.write_text(json.dumps(payload),encoding="utf-8")
            with self.assertRaises(CorrectionOverlayError):
                build_overlay(catalog_path=catalog,receipt_root=root)


if __name__=="__main__":
    unittest.main()
