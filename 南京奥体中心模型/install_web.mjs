// Run after build_aoti.py. Adds the stadium without regenerating map roads/water.
import {readFile,writeFile,copyFile,mkdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {footprintDistance} from '../sandbox-app/src/building-footprints.js';
import {AOTI_PLACEMENT} from '../sandbox-app/src/landmark-placement.js';
const root=new URL('../',import.meta.url),path=p=>new URL(p,root);
const read=async p=>JSON.parse(await readFile(path(p),'utf8'));
const write=(p,d,pretty=false)=>writeFile(path(p),JSON.stringify(d,null,pretty?2:undefined));
const site=await read('南京奥体中心模型/site-reference.json'),stats=await read('南京奥体中心模型/web/web-model-stats.json');
const poi={id:'aoti',number:15,name:'南京奥体中心体育场',zone:'E',longitude:site.longitude,latitude:site.latitude,coordinate_system:'WGS84',source:site.source,source_px:site.source_px,model:'红色双斜拱、开放式环形屋盖与体育场内场',offset_m_approx:0};
const additional=await read('output/layout-v2/additional-landmarks.json').catch(()=>[]);
await write('output/layout-v2/additional-landmarks.json',[...additional.filter(p=>p.id!=='aoti'),{...poi,label_source_px:[225,585]}],true);
for(const file of ['output/layout-v2/nanjing-layout-data.json','sandbox-app/public/data/nanjing.json']){
  const d=await read(file),p={...poi};
  if(file.startsWith('output/'))Object.assign(p,{layout_px:[48+p.source_px[0]*2.62,180+(p.source_px[1]-165)*2.62],scene_position:[+( (p.source_px[0]-350)*3.24).toFixed(3),0,+((p.source_px[1]-430)*3.24).toFixed(3)],label_source_px:[225,585]});
  d.landmarks=[...d.landmarks.filter(p=>p.id!=='aoti'),p];await write(file,d,file.startsWith('output/'));
}
const buildingsBefore=await read('sandbox-app/public/data/buildings.json'),urban=await read('sandbox-app/public/data/urban.json');
// Existing preparation rules reserve land around every POI; raw OSM remains intact.
execFileSync(process.execPath,['scripts/prepare-buildings.mjs'],{cwd:fileURLToPath(path('sandbox-app/')),stdio:'inherit'});
const buildingsAfter=await read('sandbox-app/public/data/buildings.json');
const removedUrban=urban.buildings.filter(b=>footprintDistance(poi.source_px,b)<=18);
urban.buildings=urban.buildings.filter(b=>footprintDistance(poi.source_px,b)>18);urban.counts.buildings=urban.buildings.length;
await write('sandbox-app/public/data/urban.json',urban);
const beforeIds=new Set(buildingsBefore.features.map(b=>b.id)),afterIds=new Set(buildingsAfter.features.map(b=>b.id));
const audit={removed_white:[...beforeIds].filter(id=>!afterIds.has(id)),added_white:[...afterIds].filter(id=>!beforeIds.has(id)),removed_infill:removedUrban.map(b=>b.id),white_count:buildingsAfter.count,infill_count:urban.buildings.length};
await mkdir(path('sandbox-app/artifacts/aoti-integration'),{recursive:true});
const auditPath=path('sandbox-app/artifacts/aoti-integration/placement-update.json');
if(audit.removed_white.length||audit.removed_infill.length)await writeFile(auditPath,JSON.stringify(audit,null,2));
const version=`web-${stats.triangles}-${stats.sha256.slice(0,8)}`;
const manifest=await read('sandbox-app/public/models/manifest.json');
manifest.models=[...manifest.models.filter(m=>m.id!=='aoti'),{id:'aoti',file:'aoti.glb',blender_dimensions:stats.blender_dimensions,origin:'stadium centre; lower plinth embeds 0.01 scene unit into ground',front:'glTF +Z faces south; pitch long axis north-south',status:'web detailed tree-free stadium with embedded textures and vertex AO',source_blend:'../../../南京奥体中心模型/web/南京奥体中心体育场_网页版.blend',editable_source:'../../../南京奥体中心模型/南京奥体中心体育场_分组可编辑_带材质.blend',concept:'../../../南京奥体中心效果图/南京奥体中心体育场-三视图.png',triangles:stats.triangles,triangle_budget:40000,glb_bytes:stats.glb_bytes,materials:stats.material_count,embedded_images:stats.embedded_images,vertex_ao:true,scene_scale:AOTI_PLACEMENT.scale,scene_offset:[0,0,0],scene_rotation_y:AOTI_PLACEMENT.rotationY,version,sha256:stats.sha256,geographic_source:site.source,placement_note:'OSM stadium centre, aligned to its football pitch. The existing mapped stadium white model is excluded by the standard landmark reserve.'}];
await write('sandbox-app/public/models/manifest.json',manifest,true);
await copyFile(path('南京奥体中心模型/web/南京奥体中心体育场_网页版.glb'),path('sandbox-app/public/models/aoti.glb'));
const scenePath=path('sandbox-app/src/scene.js'),code=await readFile(scenePath,'utf8');
const next=code.replace(/aoti:\{\.\.\.AOTI_PLACEMENT,version:'[^']*'\}/,`aoti:{...AOTI_PLACEMENT,version:'${version}'}`);
if(next===code&&!code.includes(version))throw new Error('Missing scene registration');
await writeFile(scenePath,next);console.log(JSON.stringify({version,...stats,placement:audit},null,2));
