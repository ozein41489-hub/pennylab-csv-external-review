"""PennyLab independent holdout v3: tests not part of original candidate test.py.
Read-only evaluation of existing engine.py. Writes only temporary test fixtures and report.
"""
import csv,importlib.util,pathlib,tempfile,json,time,traceback,random
BASE=pathlib.Path(__file__).parent
s=importlib.util.spec_from_file_location("engine",BASE/"engine_v3.py");e=importlib.util.module_from_spec(s);s.loader.exec_module(e)
checks=[]
def run(name,fn):
 t=time.perf_counter()
 try:fn();checks.append({"name":name,"pass":True,"seconds":round(time.perf_counter()-t,3)})
 except Exception as ex:checks.append({"name":name,"pass":False,"seconds":round(time.perf_counter()-t,3),"reason":str(ex)[:400]})
def fixture(l,r,key="id",chunk=2,output="out.csv"):
 with tempfile.TemporaryDirectory() as folder:
  p=pathlib.Path(folder); (p/"left.csv").open("w",encoding="utf-8",newline="").write(l);(p/"right.csv").open("w",encoding="utf-8",newline="").write(r)
  o=p/output
  e.merge_csvs(str(p/"left.csv"),str(p/"right.csv"),key,str(o),chunk_size=chunk)
  with o.open(encoding="utf-8",newline="") as f:return list(csv.reader(f))
def t_custom_key():
 assert fixture("sku,L\nx,a\ny,b\n","sku,R\ny,2\nx,1\n",key="sku")==[["sku","L","R"],["x","a","1"],["y","b","2"]]
def t_multiline():
 assert fixture('id,comment\n1,"line1\nline2"\n','id,note\n1,"hello, world"\n')==[["id","comment","note"],["1","line1\nline2","hello, world"]]
def t_injection():
 payload="__import__('os').system('echo pwn')"
 assert fixture("id,L\n1,a\n","id,R\n1,"+payload+"\n")==[["id","L","R"],["1","a",payload]]
def t_existing_output_atomic():
 with tempfile.TemporaryDirectory() as folder:
  p=pathlib.Path(folder); l=p/"left.csv";r=p/"right.csv";o=p/"out.csv"
  l.write_text("id,x\n1,A\n2\n");r.write_text("id,y\n1,B\n");o.write_text("DO NOT CHANGE")
  try:e.merge_csvs(str(l),str(r),"id",str(o))
  except ValueError:pass
  else:raise AssertionError("Expected rejection for ragged row")
  assert o.read_text()=="DO NOT CHANGE"
def t_duplicate_headers():
 for left,right in [("id,id\n1,2\n","id,x\n1,b\n"),("id,x\n1,a\n","id,id\n1,2\n")]:
  try:fixture(left,right)
  except ValueError:continue
  raise AssertionError("Duplicate header accepted")
def t_special_keys():
 assert fixture('id,left\n0001,a\n1,b\n','id,right\n0001,A\n1,B\n')==[["id","left","right"],["0001","a","A"],["1","b","B"]]
def t_output_directory():
 assert fixture("id,x\n1,A\n","id,y\n1,B\n",output="nested/out.csv")==[["id","x","y"],["1","A","B"]]
def t_fuzz_reference():
 rng=random.Random(81271)
 for case in range(20):
  left=[(str(rng.randrange(12)),str(rng.randrange(100))) for _ in range(45)]
  right=[(str(rng.randrange(12)),str(rng.randrange(100))) for _ in range(30)]
  ls="id,a\n"+"".join(f"{a},{b}\n" for a,b in left)
  rs="id,b\n"+"".join(f"{a},{b}\n" for a,b in right)
  expected=[["id","a","b"]]+[[lk,lv,rv] for lk,lv in left for rk,rv in right if lk==rk]
  got=fixture(ls,rs,chunk=3)
  assert got==expected,f"fuzz case {case}"
def t_unmatched_scale():
 n=25000
 with tempfile.TemporaryDirectory() as folder:
  p=pathlib.Path(folder);l=p/"left.csv";r=p/"right.csv";o=p/"out.csv"
  with l.open("w",newline="") as f:
   w=csv.writer(f);w.writerow(["id","x"])
   for i in range(n):w.writerow([i,"a"])
  with r.open("w",newline="") as f:
   w=csv.writer(f);w.writerow(["id","y"])
   for i in range(n,2*n):w.writerow([i,"b"])
  e.merge_csvs(str(l),str(r),"id",str(o),chunk_size=257)
  with o.open(newline="") as f:assert sum(1 for _ in csv.reader(f))==1
tests=[("non-default join key",t_custom_key),("multiline quoted CSV",t_multiline),("literal evaluation injection string",t_injection),("existing output rollback",t_existing_output_atomic),("duplicate header rejection",t_duplicate_headers),("text keys preserve leading zeroes",t_special_keys),("missing output directory",t_output_directory),("seeded differential fuzz (20 cases)",t_fuzz_reference),("25k unmatched row scale",t_unmatched_scale)]
for name,func in tests:run(name,func)
report={"suite":"PennyLab external-to-candidate holdout v3","scope":"New assistant-authored tests; not independent third-party certification","total":len(checks),"passed":sum(c["pass"] for c in checks),"score":round(100*sum(c["pass"] for c in checks)/len(checks),1),"tests":checks}
(BASE/"holdout_v3_retest_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report,indent=2))
