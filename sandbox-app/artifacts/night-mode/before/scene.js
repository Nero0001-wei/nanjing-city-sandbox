import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {mergeGeometries} from 'three/addons/utils/BufferGeometryUtils.js';
import {world,clipSegment,clipPolygon} from './geo.js';
import {createTerrainProfile} from './terrain-profile.js';
import {addTerrainSurfaces,addVegetation,addWaterFinish} from './terrain-surface.js';
import {createBuildingIndex} from './building-footprints.js';
import {addWhiteBuildings} from './buildings.js';
import {addWhiteRoads} from './roads.js';
import {createRoadLayout} from './road-clearance.js';
import {PALETTE,setupLighting} from './render-style.js';
import {setupSkyEnvironment} from './sky-environment.js';
import {addUrbanFabric,buildCityVegetation} from './urban.js';
import {addCityWalls,createWallIndex} from './city-walls.js';
import {ZHONGHUA_PLACEMENT,NORTH_LANDMARK_PLACEMENTS,BRIDGE_PLACEMENTS,AOTI_PLACEMENT} from './landmark-placement.js';
import {createCameraMotion} from './camera-motion.js';
import {addTerrainBase,TERRAIN_BASE} from './terrain-base.js';

const COLORS={water:PALETTE.water,island:PALETTE.island};
const WEB_LANDMARKS={
  aoti:{...AOTI_PLACEMENT,version:'web-38018-5b5b4794'},
  'yangtze-bridge':{...BRIDGE_PLACEMENTS['yangtze-bridge'],version:'web-37044-47f3bc90'},
  'nanjing-eye':{...BRIDGE_PLACEMENTS['nanjing-eye'],version:'web-30356-18b3b1e6'},
  jiming:{...NORTH_LANDMARK_PLACEMENTS.jiming,version:'web-36744-586344ce'},
  zifeng:{...NORTH_LANDMARK_PLACEMENTS.zifeng,version:'web-24484-59ce7d72'},
  yuejiang:{...NORTH_LANDMARK_PLACEMENTS.yuejiang,version:'web-39622-32cf398c'},
  baoen:{scale:0.425,version:'web-35628-4d2ddcb5',focusHeight:6.7},
  presidential:{scale:0.39,version:'web-36674-de8de604',focusHeight:1.5},
  fuzimiao:{scale:0.44,version:'web-36974-61b8a713',focusHeight:2.3},
  zhonghua:{...ZHONGHUA_PLACEMENT,version:'web-38780-0ea231fa',focusHeight:1.6},
  museum:{scale:0.4,version:'web-39152-a844332d',focusHeight:2.2,offsetX:-3.25},
  meiling:{scale:0.47,version:'web-37268-b083c5ac',focusHeight:2.6},
  zhongshan:{scale:.6,version:'web-36774-59573f47',focusHeight:3},
  mingxiaoling:{scale:.45,version:'web-38308-c2fd0056',focusHeight:3.2},
};
const groups={A:'滨江北段',B:'鼓楼与玄武湖',C:'钟山风景',D:'老城记忆',E:'河西滨江'};
export {groups};

