import unittest
import hashlib
from tempfile import TemporaryDirectory
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
from engine.three_convex_v09.authority_gate import verify_detached_permit,canonical,sha,AuthorityHalt

SIGNAL_ID="SOL_CONVEX_NATIVE_5M:1000000"
OID="CL8"+hashlib.sha256((SIGNAL_ID+"|LONG").encode()).hexdigest()[:28]
ACCOUNT="a"*64

def fixture():
    order={"symbol":"SOL_USDT","price":0,"vol":1,"leverage":10,
           "side":1,"type":5,"openType":1,"positionMode":1,
           "externalOid":OID}
    permit={"version":1,"venue":"MEXC_FUTURES","scope":"ONE_ENTRY",
            "symbol":"SOL_USDT","lane":"SOL_CONVEX_NATIVE_5M",
            "signal_id":SIGNAL_ID,
            "side":"LONG","position_mode":"HEDGE","margin_mode":"ISOLATED",
            "leverage":10,"contracts":1,"max_modeled_loss_usdt":"0.45",
            "signal_close_ms":1000000,"issued_ms":1001000,"expires_ms":1005000,
            "nonce":"1"*32,"account_snapshot_hash":ACCOUNT,"order_sha256":sha(order)}
    return permit,order

class RiskPermitTests(unittest.TestCase):
    def setUp(self):
        self.t=TemporaryDirectory()
        self.key=Ed25519PrivateKey.generate()
        self.pub=self.key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)
        self.db=Path(self.t.name)/"nonces.sqlite3"
    def tearDown(self):self.t.cleanup()
    def runit(self,permit,order,*,sig=None,now=1002000,account=ACCOUNT):
        return verify_detached_permit(public_key_bytes=self.pub,permit=permit,
             signature_bytes=sig if sig is not None else self.key.sign(canonical(permit)),
             proposed_order=order,now_ms=now,account_snapshot_hash=account,ledger_nonce_db=self.db)
    def test_valid_detached_signature_burns_nonce_no_trade_authority(self):
        p,o=fixture()
        x=self.runit(p,o)
        self.assertEqual(x["status"],"CRYPTOGRAPHIC_PERMIT_VERIFIED_AND_BURNED")
        self.assertFalse(x["actual_live_order_authorization"])
    def test_replay_after_restart_rejected(self):
        p,o=fixture();self.runit(p,o)
        with self.assertRaisesRegex(AuthorityHalt,"ALREADY_BURNED"):
            self.runit(p,o)
    def test_fake_signature_forbidden(self):
        p,o=fixture()
        with self.assertRaisesRegex(AuthorityHalt,"SIGNATURE_NOT_VERIFIED"):
            self.runit(p,o,sig=b"x"*64)
    def test_body_tamper_forbidden(self):
        p,o=fixture();o["vol"]=2
        with self.assertRaisesRegex(AuthorityHalt,"PAYLOAD_TAMPERED"):
            self.runit(p,o)
    def test_stale_or_delayed_entry_forbidden(self):
        p,o=fixture()
        with self.assertRaisesRegex(AuthorityHalt,"STALE_OR_OUTSIDE_V5_ENTRY"):
            self.runit(p,o,now=2000000)
    def test_mismatched_broker_account_fingerprint_forbidden(self):
        p,o=fixture()
        with self.assertRaisesRegex(AuthorityHalt,"BROKER_ACCOUNT_RECEIPT_NOT_BOUND"):
            self.runit(p,o,account="b"*64)
    def test_arbitrary_64hex_digest_cannot_authorize(self):
        p,o=fixture()
        with self.assertRaisesRegex(AuthorityHalt,"SIGNATURE_NOT_VERIFIED"):
            self.runit(p,o,sig=("f"*64).encode())
    def test_signature_cannot_move_to_another_signal(self):
        p,o=fixture()
        p["signal_id"]="SOL_CONVEX_NATIVE_5M:1000001"
        with self.assertRaisesRegex(AuthorityHalt,"SIGNAL_ID_NOT_BOUND"):
            self.runit(p,o)
    def test_signed_signal_cannot_be_reused_for_other_entry_oid(self):
        p,o=fixture()
        o["externalOid"]="CL8"+"c"*28
        p["order_sha256"]=sha(o)
        with self.assertRaisesRegex(AuthorityHalt,"ENTRY_EXTERNAL_OID_NOT_BOUND"):
            self.runit(p,o)

    def test_wrong_lane_symbol_forbidden(self):
        p,o=fixture();p["symbol"]="BNB_USDT"
        with self.assertRaisesRegex(AuthorityHalt,"LANE_SYMBOL_MISMATCH"):
            self.runit(p,o)
    def test_cross_margin_forbidden(self):
        p,o=fixture();p["margin_mode"]="CROSS"
        with self.assertRaisesRegex(AuthorityHalt,"MARGIN_MODE_UNVERIFIED"):
            self.runit(p,o)
    def test_wrong_10x_forbidden(self):
        p,o=fixture();p["leverage"]=20
        with self.assertRaisesRegex(AuthorityHalt,"RISK_SCOPE_EXCEEDED"):
            self.runit(p,o)
    def test_over_budget_forbidden(self):
        p,o=fixture();p["max_modeled_loss_usdt"]="0.51"
        with self.assertRaisesRegex(AuthorityHalt,"CASH_RISK_TOO_HIGH"):
            self.runit(p,o)
    def test_unexpected_payload_fields_forbidden(self):
        p,o=fixture();p["ignore_stop"]=True
        with self.assertRaisesRegex(AuthorityHalt,"UNEXPECTED_PERMIT_FIELDS"):
            self.runit(p,o)
if __name__=="__main__":unittest.main()
