import * as THREE from 'three';
import {mergeGeometries} from 'three/addons/utils/BufferGeometryUtils.js';
import {world,SCALE,segmentDistance,pointInPolygon} from './geo.js';

// Spatial clearance uses source coordinates, including the original wall gaps.
export function createWallIndex(data){
  const bins=new Map(),cell=16,items=[];
  for(const f of data?.features||[]){
    if(f.kind==='line')for(let i=1;i<f.source_px.length;i++)items.push({a:f.source_px[i-1],b:f.source_px[i],radius:f.width/2});
    else items.push({outer:f.outer,holes:f.holes,radius:.3});
  }
  for(const g of data?.gates||[])items.push({outer:g.display_outer||g.outer,holes:[],radius:.5});
  for(const item of items){
    const ps=item.outer||[item.a,item.b],r=item.radius;
    const bounds=[Math.min(...ps.map(p=>p[0]))-r,Math.min(...ps.map(p=>p[1]))-r,Math.max(...ps.map(p=>p[0]))+r,Math.max(...ps.map(p=>p[1]))+r];
    for(let x=Math.floor(bounds[0]/cell);x<=Math.floor(bounds[2]/cell);x++)for(let y=Math.floor(bounds[1]/cell);y<=Math.floor(bounds[3]/cell);y++){
      const key=x+','+y;if(!bins.has(key))bins.set(key,[]);bins.get(key).push(item);
    }
  }
  return (p,padding=0)=>{
    const seen=new Set();
    for(let x=Math.floor((p[0]-padding)/cell);x<=Math.floor((p[0]+padding)/cell);x++)for(let y=Math.floor((p[1]-padding)/cell);y<=Math.floor((p[1]+padding)/cell);y++){
      for(const item of bins.get(x+','+y)||[]){
        if(seen.has(item))continue;seen.add(item);
        if(item.a){if(segmentDistance(p,item.a,item.b)<=item.radius+padding)return true;}
        else{
          if(pointInPolygon(p,item.outer)&&!item.holes.some(h=>pointInPolygon(p,h)))return true;
          for(const ring of [item.outer,...item.holes])for(let i=0;i<ring.length;i++)if(segmentDistance(p,ring[i],ring[(i+1)%ring.length])<=item.radius+padding)return true;
        }
      }
    }
    return false;
  };
}

