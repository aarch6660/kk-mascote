"""Exporta a seleção adicional de gestos do diálogo cotidiano com fontes em leitura."""
import json
from extrair import HERE,DEFAULT_GAME,skeleton,load_bundle,ADV_BUNDLE,decode,identity
from glb import export_glb

def main():
 nodes,hashes=skeleton(DEFAULT_GAME)
 env=load_bundle(DEFAULT_GAME,ADV_BUNDLE)
 catalog=json.loads((HERE/'catalogo.json').read_text())
 selection=json.loads((HERE/'selecao.json').read_text())
 report=json.loads((HERE/'exportados/manifesto.json').read_text())
 extras = [('stand_ang_00','Stand_Ang_00'),('stand_sad_00','Stand_Sad_00')]
 for grupo,indices in [('Joy',[2,3,5,8]),('Oth',[2,4,5,6]),('Ang',[1,2]),('Sad',[1,2])]:
  extras += [(f'stand_{grupo.lower()}_{i:02d}',f'Stand_{grupo}_{i:02d}') for i in indices]
 for name,source in extras:
  obj=next(o for o in env.objects if o.type.name=='AnimationClip' and o.peek_name()==source)
  entry=next(c for c in catalog['clips'] if c['id']==identity(ADV_BUNDLE,obj.path_id))
  if entry['category_guess'].startswith('excluido'): raise ValueError('Clipe excluído: '+source)
  times,tracks,stats=decode(obj.read_typetree(),hashes)
  item=dict(name=name,source=source,bundle=ADV_BUNDLE,category='gesto_reacao',loop=False,description='Variação original de diálogo cotidiano; categoria pelo nome/índice nativo.')
  meta=dict(item,source_id=entry['id'],length=entry['length'],source_loop=entry['loop'],fps=30,coordinate_system='glTF RH Y-up, reflection X from Unity',decoder=stats)
  output=HERE/'exportados'/(name+'.glb');export_glb(output,nodes,times,tracks,meta)
  meta.update(glb=str(output.relative_to(HERE)),bytes=output.stat().st_size)
  selection=[x for x in selection if x['name']!=name]+[item]
  report=[x for x in report if x['name']!=name]+[meta]
  entry.update(selected=True,export=meta['glb'])
  print(name,'exportado',flush=True)
 for p,value in [(HERE/'selecao.json',selection),(HERE/'exportados/manifesto.json',report),(HERE/'catalogo.json',catalog)]:p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
