import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {buildRoadProfiles,ROAD_WHITE,ELEVATED_HEIGHT,roadLift} from '../src/road-network.js';
import {addWhiteRoads} from '../src/roads.js';
import {createTerrainProfile} from '../src/terrain-profile.js';
import {world,BOUNDS,segmentDistance} from '../src/geo.js';
const load=p=>JSON.parse(readFileSync(new URL(p,import.meta.url)));
const data=load('../public/data/nanjing.json'),snapshot=load('../../output/layout-v2/sources/osm-features.json');
snapshot.features.push(...load('../../output/layout-v2/sources/osm-features-extra.json').features);

test('simplified roads retain source positions and only use source road paths',()=>{
  const source=new Map(snapshot.features.map(f=>[f.id,f]));
  for(const road of data.roads){
    if(road.bridge==='viaduct')assert.equal(road.kind,'elevated');
    if(road.kind==='tunnel')assert.ok(road.tunnel&&road.tunnel!=='no');
    const original=source.get(road.osm_way_id);assert.ok(original);
    const projected=original.geometry.map(([lon,lat])=>[((lon+180)/360*4096-3398)*256,((1-Math.asinh(Math.tan(lat*Math.PI/180))/Math.PI)/2*4096-1661)*256]);
    road.source_px.forEach((p,i)=>{
      if(road.node_ids[i].startsWith('boundary:'))assert.ok(projected.slice(1).some((b,j)=>segmentDistance(p,projected[j],b)<.000002));
      else assert.ok(projected.some(q=>Math.hypot(q[0]-p[0],q[1]-p[1])<.000002));
    });
    let cursor=-1;
    for(const id of road.node_ids){cursor=road.source_node_ids.indexOf(id,cursor+1);assert.ok(cursor>=0,'simplification must keep the source node order');}
  }
  assert.equal(data.roads.find(r=>r.osm_way_id==='96674406').kind,'elevated','inner south ring viaduct regression');
});

test('the entire displayed road network is connected and has no interior dead ends',()=>{
  const graph=new Map(),positions=new Map();
  for(const road of data.roads){
    road.node_ids.forEach((id,i)=>{
      if(!graph.has(id))graph.set(id,new Set());
      if(positions.has(id))assert.deepEqual(positions.get(id),road.source_px[i]);
      positions.set(id,road.source_px[i]);
      const [x,y]=road.source_px[i];assert.ok(x>=BOUNDS[0]&&x<=BOUNDS[2]&&y>=BOUNDS[1]&&y<=BOUNDS[3]);
    });
    for(let i=1;i<road.node_ids.length;i++){const a=road.node_ids[i-1],b=road.node_ids[i];graph.get(a).add(b);graph.get(b).add(a);}
  }
  const stack=[graph.keys().next().value],seen=new Set();
  while(stack.length){const id=stack.pop();if(seen.has(id))continue;seen.add(id);stack.push(...graph.get(id));}
  assert.equal(seen.size,graph.size,'every displayed path must reach the same network');
  let exits=0;
  for(const [id,neighbors] of graph)if(neighbors.size===1){
    const [x,y]=positions.get(id);assert.ok(Math.min(Math.abs(x-BOUNDS[0]),Math.abs(x-BOUNDS[2]),Math.abs(y-BOUNDS[1]),Math.abs(y-BOUNDS[3]))<.00001,`interior dead end ${id}`);exits++;
  }
  assert.equal(exits,data.road_network.audit.boundary_exits);
  assert.ok(data.roads.filter(r=>r.highway.endsWith('_link')).length<150,'keep only necessary ramps');
  assert.ok([...positions.values()].some(([x,y])=>x>200&&x<280&&Math.abs(y-BOUNDS[3])<.00001),'Fengtai South Road must continue to the southern map edge instead of ending in a U-turn');
});

test('urban viaducts use one elevated level regardless of original OSM layer',()=>{
  for(const road of data.roads.filter(r=>r.kind==='elevated'&&!['南京长江大桥','南京眼步行桥'].includes(r.name)))assert.equal(roadLift(road),ELEVATED_HEIGHT);
  assert.equal(roadLift({kind:'elevated',layer:3}),roadLift({kind:'elevated',layer:1}));
});

