#!/usr/bin/env python3
"""V37 PRE-SIGNAL borrower/state reconstruction for the frozen Aave LT shock universe.

SOURCE ONLY. For one frozen shock selected by SHOCK_ID, enumerate every user whose
collateral contribution can be affected at signal-1, then capture historical Pool,
reserve-index, debt/collateral balance, eMode, isolation and oracle state needed for
later analysis. No post-signal behavior, economic outcomes, Development, 2026 data,
trading, accounts, wallets or authenticated endpoints.
"""
import gzip, hashlib, json, os, time, urllib.error, urllib.request
from pathlib import Path
from Crypto.Hash import keccak

ROOT=Path(__file__).resolve().parent
MANIFEST=json.loads((ROOT/"V39_SOURCE_CANDIDATE_MANIFEST_2026-10-08.json").read_text())
SHOCK_ID=os.environ["SHOCK_ID"]
SHOCK=next((x for x in MANIFEST["candidates"] if x["id"]==SHOCK_ID),None)
if not SHOCK:
    raise SystemExit(f"UNKNOWN_SHOCK_ID:{SHOCK_ID}")
if not SHOCK.get("signal_ts"):
    raise SystemExit(f"NO_FROZEN_SIGNAL_TS:{SHOCK_ID}")
CHAIN=SHOCK["primary_chain"]

DEFAULT_POOL="0x794a61358d6845594f94dc1db02a252b5b4814ad"
CHAINS={
 "optimism":{
   "urls":["https://mainnet.optimism.io","https://optimism-rpc.publicnode.com","https://optimism.drpc.org","https://1rpc.io/op"],
   "oracle":"0xd81eb3728a631871a7ebbad631b5f424909f0c77",
   "chunk":500000,
 },
 "avalanche":{
   "urls":["https://api.avax.network/ext/bc/C/rpc","https://avalanche-c-chain-rpc.publicnode.com","https://avalanche.drpc.org"],
   "oracle":"0xebd36016b3ed09d4693ed4251c67bd858c3c7c9c",
   "chunk":500000,
 },
 "polygon":{
   "urls":["https://polygon-bor-rpc.publicnode.com","https://polygon.drpc.org","https://1rpc.io/matic"],
   "oracle":"0xb023e699f5a33916ea823a16485e259257ca8bd1",
   "chunk":500000,
 },
 "base":{
   "urls":["https://base-rpc.publicnode.com","https://mainnet.base.org","https://base.drpc.org"],
   "pool":"0xA238Dd80C259a72e81d7e4664a9801593F98d1c5",
   "oracle":"0x2Cc0Fc26eD4563A5ce5e8bdcfe1A2878676Ae156",
   "chunk":500000,
 },
}
if CHAIN not in CHAINS:
    raise SystemExit(f"UNSUPPORTED_PRIMARY_CHAIN:{CHAIN}")
CFG=CHAINS[CHAIN]; URLS=CFG["urls"]; ORACLE=CFG["oracle"]; POOL=CFG.get("pool",DEFAULT_POOL)
OUT=Path(f"out/aave_borrower_state_v37_{SHOCK_ID.lower().replace('-','_')}");OUT.mkdir(parents=True,exist_ok=True)
WINDOW_START_TS=1640995200
SIGNAL_TS=int(SHOCK["signal_ts"])
last_request=0.0; endpoint_i=0

def sig(s):
    k=keccak.new(digest_bits=256); k.update(s.encode()); return "0x"+k.hexdigest()
