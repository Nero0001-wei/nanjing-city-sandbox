import * as THREE from 'three';
import {world,BOUNDS,clipSegment,seededRandom} from './geo.js';
import {noise,smooth} from './terrain-profile.js';
import {PALETTE,createGroundGrain} from './render-style.js';
export {addVegetation} from './vegetation.js';

// All surfaces use the same immutable map coordinates; no shoreline is relocated.
export function addTerrainSurfaces({scene,profile,mat,mesh}){
  const grass=new THREE.Color(PALETTE.grass),meadow=new THREE.Color(PALETTE.meadow),forest=new THREE.Color(PALETTE.forest),summit=new THREE.Color(PALETTE.summit);
  const grain=createGroundGrain(),groundMaterial=new THREE.MeshStandardMaterial({vertexColors:true,roughness:.93,bumpMap:grain,bumpScale:.035});
  function colorAt(p,h){
    const patch=noise(p[0]/52,p[1]/52)*.58+noise(p[0]/18,p[1]/18)*.3+noise(p[0]/5,p[1]/5)*.12;
    const c=grass.clone().lerp(meadow,smooth(.18,.82,patch)*.78);
    const woody=smooth(.4,9,h);c.lerp(forest,woody*.85);c.lerp(summit,smooth(22,38,h)*.27);
    return c;
  }
  function grid(bounds,step,elevation){
    const [left,top,right,bottom]=bounds,nx=Math.ceil((right-left)/step),ny=Math.ceil((bottom-top)/step),positions=[],colors=[],uvs=[],indices=[];
    for(let j=0;j<=ny;j++)for(let i=0;i<=nx;i++){
      const p=[left+(right-left)*i/nx,top+(bottom-top)*j/ny],[x,z]=world(p),h=elevation?profile.height(p):0,c=colorAt(p,h);
      positions.push(x,h+(elevation ? .012 : 0),z);colors.push(c.r,c.g,c.b);uvs.push(x/12,z/12);
    }
    for(let j=0;j<ny;j++)for(let i=0;i<nx;i++){const a=j*(nx+1)+i,b=a+1,c=a+nx+1,d=c+1;indices.push(a,c,b,b,c,d);}
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uvs,2));g.setIndex(indices);g.computeVertexNormals();
    const m=mesh(g,groundMaterial,scene);m.castShadow=elevation;return m;
  }
  grid(BOUNDS,6,false);
  grid([468,282,678,458],1.8,true);
  grid([232,246,286,300],1.5,true);

  // Layered sand/stone shoreline + water-side shallows. The contour's centre stays fixed.
  const bankPos=[],bankColors=[],shallowPos=[],shallowColors=[];
  const sand=new THREE.Color(PALETTE.sand),lip=new THREE.Color(PALETTE.bank),shallow=new THREE.Color(PALETTE.shallow),deep=new THREE.Color(PALETTE.water);
  function ribbon(a,b,na,nb,inner,outer,y0,y1,c0,c1,pos,colors){
    const cut=clipSegment(a,b);if(!cut)return;
    const d=Math.hypot(b[0]-a[0],b[1]-a[1]);if(d<.001)return;
    const ta=Math.hypot(cut[0][0]-a[0],cut[0][1]-a[1])/d,tb=Math.hypot(cut[1][0]-a[0],cut[1][1]-a[1])/d;
    const ma=na.map((v,i)=>v+(nb[i]-v)*ta),mb=na.map((v,i)=>v+(nb[i]-v)*tb);
    const [ax,az]=world(cut[0]),[bx,bz]=world(cut[1]);
    const points=[[ax+ma[0]*inner,y0,az+ma[1]*inner],[bx+mb[0]*inner,y0,bz+mb[1]*inner],[bx+mb[0]*outer,y1,bz+mb[1]*outer],[ax+ma[0]*outer,y1,az+ma[1]*outer]];
    for(const i of [0,1,2,0,2,3]){pos.push(...points[i]);const c=i<2?c0:c1;colors.push(c.r,c.g,c.b);}
  }
  for(const sourceRing of profile.shoreRings){
    const ring=sourceRing.filter((p,i)=>i===0||Math.hypot(p[0]-sourceRing[i-1][0],p[1]-sourceRing[i-1][1])>.001);
    if(Math.hypot(ring[0][0]-ring.at(-1)[0],ring[0][1]-ring.at(-1)[1])<.001)ring.pop();
    const normals=ring.map((a,i)=>{const b=ring[(i+1)%ring.length],d=Math.hypot(b[0]-a[0],b[1]-a[1]);return [-(b[1]-a[1])/d,(b[0]-a[0])/d];});
    const votes=ring.reduce((sum,a,i)=>{const b=ring[(i+1)%ring.length],n=normals[i];return sum+(profile.isWater([(a[0]+b[0])/2+n[0]*.8,(a[1]+b[1])/2+n[1]*.8])?1:-1);},0);
    const side=votes>=0?1:-1;
    const joined=normals.map((n,i)=>{const prev=normals[(i+ring.length-1)%ring.length],x=n[0]+prev[0],y=n[1]+prev[1],d=Math.hypot(x,y);if(d<.01)return n.map(v=>v*side);const factor=Math.min(1.6,1/Math.max(.15,(x*n[0]+y*n[1])/d));return [x/d*factor*side,y/d*factor*side];});
    for(let i=0;i<ring.length;i++){
      const j=(i+1)%ring.length,a=ring[i],b=ring[j];
      ribbon(a,b,joined[i],joined[j],-.23,.18,.15,.105,lip,sand,bankPos,bankColors);
      ribbon(a,b,joined[i],joined[j],.18,.85,.102,.091,shallow,deep,shallowPos,shallowColors);
    }
  }
  for(const [positions,colors] of [[bankPos,bankColors],[shallowPos,shallowColors]]){
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));g.computeVertexNormals();mesh(g,mat(0xffffff,{vertexColors:true,side:THREE.DoubleSide}));
  }

  // Sparse rock clusters sit on natural slopes; reserve generous landmark and road clearance.
  const random=seededRandom(9918),rocks=[],shrubs=[];
  for(let i=0;i<7000&&rocks.length<50;i++){
    const p=[475+random()*195,288+random()*158],h=profile.height(p);
    const slope=Math.hypot(profile.height([p[0]+1,p[1]])-h,profile.height([p[0],p[1]+1])-h);
    if(h<7||slope<.33||profile.landmarkDistance(p)<23||profile.roadDistance(p,8)<7||profile.occupied(p,3))continue;
    rocks.push({p,h,size:.45+random()*1.1,turn:random()*Math.PI});
  }
  const rockMesh=new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1,0),mat(0xffffff),rocks.length),dummy=new THREE.Object3D();
  rocks.forEach((r,i)=>{const [x,z]=world(r.p);dummy.position.set(x,r.h+r.size*.22,z);dummy.scale.set(r.size,r.size*.7,r.size*.8);dummy.rotation.set(random()*.3,r.turn,random()*.2);dummy.updateMatrix();rockMesh.setMatrixAt(i,dummy.matrix);rockMesh.setColorAt(i,new THREE.Color(['#c9bea3','#b9b49b','#d7cdb5'][Math.floor(random()*3)]));});
  rockMesh.castShadow=true;rockMesh.receiveShadow=true;scene.add(rockMesh);
  for(let i=0;i<5000&&shrubs.length<230;i++){
    const p=[40+random()*640,180+random()*495];
    const shore=profile.shoreDistance(p,12);
    if(shore>8||shore<1.5||profile.isWater(p)||profile.landmarkDistance(p)<17||profile.roadDistance(p,4)<2.5||profile.riverDistance(p,4)<2.5||profile.occupied(p,2))continue;
    shrubs.push({p,h:profile.height(p),size:.35+random()*.5});
  }
  const shrubMesh=new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1,1),mat(0x8fbd50),shrubs.length);
  shrubs.forEach((s,i)=>{const [x,z]=world(s.p);dummy.position.set(x,s.h+s.size*.45,z);dummy.scale.set(s.size,s.size*.7,s.size*.85);dummy.rotation.set(0,random()*6,0);dummy.updateMatrix();shrubMesh.setMatrixAt(i,dummy.matrix);});
  shrubMesh.receiveShadow=true;scene.add(shrubMesh);
  return {shrubs:shrubMesh,rockCount:rocks.length,dispose:()=>grain.dispose()};
}

