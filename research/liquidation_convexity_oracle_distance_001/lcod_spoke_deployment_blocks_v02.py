#!/usr/bin/env python3
import hashlib,json,time,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path

RPC="https://eth-mainnet.public.blastapi.io"
OUT=Path("artifacts/lcod_spoke_deployment_blocks_v02.json")
SPOKES={
"BLUECHIP":"0x973a023A77420ba610f06b3858aD991Df6d85A08",
"ETHENA_CORRELATED":"0x58131E79531caB1d52301228d1f7b842F26B9649",
"ETHENA_ECOSYSTEM":"0xba1B3D55D249692b669A164024A838309B7508AF",
"FOREX":"0xD8B93635b8C6d0fF98CbE90b5988E3F2d1Cd9da1",
"GOLD":"0x65407b940966954b23dfA3caA5C0702bB42984DC",
"LOMBARD_BTC":"0x7EC68b5695e803e98a21a9A05d744F28b0a7753D",
"MAIN":"0x94e7A5dCbE816e498b89aB752661904E2F56c485",
"PAXG_GOLD":"0xAD75cE6354f87F3135cE10621d385d8D1e2562C2",
"USDG_PENDLE":"0x956d8e0A89cfa3744428C4641b5a53B56167a7f9",
"ETHERFI_ESPOKE":"0xbF10BDfE177dE0336aFD7fcCF80A904E15386219",
"KELP_ESPOKE":"0x3131FE68C4722e726fe6B2819ED68e514395B9a4",
"LIDO_ESPOKE":"0xe1900480ac69f0B296841Cd01cC37546d92F35Cd",
"USDG_MAPLE_ESPOKE":"0x774b9655413c34809c1f1b16b654465A89EBE989",
}

def post(payload,timeout=45):
    raw=json.dumps(payload).encode()
    last=None
    for a in range(8):
        try:
            req=urllib.request.Request(RPC,data=raw,headers={"Content-Type":"application/json","User-Agent":"CryptoLab-LCOD-DeployPin/0.2"},method="POST")
            with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as e:
            last=e
            if a==7:raise
            time.sleep(min(0.5*(2**a),8))
    raise last

def rpc(method,params):
    x=json.loads(post({"jsonrpc":"2.0","id":1,"method":method,"params":params}).decode())
    if x.get("error"):raise RuntimeError(x["error"])
    return x.get("result")

final=rpc("eth_getBlockByNumber",["finalized",False])
N=int(final["number"],16)
N_hash=final["hash"]
rows=[]
for name,address in SPOKES.items():
    addr=address.lower()
    latest_code=rpc("eth_getCode",[addr,hex(N)])
    if latest_code in ("0x","0x0",None):
        rows.append({"name":name,"address":addr,"pass":False,"error":"NO_CODE_AT_FINALIZED"})
        continue
    lo=0;hi=N;calls=1
    while lo<hi:
        mid=(lo+hi)//2
        code=rpc("eth_getCode",[addr,hex(mid)]);calls+=1
        if code in ("0x","0x0",None):lo=mid+1
        else:hi=mid
    first=lo
    before=rpc("eth_getCode",[addr,hex(first-1)]) if first>0 else "0x";calls+=1
    at=rpc("eth_getCode",[addr,hex(first)]);calls+=1
    ok=(before in ("0x","0x0",None) and at not in ("0x","0x0",None))
    rows.append({"name":name,"address":addr,"first_code_block":first,
                 "code_sha256":hashlib.sha256(at.encode()).hexdigest(),
                 "binary_search_rpc_calls":calls,"pass":ok})

receipt={
 "lab_id":"LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001",
 "stage":"OFFICIAL_SPOKE_DEPLOYMENT_BLOCK_PIN_V0.2",
 "captured_at_utc":datetime.now(timezone.utc).isoformat(),
 "classification":"SPOKE_DEPLOYMENT_BLOCKS_PASS" if len(rows)==13 and all(x["pass"] for x in rows) else "SPOKE_DEPLOYMENT_BLOCKS_BLOCKED",
 "finalized_block_number":N,"finalized_block_hash":N_hash,
 "spokes":rows,"mutation":False,"market_returns_opened":False,
 "liquidation_outcomes_opened":False,"pnl_opened":False
}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2))
if receipt["classification"]!="SPOKE_DEPLOYMENT_BLOCKS_PASS":raise SystemExit(2)
