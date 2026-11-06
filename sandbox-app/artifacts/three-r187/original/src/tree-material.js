import {ShaderChunk} from 'three';

// A small wrapped-diffuse term softens the terminator of the leaf masses.
// It uses the real, shadowed light colour: there is no emissive/glow fill.
// The division by (1 + wrap) limits the extra reflected energy.
export function createTreeMaterial(mat){
  const material=mat(0xffffff,{vertexColors:true,roughness:.96,metalness:0});
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
      float treeSurface = treeGrain(vTreePosition*12.0) + .38*treeGrain(vTreePosition*23.0 + vec3(2.7,5.3,1.9));
      diffuseColor.rgb *= 1.0 + treeSurface*.04*treeLeaf*treeDetail;
    `);
    shader.fragmentShader=shader.fragmentShader.replace('#include <normal_fragment_maps>',`#include <normal_fragment_maps>
      // Screen-derivative bump: tiny surface relief only; silhouettes stay geometric.
      float treeHeight = treeSurface * .01 * treeLeaf * treeDetail;
      vec3 treeDx = dFdx(-vViewPosition), treeDy = dFdy(-vViewPosition);
      vec3 treeR1 = cross(treeDy, normal), treeR2 = cross(normal, treeDx);
      float treeDet = dot(treeDx, treeR1);
      if(abs(treeDet) > 1e-10){
        vec3 treeGradient = sign(treeDet)*(dFdx(treeHeight)*treeR1 + dFdy(treeHeight)*treeR2);
        normal = normalize(abs(treeDet)*normal - treeGradient);
      }
    `);
    const diffuse='reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseContribution ) * ( 1.0 - F );';
    const physical=ShaderChunk.lights_physical_pars_fragment;
    if(!physical.includes(diffuse))throw new Error('Tree lighting: Three.js diffuse hook changed');
    shader.fragmentShader=shader.fragmentShader.replace('#include <lights_physical_pars_fragment>',physical.replace(diffuse,`
      float treeWrap = .35;
      float treeNL = dot( geometryNormal, directLight.direction );
      float treeWrappedNL = clamp((treeNL + treeWrap) / (1.0 + treeWrap), 0.0, 1.0) / (1.0 + treeWrap);
      vec3 treeIrradiance = mix(dotNL, treeWrappedNL, .55) * directLight.color;
      reflectedLight.directDiffuse += treeIrradiance * BRDF_Lambert(material.diffuseContribution) * (1.0 - F);
    `));
  };
  material.customProgramCacheKey=()=> 'miniature-tree-diffuse-grain-v2';
  return material;
}