def sha(b): return hashlib.sha256(b).hexdigest()
def topic_addr(a): return "0x"+"0"*24+a.lower().replace("0x","")
ZERO="0x"+"0"*40
EN=sig("ReserveUsedAsCollateralEnabled(address,address)")
DIS=sig("ReserveUsedAsCollateralDisabled(address,address)")
EM=sig("UserEModeSet(address,uint8)")
SEL_RESERVE=sig("getReserveData(address)")[:10]
SEL_RESERVES=sig("getReservesList()")[:10]
SEL_CFG=sig("getUserConfiguration(address)")[:10]
SEL_ACC=sig("getUserAccountData(address)")[:10]
SEL_EMODE=sig("getUserEMode(address)")[:10]
SEL_BAL=sig("balanceOf(address)")[:10]
SEL_PRICE=sig("getAssetPrice(address)")[:10]
SEL_EMODE_DATA=sig("getEModeCategoryData(uint8)")[:10]
SEL_EMODE_COLL_BITMAP=sig("getEModeCategoryCollateralBitmap(uint8)")[:10]
SEL_EMODE_BORROW_BITMAP=sig("getEModeCategoryBorrowableBitmap(uint8)")[:10]
SEL_EMODE_LTVZERO_BITMAP=sig("getEModeCategoryLtvzeroBitmap(uint8)")[:10]
SEL_EMODE_ISOLATED=sig("getIsEModeCategoryIsolated(uint8)")[:10]
BORROW_MASK=int("55"*32,16)

def post(body):
    global last_request, endpoint_i
    time.sleep(max(0,.06-(time.monotonic()-last_request))); last_request=time.monotonic()
    url=URLS[endpoint_i%len(URLS)]; endpoint_i+=1
    raw=json.dumps(body,sort_keys=True,separators=(",",":")).encode()
    rec={"request":body,"request_sha256":sha(raw),"observed_at":time.time(),"source_url":url}
    try:
        req=urllib.request.Request(url,data=raw,headers={"Content-Type":"application/json","User-Agent":"Aave-source-audit/1.0"})
        with urllib.request.urlopen(req,timeout=45) as res:
            data=res.read(); status=res.status; headers=dict(res.headers)
    except urllib.error.HTTPError as e:
        data=e.read(); status=e.code; headers=dict(e.headers)
    except Exception as e:
        data=str(e).encode(); status=0; headers={}
    h=sha(data); (OUT/(h+".gz")).write_bytes(gzip.compress(data,mtime=0))
    rec.update(http_status=status,response_sha256=h,headers=headers)
    with (OUT/"requests.jsonl").open("a") as f: f.write(json.dumps(rec)+"\n")
    try: d=json.loads(data)
    except Exception: d={"transport_body":data.decode(errors="replace")}
    return d,status,h,url

def rpc(method,params,attempts=24):
    last=None
    for a in range(attempts):
        d,status,h,url=post({"jsonrpc":"2.0","id":1,"method":method,"params":params}); last=(d,status,h,url)
        if status==200 and isinstance(d,dict) and d.get("result") is not None:
            return d["result"],h,url
        time.sleep(min(6,.25*(a+1)))
    raise RuntimeError("RPC_EXHAUSTED_"+method+"_"+json.dumps(last))

def word(data,i):
    if not isinstance(data,str) or not data.startswith("0x") or len(data)<2+(i+1)*64:
        raise RuntimeError(f"ABI_WORD_MISSING:{i}:{str(data)[:120]}")
    return int(data[2+i*64:2+(i+1)*64],16)
def call(to,selector,arg,block):
    return rpc("eth_call",[{"to":to,"data":selector+arg},hex(block)])[0]
def decode_emode(data):
    # getEModeCategoryData(uint8) returns one tuple containing a string, so the
    # ABI top-level word is an offset to the tuple head.
    base=word(data,0)//32
    if base<1 or base>16:
        raise RuntimeError("INVALID_EMODE_TUPLE_OFFSET_"+str(base))
    return {"ltv_bps":word(data,base),"lt_bps":word(data,base+1),
            "bonus_bps":word(data,base+2),
            "price_source":"0x"+format(word(data,base+3),"040x")}
def call_capability(to,selector,arg,block):
    # Capability probe across every frozen public endpoint. A valid result from
    # any endpoint is accepted; total absence means the historical Pool version
    # does not expose that getter (or source capability is unavailable).
    body={"jsonrpc":"2.0","id":1,"method":"eth_call","params":[{"to":to,"data":selector+arg},hex(block)]}
    for _ in range(len(URLS)*2):
        d,status,h,url=post(body)
        if status==200 and isinstance(d,dict) and isinstance(d.get("result"),str) and d["result"]!="0x":
            return d["result"]
    return None
