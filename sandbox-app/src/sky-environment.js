import * as THREE from 'three';

// A broad cloud-lit sky, in linear radiance. The lower hemisphere is deliberately
// dimmer so open undersides retain depth instead of receiving a uniform ambient wash.
// Generated locally: no HDR download and no extra textures in the model assets.
export function createSkyTexture(){
  const width=512,height=256,pixels=new Float32Array(width*height*4);
  const sun=new THREE.Vector3(-150,240,160).normalize();
  const horizon=new THREE.Color().setRGB(.72,.75,.78);
  const zenith=new THREE.Color().setRGB(.43,.58,.78);
  const ground=new THREE.Color().setRGB(.10,.12,.09);
  const light=new THREE.Color().setRGB(1,.91,.76),color=new THREE.Color();
  for(let y=0;y<height;y++){
    const latitude=((y+.5)/height-.5)*Math.PI,up=Math.sin(latitude),ring=Math.cos(latitude);
    for(let x=0;x<width;x++){
      const longitude=((x+.5)/width-.5)*Math.PI*2;
      const dx=ring*Math.cos(longitude),dz=ring*Math.sin(longitude);
      color.copy(horizon);
      if(up>=0)color.lerp(zenith,Math.pow(up,.65));
      else color.lerp(ground,Math.min(1,-up*3));
      const facing=Math.max(0,dx*sun.x+up*sun.y+dz*sun.z);
      const glow=1.25*Math.pow(facing,9);
      color.r+=light.r*glow;color.g+=light.g*glow;color.b+=light.b*glow;
      const i=(y*width+x)*4;
      pixels.set([color.r,color.g,color.b,1],i);
    }
  }
  const texture=new THREE.DataTexture(pixels,width,height,THREE.RGBAFormat,THREE.FloatType);
  texture.name='cloudy-miniature-sky';
  texture.mapping=THREE.EquirectangularReflectionMapping;
  texture.colorSpace=THREE.LinearSRGBColorSpace;
  texture.magFilter=texture.minFilter=THREE.LinearFilter;
  texture.needsUpdate=true;
  return texture;
}

export function setupSkyEnvironment(scene,renderer){
  const source=createSkyTexture(),generator=new THREE.PMREMGenerator(renderer);
  // r187 prefilters into a cube render target. Bake once; reuse at every view.
  let target;
  try{target=generator.fromEquirectangular(source);}
  finally{source.dispose();generator.dispose();}
  const previous=scene.environment,previousIntensity=scene.environmentIntensity;
  scene.environment=target.texture;scene.environmentIntensity=.72;
  return ()=>{
    if(scene.environment===target.texture){scene.environment=previous;scene.environmentIntensity=previousIntensity;}
    target.dispose();
  };
}
