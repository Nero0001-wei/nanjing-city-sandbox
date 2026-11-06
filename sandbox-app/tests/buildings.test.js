import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {world} from '../src/geo.js';
import {createBuildingIndex,footprintCentre,footprintDistance} from '../src/building-footprints.js';
import {createTerrainProfile} from '../src/terrain-profile.js';
import {buildingGeometry} from '../src/buildings.js';
const load=p=>JSON.parse(readFileSync(new URL(p,import.meta.url)));
const buildings=load('../public/data/buildings.json'),raw=load('../data/building-footprints.json'),map=load('../public/data/nanjing.json');

test('white models retain actual source footprints and explicit height provenance',()=>{
  assert.equal(buildings.features.length,buildings.count);
  const signatures=new Set(raw.features.map(b=>JSON.stringify([b.id,b.outer,b.holes,b.height_m,b.height_source])));
  for(const b of buildings.features){
    assert.ok(signatures.has(JSON.stringify([b.id,b.outer,b.holes,b.height_m,b.height_source])));
    assert.ok(['osm_height','levels_estimate','type_estimate'].includes(b.height_source));
    assert.ok(b.height_m>0&&b.height_m<=600);
    for(const l of map.landmarks.filter(l=>l.id!=='xuanwu'))assert.ok(footprintDistance(l.source_px,b)>=17);
  }
  assert.ok(buildings.height_counts.osm_height>0&&buildings.height_counts.type_estimate>0);
});
test('building footprints and courtyard holes are preserved during extrusion',()=>{
  const b={outer:[[350,430],[360,430],[360,440],[350,440]],holes:[[[352,432],[358,432],[358,438],[352,438]]],bbox:[350,430,360,440],height_m:32.4};
  const g=buildingGeometry(b,{height:()=>0},buildings);g.computeBoundingBox();
  assert.ok(Math.abs(g.boundingBox.max.y-g.boundingBox.min.y-.6*buildings.vertical_exaggeration)<.0001);
  assert.ok(Math.abs(g.boundingBox.max.x-6)<.0001&&Math.abs(g.boundingBox.max.z-6)<.0001);
  const material=new THREE.MeshBasicMaterial({side:THREE.DoubleSide}),mesh=new THREE.Mesh(g,material);mesh.updateMatrixWorld();
  const ray=new THREE.Raycaster(new THREE.Vector3(3,10,3),new THREE.Vector3(0,-1,0));
  assert.equal(ray.intersectObject(mesh).length,0,'a courtyard must remain open');
  ray.ray.origin.set(.5,10,.5);assert.ok(ray.intersectObject(mesh).length>0,'building roof must exist');
  g.dispose();material.dispose();
});
test('trees avoid white-model footprints including crown clearance',()=>{
  const occupied=createBuildingIndex(buildings.features),profile=createTerrainProfile(map,occupied);
  const trees=profile.buildVegetation();assert.ok(trees.length>800);
  for(const tree of trees)assert.equal(occupied(tree.p,3.5),false);
});
test('an actual building renders at its source location without horizontal enlargement',()=>{
  const b=buildings.features[0],profile=createTerrainProfile(map),g=buildingGeometry(b,profile,buildings);g.computeBoundingBox();
  const [xmin,zmin]=world(b.bbox.slice(0,2)),[xmax,zmax]=world(b.bbox.slice(2));
  assert.ok(Math.abs(g.boundingBox.min.x-xmin)<.0001&&Math.abs(g.boundingBox.max.x-xmax)<.0001);
  assert.ok(Math.abs(g.boundingBox.min.z-zmin)<.0001&&Math.abs(g.boundingBox.max.z-zmax)<.0001);
  assert.ok(g.boundingBox.min.y>=profile.height(footprintCentre(b)));g.dispose();
});