def block_before(ts):
    latest=int(rpc("eth_blockNumber",[])[0],16); lo,hi=0,latest
    while lo<hi:
        m=(lo+hi+1)//2; b=rpc("eth_getBlockByNumber",[hex(m),False])[0]; t=int(b["timestamp"],16)
        if t<ts: lo=m
        else: hi=m-1
    return lo
def block_at_or_after(ts):
    latest=int(rpc("eth_blockNumber",[])[0],16); lo,hi=0,latest
    while lo<hi:
        m=(lo+hi)//2; b=rpc("eth_getBlockByNumber",[hex(m),False])[0]; t=int(b["timestamp"],16)
        if t<ts: lo=m+1
        else: hi=m
    return lo

SNAP=block_before(SIGNAL_TS); START=block_at_or_after(WINDOW_START_TS)
SNAP_HEADER=rpc("eth_getBlockByNumber",[hex(SNAP),False])[0]
START_HEADER=rpc("eth_getBlockByNumber",[hex(START),False])[0]
assert int(SNAP_HEADER["timestamp"],16)<SIGNAL_TS
assert int(START_HEADER["timestamp"],16)>=WINDOW_START_TS
start_code=rpc("eth_getCode",[POOL,hex(START)])[0]
if start_code!="0x":
    raise RuntimeError("POOL_CODE_PRESENT_AT_FROZEN_2022_WINDOW_START")

def getlogs_once(a,b,topics):
    body={"jsonrpc":"2.0","id":a,"method":"eth_getLogs","params":[{"address":POOL,"fromBlock":hex(a),"toBlock":hex(b),"topics":topics}]}
    last=None
    for _ in range(max(6,len(URLS)*3)):
        d,status,h,url=post(body); last=(d,status,h,url)
        if status==200 and isinstance(d,dict) and isinstance(d.get("result"),list):
            logs=d["result"]
            for x in logs:
                assert a<=int(x["blockNumber"],16)<=b and x["address"].lower()==POOL and not x.get("removed",False)
            return logs,h,url
        time.sleep(.20)
    return None,last[2],last[3]
def scan(a,b,topics):
    logs,h,url=getlogs_once(a,b,topics)
    if logs is not None: return [(a,b,logs,h,url)]
    if a==b: raise RuntimeError("UNRESOLVED_SINGLE_BLOCK_"+str(a))
    m=(a+b)//2
    return scan(a,m,topics)+scan(m+1,b,topics)
def acquire(label,topics):
    cursor=START; out=[]; cov=[]; chunk=int(CFG["chunk"])
    while cursor<=SNAP:
        target=min(cursor+chunk-1,SNAP)
        for a,b,logs,h,url in scan(cursor,target,topics):
            assert a==cursor
            cov.append({"from":a,"to":b,"response_sha256":h,"source_url":url})
            out.extend(logs); cursor=b+1
        if len(cov)%50==0:
            (OUT/(label+"_checkpoint.json")).write_text(json.dumps({"frontier":cursor-1,"coverage":cov,"row_count":len(out)},indent=2)+"\n")
    complete=bool(cov) and cov[0]["from"]==START and cov[-1]["to"]==SNAP and all(cov[i]["to"]+1==cov[i+1]["from"] for i in range(len(cov)-1))
    return out,cov,complete

BASE_CHANGES=[x for x in SHOCK["changes"] if x["kind"]=="BASE_LT"]
EMODE_CHANGES=[x for x in SHOCK["changes"] if x["kind"]=="EMODE_LT"]

