import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {CITY_HILLS} from '../src/terrain-hills.js';
import {createTerrainProfile} from '../src/terrain-profile.js';
import {drapeSurface,groundBuilding} from '../src/grounding.js';
import {BOUNDS,SCALE,world} from '../src/geo.js';
const load=name=>JSON.parse(readFileSync(new URL('../public/data/'+name+'.json',import.meta.url)));
const profile=createTerrainProfile(load('nanjing'));

test('ten mapped city hills have visible relief and continuous gentle foothills',()=>{
  for(const hill of CITY_HILLS){
    let max=0,step=0;
    for(let x=hill.p[0]-hill.radius[0];x<=hill.p[0]+hill.radius[0];x++)for(let y=Math.max(BOUNDS[1],hill.p[1]-hill.radius[1]);y<=hill.p[1]+hill.radius[1];y++){
      const h=profile.reliefHeight([x,y]);max=Math.max(h,max);
      step=Math.max(step,Math.abs(h-profile.reliefHeight([x+.5,y])),Math.abs(h-profile.reliefHeight([x,y+.5])));
      assert.ok(h>=0&&Number.isFinite(h));
    }
    assert.ok(max>1.1,`${hill.name} is still flat (${max})`);
    assert.ok(step<.9,`${hill.name} has an abrupt cliff (${step})`);
  }
});

test('new relief does not lift water or the frame and leaves ordinary plains flat',()=>{
  for(let x=BOUNDS[0];x<=BOUNDS[2];x+=3)for(let y=BOUNDS[1];y<=BOUNDS[3];y+=3){
    if(profile.isWater([x,y]))assert.equal(profile.reliefHeight([x,y]),0);
  }
  for(const p of [[30,400],[690,400],[404,170],[291,690],[220,540],[380,490],[365,655]])assert.equal(profile.height(p),0);
});

test('sloped building foundations touch terrain while their roof stays level',()=>{
  const geometry=new THREE.BoxGeometry(3,2,3).translate(0,1,0),slope={height:p=>(p[0]-350)*.18+1};
  const base=1.6;groundBuilding(geometry,slope,base,2);
  const p=geometry.attributes.position;
  for(let i=0;i<p.count;i++){
    const h=slope.height([p.getX(i)/SCALE+350,p.getZ(i)/SCALE+430]);
    if(p.getY(i)>2)assert.ok(Math.abs(p.getY(i)-(base+2))<1e-6);
    else assert.ok(Math.abs(p.getY(i)-(h-.085))<1e-6,'foundation floats over slope');
  }
  geometry.dispose();
});

test('large park polygons are subdivided and follow the hill beneath their interior',()=>{
  const [x,z]=world(CITY_HILLS[0].p),g=new THREE.PlaneGeometry(35,35).rotateX(-Math.PI/2).translate(x,0,z);
  const draped=drapeSurface(g,profile,.08),p=draped.attributes.position;
  assert.ok(p.count>100);
  for(let i=0;i<p.count;i++)assert.ok(Math.abs(p.getY(i)-profile.height([p.getX(i)/SCALE+350,p.getZ(i)/SCALE+430])-.08)<1e-4);
  draped.dispose();
});

test('Blender tree GLB uses seven species, small indexed meshes and one embedded colour material',()=>{
  const manifest=JSON.parse(readFileSync(new URL('../public/models/manifest.json',import.meta.url))).vegetation;
  const b=readFileSync(new URL('../public/models/trees.glb',import.meta.url));
  const gltf=JSON.parse(b.toString('utf8',20,20+b.readUInt32LE(12)));
  assert.equal(b.length,manifest.glb_bytes);assert.ok(b.length<100000);assert.equal(gltf.materials.length,1);
  assert.ok(gltf.buffers.every(b=>!b.uri));assert.equal(gltf.images?.length||0,0);
  const names=new Set();let total=0;
  for(const mesh of gltf.meshes){
    let triangles=0;
    for(const primitive of mesh.primitives){
      assert.equal(primitive.mode??4,4);assert.ok(primitive.indices!==undefined);assert.ok(primitive.attributes.COLOR_0!==undefined);
      triangles+=gltf.accessors[primitive.indices].count/3;
      const position=gltf.accessors[primitive.attributes.POSITION];assert.ok(position.min[1]>=-1e-5,'tree origin must be at the foot');
    }
    names.add(mesh.name);assert.ok(triangles<=400);assert.equal(triangles,manifest.triangles[mesh.name]);total+=triangles;
  }
  for(const species of ['camphor','plane','ginkgo','willow','pine','cedar','blossom'])for(const detail of ['full','compact'])assert.ok(names.has(species+'_'+detail));
  assert.equal(total,manifest.total_library_triangles);
});

test('rendered terrain resolves hilltops while retaining flat, continuous refinement boundaries',async()=>{
  const {createTerrainGeometry}=await import('../src/terrain-surface.js');
  const geometry=createTerrainGeometry(profile),p=geometry.attributes.position;
  assert.ok(geometry.index.count/3<150000,'refine hills, not the entire map');
  for(let i=0;i<p.count;i++)assert.ok(Math.abs(p.getY(i)-profile.height([p.getX(i)/SCALE+350,p.getZ(i)/SCALE+430])-.012)<1e-4);
  const edges=new Map();
  for(let i=0;i<geometry.index.count;i+=3)for(const [a,b] of [[0,1],[1,2],[2,0]]){
    const x=geometry.index.getX(i+a),y=geometry.index.getX(i+b),key=x<y?x+','+y:y+','+x;
    edges.set(key,(edges.get(key)||0)+1);
  }
  for(const [key,count] of edges)if(count===1){
    const [a,b]=key.split(',').map(Number);
    // Exterior and fine/coarse transition edges are all at the zero-height rim.
    assert.ok(Math.abs(p.getY(a)-.012)<1e-6&&Math.abs(p.getY(b)-.012)<1e-6,'a refinement edge can crack on a slope');
  }
  geometry.dispose();
});
