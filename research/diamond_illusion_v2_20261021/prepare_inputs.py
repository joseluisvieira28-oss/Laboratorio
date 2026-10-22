from pathlib import Path
import csv,json,hashlib,zipfile,xml.etree.ElementTree as ET,datetime,statistics,shutil
P=Path(__file__).parent;ROOT=P.parents[1];D=P/'data';D.mkdir(exist_ok=True)
A=ROOT/'audit_quant_20261021';C=ROOT/'work/final_mexc_private/certified'
ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def readxls(p):
 with zipfile.ZipFile(p) as z:
  ss=[]
  if 'xl/sharedStrings.xml' in z.namelist():ss=[''.join(t.itertext()) for t in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',ns)]
  out=[]
  for row in ET.fromstring(z.read('xl/worksheets/sheet1.xml')).findall('.//m:sheetData/m:row',ns):
   a=[]
   for cell in row.findall('m:c',ns):
    ref=cell.get('r');letters=''.join(x for x in ref if x.isalpha());col=0
    for x in letters:col=col*26+ord(x)-64
    while len(a)<col:a.append('')
    v=cell.find('m:v',ns);inline=cell.find('m:is',ns);tx=v.text if v is not None else ''.join(inline.itertext()) if inline is not None else ''
    a[col-1]=ss[int(tx)] if cell.get('t')=='s' else tx
   out.append(a)
  return out
workbooks=json.loads((ROOT/'work/final_mexc_private/official_workbooks.json').read_text(encoding='utf-8-sig'));actual={};sources=[]
for key in ['Trade History','Position History','Capital Flow']:
 f=C/'originals'/workbooks[key]['file'];h=hashlib.sha256(f.read_bytes()).hexdigest();assert h==workbooks[key]['sha256'];rows=readxls(f);assert rows==workbooks[key]['sheets']['Sheet1'];actual[key]=rows;sources.append({'kind':key,'file':f.name,'sha256':h,'rows':len(rows)-1})
positions=[r for r in actual['Position History'][1:] if r[1]=='BTCUSDT' and '2026-09-26'<=r[2]<'2026-10-03'];assert len(positions)==6
out=[]
for i,r in enumerate(sorted(positions,key=lambda r:r[2])):
 en,ex=r[2],r[3];fills=[f for f in actual['Trade History'][1:] if f[2]=='BTCUSDT' and en<=f[1]<=ex];flows=[f for f in actual['Capital Flow'][1:] if f[2]=='BTCUSDT' and en<=f[1]<=ex];assert len(fills)==2
 fees=sum(float(f[9]) for f in fills);gross=sum(float(f[6]) for f in flows if f[4]=='CLOSE_POSITION');funding=sum(float(f[6]) for f in flows if f[4]=='FUNDING');net=float(r[10].replace('USDT',''));assert abs(gross-fees+funding-net)<1e-8
 entry=next(f for f in fills if f[1]==en);exit=next(f for f in fills if f[1]==ex);N=float(entry[7]);assert all(f[11]=='Taker' for f in fills);assert all(abs(float(f[9])/float(f[7])-0.0008)<1e-10 for f in fills)
 out.append({'anonymous_trade':i+1,'symbol':'BTCUSDT','side':r[7],'gross_bps':gross/N*10000,'entry_fee_bps':float(entry[9])/N*10000,'exit_fee_bps_on_exit_notional':float(exit[9])/float(exit[7])*10000,'total_fees_bps_on_entry':fees/N*10000,'funding_credit_bps':funding/N*10000,'net_bps':net/N*10000,'gross_usdt':gross,'fees_usdt':fees,'funding_usdt':funding,'net_usdt':net,'entry_notional_private_omitted':True,'execution_fork_not_parent_OOS':True})
agg={}
for r in actual['Trade History'][1:]:
 if len(r)<12 or r[2]!='BTCUSDT':continue
 N=float(r[7]);fee=float(r[9]);key=r[11]
 if N<=0:continue
 v=agg.setdefault(key,{'n':0,'fee':0,'notional':0,'rates':[]});v['n']+=1;v['fee']+=fee;v['notional']+=N;v['rates'].append(fee/N*10000)
agg={k:{'fills':v['n'],'weighted_fee_bps':v['fee']/v['notional']*10000,'min_fee_bps':min(v['rates']),'max_fee_bps':max(v['rates'])} for k,v in agg.items()}
recon=json.loads((C/'reconciliation.json').read_text(encoding='utf-8-sig'));assert len(recon['entries'])==6;assert abs(sum(float(x['net_pnl_usdt']) for x in recon['entries'])-sum(x['net_usdt'] for x in out))<1e-8
res={'evidence_class':'actual observed 2026 fees and cashflows; not contemporaneous 2025 cost history','sources':sources,'workbook_bytes_and_parsed_rows_verified':True,'six_execution_fork_trades':out,'summary':{'n':6,'gross_usdt':sum(x['gross_usdt'] for x in out),'fees_usdt':sum(x['fees_usdt'] for x in out),'funding_credit_usdt':sum(x['funding_usdt'] for x in out),'net_usdt':sum(x['net_usdt'] for x in out),'mean_net_bps_equal_entry_notional':statistics.mean(x['net_bps'] for x in out),'mean_funding_credit_bps':statistics.mean(x['funding_credit_bps'] for x in out),'actual_taker_bps_per_side':8.0,'maker_bps_in_receipt_quote':6.0,'maker_quote_is_not_fill':True},'all_BTC_export_fill_fee_statistics':agg,'financial_reconciliation_pass':True,'operational_prior_gate':recon['operational_verdict'],'raw_private_data_published':False,'no_account_api_access':True}
(D/'observed_costs.json').write_text(json.dumps(res,indent=2))
shutil.copyfile(A/'etf_oos/oos_2025_observations.csv',D/'etf_oos_2025.csv');shutil.copyfile(next((A/'10504812106').rglob('*.csv')),D/'options_v21_oos_2025.csv');shutil.copyfile(A/'results/metrics.json',D/'prior_metrics.json')
F=D/'authorities';F.mkdir(exist_ok=True)
for f in (A/'authorities').glob('*'):
 if any(x in f.name.lower() for x in ['oos','forward_shadow','options_spotperp']):shutil.copyfile(f,F/f.name)
for f in [ROOT/'Laboratorio-mexc-final/crypto_edge_radar/OPTIONS_SPOTPERP_001_V21_LIVE_SHADOW_FREEZE_V0.1.json',ROOT/'Laboratorio-mexc-final/crypto_edge_radar/authorities/OPTIONS_SPOTPERP_001_V21_PROSPECTIVE_SHADOW_FREEZE_V0.1.md']:
 shutil.copyfile(f,F/f.name)
print('COSTS',json.dumps(res['summary']));print('BTC_FILL_RATES',agg)


