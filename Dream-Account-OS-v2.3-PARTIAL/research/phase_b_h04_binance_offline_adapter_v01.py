from __future__ import annotations
import csv, re, zipfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from hashlib import sha256
from io import BytesIO, TextIOWrapper
from math import isfinite
from dream_account.models import Candle

TIMEFRAME_MS=15*60*1000
EXPECTED_FIELDS=12
EXPECTED_HEADER=("open_time","open","high","low","close","volume","close_time","quote_asset_volume","number_of_trades","taker_buy_base_asset_volume","taker_buy_quote_asset_volume","ignore")
UNIVERSE=("BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT")
CHECKSUM_RE=re.compile(r"^([0-9a-fA-F]{64})\s+\*?([^\s]+)\s*$")
START=date(2023,2,1); END=date(2025,9,1)
@dataclass(frozen=True)
class H04Bar:
    candle:Candle
    quote_asset_volume:float
    number_of_trades:int
    taker_buy_base_asset_volume:float
    taker_buy_quote_asset_volume:float
    @property
    def flow_imbalance(self)->float:
        v=self.candle.volume
        if v<=0: raise ValueError("zero volume")
        x=(2*self.taker_buy_base_asset_volume-v)/v
        if not isfinite(x) or x < -1.000000000001 or x > 1.000000000001: raise ValueError("invalid flow imbalance")
        return max(-1.0,min(1.0,x))
@dataclass(frozen=True)
class H04DailyAdapterResult:
    status:str; symbol:str; date_utc:str; archive_filename:str; archive_sha256:str; checksum_verified:bool; row_count:int; detected_gap_count:int; missing_candle_count:int; source_close_time_anomaly_count:int; bars:tuple[H04Bar,...]; reasons:tuple[str,...]
def _expected_filename(symbol,day):
    if symbol not in UNIVERSE: raise ValueError("symbol outside H04 universe")
    d=date.fromisoformat(day)
    if d<START or d>=END: raise ValueError("day outside H04 discovery window")
    return f"{symbol}-15m-{day}.zip"
def _checksum(text,filename):
    m=CHECKSUM_RE.fullmatch(text.strip())
    if not m or m.group(2)!=filename: raise ValueError("invalid checksum")
    return m.group(1).lower()
def adapt_h04_binance_daily_archive_bytes(*,symbol,day,archive_filename,archive_bytes,checksum_text):
    expected=_expected_filename(symbol,day)
    if archive_filename!=expected: raise ValueError("archive filename mismatch")
    raw=bytes(archive_bytes); actual=sha256(raw).hexdigest()
    if actual!=_checksum(checksum_text,expected): return H04DailyAdapterResult("BLOCKED_CHECKSUM_MISMATCH",symbol,day,expected,actual,False,0,0,0,0,(),("ARCHIVE_SHA256_MISMATCH",))
    member=expected[:-4]+".csv"; reasons=[]; rows=[]; seen=set(); prev=None; anomalies=0
    start_ms=int(datetime.strptime(day,"%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()*1000); end_ms=start_ms+86400000
    try: zf=zipfile.ZipFile(BytesIO(raw))
    except zipfile.BadZipFile: return H04DailyAdapterResult("BLOCKED_INVALID_ZIP",symbol,day,expected,actual,True,0,0,0,0,(),("INVALID_ZIP",))
    infos=zf.infolist()
    if len(infos)!=1 or infos[0].filename!=member: return H04DailyAdapterResult("BLOCKED_ZIP_MEMBER",symbol,day,expected,actual,True,0,0,0,0,(),("UNEXPECTED_MEMBER",))
    with zf.open(infos[0],"r") as binary:
        reader=csv.reader(TextIOWrapper(binary,encoding="utf-8-sig",newline="")); first=False
        for r in reader:
            if not r or all(not c.strip() for c in r): continue
            norm=tuple(c.strip().lower().replace(" ","_") for c in r)
            if not first and norm==EXPECTED_HEADER: first=True; continue
            first=True
            if len(r)!=EXPECTED_FIELDS: reasons.append("FIELD_COUNT"); continue
            try:
                ot=int(r[0]); op,hi,lo,cl,vol=map(float,r[1:6]); source_ct=int(r[6]); qv=float(r[7]); nt=int(r[8]); tb=float(r[9]); tbq=float(r[10]); float(r[11])
            except Exception: reasons.append("NUMERIC"); continue
            vals=(op,hi,lo,cl,vol,qv,tb,tbq)
            if not all(isfinite(x) for x in vals) or min(op,hi,lo,cl)<=0 or vol<0 or qv<0 or nt<0 or tb<0 or tb>vol+max(1e-12,abs(vol)*1e-10): reasons.append("VALUE")
            if hi<max(op,cl,lo) or lo>min(op,cl,hi): reasons.append("OHLC")
            if ot in seen or (prev is not None and ot<=prev): reasons.append("ORDER")
            seen.add(ot)
            if prev is not None and (ot-prev)%TIMEFRAME_MS!=0: reasons.append("SPACING")
            prev=ot
            if ot%TIMEFRAME_MS!=0 or not start_ms<=ot<end_ms: reasons.append("TIME")
            canon=ot+TIMEFRAME_MS-1
            if source_ct<=ot or source_ct>canon: reasons.append("CLOSE_TIME")
            elif source_ct!=canon: anomalies+=1
            rows.append(H04Bar(Candle(ot,op,hi,lo,cl,vol,canon,True),qv,nt,tb,tbq))
    gaps=missing=0
    for a,b in zip(rows,rows[1:]):
        d=b.candle.open_time-a.candle.open_time
        if d>TIMEFRAME_MS and d%TIMEFRAME_MS==0: gaps+=1; missing += d//TIMEFRAME_MS-1
    rs=tuple(sorted(set(reasons)))
    if rs: return H04DailyAdapterResult("BLOCKED_BINANCE_DAILY_INTEGRITY",symbol,day,expected,actual,True,len(rows),gaps,missing,anomalies,(),rs)
    return H04DailyAdapterResult("PASS_BINANCE_DAILY_WITH_GAPS" if gaps else "PASS_BINANCE_DAILY",symbol,day,expected,actual,True,len(rows),gaps,missing,anomalies,tuple(rows),())
