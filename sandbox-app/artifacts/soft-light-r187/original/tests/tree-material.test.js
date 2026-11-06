import test from 'node:test';
import assert from 'node:assert/strict';
import {MeshStandardMaterial,ShaderLib,ShaderChunk} from 'three';
import {createTreeMaterial} from '../src/tree-material.js';

// Exercise the real installed shader source. Ordinary geometry tests do not
// compile materials, so they missed the removed r186 diffuse hook on upgrade.
test('tree lighting integrates with the installed Standard shader and preserves its BRDF',()=>{
  const original=ShaderChunk.lights_physical_pars_fragment;
  const shader={vertexShader:ShaderLib.standard.vertexShader,fragmentShader:ShaderLib.standard.fragmentShader,uniforms:{}};
  const material=createTreeMaterial((color,options)=>new MeshStandardMaterial({color,...options}));
  assert.doesNotThrow(()=>material.onBeforeCompile(shader));
  assert.equal(ShaderChunk.lights_physical_pars_fragment,original,'other materials must retain Three.js lighting');
  assert.equal(material.vertexColors,true);
  assert.equal(material.emissive.getHex(),0);
  assert.ok(shader.vertexShader.includes('vTreePosition = position;'));
  assert.equal((shader.fragmentShader.match(/vec3 treeIrradiance =/g)||[]).length,1);
  assert.match(shader.fragmentShader,/treeIrradiance\s*\*\s*diffuseBRDF/);
  assert.ok(shader.fragmentShader.includes('#include <lights_fragment_begin>'),'real light and shadow evaluation stays enabled');
  assert.ok(shader.fragmentShader.includes('treeFootprint'),'small crowns retain filtered detail');
  assert.ok(!shader.fragmentShader.includes('#include <lights_physical_pars_fragment>'),'the validated chunk was actually installed');
  material.dispose();
});
