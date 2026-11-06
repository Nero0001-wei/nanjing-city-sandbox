import * as THREE from 'three';
import {seededRandom} from './geo.js';

export const PALETTE={
  background:0xfcf9f0,water:0x65b9df,island:0xa1c573,
  grass:'#adc783',meadow:'#91b364',forest:'#659954',summit:'#a1bd70',
  sand:'#ded6b6',bank:'#a5bd79',shallow:'#89cdd9',
};

export function setupLighting(scene,renderer){
  // Neutral mapping keeps painted greens and cyan water from washing out.
  renderer.toneMapping=THREE.NeutralToneMapping;renderer.toneMappingExposure=1.04;
  renderer.outputColorSpace=THREE.SRGBColorSpace;
  renderer.shadowMap.enabled=true;
  // PCF compares a depth texture directly. The former half-float VSM moments
  // produced contour-like quantization on broad slopes on Apple Metal GPUs.
  renderer.shadowMap.type=THREE.PCFShadowMap;
  // Most indirect light now comes from the directional, prefiltered sky.
  // A small hemisphere lift leaves the undersides readable without flattening them.
  const sky=new THREE.HemisphereLight(0xe8f0ff,0xaaa58e,.18);scene.add(sky);
  const key=new THREE.DirectionalLight(0xfff5e8,2.25);key.name='soft-daylight-key';key.position.set(-150,240,160);key.castShadow=true;
  key.shadow.mapSize.set(2048,2048);Object.assign(key.shadow.camera,{left:-250,right:250,top:240,bottom:-240,near:1,far:700});
  key.shadow.radius=2.6;key.shadow.intensity=.9;key.shadow.bias=-.00008;key.shadow.normalBias=.12;
  scene.add(key);
  const fill=new THREE.DirectionalLight(0xdeebff,.28);fill.name='cool-sky-fill';fill.position.set(160,130,-150);scene.add(fill);
  // No moving shadow casters: update on initial loading or visibility changes.
  // Orbiting and panning can reuse the cached depth map.
  return ()=>{key.shadow.dispose();scene.remove(sky,key,fill);};
}

export function createGroundGrain(){
  const size=128,bytes=new Uint8Array(size*size*4),random=seededRandom(31029);
  for(let i=0;i<size*size;i++){
    const v=112+Math.floor(random()*32);bytes.set([v,v,v,255],i*4);
  }
  const texture=new THREE.DataTexture(bytes,size,size,THREE.RGBAFormat);
  texture.wrapS=texture.wrapT=THREE.RepeatWrapping;texture.magFilter=THREE.LinearFilter;
  texture.minFilter=THREE.LinearMipmapLinearFilter;texture.generateMipmaps=true;texture.anisotropy=4;texture.needsUpdate=true;
  return texture;
}
