#!/usr/bin/env python3
"""PMD-001 V0.12.1 decoder remediation.

Preserves the frozen V0.12 feature family/windows/gates. Changes decoder
plumbing only:
- failed transactions do not count as trade intents;
- recognize all Pump trade discriminators present in the official public IDL;
- decode quote-aware TradeEvent records;
- separate structural decoder completeness from SOL-volume completeness.
"""
from __future__ import annotations
import hashlib, json, math, statistics, sys
from pathlib import Path
from typing import Any
import extract_chain_exact_features_v012 as base

DECODER_VERSION="V0121_OFFICIAL_IDL_QUOTE_AWARE"
NATIVE_SOL_QUOTE="11111111111111111111111111111111"

base.BUY_DISCS={
    hashlib.sha256(b"global:buy").digest()[:8]:"buy",
    hashlib.sha256(b"global:buy_v2").digest()[:8]:"buy",
    hashlib.sha256(b"global:buy_exact_sol_in").digest()[:8]:"buy",
    hashlib.sha256(b"global:buy_exact_quote_in").digest()[:8]:"buy",
    hashlib.sha256(b"global:buy_exact_quote_in_v2").digest()[:8]:"buy",
}
base.SELL_DISCS={
    hashlib.sha256(b"global:sell").digest()[:8]:"sell",
    hashlib.sha256(b"global:sell_v2").digest()[:8]:"sell",
}

def trade_intents_v0121(item:dict[str,Any], mint:str, pda:str)->list[str]:
    if (item.get("meta") or {}).get("err") is not None:
        return []
    keys=base.account_keys(item)
    kinds=[]
    for ix in base.compiled_instructions(item):
        if base.resolve_program(ix,keys)!=base.PUMP_PROGRAM:
            continue
        data=base.ix_data(ix)
        if len(data)<8:
            continue
        accounts=set(base.resolve_ix_accounts(ix,keys))
        if mint not in accounts or pda not in accounts:
            continue
        disc=bytes(data[:8])
        if disc in base.BUY_DISCS:
            kinds.append("buy")
        elif disc in base.SELL_DISCS:
            kinds.append("sell")
    return kinds

def _u64(blob:bytes,p:int):
    if p+8>len(blob): raise ValueError
    return int.from_bytes(blob[p:p+8],"little"),p+8
def _i64(blob:bytes,p:int):
    if p+8>len(blob): raise ValueError
    return int.from_bytes(blob[p:p+8],"little",signed=True),p+8
def _pk(blob:bytes,p:int):
    if p+32>len(blob): raise ValueError
    return base.b58encode(blob[p:p+32]),p+32
def _bool(blob:bytes,p:int):
    if p+1>len(blob): raise ValueError
    v=blob[p]
    if v not in (0,1): raise ValueError
    return bool(v),p+1
def _string(blob:bytes,p:int):
    if p+4>len(blob): raise ValueError
    n=int.from_bytes(blob[p:p+4],"little");p+=4
    if n<0 or n>128 or p+n>len(blob): raise ValueError
    return blob[p:p+n].decode("utf-8"),p+n

def parse_trade_event_blob_v0121(blob:bytes,target_mint:str,block_time:int|float|None):
    at=blob.find(base.TRADE_EVENT_DISC)
    if at<0 or at>32:
        return None
    p=at+8
    try:
        mint,p=_pk(blob,p)
        sol_lamports,p=_u64(blob,p)
        token_amount,p=_u64(blob,p)
        is_buy,p=_bool(blob,p)
        user,p=_pk(blob,p)
        timestamp,p=_i64(blob,p)
        virtual_sol,p=_u64(blob,p)
        virtual_token,p=_u64(blob,p)
        real_sol,p=_u64(blob,p)
        real_token,p=_u64(blob,p)
    except Exception:
        return None
    if mint!=target_mint or token_amount<=0:
        return None
    if block_time is not None and abs(timestamp-int(block_time))>30:
        return None

    quote_mint=None; quote_amount=None; ix_name=None
    q=p
    try:
        _fee_recipient,q=_pk(blob,q)
        _fee_bps,q=_u64(blob,q); _fee,q=_u64(blob,q)
        _creator,q=_pk(blob,q)
        _creator_bps,q=_u64(blob,q); _creator_fee,q=_u64(blob,q)
        _track,q=_bool(blob,q)
        _unclaimed,q=_u64(blob,q); _claimed,q=_u64(blob,q)
        _current_sol_volume,q=_u64(blob,q); _last_update,q=_i64(blob,q)
        ix_name,q=_string(blob,q)
        _mayhem,q=_bool(blob,q)
        _cashback_bps,q=_u64(blob,q); _cashback,q=_u64(blob,q)
        _buyback_bps,q=_u64(blob,q); _buyback_fee,q=_u64(blob,q)
        if q+4>len(blob): raise ValueError
        n=int.from_bytes(blob[q:q+4],"little");q+=4
        if n>64: raise ValueError
        for _ in range(n):
            _shareholder,q=_pk(blob,q)
            if q+2>len(blob): raise ValueError
            q+=2
        quote_mint,q=_pk(blob,q)
        quote_amount,q=_u64(blob,q)
    except Exception:
        quote_mint=None; quote_amount=None; ix_name=None

    native_quote=(quote_mint in (None,NATIVE_SOL_QUOTE))
    # Legacy blobs may lack quote metadata; a positive sol field remains authoritative.
    sol_amount=(sol_lamports/1_000_000_000.0) if (sol_lamports>0 and native_quote) else None
    if sol_lamports<=0 and quote_mint is None:
        return None
    if quote_mint not in (None,NATIVE_SOL_QUOTE) and (quote_amount is None or quote_amount<=0):
        return None

    return {
        "mint":mint,
        "sol_lamports":sol_lamports if sol_amount is not None else None,
        "sol_amount":sol_amount,
        "token_amount_raw":token_amount,
        "side":"buy" if is_buy else "sell",
        "user":user,
        "timestamp":timestamp,
        "virtual_sol_reserves":virtual_sol,
        "virtual_token_reserves":virtual_token,
        "real_sol_reserves":real_sol,
        "real_token_reserves":real_token,
        "quote_mint":quote_mint,
        "quote_amount_raw":quote_amount,
        "native_sol_quote":native_quote,
        "ix_name":ix_name,
        "decoder_version":DECODER_VERSION,
    }

