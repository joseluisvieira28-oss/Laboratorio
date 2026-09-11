from __future__ import annotations
from datetime import date, timedelta
import hashlib, json
from typing import Any

HYPOTHESIS_ID = "H04_POSITIVE_TAKER_FLOW_PERSISTENCE"
FREEZE_FINGERPRINT = "a7190c9c5ff019521a88d91ce3f60cd2fc0f1d4ec3577458554d5a3c8e670c8f"
BASE_URL = "https://data.binance.vision/data/spot/daily/klines"
TIMEFRAME = "15m"
UNIVERSE = ("BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT")
START_DATE = date(2023,2,1)
END_DATE_EXCLUSIVE = date(2025,9,1)
EXPECTED_DAY_COUNT = 943
EXPECTED_ARCHIVE_COUNT = EXPECTED_DAY_COUNT * len(UNIVERSE)

def expected_h04_daily_objects() -> tuple[dict[str, Any], ...]:
    rows=[]; cursor=START_DATE
    while cursor < END_DATE_EXCLUSIVE:
        day=cursor.isoformat()
        for symbol in UNIVERSE:
            filename=f"{symbol}-{TIMEFRAME}-{day}.zip"
            url=f"{BASE_URL}/{symbol}/{TIMEFRAME}/{filename}"
            rows.append({"symbol":symbol,"date_utc":day,"timeframe":TIMEFRAME,"archive_filename":filename,"archive_url":url,"checksum_url":url+".CHECKSUM"})
        cursor += timedelta(days=1)
    if len(rows)!=EXPECTED_ARCHIVE_COUNT: raise RuntimeError("H04 manifest cardinality drift")
    return tuple(rows)

def build_h04_manifest_receipt() -> dict[str, Any]:
    body={"document_type":"PHASE_B_H04_BINANCE_DAILY_OBJECT_MANIFEST","version":"0.1","hypothesis_id":HYPOTHESIS_ID,"status":"METADATA_PLAN_ONLY_NOT_DATA_ACCESS_AUTHORIZATION","source":"OFFICIAL_BINANCE_PUBLIC_DATA_ONLY","archive_granularity":"DAILY_ZIP_FILES","timeframe":TIMEFRAME,"symbols":list(UNIVERSE),"start_date_utc_inclusive":START_DATE.isoformat(),"end_date_utc_exclusive":END_DATE_EXCLUSIVE.isoformat(),"calendar_day_count":EXPECTED_DAY_COUNT,"expected_archive_count":EXPECTED_ARCHIVE_COUNT,"expected_checksum_count":EXPECTED_ARCHIVE_COUNT,"market_data_access_authorized":False,"network_download_authorized":False,"mexc_validation_2025_authorized":False,"holdout_2026_authorized":False,"exchange_mutation_authorized":False,"live_trading_authorized":False,"h04_freeze_fingerprint":FREEZE_FINGERPRINT}
    body["fingerprint"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    return body
