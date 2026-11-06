const {chromium}=require('/Users/echo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
 const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});const errors=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 await page.goto('http://127.0.0.1:5173/',{waitUntil:'networkidle'});await page.locator('.scene-host[data-ready="true"]').waitFor({timeout:60000});
 for(const [name,file] of [['中华门','south-interchange'],['紫峰大厦','north-interchange'],['南京长江大桥','yangtze-approaches'],['南京眼','eye-bridge']]){
   await page.getByRole('button',{name,exact:true}).click();await page.waitForTimeout(1400);await page.getByRole('button',{name:'关闭景点详情'}).click();
   await page.getByRole('button',{name:'放大地图'}).click();await page.getByRole('button',{name:'放大地图'}).click();
   if(file==='south-interchange'){
     await page.mouse.move(600,600);await page.mouse.down({button:'middle'});await page.mouse.move(900,580,{steps:12});await page.mouse.up({button:'middle'});
   }
   await page.waitForTimeout(700);await page.screenshot({path:`artifacts/roads/${file}.png`});
 }
 console.log('SCENE',await page.locator('.scene-host').evaluate(e=>({...e.dataset})));
 console.log('ERRORS',errors);await browser.close();if(errors.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exit(1)});
