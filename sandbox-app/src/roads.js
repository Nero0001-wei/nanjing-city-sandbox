import * as THREE from 'three';
import {BOUNDS,SCALE,world,clipSegment,segmentDistance} from './geo.js';
import {buildRoadProfiles,roadWidth,ROAD_WHITE} from './road-network.js';
import {createRoadLayout} from './road-clearance.js';
import {hasBridgeSupport} from './landmark-placement.js';

export function addWhiteRoads({scene,data,profile,mat,layout=createRoadLayout(data)}){
  const profiles=buildRoadProfiles(layout.roads,profile.height,layout),solid=[],tunnel=[],columns=[],caps=new Map();
  const inside=p=>p[0]>=BOUNDS[0]&&p[0]<=BOUNDS[2]&&p[1]>=BOUNDS[1]&&p[1]<=BOUNDS[3];
  const tri=(out,a,b,c)=>out.push(...a,...b,...c);
  const quad=(out,a,b,c,d)=>{tri(out,a,b,c);tri(out,a,c,d);};
  const mix=(a,b,t)=>a.map((v,i)=>v+(b[i]-v)*t);
  const groundBins=new Map(),cell=8;
  // Piers avoid other surface roads and tunnel alignments at crossings.
  for(const {points,road} of profiles)for(let i=1;i<points.length;i++){
    const a=points[i-1],b=points[i];if(road.kind!=='tunnel'&&Math.min(a.lift,b.lift)>.4)continue;
    for(let x=Math.floor(Math.min(a.p[0],b.p[0])/cell);x<=Math.floor(Math.max(a.p[0],b.p[0])/cell);x++)for(let y=Math.floor(Math.min(a.p[1],b.p[1])/cell);y<=Math.floor(Math.max(a.p[1],b.p[1])/cell);y++){
      const key=x+','+y;if(!groundBins.has(key))groundBins.set(key,[]);groundBins.get(key).push([a.p,b.p]);
    }
  }
  function pierBlocked(p){
    if(layout.pierBlocked(p))return true;
    const x=Math.floor(p[0]/cell),y=Math.floor(p[1]/cell);
    for(let dx=-1;dx<=1;dx++)for(let dy=-1;dy<=1;dy++)for(const [a,b] of groundBins.get((x+dx)+','+(y+dy))||[])if(segmentDistance(p,a,b)<1.5)return true;
    return columns.some(c=>Math.hypot(c.p[0]-p[0],c.p[1]-p[1])<6);
  }
  for(const {road,points} of profiles){
    const underground=road.kind==='tunnel',width=underground?.3:roadWidth(road);
    // A single pair of mitered vertices at every bend makes a watertight ribbon.
    const edges=points.map((n,i)=>{
      const p=world(n.p),before=world(points[Math.max(0,i-1)].p),after=world(points[Math.min(points.length-1,i+1)].p);
      const normal=(a,b)=>{const dx=b[0]-a[0],dz=b[1]-a[1],l=Math.hypot(dx,dz)||1;return [-dz/l,dx/l];};
      const a=normal(i?before:p,i?p:after),b=normal(i===points.length-1?before:p,i===points.length-1?p:after);
      let nx=a[0]+b[0],nz=a[1]+b[1],l=Math.hypot(nx,nz);if(l<.001){nx=b[0];nz=b[1];l=1;}nx/=l;nz/=l;
      const radius=Math.min(width,width/2/Math.max(.5,nx*b[0]+nz*b[1]));
      const edge=sign=>{
        const x=p[0]+sign*nx*radius,z=p[1]+sign*nz*radius;
        const terrain=profile.height([x/SCALE+350,z/SCALE+430])-profile.height(n.p);
        return [x,n.y+terrain*Math.max(0,1-n.lift/.5),z];
      };
      return [edge(1),edge(-1)];
    });
    let travelled=0,nextPier=12;
    for(let i=1;i<points.length;i++){
      const a=points[i-1],b=points[i],length=Math.hypot(b.p[0]-a.p[0],b.p[1]-a.p[1]);
      const clipped=clipSegment(a.p,b.p);
      if(clipped){
        const lo=Math.hypot(clipped[0][0]-a.p[0],clipped[0][1]-a.p[1])/length;
        const hi=Math.hypot(clipped[1][0]-a.p[0],clipped[1][1]-a.p[1])/length;
        const draw=(start,end,out)=>{
          const left0=mix(edges[i-1][0],edges[i][0],start),right0=mix(edges[i-1][1],edges[i][1],start);
          const left1=mix(edges[i-1][0],edges[i][0],end),right1=mix(edges[i-1][1],edges[i][1],end);
          quad(out,left0,left1,right1,right0);
          if(underground||Math.max(a.lift,b.lift)<.25)return;
          const thickness0=.09,thickness1=.09;
          const down=(p,t)=>[p[0],p[1]-t,p[2]];
          quad(out,left1,left0,down(left0,thickness0),down(left1,thickness1));
          quad(out,right0,right1,down(right1,thickness1),down(right0,thickness0));
          quad(out,down(left0,thickness0),down(right0,thickness0),down(right1,thickness1),down(left1,thickness1));
        };
        // A thin, continuous surface guide keeps tunnel routes readable without
        // building a raised deck over a lake or leaving apparent missing roads.
        draw(lo,hi,underground?tunnel:solid);
      }
      if(!underground)while(nextPier<=travelled+length){
        const t=(nextPier-travelled)/length,p=mix(a.p,b.p,t),lift=a.lift+(b.lift-a.lift)*t;
        const y=a.y+(b.y-a.y)*t,ground=profile.height(p);
        if(lift>.8&&inside(p)&&!hasBridgeSupport(p,road.name)&&!pierBlocked(p))columns.push({p,y:ground,height:y-ground-.19,width});
        nextPier+=24;
      }
      travelled+=length;
    }
    for(const n of points){
      if(!inside(n.p)||!(n.ends||n.edges.size>2))continue;
      const old=caps.get(n.id);if(!old||old.width<width)caps.set(n.id,{n,width});
    }
  }
  // Shared-node junction discs seal joins between separate OSM ways of unequal
  // widths. No discs are created where roads only cross in plan.
  for(const {n,width} of caps.values()){
    const [x,z]=world(n.p),centre=[x,n.y+.002,z],radius=width/2;
    for(let i=0;i<8;i++){
      const vertex=k=>{const a=k/8*Math.PI*2;return [x+Math.cos(a)*radius,n.y+.002,z+Math.sin(a)*radius];};
      const a=vertex(i),b=vertex(i+1),depth=.09;
      tri(n.tunnel?tunnel:solid,centre,b,a);if(n.lift>.25)quad(solid,a,b,[b[0],b[1]-depth,b[2]],[a[0],a[1]-depth,a[2]]);
    }
  }
  const group=new THREE.Group();group.name='white-road-network';scene.add(group);
  // Decks have outward-facing walls and undersides. Culling their back faces
  // avoids fine interference where widened, adjacent carriageways overlap.
  const material=mat(ROAD_WHITE,{side:THREE.FrontSide,shadowSide:THREE.FrontSide,roughness:.94});
  const tunnelMaterial=mat(ROAD_WHITE,{side:THREE.FrontSide,roughness:.94,transparent:true,opacity:.65,depthWrite:false});
  for(const [name,positions] of [['road-decks',solid],['underground-alignments',tunnel]]){
    const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geometry.computeVertexNormals();
    const mesh=new THREE.Mesh(geometry,name==='road-decks'?material:tunnelMaterial);mesh.name=name;mesh.receiveShadow=true;mesh.castShadow=name==='road-decks';group.add(mesh);
  }
  const piers=new THREE.InstancedMesh(new THREE.CylinderGeometry(.14,.18,1,6),material,columns.length),dummy=new THREE.Object3D();
  columns.forEach((c,i)=>{const [x,z]=world(c.p);dummy.position.set(x,c.y+c.height/2,z);dummy.scale.set(1,c.height,1);dummy.updateMatrix();piers.setMatrixAt(i,dummy.matrix);});
  piers.castShadow=true;piers.receiveShadow=true;piers.name='viaduct-piers';group.add(piers);
  return {group,pierCount:columns.length,profiles,layout};
}
