import test from 'node:test';
import assert from 'node:assert/strict';
import {OrthographicCamera,Spherical,Vector3} from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {createCameraMotion} from '../src/camera-motion.js';

function rig(reduced=()=>false){
  const camera=new OrthographicCamera(-200,200,160,-160,1,1800);
  camera.position.set(70,370,360);
  const controls=new OrbitControls(camera);
  controls.enableDamping=true;controls.minZoom=.75;controls.maxZoom=16;
  controls.maxPolarAngle=Math.PI*.46;
  const motion=createCameraMotion(camera,controls,reduced);
  return {camera,controls,motion,step(dt){motion.update(dt);controls.update();}};
}
const near=(a,b)=>assert.ok(a.distanceTo(b)<1e-7,`${a.toArray()} != ${b.toArray()}`);
const destination={target:new Vector3(90,3,-50),offset:new Vector3(260,230,330),zoom:7,duration:1.4};

test('selection eases position, angle and zoom together without an initial jump or a final drift',()=>{
  const r=rig(),start=r.camera.position.clone();
  r.motion.moveTo(destination);
  near(r.camera.position,start);near(r.controls.target,new Vector3());assert.equal(r.camera.zoom,1);
  r.step(.1);
  assert.ok(r.controls.target.length()>0&&r.controls.target.length()<destination.target.length()*.02,'gentle start');
  r.step(.6);
  assert.ok(r.camera.zoom>1&&r.camera.zoom<7,'zoom must be in progress, not snap to close-up');
  assert.ok(r.controls.target.distanceTo(destination.target)>1,'pan must still be in progress');
  r.step(.7);
  near(r.controls.target,destination.target);near(r.camera.position,destination.target.clone().add(destination.offset));
  assert.equal(r.camera.zoom,7);assert.equal(r.motion.active,false);assert.equal(r.controls.enableDamping,true);
  r.step(.5);near(r.camera.position,destination.target.clone().add(destination.offset));
});

test('a second selection starts at the visible pose and manual input cancels the entire flight',()=>{
  const r=rig();r.motion.moveTo(destination);r.step(.55);
  const position=r.camera.position.clone(),target=r.controls.target.clone(),zoom=r.camera.zoom;
  r.motion.moveTo({...destination,target:new Vector3(-100,10,70),zoom:11});
  near(r.camera.position,position);near(r.controls.target,target);assert.equal(r.camera.zoom,zoom);
  r.step(.4);
  const interrupted=r.camera.position.clone(),interruptedZoom=r.camera.zoom;
  r.controls.dispatchEvent({type:'start'});r.step(3);
  near(r.camera.position,interrupted);assert.equal(r.camera.zoom,interruptedZoom);
  assert.equal(r.motion.active,false);assert.equal(r.controls.enableDamping,true);
});

test('residual drag inertia cannot move the camera at the start or after a cancelled flight',()=>{
  const r=rig();r.controls.rotateLeft(.5);
  const position=r.camera.position.clone();
  r.motion.moveTo(destination);near(r.camera.position,position);
  r.motion.cancel();
  for(let i=0;i<20;i++)r.step(1/60);
  near(r.camera.position,position);assert.equal(r.controls.enableDamping,true);
});

test('rotating across the azimuth seam takes the short arc above the map',()=>{
  const r=rig();r.camera.position.setFromSpherical(new Spherical(500,.8,Math.PI-.04));r.controls.update();
  r.motion.moveTo({target:new Vector3(),offset:new Vector3().setFromSpherical(new Spherical(500,.8,-Math.PI+.04)),zoom:1,duration:1});
  r.step(.5);
  assert.ok(r.camera.position.z<-300,'must not circle around the front of the map');
  assert.ok(r.camera.position.y>300);assert.ok(Math.abs(r.camera.position.length()-500)<1e-7);
});

test('reduced motion finishes immediately, including when enabled during a flight; zoom limits remain usable',()=>{
  let reduced=true;const r=rig(()=>reduced);
  r.motion.moveTo({...destination,zoom:16});r.controls.update();
  near(r.controls.target,destination.target);assert.equal(r.camera.zoom,16);assert.equal(r.motion.active,false);
  reduced=false;r.motion.moveTo({...destination,target:new Vector3(),zoom:.5});r.step(.2);
  assert.equal(r.motion.active,true);
  reduced=true;r.step(.01);
  near(r.controls.target,new Vector3());assert.equal(r.camera.zoom,.75);assert.equal(r.motion.active,false);
});

test('motion follows elapsed time rather than refresh rate',()=>{
  const a=rig(),b=rig();a.motion.moveTo(destination);b.motion.moveTo(destination);
  for(let i=0;i<30;i++)a.step(1/60);
  for(let i=0;i<15;i++)b.step(1/30);
  near(a.camera.position,b.camera.position);near(a.controls.target,b.controls.target);
  assert.ok(Math.abs(a.camera.zoom-b.camera.zoom)<1e-10);
});

test('rapid zoom clicks accumulate, while zooming during a flight keeps the visible location',()=>{
  const r=rig();r.motion.zoomBy(1.3);r.step(.08);r.motion.zoomBy(1.3);r.step(.32);
  assert.ok(Math.abs(r.camera.zoom-1.69)<1e-10);
  r.motion.moveTo(destination);r.step(.5);
  const target=r.controls.target.clone(),zoom=r.camera.zoom;
  r.motion.zoomBy(1.3);r.step(.32);
  near(r.controls.target,target);assert.ok(Math.abs(r.camera.zoom-zoom*1.3)<1e-10);
  r.motion.zoomBy(100);r.step(.32);assert.equal(r.camera.zoom,16);
});
