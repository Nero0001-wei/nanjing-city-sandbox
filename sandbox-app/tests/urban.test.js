import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {createBuildingIndex,footprintDistance} from '../src/building-footprints.js';
import {createTerrainProfile} from '../src/terrain-profile.js';
import {addUrbanFabric,buildCityVegetation} from '../src/urban.js';
const load=name=>JSON.parse(readFileSync(new URL('../public/data/'+name+'.json',import.meta.url)));
const map=load('nanjing'),original=load('buildings'),urban=load('urban');
const occupied=createBuildingIndex([...original.features,...urban.buildings]);
const profile=createTerrainProfile(map,occupied);

test('added white groups preserve road, water and landmark clearances',()=>{
  assert.ok(urban.buildings.length>500);
  for(const b of urban.buildings){
    assert.equal(b.source,'procedural_infill');
    assert.ok(b.height>.5&&b.height<5);
    for(const l of map.landmarks.filter(l=>l.id!=='xuanwu'))assert.ok(footprintDistance(l.source_px,b)>18);
    for(let i=0;i<b.outer.length;i++){
      const a=b.outer[i],z=b.outer[(i+1)%b.outer.length],steps=Math.ceil(Math.hypot(z[0]-a[0],z[1]-a[1])*2);
      for(let n=0;n<=steps;n++){
        const p=a.map((v,j)=>v+(z[j]-v)*n/steps);
        assert.equal(profile.isWater(p),false,b.id);
        assert.ok(profile.roadDistance(p,4)>2.4,b.id+' crosses a road');
      }
    }
  }
});
test('city planting keeps crown clearance from actual and added buildings',()=>{
  const trees=buildCityVegetation(profile,urban);
  assert.ok(trees.some(t=>t.kind==='avenue')&&trees.some(t=>t.kind==='court'));
  assert.ok(trees.some(t=>profile.mountainMask(t.p)>.1&&t.size>.8));
  for(const t of trees){
    assert.equal(profile.isWater(t.p),false);
    assert.equal(occupied(t.p,(t.clearance||3.5)-.06),false);
    assert.ok(profile.roadDistance(t.p,5)>1.8);
    assert.ok(profile.landmarkDistance(t.p)>=17);
    if(t.kind==='avenue'||t.kind==='court')assert.ok(t.size<.5,'urban trees should not dwarf white blocks');
  }
});
test('urban meshes contain finite geometry with valid bounds',()=>{
  const scene=new THREE.Scene(),mat=(color,extra)=>new THREE.MeshStandardMaterial({color,...extra});
  const fabric=addUrbanFabric({scene,profile,urban,mat});
  assert.ok(fabric.ground.children.length>0&&fabric.buildings.children.length>0);
  scene.traverse(o=>{
    if(!o.isMesh)return;
    assert.ok(Array.from(o.geometry.attributes.position.array).every(Number.isFinite));
    o.geometry.computeBoundingBox();assert.ok(!o.geometry.boundingBox.isEmpty());
    o.geometry.dispose();o.material.dispose();
  });
});
