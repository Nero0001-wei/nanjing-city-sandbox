import test from 'node:test';
import assert from 'node:assert/strict';
import {assetUrl} from '../src/asset-url.js';

test('public assets resolve under root and project deployments',()=>{
  for(const path of ['data/nanjing.json','/photos/landmarks/example.webp','models/trees.glb?v=version']){
    const relative=path.replace(/^\/+/, '');
    assert.equal(assetUrl(path,'/'),'/'+relative);
    assert.equal(assetUrl(path,'/nanjing-city-sandbox/'),'/nanjing-city-sandbox/'+relative);
    assert.equal(assetUrl(path,'./'),'./'+relative);
  }
});
