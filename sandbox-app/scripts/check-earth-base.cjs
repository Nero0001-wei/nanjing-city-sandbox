const {chromium}=require('/Users/echo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
(async()=>{
  const out=path.resolve('artifacts/earth-base'),preserved=JSON.parse(fs.readFileSync(path.join(out,'preserved-hashes.json')));
  for(const [file,hash] of Object.entries(preserved))assert.equal(crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'),hash,file);
  const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--enable-webgl','--use-angle=metal']});
  try{
    const page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'}),errors=[];
    page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
    // Inspect the live scene in this test only; ship no global scene handles.
    await page.route('**/src/scene.js*',async route=>{const response=await route.fetch();const source=await response.text();const body=source.replace(/const cameraMotion\s*=\s*createCameraMotion\(camera,\s*controls,\s*\(\)\s*=>\s*reducedMotion\.matches\);/,'$&window.__baseQA={scene,camera,controls,renderer,THREE};');assert.notEqual(body,source,'test scene hook matched');await route.fulfill({response,body});});
    await page.goto('http://127.0.0.1:5173/',{waitUntil:'networkidle'});await page.locator('.scene-host[data-ready="true"]').waitFor({timeout:90000});
    const settle=async()=>{await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));await page.waitForFunction(()=>document.querySelector('.scene-host').dataset.cameraMoving==='false');};
    const shot=async name=>{await settle();await page.screenshot({path:path.join(out,name+'.png'),animations:'disabled'});};
    const result=await page.evaluate(()=>{const {scene,renderer,THREE}=window.__baseQA,b=scene.getObjectByName('layered-earth-base'),floor=scene.getObjectByName('surrounding-floor'),g=scene.getObjectByName('continuous-city-terrain');b.geometry.computeBoundingBox();return {gpu:document.querySelector('.scene-host').dataset.gpu,base:b.userData,bounds:{min:b.geometry.boundingBox.min.toArray(),max:b.geometry.boundingBox.max.toArray()},floorY:floor.position.y,terrainTriangles:g.geometry.index.count/3,terrainCastShadow:g.castShadow,pcf:renderer.shadowMap.type===THREE.PCFShadowMap,materialCount:Array.isArray(b.material)?b.material.length:1};});
    assert(!/swiftshader|llvmpipe/i.test(result.gpu));assert(result.pcf);assert.equal(result.terrainTriangles,107402);assert.equal(result.terrainCastShadow,false);assert.equal(result.bounds.max[1],0);assert(result.floorY<result.bounds.min[1]);
    await shot('overview');
    await page.evaluate(()=>{const q=__baseQA;q.controls.target.set(6,-3,0);q.camera.position.set(90,235,440);q.camera.zoom=1;q.camera.updateProjectionMatrix();q.controls.update();});await shot('low-angle');
    await page.evaluate(()=>{const q=__baseQA;q.controls.target.set(6,-3,0);q.camera.position.set(-170,230,-420);q.camera.zoom=1;q.camera.updateProjectionMatrix();q.controls.update();});await shot('opposite-side');
    await page.getByRole('button',{name:'俯视地图',exact:true}).click();await shot('top-view');
    await page.getByRole('button',{name:'等轴视角',exact:true}).click();await settle();
    for(const name of ['中山陵','南京长江大桥','南京眼']){
      await page.locator('.landmark-button').filter({hasText:name}).click();await settle();
      await page.getByRole('heading',{name,exact:true}).waitFor();await page.getByRole('button',{name:'收起景点详情'}).click();
      await shot(name==='中山陵'?'hill-close':name==='南京眼'?'eye-bridge':'yangtze-bridge');
    }
    await page.getByRole('button',{name:'回到全景',exact:true}).click();await settle();
    await page.setViewportSize({width:390,height:844});await shot('mobile');
    await page.getByRole('button',{name:'图层',exact:true}).click();await page.getByRole('checkbox',{name:'树木',exact:true}).uncheck();await page.getByRole('checkbox',{name:'树木',exact:true}).check();await page.keyboard.press('Escape');
    assert.deepEqual(errors,[]);result.consoleErrors=errors;result.preservedFiles=Object.keys(preserved).length;
    fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
