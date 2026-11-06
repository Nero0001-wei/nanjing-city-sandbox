import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {createWallIndex} from '../src/city-walls.js';
import {ZHONGHUA_PLACEMENT,NORTH_LANDMARK_PLACEMENTS} from '../src/landmark-placement.js';
import {createTerrainProfile} from '../src/terrain-profile.js';

const manifest=JSON.parse(readFileSync(new URL('../public/models/manifest.json',import.meta.url)));
const readAsset=file=>{
  const b=readFileSync(new URL('../public/models/'+file,import.meta.url));
  return {bytes:b.length,doc:JSON.parse(b.toString('utf8',20,20+b.readUInt32LE(12)).trim()),bin:b.subarray(28+b.readUInt32LE(12))};
};

for(const id of ['jiming','zifeng','yuejiang'])test(`${id} complete terrace clears mapped walls and water`,()=>{
  const data=JSON.parse(readFileSync(new URL('../public/data/nanjing.json',import.meta.url)));
  const walls=JSON.parse(readFileSync(new URL('../public/data/city-walls.json',import.meta.url)));
  const wallAt=createWallIndex(walls),terrain=createTerrainProfile(data);
  const anchor=data.landmarks.find(l=>l.id===id).source_px,placement=NORTH_LANDMARK_PLACEMENTS[id];
  const asset=manifest.models.find(a=>a.id===id),[width,depth]=asset.blender_dimensions;
  assert.equal(asset.scene_scale,placement.scale);
  assert.deepEqual(asset.scene_offset,[placement.offsetX,0,placement.offsetZ]);
  for(let i=0;i<=96;i++)for(let j=0;j<=76;j++){
    const p=[anchor[0]+((i/96-.5)*width*placement.scale+placement.offsetX)/.6,anchor[1]+((j/76-.5)*depth*placement.scale+placement.offsetZ)/.6];
    assert.equal(wallAt(p,.5),false,`${id}: terrace cuts into a mapped city wall`);
    assert.equal(terrain.isWater(p),false,`${id}: terrace crosses water`);
  }
});

test('Zhonghua enlarged fortress clears the neighbouring Baoen foundation',()=>{
  const data=JSON.parse(readFileSync(new URL('../public/data/nanjing.json',import.meta.url)));
  const gate=data.landmarks.find(p=>p.id==='zhonghua'),tower=data.landmarks.find(p=>p.id==='baoen');
  const asset=manifest.models.find(a=>a.id==='zhonghua');
  const a=asset.scene_rotation_y||0;
  const gateSouth=(gate.source_px[1]-430)*.6+asset.scene_offset[2]+(Math.abs(Math.sin(a))*14.5+Math.cos(a)*17.5)*asset.scene_scale;
  const towerAsset=manifest.models.find(a=>a.id==='baoen');
  const towerNorth=(tower.source_px[1]-430)*.6+(towerAsset.scene_offset?.[2]||0)-towerAsset.blender_dimensions[1]/2*towerAsset.scene_scale;
  assert.ok(towerNorth-gateSouth>.75,'landmark foundations must not intersect');
});

test('Zhonghua southern terrace joins both mapped walls at their shared heading',()=>{
  const data=JSON.parse(readFileSync(new URL('../public/data/nanjing.json',import.meta.url)));
  const walls=JSON.parse(readFileSync(new URL('../public/data/city-walls.json',import.meta.url)));
  const occupied=createWallIndex(walls),anchor=data.landmarks.find(p=>p.id==='zhonghua').source_px;
  const a=manifest.models.find(a=>a.id==='zhonghua'),p=ZHONGHUA_PLACEMENT;
  assert.equal(a.scene_rotation_y,p.rotationY);assert.equal(a.scene_scale,p.scale);
  assert.deepEqual(a.scene_offset,[p.offsetX,0,p.offsetZ]);
  const alignment=a.wall_alignment,ends=alignment.attachment_source_px;
  const heading=Math.atan2(ends[1][1]-ends[0][1],ends[1][0]-ends[0][0]);
  assert.ok(Math.abs(heading+p.rotationY)<1e-8,'gate must follow the wall heading');
  for(const [i,sign] of [[0,-1],[1,1]]){
    const x=sign*alignment.local_attachment_x*p.scale,z=alignment.local_attachment_z*p.scale;
    const q=[anchor[0]+(Math.cos(p.rotationY)*x+Math.sin(p.rotationY)*z+p.offsetX)/.6,anchor[1]+(-Math.sin(p.rotationY)*x+Math.cos(p.rotationY)*z+p.offsetZ)/.6];
    assert.ok(Math.hypot(q[0]-ends[i][0],q[1]-ends[i][1])*.6<.1,'visible gap at wall joint');
    assert.equal(occupied(q,.15),true,'attachment must meet actual mapped wall geometry');
  }
});

