#!/usr/bin/env python3
"""BACKES-003: forensic attribution of unchanged BACKES-002. Read-only.\nThis module must never tune any trading rule on its diagnostic sample.\n"""
import concurrent.futures as cf
import datetime as dt
import importlib.util
import json
import math
import pathlib

HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("frozen_002",HERE.parent/"backes-diamante-002"/"rotation_backtest.py")
base=importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
OUT=HERE/"results"
WINDOWS=((2018,2022),(2023,2024),(2025,2026),(2018,2026))
BPS=10

def attribution(btc,eth,states,yr1,yr2,bps=10):
    ix=[i for i,w in enumerate(btc) if yr1<=int(w["date"][:4])<=yr2]
    if not ix:raise ValueError("empty window")
    cost=bps/10000
    out=[]; prev=None; rot=btc_nav=1.
    for j,i in enumerate(ix):
        ni=ix[j+1] if j+1<len(ix) else None
        br=(btc[ni]["open"] if ni is not None else btc[i]["close"])/btc[i]["open"]
        er=(eth[ni]["open"] if ni is not None else eth[i]["close"])/eth[i]["open"]
        held="ETH" if i>0 and states[i-1]=="ETH" else "BTC"
        switch=(j==0 or held!=prev)
        r=(1-cost if switch else 1)*(er if held=="ETH" else br)
        b=(1-cost if j==0 else 1)*br
        rot*=r;btc_nav*=b;prev=held
        excess=100*math.log(r/b)
        out.append(dict(start=btc[i]["date"],
          end=str(dt.date.fromisoformat(btc[i]["date"])+dt.timedelta(days=6)),
          held=held,switch=switch,btc_week_pct=100*(br-1),
          eth_week_pct=100*(er-1),
          eth_rel_btc_log_pct=100*math.log(er/br),
          excess_log_pct=excess,
          realized_btc_regime="UP" if br>=1 else "DOWN",
          rot_nav=rot,btc_nav=btc_nav))
    ref,switches,_=base.simulate(btc,eth,states,yr1,yr2,bps,False)
    if abs((rot-1)*100-ref["ROT"]["total_return_pct"])>.0002:raise ValueError("ROT reproduction failed")
    if abs((btc_nav-1)*100-ref["BTC"]["total_return_pct"])>.0002:raise ValueError("BTC reproduction failed")
    if abs(sum(x["excess_log_pct"] for x in out)-100*math.log(rot/btc_nav))>1e-8:
        raise ValueError("log attribution checksum failed")
    return out,ref,switches

def episodes(rows):
    es=[]
    for x in rows:
        if not es or es[-1]["asset"]!=x["held"]:
            es.append(dict(asset=x["held"],start=x["start"],end=x["end"],weeks=0,excess_log_pct=0.))
        o=es[-1];o["end"]=x["end"];o["weeks"]+=1;o["excess_log_pct"]+=x["excess_log_pct"]
    return es

