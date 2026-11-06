from pathlib import Path
import json, math, html, xml.etree.ElementTree as ET

OUT = Path(__file__).parent
OLD = json.loads((OUT.parent/'layout-v1/nanjing-layout-data.json').read_text())
ADDITIONAL = json.loads((OUT/'additional-landmarks.json').read_text())
OSM = json.loads((OUT/'sources/osm-features.json').read_text())
W,H = 2380,1700
S = 2.62
MX,MY,MW,MH = 48,180,1740,1390
def geo(lon,lat):
    return (((lon+180)/360*4096-3398)*256, ((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*4096-1661)*256)
def screen(p): return (MX+p[0]*S, MY+(p[1]-165)*S)
def scene(p): return [round((p[0]-350)*3.24,3),0,round((p[1]-430)*3.24,3)]
def project(coords): return [geo(*q) for q in coords]
def simplify(pts,tol=.45):
    if len(pts)<3:return pts
    a,b=pts[0],pts[-1]; dx,dy=b[0]-a[0],b[1]-a[1]; den=dx*dx+dy*dy
    ds=[]
    for p in pts[1:-1]:
        t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den)) if den else 0
        ds.append(math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy))
    d=max(ds)
    if d<=tol:return [a,b]
    k=ds.index(d)+1
    return simplify(pts[:k+1],tol)[:-1]+simplify(pts[k:],tol)

groups = [
 ('西侧骨架','虎踞北路 虎踞路 虎踞南路 凤台路 凤台桥 内环西线'),
 ('南侧骨架','应天大街 应天东街 内环南线'),
 ('西南延伸','凤台南路 凤台南路隧道'),
 ('东侧骨架','龙蟠中路 龙蟠南路 内环东线 西安门隧道 九华山隧道'),
 ('北侧骨架','模范西路 模范中路 新模范马路 模范马路 内环北线 玄武湖隧道'),
 ('中轴','中央路 中山路 中山南路 鼓楼地下立交'),
 ('东西中轴','汉中门大街 汉中路 中山东路 中山门大街 卫岗隧道'),
 ('北京路轴','草场门大街 草场门大桥 北京西路 北京东路'),
 ('西北斜轴','中山北路 大桥南路 南京长江大桥'),
 ('湖东联系','龙蟠路 龙蟠路隧道'),
 ('河西纵轴','江东北路 江东中路 江东快速路 江东门隧道 奥体新城隧道'),
 ('滨江纵轴','扬子江大道 宝船厂隧道 北河口隧道 万景园隧道 绿博园隧道 青奥轴线隧道'),
 ('河西横轴','河西大街 南京眼步行桥'),
 ('老城南轴','中华路 雨花路 雨花北路'),
 ('景点联系','长江路 太平北路 太平南路 建康路 长乐路 瞻园路 陵园路 博爱路 博爱东路 博爱西路 梅花谷路 太平门路'),
]
name_group={n:title for title,names in groups for n in names.split()}
roads=[]
for f in OSM['features']:
    t=f['tags']; n=t.get('name',''); h=t.get('highway','')
    if n not in name_group:continue
    if h not in ['motorway','trunk','primary','secondary','tertiary','unclassified','residential','living_street','motorway_link','trunk_link','primary_link','secondary_link','tertiary_link'] and n!='南京眼步行桥':continue
    ps=simplify(project(f['geometry']))
    kind='tunnel' if t.get('tunnel')=='yes' else 'elevated' if t.get('bridge')=='yes' else 'ground'
    roads.append(dict(osm_way_id=f['id'],name=n,group=name_group[n],kind=kind,osm_tags=t,longitude_latitude=f['geometry'],source_px=ps,scene_positions=[scene(p) for p in ps]))

# Lake relation geometry is read from the exact same OSM snapshot as the roads.
nodes={}; ways={}; relations={}
for p in (OUT/'sources').glob('area-*.osm'):
    if p.stat().st_size<1000:continue
    for e in ET.parse(p).getroot():
        if e.tag=='node':nodes[e.get('id')]=[float(e.get('lon')),float(e.get('lat'))]
        elif e.tag=='way':ways[e.get('id')]=[x.get('ref') for x in e.findall('nd')]
        elif e.tag=='relation' and e.get('id') in ['2138994','18231223']:relations[e.get('id')]=e
