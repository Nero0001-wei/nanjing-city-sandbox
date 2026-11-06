import React,{useEffect,useRef} from 'react';
import {Icon} from './Icon.jsx';

export function GuideDialog({open,onClose,data}){
  const dialog=useRef(null);
  useEffect(()=>{if(open&&!dialog.current.open)dialog.current.showModal();else if(!open&&dialog.current.open)dialog.current.close();},[open]);
  return <dialog ref={dialog} className="help-dialog" aria-labelledby="help-title" onClose={onClose} onClick={e=>{if(e.target===e.currentTarget)onClose();}} onKeyDown={e=>{if(e.key==='Escape')e.stopPropagation();}}>
    <div className="help-heading"><span className="eyebrow">南京城市导览 · 使用指南</span><button className="icon-button" autoFocus aria-label="关闭操作指引" onClick={onClose}><Icon name="close"/></button></div>
    <div className="help-content"><h2 id="help-title">换个角度，看南京。</h2><p className="help-lead">从一处地标开始，慢慢读懂这座城。</p>
      <div className="gesture-grid">
        <section><Icon name="rotate"/><h3>旋转沙盘</h3><p>鼠标左键拖动<br/>手机单指拖动</p></section>
        <section><Icon name="search"/><h3>靠近细看</h3><p>滚动鼠标滚轮<br/>手机双指缩放</p></section>
        <section><Icon name="move"/><h3>移动视野</h3><p>按住鼠标中键拖动<br/>手机双指平移</p></section>
        <section><Icon name="pin"/><h3>认识景点</h3><p>点击地图上的地标<br/>或从景点目录选择</p></section>
      </div>
      <p className="help-shortcuts"><kbd>Esc</kbd> 关闭当前面板 <span>·</span> 照片大图中用 <kbd>←</kbd> <kbd>→</kbd> 翻页</p>
      <details className="map-notes"><summary>关于这座沙盘与地图资料</summary><div>
        <p>“俯视地图”可核对位置；“图层”可分别调整景点模型、景点名称、树木、路名、建筑白模、明城墙，并开启“简模对照”查看地标占位。关闭“景点”只隐藏地标模型，保留湖泊等基础地形；关闭“景点名称”只隐藏地图标注。点击标注或从目录选择景点会恢复模型显示，名称开关保持你的选择。</p>
        <p>“日景 / 夜景”可切换昼夜。夜景中的暖色窗灯、建筑照明和桥梁灯光为艺术化示意，不代表景点实际亮灯时段。页面会记住上次选择；切换不改变当前视角。</p>
        <p>道路采用简化白模，普通短跨河桥贴近地面，立交保留一层高架，淡白细线表示隧道走向。中华门、夫子庙周边道路为避让放大的建筑做了局部展示调整，券门内的通行线为沙盘示意，不代表现实机动车路线。</p>
        <p>建筑白模保留 OpenStreetMap 的真实轮廓，当前显示 {data?.buildings?.count?.toLocaleString()||0} 个筛选后的建筑轮廓。有高度标注的按标注处理，其余由楼层或建筑类型估算；显示高度统一放大 1.6 倍，便于在沙盘上辨认。</p>
        <p>新增 {data?.urban?.counts.buildings||0} 栋概括白模组成城市背景，铺地与庭院沿现有街道划分。新增组团和绿化是美术示意，不代表逐栋实测建筑。</p>
        <p>城墙按资料核对现存段落与城门通道。集庆门采用四孔平顶通道，长干门等处通过门体连接两侧墙身，中华门沿用现有模型。前湖钢桥尚未单独建模，太平门通道西侧连接线仍待准确定位，局部空缺不能据此判断现实是否断开。城墙宽高经过艺术化处理。</p>
        <p>建筑覆盖不完整。山体高度、地标大小与道路宽度经过艺术化概括。地理位置依据校正地图，非导航地图。</p>
      </div></details>
    </div><footer><button className="primary-button" onClick={onClose}>回到沙盘<Icon name="arrow" width="18" height="18"/></button></footer>
  </dialog>;
}
