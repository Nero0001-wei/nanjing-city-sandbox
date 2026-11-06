import React,{useEffect,useRef,useState} from 'react';
import {GUIDE_REVIEWED_AT,landmarkGuides} from './landmark-guide.js';
import photoLibrary from './landmark-photos.json';
import {Icon} from './Icon.jsx';
import {assetUrl} from './asset-url.js';

function Photo({photo,large=false}){
  const [failed,setFailed]=useState(false);
  return failed ? <span className="photo-unavailable">照片暂时无法显示，可通过下方来源查看原图。</span> :
    <img src={assetUrl(photo.src)} alt={photo.alt} width={photo.width} height={photo.height} decoding="async" className={large?'photo-full':''} onError={()=>setFailed(true)}/>;
}

function PhotoCredit({photo}){
  return <span className="photo-credit"><a href={photo.sourceUrl} target="_blank" rel="noreferrer">摄影：{photo.author} · Wikimedia Commons ↗</a><span><a href={photo.licenseUrl} target="_blank" rel="noreferrer">{photo.license}</a> · 已缩放并转为 WebP{photo.date&&` · 摄于 ${photo.date}`}</span>{photo.architectureCredit&&<span>{photo.architectureCredit}</span>}</span>;
}

function Gallery({photos,name}){
  const [index,setIndex]=useState(0),[expanded,setExpanded]=useState(false);
  const dialog=useRef(null),trigger=useRef(null);
  const photo=photos[index];
  useEffect(()=>{
    if(expanded&&!dialog.current.open)dialog.current.showModal();
    if(!expanded&&dialog.current.open)dialog.current.close();
  },[expanded]);
  function move(step){setIndex(i=>(i+step+photos.length)%photos.length);}
  function close(){setExpanded(false);trigger.current?.focus();}
  return <section className="photo-gallery" aria-label={`${name}实景照片`}>
    <figure>
      <button ref={trigger} className="photo-preview" onClick={()=>setExpanded(true)} aria-label={`放大查看：${photo.alt}`}>
        <Photo key={photo.src} photo={photo}/><span className="photo-badge">实景摄影</span><span className="photo-enlarge">放大 ↗</span>
      </button>
      <figcaption><div className="photo-caption"><span>{photo.caption}</span><span>{String(index+1).padStart(2,'0')} / {String(photos.length).padStart(2,'0')}</span></div><details className="photo-attribution"><summary>摄影来源与许可</summary><PhotoCredit photo={photo}/></details></figcaption>
    </figure>
    {photos.length>1&&<div className="photo-choices" aria-label="选择实景照片">{photos.map((p,i)=><button key={p.src} className={i===index?'active':''} onClick={()=>setIndex(i)} aria-pressed={i===index} aria-label={`查看照片 ${i+1}：${p.caption}`}><img src={assetUrl(p.thumbnail)} alt="" width="80" height="54" loading="lazy"/>{i+1}</button>)}</div>}
    <dialog className="photo-dialog" ref={dialog} aria-label={`${name}实景照片大图`} onClose={close} onClick={e=>{if(e.target===e.currentTarget)close();}} onKeyDown={e=>{if(e.key==='ArrowLeft'){e.preventDefault();move(-1);}if(e.key==='ArrowRight'){e.preventDefault();move(1);}if(e.key==='Escape')e.stopPropagation();}}>
      {expanded&&<div className="photo-dialog-inner"><header><strong>{name} · 实景摄影</strong><button autoFocus className="photo-dialog-close" onClick={close} aria-label="关闭照片大图">关闭 ×</button></header>
        <div className="photo-stage"><Photo key={photo.src} photo={photo} large/></div>
        <div className="photo-dialog-caption"><span>{photo.caption}</span><div className="photo-paging"><button onClick={()=>move(-1)} disabled={photos.length<2} aria-label="上一张照片">←</button><span aria-live="polite">{index+1} / {photos.length}</span><button onClick={()=>move(1)} disabled={photos.length<2} aria-label="下一张照片">→</button></div></div>
        <PhotoCredit photo={photo}/>
      </div>}
    </dialog>
  </section>;
}

export function LandmarkDetail({poi,zoneName,onClose}){
  const guide=landmarkGuides[poi.id],photos=photoLibrary[poi.id]||[];
  const [compact,setCompact]=useState(false);
  const scroll=useRef(null);
  function jumpTo(selector){
    const target=scroll.current.querySelector(selector);
    if(!target)return;
    const top=target.getBoundingClientRect().top-scroll.current.getBoundingClientRect().top+scroll.current.scrollTop;
    scroll.current.scrollTo({top:Math.max(0,top-20),behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});
  }
  return <article className={`detail-panel landmark-detail ${compact?'compact':''}`} aria-labelledby="landmark-detail-title">
    <header className="detail-heading"><div className="detail-top"><span>{poi.area||zoneName} <span aria-hidden="true"> / </span> 景点手记</span><div className="detail-actions"><button className="icon-button detail-collapse" aria-label={compact?'展开景点详情':'收起景点详情'} aria-expanded={!compact} onClick={()=>setCompact(v=>!v)}><Icon name={compact?'expand':'minus'} width="18" height="18"/></button><button className="icon-button" aria-label="关闭景点详情" onClick={onClose}><Icon name="close"/></button></div></div><div className="detail-title-row"><span className="exhibit-number" aria-hidden="true">{String(poi.number).padStart(2,'0')}</span><h2 id="landmark-detail-title">{poi.name}</h2></div>{guide&&<p className="detail-subtitle">{guide.subtitle}</p>}</header>
    {guide&&<nav className="detail-navigation" aria-label="景点内容导航"><button onClick={()=>jumpTo('.photo-gallery')}>实景照片</button><button onClick={()=>jumpTo('.guide-about')}>景点介绍</button><button onClick={()=>jumpTo('.guide-features')}>主要看点</button></nav>}
    <div ref={scroll} className="detail-scroll" tabIndex="0" role="region" aria-label={`${poi.name}图文介绍`}>
      {photos.length>0&&<Gallery photos={photos} name={poi.name}/>}
      <div className="detail-copy">
        {guide ? <>
          <ul className="detail-tags" aria-label="景点速览">{guide.tags.map(tag=><li key={tag}>{tag}</li>)}</ul>
          <section className="guide-section guide-about"><h3>关于这里</h3>{guide.paragraphs.map(p=><p key={p}>{p}</p>)}</section>
          <section className="guide-section guide-features"><h3>值得细看</h3><ol className="guide-highlights">{guide.highlights.map(([title,body])=><li key={title}><strong>{title}</strong><p>{body}</p></li>)}</ol></section>
          <section className="guide-section photo-tip"><h3>取景小记</h3><p>{guide.photoTip}</p></section>
          <details className="guide-sources"><summary>资料来源与参观信息</summary><ul>{guide.sources.map(s=><li key={s.url}><a href={s.url} target="_blank" rel="noreferrer">{s.label} ↗</a></li>)}</ul><p>资料核对：{GUIDE_REVIEWED_AT}。取景小记为编辑建议；开放、预约和活动安排请以景区最新公告为准。</p></details>
        </> : <p>{poi.description||'可查看地理参考，了解这处地标的位置。'}</p>}
        <a className="geography-link" href={poi.source} target="_blank" rel="noreferrer">查看地理参考 ↗</a>
      </div>
    </div>
  </article>;
}
