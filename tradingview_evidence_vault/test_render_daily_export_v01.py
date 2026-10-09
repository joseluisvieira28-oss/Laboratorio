"""Synthetic tests. These tests never contact Render or any exchange."""
from datetime import date, datetime, timezone
from pathlib import Path
import hashlib
import json
import tempfile
import unittest
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import render_daily_export_v01 as a
import vault

DAY=date(2026,10,7)
START=int(datetime(DAY.year,DAY.month,DAY.day,tzinfo=timezone.utc).timestamp()*1000)

def receipt(i):
    close=START+i*a.BAR_MS
    payload={"lab_id":vault.LAB_ID,"sensor_version":vault.SENSOR_VERSION,
         "symbol":vault.SYMBOL,"timeframe":vault.TIMEFRAME,
         "bar_open_ms":close-vault.BAR_MS,"bar_close_ms":close,
         "tv_delta":float(i+1),"poc_mid":85000+i}
    return {"record_type":"TVFP_RECEIPT","app_version":"tv-ingest-v0.2-log-ledger",
        "received_at":"2026-10-07T12:30:00+00:00",
        "evidence_key":f"{vault.LAB_ID}|{vault.SENSOR_VERSION}|{vault.SYMBOL}|{vault.TIMEFRAME}|{close}",
        "payload_sha256":vault.payload_sha(payload),"payload":payload,"trading_authority":"NONE"}

def log(r):
    return {"message":"TVFP_RECEIPT "+json.dumps(r,sort_keys=True),
            "timestamp":"2026-10-07T12:30:00Z","id":"demo"}

