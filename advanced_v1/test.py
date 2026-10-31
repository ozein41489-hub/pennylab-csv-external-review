"""Independent functional benchmark for PennyLab_Advanced_CSV.py.
10 checks, 10 points each; author-created tests, not a platform certification.
"""
import csv, importlib.util, tempfile, pathlib, time, json, traceback
from concurrent.futures import ThreadPoolExecutor
spec=importlib.util.spec_from_file_location("candidate", pathlib.Path(__file__).with_name("PennyLab_Advanced_CSV.py"))
candidate=importlib.util.module_from_spec(spec); spec.loader.exec_module(candidate)
results=[]
def check(name,fn):
    try: fn(); results.append({"test":name,"passed":True,"points":10})
    except Exception as e: results.append({"test":name,"passed":False,"points":0,"error":repr(e)})
def run(a,b,key="id"):
    with tempfile.TemporaryDirectory() as td:
        p=pathlib.Path(td); lp=p/"l.csv";rp=p/"r.csv";op=p/"o.csv"
        lp.write_text(a,encoding="utf-8");rp.write_text(b,encoding="utf-8")
        candidate.merge_csvs(str(lp),str(rp),key,str(op))
        with op.open(encoding="utf-8",newline="") as f:return list(csv.reader(f))
def basic():
    assert run("id,name\n1,A\n2,B\n","id,age\n2,20\n1,10\n")==[["id","name","age"],["1","A","10"],["2","B","20"]]
def missing():
    assert run("id,name\n1,A\n","id,age\n2,20\n")==[["id","name","age"]]
def manytomany():
    assert run("id,v\n4,L1\n4,L2\n","id,w\n4,R1\n4,R2\n")==[["id","v","w"],["4","L1","R1"],["4","L1","R2"],["4","L2","R1"],["4","L2","R2"]]
def unicode():
    assert run("id,text\n1,東京\n","id,data\n1,éclair\n")==[["id","text","data"],["1","東京","éclair"]]
def quotes():
    assert run('id,name\n1,"Doe, Jane"\n','id,note\n1,"say ""hello"""\n')==[["id","name","note"],["1","Doe, Jane",'say "hello"']]
def collisions():
    assert run("id,x,x_right\n1,A,B\n","id,x\n1,C\n")==[["id","x","x_right","x_right_right"],["1","A","B","C"]]
def empties():
    assert run("id,x\n,A\n1,B\n","id,y\n,Z\n1,Y\n")==[["id","x","y"],["1","B","Y"]]
def badheader():
    try:run("uid,x\n1,A\n","id,y\n1,B\n")
    except ValueError:return
    raise AssertionError("missing key accepted")
def atomic():
    with tempfile.TemporaryDirectory() as td:
        p=pathlib.Path(td);l=p/"l.csv";r=p/"r.csv";o=p/"o.csv"
        l.write_text("id,x\n1,A\n2\n");r.write_text("id,y\n1,B\n");o.write_text("ORIGINAL")
        try:candidate.merge_csvs(str(l),str(r),"id",str(o))
        except ValueError:pass
        else:raise AssertionError("ragged CSV accepted")
        assert o.read_text()=="ORIGINAL"
def scale():
    n=100000
    with tempfile.TemporaryDirectory() as td:
        p=pathlib.Path(td);l=p/"l.csv";r=p/"r.csv";o=p/"o.csv"
        with l.open("w",newline="") as f:
            w=csv.writer(f);w.writerow(["id","value"])
            for i in range(n):w.writerow([i,"L"])
        with r.open("w",newline="") as f:
            w=csv.writer(f);w.writerow(["id","value"])
            for i in range(n):w.writerow([i,"R"])
        start=time.perf_counter()
        candidate.merge_csvs(str(l),str(r),"id",str(o))
        elapsed=time.perf_counter()-start
        with o.open(newline="") as f:
            lines=sum(1 for _ in csv.reader(f))
        assert lines==n+1,(lines,n)
        assert elapsed<30,elapsed
        return elapsed
tests=[("stable inner join",basic),("unmatched keys",missing),("many-to-many duplicate keys",manytomany),("Unicode UTF-8",unicode),("quoted CSV fields",quotes),("column collision naming",collisions),("empty join keys",empties),("missing key rejection",badheader),("atomic failure handling",atomic),("100k-row scalability",scale)]
for name,fn in tests:check(name,fn)
report={"assessment":"PennyLab Advanced Python and CSV Engineering v1","assessment_type":"internal assistant-authored test, not official pact0 or external certification","points_earned":sum(t["points"] for t in results),"points_possible":100,"passed":sum(t["passed"] for t in results),"total":len(results),"results":results}
out=pathlib.Path(__file__).with_name("PennyLab_Advanced_CSV_Report.json")
out.write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report,indent=2))
