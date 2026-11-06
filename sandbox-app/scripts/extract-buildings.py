"""Extract actual OSM footprints from the existing WGS84 map snapshot.
Building parts are not duplicated on top of their parent footprints.
This script never invents or relocates a footprint.
"""
from pathlib import Path
import xml.etree.ElementTree as ET
import math,json,re,collections

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT.parent/'output/layout-v2/sources'
nodes={};ways={};relations={};skipped=collections.Counter()
for path in sorted(SOURCE.glob('area-*.osm')):
    if path.stat().st_size<1000: continue
    for e in ET.parse(path).getroot():
        id=e.get('id')
        if e.tag=='node':nodes[id]=[float(e.get('lon')),float(e.get('lat'))]
        elif e.tag=='way':ways[id]={'nodes':[n.get('ref') for n in e.findall('nd')],'tags':{t.get('k'):t.get('v') for t in e.findall('tag')}}
        elif e.tag=='relation':relations[id]={'members':[(m.get('type'),m.get('ref'),m.get('role')) for m in e.findall('member')],'tags':{t.get('k'):t.get('v') for t in e.findall('tag')}}

def projected(p):
    lon,lat=p
    return [round(((lon+180)/360*4096-3398)*256,5),round(((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*4096-1661)*256,5)]
def ring(refs):
    if len(refs)<4 or refs[0]!=refs[-1] or any(n not in nodes for n in refs):return None
    result=[]
    for ref in refs[:-1]:
        p=projected(nodes[ref])
        if not result or p!=result[-1]:result.append(p)
    return result if len(result)>=3 else None
def area(poly):return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1])))/2
def inside(p,poly):
    x,y=p;v=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:v=not v
    return v
def number(s):
    if not s:return None
    match=re.fullmatch(r'\s*(\d+(?:\.\d+)?)\s*(m|metres|meters|ft|feet|\')?\s*',s)
    if not match:return None
    n=float(match[1]);return n*.3048 if match[2] in ['ft','feet',"'"] else n
def height(tags):
    direct=number(tags.get('height'))
    if direct is not None and 1<=direct<=600:return round(direct,2),'osm_height'
    levels=number(tags.get('building:levels'))
    if levels is not None and 0<levels<=120:
        per_floor=3.0 if tags.get('building') in ['apartments','residential','house','dormitory'] else 3.6
        return round(levels*per_floor,2),'levels_estimate'
    defaults={'apartments':24,'residential':18,'house':9,'detached':9,'dormitory':18,'office':30,'commercial':18,'retail':9,'school':12,'university':15,'hospital':21,'industrial':9,'warehouse':8,'train_station':15,'garages':3,'garage':3,'hut':3}
    return defaults.get(tags.get('building'),12),'type_estimate'

features=[]
def add(id,outer,holes,tags):
    if not outer:skipped['open_or_incomplete']+=1;return
    bbox=[min(p[0] for p in outer),min(p[1] for p in outer),max(p[0] for p in outer),max(p[1] for p in outer)]
    # Complete footprints only. Do not crop a building to create a fictitious outline.
    if bbox[0]<30 or bbox[1]<170 or bbox[2]>690 or bbox[3]>690:skipped['outside_view']+=1;return
    net=area(outer)-sum(area(h) for h in holes)
    if net<.04:skipped['small_or_degenerate']+=1;return
    h,origin=height(tags)
    features.append(dict(id=id,name=tags.get('name',''),building=tags.get('building','yes'),outer=outer,holes=holes,bbox=bbox,source_area=round(net,6),height_m=h,height_source=origin,source_tags={k:v for k,v in tags.items() if k in ['height','building:levels','min_height','building:min_level','building','name']},source='https://www.openstreetmap.org/'+id))

def stitch(ids):
    remaining=[]
    for id in ids:
        if id not in ways:return None
        remaining.append(ways[id]['nodes'][:])
    closed=[]
    while remaining:
        current=remaining.pop(0)
        while current[-1]!=current[0]:
            for i,part in enumerate(remaining):
                if part[0]==current[-1]:current+=part[1:];remaining.pop(i);break
                if part[-1]==current[-1]:current+=part[-2::-1];remaining.pop(i);break
            else:return None
        r=ring(current)
        if not r:return None
        closed.append(r)
    return closed

consumed=set()
for id,r in relations.items():
    tags=r['tags']
    if tags.get('type')!='multipolygon' or tags.get('building') in [None,'no','roof','construction','ruins']:continue
    ids=[ref for kind,ref,role in r['members'] if kind=='way' and role in ['outer','inner','']]
    outers=stitch([ref for kind,ref,role in r['members'] if kind=='way' and role in ['outer','']])
    inners=stitch([ref for kind,ref,role in r['members'] if kind=='way' and role=='inner'])
    if outers is None or inners is None:skipped['incomplete_relation']+=1;continue
    consumed.update(ids)
    for i,outer in enumerate(outers):
        add('relation/'+id,outer,[h for h in inners if inside(h[0],outer)],tags)

for id,w in ways.items():
    tags=w['tags']
    if id in consumed or tags.get('building') in [None,'no','roof','construction','ruins'] or tags.get('building:part') not in [None,'no']:continue
    add('way/'+id,ring(w['nodes']),[],tags)

out=ROOT/'data';out.mkdir(exist_ok=True)
result=dict(source='OpenStreetMap API snapshot 2026-10-29',coordinate_system='WGS84 / original z12 local projection',attribution='© OpenStreetMap contributors, ODbL 1.0',height_note='osm_height is an OSM height tag, not independent measurement. levels_estimate and type_estimate are estimates, not surveyed heights.',count=len(features),skipped=dict(skipped),height_counts=dict(collections.Counter(f['height_source'] for f in features)),features=features)
(out/'building-footprints.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')))
print(json.dumps({k:v for k,v in result.items() if k!='features'},ensure_ascii=False,indent=2))
