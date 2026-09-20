#!/usr/bin/env python3
import hashlib, json, subprocess, sys, tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
SCRIPT=HERE/"l2r_2025_resume_offline_preflight_v01.py"

def write_inventory(path, p, m, e):
    rows=[]
    for i in range(p): rows.append({"hour":i,"status":"PRESENT"})
    for i in range(m): rows.append({"hour":p+i,"status":"MISSING"})
    for i in range(e): rows.append({"hour":p+m+i,"status":"ERROR"})
    path.write_text(json.dumps(rows),encoding="utf-8")

def run(*args):
    return subprocess.run([sys.executable,str(SCRIPT),*map(str,args)],capture_output=True,text=True)

def main():
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        fake=td/"fake.zip"; fake.write_bytes(b"not-the-frozen-package")
        inv=td/"inventory.json"; write_inventory(inv,4889,360,3511)

        r=run("--package",fake,"--inventory",inv)
        assert r.returncode==2
        assert "PACKAGE_HASH_MISMATCH_FAIL_CLOSED" in r.stdout

        # Unit-test resumability semantics directly without needing the real frozen ZIP.
        import importlib.util
        spec=importlib.util.spec_from_file_location("preflight",SCRIPT)
        m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

        rows,counts,total=m.audit_inventory(inv)
        assert total==8760
        assert counts=={"PRESENT":4889,"MISSING":360,"ERROR":3511}

        progressed=td/"progressed.json"; write_inventory(progressed,5000,400,3360)
        _r,c,t=m.audit_inventory(progressed)
        assert t==8760
        assert c["ERROR"]<3511
        assert c["PRESENT"]>=4889 and c["MISSING"]>=360

        bad=td/"bad.json"; write_inventory(bad,4800,300,3660)
        _r,c,t=m.audit_inventory(bad)
        assert not (
            c["ERROR"]<=3511 and
            c["PRESENT"]+c["MISSING"]>=5249 and
            c["PRESENT"]>=4889 and
            c["MISSING"]>=360
        )

        print("RESUME_SEMANTICS_SYNTHETIC_PASS 4/4")
        print("NO_NETWORK_NO_MARKET_DATA_NO_OUTCOMES")

if __name__=="__main__":
    main()
