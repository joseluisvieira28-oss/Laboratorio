#!/usr/bin/env python3
import csv,io,json,re,urllib.request,zipfile
URL="https://data.binance.vision/data/option/daily/EOHSummary/BTCUSDT/BTCUSDT-EOHSummary-2023-05-18.zip"
def norm(x): return re.sub(r"[^a-z0-9]+","_",x.strip().strip("[]").lower()).strip("_")
def hour(v):
    s=str(v).strip()
    try:
        f=float(s)
        if 0<=f<24:return int(f)
    except: pass
    m=re.search(r"(\d{1,2})",s)
    return int(m.group(1)) if m else None
req=urllib.request.Request(URL,headers={"User-Agent":"CryptoLab-StrikeSemantics/0.1"})
with urllib.request.urlopen(req,timeout=45) as r: raw=r.read()
with zipfile.ZipFile(io.BytesIO(raw)) as z:
    name=[n for n in z.namelist() if not n.endswith("/")][0]
    with z.open(name) as fh:
        reader=csv.DictReader(io.TextIOWrapper(fh,encoding="utf-8-sig",newline=""))
        by={norm(h):h for h in (reader.fieldnames or [])}
        toks=[]
        for row in reader:
            if hour(row.get(by["hour"],"")) != 8: continue
            rec={
                "symbol":str(row.get(by["symbol"],"")).strip(),
                "type":str(row.get(by["type"],"")).strip(),
                "strike_raw":str(row.get(by["strike"],"")),
                "delta_raw":str(row.get(by["delta"],"")),
            }
            if rec not in toks:toks.append(rec)
            if len(toks)>=10:break
out={"diagnostic_id":"BOVRP-BINANCE-STRIKE-SEMANTICS-001","normalized_header_map":by,"sample_tokens":toks,"prices_emitted":False,"outcomes_opened":False}
open("binance_strike_semantics_diag_v01.json","w").write(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,sort_keys=True))
