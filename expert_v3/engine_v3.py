"""PennyLab expert external-sort streaming CSV join, standard library only."""
import csv, sqlite3, os, tempfile
from pathlib import Path

def merge_csvs(left_path, right_path, key_col, output_path, *, chunk_size=5000):
    if chunk_size < 1: raise ValueError('chunk_size must be positive')
    out=Path(output_path)
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='pennylab_',dir=str(out.parent)) as temp:
        db=sqlite3.connect(str(Path(temp)/'index.db'))
        try:
            db.execute('CREATE TABLE rhs (k TEXT NOT NULL, payload TEXT NOT NULL)')
            with open(right_path,encoding='utf-8-sig',newline='') as f:
                reader=csv.reader(f,strict=True); rh=next(reader,None)
                if not rh or key_col not in rh or len(rh)!=len(set(rh)): raise ValueError('invalid right header')
                ki=rh.index(key_col)
                batch=[]
                for row in reader:
                    if len(row)!=len(rh):raise ValueError('invalid right row')
                    if row[ki]!='':batch.append((row[ki],repr(row)))
                    if len(batch)>=chunk_size:db.executemany('INSERT INTO rhs VALUES (?,?)',batch);batch=[]
                if batch:db.executemany('INSERT INTO rhs VALUES (?,?)',batch)
            db.execute('CREATE INDEX rhs_key ON rhs(k)')
            with open(left_path,encoding='utf-8-sig',newline='') as f:
                reader=csv.reader(f,strict=True); lh=next(reader,None)
                if not lh or key_col not in lh or len(lh)!=len(set(lh)):raise ValueError('invalid left header')
                li=lh.index(key_col)
                names=lh[:]; right_idx=[]
                for i,name in enumerate(rh):
                    if i==ki:continue
                    new=name
                    while new in names:new+='_right'
                    names.append(new);right_idx.append(i)
                staged=Path(temp)/'output.csv'
                with open(staged,'w',encoding='utf-8',newline='') as target:
                    w=csv.writer(target,lineterminator='\n');w.writerow(names)
                    for row in reader:
                        if len(row)!=len(lh):raise ValueError('invalid left row')
                        if row[li]=='':continue
                        for (packed,) in db.execute('SELECT payload FROM rhs WHERE k=? ORDER BY rowid',(row[li],)):
                            import ast
                            rr=ast.literal_eval(packed)
                            w.writerow(row+[rr[i] for i in right_idx])
            os.replace(staged,out)
        finally:db.close()
