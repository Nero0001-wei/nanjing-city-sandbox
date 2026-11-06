import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {setupLighting} from '../src/render-style.js';
import {addTerrainSurfaces} from '../src/terrain-surface.js';
import {createTerrainProfile} from '../src/terrain-profile.js';

test('hill ground receives external shadows without entering the shadow depth pass',()=>{
  const scene=new THREE.Scene(),renderer={shadowMap:{}},disposeLight=setupLighting(scene,renderer);
  const data=JSON.parse(readFileSync(new URL('../public/data/nanjing.json',import.meta.url)));
  const profile=createTerrainProfile(data),mat=(color,options)=>new THREE.MeshStandardMaterial({color,...options});
  const mesh=(g,m,parent=scene)=>{const o=new THREE.Mesh(g,m);o.receiveShadow=true;parent.add(o);return o;};
  const details=addTerrainSurfaces({scene,profile,mat,mesh});
  const terrain=scene.getObjectByName('continuous-city-terrain');
  // VSM renders receivers into its half-float moment map even with castShadow
  // disabled. Both choices are needed to prevent the reproduced Metal banding.
  assert.equal(renderer.shadowMap.type,THREE.PCFShadowMap);
  assert.equal(renderer.shadowMap.enabled,true);
  assert.equal(terrain.castShadow,false);
  assert.equal(terrain.receiveShadow,true);
  assert.equal(terrain.geometry.index.count/3,107402,'the fix must not densify or flatten the relief');
  assert.ok(scene.children.some(o=>o.isDirectionalLight&&o.castShadow),'external tree/building shadows stay enabled');
  scene.traverse(o=>{o.geometry?.dispose();o.material?.dispose();});details.dispose();disposeLight();
});
