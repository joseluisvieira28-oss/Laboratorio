#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from huggingface_hub import hf_hub_download
import pyarrow.parquet as pq

REPO_ID='Slinky21/Pumpfun_Memecoin_Corpus'
FILES=['migrations.parquet','tokens.parquet','snapshots.parquet']

def main():
    root=Path('pmd_v09_schema'); root.mkdir(parents=True,exist_ok=True)
    out={'lab':'PMD-001','stage':'V09_PREMIGRATION_SCHEMA_PROBE','outcomes_opened':False,'files':{}}
    for f in FILES:
        p=Path(hf_hub_download(repo_id=REPO_ID,repo_type='dataset',filename=f,local_dir=str(root)))
        pf=pq.ParquetFile(p)
        md=pf.metadata
        schema=pf.schema_arrow
        out['files'][f]={
            'rows':md.num_rows,
            'columns':[{'name':field.name,'type':str(field.type)} for field in schema],
        }
    Path('pmd_v09_schema_probe.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__': main()
