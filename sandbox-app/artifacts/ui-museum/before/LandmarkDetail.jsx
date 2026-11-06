import React,{useEffect,useRef,useState} from 'react';
import {GUIDE_REVIEWED_AT,landmarkGuides} from './landmark-guide.js';
import photoLibrary from './landmark-photos.json';

function Photo({photo,large=false}){
  const [failed,setFailed]=useState(false);
  return failed ? <span className="photo-unavailable">照片暂时无法显示，可通过下方来源查看原图。</span> :
    <img src={photo.src} alt={photo.alt} width={photo.width} height={photo.height} decoding="async" className={large?'photo-full':''} onError={()=>setFailed(true)}/>;
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
      <figcaption><div className="photo-caption"><span>{photo.caption}</span><span>{index+1} / {photos.length}</span></div><PhotoCredit photo={photo}/></figcaption>
    </figure>
    {photos.length>1&&<div className="photo-choices" aria-label="选择实景照片">{photos.map((p,i)=><button key={p.src} className={i===index?'active':''} onClick={()=>setIndex(i)} aria-pressed={i===index} aria-label={`查看照片 ${i+1}：${p.caption}`}><img src={p.thumbnail} alt="" width="80" height="54" loading="lazy"/>{i+1}</button>)}</div>}
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
  return <article className="detail-panel landmark-detail" aria-labelledby="landmark-detail-title">
    <header className="detail-heading"><div className="detail-top"><span>{poi.area||zoneName} <span aria-hidden="true">/</span> 景点手记</span><button className="icon-button" aria-label="关闭景点详情" onClick={onClose}><svg viewBox="0 0 24 24" width="19" height="19" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg></button></div><h2 id="landmark-detail-title">{poi.name}</h2>{guide&&<p className="detail-subtitle">{guide.subtitle}</p>}</header>
    <div className="detail-scroll" tabIndex="0" role="region" aria-label={`${poi.name}图文介绍`}>
      {photos.length>0&&<Gallery photos={photos} name={poi.name}/>}
      <div className="detail-copy">
        {guide ? <>
          <ul className="detail-tags" aria-label="景点速览">{guide.tags.map(tag=><li key={tag}>{tag}</li>)}</ul>
          <section className="guide-section"><h3>关于这里</h3>{guide.paragraphs.map(p=><p key={p}>{p}</p>)}</section>
          <section className="guide-section"><h3>值得细看</h3><ol className="guide-highlights">{guide.highlights.map(([title,body])=><li key={title}><strong>{title}</strong><p>{body}</p></li>)}</ol></section>
          <section className="guide-section photo-tip"><h3>取景小记</h3><p>{guide.photoTip}</p></section>
          <details className="guide-sources"><summary>资料来源与参观信息</summary><ul>{guide.sources.map(s=><li key={s.url}><a href={s.url} target="_blank" rel="noreferrer">{s.label} ↗</a></li>)}</ul><p>资料核对：{GUIDE_REVIEWED_AT}。取景小记为编辑建议；开放、预约和活动安排请以景区最新公告为准。</p></details>
        </> : <p>{poi.description||'可查看地理参考，了解这处地标的位置。'}</p>}
        <a className="geography-link" href={poi.source} target="_blank" rel="noreferrer">查看地理参考 ↗</a>
      </div>
    </div>
  </article>;
}
