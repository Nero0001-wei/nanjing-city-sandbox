"""A connected, simplified road diagram built from the cached OSM node graph.

Keep the approved corridors. Select only necessary connecting paths, repair
interior dead ends, and trim unresolved spurs. Never connect roads by proximity.
One-way restrictions are intentionally ignored for this visual connectivity map.
"""
from pathlib import Path
import xml.etree.ElementTree as ET
import collections, json, math, heapq

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / 'output/layout-v2'
BOUNDS = (30, 170, 690, 690)
approved = json.loads((SOURCE / 'nanjing-layout-data.json').read_text())['roads']
seeds = {str(r['osm_way_id']): r for r in approved}
nodes, ways, extra_way_ids = {}, {}, set()
for path in sorted((SOURCE / 'sources').glob('area-*.osm')):
    if path.stat().st_size < 1000:
        continue
    for e in ET.parse(path).getroot():
        if e.tag == 'node':
            nodes[e.get('id')] = [float(e.get('lon')), float(e.get('lat'))]
        elif e.tag == 'way':
            tags = {t.get('k'): t.get('v') for t in e.findall('tag')}
            if tags.get('highway'):
                ways[e.get('id')] = {'nodes': [n.get('ref') for n in e.findall('nd')], 'tags': tags}
                if path.name.startswith('area-extra-'):extra_way_ids.add(e.get('id'))

extra_source={'source':'OpenStreetMap API supplementary southern coverage 2026-10-29',
    'features':[dict(id=id,tags=ways[id]['tags'],geometry=[nodes[n] for n in ways[id]['nodes']]) for id in sorted(extra_way_ids) if all(n in nodes for n in ways[id]['nodes'])]}
(SOURCE/'sources/osm-features-extra.json').write_text(json.dumps(extra_source,ensure_ascii=False,separators=(',',':')))

if set(seeds) - set(ways):
    raise ValueError('An approved corridor is missing from the snapshot')

