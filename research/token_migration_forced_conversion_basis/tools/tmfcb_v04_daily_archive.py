"""Date-only listing of transition-month archive objects; never open files."""
import json
import urllib.parse
import xml.etree.ElementTree as ET
from tmfcb_v04_sources import fetch, OUT

WINDOWS = [('PLA','PDA','2024-02','2024-03'),('MATIC','POL','2024-09','2024-09'),
           ('GAL','G','2024-07','2024-07'),('MFT','HIFI','2023-01','2023-01'),
           ('KEEP','T','2022-02','2022-02'),('NU','T','2022-02','2022-02'),
           ('RNDR','RENDER','2024-07','2024-07'),('AGIX','FET','2024-07','2024-07'),
           ('OCEAN','FET','2024-07','2024-07')]

def dates(symbol,month):
    prefix=f'data/spot/daily/klines/{symbol}USDT/1m/{symbol}USDT-1m-{month}'
    url='https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?'+urllib.parse.urlencode(
        {'list-type':2,'prefix':prefix,'max-keys':1000})
    rec=fetch(url); raw=rec.pop('body',None)
    rec.update(url=url,dates=[],listing_complete=False)
    if raw:
        ns={'s':'http://s3.amazonaws.com/doc/2006-03-01/'}
        tree=ET.fromstring(raw)
        rec['listing_complete']=tree.findtext('s:IsTruncated',namespaces=ns)=='false'
        rec['dates']=[i.findtext('s:Key',namespaces=ns).rsplit('-1m-',1)[-1][:-4]
                      for i in tree.findall('s:Contents',ns)
                      if i.findtext('s:Key',namespaces=ns).endswith('.zip')]
    return rec

def main():
    rows=[]
    for old,new,om,nm in WINDOWS:
        a,b=dates(old,om),dates(new,nm)
        rows.append({'old':old,'new':new,'old_metadata':a,'new_metadata':b,
                     'same_day_object_names':sorted(set(a['dates'])&set(b['dates'])),
                     'limitation':'Same-day filenames do not prove intraday overlap, trades or nonempty observations.'})
    (OUT/'daily_archive_metadata.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    print(json.dumps([{'old':r['old'],'new':r['new'],'old_last':max(r['old_metadata']['dates'],default=None),
                       'new_first':min(r['new_metadata']['dates'],default=None),
                       'same_day_names':r['same_day_object_names']} for r in rows]))

if __name__=='__main__': main()
