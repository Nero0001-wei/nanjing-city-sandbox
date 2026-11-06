import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {AOTI_PLACEMENT} from '../src/landmark-placement.js';
import {createTerrainProfile} from '../src/terrain-profile.js';
import {createBuildingIndex} from '../src/building-footprints.js';
const load=p=>JSON.parse(readFileSync(new URL(p,import.meta.url)));

test('stadium stays on its OSM anchor with a flat dry base clear of roads and white buildings',()=>{
  const data=load('../public/data/nanjing.json'),site=load('../../南京奥体中心模型/site-reference.json');
  const anchor=data.landmarks.find(p=>p.id==='aoti'),terrain=createTerrainProfile(data);
  assert.deepEqual(anchor.source_px,site.source_px);
  const buildings=load('../public/data/buildings.json'),urban=load('../public/data/urban.json');
  assert.ok(!buildings.features.some(b=>b.id==='relation/21641063'),'old stadium white model remains');
  const occupied=createBuildingIndex([...buildings.features,...urban.buildings]);
  const asset=load('../public/models/manifest.json').models.find(m=>m.id==='aoti');
  assert.equal(asset.scene_scale,AOTI_PLACEMENT.scale);assert.equal(asset.scene_rotation_y,AOTI_PLACEMENT.rotationY);
  for(let r=0;r<=20.5;r+=.5)for(let i=0;i<128;i++){
    const angle=i*Math.PI*2/128,p=site.source_px.map((v,j)=>v+r*AOTI_PLACEMENT.scale/.6*(j?Math.sin(angle):Math.cos(angle)));
    assert.equal(terrain.isWater(p),false);assert.ok(Math.abs(terrain.height(p)-terrain.height(anchor.source_px))<.005);
    assert.equal(occupied(p,.2),false);assert.ok(terrain.roadDistance(p,4)>1.1);
  }
  const bottom=.18-.5*AOTI_PLACEMENT.scale;assert.ok(bottom<0&&bottom>-.02,'base must slightly embed into terrain');
});

test('exported stadium has an open playing field, annular roof and two raised arches',()=>{
  const blob=readFileSync(new URL('../public/models/aoti.glb',import.meta.url)),len=blob.readUInt32LE(12);
  const doc=JSON.parse(blob.toString('utf8',20,20+len)),bin=blob.subarray(28+len);
  const read=id=>{
    const a=doc.accessors[id],v=doc.bufferViews[a.bufferView],n=a.type==='VEC3'?3:1;
    const [size,fn]=({5123:[2,'readUInt16LE'],5125:[4,'readUInt32LE'],5126:[4,'readFloatLE']})[a.componentType];
    return Array.from({length:a.count*n},(_,i)=>bin[fn]((v.byteOffset||0)+(a.byteOffset||0)+Math.floor(i/n)*(v.byteStride||n*size)+i%n*size));
  };
  const scene=new THREE.Group(),material=new THREE.MeshBasicMaterial({side:THREE.DoubleSide});
  function node(id,parent){
    const n=doc.nodes[id],g=new THREE.Group();parent.add(g);
    if(n.matrix){g.matrix.fromArray(n.matrix);g.matrix.decompose(g.position,g.quaternion,g.scale);}
    else{if(n.translation)g.position.fromArray(n.translation);if(n.rotation)g.quaternion.fromArray(n.rotation);if(n.scale)g.scale.fromArray(n.scale);}
    if(n.mesh!==undefined)for(const p of doc.meshes[n.mesh].primitives){
      const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(read(p.attributes.POSITION),3));geometry.setIndex(read(p.indices));g.add(new THREE.Mesh(geometry,material));
    }
    for(const child of n.children||[])node(child,g);
  }
  for(const id of doc.scenes[doc.scene||0].nodes)node(id,scene);scene.updateMatrixWorld(true);
  const top=(x,z)=>new THREE.Raycaster(new THREE.Vector3(x,30,z),new THREE.Vector3(0,-1,0)).intersectObject(scene,true)[0]?.point.y;
  assert.ok(top(0,0)>.4&&top(0,0)<.6,'roof must not cap the field');
  assert.ok(top(12,0)>5,'annular roof missing');
  for(const x of [-16,16])assert.ok(top(x,0)>9,'red arch apex missing');
  scene.traverse(o=>o.geometry?.dispose());material.dispose();
});
