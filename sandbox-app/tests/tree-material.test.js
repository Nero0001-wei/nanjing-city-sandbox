import test from 'node:test';
import assert from 'node:assert/strict';
import {ShaderLib,ShaderChunk} from 'three';
import {createTreeMaterial} from '../src/tree-material.js';

// Exercise the real installed shader source. Ordinary geometry tests do not
// compile materials, so they missed the removed r186 diffuse hook on upgrade.
test('tree lighting integrates with the installed Physical shader and preserves EON',()=>{
  const original=ShaderChunk.lights_physical_pars_fragment;
  const shader={vertexShader:ShaderLib.physical.vertexShader,fragmentShader:ShaderLib.physical.fragmentShader,uniforms:{}};
  const material=createTreeMaterial();
  assert.doesNotThrow(()=>material.onBeforeCompile(shader));
  assert.equal(ShaderChunk.lights_physical_pars_fragment,original,'other materials must retain Three.js lighting');
  assert.equal(material.vertexColors,true);
  assert.equal(material.isMeshPhysicalMaterial,true);
  assert.ok(material.diffuseRoughness>0,'enable r187 rough diffuse instead of the default Lambert path');
  assert.equal(material.emissive.getHex(),0);
  assert.ok(shader.vertexShader.includes('vTreePosition = position;'));
  assert.ok(shader.fragmentShader.includes('#include <lights_physical_pars_fragment>'),'preserve native EON and its supported incident-light hemisphere');
  assert.ok(original.includes('vec3 diffuseBRDF = BRDF_EON('));
  assert.ok(original.includes('EON_DirectionalAlbedo( material.diffuseColor'));
  assert.ok(shader.fragmentShader.includes('#include <lights_fragment_begin>'),'real light and shadow evaluation stays enabled');
  assert.ok(shader.fragmentShader.includes('treeFootprint'),'small crowns retain filtered detail');
  material.dispose();
});