def projected(p):
    lon, lat = p
    return [round(((lon + 180) / 360 * 4096 - 3398) * 256, 6),
            round(((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * 4096 - 1661) * 256, 6)]

positions = {n: projected(p) for n, p in nodes.items()}

def clip(a, b):
    lo, hi = 0, 1
    dx, dy = b[0]-a[0], b[1]-a[1]
    for p, q in [(-dx,a[0]-BOUNDS[0]),(dx,BOUNDS[2]-a[0]),(-dy,a[1]-BOUNDS[1]),(dy,BOUNDS[3]-a[1])]:
        if p == 0:
            if q < 0: return None
        elif p < 0: lo=max(lo,q/p)
        else: hi=min(hi,q/p)
        if lo > hi: return None
    return lo, hi

def boundary(n):
    x,y=positions[n]
    return min(abs(x-BOUNDS[0]),abs(x-BOUNDS[2]),abs(y-BOUNDS[1]),abs(y-BOUNDS[3])) < 1e-5

allowed={'motorway','trunk','primary','secondary','tertiary','unclassified','residential','living_street','service',
         'motorway_link','trunk_link','primary_link','secondary_link','tertiary_link','pedestrian','footway','path','steps','cycleway'}
full=collections.defaultdict(dict);edges={};by_way=collections.defaultdict(list)
# Approved ways win when two OSM ways describe the same node pair.
for id,w in sorted(ways.items(),key=lambda item:(item[0] not in seeds,int(item[0]))):
    tags=w['tags'];highway=tags['highway']
    if id not in seeds and (highway not in allowed or tags.get('area')=='yes' or tags.get('access') in ['no','private']):continue
    if any(n not in positions for n in w['nodes']):continue
    weight=1 if id in seeds else 1.3 if highway.endswith('_link') else 1.5 if highway in ['motorway','trunk','primary','secondary','tertiary'] else 2 if highway in ['unclassified','residential','living_street','service'] else 4
    for i,(na,nb) in enumerate(zip(w['nodes'],w['nodes'][1:])):
        a,b=positions[na],positions[nb];interval=clip(a,b)
        if not interval:continue
        lo,hi=interval
        if hi-lo<1e-8:continue
        ends=[]
        for n,t in [(na,lo),(nb,hi)]:
            if 1e-8<t<1-1e-8:
                n='boundary:'+':'.join(sorted([na,nb]))+':'+str(round(t if na<nb else 1-t,8))
                positions[n]=[round(a[0]+(b[0]-a[0])*t,6),round(a[1]+(b[1]-a[1])*t,6)]
            ends.append(n)
        a,b=ends;key=tuple(sorted(ends));length=math.dist(positions[a],positions[b])
        if length<1e-7:continue
        if key not in edges:
            edges[key]={'way':id,'index':i,'a':a,'b':b,'length':length,'weight':weight}
            full[a][b]=key;full[b][a]=key
        by_way[id].append(key)

selected=set(k for id in seeds for k in by_way[id])
corridors_at=collections.defaultdict(set)
for id,road in seeds.items():
    for k in by_way[id]:
        for n in k:corridors_at[n].add(road['group'])

def adjacency(selected):
    graph=collections.defaultdict(set)
    for a,b in selected:graph[a].add(b);graph[b].add(a)
    return graph

def components(graph):
    seen=set();result=[]
    for start in graph:
        if start in seen:continue
        stack=[start];part=set();seen.add(start)
        while stack:
            n=stack.pop();part.add(n)
            for m in graph[n]-seen:seen.add(m);stack.append(m)
        result.append(part)
    return sorted(result,key=lambda p:(-len(p),min(p)))

def shortest(starts,target,exclude=frozenset(),limit=math.inf):
    dist={n:0 for n in starts};prev={};queue=[(0,n) for n in sorted(starts)];heapq.heapify(queue)
    while queue:
        d,n=heapq.heappop(queue)
        if d!=dist[n]:continue
        if target(n) and n not in starts:
            path=[]
            while n in prev:
                m,k=prev[n];path.append(k);n=m
            return path
        for m,k in full[n].items():
            if k in exclude:continue
            e=edges[k];cost=d+e['length']*e['weight']
            if cost<=limit and cost<dist.get(m,math.inf):dist[m]=cost;prev[m]=(n,k);heapq.heappush(queue,(cost,m))
    return None

before=adjacency(selected)
initial_components=len(components(before))
initial_ends=sum(len(v)==1 and not boundary(n) for n,v in before.items())
# Join every approved component to the main network using actual streets/paths.
# This chooses necessary ramps instead of flooding all connected ramp branches.
while True:
    parts=components(adjacency(selected))
    if len(parts)<=1:break
    main=parts[0];targets=set().union(*parts[1:])
    path=shortest(main,lambda n:n in targets)
    if path is None:
        # Isolated source fragments cannot be given fictitious connectors.
        selected={k for k in selected if k[0] in main};break
    selected.update(path)

repaired=[]
# Repair small gaps/omitted continuations. A terminal can connect back into the
# diagram or continue to its boundary; do not import long, unnecessary detours.
for n in sorted(adjacency(selected)):
    graph=adjacency(selected)
    if len(graph.get(n,()))!=1 or boundary(n):continue
    targets=set(graph)-{n}
    previous=next(iter(graph[n]));p=positions[n];q=positions[previous]
    length=math.dist(p,q);direction=[(p[0]-q[0])/length,(p[1]-q[1])/length]
    def continuation(m):
        if boundary(m):return True
        if m not in targets:return False
        forward=sum((positions[m][axis]-p[axis])*direction[axis] for axis in [0,1])
        other_corridor=bool(corridors_at[n] and corridors_at[m]-corridors_at[n])
        # A short U-turn into the opposite carriageway can fool a node-degree
        # audit while still looking like a chopped-off road. Continue forward
        # or reach another corridor; do not use that U-turn as a gap repair.
        return forward>1 or other_corridor
    outward=(p[0]-BOUNDS[0]<50 and direction[0]<-.3) or (BOUNDS[2]-p[0]<50 and direction[0]>.3) or (p[1]-BOUNDS[1]<50 and direction[1]<-.3) or (BOUNDS[3]-p[1]<50 and direction[1]>.3)
    # Near the drawing edge, prefer the real outward continuation over a nearby
    # turnaround. Supplementary southern data lets Fengtai reach that edge.
    path=shortest({n},boundary,exclude=selected,limit=130) if outward else None
    if not path:path=shortest({n},continuation,exclude=selected,limit=65)
    if path:
        selected.update(path);repaired.append(n)

# Recursively trim only unresolved interior spurs, including dangling ramps.
# Boundary exits remain; pruning cannot split a connected component.
trimmed=set()
def prune_spurs():
    graph=adjacency(selected)
    queue=collections.deque(n for n,v in graph.items() if len(v)==1 and not boundary(n))
    while queue:
        n=queue.popleft()
        if len(graph[n])!=1 or boundary(n):continue
        m=next(iter(graph[n]));key=tuple(sorted([n,m]));selected.remove(key);trimmed.add(key)
        graph[n].remove(m);graph[m].remove(n)
        if len(graph[m])==1 and not boundary(m):queue.append(m)
prune_spurs()

# Remove tiny U-turn caps at the tip of an otherwise dangling pair of lanes.
# Their two lanes form a graph cycle, but look like a cut-off road in a sandbox.
# A cap is removed only if another connection already exists around the network.
removed_hairpins=[]
for id,way_edges in by_way.items():
    keys={k for k in way_edges if k in selected and edges[k]['way']==id}
    if not keys or sum(edges[k]['length'] for k in keys)>4:continue
    local=adjacency(keys);ends=[n for n,v in local.items() if len(v)==1]
    if len(ends)!=2:continue
    a,b=ends
    if not corridors_at[a].intersection(corridors_at[b]):continue
    graph=adjacency(selected)
    if any(len(graph[n])!=2 for n in local):continue
    outside_a=next(iter(graph[a]-local[a]));outside_b=next(iter(graph[b]-local[b]))
    va=[positions[a][i]-positions[outside_a][i] for i in [0,1]]
    vb=[positions[outside_b][i]-positions[b][i] for i in [0,1]]
    dot=sum(x*y for x,y in zip(va,vb))/(math.hypot(*va)*math.hypot(*vb))
    if dot>-.6:continue
    remainder=adjacency(selected-keys);seen={a};stack=[a]
    while stack and b not in seen:
        for n in remainder[stack.pop()]-seen:seen.add(n);stack.append(n)
    if b in seen:
        selected.difference_update(keys);trimmed.update(keys);removed_hairpins.append(id);prune_spurs()

# Some turnarounds span several ways. Collapse degree-two chains for this audit
# so a long out-and-back pair of carriageways is not mistaken for a useful road.
removed_return_chains=0
while True:
    graph=adjacency(selected);visited=set();removed=False
    for start in sorted(n for n,v in graph.items() if len(v)!=2):
        for neighbor in sorted(graph[start]):
            first=tuple(sorted([start,neighbor]))
            if first in visited:continue
            chain=[first];visited.add(first);previous,current=start,neighbor
            while len(graph[current])==2 and current!=start:
                following=next(iter(graph[current]-{previous}));key=tuple(sorted([current,following]))
                chain.append(key);visited.add(key);previous,current=current,following
            if math.dist(positions[start],positions[current])>3 or sum(edges[k]['length'] for k in chain)<12:continue
            owners={edges[k]['way'] for k in chain}
            if any(ways[id]['tags'].get('highway') in ['footway','path','pedestrian','steps','cycleway'] or ways[id]['tags'].get('name') in ['南京长江大桥','南京眼步行桥'] for id in owners):continue
            corridor_groups={seeds[id]['group'] for id in owners if id in seeds}
            if len(corridor_groups)>1:continue
            remainder=adjacency(selected-set(chain))
            if start not in remainder or current not in remainder:continue
            seen={start};stack=[start]
            while stack and current not in seen:
                for n in remainder[stack.pop()]-seen:seen.add(n);stack.append(n)
            if current not in seen:continue
            selected.difference_update(chain);trimmed.update(chain);removed_return_chains+=1;prune_spurs();removed=True;break
        if removed:break
    if not removed:break
graph=adjacency(selected)
if len(components(graph))!=1 or any(len(v)==1 and not boundary(n) for n,v in graph.items()):
    raise ValueError('Road connectivity invariant failed')

# Simplify bends only between protected junctions. All retained samples stay at
# their source coordinates, and shared nodes remain exact across road records.
protected={n for n,v in graph.items() if len(v)!=2 or boundary(n)}
def distance(p,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1];den=dx*dx+dy*dy
    t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den)) if den else 0
    return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)