def window_metrics_v0121(events,tx_audit,boundary_time,sec,source_complete):
    evs=[e for e in events if float(e["block_time"])>=boundary_time-sec]
    txs=[t for t in tx_audit if float(t["block_time"])>=boundary_time-sec]
    intents=sum(int(t["intent_count"]) for t in txs)
    undecoded=sum(int(t["undecoded_intents"]) for t in txs)
    ambiguous=sum(int(t["ambiguous_events"]) for t in txs)
    decoder_complete=bool(source_complete and undecoded==0 and ambiguous==0)
    buys=[e for e in evs if e["side"]=="buy"]; sells=[e for e in evs if e["side"]=="sell"]
    participants={e["user"] for e in evs}; buyers={e["user"] for e in buys}; sellers={e["user"] for e in sells}
    n=len(evs)
    sol_volume_complete=bool(decoder_complete and all(e.get("sol_amount") is not None for e in evs))
    out={
      "window_seconds":sec,"source_complete":bool(source_complete),
      "decoder_complete":decoder_complete,"sol_volume_complete":sol_volume_complete,
      "recognized_trade_intents":intents,"undecoded_trade_intents":undecoded,
      "ambiguous_events":ambiguous,"decoded_trade_events":n,
    }
    if not decoder_complete:
        for k in ["buy_count","sell_count","unique_buyers","unique_sellers","unique_participants",
                  "buy_volume_sol","sell_volume_sol","net_flow_sol","volume_balance","count_balance",
                  "buy_fraction","wallet_breadth","avg_trade_sol","median_trade_sol","largest_buy_sol","largest_sell_sol"]:
            out[k]=None
        return out

    out.update({
      "buy_count":len(buys),"sell_count":len(sells),
      "unique_buyers":len(buyers),"unique_sellers":len(sellers),"unique_participants":len(participants),
      "count_balance":((len(buys)-len(sells))/n) if n else 0.0,
      "buy_fraction":(len(buys)/n) if n else 0.0,
      "wallet_breadth":(len(participants)/n) if n else 0.0,
    })
    if not sol_volume_complete:
        for k in ["buy_volume_sol","sell_volume_sol","net_flow_sol","volume_balance",
                  "avg_trade_sol","median_trade_sol","largest_buy_sol","largest_sell_sol"]:
            out[k]=None
        return out

    buy_sol=sum(float(e["sol_amount"]) for e in buys); sell_sol=sum(float(e["sol_amount"]) for e in sells)
    amounts=[float(e["sol_amount"]) for e in evs]; denom=buy_sol+sell_sol
    out.update({
      "buy_volume_sol":buy_sol,"sell_volume_sol":sell_sol,"net_flow_sol":buy_sol-sell_sol,
      "volume_balance":((buy_sol-sell_sol)/denom) if denom>0 else 0.0,
      "avg_trade_sol":statistics.fmean(amounts) if amounts else 0.0,
      "median_trade_sol":statistics.median(amounts) if amounts else 0.0,
      "largest_buy_sol":max((float(e["sol_amount"]) for e in buys),default=0.0),
      "largest_sell_sol":max((float(e["sol_amount"]) for e in sells),default=0.0),
    })
    return out

base.trade_intents=trade_intents_v0121
base.parse_trade_event_blob=parse_trade_event_blob_v0121
base.window_metrics=window_metrics_v0121

def cli_value(flag:str):
    try:
        i=sys.argv.index(flag); return sys.argv[i+1]
    except Exception:return None

if __name__=="__main__":
    rc=base.main()
    out_dir=cli_value("--out-dir")
    if out_dir:
        out=Path(out_dir)
        rows_p=out/"chain_exact_features_v012.jsonl"
        rows=[json.loads(x) for x in rows_p.read_text(encoding="utf-8").splitlines() if x.strip()]
        for r in rows:
            r["decoder_version"]=DECODER_VERSION
        canon="".join(json.dumps(r,sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n" for r in rows)
        rows_p.write_text(canon,encoding="utf-8")
        rec_p=out/"chain_exact_features_v012_receipt.json"
        rec=json.loads(rec_p.read_text(encoding="utf-8"))
        rec["stage"]="CHAIN_EXACT_FEATURES_V0121_DECODER_REMEDIATION"
        rec["decoder_version"]=DECODER_VERSION
        rec["sol_volume_complete_w30"]=sum(bool(r.get("sol_volume_complete_w30")) for r in rows)
        rec["sol_volume_complete_w60"]=sum(bool(r.get("sol_volume_complete_w60")) for r in rows)
        rec["sol_volume_complete_w300"]=sum(bool(r.get("sol_volume_complete_w300")) for r in rows)
        rec["rows_sha256"]=hashlib.sha256(canon.encode()).hexdigest()
        rec_p.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(json.dumps(rec,indent=2,sort_keys=True))
    raise SystemExit(rc)
