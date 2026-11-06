import * as THREE from 'three';
import {SCALE} from './geo.js';

// Keep a level roof and extend each bottom vertex into the sloping terrain.
// The visible lower wall is a foundation; buildings never balance on one corner.
export function groundBuilding(geometry,profile,roofBase,depth){
  const p=geometry.attributes.position;
  const heights=Array.from({length:p.count},(_,i)=>profile.height([p.getX(i)/SCALE+350,p.getZ(i)/SCALE+430]));
  if(Math.max(...heights)-Math.min(...heights)<.001){geometry.translate(0,roofBase,0);return geometry;}
  for(let i=0;i<p.count;i++){
    const h=profile.height([p.getX(i)/SCALE+350,p.getZ(i)/SCALE+430]);
    p.setY(i,p.getY(i)<depth*.5?Math.min(roofBase,h+.015)-.10:roofBase+depth);
  }
  geometry.computeVertexNormals();return geometry;
}

// Subdivide long polygon triangles before draping parks and parcels. Without
// this, a large park triangle cuts through its hill even when its corners fit.
export function drapeSurface(geometry,profile,offset=.055){
  const input=geometry.index?geometry.toNonIndexed():geometry,src=input.attributes.position,positions=[],uvs=[];
  const pushTriangle=(a,b,c)=>{
    const ab=(a[0]-b[0])**2+(a[1]-b[1])**2,bc=(b[0]-c[0])**2+(b[1]-c[1])**2,ca=(c[0]-a[0])**2+(c[1]-a[1])**2;
    const max=Math.max(ab,bc,ca);
    if(max>1.2**2){
      if(max===bc)[a,b,c]=[b,c,a];else if(max===ca)[a,b,c]=[c,a,b];
      const m=[(a[0]+b[0])/2,(a[1]+b[1])/2];pushTriangle(a,m,c);pushTriangle(m,b,c);return;
    }
    for(const [x,z] of [a,b,c]){positions.push(x,profile.height([x/SCALE+350,z/SCALE+430])+offset,z);uvs.push(x,z);}
  };
  for(let i=0;i<src.count;i+=3){
    const points=[0,1,2].map(j=>[src.getX(i+j),src.getZ(i+j)]);
    // Flat parcels need no extra geometry at all.
    const sample=[...points,[(points[0][0]+points[1][0]+points[2][0])/3,(points[0][1]+points[1][1]+points[2][1])/3]];
    const bounds=[Math.min(...points.map(p=>p[0]))/SCALE+350,Math.min(...points.map(p=>p[1]))/SCALE+430,Math.max(...points.map(p=>p[0]))/SCALE+350,Math.max(...points.map(p=>p[1]))/SCALE+430];
    const touchesHill=profile.hills?.some(h=>bounds[0]<h.p[0]+Math.max(...h.radius)&&bounds[2]>h.p[0]-Math.max(...h.radius)&&bounds[1]<h.p[1]+Math.max(...h.radius)&&bounds[3]>h.p[1]-Math.max(...h.radius));
    if(touchesHill||sample.some(([x,z])=>profile.height([x/SCALE+350,z/SCALE+430])>.01))pushTriangle(...points);
    else for(const [x,z] of points){positions.push(x,offset,z);uvs.push(x,z);}
  }
  if(input!==geometry)input.dispose();geometry.dispose();
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uvs,2));g.computeVertexNormals();return g;
}
