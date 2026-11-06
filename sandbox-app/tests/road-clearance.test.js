import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {createRoadLayout} from '../src/road-clearance.js';
import {buildRoadProfiles,roadLift,ELEVATED_HEIGHT,RIVER_BRIDGE_HEIGHT} from '../src/road-network.js';
import {addWhiteRoads} from '../src/roads.js';
import {createTerrainProfile} from '../src/terrain-profile.js';
import {world,BOUNDS} from '../src/geo.js';
import {createWallIndex} from '../src/city-walls.js';
import {createBuildingIndex} from '../src/building-footprints.js';

const load=p=>JSON.parse(readFileSync(new URL(p,import.meta.url)));
const data=load('../public/data/nanjing.json'),manifest=load('../public/models/manifest.json');
const original=JSON.stringify(data),layout=createRoadLayout(data);
const profile=createTerrainProfile({...data,roads:layout.roads});

test('display diversions preserve source data, shared junctions and the connected graph',()=>{
  assert.equal(JSON.stringify(data),original);
  assert.equal(layout.roads.length,data.roads.length);
  assert.ok(layout.adjusted>0&&layout.adjusted<40,'changes remain local to the two landmarks');
  const graph=new Map(),positions=new Map();
  for(const road of layout.roads)road.node_ids.forEach((id,i)=>{
    if(positions.has(id))assert.deepEqual(road.source_px[i],positions.get(id),'shared nodes cannot split');
    positions.set(id,road.source_px[i]);if(!graph.has(id))graph.set(id,new Set());
    if(i){const a=road.node_ids[i-1];graph.get(id).add(a);graph.get(a).add(id);}
  });
  const pending=[graph.keys().next().value],seen=new Set();
  while(pending.length){const id=pending.pop();if(seen.has(id))continue;seen.add(id);pending.push(...graph.get(id));}
  assert.equal(seen.size,graph.size);
  for(const [id,neighbours] of graph)if(neighbours.size===1){
    const [x,z]=positions.get(id);
    assert.ok(Math.min(Math.abs(x-BOUNDS[0]),Math.abs(x-BOUNDS[2]),Math.abs(z-BOUNDS[1]),Math.abs(z-BOUNDS[3]))<1e-5,'no new interior dead end');
  }
});

test('short river bridges stay low while the actual south-ring viaduct remains elevated',()=>{
  for(const id of ['363907313','788486984','777411822']){
    const road=layout.roads.find(r=>r.osm_way_id===id);
    assert.equal(road.bridgeProfile,'river');assert.equal(roadLift(road),RIVER_BRIDGE_HEIGHT);
  }
  assert.equal(roadLift(layout.roads.find(r=>r.osm_way_id==='96674406')),ELEVATED_HEIGHT);
  const nodes=new Map();
  for(const {road,points} of buildRoadProfiles(layout.roads,profile.height,layout)){
    if(road.kind==='tunnel')assert.ok(points.every(p=>p.lift===0));
    points.forEach((p,i)=>{
      if(nodes.has(p.id))assert.deepEqual([p.p,p.y],nodes.get(p.id));else nodes.set(p.id,[p.p,p.y]);
      if(i){const q=points[i-1],distance=Math.hypot(p.p[0]-q.p[0],p.p[1]-q.p[1]);assert.ok(Math.abs(p.lift-q.lift)<=distance*.120001+1e-6);}
      if(layout.maximumLift(p.p)<Infinity)assert.ok(Math.abs(p.lift-.14)<1e-7,'one level through the gate, without overlapping ramps');
    });
  }
});

test('local diversions also clear the mapped city walls and neighbouring white buildings',()=>{
  const walls=load('../public/data/city-walls.json');
  const wallAt=createWallIndex({features:walls.display.map(f=>({...f,width:Math.max(...(f.widths||[f.width||0]))}))});
  const buildingAt=createBuildingIndex([...load('../public/data/buildings.json').features,...load('../public/data/urban.json').buildings]);
  for(const r of layout.roads.filter(r=>r.displayAdjusted))for(let i=1;i<r.source_px.length;i++){
    const a=r.source_px[i-1],b=r.source_px[i],steps=Math.ceil(Math.hypot(b[0]-a[0],b[1]-a[1])*5);
    for(let j=0;j<=steps;j++){
      const p=a.map((v,k)=>v+(b[k]-v)*j/steps);
      assert.equal(wallAt(p,.65),false,`${r.osm_way_id}: diversion crosses a mapped wall`);
      assert.equal(buildingAt(p,.65),false,`${r.osm_way_id}: diversion enters a white building`);
    }
  }
});

