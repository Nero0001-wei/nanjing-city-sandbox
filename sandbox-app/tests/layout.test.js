import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {world,clipSegment,clipPolygon,pointInPolygon} from '../src/geo.js';
const data=JSON.parse(readFileSync(new URL('../public/data/nanjing.json',import.meta.url)));
const source=JSON.parse(readFileSync(new URL('../../output/layout-v2/nanjing-layout-data.json',import.meta.url)));

test('all geographic anchors match the approved layout without artistic shifts',()=>{
  assert.equal(data.landmarks.length,source.landmarks.length);
  assert.ok(data.landmarks.length>=14);
  assert.equal(new Set(data.landmarks.map(p=>p.id)).size,data.landmarks.length);
  for(const p of data.landmarks){const original=source.landmarks.find(x=>x.id===p.id);assert.deepEqual(p.source_px,original.source_px);assert.equal(p.longitude,original.longitude);assert.equal(p.latitude,original.latitude);}
  const at=id=>world(data.landmarks.find(p=>p.id===id).source_px);
  assert.ok(at('zhonghua')[1]<at('baoen')[1],'Z increases south; Zhonghua Gate stays north of Baoen');
  assert.ok(at('nanjing-eye')[0]<at('zhonghua')[0]);
});
test('required roads and tunnel semantics survive data preparation',()=>{
  const names=new Set(data.roads.map(r=>r.name));
  for(const name of ['应天大街','虎踞路','凤台南路','北京西路','中山南路','中华路','玄武湖隧道'])assert.ok(names.has(name),name);
  assert.ok(data.roads.filter(r=>r.name==='玄武湖隧道').every(r=>r.kind==='tunnel'));
});
test('map clipping retains crossings and rejects external geometry',()=>{
  assert.deepEqual(clipSegment([-5,5],[15,5],[0,0,10,10]),[[0,5],[10,5]]);
  assert.equal(clipSegment([-5,-5],[15,-5],[0,0,10,10]),null);
  const poly=clipPolygon([[-5,-5],[15,-5],[15,15],[-5,15]],[0,0,10,10]);
  assert.ok(pointInPolygon([5,5],poly));assert.ok(!pointInPolygon([12,5],poly));
});
test('all landmark assets are valid binary glTF with meshes and no external dependencies',()=>{
  const manifest=JSON.parse(readFileSync(new URL('../public/models/manifest.json',import.meta.url)));
  assert.deepEqual(manifest.models.map(p=>p.id).sort(),data.landmarks.filter(p=>p.id!=='xuanwu').map(p=>p.id).sort());
  for(const p of data.landmarks.filter(p=>p.id!=='xuanwu')){
    const path=new URL(`../public/models/${p.id}.glb`,import.meta.url);assert.ok(existsSync(path));
    const b=readFileSync(path);assert.equal(b.toString('utf8',0,4),'glTF');assert.equal(b.readUInt32LE(4),2);assert.equal(b.readUInt32LE(8),b.length);
    const json=JSON.parse(b.toString('utf8',20,20+b.readUInt32LE(12)).trim());
    assert.ok(json.meshes.length>0);assert.ok(json.buffers.every(b=>!b.uri));
  }
});
