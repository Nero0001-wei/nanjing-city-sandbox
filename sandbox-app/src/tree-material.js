import {MeshPhysicalMaterial} from 'three';

// r187's EON rough diffuse provides the foliage response. The prefiltered sky
// softens its terminator; all direct BRDF / shadow calculations remain native.
export function createTreeMaterial(){
  const material=new MeshPhysicalMaterial({color:0xffffff,vertexColors:true,roughness:.84,metalness:0,diffuseRoughness:.65,specularIntensity:.32});
  material.name='miniature-foliage-eon';
  material.onBeforeCompile=shader=>{
    shader.vertexShader='varying vec3 vTreePosition;\n'+shader.vertexShader;
    shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nvTreePosition = position;');
    shader.fragmentShader=`varying vec3 vTreePosition;
      float treeGrain(vec3 p){
        return sin(p.x*1.17 + sin(p.z*1.73)) * sin(p.y*1.41 + sin(p.x*.93)) * sin(p.z*1.29 + sin(p.y*1.63));
      }
    `+shader.fragmentShader;
    shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
      // The green/bark ratio distinguishes the shared material's foliage colours.
      float treeLeaf = smoothstep(.81, .86, vColor.g / max(vColor.r, .001));
      float treeFootprint = max(length(dFdx(vTreePosition)), length(dFdy(vTreePosition)));
      float treeDetail = 1.0 - smoothstep(.035, .16, treeFootprint);
      float treeSurface = treeGrain(vTreePosition*15.0) + .28*treeGrain(vTreePosition*29.0 + vec3(2.7,5.3,1.9));
      // Coarser foliage variation fades later, but also vanishes on tiny trees.
      float treeMottle = treeGrain(vTreePosition*3.2) * (1.0 - smoothstep(.16,.6,treeFootprint));
      diffuseColor.rgb *= 1.0 + (treeSurface*.035*treeDetail + treeMottle*.045)*treeLeaf;
    `);
    shader.fragmentShader=shader.fragmentShader.replace('#include <normal_fragment_maps>',`#include <normal_fragment_maps>
      // Screen-derivative bump: tiny surface relief only; silhouettes stay geometric.
      float treeHeight = treeSurface * .005 * treeLeaf * treeDetail;
      vec3 treeDx = dFdx(-vViewPosition), treeDy = dFdy(-vViewPosition);
      vec3 treeR1 = cross(treeDy, normal), treeR2 = cross(normal, treeDx);
      float treeDet = dot(treeDx, treeR1);
      if(abs(treeDet) > 1e-10){
        vec3 treeGradient = sign(treeDet)*(dFdx(treeHeight)*treeR1 + dFdy(treeHeight)*treeR2);
        normal = normalize(abs(treeDet)*normal - treeGradient);
      }
    `);
    shader.fragmentShader=shader.fragmentShader.replace('#include <roughnessmap_fragment>',`#include <roughnessmap_fragment>
      roughnessFactor = mix(.96, .8 + treeSurface*.035*treeDetail, treeLeaf);
    `);
    // Do not wrap the EON cosine: it would illuminate its grazing-angle
    // singularity outside the BRDF's supported hemisphere and cause bright dots.
  };
  material.customProgramCacheKey=()=> 'miniature-tree-eon-v4-r187';
  return material;
}