res_raw=call(POOL,SEL_RESERVES,"",SNAP)
off=word(res_raw,0)//32; n=word(res_raw,off)
RESERVES=["0x"+format(word(res_raw,off+1+i),"040x") for i in range(n)]
reserve_cache={}
def reserve(asset):
    asset=asset.lower()
    if asset not in reserve_cache:
        d=call(POOL,SEL_RESERVE,asset[2:].zfill(64),SNAP)
        cfg=word(d,0)
        reserve_cache[asset]={
          "asset":asset,"config_raw":str(cfg),"ltv_bps":cfg&0xffff,"lt_bps":(cfg>>16)&0xffff,
          "bonus_bps":(cfg>>32)&0xffff,"decimals":(cfg>>48)&0xff,"active":(cfg>>56)&1,
          "frozen":(cfg>>57)&1,"borrowing_enabled":(cfg>>58)&1,"stable_borrowing_enabled":(cfg>>59)&1,
          "paused":(cfg>>60)&1,"borrowable_in_isolation":(cfg>>61)&1,"siloed_borrowing":(cfg>>62)&1,
          "flashloan_enabled":(cfg>>63)&1,"emode_category":(cfg>>168)&0xff,
          "debt_ceiling_raw":str((cfg>>212)&((1<<40)-1)),
          "liquidity_index":str(word(d,1)),"current_liquidity_rate":str(word(d,2)),
          "variable_borrow_index":str(word(d,3)),"current_variable_borrow_rate":str(word(d,4)),
          "current_stable_borrow_rate":str(word(d,5)),
          "last_update_timestamp":word(d,6),"reserve_id":word(d,7),
          "aToken":"0x"+format(word(d,8),"040x"),"stableDebt":"0x"+format(word(d,9),"040x"),
          "variableDebt":"0x"+format(word(d,10),"040x"),
          "reserve_data_abi_sha256":sha(d.encode()),
        }
    return reserve_cache[asset]

old_state_checks=[]
for ch in BASE_CHANGES:
    r=reserve(ch["asset"])
    old_state_checks.append({"kind":"BASE_LT","asset":ch["asset"].lower(),"expected_old_lt":ch["old_lt"],"observed_old_lt":r["lt_bps"],"pass":r["lt_bps"]==ch["old_lt"]})
for ch in EMODE_CHANGES:
    raw=call(POOL,SEL_EMODE_DATA,format(int(ch["category_id"]),"064x"),SNAP)
    dec=decode_emode(raw); obs=dec["lt_bps"]
    old_state_checks.append({"kind":"EMODE_LT","category_id":ch["category_id"],"expected_old_lt":ch["old_lt"],"observed_old_lt":obs,"pass":obs==ch["old_lt"],"emode_data":dec,"emode_data_abi_sha256":sha(raw.encode())})
if not all(x["pass"] for x in old_state_checks):
    raise RuntimeError("OLD_LT_SIGNAL_MINUS_ONE_MISMATCH:"+json.dumps(old_state_checks))

base_logs=[]; base_cov=[]; base_complete=True
base_active={}
if BASE_CHANGES:
    asset_topics=[topic_addr(x["asset"]) for x in BASE_CHANGES]
    base_logs,base_cov,base_complete=acquire("base_collateral",[[EN,DIS],asset_topics])
    base_logs.sort(key=lambda l:(int(l["blockNumber"],16),int(l["transactionIndex"],16),int(l["logIndex"],16)))
    for l in base_logs:
        asset="0x"+l["topics"][1][-40:].lower(); user="0x"+l["topics"][2][-40:].lower()
        base_active[(asset,user)]=(l["topics"][0].lower()==EN)

em_logs=[]; em_cov=[]; em_complete=True
emode_active={}
if EMODE_CHANGES:
    em_logs,em_cov,em_complete=acquire("emode",[EM])
    em_logs.sort(key=lambda l:(int(l["blockNumber"],16),int(l["transactionIndex"],16),int(l["logIndex"],16)))
    for l in em_logs:
        user="0x"+l["topics"][1][-40:].lower(); emode_active[user]=word(l["data"],0)

