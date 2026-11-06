// Local integration QA: Chrome/Metal, all 15 guides, local photography and responsive interactions.
const {chromium}=require('/Users/echo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');

(async()=>{
  const root=path.resolve(__dirname,'..'),out=path.join(root,'artifacts/landmark-guide');
  fs.mkdirSync(out,{recursive:true});
  const data=JSON.parse(fs.readFileSync(path.join(root,'public/data/nanjing.json')));
  const photos=JSON.parse(fs.readFileSync(path.join(root,'src/landmark-photos.json')));
  const {landmarkGuides}=await import(pathToFileURL(path.join(root,'src/landmark-guide.js')));
  assert.deepEqual(Object.keys(landmarkGuides).sort(),data.landmarks.map(p=>p.id).sort());
  assert.deepEqual(Object.keys(photos).sort(),Object.keys(landmarkGuides).sort());
  for(const p of data.landmarks){
    const guide=landmarkGuides[p.id];
    assert(guide.paragraphs.join('').length>180,`${p.id}: detailed introduction`);
    assert.equal(guide.highlights.length,3);
    assert(guide.sources.length>0);
    assert.equal(photos[p.id].length,2);
    for(const photo of photos[p.id]){
      assert(photo.author&&photo.license&&photo.sourceUrl&&photo.licenseUrl&&photo.alt);
      for(const asset of [photo.src,photo.thumbnail])assert(fs.statSync(path.join(root,'public',asset)).size>0);
      assert.equal(fs.statSync(path.join(root,'public',photo.src)).size,photo.bytes);
    }
  }
  const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--enable-webgl','--use-angle=metal']});
  try{
    const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});
    const errors=[],failed=[],requestedPhotos=[];
    page.on('pageerror',e=>errors.push(e.message));
    page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
    page.on('response',r=>{if(r.status()>=400)failed.push({url:r.url(),status:r.status()});});
    page.on('request',r=>{if(r.url().includes('/photos/landmarks/'))requestedPhotos.push(r.url());});
    await page.goto(process.env.GUIDE_QA_URL||'http://127.0.0.1:5173/',{waitUntil:'networkidle'});
    await page.locator('.scene-host[data-ready="true"]').waitFor({timeout:90000});
    const gpu=await page.locator('.scene-host').getAttribute('data-gpu');
    assert(!/swiftshader|llvmpipe/i.test(gpu),`Hardware renderer required: ${gpu}`);
    assert.equal(requestedPhotos.length,0,'Photos must not load before a landmark is selected');
    await page.screenshot({path:path.join(out,'desktop-overview.png')});
    async function waitPhoto(){await page.locator('.photo-preview>img').waitFor();await page.waitForFunction(()=>{const img=document.querySelector('.photo-preview>img');return img?.complete&&img.naturalWidth>0;});}
    const checked=[];
    for(const poi of data.landmarks){
      await page.locator('.landmark-button').filter({hasText:poi.name}).click();
      await page.getByRole('heading',{name:poi.name,exact:true}).waitFor();
      await waitPhoto();
      assert.equal(await page.locator('.detail-scroll').evaluate(e=>e.scrollTop),0,'New guide starts at top');
      assert.equal(await page.locator('.guide-highlights li').count(),3);
      assert.equal(await page.locator('.photo-preview>img').getAttribute('src'),photos[poi.id][0].src);
      await page.locator('.photo-choices button').nth(1).click();await waitPhoto();
      assert.equal(await page.locator('.photo-preview>img').getAttribute('src'),photos[poi.id][1].src);
      await page.locator('.guide-sources summary').click();
      assert.equal(await page.locator('.guide-sources a').count(),landmarkGuides[poi.id].sources.length);
      checked.push(poi.id);
    }
    await page.locator('.landmark-button').filter({hasText:'中山陵'}).click();await waitPhoto();
    await page.waitForFunction(()=>document.querySelector('.scene-host')?.dataset.cameraMoving==='false');
    await page.screenshot({path:path.join(out,'desktop-guide.png')});
    await page.locator('.photo-preview').click();
    await page.locator('.photo-dialog[open]').waitFor();
    await page.locator('.photo-full').evaluate(img=>img.decode());
    await page.screenshot({path:path.join(out,'photo-lightbox.png')});
    await page.getByRole('button',{name:'下一张照片'}).click();
    assert.equal(await page.locator('.photo-full').getAttribute('src'),photos.zhongshan[1].src);
    await page.keyboard.press('ArrowLeft');
    assert.equal(await page.locator('.photo-full').getAttribute('src'),photos.zhongshan[0].src);
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('.photo-dialog[open]').count(),0);
    assert.equal(await page.locator('.detail-panel').count(),1,'Escape closes photo, preserves guide');
    assert(await page.locator('.photo-preview').evaluate(e=>e===document.activeElement));
    await page.locator('.detail-scroll').evaluate(e=>e.scrollTop=e.scrollHeight);
    await page.screenshot({path:path.join(out,'desktop-guide-text.png')});
    await page.getByRole('button',{name:'关闭景点详情'}).click();
    assert.equal(await page.locator('.detail-panel').count(),0);
    await page.getByRole('button',{name:'回到全景'}).click();
    await page.getByRole('textbox',{name:'搜索景点'}).fill('奥体');
    assert.equal(await page.locator('.landmark-button').count(),1);
    await page.getByRole('button',{name:'清空搜索'}).click();
    await page.setViewportSize({width:390,height:844});
    await page.getByRole('button',{name:`探索 ${data.landmarks.length} 处风景`}).click();
    await page.locator('.landmark-button').filter({hasText:'南京奥体中心体育场'}).click();await waitPhoto();
    await page.waitForFunction(()=>document.querySelector('.scene-host')?.dataset.cameraMoving==='false');
    await page.screenshot({path:path.join(out,'mobile-guide.png')});
    for(const viewport of [{width:390,height:844},{width:320,height:740},{width:844,height:390}]){
      await page.setViewportSize(viewport);
      const box=await page.locator('.detail-panel').boundingBox();
      assert(box.x>=0&&box.y>=0&&box.x+box.width<=viewport.width+1&&box.y+box.height<=viewport.height,`Panel fits ${JSON.stringify(viewport)}`);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
      assert(await page.locator('.detail-scroll').evaluate(e=>e.clientHeight>=100),'Readable scroll viewport');
      await page.locator('.detail-scroll').evaluate(e=>e.scrollTop=e.scrollHeight);
      assert(await page.locator('.geography-link').isVisible());
    }
    await page.setViewportSize({width:390,height:844});
    await page.locator('.detail-scroll').evaluate(e=>e.scrollTop=0);
    await page.locator('.photo-preview').click();await page.locator('.photo-full').evaluate(img=>img.decode());
    await page.screenshot({path:path.join(out,'mobile-lightbox.png')});
    await page.getByRole('button',{name:'关闭照片大图'}).click();
    assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);
    // Explicitly test the recoverable image failure state after collecting normal network diagnostics.
    await page.route('**/photos/landmarks/zhongshan-1-*.webp',route=>route.abort());
    await page.getByRole('button',{name:`探索 ${data.landmarks.length} 处风景`}).click();
    await page.locator('.landmark-button').filter({hasText:'中山陵'}).click();
    await page.locator('.photo-unavailable').waitFor();
    assert(await page.locator('.photo-gallery .photo-credit a').first().getAttribute('href'));
    const report={gpu,landmarks:checked.length,photos:checked.length*2,checked,initialPhotoRequests:0,normalConsoleErrors:[],normalFailedResponses:[],imageFailureFallback:true,responsiveWidths:[1440,390,320,844],photoBytes:Object.values(photos).flat().reduce((n,p)=>n+p.bytes,0)};
    fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2));
    console.log(JSON.stringify(report,null,2));
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