const WALL_COLOR=0x9b9c88,TOP_COLOR=0xb4b29b;
export function addCityWalls({scene,profile,data,mat}){
  const group=new THREE.Group();group.name='Nanjing Ming city wall';scene.add(group);
  if(!data)return group;
  const stone=[],caps=[],merlons=[],dummy=new THREE.Object3D();
  const addBox=(list,w,h,d,x,y,z,angle=0)=>{
    const g=new THREE.BoxGeometry(w,h,d).toNonIndexed();g.rotateY(angle);g.translate(x,y,z);g.clearGroups();list.push(g);
  };
  const makeShape=p=>{
    const points=ring=>ring.map(p=>{const [x,z]=world(p);return new THREE.Vector2(x,-z);});
    const shape=new THREE.Shape(points(p.outer));for(const h of p.holes||[])shape.holes.push(new THREE.Path(points(h)));return shape;
  };
  function crenels(a,b,base,height,width,phase=.24){
    const [ax,az]=world(a),[bx,bz]=world(b),length=Math.hypot(bx-ax,bz-az),angle=-Math.atan2(bz-az,bx-ax);
    if(length<.00001)return phase;
    const nx=-(bz-az)/length,nz=(bx-ax)/length;
    let d=phase;
    for(;d<length;d+=.65){
      const t=d/length,x=ax+(bx-ax)*t,z=az+(bz-az)*t,y=base(a)*(1-t)+base(b)*t;
      for(const side of [-1,1])merlons.push({x:x+nx*width*.38*side,y:y+height+.18,z:z+nz*width*.38*side,angle,width:.32,depth:.15});
    }
    return d-length;
  }
  const foundation=p=>profile.height(p)+.045;
  for(const f of data.display){
    if(f.kind==='footprint'){
      const shape=makeShape(f),geometry=new THREE.ExtrudeGeometry(shape,{depth:f.height,bevelEnabled:false,steps:1,curveSegments:1});
      geometry.rotateX(-Math.PI/2);geometry.translate(0,.045,0);geometry.clearGroups();stone.push(geometry);
      const top=new THREE.ShapeGeometry(shape).toNonIndexed();top.rotateX(-Math.PI/2);top.translate(0,f.height+.05,0);caps.push(top);
      // Sparse crenellation along each footprint boundary, with no invented towers.
      for(const ring of [f.outer,...f.holes])for(let i=0;i<ring.length;i++){
        const a=ring[i],b=ring[(i+1)%ring.length],[ax,az]=world(a),[bx,bz]=world(b),len=Math.hypot(bx-ax,bz-az);
        for(let d=.25;d<len-.12;d+=.68){const t=d/len;merlons.push({x:ax+(bx-ax)*t,y:f.height+.2,z:az+(bz-az)*t,angle:-Math.atan2(bz-az,bx-ax),width:.32,depth:.16});}
      }
      continue;
    }
    // Mitered cross-sections join every bend into a tapered, continuous wall.
    const points=f.source_px,positions=[],topPositions=[];
    const sections=points.map((p,i)=>{
      const prev=points[Math.max(0,i-1)],next=points[Math.min(points.length-1,i+1)];
      const direction=(a,b)=>{const len=Math.hypot(b[0]-a[0],b[1]-a[1])||1;return [(b[0]-a[0])/len,(b[1]-a[1])/len];};
      const a=direction(i?p:prev,i?prev:next).map(v=>i?-v:v),b=direction(p,i===points.length-1?prev:next).map(v=>i===points.length-1?-v:v);
      const nx=-a[1]-b[1],nz=a[0]+b[0],n=Math.hypot(nx,nz)||1,den=Math.max(.4,(nx/n)*(-b[1])+(nz/n)*b[0]);
      const width=(f.widths?.[i]??f.width)*SCALE;
      const offset=[nx/n/den*width/2,nz/n/den*width/2],[x,z]=world(p),y=foundation(p);
      return [[x-offset[0],y,z-offset[1]],[x+offset[0],y,z+offset[1]],[x-offset[0]*.76,y+f.height,z-offset[1]*.76],[x+offset[0]*.76,y+f.height,z+offset[1]*.76]];
    });
    const quad=(out,a,b,c,d)=>out.push(...a,...b,...c,...a,...c,...d);
    let crenelPhase=.24;
    for(let i=1;i<sections.length;i++){
      const a=sections[i-1],b=sections[i];
      quad(positions,a[0],a[2],b[2],b[0]);quad(positions,a[1],b[1],b[3],a[3]);quad(topPositions,a[2],a[3],b[3],b[2]);
      const width=((f.widths?.[i-1]??f.width)+(f.widths?.[i]??f.width))*.5*SCALE;
      crenelPhase=crenels(points[i-1],points[i],foundation,f.height,width,crenelPhase);
    }
    const first=sections[0],last=sections.at(-1);quad(positions,first[0],first[1],first[3],first[2]);quad(positions,last[0],last[2],last[3],last[1]);
    for(const [out,list] of [[positions,stone],[topPositions,caps]]){
      const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(out,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(new Float32Array(out.length/3*2),2));g.computeVertexNormals();list.push(g);
    }
  }
  for(const gate of data.gates){
    const w=gate.width*SCALE,depth=gate.depth*SCALE,spring=.56;
    const h=Math.max(1.35,...gate.openings.map(o=>spring+o.width*SCALE/2+.22));
    const shape=new THREE.Shape();shape.moveTo(-w/2,0);
    for(const opening of gate.openings){
      const center=opening.center*SCALE,r=opening.width*SCALE/2;
      shape.lineTo(center-r,0);
      if(gate.opening_shape==='rectangular'){
        shape.lineTo(center-r,.88);shape.lineTo(center+r,.88);
      }else{
        shape.lineTo(center-r,spring);shape.absarc(center,spring,r,Math.PI,0,true);
      }
      shape.lineTo(center+r,0);
    }
    shape.lineTo(w/2,0);shape.lineTo(w/2,h);shape.lineTo(-w/2,h);shape.closePath();
    const geometry=new THREE.ExtrudeGeometry(shape,{depth,steps:1,bevelEnabled:false,curveSegments:8});geometry.translate(0,0,-depth/2);geometry.rotateY(-gate.angle);
    const [x,z]=world(gate.p),y=foundation(gate.p);geometry.translate(x,y,z);geometry.clearGroups();stone.push(geometry);
    addBox(caps,w+.12,.11,depth+.1,x,y+h+.055,z,-gate.angle);
    for(let offset=-w/2+.18;offset<w/2;offset+=.5)for(const side of [-1,1]){
      const ox=offset*Math.cos(gate.angle)-side*depth*.4*Math.sin(gate.angle),oz=offset*Math.sin(gate.angle)+side*depth*.4*Math.cos(gate.angle);
      merlons.push({x:x+ox,y:y+h+.22,z:z+oz,angle:-gate.angle,width:.27,depth:.16});
    }
  }
  // Few merged meshes and one instanced crenellation layer keep the wall cheap.
  for(const [geometries,color] of [[stone,WALL_COLOR],[caps,TOP_COLOR]]){
    if(!geometries.length)continue;
    const g=mergeGeometries(geometries);geometries.forEach(g=>g.dispose());
    const material=mat(color,{roughness:.98,side:THREE.FrontSide,shadowSide:THREE.FrontSide});
    const mesh=new THREE.Mesh(g,material);mesh.castShadow=true;mesh.receiveShadow=true;group.add(mesh);
  }
  const battlements=new THREE.InstancedMesh(new THREE.BoxGeometry(1,1,1),mat(TOP_COLOR,{roughness:.98}),merlons.length);
  for(let i=0;i<merlons.length;i++){
    const m=merlons[i];dummy.position.set(m.x,m.y,m.z);dummy.rotation.set(0,m.angle,0);dummy.scale.set(m.width,.25,m.depth);dummy.updateMatrix();battlements.setMatrixAt(i,dummy.matrix);
  }
  battlements.castShadow=true;battlements.receiveShadow=true;group.add(battlements);
  group.userData={segments:data.display.length,gates:data.gates.length,battlements:merlons.length};return group;
}
