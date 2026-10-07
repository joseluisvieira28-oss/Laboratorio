#!/usr/bin/env python3
"""TMFCB V0.2 metadata-only CoinGecko ID resolver.
Never requests market_data or historical price endpoints.
Outputs only id/symbol/name metadata.
"""
import json, urllib.request, sys, time

URL = "https://api.coingecko.com/api/v3/coins/list"
TARGETS = [
    {"label":"MC","symbols":["mc"],"names":["Merit Circle"]},
    {"label":"BEAM","symbols":["beam"],"names":["Beam"]},
    {"label":"OGV","symbols":["ogv"],"names":["Origin Dollar Governance"]},
    {"label":"OGN","symbols":["ogn"],"names":["Origin Protocol"]},
    {"label":"LBR","symbols":["lbr"],"names":["Lybra Finance"]},
    {"label":"MPL","symbols":["mpl"],"names":["Maple"]},
    {"label":"SYRUP","symbols":["syrup"],"names":["Syrup"]},
    {"label":"ANT","symbols":["ant"],"names":["Aragon"]},
    {"label":"ETH","symbols":["eth"],"names":["Ethereum"]},
    {"label":"CUDOS","symbols":["cudos"],"names":["Cudos"]},
    {"label":"FET","symbols":["fet"],"names":["Artificial Superintelligence Alliance","Fetch.ai"]},
    {"label":"RAINI","symbols":["raini"],"names":["Raini","Rainicorn"]},
    {"label":"RST","symbols":["rst"],"names":["Raini Studios Token"]},
    {"label":"MFT","symbols":["mft"],"names":["Mainframe"]},
    {"label":"HIFI","symbols":["hifi"],"names":["Hifi Finance"]},
    {"label":"BIT","symbols":["bit"],"names":["BitDAO"]},
    {"label":"MNT","symbols":["mnt"],"names":["Mantle"]},
    {"label":"GAL","symbols":["gal"],"names":["Galxe"]},
    {"label":"G","symbols":["g"],"names":["Gravity"]},
    {"label":"GRO","symbols":["gro"],"names":["Gro DAO Token","GRO"]},
    {"label":"USDC","symbols":["usdc"],"names":["USDC","USD Coin"]},
    {"label":"FEI","symbols":["fei"],"names":["Fei USD"]},
    {"label":"DAI","symbols":["dai"],"names":["Dai"]},
    {"label":"ROOK","symbols":["rook"],"names":["Rook"]},
    {"label":"JADE","symbols":["jade"],"names":["Jade Protocol"]},
]
req=urllib.request.Request(URL, headers={"User-Agent":"CryptoLab-TMFCB-SourceProbe/0.2"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        data=json.load(r)
except Exception as e:
    print("SOURCE_METADATA_FETCH=FAIL")
    print("ERROR_TYPE="+type(e).__name__)
    sys.exit(2)
print("SOURCE_METADATA_FETCH=PASS")
for t in TARGETS:
    syms={s.lower() for s in t["symbols"]}
    names={n.lower() for n in t["names"]}
    matches=[]
    for c in data:
        sym=str(c.get("symbol","")).lower()
        name=str(c.get("name","")).lower()
        if sym in syms or name in names:
            matches.append({"id":c.get("id"),"symbol":c.get("symbol"),"name":c.get("name")})
    print(t["label"]+"="+json.dumps(matches, sort_keys=True))
