"""Exploratory only; not frozen prospective outcome or executable PnL."""
import datetime as dt, json, time, math
from zoneinfo import ZoneInfo
from source_probe import get, OUT, records, SYMBOLS
NY=ZoneInfo("America/New_York")
DAYS=("2026-11-02","2026-11-09","2026-11-16","2026-11-23")
ROOT="https://api.kraken.com/0/public/"
def ts(day,h,m):
    return int(dt.datetime.combine(dt.date.fromisoformat(day),dt.time(h,m),NY).timestamp())
def cash_bar(cash,t):
    try:
        q=cash["chart"]["result"][0]
        i=q["timestamp"].index(t-300)
        v=q["indicators"]["quote"][0]["close"][i]
        return float(v) if v is not None and math.isfinite(v) and v>0 else None
    except (KeyError,ValueError,IndexError,TypeError): return None
def trade(s,day,t,label):
    p=get(f"{s}_{day}_{label}",ROOT+"Trades",{"pair":s+"xUSD","asset_class":"tokenized_asset","since":str((t-60)*10**9),"count":1000})
    vals=[v for k,v in p.get("result",{}).items() if k!="last" and isinstance(v,list)]
    if len(vals)!=1:return None
    # Require sorted response, no truncation before target, and a trade strictly before decision.
    rows=vals[0]
    try:
        times=[float(x[2]) for x in rows]
        if not times or times!=sorted(times) or times[0]<t-60.001 or (len(rows)>=1000 and times[-1]<t):return None
        valid=[(float(x[2]),float(x[0])) for x in rows if t-60<=float(x[2])<t and math.isfinite(float(x[0])) and float(x[0])>0]
        return max(valid) if valid else None
    except (ValueError,TypeError,IndexError): return None
def main():
    result=[]
    for s in SYMBOLS:
        cash=get(s+"_cash_1mo","https://query1.finance.yahoo.com/v8/finance/chart/"+s,{"range":"1mo","interval":"5m","events":"div,splits"})
        for day in DAYS:
            t1,t2=ts(day,9,35),ts(day,10,35)
            c1,c2=cash_bar(cash,t1),cash_bar(cash,t2)
            a=trade(s,day,t1,"entry");time.sleep(1)
            z=trade(s,day,t2,"exit");time.sleep(1)
            row=dict(symbol=s,date=day,entry_utc=t1,exit_utc=t2,cash_entry=c1,cash_exit=c2,token_entry=a,token_exit=z)
            if c1 and c2 and a and z:
                discount=(c1-a[1])/c1*10000
                ret=(z[1]/a[1]-1)*10000
                cashret=(c2/c1-1)*10000
                row.update(discount_bps=discount,qualifies_proxy=discount>=50,token_return_bps=ret,cash_return_bps=cashret,incremental_bps=ret-cashret,illustrative_net_23bps=ret-23,illustrative_stress_43bps=ret-43)
            result.append(row)
    complete=[x for x in result if "discount_bps" in x]
    eligible=[x for x in complete if x["qualifies_proxy"]]
    summary=dict(classification="DISCOVERY_ONLY_TRADE_PRICE_PROXY_NOT_EXECUTABLE",expected=20,complete=len(complete),eligible=len(eligible),rows=result,requests=records,limitations=["No historical bids or asks","Yahoo bar close and Kraken last trade are not synchronized BBO; up to 60 seconds token staleness","Corporate actions, instrument share equivalence and source timestamps not independently certified","23/43 bps illustrative only; not historical fees/depth","Four Monday dates selected before reading these historical outcomes; not independent prospective sample"])
    (OUT/"historical_proxy.json").write_text(json.dumps(summary,indent=2))
    print("HISTORICAL_PROXY_SUMMARY",json.dumps({k:v for k,v in summary.items() if k!="requests"}))
if __name__=="__main__":main()
