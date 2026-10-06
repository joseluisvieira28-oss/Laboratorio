#!/usr/bin/env python3
"""Decode audited V05 Ethereum 2025 configurator logs. SOURCE ONLY."""
import json, hashlib
from collections import Counter, defaultdict
from pathlib import Path
from Crypto.Hash import keccak

ROOT=Path(__file__).resolve().parent
INPUT=Path("input")
OUT=Path("out/aave_decode_v06"); OUT.mkdir(parents=True,exist_ok=True)
checkpoint=json.loads((INPUT/"checkpoint.json").read_text())
abi_artifact=json.loads((INPUT/"PoolConfigurator.json").read_text())
abi=abi_artifact["abi"] if isinstance(abi_artifact,dict) else abi_artifact
prior=json.loads((ROOT/"source_cache/PRIOR_ETHEREUM_BASE_LT_CENSUS_2023_2024.json").read_text())

def topic(sig):
 k=keccak.new(digest_bits=256); k.update(sig.encode()); return "0x"+k.hexdigest()
events={}
for x in abi:
 if x.get("type")!="event": continue
 sig=x["name"]+"("+",".join(i["type"] for i in x["inputs"])+")"
 events[topic(sig)]={"name":x["name"],"signature":sig,"inputs":x["inputs"]}
# Events introduced after the legacy ABI, pinned to aave-dao/aave-v3-origin
# commit 8305565ae342f1773c42cd2e4593f175fe5968a0 IPoolConfigurator.sol.
for name,sig in {
 "ReserveInterestRateDataChanged":"ReserveInterestRateDataChanged(address,address,bytes)",
 "PendingLtvChanged":"PendingLtvChanged(address,uint256)",
 "LiquidationGracePeriodDisabled":"LiquidationGracePeriodDisabled(address)",
 "ReserveFlashLoaning":"ReserveFlashLoaning(address,bool)",\n "ConfiguratorProxyUpgraded":"Upgraded(address)",
}.items(): events[topic(sig)]={"name":name,"signature":sig,"inputs":[]}
rows=checkpoint["rows"]
unknown=Counter(x["topics"][0] for x in rows if x["topics"][0] not in events)
decoded_counts=Counter(events[x["topics"][0]]["name"] if x["topics"][0] in events else "UNKNOWN:"+x["topics"][0] for x in rows)
coll_topic=topic("CollateralConfigurationChanged(address,uint256,uint256,uint256)")
emode_topic=topic("EModeCategoryAdded(uint8,uint256,uint256,uint256,address,string)")

def words(data):
 h=data[2:]; return [int(h[i:i+64],16) for i in range(0,len(h),64)]
def address_from_topic(t): return "0x"+t[-40:].lower()

prior_state={}
for x in prior["configuration_history"]:
 prior_state[x["asset"].lower()]={"ltv":int(x["ltv"]),"lt":int(x["liquidationThreshold"]),"lb":int(x["liquidationBonus"]),"block":x["block"]}
base_rows=[]; base_decreases=[]; base_disablements=[]; state=dict(prior_state)
for l in rows:
 if l["topics"][0]!=coll_topic: continue
 asset=address_from_topic(l["topics"][1]); w=words(l["data"]); cur={"ltv":w[0],"lt":w[1],"lb":w[2]}
 old=state.get(asset); baseline=old is None
 rec={"asset":asset,"block":int(l["blockNumber"],16),"timestamp":int(l["blockTimestamp"],16),"tx":l["transactionHash"],"log_index":int(l["logIndex"],16),"old":old,"new":cur,"baseline_only":baseline}
 if old is not None and cur["lt"]<old["lt"]: base_decreases.append(rec)
 if old is not None and old["lt"]>0 and cur["lt"]==0: base_disablements.append(rec)
 base_rows.append(rec); state[asset]={**cur,"block":rec["block"]}

emode_state={}; emode_rows=[]; emode_decreases=[]
for l in rows:
 if l["topics"][0]!=emode_topic: continue
 cat=int(l["topics"][1],16); w=words(l["data"]); cur={"ltv":w[0],"lt":w[1],"lb":w[2]}
 old=emode_state.get(cat); baseline=old is None
 rec={"category_id":cat,"block":int(l["blockNumber"],16),"timestamp":int(l["blockTimestamp"],16),"tx":l["transactionHash"],"log_index":int(l["logIndex"],16),"old":old,"new":cur,"baseline_only":baseline}
 if old is not None and cur["lt"]<old["lt"]: emode_decreases.append(rec)
 emode_rows.append(rec); emode_state[cat]=cur

receipt={
 "mission":"AAVE-GOV-LT-FORCED-DELEVERAGING-001",
 "phase":"V06_ABI_DECODE_SOURCE_ONLY",
 "classification":"SOURCE_GATE_PENDING",
 "hypothesis_status":"NOT_TESTED",
 "source_gate_pass":False,
 "input_run_id":37451732395,
 "input_artifact_id":11414119373,
 "input_zip_sha256":"8b8f6d9ab50dca646227f89f411b4b7b50d5a9da06bf29e8ab2e8d638dcfd57f",
 "input_terminal":checkpoint["receipt"]["terminal"],
 "input_unique_logs":len(rows),
 "decoded_event_count":sum(decoded_counts.values()),
 "unknown_topic_count":sum(unknown.values()),
 "unknown_topics":dict(sorted(unknown.items())),
 "event_counts":dict(sorted(decoded_counts.items())),
 "collateral_configuration_rows_2025":len(base_rows),
 "base_lt_decreases_2025":len(base_decreases),
 "base_collateral_disablements_2025":len(base_disablements),
 "emode_category_rows_2025":len(emode_rows),
 "emode_categories_observed_2025":len(emode_state),
 "emode_lt_decreases_after_first_observation_2025":len(emode_decreases),
 "prior_base_lt_decreases_2023_2024":prior["primary_decrease_log_count"],
 "prior_independent_episodes_2023_2024":prior["independent_24h_episode_count"],
 "independent_fully_source_gated_shocks":0,
 "defensible_independent_shock_universe":"UNKNOWN",
 "unresolved":["pre-2025 eMode category state/history","governance approved/queued lineage for all candidates","upgrade semantic boundaries","complete borrower exposure reconstruction"],
 "economic_outcomes_opened":0,"development_runs":0,"outcomes_2026_opened":False
}
assert receipt["input_terminal"]==24136052 and receipt["input_unique_logs"]==1386
assert receipt["unknown_topic_count"]==0
(OUT/"RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True))
(OUT/"DECODED_EVENTS.json").write_text(json.dumps({"receipt":receipt,"base_rows":base_rows,"base_decreases":base_decreases,"base_disablements":base_disablements,"emode_rows":emode_rows,"emode_decreases":emode_decreases},indent=2,sort_keys=True))
print(json.dumps(receipt,sort_keys=True))