cat_reserves={}; emode_membership_proof={}
for ch in EMODE_CHANGES:
    cat=int(ch["category_id"]); arr=[]; arg=format(cat,"064x")
    bitmap_raw=call_capability(POOL,SEL_EMODE_COLL_BITMAP,arg,SNAP)
    if bitmap_raw is not None:
        bitmap=word(bitmap_raw,0)
        for asset in RESERVES:
            r=reserve(asset)
            if bitmap & (1<<r["reserve_id"]):
                arr.append(r)
        borrow_raw=call_capability(POOL,SEL_EMODE_BORROW_BITMAP,arg,SNAP)
        ltvzero_raw=call_capability(POOL,SEL_EMODE_LTVZERO_BITMAP,arg,SNAP)
        isolated_raw=call_capability(POOL,SEL_EMODE_ISOLATED,arg,SNAP)
        emode_membership_proof[cat]={
          "mode":"BITMAP_GETTER","collateral_bitmap":str(bitmap),
          "borrowable_bitmap":str(word(borrow_raw,0)) if borrow_raw else None,
          "ltvzero_bitmap":str(word(ltvzero_raw,0)) if ltvzero_raw else None,
          "isolated":bool(word(isolated_raw,0)) if isolated_raw else None,
        }
    else:
        for asset in RESERVES:
            r=reserve(asset)
            if r["emode_category"]==cat and r["lt_bps"]>0:
                arr.append(r)
        if not arr:
            raise RuntimeError("EMODE_MEMBERSHIP_UNRESOLVED_"+str(cat))
        emode_membership_proof[cat]={"mode":"LEGACY_RESERVE_CONFIGURATION_CATEGORY"}
    cat_reserves[cat]=arr

candidate_users=set()
for (asset,u),enabled in base_active.items():
    if enabled: candidate_users.add(u)
for ch in EMODE_CHANGES:
    cat=int(ch["category_id"])
    for u,c in emode_active.items():
        if c==cat: candidate_users.add(u)

def token_balance(token,user):
    if token.lower()==ZERO: return 0
    try:
        d=call(token,SEL_BAL,user[2:].zfill(64),SNAP); return word(d,0)
    except Exception as e:
        raise RuntimeError(f"BALANCE_CALL_FAILED:{token}:{user}:{type(e).__name__}:{e}")
def oracle_price(asset):
    d=call(ORACLE,SEL_PRICE,asset[2:].zfill(64),SNAP); return word(d,0)