export function addWaterFinish(material){
  // A quiet animated surface, without displacing boundaries or geographic anchors.
  const clock={value:0};
  material.roughness=.42;material.metalness=0;material.shadowSide=THREE.BackSide;
  material.onBeforeCompile=shader=>{
    shader.uniforms.uWaterTime=clock;
    shader.vertexShader='varying vec2 vWaterWorld;\n'+shader.vertexShader;
    shader.vertexShader=shader.vertexShader.replace('#include <worldpos_vertex>','#include <worldpos_vertex>\nvWaterWorld = (modelMatrix * vec4(transformed, 1.0)).xz;');
    shader.fragmentShader='varying vec2 vWaterWorld;\nuniform float uWaterTime;\n'+shader.fragmentShader;
    shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
      float bend = sin(vWaterWorld.y * .31) * .75 + sin(vWaterWorld.x * .17) * .4;
      float flow = sin(vWaterWorld.x * 3.5 + vWaterWorld.y * .65 + bend + uWaterTime * .25);
      float broken = smoothstep(.35, .85, sin(vWaterWorld.y * 1.45 + sin(vWaterWorld.x * .12) * 2.3));
      float glint = pow(max(0.0, flow), 38.0) * broken;
      float broad = sin(vWaterWorld.x * .05 + sin(vWaterWorld.y * .04));
      diffuseColor.rgb *= .985 + broad * .015 + glint * .045;
    `);
  };
  material.customProgramCacheKey=()=> 'nanjing-water-v3';
  return seconds=>{clock.value=seconds;};
}