class ArchiveStrictTests(unittest.TestCase):
    def test_288_valid_receipts(self):
        got,stats=a.extract_for_day(DAY,[log(receipt(i)) for i in range(288)])
        self.assertEqual(len(got),288)
        self.assertEqual(stats["exact_duplicates_removed"],0)
    def test_duplicate_keeps_identity(self):
        arr=[log(receipt(i)) for i in range(288)]
        arr.append(log(receipt(60)))
        got,stats=a.extract_for_day(DAY,arr)
        self.assertEqual(len(got),288)
        self.assertEqual(stats["exact_duplicates_removed"],1)
    def test_one_missing_fails(self):
        with self.assertRaisesRegex(a.ArchiveBlocked,"UTC_DAY_RECEIPT_COUNT"):
            a.extract_for_day(DAY,[log(receipt(i)) for i in range(287)])
    def test_conflict_fails(self):
        arr=[log(receipt(i)) for i in range(288)]
        other=receipt(5)
        other["payload"]["tv_delta"]=12345
        other["payload_sha256"]=vault.payload_sha(other["payload"])
        arr.append(log(other))
        with self.assertRaisesRegex(a.ArchiveBlocked,"CONFLICTING_SAME_KEY"):
            a.extract_for_day(DAY,arr)
    def test_tamper_payload_sha_fails(self):
        arr=[log(receipt(i)) for i in range(288)]
        obj=json.loads(arr[0]["message"].split("TVFP_RECEIPT ")[1])
        obj["payload_sha256"]="0"*64
        arr[0]=log(obj)
        with self.assertRaisesRegex(a.ArchiveBlocked,"RENDER_RECEIPT_INVALID"):
            a.extract_for_day(DAY,arr)
    def test_wrong_sensor_identity_fails(self):
        arr=[log(receipt(i)) for i in range(288)]
        obj=receipt(5);obj["payload"]["sensor_version"]="MM-V2"
        obj["payload_sha256"]=vault.payload_sha(obj["payload"])
        arr[5]=log(obj)
        with self.assertRaises(a.ArchiveBlocked):a.extract_for_day(DAY,arr)
    def test_different_day_discarded(self):
        arr=[log(receipt(i)) for i in range(288)]
        obj=receipt(0)
        obj["payload"]["bar_open_ms"]-=a.BAR_MS
        obj["payload"]["bar_close_ms"]-=a.BAR_MS
        obj["evidence_key"]=f"{vault.LAB_ID}|{vault.SENSOR_VERSION}|{vault.SYMBOL}|{vault.TIMEFRAME}|{START-a.BAR_MS}"
        obj["payload_sha256"]=vault.payload_sha(obj["payload"])
        arr.append(log(obj))
        unique,_=a.extract_for_day(DAY,arr)
        self.assertEqual(len(unique),288)
    def test_render_page_cursor_three_pages(self):
        data=[log(receipt(i)) for i in range(288)]
        batches=[data[:100],data[100:200],data[200:]]
        idx=[0]
        def fetch(token,params):
            self.assertEqual(params["ownerId"],a.OWNER_ID)
            self.assertEqual(params["resource"],a.SERVICE_ID)
            self.assertEqual(params["type"],"app")
            self.assertEqual(params["text"],"TVFP_RECEIPT")
            i=idx[0];idx[0]+=1
            if i>=len(batches):raise AssertionError("EXTRA PAGE")
            return {"logs":batches[i],"hasMore":i<2,
                    "nextStartTime":f"2026-10-07T{i+1:02d}:05:00Z",
                    "nextEndTime":"2026-10-08T01:00:00Z"}
        (items,_),meta=a.fetch_render_day(DAY,"fake-test-token-1234",fetch_page=fetch)
        self.assertEqual(len(items),288)
        self.assertEqual(meta["pages"],3)
    def test_stalled_cursor_fails(self):
        def fetch(token,params):
            return {"logs":[],"hasMore":True,
                "nextStartTime":params["startTime"],
                "nextEndTime":params["endTime"]}
        with self.assertRaisesRegex(a.ArchiveBlocked,"STALLED"):
            a.fetch_render_day(DAY,"fake-test-token-1234",fetch_page=fetch)
    def test_pagination_schema_bad(self):
        with self.assertRaises(a.ArchiveBlocked):
            a.validate_page({"logs":"bad","hasMore":False})
    def test_page_above_100_blocked(self):
        with self.assertRaises(a.ArchiveBlocked):
            a.validate_page({"logs":[{"message":"abc"}]*101,"hasMore":False})
    def test_no_future_utc_archive(self):
        today=datetime.now(timezone.utc).date()
        with self.assertRaises(a.ArchiveBlocked):
            a.parse_day(today.isoformat())
    def test_noncanonical_day(self):
        with self.assertRaises(a.ArchiveBlocked):
            a.parse_day("2026-1-2")
    def test_missing_token_env_no_value(self):
        with self.assertRaisesRegex(a.ArchiveBlocked,"MISSING"):
            a._request_page("",{})
    def test_create_staging_atomic(self):
        with tempfile.TemporaryDirectory() as tmp:
            records=[receipt(i) for i in range(288)]
            staging,digest=a.write_staging(DAY,records,Path(tmp))
            self.assertTrue(staging.exists())
            self.assertEqual(hashlib.sha256(staging.read_bytes()).hexdigest(),digest)
            self.assertEqual(len(staging.read_text().splitlines()),288)
            with self.assertRaises(a.ArchiveBlocked):
                a.write_staging(DAY,records,Path(tmp))
    def test_existing_archive_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"archive"/DAY.isoformat()/(DAY.isoformat()+".manifest.json")
            p.parent.mkdir(parents=True,exist_ok=True);p.write_text("{}")
            with self.assertRaisesRegex(a.ArchiveBlocked,"IMMUTABLE_DAY_ALREADY"):
                a.write_staging(DAY,[receipt(i) for i in range(288)],Path(tmp))
    def test_outcome_mutation_not_present(self):
        src=Path(a.__file__).read_text().lower()
        for forbidden in ("create_order(", "place_order(", "api_key = ", "future_return", "r60", "leverage"):
            self.assertNotIn(forbidden,src)
    def test_complete_span_dates(self):
        out,_=a.extract_for_day(DAY,[log(receipt(i)) for i in range(288)])
        self.assertEqual(out[0]["payload"]["bar_close_ms"],START)
        self.assertEqual(out[-1]["payload"]["bar_close_ms"],START+287*a.BAR_MS)

if __name__=="__main__": unittest.main()