qualified=[]; processed=0
for u in sorted(candidate_users):
    arg=u[2:].zfill(64)
    cfg=word(call(POOL,SEL_CFG,arg,SNAP),0)
    acc=call(POOL,SEL_ACC,arg,SNAP); av=[word(acc,j) for j in range(6)]
    em=word(call(POOL,SEL_EMODE,arg,SNAP),0)
    if av[1]==0 or (cfg&BORROW_MASK)==0:
        processed+=1; continue
    affected=[]
    for ch in BASE_CHANGES:
        r=reserve(ch["asset"]); bit=1<<((r["reserve_id"]<<1)+1)
        if (cfg&bit) and base_active.get((r["asset"],u),False):
            bal=token_balance(r["aToken"],u)
            if bal>0: affected.append({"kind":"BASE_LT","asset":r["asset"],"aToken_balance_raw":str(bal)})
    for ch in EMODE_CHANGES:
        cat=int(ch["category_id"])
        if em!=cat or emode_active.get(u)!=cat: continue
        assets=[]
        for r in cat_reserves[cat]:
            bit=1<<((r["reserve_id"]<<1)+1)
            if cfg&bit:
                bal=token_balance(r["aToken"],u)
                if bal>0: assets.append({"asset":r["asset"],"aToken_balance_raw":str(bal),"reserve_id":r["reserve_id"]})
        if assets: affected.append({"kind":"EMODE_LT","category_id":cat,"collateral":assets})
    if not affected:
        processed+=1; continue

    positions=[]; isolation_collateral=[]
    for asset in RESERVES:
        r=reserve(asset); rid=r["reserve_id"]
        borrow_bit=1<<(rid<<1); coll_bit=1<<((rid<<1)+1)
        if not (cfg&(borrow_bit|coll_bit)): continue
        at=token_balance(r["aToken"],u) if cfg&coll_bit else 0
        sd=token_balance(r["stableDebt"],u) if cfg&borrow_bit else 0
        vd=token_balance(r["variableDebt"],u) if cfg&borrow_bit else 0
        if at==0 and sd==0 and vd==0: continue
        price=oracle_price(asset)
        pos={
          "asset":asset,"reserve_id":rid,"user_collateral_enabled":bool(cfg&coll_bit),"user_borrowing_bit":bool(cfg&borrow_bit),
          "aToken_balance_raw":str(at),"stable_debt_raw":str(sd),"variable_debt_raw":str(vd),"oracle_price_raw":str(price),
          "reserve":r,
        }
        positions.append(pos)
        if (cfg&coll_bit) and at>0 and int(r["debt_ceiling_raw"])>0:
            isolation_collateral.append(asset)
    emode_data=None
    if em:
        raw=call(POOL,SEL_EMODE_DATA,format(em,"064x"),SNAP)
        emode_data={"category_id":em,**decode_emode(raw),"abi_sha256":sha(raw.encode())}
    row={
      "user":u,"account_data_raw":[str(x) for x in av],"user_configuration_raw":str(cfg),"emode_category":em,
      "affected_exposure":affected,"isolation_mode_active":bool(isolation_collateral),"isolation_collateral_assets":isolation_collateral,
      "emode_data":emode_data,"positions":positions,
    }
    qualified.append(row)
    with (OUT/"borrowers.jsonl").open("a") as f: f.write(json.dumps(row)+"\n")
    processed+=1
    if processed%25==0:
        (OUT/"borrower_progress.json").write_text(json.dumps({"processed":processed,"candidate_users":len(candidate_users),"qualified":len(qualified)},indent=2)+"\n")

receipt={
 "lab_id":"AAVE-GOV-LT-FORCED-DELEVERAGING-001","phase":"V37_PRE_SIGNAL_BORROWER_STATE_SOURCE_ONLY",
 "shock_id":SHOCK_ID,"governance":SHOCK["gov"],"proposal_id":SHOCK["proposal_id"],"chain":CHAIN,
 "signal_timestamp":SIGNAL_TS,"snapshot_block":SNAP,"snapshot_timestamp":int(SNAP_HEADER["timestamp"],16),
 "frozen_window_start_block":START,"frozen_window_start_timestamp":int(START_HEADER["timestamp"],16),"pool_code_at_window_start":start_code,
 "base_change_count":len(BASE_CHANGES),"emode_change_count":len(EMODE_CHANGES),"old_state_checks":old_state_checks,
 "base_event_coverage_complete":base_complete,"base_transition_logs":len(base_logs),"base_intervals":len(base_cov),
 "emode_event_coverage_complete":em_complete,"emode_transition_logs":len(em_logs),"emode_intervals":len(em_cov),
 "candidate_users":len(candidate_users),"qualified_borrower_count":len(qualified),
 "borrower_state_source_pass":bool(base_complete and em_complete and all(x["pass"] for x in old_state_checks)),
 "oracle":ORACLE,"pool":POOL,"reserve_count":len(RESERVES),"emode_membership_proof":emode_membership_proof,
 "source_gate_pass":False,"hypothesis_status":"NOT_TESTED",
 "economic_outcomes_opened":0,"development_runs":0,"outcomes_2026_opened":False,
}
(OUT/"RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
(OUT/"reserve_state.json").write_text(json.dumps({"snapshot_block":SNAP,"reserves":reserve_cache,"emode_category_reserves":{str(k):v for k,v in cat_reserves.items()}},indent=2)+"\n")
(OUT/"coverage.json").write_text(json.dumps({"base":base_cov,"emode":em_cov},indent=2)+"\n")
print(json.dumps(receipt,indent=2),flush=True)
