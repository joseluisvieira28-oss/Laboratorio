"""Local fixture smoke checks for settlement audit. No market access."""
import unittest
from decimal import Decimal as D
import audit_settlement

class SettlementMathTests(unittest.TestCase):
    def test_no_friday_fee_on_thursday(self):
        import datetime as dt
        leg={"meta":{"strike":76500,"option_type":"call"}}
        self.assertEqual(audit_settlement.payoff([leg],D(80000),dt.datetime(2026,11,5,8,tzinfo=dt.timezone.utc)),(D(35),D(0)))
    def test_friday_fee_is_charged_once(self):
        import datetime as dt
        leg={"meta":{"strike":76500,"option_type":"call"}}
        gross,fee=audit_settlement.payoff([leg],D(80000),dt.datetime(2026,11,6,8,tzinfo=dt.timezone.utc))
        self.assertEqual(gross,D(35))
        self.assertEqual(fee,D(".12"))
    def test_cost_takes_one_adverse_tick(self):
        leg={"ask":D(1000),"index":D(76500),"meta":{"tick_size":5,"tick_size_steps":[]}}
        self.assertEqual(audit_settlement.entry_cost([leg],1,D(1)),D("10.2795"))
class SettlementReceiptTests(unittest.TestCase):
    def make(self,missing=False,replace_net=False):
        import hashlib, io, json, zipfile
        from pathlib import Path
        from test_audit_forward import synthetic_archive
        entry=synthetic_archive()
        with zipfile.ZipFile(io.BytesIO(entry)) as z:
            entry_hash=hashlib.sha256(z.read("raw/receipt.json")).hexdigest()
        result=dict(testnet=False,result={"data":[] if missing else [
            {"date":"2026-11-05","delivery_price":80000}]})
        source=json.dumps(result).encode()
        item=dict(name="settlement",
                  url="https://www.deribit.com/api/v2/public/get_delivery_prices?index_name=btc_usdc&count=100",
                  started="2026-11-06T08:05:01+00:00",
                  received="2026-11-06T08:05:02+00:00",
                  sha256=hashlib.sha256(source).hexdigest())
        status="UNSETTLED" if missing else "OFFICIAL_DELIVERY_SIMULATED_PNL"
        receipt=dict(status=status,freeze=audit_settlement.independent.FREEZE,
                     entry_sha256=entry_hash,simulation=True,manifest=[item])
        if not missing:
            receipt.update(terminal=80000,risk=20.559,gross=35,delivery=0,
                           control_net=999 if replace_net else 14.441,
                           primary_net=0,stress_net=0)
        buffer=io.BytesIO()
        with zipfile.ZipFile(buffer,"w") as z:
            z.writestr("raw/receipt.json",json.dumps(receipt))
            z.writestr("raw/manifest.json",json.dumps([item]))
            z.writestr("raw/settlement.json",source)
        settle=buffer.getvalue()
        return entry,settle

    def check(self,entry,settle):
        import hashlib,tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            a,b=Path(tmp)/"entry.zip",Path(tmp)/"settle.zip"
            a.write_bytes(entry);b.write_bytes(settle)
            return audit_settlement.audit(a,hashlib.sha256(entry).hexdigest(),
                                         b,hashlib.sha256(settle).hexdigest(),"2026-11-04")

    def test_complete_control_expiry_is_audited_without_claiming_edge(self):
        receipt=self.check(*self.make())
        self.assertEqual(receipt["status"],"OFFICIAL_SETTLEMENT_INDEPENDENTLY_AUDITED_NOT_EDGE")
        self.assertEqual(receipt["P1_net_usdc"],"0")
        self.assertEqual(receipt["C0_net_usdc"],"14.441")
        self.assertFalse(receipt["edge_proven"])

    def test_missing_delivery_stays_unsettled(self):
        receipt=self.check(*self.make(missing=True))
        self.assertEqual(receipt["status"],"UNSETTLED")
        self.assertFalse(receipt["edge_proven"])

    def test_wrong_settlement_pnl_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"SETTLEMENT_MISMATCH_control_net"):
            self.check(*self.make(replace_net=True))

if __name__=="__main__":unittest.main()
