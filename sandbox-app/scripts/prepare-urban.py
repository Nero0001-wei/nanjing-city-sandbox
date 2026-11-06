"""Build an artistic city background on the cached OSM street/land-use snapshot.
Roads, landmark anchors and the original white-building dataset are immutable.
Requires scripts/requirements-urban.txt; only this offline preparation needs Python.
"""
from pathlib import Path
import json, math, random, collections, subprocess, xml.etree.ElementTree as ET
from shapely.geometry import Polygon, LineString, Point, MultiPoint, box
from shapely.ops import unary_union
from shapely import affinity, make_valid
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / 'output/layout-v2/sources'
RNG = random.Random(2026102907)
load = lambda p: json.loads(p.read_text())
city = load(ROOT/'public/data/nanjing.json')
wall_data = load(ROOT/'public/data/city-walls.json')
wall_mask = unary_union([LineString(f['source_px']).buffer(f['width']/2+1.3) if f['kind']=='line' else Polygon(f['outer'],f['holes']).buffer(1.6) for f in wall_data['features']]+[Polygon(g.get('display_outer') or g['outer']).buffer(1.5) for g in wall_data['gates']])
buildings = load(ROOT/'public/data/buildings.json')['features']
raw = load(ROOT/'data/building-footprints.json')['features']
frame = box(34, 174, 686, 686)

def polys(g):
    if g.is_empty: return []
    if g.geom_type == 'Polygon': return [g]
    return [p for child in getattr(g, 'geoms', []) for p in polys(child)]
