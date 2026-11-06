import * as THREE from 'three';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {UnrealBloomPass} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';

// Allocated only on the first night view and reused across mode changes.
// Daylight uses the original direct renderer, with no postprocessing passes.
export function createNightBloom(renderer,scene,camera){
  const size=renderer.getSize(new THREE.Vector2());
  const target=new THREE.WebGLRenderTarget(size.x,size.y,{type:THREE.HalfFloatType,samples:Math.min(4,renderer.capabilities.maxSamples)});
  const composer=new EffectComposer(renderer,target),render=new RenderPass(scene,camera);
  const bloom=new UnrealBloomPass(size,.28,.55,1),output=new OutputPass();
  composer.addPass(render);composer.addPass(bloom);composer.addPass(output);
  composer.setSize(size.x,size.y);
  return {
    render(amount){bloom.strength=.28*amount;composer.render();},
    resize(w,h){composer.setSize(w,h);},
    dispose(){render.dispose();bloom.dispose();output.dispose();composer.dispose();},
  };
}
