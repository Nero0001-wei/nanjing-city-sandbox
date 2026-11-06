import * as THREE from 'three';
import {mergeGeometries} from 'three/addons/utils/BufferGeometryUtils.js';
import {world,SCALE,seededRandom} from './geo.js';

export const TREE_SPECIES=['camphor','plane','ginkgo','willow','pine','cedar','blossom'];
const LEAVES={
  camphor:['#70af43','#89bf49','#5b9e3d'],plane:['#91bd43','#a3cd50','#7db543'],
  ginkgo:['#b8cf49','#d0d963','#a1c449'],willow:['#8dc657','#a5d16b','#73b44f'],
  pine:['#4b9c55','#64b05c','#3d8c4e'],cedar:['#398b5b','#56a96a','#377e52'],
  blossom:['#e8b2ce','#f0c2d2','#d995b6'],
};

// These are artistic tree families, not an inventory of real planted species.
export function treeAppearance(tree,profile,index){
  const random=seededRandom(Math.round(tree.p[0]*179+tree.p[1]*307)+index*31);
  const mountain=profile.mountainMask(tree.p)>.08,water=profile.shoreDistance(tree.p,14)<11;
  const r=random();let species;
  if(mountain)species=r<.25?'cedar':r<.49?'pine':r<.82?'camphor':r<.94?'ginkgo':'plane';
  else if(water)species=r<.32?'willow':r<.56?'plane':r<.74?'camphor':r<.9?'ginkgo':'blossom';
  else species=r<.32?'plane':r<.60?'camphor':r<.78?'ginkgo':r<.87?'pine':r<.94?'cedar':'blossom';
  species=tree.species||species;
  return {...tree,species,variant:Math.floor(random()*3),scale:tree.size*(.85+random()*.17),stretch:.9+random()*.22,tint:random()};
}

