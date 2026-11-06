const {chromium}=require('/Users/echo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('node:fs');
(async()=>{
 const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--enable-webgl','--use-angle=metal']});
 const page=await browser.newPage({viewport:{width:1600,height:1100},deviceScaleFactor:1,reducedMotion:'reduce'}),errors=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 // Test-only instrumentation; no diagnostic globals are added to the shipped app.
 await page.route('**/src/render-style.js',async route=>{const response=await route.fetch();let body=await response.text();body=body.replace('scene.add(key);','scene.add(key);window.__shadowQA={THREE,scene,renderer,key};');await route.fulfill({response,body});});
 await page.goto('http://127.0.0.1:5173/?landmark=mingxiaoling',{waitUntil:'networkidle'});await page.locator('.scene-host[data-ready="true"]').waitFor({timeout:90000});
 const settle=async()=>{await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));await page.waitForFunction(()=>Number(document.querySelector('.scene-host').dataset.cameraZoom)>6.99&&document.querySelector('.scene-host').dataset.cameraMoving==='false');};
 // Reproduce the former settings explicitly, even after the application is fixed.
 await page.evaluate(()=>{const q=__shadowQA;q.renderer.shadowMap.type=q.THREE.VSMShadowMap;q.key.shadow.radius=4;q.key.shadow.blurSamples=8;q.scene.getObjectByName('continuous-city-terrain').castShadow=true;q.renderer.shadowMap.needsUpdate=true;});
 await settle();
 const gpu=await page.evaluate(()=>{const gl=__shadowQA.renderer.getContext(),ext=gl.getExtension('WEBGL_debug_renderer_info');return {renderer:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER),shadowType:__shadowQA.renderer.shadowMap.type,shadowTexture:__shadowQA.key.shadow.map.texture.type};});
 await page.screenshot({path:'artifacts/terrain-shadow/01-vsm-metal.png'});
 await page.evaluate(()=>{const q=__shadowQA;const g=q.scene.getObjectByName('continuous-city-terrain');g.receiveShadow=false;g.material.needsUpdate=true;q.renderer.shadowMap.needsUpdate=true;});await settle();await page.screenshot({path:'artifacts/terrain-shadow/02-ground-no-shadow.png'});
 await page.evaluate(()=>{const q=__shadowQA;const g=q.scene.getObjectByName('continuous-city-terrain');g.receiveShadow=true;g.castShadow=false;q.renderer.shadowMap.type=q.THREE.PCFShadowMap;q.key.shadow.radius=1.5;q.renderer.shadowMap.needsUpdate=true;});await settle();await page.screenshot({path:'artifacts/terrain-shadow/03-pcf-metal.png'});
 fs.writeFileSync('artifacts/terrain-shadow/diagnosis.json',JSON.stringify({gpu,errors},null,2));console.log({gpu,errors});await browser.close();if(errors.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exit(1)});
