import requests,json,re,os,time
BASE="https://www.mexc.com"
OUT="artifacts/mlrts_v011_historical_binding_probe"
os.makedirs(OUT,exist_ok=True)
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 (CryptoLabResearch/1.0)"})
TOKENS=["XTER","IP","TERM","K","EPT","SHM","ICEBERG","BOMB","TRN","EMBLEM","NEX","BTC"]

rows={}
# route 1 current symbols
try:
    r=S.get(BASE+"/api/platform/spot/market-v2/web/symbolsV2",timeout=30); r.raise_for_status()
    usdt=(((r.json().get("data") or {}).get("symbols") or {}).get("USDT") or [])
    for t in TOKENS:
        rows.setdefault(t,{})["current"]=[x for x in usdt if str(x.get("vn","")).upper()==t]
except Exception as e:
    rows["__current_error__"]=repr(e)

# route 2 spot2 public symbols endpoint
for t in TOKENS:
    try:
        r=S.get("https://api.mexc.com/api/platform/spot2/market/symbols",timeout=30)
        if r.ok:
            obj=r.json()
            blob=json.dumps(obj,ensure_ascii=False)
            ms=[m.group(0) for m in re.finditer(re.escape(t+"_USDT"),blob)]
            rows.setdefault(t,{})["spot2_symbol_string_hits"]=len(ms)
    except Exception as e:
        rows.setdefault(t,{})["spot2_error"]=repr(e)

# route 3 market-data-download pages + embedded ids
for t in TOKENS:
    try:
        u=f"{BASE}/market-data-download/{t}"
        r=S.get(u,timeout=30); r.raise_for_status(); txt=r.text
        rows.setdefault(t,{})["download_page_len"]=len(txt)
        rows[t]["symbol_text_hits"]=txt.count(t+"_USDT")
        ids=[]
        for pat in [
            rf'"id":"([^"]+)"[^{{}}]{{0,500}}"vn":"{re.escape(t)}"',
            rf'"vn":"{re.escape(t)}"[^{{}}]{{0,500}}"id":"([^"]+)"',
            rf'{re.escape(t)}_USDT[^\n]{{0,1000}}?"id":"([^"]+)"'
        ]:
            ids += re.findall(pat,txt,re.I)
        rows[t]["embedded_ids"]=sorted(set(ids))
    except Exception as e:
        rows.setdefault(t,{})["download_page_error"]=repr(e)
    time.sleep(.05)

with open(f"{OUT}/probe.json","w") as f: json.dump(rows,f,ensure_ascii=False,indent=2)
print(json.dumps(rows,ensure_ascii=False,indent=2)[:50000])