def simplify(ids):
    if len(ids)<3:return ids
    a,b=positions[ids[0]],positions[ids[-1]]
    candidates=[(distance(positions[n],a,b),i) for i,n in enumerate(ids[1:-1],1)]
    d,i=max(candidates)
    if d<=.28:return [ids[0],ids[-1]]
    return simplify(ids[:i+1])[:-1]+simplify(ids[i:])

roads=[];retained_before=0
for id in sorted(by_way,key=int):
    w=ways[id];runs=[];run=[];indices=[];last_index=-2
    for k in by_way[id]:
        if k not in selected or edges[k]['way']!=id:continue
        e=edges[k];a,b=e['a'],e['b']
        if run and (e['index']!=last_index+1 or run[-1]!=a):runs.append((run,indices));run=[];indices=[]
        if not run:run=[a]
        run.append(b);indices.append(e['index']);last_index=e['index']
    if run:runs.append((run,indices))
    tags=w['tags'];tunnel=tags.get('tunnel','no') not in ['no','false','0'];bridge=tags.get('bridge','no') not in ['no','false','0'];layer=int(tags.get('layer','0'))
    kind='tunnel' if tunnel else 'elevated' if bridge or layer>0 else 'ground'
    for part,(ids,indices) in enumerate(runs):
        retained_before+=len(ids)
        cuts=[0]+[i for i,n in enumerate(ids[1:-1],1) if n in protected]+[len(ids)-1];simplified=[]
        for a,b in zip(cuts,cuts[1:]):simplified.extend(simplify(ids[a:b+1])[:-1])
        simplified.append(ids[-1])
        roads.append(dict(osm_way_id=id,segment_id=f'{id}:{part}',name=tags.get('name',''),group=seeds.get(id,{}).get('group','路网连接'),kind=kind,
            source_px=[positions[n] for n in simplified],node_ids=simplified,source_node_ids=ids,source_edge_indices=indices,
            highway=tags['highway'],layer=layer,bridge=tags.get('bridge'),tunnel=tags.get('tunnel'),lanes=tags.get('lanes'),added_connection=id not in seeds))

