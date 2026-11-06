import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {createSkyTexture} from '../src/sky-environment.js';

test('procedural sky has finite linear HDR radiance and a dim ground hemisphere',()=>{
  const texture=createSkyTexture(),{data,width,height}=texture.image;
  assert.equal(texture.mapping,THREE.EquirectangularReflectionMapping);
  assert.equal(texture.colorSpace,THREE.LinearSRGBColorSpace);
  assert.ok(data.every(Number.isFinite));
  let sky=0,ground=0,peak=0;
  for(let y=0;y<height;y++)for(let x=0;x<width;x++){
    const i=(y*width+x)*4,luminance=data[i]*.2126+data[i+1]*.7152+data[i+2]*.0722;
    assert.ok(luminance>=0);assert.equal(data[i+3],1);
    if(y<height/4)ground+=luminance;
    if(y>=height*3/4)sky+=luminance;
    peak=Math.max(peak,data[i],data[i+1],data[i+2]);
  }
  assert.ok(sky>ground*3,'undersides should not receive the full sky radiance');
  assert.ok(peak>1,'preserve broad-source HDR values until tone mapping');
  texture.dispose();
});
