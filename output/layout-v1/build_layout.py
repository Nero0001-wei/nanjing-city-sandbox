from pathlib import Path
import json, math, html

OUT=Path(__file__).parent
W,H=1760,1200
S=1.72
def screen(p): return (64+(p[0]-20)*S,190+(p[1]-165)*S)
def geo(lon,lat):
    return (((lon+180)/360*4096-3398)*256,((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*4096-1661)*256)
def to_geo(x,y):
    return ((3398+x/256)/4096*360-180,math.degrees(math.atan(math.sinh(math.pi*(1-2*(1661+y/256)/4096)))))

# Each coordinate is a public map/encyclopedia anchor, not a surveyed building footprint.
raw=[
('yangtze-bridge','南京长江大桥',118.7388,32.1152,'A',(251.8,207.8),(300,193),'桥头堡 + 双层桁架','https://en.wikipedia.org/wiki/Nanjing_Yangtze_River_Bridge'),
('yuejiang','阅江楼',118.7411583,32.0962889,'A',(258.7,272.9),(282,273),'山顶楼阁','https://en.wikipedia.org/wiki/Yuejiang_Tower'),
('zifeng','紫峰大厦',118.77806,32.06247,'B',(350,388),(298,374),'阶梯塔身 + 尖顶','https://en.wikipedia.org/wiki/Zifeng_Tower'),
('jiming','鸡鸣寺',118.79000,32.06306,'B',(408,395),(415,424),'寺院 + 药师佛塔','https://en.wikipedia.org/wiki/Jiming_Temple'),
('xuanwu','玄武湖',118.79833,32.07306,'B',(425,352),(455,334),'湖岸 + 五洲概括','https://en.wikipedia.org/wiki/Xuanwu_Lake'),
('mingxiaoling','明孝陵',118.834568,32.060305,'C',(520,395),(493,372),'明楼 + 宝城','https://zh.wikipedia.org/wiki/明孝陵'),
('zhongshan','中山陵',118.8483,32.0643,'C',(585,380),(607,370),'蓝顶祭堂 + 台阶轴线','https://en.wikipedia.org/wiki/Sun_Yat-sen_Mausoleum'),
('meiling','美龄宫',118.84145,32.04766,'C',(557,447),(585,448),'绿顶主楼 + 林荫环道','https://zh.wikipedia.org/wiki/美龄宫'),
('museum','南京博物院',118.8194,32.0425,'C',(480,477),(501,493),'大殿屋顶 + 门前广场','https://en.wikipedia.org/wiki/Nanjing_Museum'),
('presidential','总统府',118.79222,32.04528,'D',(407,457),(351,465),'门楼 + 简化院落','https://en.wikipedia.org/wiki/Presidential_Palace_(Nanjing)'),
('fuzimiao','夫子庙',118.783786,32.022579,'D',(398,525),(434,523),'大成殿 + 秦淮河岸','https://en.wikipedia.org/wiki/Nanjing_Fuzimiao'),
('zhonghua','中华门',118.7764861,32.0146861,'D',(351,555),(284,556),'瓮城 + 两段城墙','https://en.wikipedia.org/wiki/Gate_of_China,_Nanjing'),
('baoen','大报恩寺',118.77804,32.01117,'D',(374,583),(402,606),'现代报恩塔的简化轮廓','https://mapcarta.com/W859565692'),
('nanjing-eye','南京眼',118.69788,31.99707,'E',(132.6,613.8),(154,632),'倾斜双环 + 步行桥','https://mapcarta.com/N3281370485')]
palette={'A':'#a36c3d','B':'#43776b','C':'#698044','D':'#af6050','E':'#527891'}
pois=[]
for i,(id,name,lon,lat,zone,layout,label,model,url) in enumerate(raw,1):
    anchor=geo(lon,lat)
    x,z=screen(layout)
    pois.append(dict(id=id,number=i,name=name,zone=zone,longitude=lon,latitude=lat,source=url,coordinate_system='WGS84 (public source coordinate)',anchor_source_px=list(anchor),layout_source_px=list(layout),layout_px=[round(x,2),round(z,2)],label_source_px=list(label),model=model,three_position=[round((x-640)/10,3),0,round((z-600)/10,3)],offset_m_approx=round(math.hypot(layout[0]-anchor[0],layout[1]-anchor[1])*32.4),status='public_reference_anchor; not survey-grade'))

# Hand simplified from the cached 3x3 OSM zoom-12 reference, not vector-survey geometry.
features=[
 ('yangtze','长江','water',[[0,735],[20,691],[56,659],[90,642],[125,628],[145,610],[151,592],[144,565],[145,533],[153,505],[171,474],[184,441],[196,407],[207,373],[215,340],[223,312],[240,284],[263,255],[291,231],[306,213],[354,177],[407,140],[462,104],[520,69],[584,34],[650,0],[522,0],[473,25],[428,52],[389,80],[351,107],[320,132],[287,162],[251,196],[216,233],[184,274],[152,318],[120,369],[89,428],[61,486],[29,552],[0,615]]),
 ('jiangxin','江心洲','island',[[20,677],[48,651],[79,631],[109,619],[130,605],[138,590],[130,563],[129,538],[137,502],[154,470],[173,425],[196,371],[182,381],[160,408],[136,441],[110,483],[87,528],[61,572],[40,618]]),
 ('qianzhou','潜洲','island',[[156,382],[173,366],[187,340],[198,314],[186,325],[169,350]]),
 ('xuanwu-water','玄武湖','water',[[383,331],[393,329],[405,334],[416,330],[426,334],[433,348],[439,358],[443,375],[435,385],[422,384],[408,380],[398,374],[390,362],[384,349]]),
 ('xuanwu-island-1','环洲','island',[[388,344],[394,338],[400,342],[399,353],[393,357],[389,352]]),
 ('xuanwu-island-2','樱洲','island',[[402,345],[410,343],[412,349],[405,353],[401,350]]),
 ('xuanwu-island-3','梁洲','island',[[408,333],[417,334],[419,342],[413,344],[407,341]]),
 ('xuanwu-island-4','菱洲','island',[[413,360],[422,357],[427,367],[423,374],[417,373]]),
 ('xuanwu-island-5','翠洲','island',[[427,341],[433,349],[433,359],[427,358],[423,350]]),
 ('purple-mountain','紫金山 / 钟山景区','mountain',[[471,365],[483,343],[501,331],[504,310],[532,295],[560,289],[593,284],[619,299],[634,326],[650,344],[663,372],[671,407],[659,436],[638,451],[608,455],[580,451],[548,449],[523,437],[505,418],[492,395]]),
 ('mochou','莫愁湖','water',[[272,472],[285,473],[290,486],[283,501],[273,500],[267,489]]),
 ('qinhua outer','外秦淮河','river',[[207,382],[216,410],[229,437],[237,471],[257,491],[288,515],[318,539],[352,557],[389,564],[411,570],[437,559],[454,531],[459,510],[444,493]]),
 ('qinhua inner','内秦淮河','river',[[257,491],[282,503],[310,504],[336,514],[357,526],[383,532],[407,531],[427,520],[444,493]]),
 ('taicheng','明城墙 · 台城段','wall',[[379,334],[379,356],[389,377],[407,389],[431,392],[447,388]]),
 ('zhonghua-wall','明城墙 · 中华门段','wall',[[317,542],[337,553],[352,553],[376,558],[399,565]]),
 ('zhongshan-road','中山路—中华路方向','road',[[364,389],[363,418],[365,445],[362,482],[361,520],[361,551]]),
 ('east-road','中山东路方向','road',[[307,444],[365,445],[407,449],[448,452],[486,459],[515,457]]),
 ('bridge-structure','南京长江大桥','bridge',[[210,184],[304,238]]),
 ('eye-structure','南京眼步行桥','bridge',[[125,607],[140,620]])]

base={'title':'南京主城景点沙盘二维布局 v1','created':'2026-10-29','scope':'主城景点裁切，不是南京全市行政区地图','canvas':[W,H],'projection':'OSM Web Mercator zoom 12 pixel reference; anchors from public WGS84 sources','reference_tiles':{'zoom':12,'x':[3398,3400],'y':[1661,1663]},'layout_transform':{'scale':S,'x':'64 + (source_x - 20) * 1.72','y':'190 + (source_y - 165) * 1.72'},'three_mapping':'X=(layout_px.x-640)/10; Y=0; Z=(layout_px.y-600)/10; north=-Z; heights and footprint sizes to be set independently','geometry_status':'Water/terrain/road/wall outlines manually simplified from OSM reference. Not exact surveyed boundaries. Landmarks have separate geographic anchors and display centers.','attribution':'Map reference © OpenStreetMap contributors, ODbL 1.0; https://www.openstreetmap.org/copyright','sources':['https://wlj.nanjing.gov.cn/zwfw/bszlxz/202601/t20260121_5773976.html','https://zschina.nanjing.gov.cn/fjms/fwzn/ldxl/202303/t20230310_3859261.html','https://www.xuanwuhu.net/UploadFile/20250922115602.pdf'],'landmarks':pois,'features':[dict(id=id,name=name,kind=kind,source_px=ps,lon_lat=[list(to_geo(*p)) for p in ps],layout_px=[list(screen(p)) for p in ps]) for id,name,kind,ps in features]}
(OUT/'nanjing-layout-data.json').write_text(json.dumps(base,ensure_ascii=False,indent=2))

def build(mode):
    p=[]
    def add(s):p.append(s)
    def text(x,y,t,size=22,fill='#263b37',weight=400,extra=''):
        add(f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" {extra}>{html.escape(t)}</text>')
    def path(points,fill='none',stroke='none',width=1,close=False,extra=''):
        pts=[screen(v) for v in points]
        d='M '+' L '.join(f'{x:.1f},{y:.1f}' for x,y in pts)+(' Z' if close else '')
        add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round" {extra}/>')
    add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="南京主城景点二维布局图，北向上，14个景点锚点与地形关系"><title>南京主城景点沙盘二维布局</title><defs><clipPath id="map"><rect x="48" y="170" width="1196" height="898" rx="8"/></clipPath><pattern id="grid" width="43" height="43" patternUnits="userSpaceOnUse"><path d="M43 0H0V43" fill="none" stroke="#d8dfd4" stroke-width=".6"/></pattern></defs>')
    add('<style>text{font-family:"PingFang SC","Noto Sans CJK SC","Microsoft YaHei",sans-serif} .halo{paint-order:stroke;stroke:#f5f5ed;stroke-width:7;stroke-linejoin:round}</style><rect width="1760" height="1200" fill="#f5f5ed"/>')
    text(56,52,'NANJING  /  SCENE PLAN',16,'#74887b',500, 'letter-spacing="3"')
    text(56,112,'南京 · 主城景点布局',46,'#233d34',600)
    text(58,147,'以地理关系组织山水与地标，为等轴 2.5D 沙盘预留空间。',20,'#6b7d70')
    text(1698,57,'01  /  '+('模型占位方案' if mode=='layout' else '地理锚点底稿'),19,'#425d50',500,'text-anchor="end"')
    text(1698,89,'2026.10.29',16,'#849185',400,'text-anchor="end"')
    add('<g clip-path="url(#map)"><rect x="48" y="170" width="1196" height="898" fill="#edf1e5"/><rect x="48" y="170" width="1196" height="898" fill="url(#grid)"/>')
    for id,name,kind,ps in features:
        if kind=='water':path(ps,'#a9d8da','#88bdc3',1.3,True)
        if kind=='island':path(ps,'#d6e3bf','#b9cda7',1,True)
        if kind=='mountain':
            path(ps,'#d3dfbd','#b4c99e',1.3,True)
            # Contours are schematic design bands, not elevation contours.
            for factor in [.8,.59,.38]:
                path([[571+(x-571)*factor,359+(y-359)*factor] for x,y in ps],'none','#b4c59e',1.4,True)
    for id,name,kind,ps in features:
        if kind=='river':path(ps,'none','#9ecfd0',9 if 'outer' in id else 6)
        if kind=='road':path(ps,'none','#ffffff',7);path(ps,'none','#d9d9c7',1.4)
        if kind=='wall':path(ps,'none','#7d9085',6);path(ps,'none','#edf1e5',1.8,extra='stroke-dasharray="2 9"')
        if kind=='bridge':path(ps,'none','#f5f5ed',11);path(ps,'none','#8c9c94',2.2)
    for label,sp,size,col in [('江 北',(145,245),27,'#7d9585'),('河 西',(240,587),27,'#9ba58c'),('主 城',(330,445),24,'#a4ad97'),('紫 金 山',(562,319),28,'#71855d'),('钟山景区',(561,338),16,'#84936e'),('江心洲',(102,548),17,'#758b6c'),('莫愁湖',(276,464),16,'#5d9294'),('外秦淮河',(285,523),17,'#689b9d'),('内秦淮河',(426,549),16,'#689b9d')]:
        x,y=screen(sp);text(x,y,label,size,col,500,'text-anchor="middle"')
    x,y=screen((132,394));text(x,y,'长 江',32,'#5c969f',500,f'transform="rotate(-55 {x} {y})" text-anchor="middle"')
    # Schematic links stop short of occupying the background with street detail.
    add('</g>')
    for d in pois:
        i=d['number'];color=palette[d['zone']]
        a=screen(d['anchor_source_px']);c=screen(d['layout_source_px'] if mode=='layout' else d['anchor_source_px'])
        lx,ly=screen(d['label_source_px']);x,y=c
        if mode=='layout':
            if i not in [1,5,14]:
                fw,fh=(62,44) if i not in [3,4,13] else (40,48)
                add(f'<rect x="{x-fw/2}" y="{y-fh/2}" width="{fw}" height="{fh}" rx="9" fill="{color}" fill-opacity=".09" stroke="{color}" stroke-opacity=".35" stroke-dasharray="5 4"/>')
            if math.dist(a,c)>6:
                add(f'<path d="M{a[0]:.1f},{a[1]:.1f} L{x:.1f},{y:.1f}" stroke="{color}" opacity=".45" stroke-dasharray="3 4"/><circle cx="{a[0]:.1f}" cy="{a[1]:.1f}" r="3.6" fill="#f5f5ed" stroke="{color}" stroke-width="1.8"/>')
        # Leader lines allow all anchors to retain their recorded coordinates.
        left=lx<x
        tx=lx-6 if left else lx+6
        add(f'<path d="M{x:.1f},{y:.1f} L{lx:.1f},{ly-7:.1f}" fill="none" stroke="{color}" stroke-opacity=".4" stroke-width="1.3"/>')
        add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{15 if mode=="layout" else 10}" fill="{color}" stroke="#f5f5ed" stroke-width="3"/>')
        text(x,y+5,str(i).zfill(2),14 if mode=='layout' else 10,'#ffffff',600,'text-anchor="middle"')
        text(tx,ly,d['name'],23,'#2b4338',500,f'class="halo" text-anchor="{"end" if left else "start"}"')
    # North arrow and map caption
    add('<path d="M1172 214L1163 238L1172 233L1181 238Z" fill="#355b49"/>')
    text(1172,204,'N',18,'#355b49',600,'text-anchor="middle"')
    text(1172,263,'北',15,'#355b49',400,'text-anchor="middle"')
    add('<line x1="1270" y1="170" x2="1270" y2="1068" stroke="#ccd5c8"/>')
    text(1310,198,'14 个景点锚点 · 5 组场景',23,'#294537',600)
    y=240
    for zone,title in [('A','北部滨江'),('B','鼓楼 · 玄武湖'),('C','钟山 · 博物院'),('D','总统府 · 老城南'),('E','河西滨江')]:
        color=palette[zone];add(f'<rect x="1310" y="{y-15}" width="4" height="19" rx="2" fill="{color}"/>');text(1324,y,title,19,color,600);y+=26
        for d in [q for q in pois if q['zone']==zone]:
            text(1310,y,str(d['number']).zfill(2),16,color,600)
            text(1343,y,d['name'],19,'#344a3c',500)
            text(1343,y+24,d['model'],15,'#7e8c7b');y+=45
        y+=6
    add('<line x1="56" y1="1091" x2="1704" y2="1091" stroke="#ccd5c8"/>')
    text(56,1124,'● 景点中心    ▧ 模型预留范围    ○ 原始位置（偏移时显示）',17,'#526b5b')
    text(56,1153,'北向上 · 山水轮廓概括 · 道路仅示方向 · 模型大小不代表真实建筑占地',16,'#7e8c7b')
    text(1704,1124,'范围：南京核心主城及滨江地标，不含全市行政区',16,'#526b5b',400,'text-anchor="end"')
    text(1704,1153,'地理参考 © OpenStreetMap contributors / ODbL；景点坐标来源见数据文件',15,'#7e8c7b',400,'text-anchor="end"')
    add('</svg>')
    return '\n'.join(p)

for mode in ['layout','geographic']:
    (OUT/f'nanjing-{mode}.svg').write_text(build(mode))

(OUT/'说明与来源.txt').write_text('''南京主城景点沙盘 · 二维布局 v1
制作日期：2026-10-29

交付文件
nanjing-layout.svg / .png：模型占位方案。编号圆点为建议的展示中心；淡色虚线框为初始模型范围。
nanjing-geographic.svg / .png：地理锚点底稿。所有景点圆点按公开坐标投影，标签引线仅用于排版。
nanjing-layout-data.json：原始经纬度、来源、建议展示坐标、Three.js 场景坐标和概括地形路径。
build_layout.py：可重新生成地图的源脚本。

取舍
本版为核心主城+滨江地标裁切，不是南京全市行政区域。取14个景点锚点（其中玄武湖为景观组）。
保留长江大桥、阅江楼、紫峰大厦、鸡鸣寺、玄武湖、明孝陵、中山陵、美龄宫、南京博物院、总统府、夫子庙、中华门、大报恩寺、南京眼。
老门东可并入老城南区域作为简化陪衬；牛首山、栖霞山等外围景点未布入本画幅，后续另设扩展区域。
不建立普通居民楼和普通办公楼群。图中空白区域为留白，不要求补满建筑。

地理与艺术化调整
原始位置和展示位置分开存储。中华门以南的大报恩寺、夫子庙、南京博物院等为模型和标签留空而小幅移位。
偏移值在 JSON 的 offset_m_approx 中记录，是按参考图纬度近似换算的设计偏移，不是坐标误差。
所有水体、山体、道路、城墙形状均为依据 OSM 参考底图人工概括的草图，不是精确GIS边界。
玄武湖与长江保持为独立水体；南京眼跨夹江连接江心洲一侧与河西，不跨长江主航道。
城墙仅画台城和中华门附近示意段，不捏造闭合城墙环。
北向上，后续 Three.js 中 north=-Z。所有模型高度和实际占位尺寸独立于地图尺度。
水面应使用闭合 polygon，河道需先扩展成带状 mesh，mountain 需加高度；本版不包含模型和高程。

资料
地理底图 © OpenStreetMap contributors，https://www.openstreetmap.org/copyright，ODbL 1.0。
缓存为当前城市视口的9张z12瓦片（https://tile.openstreetmap.org/12/{x}/{y}.png），仅用于人工校对，未使用高德API。
地形派生数据使用ODbL 1.0；景点坐标逐条附来源URL。网站资料查询日期：2026-10-29。
南京市文化和旅游局景区名录：https://wlj.nanjing.gov.cn/zwfw/bszlxz/202601/t20260121_5773976.html
钟山官方平面图：https://zschina.nanjing.gov.cn/fjms/fwzn/ldxl/202303/t20230310_3859261.html
玄武湖官方导览：https://www.xuanwuhu.net/UploadFile/20250922115602.pdf

核对注意
景区坐标可能指主建筑或景区中心，并非入口位置，适合作为本项目的布局锚点。
大报恩寺英文维基页在本次查询中显示了与城南位置矛盾的坐标，未采纳；采用Mapcarta引用的OSM way 859565692位置。
全程使用WGS84参考点，不混入GCJ-02或百度坐标。后续如使用高德底图，需要统一坐标系。
本阶段无须接入高德CLI/MCP，也无须API key。
''')
print('Generated 2 SVG maps and coordinate data',len(pois),'landmarks')
