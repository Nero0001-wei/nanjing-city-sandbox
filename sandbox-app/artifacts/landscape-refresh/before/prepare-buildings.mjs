import {readFile,writeFile} from 'node:fs/promises';
import {createTerrainProfile} from '../src/terrain-profile.js';
import {footprintCentre,footprintDistance} from '../src/building-footprints.js';
import {createWallIndex} from '../src/city-walls.js';

const raw=JSON.parse(await readFile(new URL('../data/building-footprints.json',import.meta.url),'utf8'));
const map=JSON.parse(await readFile(new URL('../public/data/nanjing.json',import.meta.url),'utf8'));
const walls=JSON.parse(await readFile(new URL('../public/data/city-walls.json',import.meta.url),'utf8'));
const wallOccupied=createWallIndex(walls),wallIds=new Set(walls.excluded_building_ids);
const profile=createTerrainProfile(map),candidates=[],excluded={};
const omit=reason=>{excluded[reason]=(excluded[reason]||0)+1;};
for(const b of raw.features){
  const p=footprintCentre(b);
  if(wallIds.has(b.id)){omit('city_wall_fabric');continue;}
  if(b.source_area*32.4**2<120){omit('small_footprint');continue;}
  if(profile.height(p)>2){omit('scenic_terrain');continue;}
  if(map.landmarks.some(l=>l.id!=='xuanwu'&&footprintDistance(l.source_px,b)<17)){omit('landmark_reserve');continue;}
  if([p,...b.outer].some(p=>profile.isWater(p))){omit('schematic_water_mask');continue;}
  // The displayed roads are deliberately wide: keep nearby building walls clear.
  if([p,...b.outer].some(p=>profile.roadDistance(p,2)<1.05)){omit('displayed_road_clearance');continue;}
  const edgeSamples=[p,...b.outer];
  for(let i=0;i<b.outer.length;i++){const a=b.outer[i],z=b.outer[(i+1)%b.outer.length],n=Math.ceil(Math.hypot(z[0]-a[0],z[1]-a[1]));for(let j=1;j<n;j++)edgeSamples.push(a.map((v,k)=>v+(z[k]-v)*j/n));}
  if(edgeSamples.some(p=>wallOccupied(p,1.1))){omit('city_wall_clearance');continue;}
  if(edgeSamples.some(p=>profile.roadDistance(p,2)<1.05)){omit('road_edge_clearance');continue;}
  const importance=Math.log1p(b.source_area*32.4**2)*.7+(b.height_source==='osm_height'?1:0)+(b.name?.5:0)+Math.min(b.height_m,100)/90;
  candidates.push({b,importance,p});
}
// Spread complete real footprints across both main-road corridors and block interiors.
const cells=new Map();
for(const c of candidates){const key=Math.floor(c.p[0]/18)+','+Math.floor(c.p[1]/18);if(!cells.has(key))cells.set(key,[]);cells.get(key).push(c);}
for(const list of cells.values())list.sort((a,b)=>b.importance-a.importance||a.b.id.localeCompare(b.b.id));
const features=[];
for(let round=0;round<80&&features.length<10000;round++){
  for(const key of [...cells.keys()].sort()){
    const c=cells.get(key)[round];if(c){features.push(c.b);if(features.length>=10000)break;}
  }
}
const heightCounts=features.reduce((o,b)=>(o[b.height_source]=(o[b.height_source]||0)+1,o),{});
const result={source:raw.source,attribution:raw.attribution,source_count:raw.count,candidate_count:candidates.length,count:features.length,height_counts:heightCounts,excluded,
  selection:'Selected complete OSM footprints >=120 m² across the full urban area, including block interiors, with clearance around landmarks, city walls, stylized water and roads. Max 10000, balanced across spatial cells.',
  height_note:raw.height_note,vertical_exaggeration:1.6,metres_per_source_pixel:32.4,features};
await writeFile(new URL('../public/data/buildings.json',import.meta.url),JSON.stringify(result));
console.log(JSON.stringify({...result,features:undefined},null,2));
