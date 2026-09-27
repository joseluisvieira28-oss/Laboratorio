#!/usr/bin/env python3
"""Normalize frozen Bitwise rebalance source strings without market data."""

from __future__ import annotations
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from collections import Counter

OUT=Path("artifacts/crypto_index_rebalance_flow")
NAME_MAP={"Polkadot":"DOT","Cosmos":"ATOM","Algorand":"ALGO","Bitcoin Cash":"BCH"}
AMBIGUOUS={"Curve DAO (CRV); Liquity (LQTY) exited"}

# Frozen from source census run 36329364861 / artifact 10935615452.
ROWS=[
("Jan 30, 2022",["Polkadot entered, Cosmos re-entered; Algorand and Bitcoin Cash removed"]),
("May 30, 2022",["Bitcoin Cash (BCH) re-entered, replacing Cosmos"]),
("Jun 29, 2022",["Uniswap (UNI) re-entered, replacing Bitcoin Cash (BCH)"]),
("Jul 28, 2022",["Lido DAO (LDO) entered, replacing Bancor (BNT)"]),
("Aug 30, 2022",["Cosmos (ATOM) re-entered, replacing Uniswap (UNI)","Convex Finance (CVX) entered, replacing SushiSwap (SUSHI)"]),
("Sep 29, 2022",["Uniswap (UNI) re-entered, replacing Litecoin (LTC)"]),
("Oct 30, 2022",["Litecoin (LTC) re-entered, Chainlink (LINK) exited"]),
("Nov 29, 2022",["Chainlink (LINK) re-entered, Cosmos (ATOM) exited","Balancer (BAL) entered, 0x (ZRX) exited"]),
("Jan 30, 2023",["Cosmos (ATOM) re-entered, Chainlink (LINK) exited","Sushiswap (SUSHI) re-entered, Balancer (BAL) exited"]),
("Mar 30, 2023",["Chainlink (LINK) re-entered, Cosmos (ATOM) exited","Balancer (BAL) re-entered, SushiSwap (SUSHI) exited"]),
("May 30, 2023",["Balancer (BAL) and Convex Finance (CVX) exited; Sushiswap (SUSHI) and 0x (ZRX) entered"]),
("Jun 29, 2023",["Balancer (BAL) entered; Sushiswap (SUSHI) exited"]),
("Jul 30, 2023",["XRP (XRP) entered; Chainlink (LINK) exited","XRP (XRP) entered; Cosmos (ATOM) exited","Sushiswap (SUSHI) entered; Balancer (BAL) exited"]),
("Sep 28, 2023",["Bitcoin Cash (BCH) and Chainlink (LINK) entered; Avalanche (AVAX) and Uniswap (UNI) exited"]),
("Oct 30, 2023",["Liquity (LQTY) enters"]),
("Nov 29, 2023",["Avalanche (AVAX) entered; Bitcoin Cash (BCH) exited","Curve DAO (CRV); Liquity (LQTY) exited"]),
("Dec 28, 2023",["Convex Finance (CVX) entered; SushiSwap (SUSHI) exited"]),
("Feb 29, 2024",["SushiSwap (SUSHI) enters; Yearn Finance (YFI) exits"]),
("Mar 27, 2024",["Uniswap (UNI) enters; Litecoin (LTC) exits"]),
("Apr 29, 2024",["Bitcoin Cash (BCH) enters; Uniswap (UNI) exits"]),
("May 30, 2024",["NEAR Protocol (NEAR) enters; Polygon (MATIC) exits","NEAR Protocol (NEAR) enters; Litecoin (LTC) exits"]),
("Jun 27, 2024",["Uniswap (UNI) enters; NEAR Protocol (NEAR) exits"]),
("Aug 29, 2024",["Chainlink (LINK) enters; Polygon (MATIC) exits"]),
("Sep 29, 2024",["Chainlink (LINK) enters; Polygon (MATIC) exits"]),
("Nov 28, 2024",["NEAR Protocol (NEAR) enters; Uniswap (UNI) exits"]),
("Dec 30, 2024",["Uniswap (UNI) enters; NEAR Protocol (NEAR) exits"]),
("Jan 30, 2025",["SUI (SUI) and Litecoin (LTC) enter; Uniswap (UNI) and Bitcoin Cash (BCH) exit","Jito (JTO) enters; Loopring (LRC) exits"]),
("Jul 30, 2025",["EtherFI (ETHFI) enters; 0x (ZRX) exits"]),
("Nov 27, 2025",["Yearn Finance (YFI), 0x Protocol (ZRX) enter; Sky (SKY), SushiSwap (SUSHI) exit"]),
]

VERB_RE=re.compile(r"(re-entered|reentered|entered|enters|enter|exited|exits|exit|removed)",re.I)

def extract_tickers(phrase:str)->list[str]:
    ticks=re.findall(r"\(([A-Z0-9]+)\)",phrase)
    if ticks:
        return ticks
    names=[x.strip() for x in re.split(r"\s+and\s+|,\s*",phrase) if x.strip()]
    unresolved=[x for x in names if x not in NAME_MAP]
    if unresolved:
        raise ValueError("unresolved name-only assets: "+repr(unresolved))
    return [NAME_MAP[x] for x in names]

