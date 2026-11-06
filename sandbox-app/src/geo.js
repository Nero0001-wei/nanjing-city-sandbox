// Source coordinates share the corrected map's z12 Web Mercator origin.
export const SCALE = .6;
export const BOUNDS = [30, 170, 690, 690];
export const world = ([x,y]) => [(x-350)*SCALE, (y-430)*SCALE];
export function pointInPolygon([x,y], ring) {
  let inside=false;
  for(let i=0,j=ring.length-1;i<ring.length;j=i++){
    const [a,b]=ring[i], [c,d]=ring[j];
    if(((b>y)!==(d>y)) && x<(c-a)*(y-b)/(d-b)+a) inside=!inside;
  }
  return inside;
}
export function segmentDistance(p,a,b){
  const dx=b[0]-a[0],dy=b[1]-a[1],den=dx*dx+dy*dy;
  const t=den?Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den)):0;
  return Math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy);
}
// Liang–Barsky clipping preserves crossing segments whose endpoints are outside.
export function clipSegment(a,b,bounds=BOUNDS){
  const [xmin,ymin,xmax,ymax]=bounds,dx=b[0]-a[0],dy=b[1]-a[1];
  let lo=0,hi=1;
  const ps=[-dx,dx,-dy,dy],qs=[a[0]-xmin,xmax-a[0],a[1]-ymin,ymax-a[1]];
  for(let i=0;i<4;i++){
    if(ps[i]===0){if(qs[i]<0)return null;continue;}
    const r=qs[i]/ps[i];
    if(ps[i]<0)lo=Math.max(lo,r);else hi=Math.min(hi,r);
    if(lo>hi)return null;
  }
  return [[a[0]+lo*dx,a[1]+lo*dy],[a[0]+hi*dx,a[1]+hi*dy]];
}
export function clipPolygon(poly,bounds=BOUNDS){
  let result=poly.slice();
  for(const [axis,val,sign] of [[0,bounds[0],1],[0,bounds[2],-1],[1,bounds[1],1],[1,bounds[3],-1]]){
    const prev=result;result=[];
    if(!prev.length)break;
    for(let i=0;i<prev.length;i++){
      const a=prev[i],b=prev[(i+1)%prev.length],ia=(a[axis]-val)*sign>=0,ib=(b[axis]-val)*sign>=0;
      if(ia)result.push(a);
      if(ia!==ib){const t=(val-a[axis])/(b[axis]-a[axis]);result.push([a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])]);}
    }
  }
  return result;
}
export function seededRandom(seed=29){return ()=>{seed=(Math.imul(1664525,seed)+1013904223)>>>0;return seed/4294967296;};}
