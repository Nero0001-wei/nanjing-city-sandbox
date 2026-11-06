const {chromium}=require('/Users/echo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('node:fs');
const path=require('node:path');

(async()=>{
  const root=path.resolve(__dirname,'..'),out=path.join(root,'artifacts/tree-refresh');
  const before=process.env.TREE_BEFORE==='1',dir=process.env.SANDBOX_ARTIFACT_DIR?path.resolve(root,process.env.SANDBOX_ARTIFACT_DIR):path.join(out,before?'before/browser':'after');
  fs.mkdirSync(dir,{recursive:true});
  const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--enable-webgl','--use-angle=metal']});
  try{
    const page=await browser.newPage({viewport:{width:1600,height:1050},deviceScaleFactor:1,reducedMotion:'reduce'});
    const errors=[],assets=[];
    page.on('pageerror',e=>errors.push(e.message));
    page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
    page.on('response',r=>{if(r.url().includes('/models/'))assets.push({url:r.url(),status:r.status()});});
    // Diagnostic objects are injected only into this test browser's module response.
    await page.route('**/src/scene.js*',async route=>{
      const response=await route.fetch();let body=await response.text();
      body=body.replace(/scene\.add\(modelGroup,\s*placeholderGroup,\s*treeGroup\);/,'scene.add(modelGroup,placeholderGroup,treeGroup);window.__treeQA={THREE,scene,renderer,camera,controls,treeGroup,profile,data};');
      if(!body.includes('window.__treeQA='))throw Error('Tree QA scene hook was not found');
      await route.fulfill({response,body});
    });
    if(before){
      await page.route('**/src/terrain-profile.js*',async route=>{
        const response=await route.fetch();let body=await response.text();
        // Preserve original planting for the baseline while using current terrain.
        body=body.replace(',landmarkFootprintDistance,shoreRings',',shoreRings');
        await route.fulfill({response,body});
      });
      await page.route('**/models/trees.glb*',route=>route.fulfill({path:path.join(out,'before/树木模型/web/trees.glb'),contentType:'model/gltf-binary'}));
      await page.route('**/src/vegetation.js*',async route=>{
        const response=await route.fetch();let body=await response.text();
        body=body.replace(/createTreeMaterial\((?:mat)?\)/,'mat(0xffffff,{vertexColors:true,roughness:.82})');
        body=body.replace(/\.setRGB\([^)]+\)/,'.setRGB(.93+t.tint*.07,.96+t.tint*.04,.88+t.tint*.1)');
        await route.fulfill({response,body});
      });
    }
    await page.goto('http://127.0.0.1:5173/',{waitUntil:'networkidle'});
    await page.locator('.scene-host[data-ready="true"]').waitFor({timeout:90000});
    const settle=async()=>{
      await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
      await page.waitForFunction(()=>document.querySelector('.scene-host').dataset.cameraMoving==='false');
    };
    await settle();await page.screenshot({path:dir+'/overview.png'});
    const stats=await page.locator('.scene-host').evaluate(el=>({...el.dataset}));
    const rendering=await page.evaluate(()=>{
      const {THREE,renderer,scene,treeGroup}=__treeQA,ground=scene.getObjectByName('continuous-city-terrain');
      const treeMaterial=treeGroup.children.find(o=>o.isInstancedMesh)?.material;
      const gl=renderer.getContext(),eonPrograms=renderer.info.programs.filter(p=>gl.getShaderSource(p.fragmentShader)?.includes('#define USE_DIFFUSE_ROUGHNESS')).length;
      return {threeRevision:THREE.REVISION,pcfShadows:renderer.shadowMap.type===THREE.PCFShadowMap,groundCastsShadow:ground.castShadow,groundReceivesShadow:ground.receiveShadow,
        environment:scene.environment?.name||null,environmentCube:!!scene.environment?.isCubeTexture,environmentIntensity:scene.environmentIntensity,
        treeMaterial:{type:treeMaterial?.type,diffuseRoughness:treeMaterial?.diffuseRoughness,emissive:treeMaterial?.emissive?.getHex()},
        groundDiffuseRoughness:ground.material.diffuseRoughness,eonPrograms};
    });
    if(stats.treeLoadError||stats.treeBatches!=='14')throw Error('Tree library failed to load all batches');
    const clearance=await page.evaluate(()=>{
      const {THREE,treeGroup,data,scene}=window.__treeQA;
      scene.updateMatrixWorld(true);
      const bounds=data.landmarks.filter(p=>p.id!=='xuanwu').map(p=>{
        const model=p.modelRoot.children[0],box=new THREE.Box3();
        model.traverse(o=>{if(o.isMesh){o.geometry.computeBoundingBox();box.union(o.geometry.boundingBox);}});
        return {id:p.id,box,inverse:model.matrixWorld.clone().invert()};
      });
      const overlaps=[],matrix=new THREE.Matrix4(),point=new THREE.Vector3(),local=new THREE.Vector3();
      let instances=0,finite=true;
      for(const mesh of treeGroup.children){
        if(!mesh.name.startsWith('trees-'))continue;
        const pos=mesh.geometry.attributes.position,norm=mesh.geometry.attributes.normal;
        for(let v=0;v<norm.count;v++)finite&&=Number.isFinite(norm.getX(v)+norm.getY(v)+norm.getZ(v));
        for(let i=0;i<mesh.count;i++){
          mesh.getMatrixAt(i,matrix);matrix.premultiply(mesh.matrixWorld);instances++;
          for(const b of bounds){
            let hit=false;
            for(let v=0;v<pos.count;v++){
              point.fromBufferAttribute(pos,v).applyMatrix4(matrix);local.copy(point).applyMatrix4(b.inverse);
              if(local.x>b.box.min.x&&local.x<b.box.max.x&&local.z>b.box.min.z&&local.z<b.box.max.z){hit=true;break;}
            }
            if(hit)overlaps.push({batch:mesh.name,index:i,landmark:b.id});
          }
        }
      }
      return {instances,finiteNormals:finite,projectedFootprintOverlaps:overlaps};
    });
    for(const [name,file] of [['美龄宫','meiling'],['中山陵','zhongshan'],['玄武湖','xuanwu'],['南京长江大桥','yangtze'],['南京眼','nanjing-eye'],['中华门','zhonghua'],['南京奥体中心体育场','aoti']]){
      await page.getByRole('button',{name,exact:true}).click();await settle();
      await page.screenshot({path:dir+'/'+file+'.png'});
      if(file==='meiling'){
        await page.getByRole('button',{name:'放大地图',exact:true}).click();await settle();
        await page.screenshot({path:dir+'/tree-close.png'});
      }
    }
    // Inspect the same tree batch from the opposite side, while preserving the target.
    await page.getByRole('button',{name:'美龄宫',exact:true}).click();await settle();
    await page.evaluate(()=>{
      const {camera,controls}=__treeQA;const d=camera.position.clone().sub(controls.target);
      d.x*=-1;d.z*=-1;camera.position.copy(controls.target).add(d);controls.update();
    });await settle();await page.screenshot({path:dir+'/tree-reverse.png'});
    await page.getByRole('button',{name:'回到全景',exact:true}).click();await settle();
    await page.setViewportSize({width:390,height:844});await settle();await page.screenshot({path:dir+'/mobile.png'});
    const report={before,rendering,stats,clearance,assets,errors};
    fs.writeFileSync(dir+'/browser.json',JSON.stringify(report,null,2));
    console.log(JSON.stringify({rendering,gpu:stats.gpu,trees:stats.trees,triangles:stats.treeTriangles,batches:stats.treeBatches,clearance,errors},null,2));
    if(!before&&(!rendering.environmentCube||rendering.treeMaterial.diffuseRoughness<=0||rendering.eonPrograms<2))throw Error('Sky environment / EON lighting did not reach the GPU');
    if(errors.length||!clearance.finiteNormals||clearance.projectedFootprintOverlaps.length||!rendering.pcfShadows||rendering.groundCastsShadow||!rendering.groundReceivesShadow)process.exitCode=1;
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
