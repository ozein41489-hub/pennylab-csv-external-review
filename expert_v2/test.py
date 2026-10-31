"""Reproducible bounded-memory CSV benchmark. Internal assessment only."""
import csv, tempfile, pathlib, importlib.util, tracemalloc, random, json, time
p=pathlib.Path(__file__).parent
spec=importlib.util.spec_from_file_location('candidate',p/'engine.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
results=[]
def case(name,fn):
    try:details=fn();results.append({'name':name,'pass':True,'detail':details})
    except Exception as e:results.append({'name':name,'pass':False,'error':str(e)})
def files(a,b):
    td=tempfile.TemporaryDirectory(); root=pathlib.Path(td.name);lp=root/'l.csv';rp=root/'r.csv';op=root/'o.csv'
    lp.write_text(a,encoding='utf-8');rp.write_text(b,encoding='utf-8');return td,lp,rp,op
def run(a,b,key='id',chunk_size=3):
    td,l,r,o=files(a,b)
    try:
        m.merge_csvs(l,r,key,o,chunk_size=chunk_size)
        with o.open(newline='',encoding='utf-8') as f:return list(csv.reader(f))
    finally:td.cleanup()
def assert_eq(actual,expected):assert actual==expected,(actual,expected)
def t1():assert_eq(run('id,n\n1,A\n2,B\n','id,v\n2,X\n1,Y\n'),[['id','n','v'],['1','A','Y'],['2','B','X']])
def t2():assert_eq(run('id,a\n4,L1\n4,L2\n','id,b\n4,R1\n4,R2\n'),[['id','a','b'],['4','L1','R1'],['4','L1','R2'],['4','L2','R1'],['4','L2','R2']])
def t3():assert_eq(run('id,a\n,A\n1,B\n','id,b\n,C\n1,D\n'),[['id','a','b'],['1','B','D']])
def t4():assert_eq(run('id,a,a_right\n1,λ,ξ\n','id,a\n1,東京\n'),[['id','a','a_right','a_right_right'],['1','λ','ξ','東京']])
def t5():assert_eq(run('id,a\n1,"hi, there"\n','id,b\n1,"""quoted"""\n'),[['id','a','b'],['1','hi, there','"quoted"']])
def t6():
    try:run('id,a\n1,X\n','bad,b\n1,Y\n')
    except ValueError:return
    raise AssertionError('invalid schema accepted')
def t7():
    td,l,r,o=files('id,a\n1,X\n2\n','id,b\n1,Y\n');o.write_text('ORIGINAL')
    try:
        try:m.merge_csvs(l,r,'id',o)
        except ValueError:pass
        else:raise AssertionError('ragged row accepted')
        assert_eq(o.read_text(),'ORIGINAL')
    finally:td.cleanup()
def t8():
    random.seed(410);keys=[str(random.randrange(19)) for _ in range(170)]
    left='id,a\n'+''.join(f'{k},L{i}\n' for i,k in enumerate(keys[:70]))
    right='id,b\n'+''.join(f'{k},R{i}\n' for i,k in enumerate(keys[70:]))
    actual=run(left,right,chunk_size=7)
    expected=[['id','a','b']]+[[k,'L'+str(i),'R'+str(j)] for i,k in enumerate(keys[:70]) for j,v in enumerate(keys[70:]) if v==k]
    assert_eq(actual,expected)
def t9():
    td,l,r,o=files('id,a\n1,X\n','id,b\n1,Y\n')
    try:
        try:m.merge_csvs(l,r,'id',o,chunk_size=0)
        except ValueError:return
        raise AssertionError('invalid chunk size accepted')
    finally:td.cleanup()
def t10():
    n=100000
    with tempfile.TemporaryDirectory() as td:
        root=pathlib.Path(td);l=root/'l.csv';r=root/'r.csv';o=root/'o.csv'
        for file,col in ((l,'L'),(r,'R')):
            with file.open('w',newline='',encoding='utf-8') as f:
                w=csv.writer(f);w.writerow(['id','v']);w.writerows((i,col) for i in range(n))
        tracemalloc.start();start=time.perf_counter()
        m.merge_csvs(l,r,'id',o,chunk_size=2000)
        elapsed=time.perf_counter()-start;_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        with o.open(newline='',encoding='utf-8') as f:count=sum(1 for _ in csv.reader(f))-1
        assert count==n,count
        assert peak<85*1024*1024,peak
        assert elapsed<180,elapsed
        return {'rows':count,'seconds':round(elapsed,2),'traced_peak_mb':round(peak/1048576,2)}
for name,fn in [('stable join',t1),('duplicate key many-to-many',t2),('empty-key safety',t3),('Unicode column collision',t4),('quoted field parsing',t5),('invalid header rejection',t6),('atomic failure rollback',t7),('seeded randomized oracle',t8),('invalid chunk configuration',t9),('100k bounded-memory benchmark',t10)]:case(name,fn)
result={'assessment':'PennyLab expert CSV engineering v2','classification':'Internal assistant-authored benchmark; not official platform credential','score':10*sum(x['pass'] for x in results),'possible':100,'tests':results}
(p/'report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
