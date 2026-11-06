// A diagram with ground roads and one elevated level, not a layered road model.
export const ROAD_BASE = .2;
export const ROAD_WHITE = 0xeeeee8;
export const ELEVATED_HEIGHT = 1.1;
export const RIVER_BRIDGE_HEIGHT = .18;
export function roadWidth(road){
  if(road.highway?.endsWith('_link'))return .43;
  if(road.highway==='footway')return .45;
  return road.group==='景点联系'?.48:.7;
}
export function roadLift(road){
  if(road.kind!=='elevated')return 0;
  if(road.name==='南京长江大桥')return 3.425;
  if(road.name==='南京眼步行桥')return 1.64;
  if(road.bridgeProfile==='river')return RIVER_BRIDGE_HEIGHT;
  return ELEVATED_HEIGHT;
}

class MaxHeap{
  values=[];
  push(item){
    const a=this.values;let i=a.length;a.push(item);
    while(i){const parent=(i-1)>>1;if(a[parent].lift>=item.lift)break;a[i]=a[parent];i=parent;}a[i]=item;
  }
  pop(){
    const a=this.values,top=a[0],tail=a.pop();if(!a.length)return top;
    let i=0;
    while(i*2+1<a.length){let c=i*2+1;if(c+1<a.length&&a[c+1].lift>a[c].lift)c++;if(a[c].lift<=tail.lift)break;a[i]=a[c];i=c;}a[i]=tail;return top;
  }
}

export function buildRoadProfiles(roads,height=()=>0,{minimumLift=()=>0,maximumLift=()=>Infinity}={}){
  const nodes=new Map(),profiles=[];
  function node(id,p){
    if(!nodes.has(id))nodes.set(id,{id,p,lift:minimumLift(p),edges:new Map(),ends:0});
    return nodes.get(id);
  }
  for(const road of roads){
    const points=[];
    for(let i=0;i<road.source_px.length;i++){
      const p=road.source_px[i],id=road.node_ids?.[i]||`point:${p.join(',')}`;
      const n=node(id,p);n.lift=Math.max(n.lift,roadLift(road));if(road.kind==='tunnel')n.tunnel=true;
      if(i){
        const a=road.source_px[i-1],steps=Math.ceil(Math.hypot(p[0]-a[0],p[1]-a[1])/2.5);
        for(let j=1;j<steps;j++){
          const q=node(`sample:${road.segment_id||road.osm_way_id}:${i}:${j}`,[a[0]+(p[0]-a[0])*j/steps,a[1]+(p[1]-a[1])*j/steps]);
          q.lift=Math.max(q.lift,roadLift(road));if(road.kind==='tunnel')q.tunnel=true;points.push(q);
        }
      }
      if(!points.length||Math.hypot(p[0]-points.at(-1).p[0],p[1]-points.at(-1).p[1])>1e-7)points.push(n);
    }
    points[0].ends++;points.at(-1).ends++;
    if(road.kind!=='tunnel'){
      for(let i=1;i<points.length;i++){
        const a=points[i-1],b=points[i],cost=Math.hypot(b.p[0]-a.p[0],b.p[1]-a.p[1])*.12;
        a.edges.set(b.id,cost);b.edges.set(a.id,cost);
      }
    }
    profiles.push({road,points});
  }
  // Propagate elevation only along actual shared-node connections. This fills
  // short tag gaps and grades the approaches, without joining grade crossings.
  const queue=new MaxHeap();
  for(const n of nodes.values())if(n.lift>0)queue.push({id:n.id,lift:n.lift});
  while(queue.values.length){
    const current=queue.pop(),n=nodes.get(current.id);if(current.lift<n.lift)continue;
    for(const [id,cost] of n.edges){
      const next=nodes.get(id),lift=n.lift-cost;
      if(lift>next.lift+1e-8){next.lift=lift;queue.push({id,lift});}
    }
  }
  // Bring approaches down to tunnel mouths and the gate passage floor. Spread
  // height limits through the same graph so lowering a deck cannot make a step.
  const limits=new MaxHeap();
  for(const n of nodes.values()){
    n.cap=n.tunnel?0:maximumLift(n.p);
    if(Number.isFinite(n.cap))limits.push({id:n.id,lift:-n.cap});
  }
  while(limits.values.length){
    const current=limits.pop(),n=nodes.get(current.id);if(-current.lift>n.cap)continue;
    for(const [id,cost] of n.edges){
      const next=nodes.get(id),cap=n.cap+cost;
      if(cap<next.cap){next.cap=cap;limits.push({id,lift:-cap});}
    }
  }
  for(const n of nodes.values())n.lift=Math.min(n.lift,n.cap);
  for(const n of nodes.values())n.y=height(n.p)+ROAD_BASE+n.lift;
  return profiles;
}
