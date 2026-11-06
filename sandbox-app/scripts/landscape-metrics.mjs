import fs from 'node:fs';
import {pathToFileURL} from 'node:url';
import {createBuildingIndex} from '../src/building-footprints.js';
import {createWallIndex} from '../src/city-walls.js';
import {createRoadLayout} from '../src/road-clearance.js';
const read=p=>JSON.parse(fs.readFileSync(p));
const oldModule=async file=>{
  let code=fs.readFileSync('artifacts/landscape-refresh/before/'+file,'utf8');
  code=code.replace(/from '([^']+)'/g,(_,name)=>{
    const path=name==='three'?'node_modules/three/build/three.module.js':name.startsWith('three/addons/')?'node_modules/three/examples/jsm/'+name.slice(13):'src/'+name.slice(2);
    return `from '${pathToFileURL(process.cwd()+'/'+path)}'`;
  });
  return import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));
};
const [{createTerrainProfile},{buildCityVegetation},{treeAppearance,createTreeGeometry}]=await Promise.all(['terrain-profile.js','urban.js','vegetation.js'].map(oldModule));
const data=read('public/data/nanjing.json'),buildings=read('artifacts/landscape-refresh/before/buildings.json'),urban=read('artifacts/landscape-refresh/before/urban.json');
const occupiedB=createBuildingIndex([...buildings.features,...urban.buildings]),occupiedW=createWallIndex(read('public/data/city-walls.json'));
const layout=createRoadLayout(data),profile=createTerrainProfile({...data,roads:layout.roads},(p,r)=>occupiedB(p,r)||occupiedW(p,r));
const trees=buildCityVegetation(profile,urban).map((t,i)=>treeAppearance(t,profile,i)),geometries=new Map();
let triangles=0,bufferBytes=0;const speciesCounts={};
for(const t of trees){
 const compact=t.size<.7,key=t.species+':'+t.variant+':'+compact;
 if(!geometries.has(key)){const g=createTreeGeometry(t.species,t.variant,compact);geometries.set(key,g);for(const a of Object.values(g.attributes))bufferBytes+=a.array.byteLength;}
 triangles+=geometries.get(key).attributes.position.count/3;speciesCounts[t.species]=(speciesCounts[t.species]||0)+1;
}
const before={trees:trees.length,treeTriangles:triangles,treeBatches:geometries.size,treeGeometryBufferBytes:bufferBytes,treeGLBBytes:0,treeAssetNote:'Procedural JavaScript geometry; no previous GLB download.',buildingCount:buildings.count+urban.counts.buildings,speciesCounts,...read('artifacts/landscape-refresh/before/browser.json')};
const after={...read('artifacts/landscape-refresh/browser.json').stats,treeGLBBytes:read('public/models/manifest.json').vegetation.glb_bytes};
const metrics={before,after};fs.writeFileSync('artifacts/landscape-refresh/comparison.json',JSON.stringify(metrics,null,2));console.log(JSON.stringify(metrics,null,2));
for(const g of geometries.values())g.dispose();
