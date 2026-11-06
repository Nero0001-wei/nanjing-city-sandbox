import React,{useEffect,useRef,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {createSandbox,groups} from './scene.js';
import {LandmarkDetail} from './LandmarkDetail.jsx';
import {Icon} from './Icon.jsx';
import {GuideDialog} from './GuideDialog.jsx';
import {assetUrl} from './asset-url.js';
import './style.css';

function App(){
  const mount=useRef(null),engine=useRef(null),dataRef=useRef(null),sidebar=useRef(null),exploreButton=useRef(null),layerButton=useRef(null),selectionTrigger=useRef(null);
  const [data,setData]=useState(null),[selected,setSelected]=useState(null),[query,setQuery]=useState(''),[view,setView]=useState('iso');
  const [trees,setTrees]=useState(true),[roadNames,setRoadNames]=useState(true),[models,setModels]=useState(true),[progress,setProgress]=useState(0);
  const [buildings,setBuildings]=useState(true),[walls,setWalls]=useState(true),[landmarks,setLandmarks]=useState(true);
  const [landmarkNames,setLandmarkNames]=useState(true);
  const [night,setNight]=useState(()=>{
    const time=new URLSearchParams(window.location.search).get('time');
    if(time==='night'||time==='day')return time==='night';
    try{return localStorage.getItem('nanjing-time-of-day')==='night';}catch{return false;}
  });
  const [ready,setReady]=useState(false),[error,setError]=useState(''),[warning,setWarning]=useState(''),[mobileList,setMobileList]=useState(false),[help,setHelp]=useState(false),[layersOpen,setLayersOpen]=useState(false);
  function select(id){
    if(id){selectionTrigger.current=document.activeElement;setLandmarks(true);engine.current?.landmarks(true);}
    setSelected(id);engine.current?.select(id);setMobileList(false);setLayersOpen(false);
    if(!id)requestAnimationFrame(()=>{
      const trigger=selectionTrigger.current;
      if(trigger?.isConnected&&trigger.getClientRects().length)trigger.focus();
      else if(exploreButton.current?.getClientRects().length)exploreButton.current.focus();
      else mount.current?.parentElement.focus();
    });
  }
  useEffect(()=>{
    let dead=false;const abort=new AbortController();let api;
    async function init(){
      try{
        const [res,buildingData,urbanData,wallData]=await Promise.all([fetch(assetUrl('data/nanjing.json'),{signal:abort.signal}),fetch(assetUrl('data/buildings.json'),{signal:abort.signal}).then(r=>{if(!r.ok)throw new Error('buildings unavailable');return r.json();}).catch(e=>{if(e.name==='AbortError')throw e;return null;}),fetch(assetUrl('data/urban.json'),{signal:abort.signal}).then(r=>{if(!r.ok)throw new Error('urban unavailable');return r.json();}).catch(e=>{if(e.name==='AbortError')throw e;return null;}),fetch(assetUrl('data/city-walls.json'),{signal:abort.signal}).then(r=>{if(!r.ok)throw new Error('walls unavailable');return r.json();}).catch(e=>{if(e.name==='AbortError')throw e;return null;})]);
        if(!res.ok)throw new Error('地图数据读取失败');
        const d=await res.json();if(dead)return;d.buildings=buildingData;d.urban=urbanData;d.cityWalls=wallData;if(!wallData)setWarning('明城墙暂时未能载入，请刷新重试。');if(!urbanData)setWarning('街区背景暂时未能载入，请刷新重试。');if(!buildingData)setWarning('建筑白模暂时未能载入，请刷新重试。');dataRef.current=d;setData(d);
        api=await createSandbox(mount.current,d,{onSelect:id=>{if(!dead){selectionTrigger.current=document.activeElement;setLandmarks(true);api?.landmarks(true);setSelected(id);api?.select(id);setMobileList(false);setLayersOpen(false);}},onProgress:n=>{if(!dead)setProgress(n);},onReady:()=>{if(!dead)setReady(true);},onWarning:s=>{if(!dead)setWarning(s);}});
        if(dead)api.dispose();else {
          engine.current=api;
          api.setNight(night,true);
          const initialId=new URLSearchParams(window.location.search).get('landmark');
          if(d.landmarks.some(p=>p.id===initialId))api.loading.then(()=>{if(!dead){setSelected(initialId);api.select(initialId);}});
        }
      }catch(e){if(!dead&&e.name!=='AbortError')setError('沙盘暂时无法打开。请使用支持 WebGL 的浏览器，或重新加载页面。');}
    }
    init();return()=>{dead=true;abort.abort();api?.dispose();engine.current=null;};
  },[]);
  useEffect(()=>{
    function onKey(e){
      if(e.key!=='Escape'||document.querySelector('dialog[open]'))return;
      if(mobileList){setMobileList(false);return;}
      if(layersOpen){setLayersOpen(false);layerButton.current?.focus();return;}
      if(selected)select(null);
    }
    window.addEventListener('keydown',onKey);return()=>window.removeEventListener('keydown',onKey);
  },[mobileList,layersOpen,selected]);
  useEffect(()=>{
    if(!layersOpen)return;
    const closeOutside=e=>{if(!e.target.closest('.layer-control'))setLayersOpen(false);};
    document.addEventListener('pointerdown',closeOutside);return()=>document.removeEventListener('pointerdown',closeOutside);
  },[layersOpen]);
  useEffect(()=>{
    const media=window.matchMedia('(max-width: 900px)');
    const onResize=()=>{if(!media.matches)setMobileList(false);};
    media.addEventListener('change',onResize);return()=>media.removeEventListener('change',onResize);
  },[]);
  useEffect(()=>{
    if(!mobileList)return;
    sidebar.current?.querySelector('.mobile-close')?.focus();
    function trap(e){
      if(e.key!=='Tab')return;
      const items=[...sidebar.current.querySelectorAll('button:not([disabled]),input,a[href]')].filter(el=>el.getClientRects().length);
      const first=items[0],last=items[items.length-1];
      if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus();}
      if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus();}
    }
    const current=sidebar.current;current.addEventListener('keydown',trap);
    return()=>{current.removeEventListener('keydown',trap);exploreButton.current?.focus();};
  },[mobileList]);
  const poi=data?.landmarks.find(p=>p.id===selected);
  const filtered=data?.landmarks.filter(p=>p.name.includes(query.trim()))||[];
  const landmarkCount=data?.landmarks.length||0,modelCount=data?.landmarks.filter(p=>p.id!=='xuanwu').length||0;
  function reset(){setSelected(null);engine.current?.reset();}
  function changeLandmarks(show){
    setLandmarks(show);engine.current?.landmarks(show);
    if(!show){setSelected(null);engine.current?.select(null);}
  }
  function changeTime(next){
    setNight(next);engine.current?.setNight(next);
    try{localStorage.setItem('nanjing-time-of-day',next?'night':'day');}catch{/* Private browsing may disable persistence. */}
    const url=new URL(window.location.href);url.searchParams.set('time',next?'night':'day');window.history.replaceState(null,'',url);
  }
  return <div className="app" data-time={night?'night':'day'}>
    <a className="skip-link" href="#city-map">跳转到城市沙盘</a>
    <header className="header" inert={mobileList}>
      <a className="wordmark" href={assetUrl('')} aria-label="南京城市沙盘首页"><span className="seal">宁</span><span className="wordmark-name">南京<span className="wordmark-dot"> · </span>山水之间<small>Nanjing · A city to explore</small></span></a>
      <p className="header-note">城市导览<span aria-hidden="true"> / </span>三维沙盘</p>
      <div className="header-actions"><span className="edition">沿着山水，慢慢看。</span><button className="text-button help-button" onClick={()=>setHelp(true)} aria-haspopup="dialog" aria-label="操作指引"><Icon name="book"/><span>操作指引</span></button></div>
    </header>
    {mobileList&&<button className="sidebar-scrim" tabIndex="-1" aria-label="关闭景点目录遮罩" onClick={()=>setMobileList(false)}/>}
    <aside ref={sidebar} className={`sidebar ${mobileList?'open':''}`} aria-label="景点导航" role={mobileList?'dialog':undefined} aria-modal={mobileList||undefined}>
      <div className="sidebar-head"><span className="eyebrow">城市索引</span><h1>山水之间，读南京。</h1><p>从长江边，到钟山下。</p><button className="mobile-close icon-button" aria-label="关闭景点列表" onClick={()=>setMobileList(false)}><Icon name="close"/></button></div>
      <div className="search-block"><label htmlFor="landmark-search" className="search-label">寻找景点</label><div className="search"><Icon name="search" width="18" height="18"/><input id="landmark-search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="输入景点名称" aria-label="搜索景点"/>{query&&<button className="clear-search icon-button" aria-label="清空搜索" onClick={()=>setQuery('')}><Icon name="close" width="16" height="16"/></button>}</div></div>
      <div className="index-count"><span>{query?'搜索结果':'景点目录'}</span><span aria-live="polite">{query?filtered.length:landmarkCount} 处</span></div>
      <nav className="landmark-list" aria-label="南京景点">
        {Object.entries(groups).map(([zone,name])=>{const list=filtered.filter(p=>p.zone===zone);return list.length>0&&<section className="landmark-group" key={zone}><h2><span>{name}</span><span className="group-rule" aria-hidden="true"/><span>{list.length}</span></h2>{list.map(p=><button key={p.id} className={'landmark-button '+(selected===p.id?'selected':'')} onClick={()=>select(p.id)} aria-pressed={selected===p.id} aria-label={p.name}><span className="landmark-number" aria-hidden="true">{String(p.number).padStart(2,'0')}</span><span className="landmark-name">{p.name}</span><Icon name="arrow" width="16" height="16"/></button>)}</section>;})}
        {data&&!filtered.length&&<div className="no-results" role="status"><Icon name="search" width="28" height="28"/><strong>还没有找到这处风景</strong><p>试试“中山陵”或“玄武湖”。</p><button className="text-link" onClick={()=>setQuery('')}>查看全部景点<Icon name="arrow" width="16" height="16"/></button></div>}
      </nav>
      <div className="sidebar-footer"><span className="status-dot"/><span>{ready?'点击地标，开启一段城市漫游':'正在铺开这座城市…'}</span><small>核心主城与滨江地标</small></div>
    </aside>
    <main id="city-map" tabIndex="-1" className={`scene-area ${poi?'has-detail':''}`} inert={mobileList} aria-label="南京城市沙盘">
      <div className="scene-host" ref={mount}/>
      {!ready&&!error&&<div className="loading" role="status"><Icon name="city" width="40" height="40"/><span className="eyebrow">南京 · 山水之间</span><strong>正在铺开这座城市</strong><progress aria-label="地标加载进度" value={progress} max={modelCount||1}/><span>载入地标 {progress} / {data?modelCount:'…'}</span></div>}
      {error&&<div className="error-state" role="alert"><strong>暂时无法展示三维场景</strong><p>{error}</p><button onClick={()=>window.location.reload()}>重新加载</button><a href={assetUrl('data/nanjing.json')}>查看地图数据</a></div>}
      <div className="scene-toolbar">
        <div className="view-switch" aria-label="地图视角">{[['iso','等轴视角'],['top','俯视地图']].map(([id,label])=><button key={id} aria-pressed={view===id} className={view===id?'active':''} onClick={()=>{setView(id);setSelected(null);engine.current?.select(null);engine.current?.setView(id);}}>{label}</button>)}</div>
        <button className="reset-button" onClick={reset} aria-label="回到全景" title="回到全景"><Icon name="reset" width="18" height="18"/><span className="control-label">回到全景</span></button>
        <div className="time-switch" role="group" aria-label="沙盘昼夜">
          <button disabled={!ready} aria-label="白天模式" aria-pressed={!night} onClick={()=>changeTime(false)}><Icon name="sun" width="16" height="16"/><span>日景</span></button>
          <button disabled={!ready} aria-label="夜晚模式" aria-pressed={night} onClick={()=>changeTime(true)}><Icon name="moon" width="16" height="16"/><span>夜景</span></button>
        </div>
        <div className="layer-control">
          <button ref={layerButton} className={`layers-button ${layersOpen?'active':''}`} aria-expanded={layersOpen} aria-controls="map-layers" onClick={()=>setLayersOpen(v=>!v)}><Icon name="layers" width="18" height="18"/><span>图层</span></button>
          {layersOpen&&<section id="map-layers" className="map-options" aria-label="显示设置"><header><h2>地图图层</h2><button className="icon-button" aria-label="关闭图层设置" onClick={()=>{setLayersOpen(false);layerButton.current?.focus();}}><Icon name="close" width="18" height="18"/></button></header><p>按你的习惯，看这座城。</p>
            <label><span>景点<small>地标建筑与桥梁模型</small></span><input type="checkbox" aria-label="景点" checked={landmarks} disabled={!ready} onChange={e=>changeLandmarks(e.target.checked)}/><span className="switch-track" aria-hidden="true"/></label>
            <label><span>景点名称<small>地图上的景点标注</small></span><input type="checkbox" aria-label="景点名称" checked={landmarkNames} disabled={!ready} onChange={e=>{setLandmarkNames(e.target.checked);engine.current?.landmarkNames(e.target.checked);}}/><span className="switch-track" aria-hidden="true"/></label>
            <label><span>树木<small>山林与街道绿意</small></span><input type="checkbox" aria-label="树木" checked={trees} onChange={e=>{setTrees(e.target.checked);engine.current?.trees(e.target.checked);}}/><span className="switch-track" aria-hidden="true"/></label>
            <label><span>路名<small>辨认城市道路</small></span><input type="checkbox" aria-label="路名" checked={roadNames} onChange={e=>{setRoadNames(e.target.checked);engine.current?.roadNames(e.target.checked);}}/><span className="switch-track" aria-hidden="true"/></label>
            <label><span>建筑白模<small>真实轮廓与概括组团</small></span><input type="checkbox" aria-label="建筑白模" checked={buildings} disabled={!data?.buildings} onChange={e=>{setBuildings(e.target.checked);engine.current?.buildings(e.target.checked);}}/><span className="switch-track" aria-hidden="true"/></label>
            <label><span>明城墙<small>已核实的墙段与城门</small></span><input type="checkbox" aria-label="明城墙" checked={walls} disabled={!data?.cityWalls} onChange={e=>{setWalls(e.target.checked);engine.current?.walls(e.target.checked);}}/><span className="switch-track" aria-hidden="true"/></label>
            <label className="compare-layer"><span>简模对照<small>查看地标占位轮廓</small></span><input type="checkbox" aria-label="简模对照" checked={!models} disabled={!landmarks} onChange={e=>{setModels(!e.target.checked);engine.current?.models(!e.target.checked);}}/><span className="switch-track" aria-hidden="true"/></label>
          </section>}
        </div>
      </div>
      <div className="compass" title="俯视地图保持北向上"><span>北</span><svg viewBox="0 0 30 40" width="26" height="34"><path d="M15 3 5 31 15 24Z" fill="#325747"/><path d="M15 3 25 31 15 24Z" fill="#9bac98"/></svg></div>
      <div className="zoom-controls"><button aria-label="放大地图" onClick={()=>engine.current?.zoom(1.3)}><Icon name="plus"/></button><button aria-label="缩小地图" onClick={()=>engine.current?.zoom(1/1.3)}><Icon name="minus"/></button></div>
      {poi&&<LandmarkDetail key={poi.id} poi={poi} zoneName={groups[poi.zone]} onClose={()=>select(null)}/>}
      {warning&&<div className="warning" role="status">{warning}</div>}
      <button ref={exploreButton} className="mobile-explore" onClick={()=>{setMobileList(true);setLayersOpen(false);}} aria-label={`探索 ${landmarkCount} 处风景`} aria-expanded={mobileList}><Icon name="list"/><span>景点目录</span><span className="explore-count">{landmarkCount} 处</span></button>
      <footer className="map-footer"><span className="gesture-hint">左键旋转 · 中键平移 · 滚轮缩放</span><span className="building-note" aria-live="polite">{night?'夜景灯光 · 艺术化示意':buildings&&data?.buildings?'白模：真实轮廓＋概括组团':''}</span><a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">© OpenStreetMap contributors · ODbL</a></footer>
    </main>
    <GuideDialog open={help} onClose={()=>setHelp(false)} data={data}/>
  </div>;
}
createRoot(document.getElementById('root')).render(<App/>);
