import {MathUtils,Spherical,Vector3} from 'three';

const ease=t=>{t=MathUtils.clamp(t,0,1);return t*t*t*(t*(t*6-15)+10);};

// Animate the complete view together. Spherical offsets keep the camera above
// the map and take the short route when the user has rotated past north.
export function createCameraMotion(camera,controls,reducedMotion=()=>false){
  let flight=null;
  const orbit=new Spherical(),offset=new Vector3();

  function cancel(){
    if(flight)controls.enableDamping=flight.damping;
    flight=null;
  }

  function update(dt){
    if(!flight)return;
    const f=flight;
    f.elapsed+=Math.max(0,dt);
    const t=reducedMotion()||f.duration===0?1:Math.min(1,f.elapsed/f.duration);
    const pan=ease(t),zoom=ease((t-.08)/.92);
    controls.target.lerpVectors(f.from.target,f.to.target,pan);
    orbit.radius=MathUtils.lerp(f.from.orbit.radius,f.to.orbit.radius,pan);
    orbit.phi=MathUtils.lerp(f.from.orbit.phi,f.to.orbit.phi,pan);
    orbit.theta=f.from.orbit.theta+f.angle*pan;
    camera.position.copy(controls.target).add(offset.setFromSpherical(orbit));
    camera.zoom=Math.exp(MathUtils.lerp(Math.log(f.from.zoom),Math.log(f.to.zoom),zoom));
    if(t===1){
      controls.target.copy(f.to.target);
      camera.position.copy(f.to.target).add(f.to.offset);
      camera.zoom=f.to.zoom;
      cancel();
    }
    camera.lookAt(controls.target);
    camera.updateProjectionMatrix();
  }

  function moveTo({target,offset:nextOffset,zoom,duration,zoomOnly=false}){
    cancel();
    const from={target:controls.target.clone(),position:camera.position.clone(),zoom:camera.zoom};
    from.orbit=new Spherical().setFromVector3(from.position.clone().sub(from.target));
    const to={target:target.clone(),offset:nextOffset.clone(),zoom:MathUtils.clamp(zoom,controls.minZoom,controls.maxZoom)};
    to.orbit=new Spherical().setFromVector3(to.offset);
    to.orbit.phi=MathUtils.clamp(to.orbit.phi,controls.minPolarAngle,controls.maxPolarAngle);
    to.orbit.makeSafe();to.offset.setFromSpherical(to.orbit);

    // Drain any mouse-drag inertia through the public controls API, then put
    // the visible pose back before the next frame. A new flight never snaps.
    const damping=controls.enableDamping;
    controls.enableDamping=false;controls.update();
    controls.target.copy(from.target);camera.position.copy(from.position);camera.zoom=from.zoom;
    camera.updateProjectionMatrix();controls.update();

    const distance=from.target.distanceTo(to.target);
    flight={from,to,damping,zoomOnly,elapsed:0,
      duration:duration??MathUtils.clamp(1.05+distance*.0015+Math.abs(Math.log(to.zoom/from.zoom))*.15,1.1,1.6),
      angle:Math.atan2(Math.sin(to.orbit.theta-from.orbit.theta),Math.cos(to.orbit.theta-from.orbit.theta))};
    if(reducedMotion()||flight.duration===0)update(0);
  }

  controls.addEventListener('start',cancel);
  function zoomBy(factor){
    const zoom=(flight?.zoomOnly?flight.to.zoom:camera.zoom)*factor;
    moveTo({target:controls.target,offset:camera.position.clone().sub(controls.target),zoom,duration:.32,zoomOnly:true});
  }

  return {moveTo,update,cancel,zoomBy,get active(){return flight!==null;},
    dispose(){cancel();controls.removeEventListener('start',cancel);}};
}
