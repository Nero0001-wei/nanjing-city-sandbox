import {pointInPolygon,segmentDistance,seededRandom,BOUNDS,SCALE} from './geo.js';
import {cityHillHeight,CITY_HILLS} from './terrain-hills.js';
import {ZHONGHUA_PLACEMENT,BRIDGE_PLACEMENTS,NORTH_LANDMARK_PLACEMENTS,AOTI_PLACEMENT} from './landmark-placement.js';

const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
export const smooth=(a,b,v)=>{const t=clamp((v-a)/(b-a));return t*t*(3-2*t);};
function hash(x,y){const n=Math.sin(x*127.1+y*311.7+29)*43758.5453;return n-Math.floor(n);}
export function noise(x,y){
  const ix=Math.floor(x),iy=Math.floor(y),u=smooth(0,1,x-ix),v=smooth(0,1,y-iy);
  const a=hash(ix,iy)*(1-u)+hash(ix+1,iy)*u,b=hash(ix,iy+1)*(1-u)+hash(ix+1,iy+1)*u;
  return a*(1-v)+b*v;
}

function segmentIndex(segments,cell=16){
  const bins=new Map();
  for(const [a,b] of segments){
    // Split long segments so distance queries do not populate giant bounding boxes.
    const n=Math.max(1,Math.ceil(Math.hypot(b[0]-a[0],b[1]-a[1])/12));
    for(let j=0;j<n;j++){
      const c=[a[0]+(b[0]-a[0])*j/n,a[1]+(b[1]-a[1])*j/n],d=[a[0]+(b[0]-a[0])*(j+1)/n,a[1]+(b[1]-a[1])*(j+1)/n];
      for(let x=Math.floor(Math.min(c[0],d[0])/cell);x<=Math.floor(Math.max(c[0],d[0])/cell);x++)for(let y=Math.floor(Math.min(c[1],d[1])/cell);y<=Math.floor(Math.max(c[1],d[1])/cell);y++){
        const key=x+','+y;if(!bins.has(key))bins.set(key,[]);bins.get(key).push([c,d]);
      }
    }
  }
  return (p,r=16)=>{
    let distance=r;
    for(let x=Math.floor((p[0]-r)/cell);x<=Math.floor((p[0]+r)/cell);x++)for(let y=Math.floor((p[1]-r)/cell);y<=Math.floor((p[1]+r)/cell);y++){
      for(const [a,b] of bins.get(x+','+y)||[])distance=Math.min(distance,segmentDistance(p,a,b));
    }
    return distance;
  };
}
const segments=(ring,closed=false)=>ring.slice(1).map((p,i)=>[ring[i],p]).concat(closed&&ring.length>2?[[ring.at(-1),ring[0]]]:[]);

