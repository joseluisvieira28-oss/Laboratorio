#!/usr/bin/env python3
import importlib.util,json,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent

def load(name,fn):
    spec=importlib.util.spec_from_file_location(name,HERE/fn)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod

base=load("collect_protocol_history_v0_1","collect_protocol_history_v0_1.py")
v2=load("collect_protocol_history_v0_2","collect_protocol_history_v0_2.py")
reg=json.loads((HERE/"protocol_registry_v0_2.json").read_text())

assert reg["registry_version"]=="V0.2"
assert reg["lab_id"]=="DEFI-LIQUIDATION-SHOCK-001"
by={p["protocol"]:p for p in reg["protocols"]}
assert set(by)=={"save_solend","marginfi_v2","kamino_lend","drift_v2"}

kam=by["kamino_lend"]
active={x["prefix_hex"] for x in kam["reference_liquidation_encodings"]}
assert active=={"b1479abce2854a37"},active
assert "b1479acce2854a37" in kam["retired_wrong_prefixes"]

# Correct bytes match; retired bytes do not.
ix={"first_byte_hex":"b1","prefix_8_hex":"b1479abce2854a37"}
assert base.reference_matches(kam,ix)==["liquidate_obligation_and_redeem_reserve_collateral"]
ix_bad={"first_byte_hex":"b1","prefix_8_hex":"b1479acce2854a37"}
assert base.reference_matches(kam,ix_bad)==[]

drift=by["drift_v2"]
names={x["name"] for x in drift["reference_liquidation_encodings"]}
assert names=={
 "liquidate_perp","liquidate_spot","liquidate_borrow_for_perp_pnl","liquidate_perp_pnl_for_deposit"
},names
outside={x["name"] for x in drift["outside_frozen_window_reference_only"]}
assert outside=={"liquidate_spot_with_swap_begin","liquidate_spot_with_swap_end"}
assert names.isdisjoint(outside)

# Boundaries retained in active registry.
assert by["save_solend"]["reference_liquidation_encodings"][0]["source_supported_from"].startswith("2021-12-08")
assert by["marginfi_v2"]["reference_liquidation_encodings"][0]["source_supported_from"].startswith("2023-02-07")
assert kam["reference_liquidation_encodings"][0]["source_supported_from"].startswith("2023-11-17")
assert all(x["source_supported_from"].startswith("2022-11-04") for x in drift["reference_liquidation_encodings"])

print("DLS_SOURCE_REGISTRY_V02_QA_PASS")
