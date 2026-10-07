#!/usr/bin/env python3
"""Map known Aave LT-decrease effect txs to Aave Governance V3 proposal IDs.

SOURCE-ONLY. Reads a pinned checkout of aave-dao/seatbelt-gov-v3.
No outcomes, borrower state, or 2026 data.
"""
import json,re,os
from pathlib import Path

ROOT=Path(os.environ["SEATBELT_ROOT"])
OUT=Path("out/aave_proposal_mapper_v16"); OUT.mkdir(parents=True,exist_ok=True)

CANDIDATES={
 "optimism":[
 "0x50097b7a4ae1464f7c78b3be86da487b15a4aa8f9e7b95784844a4c279145b1d",
 "0x367cce6e426cdc69a071afeff846189b69db43f101163fb2710399f51c40d3f4",
 "0x22c2eb7b02ae215657fdccfc4d923b78dc035eefa85d23950c8074fc925d9444",
 "0xa8ecf8b94a86aac1e68db482e01282cc4e66a051cc7c97d816ed293443db9538",
 "0x32d60434b74e59c69ecf7a06d38b67527245aff9c2e5eef7e3bc5da3e30fbac9",
 "0x6d6f4750a7109b7322de3782ffdd6f7e6a99a079242a7929481802f7094a026f",
 "0x99af268f6b4145c78bc2239bb21e84e196638704ad9a3a15dd808742535bd485",
 "0xf646ec46e06384edbed76231bbb0fb92ea4d5de33f083079721684ca14047a50"],
 "avalanche":[
 "0x59b8f6193d7aa5442fcff2ec739ac6355a6b78a0084be7156229f049f9738329",
 "0xce6ac8064744d211867be08855d0e66860a55875afe185ef79cd511d4f476d59",
 "0xa384379aea3b70bf3f56c3bafc01d8c0fa0464207367fd21135352ba65b320d7",
 "0xa3c46c26959c03b46a0937a91c6650cb9e12ee7ca05119786ae2216db4b721c5",
 "0x5cc4982eb7025f24d16f15adc99bf06d553e43d6b7b69ee96a0707d7fdd4db6f",
 "0x5e11d89fd7bb790e4eef4c39936abf490aa1fe23fb5818684bfe69b3b0f01104",
 "0xb15cb870965d67987456f2cc9f022b9487ca21e2648fefce4c4ad7bbf577d80a",
 "0xbf97694ed5c2e26b9f95bbf49b892e2cbef9b40e5011cd44d6e4c2a8122ea624"],
 "arbitrum":[
 "0xf6b23f657ee1c9981f70de679b94774c32ad21a000bbfbbc88a56339125bfaa5",
 "0xf36d02fe4f8e52681e96c2fc7893821be6bcd38859354dc0c69a860cf090eae3",
 "0x76a5cc2c78abb8823eb43e38ec1951d4b48e225e61e5407c18b1b9ca5077478d",
 "0xb91c08b19b5c0bbbfe1218bcdf9f86d90a44a185bc2f9b1570a5b2cbd1340bb9",
 "0x9313ad46a6ff44a55b43108a48508f29a9976858856e2005108fb0d60156d523",
 "0xded61a74f3a8fb11441dc68cadc53afd51afca41bbe31abeca9c8ccc5dbd2c26",
 "0x5c5186993fe7cbc0e3c4390c75745a01058db0cc32a9417d950db0863fbb550c"],
 "polygon":[
 "0x4fcbf9258c3932cf76d36c83f052f9330c51cffd361ebc66151491481c5f8978",
 "0x8d128ca9c637576b6a0d967da565cff139a492a749108fed2ac35f4e9bf888a9",
 "0xa76d93fba3c709b11fdde86b1b1b92ac0b47ec978083414987218b1618e93d1d",
 "0x02efe2f6e301c2169f94218b338bdcaead73e2bc0bd039c9c440ae50edc5a251",
 "0x00bf99a3ba3b014a7753157eb633a54f17bf128c067ba883f10789aabc6c7d2f",
 "0x567d257898d99fed55a7c5b69771545f4f8452211f0fefc4e2cc0797f38389df",
 "0x4a68392fa153577d9c6a0580979c426bb708448d2c7d1f92b847e6b294cbdef2",
 "0x57e0f344b2922a31be65d520024d21ced0ff75f520e528805c600c357381317b",
 "0x632883fea7ce5790141cf187beda7181c7029c780bbe3beef30dcea5b78fbdb5",
 "0x71bf17962248f4a406c1b3cbb6b927391504832774f1a9175368bc706a977b09",
 "0x07eaf8fcfbb4a34bf3bbfb50de2116785eba6d74d5a2ac96a55f85d07fa15e98",
 "0xd99064b3668c92d453973ffa84cb56fd52fcc8720aae853f247fb00a853371ae",
 "0xaf73caa4050d0abf0a8b9bb0cb6b37b8c9ac74e1196a352a3e71d4d7e707ccb4"]
}
# V2 AIP-233 effect txs are intentionally excluded from V3 proposal counting.
payload_files=list((ROOT/"reports/payloads").rglob("*.md"))
proposal_files=list((ROOT/"reports/proposals").glob("*.md"))
payload_text={p:p.read_text(errors="replace").lower() for p in payload_files}
proposal_text={p:p.read_text(errors="replace") for p in proposal_files}

