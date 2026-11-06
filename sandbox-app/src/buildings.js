import * as THREE from 'three';
import {mergeGeometries} from 'three/addons/utils/BufferGeometryUtils.js';
import {world,SCALE} from './geo.js';
import {groundBuilding} from './grounding.js';
import {footprintCentre} from './building-footprints.js';

export function buildingGeometry(b,profile,settings){
  const points=ring=>ring.map(p=>{const [x,z]=world(p);return new THREE.Vector2(x,-z);});
  const shape=new THREE.Shape(points(b.outer));
  for(const hole of b.holes)shape.holes.push(new THREE.Path(points(hole)));
  const height=b.height_m/settings.metres_per_source_pixel*SCALE*settings.vertical_exaggeration;
  const geometry=new THREE.ExtrudeGeometry(shape,{depth:height,bevelEnabled:false,steps:1,curveSegments:1});
  geometry.rotateX(-Math.PI/2);
  const base=Math.max(profile.height(footprintCentre(b)),...b.outer.map(p=>profile.height(p)))+.055;
  groundBuilding(geometry,profile,base,height);geometry.clearGroups();
  return geometry;
}

export function addWhiteBuildings({scene,profile,data,mat}){
  const group=new THREE.Group();group.name='OSM building footprints';scene.add(group);
  // Small batches avoid one draw call per building while retaining inexpensive culling.
  const batches=new Map();
  for(const b of data.features){const p=footprintCentre(b),key=Math.floor(p[0]/70)+','+Math.floor(p[1]/70);if(!batches.has(key))batches.set(key,[]);batches.get(key).push(b);}
  const material=mat(0xebebe5,{roughness:.92});
  for(const buildings of batches.values()){
    const geometries=buildings.map(b=>buildingGeometry(b,profile,data));
    const merged=mergeGeometries(geometries);geometries.forEach(g=>g.dispose());
    const mesh=new THREE.Mesh(merged,material);mesh.receiveShadow=true;mesh.castShadow=true;group.add(mesh);
  }
  return group;
}
