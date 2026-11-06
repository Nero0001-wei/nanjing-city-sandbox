import {world,SCALE,clipSegment,segmentDistance} from './geo.js';
import {ZHONGHUA_PLACEMENT,alignBridgeRoads} from './landmark-placement.js';

// These are the exported GLB foundations in Y-up model coordinates. Only the
// display paths bend around the enlarged assets; OSM coordinates stay intact.
const FOUNDATIONS={
  fuzimiao:{scale:.44,bounds:[-14,-12,14,14]},
  zhonghua:{...ZHONGHUA_PLACEMENT,bounds:[-14.5,-16.5,14.5,17.5],passage:true},
};
export function landmarkRoadZones(landmarks=[]){
  return landmarks.filter(l=>FOUNDATIONS[l.id]).map(l=>{
    const placement=FOUNDATIONS[l.id],a=placement.rotationY||0,c=Math.cos(a),s=Math.sin(a);
    const anchor=world(l.source_px),origin=[anchor[0]+(placement.offsetX||0),anchor[1]+(placement.offsetZ||0)];
    const local=p=>{const w=world(p),x=w[0]-origin[0],z=w[1]-origin[1];return [c*x-s*z,s*x+c*z];};
    const source=([x,z])=>[(origin[0]+c*x+s*z)/SCALE+350,(origin[1]-s*x+c*z)/SCALE+430];
    const bounds=placement.bounds.map(v=>v*placement.scale),[x0,z0,x1,z1]=bounds,padding=.5;
    // Zhonghua's four real arch openings remain usable. Reserve the centre
    // passage instead of sending the road across its walls or around wall joints.
    const rectangles=placement.passage?
      [[x0-padding,z0-padding,-.14,z1+padding],[.14,z0-padding,x1+padding,z1+padding]]:
      [[x0-padding,z0-padding,x1+padding,z1+padding]];
    return {id:l.id,local,source,bounds,rectangles,passage:placement.passage};
  });
}
const inside=([x,z],[x0,z0,x1,z1],epsilon=1e-7)=>x>x0+epsilon&&x<x1-epsilon&&z>z0+epsilon&&z<z1-epsilon;
const distance=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]);
const corners=([x0,z0,x1,z1])=>[[x0,z0],[x1,z0],[x1,z1],[x0,z1]];
function project(p,zone){
  const q=zone.local(p),r=zone.rectangles.find(r=>inside(q,r));
  if(!r)return p;
  if(zone.passage)return zone.source([0,q[1]]);
  const [x0,z0,x1,z1]=r,options=[[x0,q[1]],[x1,q[1]],[q[0],z0],[q[0],z1]];
  return zone.source(options.reduce((a,b)=>distance(q,a)<distance(q,b)?a:b));
}
const blocked=(p,zones)=>zones.some(z=>z.rectangles.some(r=>inside(z.local(p),r)));
function route(a,b,zones){
  const visible=(a,b)=>!zones.some(z=>z.rectangles.some(r=>{
    const hit=clipSegment(z.local(a),z.local(b),[r[0]+1e-6,r[1]+1e-6,r[2]-1e-6,r[3]-1e-6]);
    return hit&&distance(hit[0],hit[1])>1e-6;
  }));
  if(visible(a,b))return [a,b];
  const candidates=zones.flatMap(z=>z.rectangles.flatMap(corners).map(z.source)).filter(p=>!blocked(p,zones));
  const points=[a,b,...candidates],cost=points.map(()=>Infinity),parent=[],done=new Set();cost[0]=0;
  while(done.size<points.length){
    let i=-1;for(let j=0;j<points.length;j++)if(!done.has(j)&&(i<0||cost[j]<cost[i]))i=j;
    if(i===1||!Number.isFinite(cost[i]))break;done.add(i);
    for(let j=0;j<points.length;j++)if(!done.has(j)&&visible(points[i],points[j])){
      const next=cost[i]+distance(points[i],points[j]);if(next<cost[j]){cost[j]=next;parent[j]=i;}
    }
  }
  if(!Number.isFinite(cost[1]))throw new Error('No continuous display road around landmark foundations');
  const path=[1];while(path[0]!==0)path.unshift(parent[path[0]]);
  return path.map(i=>points[i]);
}

export function createRoadLayout(data){
  const zones=landmarkRoadZones(data.landmarks),positions=new Map();let adjusted=0;
  const displayRoads=alignBridgeRoads(data.roads);
  const rivers=(data.rivers||[]).flatMap(r=>r.source_px.slice(1).map((b,i)=>[r.source_px[i],b]));
  const idAt=(r,i)=>r.node_ids?.[i]||`point:${r.source_px[i].join(',')}`;
  for(const r of displayRoads)r.source_px.forEach((p,i)=>{
    const id=idAt(r,i);if(!positions.has(id)){
      let q=p;for(let i=0;i<4;i++){q=zones.reduce(project,q);if(!blocked(q,zones))break;}
      positions.set(id,q);
    }
  });
  const roads=displayRoads.map(road=>{
    const points=[],ids=[];
    for(let i=1;i<road.source_px.length;i++){
      const path=route(positions.get(idAt(road,i-1)),positions.get(idAt(road,i)),zones);
      path.forEach((p,j)=>{
        if(i>1&&j===0)return;
        points.push(p);ids.push(j===0?idAt(road,i-1):j===path.length-1?idAt(road,i):`clearance:${road.segment_id||road.osm_way_id}:${i}:${j}`);
      });
    }
    const changed=!!road.bridgeAligned||points.length!==road.source_px.length||points.some((p,i)=>distance(p,road.source_px[i])>1e-6);
    if(changed)adjusted++;
    const length=road.source_px.slice(1).reduce((sum,b,i)=>sum+distance(road.source_px[i],b),0);
    const a=road.source_px[0],b=road.source_px.at(-1),middle=[(a[0]+b[0])/2,(a[1]+b[1])/2];
    const riverBridge=road.kind==='elevated'&&road.bridge==='yes'&&length<6
      &&!['trunk','trunk_link','motorway','motorway_link'].includes(road.highway)
      &&rivers.some(([a,b])=>segmentDistance(middle,a,b)<1.8);
    return changed||riverBridge?{...road,source_px:points,node_ids:ids,displayAdjusted:changed,bridgeProfile:riverBridge?'river':undefined}:road;
  });
  const gate=zones.find(z=>z.passage);
  const minimumLift=p=>{
    if(!gate)return 0;
    const [x,z]=gate.local(p),b=gate.bounds;
    // The GLB paving is .32 * .38 + .18 high; keep the road just above it.
    return Math.abs(x)<.55&&z>b[1]-.9&&z<b[3]+.9?.14:0;
  };
  const maximumLift=p=>minimumLift(p)===.14?.14:Infinity;
  const pierBlocked=p=>zones.some(z=>inside(z.local(p),z.bounds));
  return {roads,adjusted,zones,minimumLift,maximumLift,pierBlocked};
}
