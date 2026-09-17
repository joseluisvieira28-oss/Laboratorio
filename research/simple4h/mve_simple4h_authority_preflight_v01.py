#!/usr/bin/env python3
import argparse, csv, gzip, hashlib, io, json, sys, zipfile

PKG_SHA = "2bd1fa5170f2464445164caa7cf5f8b9df4808464cbd3aef30978f445771873e"
RES_SHA = "b23798fbe6b8f674be94014add8d2b00278cffdcf7889a01b2ec0917fd89134d"
PKG_INTERNAL = {
    "SIMPLE_TRADING_LAB_SCIENTIFIC_FREEZE_V0.1.md": "6f126041a8729f6ecec89afb92c4b58a5f391f91f00b855f5cd1becdbc1a8efa",
    "simple_trading_lab_v01.py": "b4549b53247ff67c8bf4cbbf780611c8231eb1be72a52ae240168de2fa7ac71a",
}
RES_INTERNAL = {
    "SIMPLE_TRADING_LAB_RESULTS_V0.1/ST_CLOSEOUT_V0.1.json": "6e08f5ca8b9578e551cab31a70b6b8c8ae6e3ab33e766691dbc31851f15062b2",
    "SIMPLE_TRADING_LAB_RESULTS_V0.1/ST_EVENTS_V0.1.csv.gz": "dc33df026d851cf4e7245b33c7b842e164b70ba783d38cef6d606b57b46a3f11",
    "SIMPLE_TRADING_LAB_RESULTS_V0.1/ST_PRIMARY_36_CELL_SUMMARY_V0.1.csv": "5e9873d830d8f08d754be2c2b507c3c5631242a9043643ad9f9ce3bf0d349f0f",
}
FIXED = {
    "ST-01_DONCHIAN_BREAKOUT-BNBUSDT-4H",
    "ST-01_DONCHIAN_BREAKOUT-DOGEUSDT-4H",
    "ST-01_DONCHIAN_BREAKOUT-SOLUSDT-4H",
    "ST-01_DONCHIAN_BREAKOUT-XRPUSDT-4H",
    "ST-02_EMA_PULLBACK-SOLUSDT-4H",
    "ST-02_EMA_PULLBACK-DOGEUSDT-4H",
    "ST-03_EXTREME_MEAN_REVERSION-DOGEUSDT-4H",
}

def sha_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def sha_bytes(b): return hashlib.sha256(b).hexdigest()

def fail(msg):
    print(json.dumps({"status":"FAIL_CLOSED","reason":msg},indent=2))
    sys.exit(2)

def main():
    ap=argparse.ArgumentParser(description="Authority-only preflight. Does not read protected market data.")
    ap.add_argument('--package-zip',required=True)
    ap.add_argument('--results-zip',required=True)
    a=ap.parse_args()
    if sha_file(a.package_zip)!=PKG_SHA: fail('package_zip_sha256_mismatch')
    if sha_file(a.results_zip)!=RES_SHA: fail('results_zip_sha256_mismatch')

    with zipfile.ZipFile(a.package_zip) as z:
        for name,exp in PKG_INTERNAL.items():
            if name not in z.namelist(): fail('missing_package_member:'+name)
            if sha_bytes(z.read(name))!=exp: fail('package_member_sha256_mismatch:'+name)

    with zipfile.ZipFile(a.results_zip) as z:
        for name,exp in RES_INTERNAL.items():
            if name not in z.namelist(): fail('missing_results_member:'+name)
            if sha_bytes(z.read(name))!=exp: fail('results_member_sha256_mismatch:'+name)
        close=json.loads(z.read('SIMPLE_TRADING_LAB_RESULTS_V0.1/ST_CLOSEOUT_V0.1.json'))
        if close.get('primary_cells')!=36 or close.get('survivor_count')!=0: fail('historical_closeout_identity_mismatch')
        if close.get('2025_opened') is not False or close.get('2026_opened') is not False: fail('historical_temporal_firewall_mismatch')

        sb=z.read('SIMPLE_TRADING_LAB_RESULTS_V0.1/ST_PRIMARY_36_CELL_SUMMARY_V0.1.csv')
        summary=list(csv.DictReader(io.StringIO(sb.decode('utf-8-sig'))))
        if len(summary)!=36: fail('summary_not_36_cells')
        summary_by={r['cell_id']:r for r in summary}
        if not FIXED.issubset(summary_by): fail('fixed_cell_missing_from_summary')

        eb=z.read('SIMPLE_TRADING_LAB_RESULTS_V0.1/ST_EVENTS_V0.1.csv.gz')
        counts={}; sums10={}; sums14={}; wins={}; total=0
        with gzip.GzipFile(fileobj=io.BytesIO(eb)) as gz:
            txt=io.TextIOWrapper(gz,encoding='utf-8-sig',newline='')
            for r in csv.DictReader(txt):
                cid=r['cell_id']; total+=1
                counts[cid]=counts.get(cid,0)+1
                v10=float(r['net10_bps']); v14=float(r['net14_bps'])
                sums10[cid]=sums10.get(cid,0.0)+v10
                sums14[cid]=sums14.get(cid,0.0)+v14
                wins[cid]=wins.get(cid,0)+(1 if v10>0 else 0)
        if total!=32243: fail('historical_event_count_mismatch')
        for cid,row in summary_by.items():
            n=counts.get(cid,0)
            if n!=int(row['n']): fail('n_mismatch:'+cid)
            if n:
                m10=sums10[cid]/n; m14=sums14[cid]/n; wr=wins[cid]/n
                if abs(m10-float(row['net10_mean_bps']))>1e-8: fail('net10_mean_mismatch:'+cid)
                if abs(m14-float(row['net14_mean_bps']))>1e-8: fail('net14_mean_mismatch:'+cid)
                if abs(wr-float(row['win_rate_net10']))>1e-8: fail('win_rate_mismatch:'+cid)

    print(json.dumps({
        "status":"AUTHORITY_PREFLIGHT_PASS",
        "package_sha256":PKG_SHA,
        "results_sha256":RES_SHA,
        "historical_cells_verified":36,
        "historical_events_verified":32243,
        "fixed_cells_verified":7,
        "protected_2025_opened":False,
        "protected_2026_opened":False,
        "market_data_read":False,
        "live_trading_authorized":False
    },indent=2))

if __name__=='__main__': main()
