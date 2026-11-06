// Match Zhonghua Gate's southern terrace to the two mapped wall approaches.
// Geographic landmark root stays fixed; glTF +Z faces out of the city.
export const ZHONGHUA_PLACEMENT={"scale":0.38,"offsetX":1.8202913,"offsetZ":-3.8261449,"rotationY":-0.3437929796};

// Preserve geographic roots while keeping complete architecture inside the walls.
// Shared by rendering, terrain support, planting reserves and clearance checks.
export const NORTH_LANDMARK_PLACEMENTS={
  jiming:{scale:.43,offsetX:0,offsetZ:3.6,focusHeight:4.7},
  zifeng:{scale:.42,offsetX:0,offsetZ:0,focusHeight:16},
  yuejiang:{scale:.28,offsetX:4.9,offsetZ:.65,focusHeight:3.4},
};

// OSM stadium / pitch alignment. Keep the stadium centred at its real anchor.
export const AOTI_PLACEMENT={scale:.38,rotationY:-.008711596616221354,focusHeight:2,focusZoom:10,focusOffset:[320,290,280]};

// Align the Yangtze main span with the schematic riverbanks; retain source anchors.
// Nanjing Eye keeps its original walking span with stairs extending onto the banks.
// Native glTF bridge axis is +X; all three axes use the same scale.
export const BRIDGE_PLACEMENTS={
  'yangtze-bridge':{scale:0.6661128596140101,offsetX:6.761167699658131,offsetY:.02,offsetZ:8.356420234202846,rotationY:-0.7420523196136742,focusHeight:3.8,focusZoom:11,focusOffset:[340,240,-100],nativeDeckLength:60,endpoints:[[238.54166458590976,199.24266141397703],[287.63972107952617,244.2587059534653]]},
  'nanjing-eye':{scale:0.3229860731394905,offsetX:-2.115938899965181,offsetY:.02,offsetZ:-1.0532778825596778,rotationY:-0.7600583401300415,focusHeight:2,focusZoom:16,focusOffset:[340,240,-100],nativeDeckLength:40,endpoints:[[121.304078,604.629209],[136.910675,619.464255]]},
};

// The river is an artistic outline and does not follow the OSM shoreline.
// Fit only the displayed crossing to the new span, keeping source data intact.
export function alignBridgeRoads(roads){
  const [a,b]=BRIDGE_PLACEMENTS['yangtze-bridge'].endpoints;
  const dx=b[0]-a[0],dy=b[1]-a[1],den=dx*dx+dy*dy;
  const parameter=p=>((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den;
  const project=(p,t)=>t>=-1e-10&&t<=1+1e-10?[a[0]+dx*Math.max(0,Math.min(1,t)),a[1]+dy*Math.max(0,Math.min(1,t))]:p;
  return roads.map(road=>{
    if(road.name!=='南京长江大桥')return road;
    const points=[],ids=[];
    const append=(p,id)=>{points.push(project(p,parameter(p)));ids.push(id);};
    append(road.source_px[0],road.node_ids[0]);
    for(let i=1;i<road.source_px.length;i++){
      const p=road.source_px[i-1],q=road.source_px[i],t0=parameter(p),t1=parameter(q);
      const cuts=[0,1].map(t=>({t,u:(t-t0)/(t1-t0)})).filter(c=>c.u>1e-9&&c.u<1-1e-9).sort((a,b)=>a.u-b.u);
      for(const {t,u} of cuts)append(p.map((v,k)=>v+(q[k]-v)*u),`bridge-span:${road.segment_id}:${i}:${t}`);
      append(q,road.node_ids[i]);
    }
    const changed=points.length!==road.source_px.length||points.some((p,i)=>Math.hypot(p[0]-road.source_px[i][0],p[1]-road.source_px[i][1])>1e-7);
    return changed?{...road,source_px:points,node_ids:ids,bridgeAligned:true}:road;
  });
}

// Source-map distance to the complete Yangtze bridge footprint, including towers.
export function yangtzeFootprintDistance(p){
  const placement=BRIDGE_PLACEMENTS['yangtze-bridge'],[a,b]=placement.endpoints;
  const x=(p[0]-(a[0]+b[0])/2)*.6,z=(p[1]-(a[1]+b[1])/2)*.6;
  const c=Math.cos(placement.rotationY),s=Math.sin(placement.rotationY);
  return Math.hypot(Math.max(0,Math.abs(c*x-s*z)-30.2*placement.scale),Math.max(0,Math.abs(s*x+c*z)-2.85*placement.scale))/.6;
}

// Detailed bridge assets supply their own piers inside the mapped main span.
// Approach-road piers outside that span remain part of the road network.
export function hasBridgeSupport(p,roadName){
  const id={'南京长江大桥':'yangtze-bridge','南京眼步行桥':'nanjing-eye'}[roadName];
  if(!id)return false;
  const [a,b]=BRIDGE_PLACEMENTS[id].endpoints,dx=b[0]-a[0],dy=b[1]-a[1];
  const t=((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy);
  return t>=0&&t<=1&&Math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)<2.5;
}