lakes=[]
for rid,e in relations.items():
    tags={x.get('k'):x.get('v') for x in e.findall('tag')}
    rings=[]
    for m in e.findall('member'):
        refs=ways[m.get('ref')]
        assert refs[0]==refs[-1], 'Open lake ring requires joining'
        rings.append(dict(role=m.get('role'),longitude_latitude=[nodes[n] for n in refs],source_px=simplify(project([nodes[n] for n in refs]),.25)))
    lakes.append(dict(osm_relation_id=rid,name=tags['name'],rings=rings))
river_names={'秦淮河','外秦淮河','内秦淮河','内秦淮河中段(运渎)','内秦淮河中段（运渎）'}
rivers=[dict(osm_way_id=f['id'],name=f['tags']['name'],source_px=simplify(project(f['geometry']),.3)) for f in OSM['features'] if f['tags'].get('waterway')=='river' and f['tags'].get('name') in river_names]

palette={'A':'#a36c3d','B':'#39786b','C':'#6c7e40','D':'#ad5d4c','E':'#497b92'}
label_positions={1:(308,200),2:(285,264),3:(327,367),4:(420,405),5:(457,350),6:(503,377),7:(587,369),8:(569,432),9:(491,482),10:(412,432),11:(420,519),12:(329,548),13:(400,589),14:(153,639)}
pois=[]
for d in OLD['landmarks']+ADDITIONAL:
    p=geo(d['longitude'],d['latitude'])
    pois.append(dict(id=d['id'],number=d['number'],name=d['name'],zone=d['zone'],longitude=d['longitude'],latitude=d['latitude'],coordinate_system='WGS84',source=d['source'],source_px=p,layout_px=screen(p),scene_position=scene(p),label_source_px=label_positions.get(d['number'],d.get('label_source_px',p)),model=d['model'],offset_m_approx=0))

