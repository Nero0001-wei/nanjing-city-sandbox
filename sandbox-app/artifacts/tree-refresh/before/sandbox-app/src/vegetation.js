import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {world,SCALE,seededRandom} from './geo.js';
export const TREE_SPECIES=['camphor','plane','ginkgo','willow','pine','cedar','blossom'];
import {TREE_ASSET} from './tree-asset.js';
export {TREE_ASSET};

// Each Blender node contains one low-poly tree at its trunk foot. Retain
// indexed vertices, smooth normals and baked colour; reuse across every instance.
export async function loadTreeLibrary(){
  const gltf=await new GLTFLoader().loadAsync(TREE_ASSET),library=new Map(),materials=new Set();
  gltf.scene.updateMatrixWorld(true);
  gltf.scene.traverse(o=>{
    if(!o.isMesh)return;
    library.set(o.name,o.geometry.clone().applyMatrix4(o.matrixWorld));
    o.geometry.dispose();for(const m of Array.isArray(o.material)?o.material:[o.material])materials.add(m);
  });
  for(const m of materials)m.dispose();
  for(const species of TREE_SPECIES)for(const detail of ['full','compact']){
    const geometry=library.get(species+'_'+detail);
    if(!geometry?.attributes.color)throw new Error('Tree asset missing '+species+'_'+detail+' or vertex colour');
    geometry.computeBoundingBox();geometry.computeBoundingSphere();
  }
  return library;
}

// These are artistic tree families, not an inventory of real planted species.
export function treeAppearance(tree,profile,index){
  const random=seededRandom(Math.round(tree.p[0]*179+tree.p[1]*307)+index*31);
  const mountain=(profile.woodlandMask||profile.mountainMask)(tree.p)>.08,water=profile.shoreDistance(tree.p,14)<11;
  const r=random();let species;
  if(mountain)species=r<.25?'cedar':r<.49?'pine':r<.82?'camphor':r<.94?'ginkgo':'plane';
  else if(water)species=r<.32?'willow':r<.56?'plane':r<.74?'camphor':r<.9?'ginkgo':'blossom';
  else species=r<.32?'plane':r<.60?'camphor':r<.78?'ginkgo':r<.87?'pine':r<.94?'cedar':'blossom';
  species=tree.species||species;
  return {...tree,species,variant:Math.floor(random()*3),scale:tree.size*(.85+random()*.17),stretch:.9+random()*.22,tint:random()};
}

export async function addVegetation({profile,parent,mat,trees:sourceTrees=profile.buildVegetation()}){
  const library=await loadTreeLibrary();
  const trees=sourceTrees.map((tree,i)=>treeAppearance(tree,profile,i)),batches=new Map(),counts={};
  for(const t of trees){const key=t.species+'_'+(t.size<.7?'compact':'full');if(!batches.has(key))batches.set(key,[]);batches.get(key).push(t);counts[t.species]=(counts[t.species]||0)+1;}
  const material=mat(0xffffff,{vertexColors:true,roughness:.82}),dummy=new THREE.Object3D();
  let renderedTriangles=0;
  for(const [key,list] of batches){
    const geometry=library.get(key),mesh=new THREE.InstancedMesh(geometry,material,list.length);mesh.name='trees-'+key;
    renderedTriangles+=(geometry.index?.count??geometry.attributes.position.count)/3*list.length;
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
  // Real tree shadows and baked crown colour avoid tangent decals cutting into slopes.
  parent.userData.speciesCounts=counts;parent.userData.triangles=renderedTriangles;parent.userData.batches=batches.size;parent.userData.asset=TREE_ASSET;
  for(const [key,geometry] of library)if(!batches.has(key))geometry.dispose();
  return trees.length;
}