export async function createSandbox(host,data,events){
  let disposed=false,frame,view='iso',selected=null;
  const scene=new THREE.Scene();scene.background=new THREE.Color(PALETTE.background);
  const renderer=new THREE.WebGLRenderer({antialias:true,alpha:false,powerPreference:'high-performance'});
  const gl=renderer.getContext(),gpuInfo=gl.getExtension('WEBGL_debug_renderer_info');
  host.dataset.gpu=String(gl.getParameter(gpuInfo?gpuInfo.UNMASKED_RENDERER_WEBGL:gl.RENDERER));
  renderer.setPixelRatio(Math.min(window.devicePixelRatio,1.75));
  const disposeLighting=setupLighting(scene,renderer);
  const disposeEnvironment=setupSkyEnvironment(scene,renderer);
  renderer.domElement.setAttribute('aria-label','南京城市三维沙盘；也可通过左侧景点列表选择地标');
  host.appendChild(renderer.domElement);
  const camera=new THREE.OrthographicCamera(-200,200,160,-160,1,1800);
  const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.085;
  controls.minZoom=.75;controls.maxZoom=16;controls.maxPolarAngle=Math.PI*.46;controls.minPolarAngle=0;
  controls.mouseButtons={LEFT:THREE.MOUSE.ROTATE,MIDDLE:THREE.MOUSE.PAN,RIGHT:THREE.MOUSE.PAN};
  controls.touches={ONE:THREE.TOUCH.ROTATE,TWO:THREE.TOUCH.DOLLY_PAN};
  const materials=new Map();
  const mat=(color,extra={})=>{const key=JSON.stringify([color,extra]);if(!materials.has(key))materials.set(key,new THREE.MeshStandardMaterial({color,roughness:.86,...extra}));return materials.get(key);};
  function mesh(geo,material,parent=scene){const m=new THREE.Mesh(geo,material);m.receiveShadow=true;parent.add(m);return m;}
  const buildingData=data.buildings||{features:[],count:0};
  const occupiedBuildings=createBuildingIndex([...buildingData.features,...(data.urban?.buildings||[])]),occupiedWalls=createWallIndex(data.cityWalls);
  const occupied=(p,padding=0)=>occupiedBuildings(p,padding)||occupiedWalls(p,padding);
  const roadLayout=createRoadLayout(data);
  const profile=createTerrainProfile({...data,roads:roadLayout.roads},occupied),height=profile.height;
  const terrainDetails=addTerrainSurfaces({scene,profile,mat,mesh});
  const terrainBase=addTerrainBase(scene);
  host.dataset.baseDepth=String(TERRAIN_BASE.depth);host.dataset.baseTriangles=String(terrainBase.userData.triangles);
  const waterMaterial=mat(COLORS.water,{side:THREE.DoubleSide}),updateWater=addWaterFinish(waterMaterial);
  const reducedMotion=window.matchMedia('(prefers-reduced-motion: reduce)');
  const cameraMotion=createCameraMotion(camera,controls,()=>reducedMotion.matches);
  // Lower only the presentation floor; the mapped surface and all anchors stay put.
  const floor=mesh(new THREE.PlaneGeometry(3000,3000),new THREE.MeshBasicMaterial({color:PALETTE.background,toneMapped:false}));
  floor.name='surrounding-floor';floor.rotation.x=-Math.PI/2;floor.position.y=TERRAIN_BASE.bottom-.05;floor.receiveShadow=false;

  function shapeFor(ring){return new THREE.Shape(ring.map(p=>{const [x,z]=world(p);return new THREE.Vector2(x,-z);}));}
  function polygon(ring,color,y,holes=[]){
    const shape=shapeFor(clipPolygon(ring));
    for(const h of holes)shape.holes.push(new THREE.Path(h.map(p=>{const [x,z]=world(p);return new THREE.Vector2(x,-z);} )));
    const m=mesh(new THREE.ShapeGeometry(shape),color===COLORS.water?waterMaterial:mat(color,{side:THREE.DoubleSide}));m.rotation.x=-Math.PI/2;m.position.y=y;return m;
  }
  const riverTerrain=data.schematic_terrain.find(f=>f.id==='yangtze');
  polygon(riverTerrain.source_px,COLORS.water,.07);
  const islands=data.schematic_terrain.filter(f=>f.kind==='island');islands.forEach(f=>polygon(f.source_px,COLORS.island,.12));
  data.lakes.forEach(l=>{
    const outer=l.rings.filter(r=>r.role==='outer'),inner=l.rings.filter(r=>r.role==='inner');
    outer.forEach(r=>{const m=polygon(r.source_px,COLORS.water,.08,inner.map(r=>r.source_px));if(l.name==='玄武湖')m.userData.id='xuanwu';});
  });
  // Waterways keep their own material; road topology is rendered in roads.js.
  const riverPositions=[];
  for(const river of data.rivers)for(let i=1;i<river.source_px.length;i++){
    const clipped=clipSegment(river.source_px[i-1],river.source_px[i]);if(!clipped)continue;
    const [a,b]=clipped,[ax,az]=world(a),[bx,bz]=world(b),length=Math.hypot(bx-ax,bz-az);if(length<.001)continue;
    const width=/中段/.test(river.name)?.65:1.45,ox=-(bz-az)/length*width/2,oz=(bx-ax)/length*width/2;
    const vertices=[[ax+ox,.095,az+oz],[ax-ox,.095,az-oz],[bx-ox,.095,bz-oz],[bx+ox,.095,bz+oz]];
    for(const j of [0,2,1,0,3,2])riverPositions.push(...vertices[j]);
  }
  const riverGeometry=new THREE.BufferGeometry();riverGeometry.setAttribute('position',new THREE.Float32BufferAttribute(riverPositions,3));riverGeometry.computeVertexNormals();mesh(riverGeometry,waterMaterial);
  const roads=addWhiteRoads({scene,data,profile,mat,layout:roadLayout});
  host.dataset.adjustedRoads=String(roadLayout.adjusted);
  host.dataset.lowRiverBridges=String(roadLayout.roads.filter(r=>r.bridgeProfile==='river').length);
  const cityWalls=addCityWalls({scene,profile,data:data.cityWalls,mat});
  host.dataset.wallSegments=String(cityWalls.userData.segments||0);host.dataset.wallGates=String(cityWalls.userData.gates||0);host.dataset.wallsVisible='true';
  host.dataset.roads=String(data.roads.length);host.dataset.piers=String(roads.pierCount);
  host.dataset.roadComponents=String(data.road_network.audit.components);host.dataset.interiorRoadEnds=String(data.road_network.audit.interior_dead_ends);

  const modelGroup=new THREE.Group(),placeholderGroup=new THREE.Group(),treeGroup=new THREE.Group();scene.add(modelGroup,placeholderGroup,treeGroup);placeholderGroup.visible=false;
  const clickable=[],anchors=new Map(),labels=[],modelErrors=[];
  scene.children.forEach(o=>{if(o.userData.id==='xuanwu')clickable.push(o);});
  const labelLayer=document.createElement('div');labelLayer.className='scene-labels';host.appendChild(labelLayer);
  const desc={
    aoti:'河西的南京奥体中心体育场，两道红色斜拱托起银灰色环形屋盖，开放的内场保留看台、跑道和足球场。',
    'yangtze-bridge':'从长江大桥开始，沿东岸走入南京。双层桁架和桥头堡是这处地标的识别特征。',
    yuejiang:'金瓦朱柱的四层外观、层叠回廊与歇山重檐构成阅江楼轮廓，侧翼与石台坐落于狮子山。',
    zifeng:'蓝灰玻璃幕墙沿折面塔身逐级退台，银灰竖框与偏置尖顶构成鼓楼天际线的高点。',
    jiming:'黄墙灰瓦的寺殿与七层八面的药师佛塔组成紧凑寺院，朱红回廊、塔檐和石阶依次展开。',
    xuanwu:'湖泊与洲岛构成城北的开阔留白。向东望去，是钟山的绿色轮廓。',
    mingxiaoling:'黄瓦重檐、朱红明楼与石砌方城，中央拱洞贯穿城台，呈现明孝陵的标志性轮廓。',
    zhongshan:'蓝色屋顶、白色祭堂和台阶轴线，让这处山间地标一眼可辨。',
    meiling:'绿瓦、浅色墙体和红柱门廊，配以石栏阳台与分层窗格，呈现美龄宫的别墅轮廓。',
    museum:'老大殿的单檐黄瓦顶覆盖九开间红柱长廊，两侧附殿与白石台阶展开对称的轮廓。',
    presidential:'白色西式门楼的三道拱门通向中式院落，灰瓦回廊与接待大堂沿中轴展开。',
    fuzimiao:'双檐灰瓦的大成殿、朱红格扇与两侧庑廊围合石庭，沿秦淮河形成老城南的庙学景观。',
    zhonghua:'四道券门沿中轴贯通三重瓮城，城台、藏兵洞与登城石阶保留了厚重的防御建筑轮廓。',
    baoen:'中华门以南的现代大报恩塔，以九层八面塔身、浅蓝玻璃、白色框架和修长塔刹表现。',
    'nanjing-eye':'河西与江心洲之间的步行桥。两座向岸侧倾斜的椭圆索塔跨过夹江，收束这段滨江漫游。'
  };
  for(const p of data.landmarks){
    const [x,z]=world(p.source_px),y=height(p.source_px)+.18;const anchor=new THREE.Vector3(x,y,z);anchors.set(p.id,anchor);
    const root=new THREE.Group();root.position.copy(anchor);root.userData.id=p.id;modelGroup.add(root);
    const proxy=mesh(new THREE.CylinderGeometry(p.id==='xuanwu'?4:2.7,p.id==='xuanwu'?4:2.7,2,12),mat(p.id==='xuanwu'?COLORS.water:0xf1dbad),placeholderGroup);proxy.position.set(x,y+1,z);proxy.userData.id=p.id;clickable.push(proxy);
    const pin=document.createElement('button');pin.className='map-label';pin.textContent=p.name;pin.setAttribute('aria-label','查看'+p.name);pin.onclick=()=>events.onSelect(p.id);labelLayer.appendChild(pin);
    const labelAnchor=anchor.clone(),northPlacement=NORTH_LANDMARK_PLACEMENTS[p.id]||BRIDGE_PLACEMENTS[p.id];
    if(northPlacement){labelAnchor.x+=northPlacement.offsetX;labelAnchor.z+=northPlacement.offsetZ;}
    labels.push({element:pin,anchor:labelAnchor,id:p.id,offset:p.id==='baoen'?[18,12]:p.id==='zhonghua'?[-24,-5]:[0,0]});
    p.description=desc[p.id];p.area=groups[p.zone];p.modelRoot=root;
  }
  const roadLabelDefs=[['北京西路',[329,398]],['虎踞路',[282,432]],['应天大街',[278,568]],['凤台南路',[286,631]]];
  const roadLabels=roadLabelDefs.map(([name,hint])=>{
    let p=hint,distance=Infinity;
    for(const road of data.roads.filter(r=>r.name===name))for(let i=1;i<road.source_px.length;i++){
      const a=road.source_px[i-1],b=road.source_px[i],dx=b[0]-a[0],dy=b[1]-a[1],den=dx*dx+dy*dy;
      const t=den?Math.max(0,Math.min(1,((hint[0]-a[0])*dx+(hint[1]-a[1])*dy)/den)):0;
      const q=[a[0]+dx*t,a[1]+dy*t],d=Math.hypot(q[0]-hint[0],q[1]-hint[1]);if(d<distance){distance=d;p=q;}
    }
    const [x,z]=world(p),el=document.createElement('span');el.className='road-label';el.textContent=name;labelLayer.appendChild(el);return {element:el,anchor:new THREE.Vector3(x,height(p)+.5,z)};
  });

  const urbanFabric=addUrbanFabric({scene,profile,urban:data.urban,mat});
  const treeCount=await addVegetation({profile,parent:treeGroup,mat,trees:buildCityVegetation(profile,data.urban)}).catch(error=>{host.dataset.treeLoadError=error.message;events.onWarning('树木模型暂时未能载入，请刷新重试。');return 0;});
  host.dataset.parcels=String(data.urban?.counts.parcels||0);host.dataset.infillBuildings=String(data.urban?.counts.buildings||0);host.dataset.plantedTrees=String(data.urban?.counts.trees||0);
  treeGroup.add(terrainDetails.shrubs);
  host.dataset.treeAsset=treeGroup.userData.asset;host.dataset.treeTriangles=String(treeGroup.userData.triangles);host.dataset.treeBatches=String(treeGroup.userData.batches);
  host.dataset.hills=profile.hills.map(h=>h.name).join('、');
  host.dataset.treeSpecies=JSON.stringify(treeGroup.userData.speciesCounts);host.dataset.trees=String(treeCount);host.dataset.rocks=String(terrainDetails.rockCount);
  const whiteBuildings=addWhiteBuildings({scene,profile,data:buildingData,mat});
  host.dataset.buildings=String(buildingData.count);host.dataset.buildingsVisible='true';
  // A single ring gives selection feedback without altering the geographic anchor.
  const ring=mesh(new THREE.RingGeometry(5,5.55,64),new THREE.MeshBasicMaterial({color:0x315e4a,transparent:true,opacity:.8,side:THREE.DoubleSide,depthTest:false}));ring.rotation.x=-Math.PI/2;ring.visible=false;ring.renderOrder=5;

  const loader=new GLTFLoader(),landmarkTriangles={};let loaded=0;
  function consolidate(gltf,id){
    const buckets=new Map();gltf.updateMatrixWorld(true);
    gltf.traverse(o=>{if(!o.isMesh)return;const m=o.material,key=m.uuid;let g=o.geometry.clone().applyMatrix4(o.matrixWorld);if(g.index&&!WEB_LANDMARKS[id]){const old=g;g=g.toNonIndexed();old.dispose();}
      // Keep the web asset indexed and preserve its baked vertex contact shading.
      for(const name of Object.keys(g.attributes))if(!['position','normal','uv','color'].includes(name))g.deleteAttribute(name);
      if(!g.getAttribute('uv'))g.setAttribute('uv',new THREE.Float32BufferAttribute(new Float32Array(g.getAttribute('position').count*2),2));
      if(!buckets.has(key))buckets.set(key,{material:m,geometries:[]});buckets.get(key).geometries.push(g);
    });
    const result=new THREE.Group();
    for(const {material,geometries} of buckets.values()){
      const g=mergeGeometries(geometries);geometries.forEach(g=>g.dispose());
      // Detailed web assets carry their own glazed tile, stone and painted timber materials.
      if(!WEB_LANDMARKS[id]){material.roughness=.85;material.metalness=0;}
      const m=mesh(g,material,result);m.castShadow=true;m.userData.id=id;
      // City-wide shadow texels are larger than the detailed stone joints and tiles.
      // Keep its ground shadow without coarse self-shadow artefacts on the asset.
      if(WEB_LANDMARKS[id])m.receiveShadow=false;
      clickable.push(m);
    }
    gltf.traverse(o=>{if(o.isMesh)o.geometry.dispose();});return result;
  }
  const modelLandmarks=data.landmarks.filter(p=>p.id!=='xuanwu');
  const loading=Promise.all(modelLandmarks.map(async p=>{
    try{
      const webAsset=WEB_LANDMARKS[p.id];
      const gltf=await loader.loadAsync('/models/'+p.id+'.glb'+(webAsset?'?v='+webAsset.version:''));if(disposed){gltf.scene.traverse(o=>{if(o.isMesh){o.geometry.dispose();o.material.dispose();}});return;}
      const model=consolidate(gltf.scene,p.id);model.scale.set(1.1,1.35,1.1);
      if(webAsset){model.scale.setScalar(webAsset.scale);model.position.z=webAsset.offsetZ||0;model.position.x=webAsset.offsetX||0;model.position.y=webAsset.offsetY||0;model.rotation.y=webAsset.rotationY||0;}
      landmarkTriangles[p.id]=0;model.traverse(o=>{if(o.isMesh)landmarkTriangles[p.id]+=(o.geometry.index?.count??o.geometry.attributes.position.count)/3;});host.dataset.landmarkTriangles=JSON.stringify(landmarkTriangles);
      if(p.id==='zhonghua'&&!webAsset)model.scale.set(1.05,1.2,.65);
      if(p.id==='baoen'&&!webAsset)model.scale.set(.85,1.4,.85);
      p.modelRoot.add(model);
    }catch(e){modelErrors.push(p.name);events.onWarning('未能载入：'+modelErrors.join('、'));}
    finally{loaded++;events.onProgress(loaded,modelLandmarks.length);}
  })).then(()=>{if(!disposed){renderer.shadowMap.autoUpdate=false;renderer.shadowMap.needsUpdate=true;events.onReady({loaded:modelLandmarks.length-modelErrors.length,failed:modelErrors});host.dataset.ready='true';}});

  function resize(){
    const w=host.clientWidth,h=host.clientHeight;if(!w||!h)return;
    renderer.setSize(w,h);const aspect=w/h,extent=Math.max(310,460/aspect);
    camera.left=-extent*aspect/2;camera.right=extent*aspect/2;camera.top=extent/2;camera.bottom=-extent/2;camera.updateProjectionMatrix();
  }
  const observer=new ResizeObserver(resize);observer.observe(host);
  function setView(next,immediate=false){
    view=next;
    cameraMotion.moveTo({target:new THREE.Vector3(),offset:next==='top'?new THREE.Vector3(0,600,.01):new THREE.Vector3(70,370,360),zoom:1,duration:immediate?0:1.25});
    controls.update();
  }
  setView('iso',true);resize();
  const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();let down=null;
  function pointerDown(e){if(e.button===1)e.preventDefault();down=e.button===0?[e.clientX,e.clientY]:null;}
  function pointerUp(e){
    if(e.button!==0||!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;
    const r=renderer.domElement.getBoundingClientRect();pointer.set((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);raycaster.setFromCamera(pointer,camera);
    const hits=raycaster.intersectObjects(clickable.filter(o=>{let p=o;while(p){if(!p.visible)return false;p=p.parent;}return true;}));
    if(hits.length)events.onSelect(hits[0].object.userData.id);
  }
  renderer.domElement.addEventListener('pointerdown',pointerDown);renderer.domElement.addEventListener('pointerup',pointerUp);
  const v=new THREE.Vector3(),north=new THREE.Vector3(),centre=new THREE.Vector3();let lastDiagnostics=0,lastFrame=0;
  function loop(t){
    if(disposed)return;frame=requestAnimationFrame(loop);const dt=lastFrame?Math.min(.15,(t-lastFrame)/1000):1/60;lastFrame=t;if(document.hidden)return;
    cameraMotion.update(dt);controls.update();
    host.dataset.cameraMoving=String(cameraMotion.active);host.dataset.cameraZoom=camera.zoom.toFixed(3);
    updateWater(reducedMotion.matches?0:t/1000);renderer.render(scene,camera);
    const w=host.clientWidth,h=host.clientHeight,occupied=[];
    const compass=host.parentElement.querySelector('.compass svg');
    if(compass){centre.copy(controls.target).project(camera);north.copy(controls.target).add(new THREE.Vector3(0,0,-10)).project(camera);const angle=Math.atan2(-(north.y-centre.y)*h,(north.x-centre.x)*w)*180/Math.PI+90;compass.style.transform=`rotate(${angle}deg)`;}
    const sorted=[...labels].sort((a,b)=>Number(b.id===selected)-Number(a.id===selected));
    for(const l of sorted){
      v.copy(l.anchor);v.y+=2;v.project(camera);const x=(v.x*.5+.5)*w+l.offset[0],y=(-v.y*.5+.5)*h+l.offset[1]+14;
      const rect=[x-l.element.offsetWidth/2,y,l.element.offsetWidth,24];
      const conflict=occupied.some(b=>rect[0]<b[0]+b[2]+5&&rect[0]+rect[2]+5>b[0]&&rect[1]<b[1]+b[3]+3&&rect[1]+rect[3]+3>b[1]);
      const show=(l.id===selected||!conflict)&&v.z<1&&v.z>-1&&x>16&&x<w-16&&y>50&&y<h-30;
      l.element.style.display=show?'':'none';if(show)occupied.push(rect);
      l.element.style.transform=`translate(${x}px,${y}px) translate(-50%,0)`;l.element.classList.toggle('active',l.id===selected);
    }
    for(const l of roadLabels){v.copy(l.anchor).project(camera);l.element.style.transform=`translate(${(v.x*.5+.5)*w}px,${(-v.y*.5+.5)*h}px) translate(-50%,-50%)`;}
    if(t-lastDiagnostics>1000){host.dataset.drawCalls=renderer.info.render.calls;host.dataset.triangles=renderer.info.render.triangles;lastDiagnostics=t;}
  }
  frame=requestAnimationFrame(loop);
  return {
    loading,
    select(id){
      selected=id;labels.forEach(l=>l.element.setAttribute('aria-pressed',String(l.id===id)));
      if(!id){ring.visible=false;cameraMotion.cancel();return;}
      const p=anchors.get(id),asset=WEB_LANDMARKS[id];
      ring.position.copy(p).y+=.25;ring.visible=!asset;
      const target=p.clone(),offset=view==='top'?new THREE.Vector3(0,600,.01):camera.position.clone().sub(controls.target);
      let zoom=host.clientWidth<680?3:2.3;
      if(asset){
        target.y+=asset.focusHeight;target.z+=asset.offsetZ||0;target.x+=asset.offsetX||0;
        if(view==='iso')offset.fromArray(asset.focusOffset||[260,230,330]);
        zoom=asset.focusZoom||(host.clientWidth<680?9:7);
      }
      cameraMotion.moveTo({target,offset,zoom});
    },
    setView,
    reset(){selected=null;ring.visible=false;labels.forEach(l=>l.element.setAttribute('aria-pressed','false'));setView(view);},
    zoom(factor){cameraMotion.zoomBy(factor);},
    trees(show){treeGroup.visible=show;renderer.shadowMap.needsUpdate=true;},
    walls(show){cityWalls.visible=show;host.dataset.wallsVisible=String(show);renderer.shadowMap.needsUpdate=true;},
    roadNames(show){roadLabels.forEach(l=>l.element.style.visibility=show?'visible':'hidden');},
    models(show){modelGroup.visible=show;placeholderGroup.visible=!show;renderer.shadowMap.needsUpdate=true;},
    buildings(show){whiteBuildings.visible=show;urbanFabric.buildings.visible=show;host.dataset.buildingsVisible=String(show);renderer.shadowMap.needsUpdate=true;},
    dispose(){disposed=true;cancelAnimationFrame(frame);observer.disconnect();cameraMotion.dispose();controls.dispose();renderer.domElement.removeEventListener('pointerdown',pointerDown);renderer.domElement.removeEventListener('pointerup',pointerUp);scene.traverse(o=>{o.geometry?.dispose();if(o.material){(Array.isArray(o.material)?o.material:[o.material]).forEach(m=>m.dispose());}});terrainDetails.dispose();disposeLighting();disposeEnvironment();renderer.dispose();renderer.domElement.remove();labelLayer.remove();},
  };
}
