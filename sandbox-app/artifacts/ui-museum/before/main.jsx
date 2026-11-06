import React,{useEffect,useRef,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {createSandbox,groups} from './scene.js';
import {LandmarkDetail} from './LandmarkDetail.jsx';
import './style.css';

function Icon({name,...props}){
  const paths={plus:<path d="M12 5v14M5 12h14"/>,minus:<path d="M5 12h14"/>,reset:<><path d="M4 10a8 8 0 1 1 1 8M4 4v6h6"/></>,arrow:<path d="m9 5 7 7-7 7"/>,close:<path d="m6 6 12 12M18 6 6 18"/>,mountain:<path d="m3 19 7-13 5 8 3-5 4 10H3Zm4-7 3 2 2-2"/>,layers:<><path d="m3 8 9-5 9 5-9 5-9-5Zm0 5 9 5 9-5M3 18l9 4 9-4"/></>,compass:<><circle cx="12" cy="12" r="9"/><path d="m15 8-2 6-5 2 2-6 5-2Z"/></>,search:<><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></>,list:<path d="M5 6h14M5 12h14M5 18h14"/>,pin:<><path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 0 1 14 0Z"/><circle cx="12" cy="10" r="2"/></>};
  return <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>{paths[name]}</svg>;
}
function App(){
  const mount=useRef(null),engine=useRef(null),dataRef=useRef(null);
  const [data,setData]=useState(null),[selected,setSelected]=useState(null),[query,setQuery]=useState(''),[view,setView]=useState('iso');
  const [trees,setTrees]=useState(true),[roadNames,setRoadNames]=useState(true),[models,setModels]=useState(true),[progress,setProgress]=useState(0);
  const [buildings,setBuildings]=useState(true),[walls,setWalls]=useState(true);
  const [ready,setReady]=useState(false),[error,setError]=useState(''),[warning,setWarning]=useState(''),[mobileList,setMobileList]=useState(false),[help,setHelp]=useState(false);
  function select(id){setSelected(id);engine.current?.select(id);setMobileList(false);}
  useEffect(()=>{
    let dead=false;const abort=new AbortController();let api;
    async function init(){
      try{
        const [res,buildingData,urbanData,wallData]=await Promise.all([fetch('/data/nanjing.json',{signal:abort.signal}),fetch('/data/buildings.json',{signal:abort.signal}).then(r=>{if(!r.ok)throw new Error('buildings unavailable');return r.json();}).catch(e=>{if(e.name==='AbortError')throw e;return null;}),fetch('/data/urban.json',{signal:abort.signal}).then(r=>{if(!r.ok)throw new Error('urban unavailable');return r.json();}).catch(e=>{if(e.name==='AbortError')throw e;return null;}),fetch('/data/city-walls.json',{signal:abort.signal}).then(r=>{if(!r.ok)throw new Error('walls unavailable');return r.json();}).catch(e=>{if(e.name==='AbortError')throw e;return null;})]);
        if(!res.ok)throw new Error('地图数据读取失败');
        const d=await res.json();if(dead)return;d.buildings=buildingData;d.urban=urbanData;d.cityWalls=wallData;if(!wallData)setWarning('明城墙暂时未能载入，请刷新重试。');if(!urbanData)setWarning('街区背景暂时未能载入，请刷新重试。');if(!buildingData)setWarning('建筑白模暂时未能载入，请刷新重试。');dataRef.current=d;setData(d);
        api=await createSandbox(mount.current,d,{onSelect:id=>{if(!dead){setSelected(id);api?.select(id);setMobileList(false);}},onProgress:n=>{if(!dead)setProgress(n);},onReady:()=>{if(!dead)setReady(true);},onWarning:s=>{if(!dead)setWarning(s);}});
        if(dead)api.dispose();else {
          engine.current=api;
          const initialId=new URLSearchParams(window.location.search).get('landmark');
          if(d.landmarks.some(p=>p.id===initialId))api.loading.then(()=>{if(!dead){setSelected(initialId);api.select(initialId);}});
        }
      }catch(e){if(!dead&&e.name!=='AbortError')setError('沙盘暂时无法打开。请使用支持 WebGL 的浏览器，或重新加载页面。');}
    }
    init();return()=>{dead=true;abort.abort();api?.dispose();engine.current=null;};
  },[]);
  useEffect(()=>{function onKey(e){if(e.key==='Escape'&&!document.querySelector('dialog[open]')){setSelected(null);engine.current?.select(null);setMobileList(false);setHelp(false);}}window.addEventListener('keydown',onKey);return()=>window.removeEventListener('keydown',onKey);},[]);
  const poi=data?.landmarks.find(p=>p.id===selected);
  const filtered=data?.landmarks.filter(p=>p.name.includes(query.trim()))||[];
  const landmarkCount=data?.landmarks.length||0,modelCount=data?.landmarks.filter(p=>p.id!=='xuanwu').length||0;
  function reset(){setSelected(null);engine.current?.reset();}
  return <div className="app">
    <header className="header">
      <a className="wordmark" href="/" aria-label="南京城市沙盘首页"><span className="seal">宁</span><span>南京<span className="wordmark-dot"> · </span>山水之间</span></a>
      <p className="header-note">一座城，慢慢看。</p>
      <div className="header-actions"><button className="text-button help-button" onClick={()=>setHelp(v=>!v)} aria-expanded={help}><Icon name="compass"/>操作指引</button><span className="edition">城市沙盘 / 初版</span></div>
    </header>
    <aside className={`sidebar ${mobileList?'open':''}`} aria-label="景点导航">
      <div className="sidebar-head"><h1>沿着山水<br/>走进南京。</h1><p>从长江边，到钟山下。<br/>选一处地标，开始探索。</p><button className="mobile-close icon-button" aria-label="关闭景点列表" onClick={()=>setMobileList(false)}><Icon name="close"/></button></div>
      <label className="search"><Icon name="search"/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="寻找一处风景" aria-label="搜索景点"/>{query&&<button className="clear-search" aria-label="清空搜索" onClick={()=>setQuery('')}><Icon name="close" width="15" height="15"/></button>}</label>
      <nav className="landmark-list" aria-label="南京景点">
        {Object.entries(groups).map(([zone,name])=>{const list=filtered.filter(p=>p.zone===zone);return list.length>0&&<section className="landmark-group" key={zone}><h2><span className={'zone-dot zone-'+zone}/>{name}</h2>{list.map(p=><button key={p.id} className={'landmark-button '+(selected===p.id?'selected':'')} onClick={()=>select(p.id)} aria-pressed={selected===p.id}><span>{p.name}</span><Icon name="arrow" width="15" height="15"/></button>)}</section>;})}
        {data&&!filtered.length&&<p className="no-results">没有找到这个景点。试试“钟山”附近的“中山陵”，或清空搜索。</p>}
      </nav>
      <div className="sidebar-footer"><span className="status-dot"/>{ready?`${landmarkCount} 处风景，等你探索`:'正在铺开这座城市…'}<small>核心主城与滨江地标</small></div>
    </aside>
    <main className="scene-area">
      <div className="scene-host" ref={mount}/>
      {!ready&&!error&&<div className="loading" role="status"><span className="loading-ring"/><strong>南京，正在眼前展开</strong><span>载入地标 {progress} / {data?modelCount:'…'}</span></div>}
      {error&&<div className="error-state" role="alert"><strong>暂时无法展示三维场景</strong><p>{error}</p><button onClick={()=>window.location.reload()}>重新加载</button><a href="/data/nanjing.json">查看地图数据</a></div>}
      <div className="scene-toolbar">
        <div className="view-switch" aria-label="地图视角">{[['iso','等轴视角'],['top','俯视地图']].map(([id,label])=><button key={id} aria-pressed={view===id} className={view===id?'active':''} onClick={()=>{setView(id);setSelected(null);engine.current?.select(null);engine.current?.setView(id);}}>{label}</button>)}</div>
        <button className="reset-button" onClick={reset}><Icon name="reset" width="17" height="17"/>回到全景</button>
      </div>
      <div className="map-options" aria-label="显示设置"><Icon name="layers" width="17" height="17"/>
        <label><input type="checkbox" checked={trees} onChange={e=>{setTrees(e.target.checked);engine.current?.trees(e.target.checked);}}/>树木</label>
        <label><input type="checkbox" checked={roadNames} onChange={e=>{setRoadNames(e.target.checked);engine.current?.roadNames(e.target.checked);}}/>路名</label>
        <label title="真实建筑轮廓与概括白模组团，部分高度估算"><input type="checkbox" checked={buildings} disabled={!data?.buildings} onChange={e=>{setBuildings(e.target.checked);engine.current?.buildings(e.target.checked);}}/>建筑白模</label>
        <label title="已核实墙段与城门；部分连接细节待定位"><input type="checkbox" checked={walls} disabled={!data?.cityWalls} onChange={e=>{setWalls(e.target.checked);engine.current?.walls(e.target.checked);}}/>明城墙</label>
        <label><input type="checkbox" checked={!models} onChange={e=>{setModels(!e.target.checked);engine.current?.models(!e.target.checked);}}/>简模对照</label>
      </div>
      <div className="compass" title="俯视地图保持北向上"><span>北</span><svg viewBox="0 0 30 40" width="26" height="34"><path d="M15 3 5 31 15 24Z" fill="#325747"/><path d="M15 3 25 31 15 24Z" fill="#9bac98"/></svg></div>
      <div className="zoom-controls"><button aria-label="放大地图" onClick={()=>engine.current?.zoom(1.3)}><Icon name="plus"/></button><button aria-label="缩小地图" onClick={()=>engine.current?.zoom(1/1.3)}><Icon name="minus"/></button></div>
      {poi&&<LandmarkDetail key={poi.id} poi={poi} zoneName={groups[poi.zone]} onClose={()=>select(null)}/>}
      {help&&<div className="help-panel" role="dialog" aria-label="沙盘操作指引"><button className="icon-button" aria-label="关闭操作指引" onClick={()=>setHelp(false)}><Icon name="close"/></button><h2>换个角度，看南京</h2><p>左键拖动旋转 · 滚轮缩放<br/>按住中键拖动平移 · 点击地标查看<br/>手机单指旋转，双指缩放和平移。</p><p>“俯视地图”可核对位置；“简模对照”可查看地标占位。</p><p>道路采用简化白模，普通短跨河桥贴近地面，立交保留一层高架，淡白细线表示隧道走向。中华门、夫子庙周边道路为避让放大的建筑做了局部展示调整，券门内的通行线为沙盘示意，不代表现实机动车路线。</p><p>建筑白模保留 OpenStreetMap 的真实轮廓，当前显示 {data?.buildings?.count?.toLocaleString()||0} 个筛选后的建筑轮廓。有高度标注的按标注处理，其余由楼层或建筑类型估算；显示高度统一放大 1.6 倍，便于在沙盘上辨认。</p><p>新增 {data?.urban?.counts.buildings||0} 栋概括白模组成城市背景，铺地与庭院沿现有街道划分。新增组团和绿化是美术示意，不代表逐栋实测建筑。</p><p>城墙按资料核对现存段落与城门通道。集庆门采用四孔平顶通道，长干门等处通过门体连接两侧墙身，中华门沿用现有模型。前湖钢桥尚未单独建模，太平门通道西侧连接线仍待准确定位，局部空缺不能据此判断现实是否断开。城墙宽高经过艺术化处理。</p><small>建筑覆盖不完整。山体高度、地标大小与道路宽度经过艺术化概括。地理位置依据校正地图，非导航地图。</small></div>}
      {warning&&<div className="warning" role="status">{warning}</div>}
      <button className="mobile-explore" onClick={()=>setMobileList(true)}><Icon name="list"/>探索 {landmarkCount} 处风景</button>
      <footer className="map-footer"><span className="gesture-hint">左键旋转 · 中键平移 · 滚轮缩放</span>{buildings&&data?.buildings&&<span className="building-note">白模：真实轮廓＋概括组团</span>}<a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">© OpenStreetMap contributors · ODbL</a></footer>
    </main>
  </div>;
}
createRoot(document.getElementById('root')).render(<App/>);
