"""Entirely synthetic fixtures; independent auditor makes zero exchange requests."""
import datetime as dt
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
import audit_forward

UTC=dt.timezone.utc
DAY=dt.date(2026,11,4)
EXPIRE=dt.datetime(2026,11,5,8,tzinfo=UTC)
PRICE=76500
STRIKE=76500
STAMP=int(dt.datetime(2026,11,4,8,5,2,tzinfo=UTC).timestamp()*1000)
SOURCES=("instruments","summaries","deliveries","index","atm_call","atm_put")

def fake_docs():
    meta=[]
    for suffix,kind in (("C","call"),("P","put")):
        meta.append(dict(instrument_name="BTC_USDC-5NOV26-76500-"+suffix,
                         expiration_timestamp=int(EXPIRE.timestamp()*1000),option_type=kind,
                         strike=STRIKE,kind="option",base_currency="BTC",price_index="btc_usdc",
                         quote_currency="USDC",settlement_currency="USDC",contract_size=1,
                         min_trade_amount=.01,taker_commission=.0003,is_active=True,
                         tick_size=5,tick_size_steps=[]))
    books={}
    for m in meta:
        books["atm_call" if m["option_type"]=="call" else "atm_put"]=dict(
            timestamp=STAMP,instrument_name=m["instrument_name"],state="open",
            bids=[[995,1]],asks=[[1000,1]],index_price=PRICE)
    dates=[DAY-dt.timedelta(days=i) for i in reversed(range(61))]
    data=dict(instruments=meta,summaries=[],deliveries={"data":[
         dict(date=d.isoformat(),delivery_price=PRICE) for d in dates]},
         index={"index_price":PRICE},**books)
    return data,dates

def synthetic_archive(invalid=None):
    data,dates=fake_docs()
    times=[("08:05:00.100000","08:05:00.200000"),
           ("08:05:00.300000","08:05:00.400000"),
           ("08:05:00.500000","08:05:00.600000"),
           ("08:05:01.400000","08:05:01.500000"),
           ("08:05:02.000000","08:05:02.250000"),
           ("08:05:02.000000","08:05:02.250000")]
    raw={}
    manifest=[]
    for name,(start,recv) in zip(SOURCES,times):
        body=json.dumps(dict(testnet=False,result=data[name])).encode()
        raw["raw/"+name+".json"]=body
        manifest.append(dict(name=name,sha256=hashlib.sha256(body).hexdigest(),
                             started="2026-11-04T"+start+"+00:00",
                             received="2026-11-04T"+recv+"+00:00"))
    premium=20.0
    fees=2*.01*min(.0003*PRICE,.125*1000)
    spread=.01*(2*(1000-995))
    pct=100*(spread+2*fees)/premium
    receipt=dict(freeze=audit_forward.FREEZE,mode="entry",simulation=True,
                 status="ABSTAIN_FORECAST",observed="2026-11-04T08:05:00.050000+00:00",
                 decision_at="2026-11-04T08:05:03+00:00",diagnostic_only=False,
                 orders=0,index=PRICE,expiry=EXPIRE.isoformat(),manifest=manifest,
                 chosen={"atm_call":data["atm_call"]["instrument_name"],
                         "atm_put":data["atm_put"]["instrument_name"]},
                 control_selected=True,
                 structures={"straddle":{"entry_premium":premium,"entry_fee":fees,
                     "entry_allin":premium+fees,"roundtrip_pct":pct,
                     "one_tick_allin":premium+.01*10+fees,
                     "legs":[dict(symbol=data[name]["instrument_name"],
                                  side="call" if name=="atm_call" else "put",
                                  strike=STRIKE,ask=1000,bid=995,index=PRICE,
                                  bid_depth=1,ask_depth=1,expiry=EXPIRE.isoformat())
                             for name in ("atm_call","atm_put")]}},
                 forecast={"selected":False,"forecast_net_proceeds":0,
                           "input_dates":[d.isoformat() for d in dates]})
    if invalid=="late":receipt["decision_at"]="2026-11-04T08:10:00+00:00"
    if invalid=="raw":raw["raw/index.json"]=b'{"testnet":false,"result":{"index_price":1}}'
    raw["raw/receipt.json"]=json.dumps(receipt).encode()
    raw["raw/manifest.json"]=json.dumps(manifest).encode()
    file=io.BytesIO()
    with zipfile.ZipFile(file,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for name,body in raw.items():z.writestr(name,body)
    return file.getvalue()

class ForwardAuditTests(unittest.TestCase):
    def audit(self,body):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"entry.zip";target.write_bytes(body)
            return audit_forward.audit_entry(target,hashlib.sha256(body).hexdigest(),DAY.isoformat())

    def test_control_only_synthetic_entry_independently_accepted(self):
        out=self.audit(synthetic_archive())
        self.assertEqual(out["status"],"FORWARD_DECISION_AUDITED_NOT_PROFIT")
        self.assertFalse(out["P1_selected"])
        self.assertTrue(out["C0_selected"])
        self.assertFalse(out["edge_proven"])
        self.assertEqual(out["raw_responses_verified"],6)

    def test_altered_raw_rejected_even_if_outer_archive_rehashed(self):
        with self.assertRaisesRegex(ValueError,"RAW_HASH_MISMATCH"):
            self.audit(synthetic_archive("raw"))

    def test_late_decision_rejected(self):
        with self.assertRaisesRegex(ValueError,"OUT_OF_WINDOW_DECISION"):
            self.audit(synthetic_archive("late"))

    def test_outer_archive_sha_must_be_pinned(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"entry.zip";path.write_bytes(synthetic_archive())
            with self.assertRaisesRegex(ValueError,"ENTRY_ARCHIVE_HASH_MISMATCH"):
                audit_forward.audit_entry(path,"0"*64,DAY.isoformat())

if __name__=="__main__":unittest.main()
