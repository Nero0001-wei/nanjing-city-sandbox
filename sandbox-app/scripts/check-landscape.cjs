const {chromium}=require('/Users/echo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('node:fs');
(async()=>{
 const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:process.env.SANDBOX_SOFTWARE_RENDER==='1'?['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader']:['--enable-webgl',...(process.platform==='darwin'?['--use-angle=metal']:[])]});
 const page=await browser.newPage({viewport:{width:1600,height:1050},deviceScaleFactor:1,reducedMotion:'reduce'});
 const errors=[],assets=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 page.on('response',r=>{if(r.url().includes('/models/'))assets.push({url:r.url(),status:r.status()});});
 const dir=process.env.SANDBOX_ARTIFACT_DIR||'artifacts/landscape-refresh';fs.mkdirSync(dir,{recursive:true});
 await page.goto('http://127.0.0.1:5173/',{waitUntil:'networkidle'});await page.locator('.scene-host[data-ready="true"]').waitFor({timeout:90000});
 const settle=async()=>{await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));await page.waitForFunction(()=>document.querySelector('.scene-host').dataset.cameraMoving==='false');};
 await settle();await page.screenshot({path:dir+'/overview.png'});const stats=await page.locator('.scene-host').evaluate(e=>({...e.dataset}));
 if(stats.treeLoadError||!stats.treeAsset||stats.treeBatches!=='14')throw new Error('Blender tree asset did not instantiate');
 for(const [name,file] of [['明孝陵','mingxiaoling'],['美龄宫','meiling'],['中山陵','trees-zhongshan'],['大报恩寺','yuhuatai'],['紫峰大厦','wutai-qingliang'],['玄武湖','north-hills'],['南京长江大桥','yangtze'],['南京眼','nanjing-eye'],['中华门','zhonghua']]){
  await page.getByRole('button',{name,exact:true}).click();await page.waitForTimeout(100);await settle();
  if(['大报恩寺','紫峰大厦'].includes(name)){
   for(let i=0;i<2;i++){await page.getByRole('button',{name:'缩小地图',exact:true}).click();await settle();}
  }
  await page.screenshot({path:dir+'/'+file+'.png'});
  if(name==='大报恩寺'){
   await page.getByRole('checkbox',{name:'树木',exact:true}).uncheck();await page.getByRole('checkbox',{name:'建筑白模',exact:true}).uncheck();await page.waitForTimeout(350);await page.screenshot({path:dir+'/yuhuatai-relief.png'});
   await page.getByRole('checkbox',{name:'树木',exact:true}).check();await page.getByRole('checkbox',{name:'建筑白模',exact:true}).check();
  }
 }
 await page.getByRole('button',{name:'俯视地图',exact:true}).click();await page.waitForTimeout(100);await settle();await page.screenshot({path:dir+'/top.png'});
 await page.setViewportSize({width:390,height:844});await page.getByRole('button',{name:'等轴视角',exact:true}).click();await page.waitForTimeout(100);await settle();await page.screenshot({path:dir+'/mobile.png'});
 const gpu=await page.evaluate(()=>{const gl=document.querySelector('.scene-host canvas').getContext('webgl2'),ext=gl.getExtension('WEBGL_debug_renderer_info');return ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER);});
 const report={gpu,stats,assets,errors};fs.writeFileSync(dir+'/browser.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));await browser.close();if(errors.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exit(1)});