# Audit the exact simplified geometry that the browser will render, after crop.
render_graph=adjacency({tuple(sorted([a,b])) for r in roads for a,b in zip(r['node_ids'],r['node_ids'][1:])})
ends=[n for n,v in render_graph.items() if len(v)==1]
audit=dict(components=len(components(render_graph)),interior_dead_ends=sum(not boundary(n) for n in ends),boundary_exits=sum(boundary(n) for n in ends),
    initial_components=initial_components,initial_interior_dead_ends=initial_ends,repaired_terminals=len(repaired),trimmed_edges=len(trimmed),
    removed_hairpin_caps=removed_hairpins,
    removed_return_chains=removed_return_chains,
    source_points=retained_before,display_points=sum(len(r['source_px']) for r in roads),ramp_segments=sum(r['highway'].endswith('_link') for r in roads))
if audit['components']!=1 or audit['interior_dead_ends']!=0:raise ValueError(f'Simplification disconnected roads: {audit}')
result=dict(source='OpenStreetMap API snapshot 2026-10-29',connection_rule='Shared-node shortest connectors; interior spurs pruned; boundary exits retained; junction-preserving simplification.',
    height_note='Ground plus one stylized elevated level. Water-crossing landmark bridges retain their own deck height. Not a navigation or surveyed model.',
    approved_count=len(seeds),added_count=sum(r['added_connection'] for r in roads),audit=audit,roads=roads)
(ROOT/'data/road-network.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')))
audit_folder=ROOT/'artifacts/roads-simple';audit_folder.mkdir(parents=True,exist_ok=True)
(audit_folder/'connectivity.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='roads'},ensure_ascii=False,indent=2))