test('shared junctions have identical deck heights and approach grades stay continuous',()=>{
  const profiles=buildRoadProfiles(data.roads,createTerrainProfile(data).height),junctions=new Map();
  for(const {road,points} of profiles){
    if(road.kind==='tunnel')assert.ok(points.every(p=>p.lift===0));
    for(let i=0;i<points.length;i++){
      const p=points[i];
      if(junctions.has(p.id))assert.equal(p.y,junctions.get(p.id));else junctions.set(p.id,p.y);
      if(i){const q=points[i-1],distance=Math.hypot(p.p[0]-q.p[0],p.p[1]-q.p[1]);assert.ok(Math.abs(p.lift-q.lift)<=distance*.120001+1e-6);}
    }
  }
});

test('roads crossing in plan do not receive fictitious ramp connections',()=>{
  const roads=[
    {osm_way_id:'high',kind:'elevated',layer:1,source_px:[[340,430],[360,430]],node_ids:['a','b']},
    {osm_way_id:'low',kind:'ground',source_px:[[350,420],[350,440]],node_ids:['c','d']}
  ];
  const profiles=buildRoadProfiles(roads);
  assert.ok(profiles[0].points.every(p=>p.lift>1));assert.ok(profiles[1].points.every(p=>p.lift===0));
});

test('white road decks and flat tunnel guides cover bends and joins without visual gaps',()=>{
  const roads=[
    {osm_way_id:'bend',kind:'ground',source_px:[[340,430],[350,430],[350,440]],node_ids:['a','b','c']},
    {osm_way_id:'join',kind:'elevated',layer:1,highway:'trunk_link',source_px:[[350,440],[360,440]],node_ids:['c','d']},
    {osm_way_id:'tunnel',kind:'tunnel',source_px:[[340,450],[340,450.5],[340,451],[340,458]],node_ids:['e','f','g','h']}
  ];
  const scene=new THREE.Scene(),profile={height:()=>0};
  const {group}=addWhiteRoads({scene,data:{roads},profile,mat:(color,extra)=>new THREE.MeshStandardMaterial({color,...extra})});scene.updateMatrixWorld(true);
  const deck=group.getObjectByName('road-decks'),tunnel=group.getObjectByName('underground-alignments');
  assert.equal(deck.material.color.getHex(),ROAD_WHITE);assert.equal(tunnel.material.color.getHex(),ROAD_WHITE);
  for(const object of group.children){for(const v of object.geometry.attributes.position.array)assert.ok(Number.isFinite(v));}
  const hits=(p,mesh)=>{const [x,z]=world(p);return new THREE.Raycaster(new THREE.Vector3(x,20,z),new THREE.Vector3(0,-1,0)).intersectObject(mesh);};
  for(const p of [[349.9,430],[350,430.1],[350,439.9],[350.1,440]])assert.ok(hits(p,deck).length,'no cracks at bends or inter-way joins');
  for(const p of [[340,450.1],[340,451],[340,453],[340,457.9]])assert.ok(hits(p,tunnel).length,'the tunnel guide must remain continuous');
  assert.equal(tunnel.castShadow,false);tunnel.geometry.computeBoundingBox();assert.ok(tunnel.geometry.boundingBox.max.y-tunnel.geometry.boundingBox.min.y<.003,'no raised deck for tunnels');
  assert.ok(tunnel.material.opacity<1);
  group.traverse(o=>{o.geometry?.dispose();o.material?.dispose();});
});

test('an elevated approach meets the tunnel mouth without a vertical gap',()=>{
  const profiles=buildRoadProfiles([
    {osm_way_id:'approach',kind:'elevated',layer:3,source_px:[[320,430],[340,430]],node_ids:['a','mouth']},
    {osm_way_id:'tunnel',kind:'tunnel',source_px:[[340,430],[360,430]],node_ids:['mouth','b']}
  ]);
  assert.equal(profiles[0].points.at(-1).y,profiles[1].points[0].y);
  assert.ok(profiles[0].points.at(-2).lift<profiles[0].points[0].lift);
});
