import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import * as THREE from 'three';
import {BRIDGE_PLACEMENTS} from '../src/landmark-placement.js';
import {createTerrainProfile} from '../src/terrain-profile.js';
import {createRoadLayout} from '../src/road-clearance.js';
import {buildRoadProfiles} from '../src/road-network.js';
import {world} from '../src/geo.js';
import {addWhiteRoads} from '../src/roads.js';
import {createBuildingIndex} from '../src/building-footprints.js';
import {buildCityVegetation} from '../src/urban.js';
import {yangtzeFootprintDistance} from '../src/landmark-placement.js';

const data=JSON.parse(readFileSync(new URL('../public/data/nanjing.json',import.meta.url)));
data.cityWalls=JSON.parse(readFileSync(new URL('../public/data/city-walls.json',import.meta.url)));
const manifest=JSON.parse(readFileSync(new URL('../public/models/manifest.json',import.meta.url)));
const terrain=createTerrainProfile(data);
const layout=createRoadLayout(data),profiles=buildRoadProfiles(layout.roads,terrain.height,layout);

function load(id){
  const buffer=readFileSync(new URL(`../public/models/${id}.glb`,import.meta.url));
  const length=buffer.readUInt32LE(12),doc=JSON.parse(buffer.toString('utf8',20,20+length)),bin=buffer.subarray(28+length);
  function accessor(index){
    const a=doc.accessors[index],v=doc.bufferViews[a.bufferView],n=a.type==='VEC3'?3:1;
    const [size,read]=({5123:[2,'readUInt16LE'],5125:[4,'readUInt32LE'],5126:[4,'readFloatLE']})[a.componentType];
    return Array.from({length:a.count*n},(_,i)=>bin[read]((v.byteOffset||0)+(a.byteOffset||0)+Math.floor(i/n)*(v.byteStride||n*size)+(i%n)*size));
  }
  const model=new THREE.Group(),material=new THREE.MeshBasicMaterial({side:THREE.DoubleSide});
  function add(index,parent){
    const node=doc.nodes[index],group=new THREE.Group();parent.add(group);
    if(node.matrix){group.matrix.fromArray(node.matrix);group.matrix.decompose(group.position,group.quaternion,group.scale);}
    else{if(node.translation)group.position.fromArray(node.translation);if(node.rotation)group.quaternion.fromArray(node.rotation);if(node.scale)group.scale.fromArray(node.scale);}
    if(node.mesh!==undefined)for(const p of doc.meshes[node.mesh].primitives){
      const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(accessor(p.attributes.POSITION),3));g.setIndex(accessor(p.indices));group.add(new THREE.Mesh(g,material));
    }
    for(const child of node.children||[])add(child,group);
  }
  for(const index of doc.scenes[doc.scene||0].nodes)add(index,model);
  model.updateMatrixWorld(true);
  return {model,buffer,dispose(){model.traverse(o=>o.geometry?.dispose());material.dispose();}};
}

for(const id of Object.keys(BRIDGE_PLACEMENTS)){
  test(`${id} keeps its mapped span endpoints and delivered asset identity`,()=>{
    const placement=BRIDGE_PLACEMENTS[id],a=manifest.models.find(a=>a.id===id),anchor=data.landmarks.find(l=>l.id===id).source_px;
    assert.equal(a.scene_scale,placement.scale);assert.equal(a.scene_rotation_y,placement.rotationY);
    assert.deepEqual(a.scene_offset,[placement.offsetX,placement.offsetY,placement.offsetZ]);
    const asset=load(id);
    assert.equal(createHash('sha256').update(asset.buffer).digest('hex'),a.sha256);
    const [x,z]=world(anchor),transform=new THREE.Matrix4().compose(new THREE.Vector3(x+placement.offsetX,.2,z+placement.offsetZ),new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,1,0),placement.rotationY),new THREE.Vector3().setScalar(placement.scale));
    for(const [i,sign] of [[0,-1],[1,1]]){
      const p=new THREE.Vector3(sign*placement.nativeDeckLength/2,0,0).applyMatrix4(transform),expected=world(placement.endpoints[i]);
      assert.ok(Math.hypot(p.x-expected[0],p.z-expected[1])<1e-6,'main span endpoint moved');
    }
    asset.dispose();
  });

  test(`${id} exported bridge deck is continuous and has an open central passage`,()=>{
    const a=manifest.models.find(a=>a.id===id),asset=load(id),L=a.native_deck_length;
    for(let i=0;i<=20;i++){
      const x=-L/2+.12+(L-.24)*i/20;
      const hits=new THREE.Raycaster(new THREE.Vector3(x,40,0),new THREE.Vector3(0,-1,0),0,80).intersectObject(asset.model,true);
      assert.ok(hits.length,'hole in finished deck');
      assert.ok(Math.abs(hits[0].point.y-a.native_deck_top)<.025,'unexpected obstacle or deck height');
    }
    const hits=new THREE.Raycaster(new THREE.Vector3(-L/2+.1,a.native_deck_top+.5,0),new THREE.Vector3(1,0,0),0,L-.2).intersectObject(asset.model,true);
    assert.equal(hits.length,0,'tower, cable or railing blocks the middle of the bridge');
    if(id==='yangtze-bridge')for(const p of a.source_endpoints){
      const nodes=profiles.filter(r=>r.road.name==='南京长江大桥').flatMap(r=>r.points.filter(n=>Math.hypot(n.p[0]-p[0],n.p[1]-p[1])<1e-6));
      assert.ok(nodes.length>0,'bridge must attach to actual mapped road nodes');
      for(const n of nodes)assert.ok(Math.abs(.2+a.native_deck_top*a.scene_scale-n.y-.018)<1e-6,'bridge surface does not meet the approach road');
    }
    asset.dispose();
  });
}