// Read the final GLB hierarchy, not a manually assumed Blender source bound.
function exportedBounds(file){
  const b=readFileSync(new URL('../public/models/'+file,import.meta.url));
  const doc=JSON.parse(b.toString('utf8',20,20+b.readUInt32LE(12))),box=new THREE.Box3();
  function visit(i,parent){
    const node=doc.nodes[i],matrix=new THREE.Matrix4();
    if(node.matrix)matrix.fromArray(node.matrix);
    else matrix.compose(new THREE.Vector3(...(node.translation||[0,0,0])),new THREE.Quaternion(...(node.rotation||[0,0,0,1])),new THREE.Vector3(...(node.scale||[1,1,1])));
    matrix.premultiply(parent);
    if(node.mesh!==undefined)for(const p of doc.meshes[node.mesh].primitives){
      const a=doc.accessors[p.attributes.POSITION];box.union(new THREE.Box3(new THREE.Vector3(...a.min),new THREE.Vector3(...a.max)).applyMatrix4(matrix));
    }
    for(const child of node.children||[])visit(child,matrix);
  }
  for(const i of doc.scenes[doc.scene||0].nodes)visit(i,new THREE.Matrix4());
  return box;
}

test('rendered road ribbons and junction caps clear the final landmark foundations and walls',()=>{
  const scene=new THREE.Scene();
  const {group}=addWhiteRoads({scene,data,profile,layout,mat:(color,extra)=>new THREE.MeshStandardMaterial({color,...extra})});
  const positions=group.getObjectByName('road-decks').geometry.attributes.position;
  for(const zone of layout.zones){
    const asset=manifest.models.find(a=>a.id===zone.id),bound=exportedBounds(asset.file);
    const root=data.landmarks.find(p=>p.id===zone.id),[x,z]=world(root.source_px),offset=asset.scene_offset||[0,0,0];
    const matrix=new THREE.Matrix4().compose(new THREE.Vector3(x+offset[0],profile.height(root.source_px)+.18,z+offset[2]),new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,1,0),asset.scene_rotation_y||0),new THREE.Vector3().setScalar(asset.scene_scale));
    const inverse=matrix.clone().invert(),worldBounds=bound.clone().applyMatrix4(matrix);
    const blockers=zone.passage?[
      new THREE.Box3(bound.min.clone(),new THREE.Vector3(-1.55,bound.max.y,bound.max.z)),
      new THREE.Box3(new THREE.Vector3(1.55,bound.min.y,bound.min.z),bound.max.clone()),
    ]:[bound];
    let nearby=0;
    for(let i=0;i<positions.count;i+=3){
      const triangle=new THREE.Triangle(...[0,1,2].map(j=>new THREE.Vector3().fromBufferAttribute(positions,i+j)));
      if(!worldBounds.intersectsTriangle(triangle))continue;nearby++;
      triangle.a.applyMatrix4(inverse);triangle.b.applyMatrix4(inverse);triangle.c.applyMatrix4(inverse);
      for(const blocker of blockers)assert.equal(blocker.intersectsTriangle(triangle),false,`${zone.id}: road triangle ${i/3} penetrates the exported building`);
      if(zone.passage)for(const v of [triangle.a,triangle.b,triangle.c]){
        if(v.z>bound.min.z&&v.z<bound.max.z&&Math.abs(v.x)<1.55){
          assert.ok(v.y>.32+.01,'road must be above the stone paving');
          assert.ok(v.y<1.65,'road must clear the lowest gate vault');
        }
      }
    }
    if(zone.passage)assert.ok(nearby>10,'the gate passage must actually be drawn');
  }
  group.traverse(o=>{o.geometry?.dispose();o.material?.dispose();});
});
