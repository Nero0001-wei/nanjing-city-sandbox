import * as THREE from 'three';
import {BOUNDS,world} from './geo.js';

// An illustrative cutaway beneath the existing y=0 surface, not geological data.
// Layer boundaries share world-space samples so all four corners stay closed.
export const TERRAIN_BASE={top:0,depth:12.4,bottom:-12.4,bevel:.4,inset:.45};
const layers=[
  {depth:0,color:'#a2946d'},
  {depth:2.3,color:'#c5ad84'},
  {depth:6.8,color:'#a69c86'},
  {depth:12,color:'#928c7b'},
];

export function createTerrainBaseGeometry(){
  const [x0,z0]=world(BOUNDS.slice(0,2)),[x1,z1]=world(BOUNDS.slice(2));
  const corners=[[x0,z0],[x1,z0],[x1,z1],[x0,z1]],rim=[];
  for(let side=0;side<4;side++){
    const a=corners[side],b=corners[(side+1)%4],steps=Math.ceil(Math.hypot(b[0]-a[0],b[1]-a[1])/18);
    for(let i=0;i<steps;i++)rim.push([a[0]+(b[0]-a[0])*i/steps,a[1]+(b[1]-a[1])*i/steps]);
  }
  const centre=[(x0+x1)/2,(z0+z1)/2],positions=[],colors=[];
  function boundary(p,level){
    const [x,z]=p;
    if(level===0)return [x,TERRAIN_BASE.top,z];
    if(level===3)return [x,-12,z];
    const ripple=Math.sin(x*.025+z*.014+level)*.24+Math.sin(x*.067-z*.021)*.1;
    return [x,-layers[level].depth+ripple,z];
  }
  function lower(p){
    return [centre[0]+(p[0]-centre[0])*(1-2*TERRAIN_BASE.inset/(x1-x0)),TERRAIN_BASE.bottom,centre[1]+(p[1]-centre[1])*(1-2*TERRAIN_BASE.inset/(z1-z0))];
  }
  function triangle(a,b,c,color){
    for(const p of [a,b,c]){positions.push(...p);colors.push(color.r,color.g,color.b);}
  }
  function quad(a,b,c,d,color){triangle(a,b,c,color);triangle(a,c,d,color);}
  for(let i=0;i<rim.length;i++){
    const a=rim[i],b=rim[(i+1)%rim.length];
    for(let layer=0;layer<3;layer++)quad(boundary(a,layer),boundary(b,layer),boundary(b,layer+1),boundary(a,layer+1),new THREE.Color(layers[layer].color));
    quad(boundary(a,3),boundary(b,3),lower(b),lower(a),new THREE.Color(layers[3].color));
    triangle([centre[0],TERRAIN_BASE.top,centre[1]],boundary(b,0),boundary(a,0),new THREE.Color(layers[0].color));
    triangle([centre[0],TERRAIN_BASE.bottom,centre[1]],lower(a),lower(b),new THREE.Color(layers[3].color));
  }
  const geometry=new THREE.BufferGeometry();
  geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
  geometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
  geometry.computeVertexNormals();geometry.computeBoundingBox();geometry.computeBoundingSphere();
  return geometry;
}

export function addTerrainBase(scene){
  const base=new THREE.Mesh(createTerrainBaseGeometry(),new THREE.MeshStandardMaterial({vertexColors:true,roughness:.96}));
  base.name='layered-earth-base';base.receiveShadow=true;base.castShadow=false;
  base.userData={depth:TERRAIN_BASE.depth,layers:3,triangles:base.geometry.getAttribute('position').count/3,interpretation:'artistic cutaway'};
  scene.add(base);return base;
}
