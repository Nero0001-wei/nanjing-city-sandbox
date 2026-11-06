import {pointInPolygon,segmentDistance} from './geo.js';

export const footprintCentre=b=>[(b.bbox[0]+b.bbox[2])/2,(b.bbox[1]+b.bbox[3])/2];
export function footprintContains(p,b){return pointInPolygon(p,b.outer)&&!b.holes.some(h=>pointInPolygon(p,h));}
export function footprintDistance(p,b){
  if(footprintContains(p,b))return 0;
  let distance=Infinity;
  for(const ring of [b.outer,...b.holes])for(let i=0;i<ring.length;i++)distance=Math.min(distance,segmentDistance(p,ring[i],ring[(i+1)%ring.length]));
  return distance;
}
export function createBuildingIndex(buildings){
  const cell=12,bins=new Map();
  for(const b of buildings){
    for(let x=Math.floor(b.bbox[0]/cell);x<=Math.floor(b.bbox[2]/cell);x++)for(let y=Math.floor(b.bbox[1]/cell);y<=Math.floor(b.bbox[3]/cell);y++){
      const key=x+','+y;if(!bins.has(key))bins.set(key,[]);bins.get(key).push(b);
    }
  }
  return (p,padding=0)=>{
    const checked=new Set();
    for(let x=Math.floor((p[0]-padding)/cell);x<=Math.floor((p[0]+padding)/cell);x++)for(let y=Math.floor((p[1]-padding)/cell);y<=Math.floor((p[1]+padding)/cell);y++){
      for(const b of bins.get(x+','+y)||[]){if(checked.has(b))continue;checked.add(b);
        if(p[0]<b.bbox[0]-padding||p[0]>b.bbox[2]+padding||p[1]<b.bbox[1]-padding||p[1]>b.bbox[3]+padding)continue;
        if(footprintDistance(p,b)<=padding)return true;
      }
    }
    return false;
  };
}
