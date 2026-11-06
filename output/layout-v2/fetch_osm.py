from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,xml.etree.ElementTree as ET,json,time
P=Path(__file__).parent/'sources';P.mkdir(exist_ok=True)
boxes=[]
for i in range(3):
 for j in range(4):
  if (i,j) in [(1,1),(2,3)]:
   for k in range(2):
    if (i,j,k)==(1,1,1):
     for h in range(2): boxes.append((f'{i}-{j}-{k}-{h}',(118.68+i*.06+k*.03,31.985+j*.035+h*.0175,118.68+i*.06+(k+1)*.03,31.985+j*.035+(h+1)*.0175)))
    else: boxes.append((f'{i}-{j}-{k}',(118.68+i*.06+k*.03,31.985+j*.035,118.68+i*.06+(k+1)*.03,31.985+(j+1)*.035)))
  else: boxes.append((f'{i}-{j}',(118.68+i*.06,31.985+j*.035,118.68+(i+1)*.06,31.985+(j+1)*.035)))
def fetch(item):
 name,bbox=item;p=P/f'area-{name}.osm'
 if p.exists() and p.stat().st_size>1000:return str(p)
 u='https://api.openstreetmap.org/api/0.6/map?bbox='+','.join(f'{n:.5f}' for n in bbox)
 r=subprocess.run(['curl','-sSL','--max-time','45','-A','NanjingSceneLayout/1.0 (one-time city layout study)',u,'-o',str(p),'-w','%{http_code}'],capture_output=True,text=True)
 print(name,r.stdout,p.stat().st_size if p.exists() else 0,flush=True)
 return str(p)
with ThreadPoolExecutor(max_workers=2) as pool: files=list(pool.map(fetch,boxes))
nodes={};ways={};failed=[]
for f in files:
 try:
  rt=ET.parse(f).getroot()
  if rt.tag!='osm':raise ValueError('not osm')
  for e in rt:
   if e.tag=='node':nodes[e.attrib['id']]=[float(e.attrib['lon']),float(e.attrib['lat'])]
   elif e.tag=='way':ways[e.attrib['id']]={'id':e.attrib['id'],'nodes':[n.attrib['ref'] for n in e.findall('nd')],'tags':{t.attrib['k']:t.attrib['v'] for t in e.findall('tag')}}
 except Exception as ex: failed.append(f)
features=[]
for w in ways.values():
 if w['tags'].get('highway') or w['tags'].get('waterway') or w['tags'].get('natural')=='water' or w['tags'].get('barrier')=='city_wall':
  if all(n in nodes for n in w['nodes']):features.append({'id':w['id'],'tags':w['tags'],'geometry':[nodes[n] for n in w['nodes']]})
(P/'osm-features.json').write_text(json.dumps({'source':'https://api.openstreetmap.org/api/0.6/map','bbox':[118.68,31.985,118.86,32.125],'failed':failed,'features':features},ensure_ascii=False))
print('FINISHED',len(nodes),'nodes',len(ways),'ways',len(features),'features','failed',failed,flush=True)