def poly(ring): return make_valid(Polygon(ring))
def projected(lon, lat):
    return (((lon+180)/360*4096-3398)*256, ((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*4096-1661)*256)
def encode(g):
    return {'outer': [[round(x,4),round(y,4)] for x,y in list(g.exterior.coords)[:-1]],
            'holes': [[[round(x,4),round(y,4)] for x,y in list(h.coords)[:-1]] for h in g.interiors]}
def local_rect(x,y,w,d,angle,origin):
    return affinity.rotate(box(x-w/2,y-d/2,x+w/2,y+d/2),angle,origin=origin)

# Complete OSM closed ways provide park/land-use hints. Incomplete multipolygons
# are deliberately omitted, never closed by guessing missing edges.
nodes, ways = {}, {}
for path in sorted(SOURCE.glob('area-*.osm')):
    if path.stat().st_size < 1000: continue
    for e in ET.parse(path).getroot():
        if e.tag == 'node': nodes[e.get('id')] = (float(e.get('lon')),float(e.get('lat')))
        elif e.tag == 'way':
            tags = {t.get('k'):t.get('v') for t in e.findall('tag')}
            if any(k in tags for k in ['landuse','leisure','amenity']):
                ways[e.get('id')] = ([n.get('ref') for n in e.findall('nd')],tags)
uses = []
for id,(refs,tags) in ways.items():
    if len(refs)<4 or refs[0]!=refs[-1] or any(n not in nodes for n in refs): continue
    g = poly([projected(*nodes[n]) for n in refs]).intersection(frame)
    if g.is_empty or g.area < 12: continue
    park = tags.get('leisure') in ['park','garden','nature_reserve'] or tags.get('landuse') in ['forest','grass','recreation_ground','cemetery']
    kind = 'park' if park else 'commercial' if tags.get('landuse') in ['commercial','retail','industrial'] else 'residential' if tags.get('landuse')=='residential' else 'campus' if tags.get('amenity') in ['school','university','college','hospital'] else None
    if kind: uses.extend((p,kind,'way/'+id) for p in polys(g))
use_geoms = [u[0] for u in uses]
use_index = STRtree(use_geoms)
parks = unary_union([g for g,k,_ in uses if k=='park'])
mountains = unary_union([poly(t['source_px']) for t in city['schematic_terrain'] if t['kind']=='mountain'])
water = poly(next(t['source_px'] for t in city['schematic_terrain'] if t['id']=='yangtze'))
water = water.difference(unary_union([poly(t['source_px']) for t in city['schematic_terrain'] if t['kind']=='island']))
waters = [water]
for lake in city['lakes']:
    outer = unary_union([poly(r['source_px']) for r in lake['rings'] if r['role']=='outer'])
    inner = unary_union([poly(r['source_px']) for r in lake['rings'] if r['role']=='inner'])
    waters.append(outer.difference(inner))
waters += [LineString(r['source_px']).buffer(2.2) for r in city['rivers']]
water = unary_union(waters)
reserves = unary_union([Point(l['source_px']).buffer(18,resolution=20) for l in city['landmarks'] if l['id']!='xuanwu'])
road_lines = [LineString(r['source_px']) for r in city['roads']]
road_mask = unary_union(road_lines).buffer(1.35,cap_style=2,join_style=2)

# Building coverage establishes the urban extent. Nearby OSM local streets
# subdivide it into readable parcels; these cuts are not new navigation roads.
cells = sorted(set((int((b['bbox'][0]+b['bbox'][2])/16),int((b['bbox'][1]+b['bbox'][3])/16)) for b in raw))
urban_extent = unary_union([Point(x*8+4,y*8+4).buffer(17,resolution=4) for x,y in cells])
urban_extent = unary_union([urban_extent]+[g for g,k,_ in uses if k!='park']).intersection(frame)
# Read the shared bridge placement rather than duplicating its rotation/endpoints.
bridge_placements=json.loads(subprocess.check_output(['node','--input-type=module','-e',"import {BRIDGE_PLACEMENTS} from './src/landmark-placement.js'; console.log(JSON.stringify(BRIDGE_PLACEMENTS))"],cwd=ROOT,text=True))
bridge_reserves=[]
for id,placement in bridge_placements.items():
    anchor=next(l['source_px'] for l in city['landmarks'] if l['id']==id)
    cx=anchor[0]+placement['offsetX']/.6;cy=anchor[1]+placement['offsetZ']/.6
    half_length,half_width=(30.2,2.85) if id=='yangtze-bridge' else (28,3.4)
    rect=box(cx-half_length*placement['scale']/.6,cy-half_width*placement['scale']/.6,cx+half_length*placement['scale']/.6,cy+half_width*placement['scale']/.6)
    bridge_reserves.append(affinity.rotate(rect,-math.degrees(placement['rotationY']),origin=(cx,cy)).buffer(1.5))
no_build = unary_union([water.buffer(2.4),mountains.buffer(3),reserves,wall_mask,*bridge_reserves])
city_land = urban_extent.difference(no_build).difference(parks).buffer(0)
local_streets = []
source_features = load(SOURCE/'osm-features.json')['features']
for f in source_features:
    tags = f['tags']
    if tags.get('highway') not in ['residential','living_street','unclassified','tertiary','secondary','primary']: continue
    coords = [projected(*p) for p in f['geometry']]
    if len(coords)<2: continue
    line = LineString(coords).intersection(frame)
    if not line.is_empty: local_streets.append(line)
local_mask = unary_union(local_streets).buffer(.48,cap_style=2,join_style=2)
blocks = city_land.difference(unary_union([road_mask,local_mask]))

def subdivide(g,depth=0):
    if g.area < 30: return []
    if (g.area < 540 and max(g.bounds[2]-g.bounds[0],g.bounds[3]-g.bounds[1])<45) or depth>8: return [g]
    rect = list(g.minimum_rotated_rectangle.exterior.coords)
    lengths = [math.dist(rect[i],rect[i+1]) for i in range(4)]
    i = lengths.index(max(lengths))
    angle = math.degrees(math.atan2(rect[i+1][1]-rect[i][1],rect[i+1][0]-rect[i][0]))
    origin = g.centroid.coords[0]
    flat = affinity.rotate(g,-angle,origin=origin)
    x0,y0,x1,y1 = flat.bounds
    mid = x0+(x1-x0)*(.44+RNG.random()*.12)
    pieces = [flat.intersection(box(x0-1,y0-1,mid-.35,y1+1)),flat.intersection(box(mid+.35,y0-1,x1+1,y1+1))]
    return [r for piece in pieces for p in polys(piece) for r in subdivide(affinity.rotate(p,angle,origin=origin),depth+1)]

patches=[]
for block in sorted(polys(blocks),key=lambda g:(round(g.centroid.y,3),round(g.centroid.x,3))):
    patches.extend(subdivide(block))
patches = [p.simplify(.2,preserve_topology=True) for p in patches if p.area>=30]
existing = [Polygon(b['outer'],b['holes']) for b in buildings]
existing_index = STRtree(existing)
parcels, groups, lawns, paths = [], [], [], []
all_additions=[]
for i,g in enumerate(patches):
    pt = g.representative_point()
    matches = [uses[int(j)] for j in use_index.query(pt) if uses[int(j)][0].covers(pt)]
    kind = min(matches,key=lambda u:u[0].area)[1] if matches else ('courtyard' if 300<pt.x<465 and 465<pt.y<595 else 'residential')
    if kind=='park': continue
    rect = list(g.minimum_rotated_rectangle.exterior.coords)
    k = max(range(4),key=lambda j:math.dist(rect[j],rect[j+1]))
    angle = math.degrees(math.atan2(rect[k+1][1]-rect[k][1],rect[k+1][0]-rect[k][0]))
    origin = pt.coords[0]
    flat = affinity.rotate(g,-angle,origin=origin)
    x0,y0,x1,y1 = flat.bounds
    obstacles = [existing[int(j)].buffer(.85) for j in existing_index.query(g)]
    available = g.buffer(-1.3).difference(unary_union(obstacles))
    # Rotate a small set of white-model types to follow each parcel, retaining
    # a common courtyard / planted centre rather than filling every gap.
    template = 'office' if kind=='commercial' else 'court' if kind in ['courtyard','campus'] else 'slab'
    target = min(9,max(1,int(g.area/46)))
    candidates=[]
    for yy in range(math.ceil(y0/5),math.floor(y1/5)+1):
        for xx in range(math.ceil(x0/6),math.floor(x1/6)+1):
            x,y=xx*6+(i%3)*.4,yy*5
            if template=='court' and abs(x-(x0+x1)/2)<(x1-x0)*.22 and abs(y-(y0+y1)/2)<(y1-y0)*.22: continue
            w,d=(3.0,2.9) if template=='office' else (4.0,1.8) if template=='slab' else (3.8,1.65)
            footprint=local_rect(x,y,w,d,angle,origin)
            if available.covers(footprint): candidates.append((footprint,x,y,w,d))
    RNG.shuffle(candidates)
    accepted=[]
    for fp,x,y,w,d in candidates:
        if len(accepted)>=target: break
        if any(fp.distance(other)<1.1 for other in accepted): continue
        accepted.append(fp)
        h=(2.0+RNG.random()*2.6) if template=='office' else (1.05+RNG.random()*1.15) if template=='slab' else (.65+RNG.random()*.5)
        p=fp.centroid
        item={'id':'infill-'+str(len(groups)),'parcel':i,'template':template,'p':[round(p.x,4),round(p.y,4)],'angle':round(angle,4),'width':w,'depth':d,'height':round(h,3),**encode(fp),'bbox':list(fp.bounds),'height_source':'artistic_massing','source':'procedural_infill'}
        groups.append(item);all_additions.append(fp)
    parcels.append({'id':i,'kind':kind,'tone':i%4,'basis':min(matches,key=lambda u:u[0].area)[2] if matches else 'OSM street subdivision / artistic land-use',**encode(g)})
    # Ground-level planted courts, clipped to every actual or added footprint.
    free = available.difference(unary_union([fp.buffer(.65) for fp in accepted]))
    court = local_rect((x0+x1)/2,(y0+y1)/2,max(2,(x1-x0)*.38),max(2,(y1-y0)*.40),angle,origin).intersection(free)
    for p in polys(court):
        if p.area>5: lawns.append({'parcel':i,**encode(p.simplify(.15,preserve_topology=True))})

# Park paving is never filled with background buildings. Boundaries remain
# geographic hints; all courtyard planting and volumes are artistic additions.
park_surfaces = [p for p in polys(parks.intersection(urban_extent).difference(no_build).difference(road_mask)) if p.area>20]
park_surfaces = [p.simplify(.3,preserve_topology=True) for p in park_surfaces]
occupied_geoms = existing+all_additions
occupied_index = STRtree(occupied_geoms)
def clear_tree(pt,radius=1.4):
    if not frame.contains(pt) or no_build.covers(pt) or road_mask.distance(pt)<.55: return False
    return not any(occupied_geoms[int(j)].distance(pt)<radius for j in occupied_index.query(pt.buffer(radius)))
trees=[];tree_bins={}
def add_tree(pt,kind,size,species,turn=0):
    key=(int(pt.x/3),int(pt.y/3))
    for xx in range(key[0]-1,key[0]+2):
        for yy in range(key[1]-1,key[1]+2):
            if any(pt.distance(q)<2.7 for q in tree_bins.get((xx,yy),[])): return False
    if not clear_tree(pt): return False
    tree_bins.setdefault(key,[]).append(pt)
    trees.append({'p':[round(pt.x,4),round(pt.y,4)],'kind':kind,'size':round(size,3),'species':species,'turn':turn,'clearance':1.4})
    return True
# Sample the same road alignments, with coherent species along each avenue.
for i,line in enumerate(road_lines):
    if len(trees)>=1600: break
    if city['roads'][i]['kind']!='ground': continue
    for n in range(1,int(line.length/6.5)):
        t=n*6.5;pt=line.interpolate(t);before=line.interpolate(max(0,t-.3));after=line.interpolate(min(line.length,t+.3))
        dx,dy=after.x-before.x,after.y-before.y;length=math.hypot(dx,dy)
        if length<.001: continue
        for side in [-1,1]:
            q=Point(pt.x-dy/length*2.9*side,pt.y+dx/length*2.9*side)
            if urban_extent.covers(q):add_tree(q,'avenue',.36+RNG.random()*.11,'plane' if i%3 else 'ginkgo',RNG.random()*6.28)
# Plant courtyards in small groups, with modest size variation.
for lawn in lawns:
    g=Polygon(lawn['outer'],lawn['holes']);x0,y0,x1,y1=g.bounds
    for _ in range(min(4,max(1,int(g.area/12)))):
        p=Point(RNG.uniform(x0,x1),RNG.uniform(y0,y1))
        if g.contains(p):add_tree(p,'court',.31+RNG.random()*.13,'camphor' if RNG.random()<.8 else 'blossom',RNG.random()*6.28)

result={'version':1,'seed':2026102907,'note':'City-wall clearances follow mapped standing fabric. Road/park hints come from the cached OSM snapshot. Parcel subdivisions, added white building groups and planting are artistic massing, not surveyed buildings or navigable roads.',
        'counts':{'parcels':len(parcels),'buildings':len(groups),'courtyards':len(lawns),'parks':len(park_surfaces),'trees':len(trees)},
        'parcels':parcels,'buildings':groups,'lawns':lawns,'parks':[encode(p) for p in park_surfaces],'trees':trees}
(ROOT/'public/data/urban.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')))
print(json.dumps(result['counts'],indent=2))