def parse_change(text:str)->tuple[list[tuple[str,str]],str]:
    if text in AMBIGUOUS:
        return [],"SOURCE_TEXT_AMBIGUOUS_EXCLUDED"

    m=re.fullmatch(r"(.+?)\s+(re-entered|entered|enters|enter),?\s+replacing\s+(.+)",text,re.I)
    if m:
        return ([(t,"ADD") for t in extract_tickers(m.group(1))]+
                [(t,"REMOVE") for t in extract_tickers(m.group(3))]),"OK"

    out=[]
    pat=re.compile(r"(?:^|[;,])\s*([^;,]+?)\s+(re-entered|reentered|entered|enters|enter|exited|exits|exit|removed)(?=\s*(?:[;,]|$))",re.I)
    for m in pat.finditer(text):
        verb=m.group(2).lower()
        direction="ADD" if verb in {"re-entered","reentered","entered","enters","enter"} else "REMOVE"
        out.extend((t,direction) for t in extract_tickers(m.group(1).strip()) )
    if not out:
        raise ValueError("unparseable non-ambiguous source string: "+text)
    return out,"OK"

def main()->int:
    OUT.mkdir(parents=True,exist_ok=True)
    raw_legs=[]
    ambiguous=[]
    for date_str,changes in ROWS:
        date=dt.datetime.strptime(date_str,"%b %d, %Y").date()
        for source_text in changes:
            legs,state=parse_change(source_text)
            if state!="OK":
                ambiguous.append({"date":date.isoformat(),"source_text":source_text,"state":state})
                continue
            for ticker,direction in legs:
                raw_legs.append({
                    "rebalance_date":date.isoformat(),
                    "ticker":ticker,
                    "direction":direction,
                    "source_text":source_text,
                    "period_role":"DISCOVERY_SOURCE" if date.year<=2024 else "HOLDOUT_SOURCE_ONLY",
                })

    grouped={}
    for leg in raw_legs:
        key=(leg["rebalance_date"],leg["ticker"],leg["direction"])
        grouped.setdefault(key,[]).append(leg["source_text"])

    by_date_ticker={}
    for d,t,side in grouped:
        by_date_ticker.setdefault((d,t),set()).add(side)
    contradictions=[{"date":d,"ticker":t,"directions":sorted(sides)}
                    for (d,t),sides in by_date_ticker.items() if len(sides)>1]
    if contradictions:
        raise SystemExit("FAIL_CLOSED_SOURCE_CONTRADICTION: "+json.dumps(contradictions))

    events=[]
    for (date,ticker,direction),texts in sorted(grouped.items()):
        events.append({
            "rebalance_date":date,
            "ticker":ticker,
            "direction":direction,
            "period_role":"DISCOVERY_SOURCE" if int(date[:4])<=2024 else "HOLDOUT_SOURCE_ONLY",
            "duplicate_section_records_collapsed":len(texts)-1,
            "source_texts":sorted(set(texts)),
        })

    disc=[e for e in events if e["period_role"]=="DISCOVERY_SOURCE"]
    hold=[e for e in events if e["period_role"]=="HOLDOUT_SOURCE_ONLY"]
    dates=sorted({e["rebalance_date"] for e in disc})
    years=sorted({int(e["rebalance_date"][:4]) for e in disc})
    dirs=Counter(e["direction"] for e in disc)
    gates={
        "min_30_event_legs":len(disc)>=30,
        "min_12_rebalance_dates":len(dates)>=12,
        "min_2_years":len(years)>=2,
        "both_directions":dirs["ADD"]>0 and dirs["REMOVE"]>0,
    }
    result={
        "schema":"BITWISE_EVENT_NORMALIZATION_V0.1",
        "generated_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "input_run_id":36329364861,
        "input_artifact_id":10935615452,
        "input_artifact_zip_sha256":"b3c5911e854e3d915a3a8293c1c7f4c4dccca37e8e4af0d7d52f6516cdc765b0",
        "events":events,
        "ambiguous_source_records":ambiguous,
        "raw_parsed_legs":len(raw_legs),
        "unique_all_2022_2025_legs":len(events),
        "discovery_2022_2024_unique_legs":len(disc),
        "discovery_rebalance_dates":len(dates),
        "discovery_years":years,
        "discovery_direction_counts":dict(dirs),
        "holdout_2025_unique_legs":len(hold),
        "duplicate_section_records_collapsed":len(raw_legs)-len(events),
        "source_sample_gates":gates,
        "classification":"NORMALIZATION_PASS" if all(gates.values()) else "NORMALIZATION_INSUFFICIENT",
        "market_prices_read":False,
        "returns_computed":False,
        "pnl_computed":False,
        "holdout_2025_market_data_opened":False,
    }
    encoded=json.dumps(result,sort_keys=True,separators=(",",":")).encode()
    result["result_sha256"]=hashlib.sha256(encoded).hexdigest()
    path=OUT/"event_normalization_v0.1.json"
    path.write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps({k:result[k] for k in [
        "classification","discovery_2022_2024_unique_legs","discovery_rebalance_dates",
        "discovery_years","discovery_direction_counts","holdout_2025_unique_legs",
        "duplicate_section_records_collapsed","source_sample_gates"]},indent=2,sort_keys=True))
    return 0 if result["classification"]=="NORMALIZATION_PASS" else 2

if __name__=="__main__":
    raise SystemExit(main())
