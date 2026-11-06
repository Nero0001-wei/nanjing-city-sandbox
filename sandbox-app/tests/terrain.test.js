import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createTerrainProfile} from '../src/terrain-profile.js';
import {ZHONGHUA_PLACEMENT as gate,NORTH_LANDMARK_PLACEMENTS as north} from '../src/landmark-placement.js';
const data=JSON.parse(readFileSync(new URL('../public/data/nanjing.json',import.meta.url)));
const profile=createTerrainProfile(data);

test('approved urban landmark bases stay level and mountain pads remain usable',()=>{
  for(const id of ['zifeng','presidential','zhonghua','baoen'])assert.equal(profile.height(data.landmarks.find(p=>p.id===id).source_px),0);
  for(const id of ['zhongshan','mingxiaoling','meiling','yuejiang']){
    const p=data.landmarks.find(p=>p.id===id).source_px,h=profile.height(p);
    for(const dx of [-7,0,7])for(const dy of [-7,0,7]){
      // Each future Blender model has a flat central footprint, not a terrain spike.
      if(Math.hypot(dx,dy)<=8)assert.ok(Math.abs(profile.height([p[0]+dx,p[1]+dy])-h)<.01,id);
    }
  }
});
test('terrain has bounded, continuous slopes and no artificial vertical rim',()=>{
  let max=0,change=0;
  for(let y=282;y<=458;y+=2)for(let x=468;x<=678;x+=2){
    const h=profile.height([x,y]);assert.ok(Number.isFinite(h)&&h>=0);
    max=Math.max(max,h);change=Math.max(change,Math.abs(h-profile.height([x+2,y])),Math.abs(h-profile.height([x,y+2])));
  }
  assert.ok(max>25&&max<50);assert.ok(change<6,'no abrupt cliff between adjacent samples');
});
test('detailed landmark foundations remain flat across their complete exported footprints',()=>{
  for(const [id,xs,ys,scale,offsetZ=0,offsetX=0,rotationY=0] of [['jiming',[-12,12],[-8,8],north.jiming.scale,north.jiming.offsetZ,north.jiming.offsetX],['zifeng',[-10,10],[-8,8],north.zifeng.scale],['yuejiang',[-12,12],[-9.5,9.5],north.yuejiang.scale,north.yuejiang.offsetZ,north.yuejiang.offsetX],['fuzimiao',[-14,14],[-14,12],.44],['presidential',[-13,13],[-14,14],.39],['baoen',[-5,5],[-5,5],.425],['mingxiaoling',[-13,13],[-10.4,9.6],.45],['zhongshan',[-11,11],[-17,17],.6],['meiling',[-10,10],[-9,8],.47],['museum',[-17,17],[-10.8,9],.4,0,-3.25],['zhonghua',[-14.5,14.5],[-17.5,16.5],gate.scale,gate.offsetZ,gate.offsetX,gate.rotationY]]){
    const p=data.landmarks.find(p=>p.id===id).source_px,h=profile.height(p);
    for(let x=xs[0];x<=xs[1];x+=.5)for(let y=ys[0];y<=ys[1];y+=.5){
      assert.ok(Math.abs(profile.height([p[0]+((Math.cos(rotationY)*x-Math.sin(rotationY)*y)*scale+offsetX)/.6,p[1]+(offsetZ-(Math.sin(rotationY)*x+Math.cos(rotationY)*y)*scale)/.6])-h)<.001,`${id}: sloping foundation`);
    }
  }
});
test('vegetation respects water, roads and future landmark footprints',()=>{
  const trees=profile.buildVegetation();assert.ok(trees.length>1000);assert.ok(trees.some(t=>t.pine));
  for(const t of trees){
    assert.equal(profile.isWater(t.p),false);
    assert.ok(profile.roadDistance(t.p,5)>=3.1);
    assert.ok(profile.landmarkDistance(t.p)>=17);
    assert.ok(Math.abs(t.y-profile.height(t.p))<.001);
  }
});
