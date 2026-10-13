"""Source-only official USD-M 1m audit for SOL/XRP missing 5m intervals."""
from __future__ import annotations
import argparse,hashlib,io,json,csv,zipfile,math
from pathlib import Path
from research.btc_convex_multifront_v01 import retrospective_diagnostic as src

SYMS=("SOLUSDT","XRPUSDT")
GAPS=((1645833600000,1646092800000,"2022-02"),
      (1648771200000,1648944000000,"2022-04"))
ONE=60_000
FIVE=300_000

def month1(symbol,mo):
    url=f"https://data.binance.vision/data/futures/um/monthly/klines/{symbol}/1m/{symbol}-1m-{mo}.zip"
    zipped=src.fetch(url,25_000_000)
    expected=src.fetch(url+".CHECKSUM",1000).decode("utf-8-sig").strip().split()[0].lower()
    digest=hashlib.sha256(zipped).hexdigest()
    if len(expected)!=64 or digest!=expected:raise ValueError("OFFICIAL_ONE_MINUTE_SHA256_MISMATCH")
    with zipfile.ZipFile(io.BytesIO(zipped)) as z:
        files=[n for n in z.namelist() if n.lower().endswith(".csv")]
        if len(files)!=1:raise ValueError("SOURCE_MEMBERS_BAD")
        rows=list(csv.reader(io.StringIO(z.read(files[0]).decode("utf-8-sig"))))
    bars=src.candles(rows,ONE)
    return bars,{"url":url,"sha256":digest,"bars":len(bars)}

def check(symbol):
    if symbol not in SYMS:raise ValueError("SYMBOL_NOT_FROZEN")
    res=[]
    for start,end,mo in GAPS:
        bars,receipt=month1(symbol,mo)
        expected=set(range(start,end,ONE))
        available=expected&set(bars)
        missing=sorted(expected-set(bars))
        res.append({"period":mo,"first_missing_5m_bar_ms":start,
                    "last_missing_5m_bar_end_ms":end,
                    "one_minute_expected":len(expected),
                    "one_minute_found":len(available),
                    "one_minute_missing":len(missing),
                    "first_10_missing_minutes_ms":missing[:10],
                    "fully_recoverable":len(missing)==0,
                    "official_source":receipt})
    return {"symbol":symbol,"status":"OFFICIAL_1M_SOURCE_COMPLETE_FOR_ALL_5M_HOLES"
            if all(x["fully_recoverable"] for x in res) else "OFFICIAL_1M_INCOMPLETE",
            "windows":res,"price_performance_tested":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--symbol",choices=SYMS,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    ret={"symbol":a.symbol,"status":"SOURCE_BLOCKED"}
    try:ret=check(a.symbol)
    except Exception as e:ret["reason"]=type(e).__name__+":"+str(e)
    (a.output_dir/"REPAIRABILITY.json").write_text(json.dumps(ret,indent=2,sort_keys=True)+"\n")
    print("ONE_MINUTE_SOURCE_VERDICT",json.dumps(ret,sort_keys=True),flush=True)
    if ret["status"]=="SOURCE_BLOCKED":raise SystemExit(2)
if __name__=="__main__":main()
