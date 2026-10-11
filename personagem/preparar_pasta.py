"""Isola hardlinks antes de regenerar: uma boneca nunca altera outra."""
import os,pathlib,shutil
p=pathlib.Path(os.environ['BONECA_DIR'])
for f in p.rglob('*'):
 if f.is_file() and not f.is_symlink() and f.stat().st_nlink>1:
  tmp=f.with_name(f.name+'.isolado');shutil.copy2(f,tmp);os.replace(tmp,f)
t=p/'trabalho';t.mkdir(exist_ok=True);(t/'.gdignore').touch()