base_terrain=[f for f in OLD['features'] if f['id'] in ['yangtze','jiangxin','qianzhou','purple-mountain']]
data=dict(title='南京主城景点与主要道路布局 v2',date='2026-10-29',scope='主城景点视口；不是南京全市行政地图',canvas=[W,H],projection='WGS84 → Web Mercator local pixels (z12, origin tile 3398/1661)',scene_mapping='X=(source_px.x-350)*3.24; Y=0; Z=(source_px.y-430)*3.24. 1 unit ≈10m at Nanjing latitude. North = -Z. Heights independent.',geometry_notes='Roads and lake rings from OSM API; roads simplified with 0.45 source-pixel tolerance (~15m). Dual carriageways retained. Rivers use OSM centerlines with illustrative width. Yangtze/islands/mountain are inherited hand-simplified v1 shapes, not survey boundaries. POIs have zero artistic shift; public source coordinates may represent a site centre rather than an entrance.',attribution='© OpenStreetMap contributors, ODbL 1.0; https://www.openstreetmap.org/copyright',landmarks=pois,roads=roads,lakes=lakes,rivers=rivers,schematic_terrain=base_terrain,road_groups=[dict(name=a,roads=b.split()) for a,b in groups])
(OUT/'nanjing-layout-data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))

def build():
    out=[]
    def add(s):out.append(s)
    def txt(x,y,t,size=22,color='#2b433b',weight=400,extra=''):
        add(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{color}" font-weight="{weight}" {extra}>{html.escape(t)}</text>')
    def pd(ps,close=False):return 'M '+' L '.join(f'{x:.1f},{y:.1f}' for x,y in map(screen,ps))+(' Z' if close else '')
    def path(ps,stroke='none',width=1,fill='none',close=False,extra=''):
        add(f'<path d="{pd(ps,close)}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round" {extra}/>')
    add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><title>南京主城景点与道路校正版</title><defs><clipPath id="map"><rect x="{MX}" y="{MY}" width="{MW}" height="{MH}" rx="10"/></clipPath></defs>')
    add('<style>text{font-family:"PingFang SC","Microsoft YaHei",sans-serif}.halo{paint-order:stroke;stroke:#f3f4e9;stroke-width:6px;stroke-linejoin:round}</style>')
    add(f'<rect width="{W}" height="{H}" fill="#f7f7ef"/>')
    txt(52,52,'NANJING / GEOGRAPHIC SCENE PLAN',17,'#748679',500,'letter-spacing="3"')
    txt(50,112,'南京 · 景点与主干道',48,'#244339',600)
    txt(53,151,'位置校正版   /   北向上 · 景点锚点归位 · 道路按公开地图线形',22,'#6c8071')
    txt(2320,65,'02 / 二维布局底稿',23,'#4b6656',500,'text-anchor="end"')
    txt(2320,101,'2026.10.29',18,'#8a9789',400,'text-anchor="end"')
    add(f'<g clip-path="url(#map)"><rect x="{MX}" y="{MY}" width="{MW}" height="{MH}" fill="#edf1e5"/>')
    for f in base_terrain:
        k=f['kind'];ps=f['source_px']
        if k=='water':path(ps,'#8cbac0',1.5,'#afd7d7',True)
        elif k=='island':path(ps,'#b5c8a4',1,'#d5e1bb',True)
        elif k=='mountain':
            path(ps,'#b6c89d',1.5,'#d6e0bf',True)
            for scale in [.78,.56,.34]:path([[571+(x-571)*scale,359+(y-359)*scale] for x,y in ps],'#c0cda9',1.6,close=True)
    for lake in lakes:
        d=' '.join(pd(r['source_px'],True) for r in lake['rings'])
        add(f'<path d="{d}" fill-rule="evenodd" fill="#afd7d7" stroke="#8cbac0" stroke-width="1.5"/>')
    for r in rivers:path(r['source_px'],'#9bc9ce',7 if r['name'] in ['秦淮河','外秦淮河'] else 4)
    for f in OSM['features']:
        if f['tags'].get('barrier')=='city_wall':
            ps=project(f['geometry'])
            if all(310<x<475 and 320<y<590 for x,y in ps):path(simplify(ps),'#91a08b',3)
    # Surface roads, then elevated roads, then dashed tunnels; no invented intersections.
    for kind in ['ground','elevated','tunnel']:
        for r in roads:
            if r['kind']!=kind:continue
            ps=r['source_px'];scenic=r['group']=='景点联系'
            width=4 if scenic else 6
            if kind=='ground':
                path(ps,'#c6c5b4',width+2.5);path(ps,'#faf9f0',width)
            elif kind=='elevated':
                path(ps,'#ad9374',width+4);path(ps,'#f5d8a5',width)
            else:path(ps,'#9a94b4',3.1,extra='stroke-dasharray="8 7"')
    for label,p,size,c in [('江 北',(135,245),32,'#819782'),('河 西',(225,597),31,'#98a38a'),('紫 金 山',(565,311),33,'#75865f'),('钟山景区',(565,327),18,'#8a9676'),('江心洲',(93,546),20,'#81926e'),('夹江',(140,554),17,'#67939a'),('莫愁湖',(281,465),16,'#60949a')]:
        x,y=screen(p);txt(x,y,label,size,c,500,'text-anchor="middle"')
    x,y=screen((125,410));txt(x,y,'长 江',40,'#6a9ea4',500,f'transform="rotate(-59 {x} {y})" text-anchor="middle"')

    # Fixed POI anchors; only the text labels may move.
    reserved=[]
    for d in pois:
        x,y=d['layout_px'];lx,ly=screen(d['label_source_px']);n=d['name'];left=lx<x
        tx=lx-8 if left else lx+8;tw=len(n)*24
        bx=tx-tw-6 if left else tx-6
        reserved.extend([(bx-8,ly-31,tw+28,44),(x-22,y-22,44,44)])
    def intersects(a,b):return a[0]<b[0]+b[2] and a[0]+a[2]>b[0] and a[1]<b[1]+b[3] and a[1]+a[3]>b[1]
    manual_labels={
        '中华路':((367,533),(387,546)), '雨花路':((359,566),(325,578)),
        '北京东路':((390,397),(381,413)), '长江路':((390,445),(354,430)),
        '模范中路':((318,340),(287,329)), '大桥南路':((282,299),(311,292)),
        '梅花谷路':((511,444),(514,426)), '太平北路':((405,420),(435,418)),
        '建康路':((390,516),(423,496)), '博爱路':((556,455),(578,469)),
        '龙蟠南路':((404,573),(438,572)),
    }
    roadlabels=[]
    for n,(anchor,label) in manual_labels.items():
        x,y=screen(anchor);lx,ly=screen(label);left=lx<x
        tw=len(n)*16;tx=lx-5 if left else lx+5
        reserved.append((tx-tw-5 if left else tx-5,ly-22,tw+10,30))
        add(f'<path d="M{x:.1f},{y:.1f} L{lx:.1f},{ly-6:.1f}" fill="none" stroke="#9a9e89" stroke-width="1.1"/>')
        txt(tx,ly,n,16,'#687263',500,f'class="halo" text-anchor="{"end" if left else "start"}"')
        roadlabels.append(n)
    labelnames='应天大街 虎踞路 凤台南路 北京西路 中山路 中山南路 中华路 中山东路 中山北路 中央路 虎踞北路 虎踞南路 凤台路 龙蟠中路 龙蟠南路 新模范马路 模范中路 北京东路 汉中路 汉中门大街 中山门大街 草场门大街 大桥南路 龙蟠路 江东北路 江东中路 扬子江大道 河西大街 雨花路 长江路 太平北路 太平南路 建康路 长乐路 陵园路 博爱路 梅花谷路 玄武湖隧道'.split()
    special={'应天大街','虎踞路','凤台南路','北京西路'}
    for n in labelnames:
        if n in manual_labels:continue
        candidates=[]
        for r in roads:
            if r['name']!=n:continue
            pts=[screen(p) for p in r['source_px']]
            for a,b in zip(pts,pts[1:]):
                dist=math.dist(a,b)
                if dist<10:continue
                angle=math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))
                if angle>90:angle-=180
                if angle<-90:angle+=180
                for frac in [.5,.25,.75]:
                    x=a[0]+(b[0]-a[0])*frac;y=a[1]+(b[1]-a[1])*frac
                    size=19 if n in special else 16
                    tw=len(n)*size; rad=math.radians(angle)
                    bw=abs(tw*math.cos(rad))+abs(24*math.sin(rad));bh=abs(tw*math.sin(rad))+abs(24*math.cos(rad))
                    box=(x-bw/2-5,y-bh/2-5,bw+10,bh+10)
                    if not(MX+18<box[0] and box[0]+box[2]<MX+MW-18 and MY+18<box[1] and box[1]+box[3]<MY+MH-18):continue
                    overlap=sum(intersects(box,bx) for bx in reserved)
                    candidates.append((overlap,-min(dist,tw*2),x,y,angle,box,size))
        if candidates:
            c=min(candidates);overlap,_,x,y,angle,box,size=c
            if overlap==0:
                reserved.append(box);roadlabels.append(n)
                txt(x,y+5,n,size,'#876441' if n in special else '#6e776a',600 if n in special else 400,f'class="halo" text-anchor="middle" transform="rotate({angle:.1f} {x:.1f} {y:.1f})"')
    for d in pois:
        x,y=d['layout_px'];lx,ly=screen(d['label_source_px']);c=palette[d['zone']];left=lx<x
        tx=lx-8 if left else lx+8
        add(f'<path d="M{x:.1f},{y:.1f} L{lx:.1f},{ly-9:.1f}" fill="none" stroke="{c}" stroke-width="1.6"/>')
        add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="16" fill="{c}" stroke="#f7f7ef" stroke-width="3"/>')
        txt(x,y+5,str(d['number']).zfill(2),14,'white',600,'text-anchor="middle"')
        txt(tx,ly,d['name'],24,'#2b433b',600,f'class="halo" text-anchor="{"end" if left else "start"}"')
    add('</g>')
    add('<path d="M1730 225L1719 256L1730 249L1741 256Z" fill="#355b49"/>')
    txt(1730,215,'N',19,'#355b49',600,'text-anchor="middle"')
    # Approximate scale at central latitude, corresponding to the unwarped map.
    sx,sy=100,1518; length=1000/32.4*S
    add(f'<path d="M{sx},{sy-8}V{sy}H{sx+length:.1f}V{sy-8}" fill="none" stroke="#5b7465" stroke-width="2"/>')
    txt(sx,sy+27,'约 1 km',17,'#6c8071')
    add('<line x1="1820" y1="180" x2="1820" y2="1570" stroke="#d2dacb"/>')
    txt(1862,214,'景点索引',28,'#2d493b',600)
    y=258
    for zone,title in [('A','滨江北段'),('B','鼓楼 · 玄武湖'),('C','钟山 · 博物院'),('D','总统府 · 老城南'),('E','河西滨江')]:
        txt(1862,y,title,18,palette[zone],600);y+=34
        for d in [d for d in pois if d['zone']==zone]:
            txt(1862,y,str(d['number']).zfill(2),17,palette[zone],600)
            txt(1904,y,d['name'],23,'#344c3e',500);y+=35
        y+=19
    y+=10
    txt(1862,y,'道路与地形图例',26,'#2d493b',600);y+=42
    for kind,label in [('ground','地面主要道路'),('elevated','高架 / 桥梁段'),('tunnel','隧道 / 下穿段')]:
        col={'ground':'#c6c5b4','elevated':'#ad9374','tunnel':'#9a94b4'}[kind]
        extra='stroke-dasharray="8 7"' if kind=='tunnel' else ''
        add(f'<path d="M1862 {y-6}H1923" stroke="{col}" stroke-width="{3 if kind=="tunnel" else 8}" {extra}/>')
        if kind!='tunnel':add(f'<path d="M1862 {y-6}H1923" stroke="{"#faf9f0" if kind=="ground" else "#f5d8a5"}" stroke-width="4"/>')
        txt(1940,y,label,21,'#657767');y+=38
    y+=22
    txt(1862,y,'这一版校正了什么',26,'#2d493b',600);y+=40
    for line in ['景点保留公开坐标，名称用引线避让。','中山南路、中华路分别绘制。','玄武湖隧道用虚线表示地下通行。','湖岸与秦淮河采用 OSM 几何数据。','南京眼仍跨夹江，连接江心洲与河西。']:
        txt(1862,y,line,19,'#6d7e6e');y+=34
    y+=22
    txt(1862,y,'建模边界',25,'#2d493b',600);y+=38
    for line in ['普通楼群继续留白；先建立道路和地标。','长江、岛屿、山体仍为概括形状。','景点锚点不等于入口或建筑占地边界。']:
        txt(1862,y,line,19,'#6d7e6e');y+=32
    add('<line x1="48" y1="1600" x2="2330" y2="1600" stroke="#d2dacb"/>')
    txt(50,1636,'14 个景点锚点  /  14 组骨架道路 + 景点连接路  /  道路宽度与标记大小为示意',19,'#5f7766')
    txt(50,1668,'核心主城视口，不含南京全市行政区；未展开匝道及普通支路。',17,'#829080')
    txt(2328,1636,'地理数据 © OpenStreetMap contributors · ODbL 1.0',17,'#6f8273',400,'text-anchor="end"')
    txt(2328,1668,'坐标、分层与来源见同目录 JSON / 说明文件',17,'#829080',400,'text-anchor="end"')
    add('</svg>')
    print('Road labels placed:',len(roadlabels),'Missing:',set(labelnames)-set(roadlabels))
    return '\n'.join(out)

(OUT/'nanjing-layout-corrected.svg').write_text(build())
print('Generated',len(roads),'road ways;',len(lakes),'lake relations;',len(pois),'unshifted landmarks')
