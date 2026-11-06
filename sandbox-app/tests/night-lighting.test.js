import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {setupLighting} from '../src/render-style.js';
import {addNightMaterial,createNightLighting,createNightTransition,landmarkLightStyle} from '../src/night-lighting.js';

test('night lighting returns exactly to daylight and retains cached PCF shadows',()=>{
  const scene=new THREE.Scene(),renderer={shadowMap:{autoUpdate:false}};
  const lighting=setupLighting(scene,renderer);lighting.setNight(0);
  const snapshot=()=>({lights:scene.children.map(o=>({color:o.color.toArray(),ground:o.groundColor?.toArray(),intensity:o.intensity,position:o.position.toArray()})),environment:scene.environmentIntensity,exposure:renderer.toneMappingExposure});
  const day=snapshot();lighting.setNight(1);
  assert.ok(scene.environmentIntensity<day.environment/4);
  assert.equal(renderer.shadowMap.type,THREE.PCFShadowMap);
  assert.equal(renderer.shadowMap.autoUpdate,false);
  for(let i=0;i<6;i++){lighting.setNight(.4);lighting.setNight(1);lighting.setNight(0);}
  assert.deepEqual(snapshot(),day);lighting();assert.equal(scene.children.length,0);
});

test('reversing a transition preserves continuity and reduced motion reaches its endpoint',()=>{
  const values=[],transition=createNightTransition(v=>values.push(v));
  transition.set(true);transition.update(.6);assert.equal(transition.value,.5);
  transition.set(false);assert.equal(transition.value,.5);
  transition.update(.6);assert.equal(transition.value,.25);
  transition.update(.6);assert.equal(transition.value,0);assert.equal(transition.active,false);
  transition.set(true,true);assert.equal(transition.value,1);
  transition.set(false);transition.update(.01,true);assert.equal(transition.value,0);
  assert.ok(values.every(v=>v>=0&&v<=1));
});

test('night materials retain texture and vertex AO hooks and share late-loading state',()=>{
  const lighting=createNightLighting(),material=new THREE.MeshStandardMaterial({vertexColors:true});
  material.name='灰蓝玻璃';const root=new THREE.Group(),geometry=new THREE.BoxGeometry();root.add(new THREE.Mesh(geometry,material));
  lighting.uniform.value=1;lighting.registerLandmark(root,'meiling');
  const shader={uniforms:{},vertexShader:THREE.ShaderLib.standard.vertexShader,fragmentShader:THREE.ShaderLib.standard.fragmentShader};
  material.onBeforeCompile(shader);
  assert.equal(shader.uniforms.uNight,lighting.uniform);
  for(const hook of ['map_fragment','color_fragment','lights_fragment_begin','emissivemap_fragment'])assert.ok(shader.fragmentShader.includes(`#include <${hook}>`));
  assert.equal(material.vertexColors,true);assert.equal(material.emissive.getHex(),0);
  lighting.uniform.value=0;assert.equal(shader.uniforms.uNight.value,0);
  const key=material.customProgramCacheKey();lighting.registerLandmark(root,'meiling');assert.equal(material.customProgramCacheKey(),key);
  material.dispose();geometry.dispose();
});

test('window shader filters small windows, masks roofs, and preserves prior material hooks',()=>{
  const material=new THREE.MeshStandardMaterial();
  material.onBeforeCompile=shader=>{shader.uniforms.previous={value:7};};
  addNightMaterial(material,{value:0},{color:0xffd39a,emission:1,windows:true});
  const shader={uniforms:{},vertexShader:THREE.ShaderLib.standard.vertexShader,fragmentShader:THREE.ShaderLib.standard.fragmentShader};
  material.onBeforeCompile(shader);assert.equal(shader.uniforms.previous.value,7);
  assert.ok(shader.fragmentShader.includes('roomMask(facadeUV) * facade'));
  assert.ok(shader.fragmentShader.includes('fwidth(grid)'));
  assert.ok(shader.fragmentShader.includes('roomRandom(floor(grid))'));
  material.dispose();
});

test('lamp globes, glass rooms and stone bases have separate lighting roles',()=>{
  assert.ok(landmarkLightStyle('yangtze-bridge','玉兰灯磨砂罩').emission>3);
  assert.equal(landmarkLightStyle('meiling','浅色铺石').emission,undefined);
  assert.ok(landmarkLightStyle('zifeng','蓝灰玻璃幕墙').windows);
  assert.notEqual(landmarkLightStyle('baoen','浅雾蓝玻璃面').color,landmarkLightStyle('meiling','灰蓝玻璃').color);
});
