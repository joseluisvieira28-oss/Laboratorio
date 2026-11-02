"""Separate raw-source replay; no import of experiment module. Same author, not external review."""
import csv, datetime, hashlib, io, json, math, pathlib, random, zipfile
P=pathlib.Path(__file__).resolve().parent
manifest=json.loads((P/"source_manifest.json").read_text())
source_by_month={}
for item in manifest:
    s,m=item["symbol"],item["month"]
    path=P/"raw"/(s+"-1m-"+m+".zip")
    raw=path.read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    checksum=pathlib.Path(str(path)+".CHECKSUM").read_text().split()[0]
    assert digest==checksum==item["sha256"]
    data={}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for line in csv.reader(io.TextIOWrapper(archive.open(s+"-1m-"+m+".csv"))):
            ms=int(line[0])
            usable=float(line[5])>0 and int(line[8])>0
            data[ms]=(float(line[1]),float(line[4]),usable)
    source_by_month.setdefault(m,{})[s]=data
# Construct signal from one-minute residual signs, rather than main implementation's indexed arrays.
replay=[]
for month,parts in sorted(source_by_month.items()):
    # Permit preceding/following month source lookup without imputing.
    y,m=map(int,month.split("-"))
    prev=f"{y-1 if m==1 else y}-{12 if m==1 else m-1:02d}"
    nxt=f"{y+1 if m==12 else y}-{1 if m==12 else m+1:02d}"
    joined={}
    for symbol in ("BTCUSDT","BTCUSDC","USDCUSDT"):
        joined[symbol]={}
        for key in (prev,month,nxt):
            joined[symbol].update(source_by_month.get(key,{}).get(symbol,{}))
    for boundary in sorted(parts["BTCUSDT"]):
        if boundary%600000:continue
        date=datetime.datetime.fromtimestamp(boundary/1000,datetime.UTC)
        end=datetime.datetime.fromtimestamp((boundary+600000)/1000,datetime.UTC)
        if date.year!=end.year:continue
        directions=[]
        for stamp in (boundary-180000,boundary-120000,boundary-60000):
            if not all(stamp in joined[s] and joined[s][stamp][2] for s in joined):break
            a=joined["BTCUSDC"][stamp][1]
            b=joined["USDCUSDT"][stamp][1]
            c=joined["BTCUSDT"][stamp][1]
            # Independent log decomposition; mathematically equivalent.
            r=10000*(math.log(a)+math.log(b)-math.log(c))
            directions.append(1 if r>=5 else -1 if r<=-5 else 0)
        if len(directions)!=3 or len(set(directions))!=1 or not directions[0]:continue
        btc=joined["BTCUSDT"]
        if boundary+600000 not in btc or not btc[boundary][2] or not btc[boundary+600000][2]:continue
        entry=btc[boundary][0];exit=btc[boundary+600000][0]
        replay.append((boundary,directions[0],(exit>entry)-(exit<entry),entry,exit))
original=json.loads((P/"events.json").read_text())
expected=[(e["time_ms"],e["side"],e["truth"],e["entry"],e["exit"]) for e in original]
assert replay==expected,"raw-source replay mismatch"
results=json.loads((P/"results.json").read_text())
audit={"scope":"Independent implementation, same author; not external independent review",
       "source_zip_hashes_verified":len(manifest),"all_event_identities_sides_labels_prices_match":True,
       "events_all_periods":len(replay),"years":{},"orders":0}
for year in (2023,2024):
    rows=[r for r in replay if datetime.datetime.fromtimestamp(r[0]/1000,datetime.UTC).year==year]
    win=sum(side==truth for _,side,truth,_,_ in rows)
    tie=sum(truth==0 for _,_,truth,_,_ in rows)
    loss=len(rows)-win-tie
    ev70=(7*win-10*loss)/(10*len(rows)) if rows else None
    ev80=(8*win-10*loss)/(10*len(rows)) if rows else None
    primary=results["development" if year==2023 else "oos"]
    assert (len(rows),win,loss,tie)==tuple(primary[k] for k in ("signals","wins","losses","ties"))
    assert ev70 is None or abs(ev70-primary["q70_ev"])<1e-12
    assert ev80 is None or abs(ev80-primary["q80_ev"])<1e-12
    ndays=(datetime.date(year+1,1,1)-datetime.date(year,1,1)).days
    daily=[[0,0,0] for _ in range(ndays)]
    for stamp,side,truth,_,_ in rows:
        d=datetime.datetime.fromtimestamp(stamp/1000,datetime.UTC).date()
        idx=(d-datetime.date(year,1,1)).days
        daily[idx][0]+=1
        daily[idx][1]+=0 if truth==0 else 7 if truth==side else -10
        daily[idx][2]+=0 if truth==0 else 8 if truth==side else -10
    rng=random.Random(72161102);boot=[[],[]]
    for _ in range(10000):
        sampled=rng.choices(daily,k=ndays)
        total=sum(x[0] for x in sampled)
        if total:
            boot[0].append(sum(x[1] for x in sampled)/(10*total))
            boot[1].append(sum(x[2] for x in sampled)/(10*total))
    def percentile(a):
        a.sort();pos=.025*(len(a)-1);i=int(pos)
        return a[i]+(a[min(i+1,len(a)-1)]-a[i])*(pos-i) if a else None
    audit["years"][year]={"n":len(rows),"wins":win,"losses":loss,"ties":tie,"q70_ev":ev70,"q80_ev":ev80,
        "separate_seed_lower_q70":percentile(boot[0]),"separate_seed_lower_q80":percentile(boot[1])}
audit["status"]="RAW_REPLAY_PASS"
(P/"audit.json").write_text(json.dumps(audit,indent=2))
print(json.dumps(audit,indent=2))