def diagnostics(btc,eth,states,yr1,yr2):
    rows,ref,sw=attribution(btc,eth,states,yr1,yr2)
    logs=[x["excess_log_pct"] for x in rows]
    by_regime={}
    for status in ("UP","DOWN"):
        for asset in ("ETH","BTC"):
            a=[x for x in rows if x["held"]==asset and x["realized_btc_regime"]==status]
            by_regime[status+"_"+asset]=dict(n=len(a),excess_log_pct=sum(x["excess_log_pct"] for x in a))
    return dict(window=f"{yr1}-{yr2}",weeks=len(rows),switches=sw,
        eth_weeks=sum(x["held"]=="ETH" for x in rows),
        excess_log_pct=sum(logs),
        positive_log_pct=sum(x for x in logs if x>0),
        negative_log_pct=sum(x for x in logs if x<0),
        best=sorted(rows,key=lambda x:-x["excess_log_pct"])[:5],
        worst=sorted(rows,key=lambda x:x["excess_log_pct"])[:5],
        periods=episodes(rows),observed_regime_not_predictive=by_regime,
        reference=ref,weekly=rows)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    files=[];errors=[]
    with cf.ThreadPoolExecutor(max_workers=12) as pool:
        fut=[pool.submit(base.download,x) for x in base.jobs()]
        for f in cf.as_completed(fut):
            try:files.append(f.result())
            except Exception as e:errors.append(str(e))
    manifest={"source_zip_files":sorted(files,key=lambda x:x["file"]),"errors":errors}
    (OUT/"source_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    if errors or len(files)!=384:
        (OUT/"RESULT.md").write_text("# SOURCE_BLOCKED\n"+str(errors[:5]))
        raise ValueError("SOURCE_BLOCKED: downloads missing")
    w={sym:base.parse(files,sym) for sym in base.SYMS}
    a,b,c=w["BTCUSDT"],w["ETHUSDT"],w["ETHBTC"]
    for x,y,z in zip(a,b,c):
        if x["date"]!=y["date"] or x["date"]!=z["date"] or not .9<z["open"]/(y["open"]/x["open"])<1.1:
            raise ValueError("SOURCE_BLOCKED: cross market mismatch")
    states=base.signals(c)
    summaries=[diagnostics(a,b,states,*window) for window in WINDOWS]
    result={"study":"BACKES-DIAMANTE-003","data_cutoff":str(base.END),
       "method":"UNCHANGED BACKES-002, descriptive hindsight attribution",
       "not_backes_private_strategy":True,"trades":0,"summaries":summaries}
    (OUT/"diagnostics.json").write_text(json.dumps(result,indent=2)+"\n")
    s=next(x for x in summaries if x["window"]=="2025-2026")
    lines=["# BACKES-003 — Histórico: Atribuição sem otimização","",
      "Dados originais: Binance Spot; 384 ZIPs verificados por SHA256 no manifesto.",
      "Este estudo usa a estratégia de laboratório BACKES-002, não a estratégia privada de Augusto Backes.",
      "Todos os regimes rotulados como UP/DOWN usam retornos realizados e são APENAS descritivos.","",
      "## 2025–2026: excesso logarítmico de ROT face a BTC",
      f"- Excesso acumulado: {s['excess_log_pct']:+.3f} log-pontos percentuais",
      f"- Semanas em ETH: {s['eth_weeks']}/{s['weeks']}; mudanças entre ativos: {s['switches']}",
      f"- Contribuições positivas: {s['positive_log_pct']:+.3f} log-pp; negativas: {s['negative_log_pct']:+.3f} log-pp",
      "", "## Períodos sem mudança de ativo", "",
      "| Ativo | Inicio UTC | Fim UTC | Semanas | Excesso log face ao BTC |",
      "|---|---|---|---:|---:|"]
    for e in s["periods"]:
        lines.append(f"| {e['asset']} | {e['start']} | {e['end']} | {e['weeks']} | {e['excess_log_pct']:+.3f} |")
    lines+=["","## As 5 semanas que mais explicam a diferença (a posteriori)"]
    for q in s["best"]:lines.append(f"- {q['start']} {q['held']}: {q['excess_log_pct']:+.3f} log-pp")
    lines+=["","## As 5 semanas que mais prejudicaram a rotação"]
    for q in s["worst"]:lines.append(f"- {q['start']} {q['held']}: {q['excess_log_pct']:+.3f} log-pp")
    lines+=["","## Comparação entre períodos","",
       "| Período | Excesso log face ao BTC | ETH semanas | Trocas | Rotação max DD |",
       "|---|---:|---:|---:|---:|"]
    for q in summaries:
        lines.append(f"| {q['window']} | {q['excess_log_pct']:+.3f} | {q['eth_weeks']} | {q['switches']} | {q['reference']['ROT']['max_drawdown_pct']:.2f}% |")
    lines+=["","## Limites e decisão","",
      "Os vencedores e perdedores são observações do passado, não variáveis preditivas acessíveis antes da operação.",
      "Não foi alterado nenhum parâmetro da estratégia; não há sinal independente nem lucros futuros demonstrados.",
      "NO-GO económico e para trading real. GO para registo futuro de sinais temporizados sem capital."]
    (OUT/"RESULT.md").write_text("\n".join(lines)+"\n")
    print("ATTRIBUTION_OK",len(files),"ZIP",len(a),"weeks",s["switches"],"switches_recent")
if __name__=="__main__":main()
