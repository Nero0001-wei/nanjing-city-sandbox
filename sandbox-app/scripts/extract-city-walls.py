"""Extract mapped standing Ming city-wall fabric, keeping source gaps.
Historic tags and barrier tags require corroboration from the review file. Coordinates
come from the cached OSM snapshot; model dimensions are miniature-scale hints.
"""
from pathlib import Path
import xml.etree.ElementTree as ET
import json, math
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
from shapely import make_valid
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT.parent/'output/layout-v2/sources'
review=json.loads((ROOT/'data/city-wall-review.json').read_text())
nodes={};node_tags={};ways={};relations={}
for path in sorted(SOURCE.glob('area-*.osm')):
    if path.stat().st_size<1000: continue
    for e in ET.parse(path).getroot():
        id=e.get('id');tags={t.get('k'):t.get('v') for t in e.findall('tag')}
        if e.tag=='node':nodes[id]=(float(e.get('lon')),float(e.get('lat')));node_tags[id]=tags
        elif e.tag=='way':ways[id]={'nodes':[n.get('ref') for n in e.findall('nd')],'tags':tags}
        elif e.tag=='relation':relations[id]={'members':[(m.get('type'),m.get('ref'),m.get('role')) for m in e.findall('member')],'tags':tags}
def projected(p):
    lon,lat=p
    return [round(((lon+180)/360*4096-3398)*256,6),round(((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*4096-1661)*256,6)]
def coords(refs):return [projected(nodes[n]) for n in refs] if all(n in nodes for n in refs) else None
def parts(g,kind):
    if g.is_empty:return []
    if g.geom_type==kind:return [g]
    return [p for child in getattr(g,'geoms',[]) for p in parts(child,kind)]
def encode(g):return {'outer':[list(p) for p in list(g.exterior.coords)[:-1]],'holes':[[list(p) for p in list(h.coords)[:-1]] for h in g.interiors]}
def stitch(ids):
    remaining=[ways[id]['nodes'][:] for id in ids if id in ways];rings=[]
    if len(remaining)!=len(ids):return []
    while remaining:
        current=remaining.pop(0)
        while current[0]!=current[-1]:
            for i,part in enumerate(remaining):
                if part[0]==current[-1]:current+=part[1:];remaining.pop(i);break
                if part[-1]==current[-1]:current+=part[-2::-1];remaining.pop(i);break
            else:return []
        ps=coords(current)
        if ps:rings.append(ps)
    return rings
frame=box(30,170,690,690)
features=[];surfaces=[];consumed=set();excluded=[]
for id,r in relations.items():
    t=r['tags']
    if t.get('barrier')!='city_wall' or t.get('type')!='multipolygon':continue
    outerids=[ref for kind,ref,role in r['members'] if kind=='way' and role in ['outer','']]
    innerids=[ref for kind,ref,role in r['members'] if kind=='way' and role=='inner']
    outers=stitch(outerids);inners=stitch(innerids)
    if not outers:continue
    for ring in outers:
        p=Polygon(ring,[h for h in inners if Polygon(ring).covers(Point(h[0]))])
        if not p.is_valid:p=make_valid(p)
        for g in parts(p.intersection(frame),'Polygon'):
            if g.area<.05:continue
            surfaces.append(g);features.append({'id':'relation/'+id,'kind':'footprint','name':t.get('name','南京明城墙'),'source_tags':t,'source':'https://www.openstreetmap.org/relation/'+id,'height_m':float(t.get('height',20)),'height_source':'osm_height' if t.get('height') else 'estimated',**encode(g)})
    consumed.update(outerids+innerids);excluded.append('relation/'+id)
for id,w in ways.items():
    t=w['tags'];refs=w['nodes']
    if id in consumed or id in {r['way'] for r in review['excluded_traces']} or t.get('barrier')!='city_wall':continue
    ps=coords(refs)
    if not ps or len(ps)<2 or refs[0]==refs[-1]:continue
    for line in parts(LineString(ps).intersection(frame),'LineString'):
        if line.length<.1:continue
        width_m=float(t.get('width',12));width=max(.9,min(1.5,width_m/32.4*1.8))
        features.append({'id':'way/'+id,'kind':'line','name':t.get('name','南京明城墙'),'source_tags':t,'source':'https://www.openstreetmap.org/way/'+id,'source_px':[list(p) for p in line.coords],'height_m':float(t.get('height',20)),'height_source':'osm_height' if t.get('height') else 'estimated','width':width,'source_node_ids':refs})
# A historic tag does not mean demolished. Admit only independently reviewed
# standing sections, retaining their original tags and the supporting reference.
for item in review['standing_additions']:
    id=item['way'];w=ways[id];refs=w['nodes']
    if item.get('end_node'):refs=refs[:refs.index(item['end_node'])+1]
    ps=coords(refs)
    assert ps, f'Incomplete reviewed wall {id}'
    features.append({'id':'way/'+id,'kind':'line','name':item['name'],'source_tags':w['tags'],'source':'https://www.openstreetmap.org/way/'+id,'source_px':ps,'source_node_ids':refs,'height_m':20,'height_source':'estimated','width':.9,'review':{'status':'verified_standing','reference':review['references'][item['evidence']]}})
# Closed mapped wall outlines duplicate the centre-lines around Xuanwu Lake
# and Dinghuai Gate. Keep them as source evidence but do not render twice.
duplicate_outlines=[]
for id,w in ways.items():
    if w['tags'].get('barrier')=='city_wall' and w['nodes'][0]==w['nodes'][-1]:
        duplicate_outlines.append('way/'+id);excluded.append('way/'+id)
# Modern gateways within the wall are shown as current gateways, not claimed
# to be original Ming-period gate towers. Zhonghua Gate keeps its existing asset.
gate_defs={'940335843':('玄武门',3),'1061610836':('解放门',1),'859591128':('中山门',3),'995772006':('挹江门',3),'461035550':('仪凤门',3)}
gate_defs.update({d['way']:(d['name'],d['arches']) for d in review['additional_gates'] if 'way' in d})
gates=[]
for id,(name,arches) in gate_defs.items():
    w=ways[id];ps=coords(w['nodes']);g=Polygon(ps);rect=list(g.minimum_rotated_rectangle.exterior.coords)
    i=max(range(4),key=lambda i:math.dist(rect[i],rect[i+1]));a,b=rect[i],rect[i+1];p=g.centroid
    gates.append({'id':'way/'+id,'name':name,'p':[p.x,p.y],'angle':math.atan2(b[1]-a[1],b[0]-a[0]),'width':max(math.dist(a,b),4.3 if arches==3 else 2.3),'depth':max(.95,min(1.8,math.dist(rect[(i+1)%4],rect[(i+2)%4]))),'arches':arches,'height_m':20,'source':'https://www.openstreetmap.org/way/'+id,'source_tags':w['tags'],**encode(g)})
    excluded.append('way/'+id)
for d in review['additional_gates']:
    if 'way' in d:continue
    p=projected(nodes[d['node']]) if 'node' in d else d['p']
    id='node/'+d['node'] if 'node' in d else 'review/'+d['name']
    gates.append({**d,'id':id,'p':p,'source':'https://www.openstreetmap.org/'+id if 'node' in d else 'https://www.openstreetmap.org/relation/20427375' if d['name']=='长干门' else 'https://www.openstreetmap.org/way/134497186','source_tags':node_tags[d['node']] if 'node' in d else {},'height_m':20,'reference':review['references'][d['evidence']]})
excluded+=['way/1061607219','relation/11308636']
city=json.loads((ROOT/'public/data/nanjing.json').read_text())
# Fit actual displayed road widths through mapped gateways. These opening
# dimensions are visual clearance adjustments, not facade measurements.
for g in gates:
    p=g['p'];a=g['angle'];half=g['width']/2
    axis=LineString([[p[0]-math.cos(a)*half,p[1]-math.sin(a)*half],[p[0]+math.cos(a)*half,p[1]+math.sin(a)*half]])
    pitch=g['width']/(g['arches']+.5);slot=g['width']/(g['arches']*1.45+.6)
    openings=[{'center':(i-(g['arches']-1)/2)*pitch,'width':slot} for i in range(g['arches'])]
    for road in city['roads']:
        if road['kind']=='tunnel':continue
        line=LineString(road['source_px'])
        cross=axis.intersection(line)
        if cross.geom_type!='Point':continue
        center=(cross.x-p[0])*math.cos(a)+(cross.y-p[1])*math.sin(a)
        spans=parts(axis.intersection(line.buffer(.72)),'LineString')
        if not spans:continue
        reach=max(span.length for span in spans)
        nearest=min(openings,key=lambda o:abs(o['center']-center))
        nearest.update(center=center,width=max(slot,reach+.14))
    for i in range(1,len(openings)):
        prev=openings[i-1];openings[i]['center']=max(openings[i]['center'],prev['center']+(prev['width']+openings[i]['width'])/2+.26)
    g['width']=max(g['width'],2*(max(abs(o['center'])+o['width']/2 for o in openings)+.3))
    g['openings']=openings
# The original Zhonghua landmark is deliberately oversized. Leave room for it.
zhonghua=next(l['source_px'] for l in city['landmarks'] if l['id']=='zhonghua')
zhonghua_reserve=Point(zhonghua).buffer(5.8)
gate_masks=[]
for g in gates:
    p=g['p'];a=g['angle'];w=g['width']/2;d=g['depth']/2+.25
    ring=[[p[0]+x*math.cos(a)-y*math.sin(a),p[1]+x*math.sin(a)+y*math.cos(a)] for x,y in [(-w,-d),(w,-d),(w,d),(-w,d)]]
    g['display_outer']=ring
    # Slight overlap prevents a hairline break at the gate/wall junction.
    gate_masks.append(Polygon(ring).buffer(-.18))
portal_mask=unary_union([zhonghua_reserve]+gate_masks)
# Roads alongside walls must not erase entire wall sections. Reduce only the
# display thickness locally; actual road crossings are handled by the gates.
road_lines=unary_union([LineString(r['source_px']) for r in city['roads'] if r['kind']!='tunnel'])
display=[]
for feature in features:
    h=max(.95,min(1.6,feature['height_m']/32.4*.6*3))
    if feature['kind']=='line':
        line=LineString(feature['source_px'])
        for part in parts(line.difference(portal_mask),'LineString'):
            if part.length>.25:
                points=[]
                for a,b in zip(part.coords, list(part.coords)[1:]):
                    steps=max(1,math.ceil(math.dist(a,b)/.4))
                    points.extend([[a[k]+(b[k]-a[k])*i/steps for k in [0,1]] for i in range(steps)])
                points.append(list(part.coords[-1]))
                widths=[min(feature['width'],max(.08,2*(road_lines.distance(Point(p))-.04))) for p in points]
                display.append({'source_id':feature['id'],'kind':'line','source_px':points,'width':feature['width'],'widths':widths,'height':h,'name':feature['name']})
    else:
        g=Polygon(feature['outer'],feature['holes']).buffer(.28,join_style=2).difference(portal_mask).difference(road_lines.buffer(.04))
        for part in parts(g,'Polygon'):
            if part.area>.08:display.append({'source_id':feature['id'],'kind':'footprint','height':h,'name':feature['name'],**encode(part)})
result={'source':'OpenStreetMap cached API snapshot 2026-10-29, with evidence-reviewed standing sections and gateways','attribution':'© OpenStreetMap contributors, ODbL 1.0',
 'references':list(review['references'].values()),'connectivity_review':review['decisions'],
 'note':'Source tags alone do not determine standing fabric. Reviewed existing walls and reconstructed gateways remain connected. No blanket road-buffer cuts; traffic passes through explicit gate openings. Historical gaps and unresolved alignments are not automatically bridged. Model dimensions are stylized, not surveyed.',
 'features':features,'display':display,'gates':gates,'excluded_building_ids':excluded,
 'audit':{'source_features':len(features),'display_parts':len(display),'gates':len(gates),'omitted_duplicate_outline_ids':duplicate_outlines,'reviewed_standing_additions':review['standing_additions'],'reviewed_excluded_traces':review['excluded_traces'],'blanket_road_cuts':False,'historic_only_paths_omitted':sum(w['tags'].get('historic')=='citywalls' and w['tags'].get('barrier')!='city_wall' for w in ways.values())-len(review['standing_additions'])}}
(ROOT/'public/data/city-walls.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')))
print(json.dumps(result['audit'],ensure_ascii=False,indent=2))
print('Source line length px',sum(LineString(f['source_px']).length for f in features if f['kind']=='line'),'footprint areas',[round(g.area,2) for g in surfaces])