test('Nanjing Eye stairs reach dry ground on both banks',()=>{
  const asset=load('nanjing-eye'),a=manifest.models.find(a=>a.id==='nanjing-eye'),placement=BRIDGE_PLACEMENTS['nanjing-eye'];
  const centre=placement.endpoints[0].map((v,i)=>(v+placement.endpoints[1][i])/2);
  for(const sign of [-1,1]){
    const x=sign*27.8;
    const hits=new THREE.Raycaster(new THREE.Vector3(x,20,0),new THREE.Vector3(0,-1,0),0,40).intersectObject(asset.model,true);
    assert.ok(hits.length,'missing bank staircase');
    const q=[centre[0]+Math.cos(placement.rotationY)*x*placement.scale/.6,centre[1]-Math.sin(placement.rotationY)*x*placement.scale/.6];
    assert.equal(terrain.isWater(q),false,'staircase ends in water');
    const clearance=.2+hits[0].point.y*placement.scale-terrain.height(q);
    assert.ok(clearance>=0&&clearance<.07,'last step must meet the terrain');
  }
  asset.dispose();
});

test('Yangtze bridge crosses the rendered river with both bridgehead pairs on dry banks',()=>{
  const p=BRIDGE_PLACEMENTS['yangtze-bridge'],[a,b]=p.endpoints;
  const buildings=JSON.parse(readFileSync(new URL('../public/data/buildings.json',import.meta.url))).features;
  const urban=JSON.parse(readFileSync(new URL('../public/data/urban.json',import.meta.url)));
  const occupied=createBuildingIndex([...buildings,...urban.buildings]);
  const centre=a.map((v,i)=>(v+b[i])/2),c=Math.cos(p.rotationY),s=Math.sin(p.rotationY);
  const source=(x,z)=>[centre[0]+(c*x+s*z)*p.scale/.6,centre[1]+(-s*x+c*z)*p.scale/.6];
  // Test complete footings, not just the landmark pin or bridge midpoint.
  for(const x of [-25.8,25.8])for(const z of [-2.05,2.05]){
    for(let i=0;i<=8;i++)for(let j=0;j<=6;j++){
      const q=source(x-1.1+i*2.2/8,z-.75+j*1.5/6);
      assert.equal(terrain.isWater(q),false,'bridgehead footing ends in the river');
      assert.equal(occupied(q,.35),false,'bridgehead footing intersects an existing building');
    }
  }
  for(let x=-20;x<=20;x+=.5)for(const z of [-1.325,0,1.325])assert.equal(terrain.isWater(source(x,z)),true,'main truss is over land instead of spanning the river');
  for(const tree of buildCityVegetation(terrain,urban))assert.ok(yangtzeFootprintDistance(tree.p)>=3.5,'tree crown overlaps the relocated bridge');
});

test('road network keeps approach piers without duplicating the landmark bridge supports',()=>{
  const scene=new THREE.Scene(),roads=addWhiteRoads({scene,data,profile:terrain,layout,mat:(color,options)=>new THREE.MeshStandardMaterial({color,...options})});
  const piers=roads.group.getObjectByName('viaduct-piers'),matrix=new THREE.Matrix4();
  assert.ok(piers.count>0,'approach and other viaduct supports must remain');
  const [a,b]=BRIDGE_PLACEMENTS['yangtze-bridge'].endpoints.map(world),dx=b[0]-a[0],dz=b[1]-a[1];
  for(let i=0;i<piers.count;i++){
    piers.getMatrixAt(i,matrix);const x=matrix.elements[12],z=matrix.elements[14];
    const t=((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz);
    const distance=Math.hypot(x-a[0]-t*dx,z-a[1]-t*dz);
    assert.ok(t<0||t>1||distance>1.2,'duplicate road pier intersects detailed bridge');
  }
  scene.traverse(o=>{o.geometry?.dispose();o.material?.dispose();});
});