rows=[]
for chain,txs in CANDIDATES.items():
 for tx in txs:
  matches=[p for p,t in payload_text.items() if tx.lower() in t]
  row={"chain":chain,"effect_tx":tx,"payload_report_matches":[str(p.relative_to(ROOT)) for p in matches]}
  if len(matches)==1:
   rel=str(matches[0].relative_to(ROOT)).replace("\\","/")
   # Proposal reports link as /reports/payloads/... or reports/payloads/...
   props=[]
   for p,t in proposal_text.items():
    if rel in t or ("/"+rel) in t:
     m=re.search(r"reports/proposals/(\d+)\.md$",str(p).replace("\\","/"))
     if m: props.append(int(m.group(1)))
   row["proposal_ids"]=sorted(set(props))
   row["status"]="UNIQUE_PROPOSAL_LINK" if len(set(props))==1 else ("NO_PROPOSAL_LINK" if not props else "AMBIGUOUS_PROPOSAL_LINK")
  else:
   row["proposal_ids"]=[]
   row["status"]="NO_UNIQUE_PAYLOAD_REPORT"
  rows.append(row)

proposal_ids=sorted({pid for r in rows for pid in r["proposal_ids"] if r["status"]=="UNIQUE_PROPOSAL_LINK"})
by_proposal={}
for pid in proposal_ids:
 by_proposal[str(pid)]=[{"chain":r["chain"],"effect_tx":r["effect_tx"],"payload_report":r["payload_report_matches"][0]} for r in rows if r.get("proposal_ids")==[pid]]
receipt={
 "lab_id":"AAVE-GOV-LT-FORCED-DELEVERAGING-001",
 "phase":"V16_GOVERNANCE_V3_PROPOSAL_CLUSTERING_SOURCE_ONLY",
 "seatbelt_repo":"aave-dao/seatbelt-gov-v3",
 "seatbelt_commit":os.environ["SEATBELT_COMMIT"],
 "candidate_v3_effects":len(rows),
 "unique_proposal_link_rows":sum(r["status"]=="UNIQUE_PROPOSAL_LINK" for r in rows),
 "no_proposal_link_rows":sum(r["status"]=="NO_PROPOSAL_LINK" for r in rows),
 "ambiguous_rows":sum(r["status"] in {"AMBIGUOUS_PROPOSAL_LINK","NO_UNIQUE_PAYLOAD_REPORT"} for r in rows),
 "distinct_v3_proposal_ids":proposal_ids,
 "distinct_v3_proposal_count":len(proposal_ids),
 "rows":rows,
 "clusters":by_proposal,
 "v2_aip233_not_counted_here":True,
 "source_gate_pass":False,
 "hypothesis_status":"NOT_TESTED",
 "economic_outcomes_opened":0,
 "development_runs":0,
 "outcomes_2026_opened":False
}
(OUT/"RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
print(json.dumps({k:v for k,v in receipt.items() if k not in {"rows","clusters"}},indent=2))
for r in rows: print(json.dumps(r))
