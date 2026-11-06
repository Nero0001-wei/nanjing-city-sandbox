import * as THREE from 'three';
import {mergeGeometries} from 'three/addons/utils/BufferGeometryUtils.js';
import {world,SCALE,seededRandom} from './geo.js';
import {createBuildingIndex} from './building-footprints.js';
import {yangtzeFootprintDistance} from './landmark-placement.js';

const bounds=ring=>[Math.min(...ring.map(p=>p[0])),Math.min(...ring.map(p=>p[1])),Math.max(...ring.map(p=>p[0])),Math.max(...ring.map(p=>p[1]))];
export function createParcelIndex(urban){
  return createBuildingIndex((urban?.parcels||[]).map(p=>({...p,bbox:bounds(p.outer)})));
}
function shapeFor(p){
  const points=ring=>ring.map(p=>{const [x,z]=world(p);return new THREE.Vector2(x,-z);});
  const shape=new THREE.Shape(points(p.outer));
  for(const h of p.holes||[])shape.holes.push(new THREE.Path(points(h)));
  return shape;
}

export function addUrbanFabric({scene,profile,urban,mat}){
  const ground=new THREE.Group(),buildings=new THREE.Group();
  ground.name='urban-parcels';buildings.name='artistic-white-building-groups';scene.add(ground,buildings);
  if(!urban)return {ground,buildings};
  const surfaces=new Map();
  const palette={residential:['#d2cfb8','#d8d2bc','#cdd0ba','#d6d3c0'],courtyard:['#d4cbb6','#d9d1bd','#d2cab9','#ded6c2'],commercial:['#c9c9bd','#cecec4','#c4c8bd','#d0ccbf'],campus:['#cbd1ba','#d4d4bf','#ced1b9','#d6d3bc']};
  function surface(p,color,y){
    const g=new THREE.ShapeGeometry(shapeFor(p));g.rotateX(-Math.PI/2);g.translate(0,y,0);
    // Urban parcels are deliberately clipped away from the mountain relief.
    // Source-space coordinates are shared with road and building meshes.
    if(!surfaces.has(color))surfaces.set(color,[]);surfaces.get(color).push(g);
  }
  for(const p of urban.parcels)surface(p,(palette[p.kind]||palette.residential)[p.tone],.032);
  for(const p of urban.parks)surface(p,'#96b36e',.033);
  for(const p of urban.lawns)surface(p,'#a0bc76',.042);
  for(const [color,geometries] of surfaces){
    const g=mergeGeometries(geometries);geometries.forEach(g=>g.dispose());
    const mesh=new THREE.Mesh(g,mat(color,{roughness:.96,shadowSide:THREE.BackSide}));mesh.receiveShadow=true;ground.add(mesh);
  }
  const batches=new Map();
  for(const b of urban.buildings){
    const geometry=new THREE.ExtrudeGeometry(shapeFor(b),{depth:b.height,bevelEnabled:false,steps:1,curveSegments:1});
    geometry.rotateX(-Math.PI/2);geometry.translate(0,profile.height(b.p)+.055,0);geometry.clearGroups();
    const key=Math.floor(b.p[0]/80)+','+Math.floor(b.p[1]/80);
    if(!batches.has(key))batches.set(key,[]);batches.get(key).push(geometry);
    // A shallow roof step adds a readable silhouette without facade details.
    if(b.template==='office'){
      const roof=new THREE.BoxGeometry(b.width*SCALE*.72,.12,b.depth*SCALE*.72).toNonIndexed();
      roof.rotateY(-b.angle*Math.PI/180);const [x,z]=world(b.p);roof.translate(x,profile.height(b.p)+b.height+.11,z);roof.clearGroups();batches.get(key).push(roof);
    }
  }
  for(const geometries of batches.values()){
    const g=mergeGeometries(geometries);geometries.forEach(g=>g.dispose());
    const mesh=new THREE.Mesh(g,mat(0xeeeae1,{roughness:.91}));mesh.castShadow=true;mesh.receiveShadow=true;buildings.add(mesh);
  }
  return {ground,buildings};
}

export function buildCityVegetation(profile,urban){
  const clearsBridge=tree=>yangtzeFootprintDistance(tree.p)>=3.5;
  if(!urban)return profile.buildVegetation().filter(clearsBridge);
  const parcelAt=createParcelIndex(urban),random=seededRandom(76189),planned=[],bins=new Map(),cell=3;
  const key=p=>Math.floor(p[0]/cell)+','+Math.floor(p[1]/cell);
  for(const tree of urban.trees){
    const p=tree.p;
    if(profile.isWater(p)||profile.landmarkDistance(p)<17||profile.occupied(p,1.35)||profile.height(p)>.4)continue;
    const entry={...tree,y:profile.height(p)+.045,color:random(),pine:false};planned.push(entry);
    const k=key(p);if(!bins.has(k))bins.set(k,[]);bins.get(k).push(p);
  }
  function nearPlanted(p){
    const x=Math.floor(p[0]/cell),y=Math.floor(p[1]/cell);
    for(let i=x-1;i<=x+1;i++)for(let j=y-1;j<=y+1;j++)if((bins.get(i+','+j)||[]).some(q=>Math.hypot(p[0]-q[0],p[1]-q[1])<3))return true;
    return false;
  }
  const natural=profile.buildVegetation().filter(t=>!nearPlanted(t.p)).map(t=>{
    const urbanTree=parcelAt(t.p),mountain=profile.mountainMask(t.p)>.08;
    return {...t,size:urbanTree?Math.min(.52,t.size*.38):mountain?t.size:t.size*.78,y:t.y+(urbanTree?.045:0),kind:urbanTree?'garden':'natural'};
  });
  return [...natural,...planned].filter(clearsBridge);
}
