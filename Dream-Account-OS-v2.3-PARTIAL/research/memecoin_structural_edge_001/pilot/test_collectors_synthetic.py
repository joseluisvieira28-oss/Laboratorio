#!/usr/bin/env python3
"""Synthetic, outcome-free tests for MSEL-001 pilot collectors."""

import struct
import unittest

from collect_25_creates import (
    BUY_DISC,
    CREATE_DISC,
    PUMP_PROGRAM,
    b58encode,
    decode_create_data,
    extract_creates,
)


def borsh_string(value: str) -> bytes:
    raw = value.encode("utf-8")
    return struct.pack("<I", len(raw)) + raw


class CollectorSyntheticTests(unittest.TestCase):
    def test_historical_create_roundtrip(self) -> None:
        creator_raw = bytes(range(1, 33))
        payload = (
            CREATE_DISC
            + borsh_string("MSEL TEST")
            + borsh_string("MSEL")
            + borsh_string("ipfs://example")
            + creator_raw
        )
        decoded = decode_create_data(b58encode(payload))
        self.assertEqual(decoded["name"], "MSEL TEST")
        self.assertEqual(decoded["symbol"], "MSEL")
        self.assertEqual(decoded["uri"], "ipfs://example")
        self.assertEqual(decoded["origin_creator"], b58encode(creator_raw))
        self.assertEqual(decoded["trailing_bytes"], "0")

    def test_extract_create_separates_creator_user_payer_and_detects_same_tx_buy(self) -> None:
        creator_raw = bytes(range(1, 33))
        create_payload = (
            CREATE_DISC
            + borsh_string("MSEL TEST")
            + borsh_string("MSEL")
            + borsh_string("ipfs://example")
            + creator_raw
        )
        buy_payload = BUY_DISC + struct.pack("<QQ", 1, 2)

        payer = "11111111111111111111111111111111"
        mint = "So11111111111111111111111111111111111111112"
        user = "Vote111111111111111111111111111111111111111"
        keys = [
            payer,
            "MintAuth111111111111111111111111111111111",
            "Curve11111111111111111111111111111111111",
            "AssocCurve1111111111111111111111111111111",
            "Global1111111111111111111111111111111111",
            "Meta11111111111111111111111111111111111",
            "Metadata111111111111111111111111111111111",
            user,
            PUMP_PROGRAM,
        ]
        item = {
            "slot": 1,
            "blockTime": 1749817334,
            "transactionIndex": 3,
            "transaction": {
                "signatures": ["sig-test"],
                "message": {
                    "accountKeys": keys,
                    "instructions": [
                        {
                            "programIdIndex": 8,
                            "accounts": list(range(8)),
                            "data": b58encode(create_payload),
                        },
                        {
                            "programIdIndex": 8,
                            "accounts": [4, 0, 0, 2, 3, 7],
                            "data": b58encode(buy_payload),
                        },
                    ],
                },
            },
            "meta": {"loadedAddresses": {"writable": [], "readonly": []}, "innerInstructions": []},
        }
        records = extract_creates(item, 1)
        self.assertEqual(len(records), 1)
        rec = records[0]
        self.assertEqual(rec["mint"], payer)
        self.assertEqual(rec["tx_user"], user)
        self.assertEqual(rec["fee_payer"], payer)
        self.assertEqual(rec["origin_creator"], b58encode(creator_raw))
        self.assertTrue(rec["same_tx_pump_buy"])
        self.assertEqual(rec["transaction_index"], 3)


if __name__ == "__main__":
    unittest.main()
