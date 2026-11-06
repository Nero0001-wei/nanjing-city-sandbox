import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {addCityWalls,createWallIndex} from '../src/city-walls.js';
import {createTerrainProfile} from '../src/terrain-profile.js';
import {world,SCALE,segmentDistance} from '../src/geo.js';
const load=name=>JSON.parse(readFileSync(new URL('../public/data/'+name+'.json',import.meta.url)));
const data=load('city-walls'),map=load('nanjing'),buildings=load('buildings'),urban=load('urban');
const profile=createTerrainProfile(map),wallOccupied=createWallIndex(data);

test('standing wall display follows source fabric without connecting historical gaps',()=>{
  assert.ok(data.features.length>10&&data.gates.length>=12);
  for(const f of data.features)assert.ok(f.source_tags.barrier==='city_wall'||f.review?.status==='verified_standing');
  for(const f of data.display.filter(f=>f.kind==='line')){
    const source=data.features.find(s=>s.id===f.source_id);
    assert.ok(source);
    for(const p of f.source_px){
      const distance=Math.min(...source.source_px.slice(1).map((b,i)=>segmentDistance(p,source.source_px[i],b)));
      assert.ok(distance<.00001,'wall has shifted off the mapped alignment');
    }
  }
  assert.ok(data.audit.historic_only_paths_omitted>0);
});

test('real and artistic white buildings leave mapped walls clear',()=>{
  assert.ok(buildings.count>=8000,'full-area real footprint coverage should increase');
  for(const b of [...buildings.features,...urban.buildings]){
    for(const p of b.outer)assert.equal(wallOccupied(p,.9),false,b.id);
  }
});

test('standing wall tops have no unexplained road-buffer cuts',()=>{
  assert.equal(data.audit.blanket_road_cuts,false);
  const scene=new THREE.Scene(),group=addCityWalls({scene,profile,data,mat:(color,extra)=>new THREE.MeshStandardMaterial({color,...extra})});
  group.updateMatrixWorld(true);
  const zhonghua=map.landmarks.find(l=>l.id==='zhonghua').source_px;
  const meshes=group.children.filter(o=>o.isMesh&&!o.isInstancedMesh);
  const paths=data.features.flatMap(f=>f.kind==='line'?[f]:[{...f,source_px:[...f.outer,f.outer[0]]}]);
  for(const f of paths)for(let i=1;i<f.source_px.length;i++){
    const a=f.source_px[i-1],b=f.source_px[i],steps=Math.max(1,Math.ceil(Math.hypot(b[0]-a[0],b[1]-a[1])*2));
    for(let j=0;j<=steps;j++){
      // Sample immediately inside segment ends to avoid Float32 edge ambiguity.
      const p=a.map((v,k)=>v+(b[k]-v)*(j+.005)/(steps+.01));
      if(Math.hypot(p[0]-zhonghua[0],p[1]-zhonghua[1])<5.85)continue;
      const [x,z]=world(p),ray=new THREE.Raycaster(new THREE.Vector3(x,100,z),new THREE.Vector3(0,-1,0),0,150);
      assert.ok(ray.intersectObjects(meshes).length>0,`${f.id} has an unexplained top break at ${p}`);
    }
  }
  group.traverse(o=>{o.geometry?.dispose();o.material?.dispose();});
});

test('Jiqing is a four-opening lintel gate, and reviewed southern wall sections exist',()=>{
  const gate=data.gates.find(g=>g.name==='集庆门');
  assert.equal(gate.opening_shape,'rectangular');assert.equal(gate.openings.length,4);
  assert.equal(data.gates.find(g=>g.name==='长干门').openings.length,5);
  assert.equal(data.gates.find(g=>g.name==='华严岗门').openings.length,4);
  for(const name of ['东水关段','武定门段','武定门至雨花门段','雨花门东侧段'])assert.ok(data.features.some(f=>f.name===name));
  assert.equal(data.features.some(f=>f.id==='way/437649421'),false,'lost Shuiximen–Hanximen trace must not become a continuous high wall');
});

test('gateway arches are actual openings while their piers remain solid',()=>{
  for(const gate of data.gates){
    const scene=new THREE.Scene(),group=addCityWalls({scene,profile,data:{...data,gates:[gate]},mat:(color,extra)=>new THREE.MeshStandardMaterial({color,...extra})});
    group.updateMatrixWorld(true);
    const [x,z]=world(gate.p),angle=gate.angle,depth=gate.depth*SCALE,base=profile.height(gate.p)+.045;
    const hitsAt=offset=>{
      const localZ=-depth/2-.01;
      const start=new THREE.Vector3(x+offset*Math.cos(angle)-localZ*Math.sin(angle),base+.35,z+offset*Math.sin(angle)+localZ*Math.cos(angle));
      const ray=new THREE.Raycaster(start,new THREE.Vector3(-Math.sin(angle),0,Math.cos(angle)),0,depth+.02);
      return ray.intersectObject(group,true);
    };
    for(const opening of gate.openings)assert.equal(hitsAt(opening.center*SCALE).length,0,gate.name+' opening is blocked');
    assert.ok(hitsAt(gate.width*SCALE/2-.05).length>0,gate.name+' missing pier');
    group.traverse(o=>{o.geometry?.dispose();o.material?.dispose();});
  }
});
