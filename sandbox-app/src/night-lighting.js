import * as THREE from 'three';

// Lighting art direction, not a survey of each landmark's real opening hours.
// Reuse the asset's material boundaries: no replacement GLBs or extra geometry.
export function landmarkLightStyle(id,name){
  const warm=0xffcf88,cool=0xa8dcff;
  if(/灯磨砂罩/.test(name))return {color:warm,emission:4.2};
  if(/铺石|铺装|桥面|平台石砌/.test(name))return {color:warm,wash:.055};
  if(/匾额/.test(name))return {color:warm,wash:.6};
  if(id==='zifeng'){
    if(/玻璃/.test(name))return {color:warm,emission:2.4,windows:true,spacing:[.65,.62],density:.62,wash:.1};
    if(/铝框|金线/.test(name))return {color:cool,emission:.42,wash:.3};
  }
  if(id==='baoen'&&/玻璃/.test(name))return {color:cool,emission:.95,wash:.18};
  if(id==='baoen'&&/钢构|窗框|檐饰/.test(name))return {color:0xffe1a8,emission:.65,wash:.3};
  if(id==='aoti'){
    if(/红钢拱/.test(name))return {color:0xff6947,wash:1.3,emission:.2};
    if(/屋盖|白钢构/.test(name))return {color:cool,wash:.6};
    if(/草坪|跑道|看台/.test(name))return {color:0xe6f0ff,wash:.62};
  }
  if(id==='nanjing-eye'&&/钢塔|索缆/.test(name))return {color:cool,emission:.35,wash:.6};
  if(/栏杆饰条/.test(name))return {color:warm,emission:1.1,wash:.3};
  if(/玻璃/.test(name)&&!/钢轨/.test(name))return {color:warm,emission:1.75};
  if(/檐饰|彩绘金线/.test(name))return {color:warm,emission:.6,wash:.45};
  if(/琉璃|灰陶瓦/.test(name))return {color:warm,wash:.65};
  if(/石材|墙|桥头堡|石砌|灰砖/.test(name))return {color:warm,wash:.5};
  if(/漆柱|木构|彩绘|门框|门扇|木门|线脚/.test(name))return {color:warm,wash:.7};
  if(/钢构/.test(name))return {color:cool,wash:.48};
  return {color:warm,wash:.12};
}

// The shared uniform is also used by materials arriving after a mode change.
// Normals suppress windows on roofs; derivative filtering keeps distant windows
// from shimmering. Positions are static, so lit rooms never randomly flicker.
export function addNightMaterial(material,night,style){
  if(!material.isMeshStandardMaterial||material.userData.nightLighting)return;
  material.userData.nightLighting=true;
  const previousCompile=material.onBeforeCompile,previousKey=material.customProgramCacheKey();
  const color=new THREE.Color(style.color);
  material.onBeforeCompile=function(shader,renderer){
    previousCompile.call(this,shader,renderer);
    Object.assign(shader.uniforms,{
      uNight:night,uNightColor:{value:color},uNightWash:{value:style.wash||0},
      uNightEmission:{value:style.emission||0},uNightSpacing:{value:new THREE.Vector2(...(style.spacing||[.34,.28]))},
      uNightDensity:{value:style.density??.38},
    });
    shader.vertexShader='varying vec3 vNightPosition;\nvarying vec3 vNightNormal;\n'+shader.vertexShader;
    shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>',`#include <begin_vertex>
      vNightPosition = position;
      vNightNormal = normal;
    `);
    shader.fragmentShader=`
      uniform float uNight, uNightWash, uNightEmission, uNightDensity;
      uniform vec3 uNightColor;
      uniform vec2 uNightSpacing;
      varying vec3 vNightPosition;
      varying vec3 vNightNormal;
      float roomRandom(vec2 cell) {
        vec3 p = fract(vec3(cell.xyx) * .1031);
        p += dot(p, p.yzx + 33.33);
        return fract((p.x + p.y) * p.z);
      }
      float roomMask(vec2 coords) {
        vec2 grid = coords / uNightSpacing;
        vec2 footprint = max(fwidth(grid), vec2(.0001));
        vec2 edge = abs(fract(grid) - .5);
        vec2 pane = 1.0 - smoothstep(vec2(.29,.30) - footprint, vec2(.29,.30) + footprint, edge);
        float occupied = step(1.0 - uNightDensity, roomRandom(floor(grid)));
        // At less than a pixel per room, fade to its average luminous coverage.
        float distant = smoothstep(.7, 2.0, max(footprint.x, footprint.y));
        return mix(pane.x * pane.y * occupied, .348 * uNightDensity, distant);
      }
    `+shader.fragmentShader;
    shader.fragmentShader=shader.fragmentShader.replace('#include <emissivemap_fragment>',`#include <emissivemap_fragment>
      vec3 nightNormal = normalize(vNightNormal);
      float facade = 1.0 - smoothstep(.12, .5, abs(nightNormal.y));
      float wash = .45 + .55 * abs(dot(nightNormal, normalize(vec3(.5,.65,1.0))));
      float rooms = 1.0;
      ${style.windows?`vec2 facadeUV = vec2(abs(nightNormal.z) > abs(nightNormal.x) ? vNightPosition.x : vNightPosition.z, vNightPosition.y);
      rooms = roomMask(facadeUV) * facade;`:''}
      totalEmissiveRadiance += uNight * uNightColor * (diffuseColor.rgb * uNightWash * wash + uNightEmission * rooms);
    `);
  };
  // Colors and intensities are uniforms, so all opaque accents share a program.
  material.customProgramCacheKey=()=>previousKey+'|night-v1|'+Boolean(style.windows);
  material.needsUpdate=true;
}

export function createNightLighting(){
  const uniform={value:0};
  return {
    uniform,
    registerLandmark(root,id){root.traverse(o=>{if(o.isMesh)for(const m of Array.isArray(o.material)?o.material:[o.material])addNightMaterial(m,uniform,landmarkLightStyle(id,m.name));});},
    registerBuildings(root){root.traverse(o=>{if(o.isMesh)addNightMaterial(o.material,uniform,{color:0xffd39a,emission:1.25,windows:true,density:.38});});},
  };
}

export function createNightTransition(apply){
  let value=0,start=0,target=0,elapsed=0;
  return {
    get value(){return value;},
    get active(){return value!==target;},
    set(night,immediate=false){start=value;target=night?1:0;elapsed=0;if(immediate){value=target;apply(value);}},
    update(dt,immediate=false){
      if(value===target)return;
      elapsed+=Math.max(0,dt);const t=immediate?1:Math.min(1,elapsed/1.2);
      value=t===1?target:THREE.MathUtils.lerp(start,target,t*t*(3-2*t));apply(value);
    },
  };
}