export function createTerrainProfile(data,occupied=()=>false){
  const mountain=data.schematic_terrain.find(f=>f.kind==='mountain').source_px;
  const yangtze=data.schematic_terrain.find(f=>f.id==='yangtze').source_px;
  const islands=data.schematic_terrain.filter(f=>f.kind==='island').map(f=>f.source_px);
  const lakeRings=data.lakes.flatMap(l=>l.rings.map(r=>r.source_px));
  const shoreRings=[yangtze,...islands,...lakeRings];
  const shoreDistance=segmentIndex(shoreRings.flatMap(r=>segments(r,true)));
  const riverDistance=segmentIndex(data.rivers.flatMap(r=>segments(r.source_px)));
  const roadDistance=segmentIndex(data.roads.flatMap(r=>segments(r.source_px)));
  const mountainBounds=[Math.min(...mountain.map(p=>p[0])),Math.min(...mountain.map(p=>p[1])),Math.max(...mountain.map(p=>p[0])),Math.max(...mountain.map(p=>p[1]))];
  const mountainSegments=segments(mountain,true),yuejiang=data.landmarks.find(l=>l.id==='yuejiang').source_px;
  function mountainMask(p){
    if(p[0]<mountainBounds[0]||p[0]>mountainBounds[2]||p[1]<mountainBounds[1]||p[1]>mountainBounds[3]||!pointInPolygon(p,mountain))return 0;
    const edge=Math.min(...mountainSegments.map(([a,b])=>segmentDistance(p,a,b)));
    return smooth(0,22,edge);
  }
  // Artistic relief only: several rounded ridges instead of one flat-topped mound.
  const peaks=[[522,342,17,29,32],[563,319,28,34,27],[611,339,34,34,31],[638,381,24,26,35],[577,382,22,36,29],[533,398,9,24,25]];
  function rawHeight(p){
    const mask=mountainMask(p);let h=0;
    if(mask){
      const values=peaks.map(([x,y,z,rx,ry])=>z*Math.exp(-(((p[0]-x)/rx)**2+((p[1]-y)/ry)**2))).sort((a,b)=>b-a);
      const detail=(noise(p[0]/11,p[1]/11)-.5)*2.1+(noise(p[0]/5,p[1]/5)-.5)*.45;
      h=(values[0]+values[1]*.18+detail)*mask;
    }
    // Preserve the approved Shizishan terrace elevation and support area.
    const q=yuejiang;
    const d=Math.hypot(p[0]-q[0],p[1]-q[1]);
    h+=3.7*(1-smooth(3,24,d));
    return Math.max(0,h);
  }
  const pads=data.landmarks.filter(p=>['zhongshan','mingxiaoling','meiling','yuejiang'].includes(p.id)).map(p=>({id:p.id,p:p.source_px,h:rawHeight(p.source_px),radius:p.id==='zhongshan'?23:p.id==='mingxiaoling'?14:p.id==='yuejiang'?9:11}));
  const towerPlacement=NORTH_LANDMARK_PLACEMENTS.yuejiang;
  pads.push({id:'yuejiang-terrace',p:[yuejiang[0]+towerPlacement.offsetX/SCALE,yuejiang[1]+towerPlacement.offsetZ/SCALE],h:rawHeight(yuejiang),radius:8});
  const landmarkReserves=data.landmarks.filter(l=>l.id!=='xuanwu').flatMap(l=>{
    const a=NORTH_LANDMARK_PLACEMENTS[l.id];
    return a&&(a.offsetX||a.offsetZ)?[l.source_px,[l.source_px[0]+a.offsetX/SCALE,l.source_px[1]+a.offsetZ/SCALE]]:[l.source_px];
  });
  function mountainHeight(p){
    let h=rawHeight(p),total=1;
    // Nearby feathered pads must not tilt the fully flat area beneath another landmark.
    // Normalize soft weights to keep a continuous slope between pads at different heights.
    for(const pad of pads){
      const d=Math.hypot(p[0]-pad.p[0],p[1]-pad.p[1]);
      if(d<=pad.radius)return pad.h;
      const w=1-smooth(pad.radius,pad.radius+9,d),weight=(w/Math.max(1e-9,1-w))**.6;
      h+=pad.h*weight;total+=weight;
    }
    return h/total;
  }
  const footprints={
    aoti:[41,41,AOTI_PLACEMENT.scale,0,0,AOTI_PLACEMENT.rotationY],
    jiming:[24,16,.43,0,3.6],zifeng:[20,16,.42],yuejiang:[24,19,.28,4.9,.65],
    zhongshan:[22,34,.6],mingxiaoling:[26,21,.45],meiling:[20,18,.47],museum:[34,22,.4,-3.25,0],
    presidential:[26,28,.39],fuzimiao:[28,28,.44],baoen:[10,10,.425],
    zhonghua:[29,35,.38,ZHONGHUA_PLACEMENT.offsetX,ZHONGHUA_PLACEMENT.offsetZ,ZHONGHUA_PLACEMENT.rotationY],
  };
  const foundations=data.landmarks.filter(l=>footprints[l.id]).map(l=>{
    const [w,d,scale,ox=0,oz=0,angle=0]=footprints[l.id];
    return {p:l.source_px,w:w*scale/2/SCALE+1.2,d:d*scale/2/SCALE+1.2,ox:ox/SCALE,oz:oz/SCALE,c:Math.cos(angle),s:Math.sin(angle)};
  });
  function hillMask(p){
    if(isWater(p))return 0;
    let mask=smooth(1.5,8,shoreDistance(p,8))*smooth(2,7,riverDistance(p,7));
    // Feather inside the map edge and around complete rotated landmark bases.
    mask*=smooth(0,9,Math.min(p[0]-BOUNDS[0],BOUNDS[2]-p[0],p[1]-BOUNDS[1],BOUNDS[3]-p[1]));
    for(const f of foundations){
      const dx=p[0]-f.p[0]-f.ox,dy=p[1]-f.p[1]-f.oz;
      const distance=Math.hypot(Math.max(0,Math.abs(f.c*dx-f.s*dy)-f.w),Math.max(0,Math.abs(f.s*dx+f.c*dy)-f.d));
      mask=Math.min(mask,smooth(0,9,distance),smooth(2,9,Math.hypot(p[0]-f.p[0],p[1]-f.p[1])));
    }
    for(const bridge of Object.values(BRIDGE_PLACEMENTS))mask=Math.min(mask,smooth(6,16,segmentDistance(p,...bridge.endpoints)));
    return mask;
  }
  const reliefHeight=p=>{const h=cityHillHeight(p);return h>0?h*hillMask(p):0;};
  const height=p=>mountainHeight(p)+reliefHeight(p);
  const woodlandMask=p=>Math.max(mountainMask(p),smooth(.25,2.8,reliefHeight(p)));
  function isWater(p){
    if(pointInPolygon(p,yangtze)&&!islands.some(r=>pointInPolygon(p,r)))return true;
    if(data.lakes.some(l=>l.rings.some(r=>r.role==='outer'&&pointInPolygon(p,r.source_px))&&!l.rings.some(r=>r.role==='inner'&&pointInPolygon(p,r.source_px))))return true;
    return riverDistance(p,3)<1.7;
  }
  function landmarkDistance(p){return Math.min(...landmarkReserves.map(q=>Math.hypot(q[0]-p[0],q[1]-p[1])));}
  function buildVegetation(){
    const random=seededRandom(2026102902),trees=[],cells=new Map(),spacing=3.3;
    const nearby=p=>{
      const cx=Math.floor(p[0]/spacing),cy=Math.floor(p[1]/spacing);
      for(let x=cx-1;x<=cx+1;x++)for(let y=cy-1;y<=cy+1;y++)for(const q of cells.get(x+','+y)||[])if(Math.hypot(p[0]-q[0],p[1]-q[1])<spacing)return true;
      return false;
    };
    for(let i=0;i<28000&&trees.length<1550;i++){
      const p=[BOUNDS[0]+12+random()*(BOUNDS[2]-BOUNDS[0]-24),BOUNDS[1]+12+random()*(BOUNDS[3]-BOUNDS[1]-24)];
      const mask=woodlandMask(p),shore=shoreDistance(p,16),cluster=noise(p[0]/34,p[1]/34),urban=p[0]>270&&p[0]<465&&p[1]>345&&p[1]<600;
      const density=mask>.08?.92:shore<9?.68:urban?.045:.045+smooth(.46,.75,cluster)*.58;
      if(random()>density||isWater(p)||nearby(p)||landmarkDistance(p)<17||roadDistance(p,5)<3.1||riverDistance(p,5)<3.1||shore<1.8||occupied(p,3.5))continue;
      if(pads.some(pad=>pad.id==='zhongshan'&&Math.hypot(p[0]-pad.p[0],p[1]-pad.p[1])<24))continue;
      const key=Math.floor(p[0]/spacing)+','+Math.floor(p[1]/spacing);if(!cells.has(key))cells.set(key,[]);cells.get(key).push(p);
      trees.push({p,y:height(p),size:.82+random()*.77,pine:mask>.12&&random()<.36,color:random(),turn:random()*Math.PI*2});
    }
    return trees;
  }
  return {height,rawHeight,mountainMask,woodlandMask,reliefHeight,hills:CITY_HILLS,isWater,shoreDistance,riverDistance,roadDistance,landmarkDistance,shoreRings,buildVegetation,occupied};
}
