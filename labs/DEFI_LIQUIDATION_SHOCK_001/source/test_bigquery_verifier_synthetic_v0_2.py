#!/usr/bin/env python3
"""Network-free corrected Kamino verifier test."""
import importlib.util,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent

def load(name,fn):
    spec=importlib.util.spec_from_file_location(name,HERE/fn)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod

collector=load("collect_protocol_history_v0_1","collect_protocol_history_v0_1.py")
verifier=load("verify_bigquery_candidates_v0_1","verify_bigquery_candidates_v0_1.py")

def b58encode(blob:bytes)->str:
    n=int.from_bytes(blob,"big");out=""
    while n:
        n,rem=divmod(n,58);out=collector.BASE58_ALPHABET[rem]+out
    leading=len(blob)-len(blob.lstrip(b"\x00"))
    return "1"*leading+out

program="KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD"
correct=bytes.fromhex("b1479abce2854a37")+b"\0"*8
wrong=bytes.fromhex("b1479acce2854a37")+b"\0"*8

def tx(payload):
    return {
      "transaction":{"message":{"accountKeys":["payer","outer","acct"],
        "instructions":[{"programIdIndex":1,"accounts":[],"data":"1"}]}},
      "meta":{"err":None,"loadedAddresses":{"writable":[],"readonly":[program]},
        "innerInstructions":[{"index":0,"instructions":[
          {"programIdIndex":3,"accounts":[2],"data":b58encode(payload)}
        ]}]}
    }

row={"program_id":program,"parent_index":0,"instruction_index":0,"tx_signature":"sig"}
ix=verifier.find_instruction(tx(correct),row)
assert ix["location"]=="inner"
assert ix["prefix_8_hex"]=="b1479abce2854a37"
assert ix["data_hex"].startswith("b1479abce2854a37")
assert not ix["data_hex"].startswith("b1479acce2854a37")

ixw=verifier.find_instruction(tx(wrong),row)
assert ixw["prefix_8_hex"]=="b1479acce2854a37"
assert not ixw["data_hex"].startswith("b1479abce2854a37")

print("DLS_BIGQUERY_VERIFIER_KAMINO_V02_QA_PASS")
