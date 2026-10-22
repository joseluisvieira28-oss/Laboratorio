import json,pathlib,math,hashlib,datetime,zipfile,csv,io
P=pathlib.Path(__file__).resolve().parent
r=json.loads((P/"DCA_RESULTS.json").read_text()); runs=json.loads((P/"DCA_LEDGERS.json").read_text())
checks=0
def check(ok):
    global checks
    assert ok
    checks+=1
for v in runs:
    c=v["cost_bps_per_side"]/10000
    dep=sum(x["contribution"] for x in v["ledger"])
    check(abs(dep-v["contributions"])<1e-9)
    check(abs(sum(x["notional"]+x["friction"] for x in v["ledger"])+v["terminal_cash_before_sale"]-dep)<1e-7)
    check(abs(v["total_friction"]-c*v["gross_turnover"])<1e-8)
    check(all(x["cash"]>=0 and x["units"]>=0 for x in v["ledger"]))
    check(abs(sum(x["friction"] for x in v["ledger"])+v["terminal_sell_cost"]-v["total_friction"])<1e-8)
    prior=0
    for x in v["ledger"]:
        check(abs((x["units"]-prior)*x["price"]-x["notional"])<1e-7)
        prior=x["units"]
    check(abs(prior-v["terminal_units_before_sale"])<1e-12)
    if v["mode"]=="cash": check(v["net_terminal_wealth"]==dep)
for y in range(2021,2026):
    check(len({x["contributions"] for x in runs if x["year"]==y})==1)
for e in r["effects"]:
    selected={x["mode"]:x for x in runs if x["year"]==e["year"] and x["cost_bps_per_side"]==e["cost_bps_per_side"]}
    expected=(selected["adaptive"]["net_terminal_wealth"]-selected["fixed"]["net_terminal_wealth"])/selected["fixed"]["contributions"]
    check(abs(expected-e["effect_on_contributions"])<1e-12)
out={"checks_passed":checks,"status":"PASS","kind":"Independent ledger accounting verification; no parameter changes or outcome rerun","at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"results_sha256":hashlib.sha256((P/"DCA_RESULTS.json").read_bytes()).hexdigest(),"runner_sha256":hashlib.sha256((P/"dca_replay.py").read_bytes()).hexdigest()}
(P/"ACCOUNTING_VERIFICATION.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out))