export function createTreeGeometry(species,variant=0,compact=false){
  const parts=[],crowns=[],random=seededRandom(2143+TREE_SPECIES.indexOf(species)*117+variant*431);
  const palette=LEAVES[species],rotation=new THREE.Quaternion(),up=new THREE.Vector3(0,1,0);
  function part(geometry,position,scale,color,quaternion=null){
    geometry.scale(...scale);if(quaternion)geometry.applyQuaternion(quaternion);geometry.translate(...position);
    const g=geometry.index?geometry.toNonIndexed():geometry;if(g!==geometry)geometry.dispose();
    if(g.getAttribute('uv'))g.deleteAttribute('uv');
    const colors=[],base=new THREE.Color(color),p=g.getAttribute('position');
    for(let i=0;i<p.count;i++){
      const lift=THREE.MathUtils.clamp((p.getY(i)-1.1)/3,0,1),c=base.clone().multiplyScalar(.85+lift*.24);
      colors.push(c.r,c.g,c.b);
    }
    g.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));parts.push(g);return g;
  }
  function branch(a,b,r=.07){
    const va=new THREE.Vector3(...a),vb=new THREE.Vector3(...b),direction=vb.clone().sub(va);
    rotation.setFromUnitVectors(up,direction.clone().normalize());
    part(new THREE.CylinderGeometry(r*.72,r,direction.length(),6),va.add(vb).multiplyScalar(.5).toArray(),[1,1,1],'#92724a',rotation);
  }
  const leaf=(p,s,color=palette[Math.floor(random()*palette.length)],detail=compact?0:1)=>{
    const geometry=new THREE.IcosahedronGeometry(1,detail),positions=geometry.getAttribute('position'),phase=random()*Math.PI*2;
    // Small coherent irregularities remove the perfect-sphere appearance.
    // Repeated vertices use the same field, keeping each leaf cluster closed.
    for(let i=0;i<positions.count;i++){
      const x=positions.getX(i),y=positions.getY(i),z=positions.getZ(i),r=1+Math.sin(x*7+phase)*Math.sin(y*8-z*5+phase)*.065;
      positions.setXYZ(i,x*r,y*r,z*r);
    }
    const g=part(geometry,p,s,color);crowns.push({geometry:g,p,s});
  };
  const ring=(count,radius,y,sizes,phase=0)=>{
    for(let j=0;j<count;j++){
      const a=phase+j/count*Math.PI*2+(random()-.5)*.35;
      leaf([Math.cos(a)*radius,y+(random()-.5)*.26,Math.sin(a)*radius],sizes.map(s=>s*(.88+random()*.22)));
    }
  };
  if(species==='cedar'){
    branch([0,0,0],[.05,4.1,0],.14);
    for(let j=0;j<5;j++){
      const r=1.05-j*.18;
      part(new THREE.ConeGeometry(r,1.45-j*.08,10),[0,1.25+j*.58,0],[1,1,.9],palette[j%3]);
    }
  }else if(species==='pine'){
    branch([0,0,0],[.18,3.25,0],.16);
    for(let j=0;j<3;j++){
      const angle=j*2.6+variant*.7,radius=.7-j*.12,tip=[Math.cos(angle)*radius,1.9+j*.62,Math.sin(angle)*radius];
      branch([.1,1.2+j*.6,0],tip,.08);leaf(tip,[.95-j*.15,.47,.76-j*.08]);
      leaf([tip[0]+.35,tip[1]+.15,tip[2]+.18],[.6,.43,.56]);
    }
    leaf([.12,3.55,0],[.66,.55,.63]);
  }else if(species==='willow'){
    branch([0,0,0],[.1,2.5,0],.14);
    leaf([0,2.8,0],[.91,.7,.88]);
    for(let j=0;j<6;j++){
      const a=j/6*Math.PI*2,tip=[Math.cos(a)*.69,2.45,Math.sin(a)*.69];branch([0,1.7,0],tip,.05);
      leaf([tip[0],2.05+(random()-.5)*.15,tip[2]],[.46,1.02,.43]);
    }
  }else if(species==='ginkgo'){
    branch([0,0,0],[0,3.2,0],.13);
    ring(3,.45,2.55,[.65,.77,.6],variant*.8);
    ring(4,.68,3.12,[.62,.65,.62],.4);
    leaf([0,3.65,0],[.59,.51,.6]);
  }else if(species==='plane'){
    branch([0,0,0],[.04,2.3,0],.18);
    for(let j=0;j<3;j++){const a=j/3*Math.PI*2;branch([0,1.15,0],[Math.cos(a)*.8,2.35,Math.sin(a)*.8],.1);}
    ring(5,.68,2.55,[.69,.61,.65],variant*.3);
    ring(3,.35,3.12,[.7,.63,.64],.6);
  }else if(species==='blossom'){
    branch([0,0,0],[.1,2,0],.13);
    ring(5,.58,2.2,[.62,.64,.59],variant*.9);ring(3,.25,2.76,[.59,.55,.56]);
    for(let j=0;j<5;j++){const a=j*2.4;leaf([Math.cos(a)*.82,2.6+(j%2)*.3,Math.sin(a)*.82],[.23,.25,.23],'#fae1d9',0);}
  }else{
    branch([0,0,0],[.08,2.5,0],.18);
    ring(4,.55,2.3,[.75,.8,.69],variant*.4);ring(3,.32,3.05,[.69,.72,.64],.6);
    leaf([.08,3.52,0],[.54,.5,.5]);
  }
  // Bake gentle contact occlusion between leaf clusters into vertex colour.
  // This preserves small canopy creases without adding a screen-space pass.
  for(const crown of crowns){
    const p=crown.geometry.getAttribute('position'),normal=crown.geometry.getAttribute('normal'),colors=crown.geometry.getAttribute('color');
    for(let i=0;i<p.count;i++){
      let occlusion=1;
      for(const other of crowns){
        if(other===crown)continue;
        const dx=other.p[0]-p.getX(i),dy=other.p[1]-p.getY(i),dz=other.p[2]-p.getZ(i),length=Math.hypot(dx,dy,dz)||1;
        const distance=Math.hypot(dx/other.s[0],dy/other.s[1],dz/other.s[2]);
        const facing=Math.max(0,(normal.getX(i)*dx+normal.getY(i)*dy+normal.getZ(i)*dz)/length);
        occlusion=Math.min(occlusion,1-.18*(1-THREE.MathUtils.smoothstep(distance,.95,1.45))*facing);
      }
      colors.setXYZ(i,colors.getX(i)*occlusion,colors.getY(i)*occlusion,colors.getZ(i)*occlusion);
    }
  }
  const result=mergeGeometries(parts);parts.forEach(g=>g.dispose());result.computeBoundingBox();result.computeBoundingSphere();return result;
}

