const {chromium}=require('/Users/echo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
 const b=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const p=await b.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});const errors=[];p.on('pageerror',e=>errors.push(e.message));p.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 await p.goto('http://127.0.0.1:5173/',{waitUntil:'networkidle'});await p.locator('.scene-host[data-ready="true"]').waitFor();
 await p.getByRole('button',{name:'中山陵',exact:true}).click();await p.waitForTimeout(1700);await p.screenshot({path:'artifacts/terrain/zhongshan.png'});
 await p.getByRole('checkbox',{name:'树木',exact:true}).uncheck();await p.waitForTimeout(400);await p.screenshot({path:'artifacts/terrain/relief.png'});
 await p.getByRole('checkbox',{name:'树木',exact:true}).check();await p.getByRole('button',{name:'玄武湖',exact:true}).click();await p.waitForTimeout(1600);await p.screenshot({path:'artifacts/terrain/xuanwu.png'});
 console.log('ERRORS',errors);await b.close();if(errors.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exit(1)});