test('Museum terrace leaves the mapped city walls intact and clear',()=>{
  const data=JSON.parse(readFileSync(new URL('../public/data/nanjing.json',import.meta.url)));
  const walls=JSON.parse(readFileSync(new URL('../public/data/city-walls.json',import.meta.url)));
  const occupied=createWallIndex(walls),p=data.landmarks.find(p=>p.id==='museum').source_px;
  const a=manifest.models.find(a=>a.id==='museum');
  for(let x=-17;x<=17;x+=.5)for(let y=-10.8;y<=9;y+=.5){
    const q=[p[0]+(x*a.scene_scale+a.scene_offset[0])/.6,p[1]+(-y*a.scene_scale+a.scene_offset[2])/.6];
    assert.equal(occupied(q,.5),false,'museum terrace intersects the city wall');
  }
});

test('shipped landmark GLBs obey the 40,000-triangle web budget after export',()=>{
  for(const asset of manifest.models){
    const {doc}=readAsset(asset.file);let triangles=0;
    for(const mesh of doc.meshes)for(const primitive of mesh.primitives){
      const mode=primitive.mode??4;
      const count=doc.accessors[primitive.indices??primitive.attributes.POSITION].count;
      if(mode===4)triangles+=count/3;
      else if(mode===5||mode===6)triangles+=Math.max(0,count-2);
    }
    assert.ok(triangles<=40000,`${asset.id}: ${triangles} triangles exceeds AGENTS.md budget`);
    if(asset.triangles!==undefined)assert.equal(triangles,asset.triangles,`${asset.id}: stale manifest`);
    if(['zhongshan','mingxiaoling','meiling','museum','zhonghua','fuzimiao','presidential','baoen','jiming','zifeng','yuejiang','yangtze-bridge','nanjing-eye','aoti'].includes(asset.id))assert.ok(triangles>=20000,`${asset.id}: must retain the requested detail tier`);
  }
});

for(const [id,clearHeight,solidHeight] of [['mingxiaoling',2.6,5.8],['zhonghua',1.8,3.8],['presidential',1.6,4.6]])test(`${id} exported building has traversable gates and solid surrounding masonry`,()=>{
  const {doc,bin}=readAsset(id+'.glb');
  function accessor(id){
    const a=doc.accessors[id],v=doc.bufferViews[a.bufferView],n=a.type==='VEC3'?3:1;
    const [size,read]=({5123:[2,'readUInt16LE'],5125:[4,'readUInt32LE'],5126:[4,'readFloatLE']})[a.componentType];
    return Array.from({length:a.count*n},(_,i)=>bin[read]((v.byteOffset||0)+(a.byteOffset||0)+Math.floor(i/n)*(v.byteStride||n*size)+(i%n)*size));
  }
  const material=new THREE.MeshBasicMaterial({side:THREE.DoubleSide}),scene=new THREE.Group();
  function addNode(id,parent){
    const node=doc.nodes[id],group=new THREE.Group();parent.add(group);
    if(node.matrix){group.matrix.fromArray(node.matrix);group.matrix.decompose(group.position,group.quaternion,group.scale);}
    else{if(node.translation)group.position.fromArray(node.translation);if(node.rotation)group.quaternion.fromArray(node.rotation);if(node.scale)group.scale.fromArray(node.scale);}
    if(node.mesh!==undefined)for(const p of doc.meshes[node.mesh].primitives){
      const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(accessor(p.attributes.POSITION),3));g.setIndex(accessor(p.indices));group.add(new THREE.Mesh(g,material));
    }
    for(const child of node.children||[])addNode(child,group);
  }
  for(const id of doc.scenes[doc.scene||0].nodes)addNode(id,scene);
  scene.updateMatrixWorld(true);
  const hit=(x,y)=>new THREE.Raycaster(new THREE.Vector3(x,y,id==='presidential'?13:20),new THREE.Vector3(0,0,-1),0,id==='presidential'?4:40).intersectObject(scene,true).length;
  for(const x of id==='presidential'?[-7,0,7]:[-.8,0,.8])assert.equal(hit(x,clearHeight),0,'central passage is blocked');
  assert.ok(hit(5,clearHeight)>0,'missing pier');assert.ok(hit(0,solidHeight)>0,'missing masonry above the arch');
  scene.traverse(o=>o.geometry?.dispose());material.dispose();
});

for(const id of ['zhongshan','mingxiaoling','meiling','museum','zhonghua','fuzimiao','presidential','baoen','jiming','zifeng','yuejiang','yangtze-bridge','nanjing-eye','aoti'])test(`${id} web GLB retains embedded maps and baked vertex shading`,()=>{
  const asset=manifest.models.find(a=>a.id===id);const {doc,bytes}=readAsset(asset.file);
  assert.equal(bytes,asset.glb_bytes);
  assert.ok(doc.images.length>=2);
  assert.ok(doc.images.every(im=>im.bufferView!==undefined&&!im.uri));
  for(const mesh of doc.meshes)for(const p of mesh.primitives){
    assert.ok(p.indices!==undefined,'indexed geometry avoids duplicated vertex buffers');
    assert.ok(p.attributes.COLOR_0!==undefined,'baked contact shading must survive export');
  }
});