export function addVegetation({profile,parent,mat,trees:sourceTrees=profile.buildVegetation()}){
  const trees=sourceTrees.map((tree,i)=>treeAppearance(tree,profile,i)),batches=new Map(),counts={};
  for(const t of trees){const key=t.species+':'+t.variant+':'+(t.size<.7?'compact':'full');if(!batches.has(key))batches.set(key,[]);batches.get(key).push(t);counts[t.species]=(counts[t.species]||0)+1;}
  const material=mat(0xffffff,{vertexColors:true,roughness:.82}),dummy=new THREE.Object3D();
  for(const list of batches.values()){
    const {species,variant}=list[0],geometry=createTreeGeometry(species,variant,list[0].size<.7),mesh=new THREE.InstancedMesh(geometry,material,list.length);mesh.name='trees-'+species+'-'+variant;
    const vertices=geometry.getAttribute('position');let radius=0;
    for(let i=0;i<vertices.count;i++)radius=Math.max(radius,Math.hypot(vertices.getX(i),vertices.getZ(i)));
    list.forEach((t,i)=>{
      // Keep the richer crowns clear of the previously repaired road network
      // and the building footprint exclusion margin, even for wide pine shapes.
      t.scale=Math.min(t.scale,(profile.roadDistance(t.p,6)*SCALE-.12)/radius,((t.clearance||3.5)*SCALE-.12)/radius);
      const [x,z]=world(t.p);dummy.position.set(x,t.y,z);dummy.rotation.set(0,t.turn,0);dummy.scale.set(t.scale,t.scale*t.stretch,t.scale);dummy.updateMatrix();mesh.setMatrixAt(i,dummy.matrix);
      mesh.setColorAt(i,new THREE.Color().setRGB(.93+t.tint*.07,.96+t.tint*.04,.88+t.tint*.1));
    });
    mesh.castShadow=true;mesh.receiveShadow=true;parent.add(mesh);
  }
  // A subtle, soft contact shade grounds each trunk even under broad lighting.
  const shadowMaterial=new THREE.ShaderMaterial({transparent:true,depthWrite:false,uniforms:{color:{value:new THREE.Color('#375e37')}},
    vertexShader:'varying vec2 vUv; void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*instanceMatrix*vec4(position,1.0);}',
    fragmentShader:'varying vec2 vUv; uniform vec3 color; void main(){float d=length((vUv-.5)*2.0);float a=(1.0-smoothstep(.1,1.0,d))*.14;gl_FragColor=vec4(color,a);#include <tonemapping_fragment>\n#include <colorspace_fragment>\n}',
  });
  // Shader preprocessor directives must begin on their own line.
  shadowMaterial.fragmentShader=shadowMaterial.fragmentShader.replace(';#include',';\n#include');
  const contacts=new THREE.InstancedMesh(new THREE.PlaneGeometry(1,1).rotateX(-Math.PI/2),shadowMaterial,trees.length);contacts.name='tree-contact-shade';
  const up=new THREE.Vector3(0,1,0);
  trees.forEach((t,i)=>{
    const [x,z]=world(t.p),dx=(profile.height([t.p[0]+.5,t.p[1]])-profile.height([t.p[0]-.5,t.p[1]]))/SCALE;
    const dz=(profile.height([t.p[0],t.p[1]+.5])-profile.height([t.p[0],t.p[1]-.5]))/SCALE;
    dummy.position.set(x,t.y+.035,z);dummy.quaternion.setFromUnitVectors(up,new THREE.Vector3(-dx,1,-dz).normalize());dummy.scale.set(t.scale*2.8,1,t.scale*2.8);dummy.updateMatrix();contacts.setMatrixAt(i,dummy.matrix);
  });
  parent.add(contacts);parent.userData.speciesCounts=counts;
  return trees.length;
}
