"""Shared, deterministic Blender source for nine tree-free miniature landmarks.
Usage: Blender -b --factory-startup --python build_landmark.py -- meiling|museum|zhonghua|fuzimiao|presidential|baoen|jiming|zifeng|yuejiang
Concept models, not surveyed reconstructions. Final glTF triangle budget is verified.
"""
import bpy, math, json, struct, hashlib, sys
from pathlib import Path
from math import sin, cos, pi
from mathutils import Vector
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE)); import geometry as G
ID=sys.argv[sys.argv.index('--')+1]
NAME,SCALE={'meiling':('美龄宫',.47),'museum':('南京博物院',.4),'zhonghua':('中华门',.38),'fuzimiao':('夫子庙',.44),'presidential':('总统府',.39),'baoen':('大报恩寺',.425),'jiming':('鸡鸣寺',.43),'zifeng':('紫峰大厦',.42),'yuejiang':('阅江楼',.28)}[ID]
PROJECT=HERE.parent/(NAME+'模型'); OUT=PROJECT/'web';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
G.COL={}
for name in ['01_基础台阶','02_主体墙柱','03_屋顶或城墙','04_门窗装饰','05_栏杆线脚','06_摄影棚']:
    c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c);G.COL[name]=c
root=bpy.data.objects.new(NAME+'_整体控制器',None);G.COL['01_基础台阶'].objects.link(root);G.root=root
root['说明']='同风格无树木建筑概念模型，非测绘复原。Z-up，正面 -Y。'
root['网页预算']='20,000–40,000 个导出三角面，包含材质、贴图与顶点 AO。'
root['网页等比缩放']=SCALE
Mesh=G.Mesh;material=G.material
STONE=material('暖白石材','E2D4BC',.76)
CREAM=material('奶油灰黄墙面','D7BD91',.87)
RED=material('暗朱红漆柱','974A36',.49,coat=.12)
WOOD=material('深胡桃木门框','594135',.62)
GLASS=material('灰蓝玻璃','40555B',.26,coat=.3)
TEAL=material('青绿木构','355D55',.62)
GOLD=material('金线与檐饰','BA9149',.48)
DARK=material('内室暗灰','3C4140',.95)
roofcolor={'meiling':'527A43','fuzimiao':'555B60','presidential':'60666B','baoen':'BECFD4','jiming':'606467'}.get(ID,'D69B3A')
TILE=material({'meiling':'绿色琉璃瓦','fuzimiao':'灰陶瓦','presidential':'灰陶瓦','baoen':'浅蓝玻璃翼板','jiming':'灰陶瓦'}.get(ID,'金色琉璃瓦'),roofcolor,.34,coat=.24)
TILEBASE=material('瓦垄阴影底色',{'meiling':'3A5A37','fuzimiao':'3B4146','presidential':'42494E','baoen':'91ABB4','jiming':'3D4448'}.get(ID,'AB742B'),.5,coat=.08)
BACK=material('摄影棚暖灰','E9E9E6',.85)

def box(name,p,d,mat=STONE,col='02_主体墙柱',bevel=0):
    m=Mesh(name,col,mat);m.box(p,d);o=m.finish()
    if bevel:
        mod=o.modifiers.new('轮廓单段倒角','BEVEL');mod.width=bevel;mod.segments=1
        mod=o.modifiers.new('加权法线','WEIGHTED_NORMAL');mod.keep_sharp=True
    return o

def texture(name,kind):
    w=1024;h=256 if kind=='frieze' else 1024
    yy,xx=np.mgrid[0:h,0:w].astype(np.float32);u=xx/w;v=yy/h
    if kind=='frieze':
        x=u*4%1;rgb=np.full((h,w,3),[.21,.34,.31],np.float32)
        rgb[(v<.08)|(v>.92)|(x<.025)|(x>.975)]=[.73,.57,.29]
        diamond=abs(x-.5)/.32+abs(v-.5)/.28
        rgb[(abs(diamond-1)<.045)|(abs(np.sqrt(((x-.5)/.17)**2+((v-.5)/.21)**2)-1)<.09)]=[.81,.65,.36]
    else:
        nx,ny=(3,7) if kind=='brick' else (4,4)
        row=np.floor(v*ny);x=u*nx+(row%2)*(.5 if kind=='brick' else 0);y=v*ny
        edge=np.minimum(np.minimum(x%1,1-x%1),np.minimum(y%1,1-y%1));seam=np.clip((.015-edge)/.009,0,1)
        variation=.034*np.sin(np.floor(x)*23.1+row*31.7)
        col=np.array([.66,.65,.60] if kind=='brick' else [.86,.81,.72])
        rgb=np.clip(col*(1-.24*seam[...,None]+variation[...,None]),0,1).astype(np.float32)
    px=np.ones((h,w,4),np.float32);px[:,:,:3]=rgb
    im=bpy.data.images.new(name,width=w,height=h,alpha=False);im.colorspace_settings.name='sRGB';im.pixels.foreach_set(px.ravel());im.filepath_raw=str(OUT/(kind+'_1024.png'));im.file_format='PNG';im.save();im.pack()
    mat=material(name,'FFFFFF',.82);n=mat.node_tree.nodes;l=mat.node_tree.links;bs=next(n for n in n if n.type=='BSDF_PRINCIPLED');tex=n.new('ShaderNodeTexImage');tex.image=im;tex.extension='REPEAT';l.new(tex.outputs['Color'],bs.inputs['Base Color']);return mat
BRICK=texture('灰砖错缝','brick');PAVING=texture('浅色铺石','paving');PAINT=texture('青绿金线彩绘','frieze')

def stairs(name,x,y,width,length,z0,z1,n):
    m=Mesh(name,'01_基础台阶',STONE)
    for j in range(n):
        h=(z1-z0)*(j+1)/n;m.box((x,y+length*(j+.5)/n,z0+h/2),(width,abs(length)/n+.004,h))
    return m.finish()

RAIL_POSTS=set()
def rail(name,a,b,z,n=8,height=.9):
    m=Mesh(name,'05_栏杆线脚',STONE)
    for j in range(n+1):
        t=j/n;x=a[0]+(b[0]-a[0])*t;y=a[1]+(b[1]-a[1])*t
        key=tuple(round(v,4) for v in (x,y,z))
        if key in RAIL_POSTS:continue
        RAIL_POSTS.add(key)
        m.box((x,y,z+height/2),(.23,.23,height));m.box((x,y,z+height),(.31,.31,.16));m.box((x,y,z+.08),(.33,.33,.16))
    L=math.dist(a,b);angle=math.atan2(b[1]-a[1],b[0]-a[0]);dx,dy=cos(angle),sin(angle)
    # Rectangular stone rails rotated along any line, including stair handrails.
    for h in [.24,height-.12]:
        verts=[((a[0]+b[0])/2+dx*s*L/2-dy*q*.085,(a[1]+b[1])/2+dy*s*L/2+dx*q*.085,z+h+r*.08) for s,q,r in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
        m.add(verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    return m.finish()

def window(name,x,y,z,w,h,angle=0,door=False):
    m=Mesh(name,'04_门窗装饰',[GLASS,WOOD,STONE])
    m.box((0,.01,0),(w,.09,h),1 if door else 0)
    for sx in [-1,1]:m.box((sx*(w/2+.055),-.06,0),(.11,.18,h+.2),1)
    for sz in [-1,1]:m.box((0,-.06,sz*(h/2+.055)),(w+.22,.18,.11),1)
    for xx in [-w*.25,0,w*.25]:m.box((xx,-.075,h*.12),(.036,.13,h*.76),1)
    for zz in [-.22,.12,.44]:m.box((0,-.08,zz*h),(w,.13,.036),1)
    m.box((0,-.12,-h/2-.14),(w+.35,.33,.16),2)
    if door:
        for xx in [-w*.25,w*.25]:
            m.box((xx,-.10,-h*.29),(w*.38,.12,h*.29),1)
            m.tube([(xx*.32,-.19,-.15),(xx*.32,-.19,.1)],.045,6,2)
    o=m.finish();o.location=(x,y,z);o.rotation_euler.z=angle;return o

def column(name,x,y,z,h,r=.23):
    m=Mesh(name,'02_主体墙柱',[RED,STONE]);m.tube([(x,y,z+.18),(x,y,z+h)],r,12,0)
    m.tube([(x,y,z),(x,y,z+.15)],r*1.4,12,1);m.tube([(x,y,z+h-.10),(x,y,z+h+.05)],r*1.2,12,0);return m.finish()

def roof(name,cx,cy,z,a,b,h,ridge,nu=38,ns=17,rows=9,skirt=False):
    """Curved hip roof, four watertight-looking planes and explicit ceramic ribs."""
    def front(u,t,s):return (cx+u*(ridge+(a-ridge)*t),cy+s*b*t,z+h*(1-t)**1.55+.24*abs(u)**8*t**4+.11*t**8)
    def side(u,t,s):return (cx+s*(ridge+(a-ridge)*t),cy+u*b*t,z+h*(1-t)**1.55+.24*abs(u)**8*t**4+.11*t**8)
    m=Mesh(name+'_曲面瓦底','03_屋顶或城墙',TILEBASE)
    compact=ID in ['jiming','yuejiang']
    for fun,n in [(front,(12 if compact else 24) if a>3 else 8),(side,(6 if compact else 12) if a>3 else 6)]:
        for s in [-1,1]:
            vs=[fun(-1+2*i/n,.001+.999*j/rows,s) for j in range(rows+1) for i in range(n+1)]
            fs=[(j*(n+1)+i,j*(n+1)+i+1,(j+1)*(n+1)+i+1,(j+1)*(n+1)+i) for j in range(rows) for i in range(n)]
            m.add(vs,fs)
    o=m.finish();so=o.modifiers.new('瓦底厚度','SOLIDIFY');so.thickness=.075
    ribs=Mesh(name+'_琉璃筒瓦','03_屋顶或城墙',TILE,smooth=True)
    for fun,n in [(front,nu),(side,ns)]:
        for s in [-1,1]:
            for i in range(n+1):
                u=-1+2*i/n;ts=np.linspace(.02 if fun==front else .06,1,rows+1)
                ribs.tube([(x,y,zz+.045) for x,y,zz in [fun(u,float(t),s) for t in ts]],.075 if a>6 else .055,6)
    ribs.finish()
    edge_steps=8 if ID=='yuejiang' else 12 if ID in ['fuzimiao','presidential','jiming'] else 24
    hip_steps=4 if ID=='yuejiang' else 6 if ID in ['fuzimiao','presidential','jiming'] else 10
    edge=Mesh(name+'_屋脊与翘角','03_屋顶或城墙',TILE,smooth=True)
    edge.tube([(cx-ridge,cy,z+h+.07),(cx+ridge,cy,z+h+.07)],.15,8)
    for s in [-1,1]:
        for fun in [front,side]:edge.tube([fun(-1+2*i/edge_steps,1,s) for i in range(edge_steps+1)],.11,6)
        for sx in [-1,1]:edge.tube([front(sx,j/hip_steps,s) for j in range(hip_steps+1)],.13,6)
        edge.tube([(cx+s*(ridge+.55*sin(t*pi/2)),cy,z+h+.1+.65*t) for t in np.linspace(0,1,hip_steps)],.13,7)
    edge.finish()
    box(name+'_檐下枋',(cx,cy,z-.12),(a*1.82,b*1.8,.34),TEAL)
    for sy in [-1,1]:box(name+'_彩绘横枋',(cx,cy+sy*b*.905,z-.14),(a*1.82,.06,.28),PAINT,'04_门窗装饰')

def archwall(name,width,depth,height,openings,z0=0,loc=(0,0),angle=0,mat=None):
    m=Mesh(name,'03_屋顶或城墙',mat or BRICK);left=-width/2
    for cx,r,spring in sorted(openings):
        if cx-r>left:m.box(((left+cx-r)/2,0,z0+height/2),(cx-r-left,depth,height))
        for j in range(20):
            x1=cx-r+2*r*j/20;x2=cx-r+2*r*(j+1)/20
            z1=z0+spring+math.sqrt(max(0,r*r-(x1-cx)**2));z2=z0+spring+math.sqrt(max(0,r*r-(x2-cx)**2))
            m.prism([(x1,z1),(x2,z2),(x2,z0+height),(x1,z0+height)],-depth/2,depth/2)
        left=cx+r
    if left<width/2:m.box(((left+width/2)/2,0,z0+height/2),(width/2-left,depth,height))
    o=m.finish();o.location=(loc[0],loc[1],0);o.rotation_euler.z=angle
    return o

def archring(name,cx,y,z,r,spring,width=.22,depth=.18,segments=20,angle=0,origin=(0,0),bevel=.012):
    m=Mesh(name,'04_门窗装饰',STONE)
    for s in [-1,1]:
        for j in range(4):m.box((cx+s*(r+width/2),y,z+spring*(j+.5)/4),(width,depth,spring/4-.013))
    for j in range(segments):
        a=j*pi/segments+.006;b=(j+1)*pi/segments-.006
        m.prism([(cx+rr*cos(t),z+spring+rr*sin(t)) for rr,t in [(r,a),(r,b),(r+width,b),(r+width,a)]],y-depth/2,y+depth/2)
    o=m.finish();o.location=(origin[0],origin[1],0);o.rotation_euler.z=angle
    if bevel and r>1:
        mod=o.modifiers.new('券石边缘倒角','BEVEL');mod.width=bevel;mod.segments=1
    return o

CRENEL_POSTS=[]
def crenels(name,a,b,z,n):
    m=Mesh(name,'03_屋顶或城墙',[BRICK,STONE]);dx=b[0]-a[0];dy=b[1]-a[1]
    for j in range(n+1):
        x=a[0]+dx*j/n;y=a[1]+dy*j/n
        if any(abs(x-xx)<.67 and abs(y-yy)<.67 and abs(z-zz)<.12 for xx,yy,zz in CRENEL_POSTS):continue
        CRENEL_POSTS.append((x,y,z))
        m.box((x,y,z+.39),(.59,.59,.78),0);m.box((x,y,z+.79),(.66,.66,.13),1)
    o=m.finish()
    box(name+'_矮墙',((a[0]+b[0])/2,(a[1]+b[1])/2,z+.15),(abs(dx)+.5 if dx else .5,abs(dy)+.5 if dy else .5,.3),BRICK,'03_屋顶或城墙')
    return o

def build_meiling():
    box('紧凑石底座',(0,-.5,.16),(20,17,.32),PAVING,'01_基础台阶',.05)
    box('三层别墅_石基',(0,0,1.0),(16,11.2,1.35),BRICK,bevel=.045)
    box('主楼_奶油墙体',(0,0,4.55),(15.6,10.9,5.8),CREAM,bevel=.045)
    for z in [1.73,4.50,7.42]:box('环绕腰线',(0,0,z),(16.1,11.3,.22),STONE)
    # A recessed porch built in front of the principal wall, balcony above it.
    box('前廊石坪',(0,-6.4,.95),(8,2.9,1.25),PAVING,'01_基础台阶')
    stairs('入口宽阶',0,-8.8,5.5,1.4,.32,1.58,8)
    for x in [-3.3,-1.1,1.1,3.3]:column('前廊红柱',x,-7.1,1.6,2.8,.20)
    box('上层阳台板',(0,-6.35,4.48),(8.4,3.0,.3),STONE,bevel=.04)
    rail('阳台正面',(-3.9,-7.7),(3.9,-7.7),4.65,12,.8)
    for s in [-1,1]:rail('阳台侧面',(s*3.9,-7.7),(s*3.9,-5.45),4.65,4,.8)
    for z in [3.05,5.99]:
        for x in [-6.4,-4.1,-1.35,1.35,4.1,6.4]:window('南立面窗门',x,-5.49,z,1.32,1.94,door=abs(x)<2 and z<4)
        for x in [-6.2,-3.7,-1.2,1.2,3.7,6.2]:window('北立面窗',x,5.49,z,1.28,1.92,pi)
        for s in [-1,1]:
            for y in [-3.7,-1.2,1.2,3.7]:window('侧立面窗',s*7.84,y,z,1.28,1.92,s*pi/2)
    for x in [-6,-3,3,6]:
        for s in [-1,1]:window('石基层通风窗',x,s*5.66,1.02,.95,.55,pi if s>0 else 0)
    for s in [-1,1]:
        for x in [-7.7,7.7]:box('墙面竖向壁柱',(x,s*5.51,4.55),(.24,.13,5.65),STONE)
    # Slim green skirt around the upper-floor sill, characteristic double eaves.
    roof('下层绿瓦腰檐',0,0,4.73,8.65,6.1,.50,7.9,nu=40,ns=13,rows=3)
    # Waist roof must leave the occupied upper volume visible: its interior is hidden.
    roof('主楼绿瓦大顶',0,0,7.80,9.1,6.55,2.55,5.0,nu=40,ns=17,rows=7)
    # Small front dormer, a triangular gable emerging from the roof.
    m=Mesh('中央老虎窗山墙','02_主体墙柱',CREAM);m.prism([(-1.6,8.15),(1.6,8.15),(1.6,8.9),(0,10.05),(-1.6,8.9)],-4.4,-2.8);m.finish()
    window('老虎窗',0,-4.43,8.95,1.05,.90)
    roof('老虎窗小瓦顶',0,-3.45,9.04,1.95,1.18,1.15,.15,nu=10,ns=5,rows=4)
    for s in [-1,1]:rail('前台侧栏',(s*3.8,-7.5),(s*3.8,-5.5),1.6,4,.85)

def build_museum():
    box('整块石坪',(0,-.9,.16),(34,19.8,.32),PAVING,'01_基础台阶',.05)
    for z,w,d,h in [(.55,32,16.2,.46),(1.05,31.7,15.9,.54),(1.40,32.2,16.4,.18)]:box('大殿基台',(0,0,z),(w,d,h),PAVING,'01_基础台阶',.025)
    stairs('中央广阶',0,-10.4,11.6,2.6,.32,1.5,10)
    box('九开间大殿墙身',(0,.55,4.05),(22.1,10.2,5.1),CREAM,bevel=.035)
    for s in [-1,1]:
        box('对称附殿墙身',(s*13.1,.55,3.25),(4.1,8.4,3.5),CREAM,bevel=.03)
        roof('东西附殿',s*13.1,.55,5.17,2.85,5.0,1.5,.7,nu=10,ns=14,rows=4)
        for x in [s*12.1,s*14.1]:
            column('附殿檐柱',x,-4.5,1.5,3.4,.20);window('附殿前窗',x,-3.69,3.1,1.3,2.4)
        for y in [-1.8,.55,2.9]:window('附殿侧窗',s*15.18,y,3.2,1.45,2.35,s*pi/2)
    for i in range(10):
        x=-10.8+i*2.4
        column('九开间前檐红柱',x,-5.5,1.5,5.1,.25)
        column('九开间后檐红柱',x,5.5,1.5,5.1,.25)
        # Simplified but geometric layered bracket clusters.
        for sy in [-1,1]:
            y=sy*5.5
            for j in range(3):box('叠层斗拱',(x,y,6.2+j*.19),(.48+j*.29,.65+j*.31,.15),TEAL,'04_门窗装饰')
            box('斗拱金线',(x,y,6.67),(1.2,1.3,.065),GOLD,'04_门窗装饰')
    for i in range(9):
        x=-9.6+i*2.4
        window('九开间门窗',x,-4.59,3.65,1.93,3.9,door=abs(x)<4.9)
        window('背面门窗',x,5.69,3.65,1.93,3.9,pi)
    roof('老大殿单檐庑殿顶',0,.5,6.95,12.65,7.1,3.25,6.4,nu=44,ns=19,rows=6)
    for s in [-1,1]:
        rail('正面白石栏',(s*6.25,-8),(s*15.65,-8),1.5,10,.85)
        rail('侧面白石栏',(s*15.65,-8),(s*15.65,7.8),1.5,15,.85)
    rail('后方白石栏',(-15.65,7.8),(15.65,7.8),1.5,28,.85)
    # Restrained geometric stone lions, leg/body/head silhouettes instead of generic balls.
    for s in [-1,1]:
        x=s*6.25;y=-9.1;box('石狮基座',(x,y,.7),(.9,1.2,.72),STONE,'04_门窗装饰',.06)
        m=Mesh('入口石狮','04_门窗装饰',STONE)
        m.box((x,y,1.45),(.53,.72,.72));m.box((x,y-.26,1.97),(.60,.52,.55));m.box((x,y-.54,1.92),(.37,.23,.20))
        for dx in [-.23,.23]:m.box((x+dx,y-.23,1.26),(.19,.38,.57));m.box((x+dx,y-.4,1.04),(.23,.36,.18))
        o=m.finish();mod=o.modifiers.new('石狮造型倒角','BEVEL');mod.width=.09;mod.segments=2

def build_zhonghua():
    box('瓮城薄石底座',(0,-.5,.16),(29,34,.32),PAVING,'01_基础台阶',.05)
    # Four genuinely open passages, three exterior courts, shared central axis.
    for k,y in enumerate([-13.5,-5.2,4.2,13.5]):
        depth=2.8 if k==0 else 1.65;h=4.8 if k==0 else 4.35
        archwall('第%d道通透城门'%(k+1),23.6,depth,h,[(0,1.55,1.65)],.32,(0,y))
        for sy in [-1,1]:archring('主券门逐块券石',0,y+sy*(depth/2+.05),.32,1.55,1.65,.34,.24,20)
        box('城门上方石走道',(0,y,.32+h+.06),(26.3,depth+.25,.18),PAVING,'03_屋顶或城墙')
        for sy in [-1,1]:crenels('城门垛墙',(-12.8,y+sy*depth*.48),(12.8,y+sy*depth*.48),.32+h+.16,24)
    # Exterior walls seal the backs of the chambers; inner layer has real arched recesses.
    for s in [-1,1]:
        box('两侧外墙',(s*12.4,-.275,2.5),(1.2,29.25,4.36),BRICK,'03_屋顶或城墙')
        openings=[(-s*y,.73,1.45) for y in [-9.2,-7.15,-2.5,0,2.4,7.4,10.6]]
        angle=-s*pi/2;origin=(s*10.8,0)
        archwall('侧墙七处藏兵洞',28.5,2.0,4.35,openings,.32,origin,angle)
        for cy,r,sp in openings:archring('侧墙藏兵洞石券',cy,-1.07,.32,r,sp,.21,.16,18,angle,origin)
        box('两侧贯通步道',(s*11.2,0,4.77),(3.8,28.6,.3),PAVING,'03_屋顶或城墙')
        for x in [s*9.45,s*12.9]:crenels('两侧贯通垛墙',(x,-14.1),(x,14.1),4.92,26)
        # Shallow stairs climb the side paths and leave the middle gate passage open.
        stairs('对称登城阶梯',s*8.0,-6.15,1.6,-4.95,.32,4.92,30)
        m=Mesh('登城斜扶栏','05_栏杆线脚',STONE)
        for dx in [-.9,.9]:m.tube([(s*8+dx,-6.15,.95),(s*8+dx,-11.1,5.5)],.12,6)
        m.finish()
        stairs('城台上层登临石阶',s*11.75,-10.5,1.25,-3.4,4.92,8.29,20)
    # Front main terrace, chambers open north into the first courtyard.
    lower=[(x,.83,1.48) for x in [-9.7,-6.6,-3.6,3.6,6.6,9.7]]+[(0,1.55,1.65)]
    archwall('主城台后部六处藏兵洞',23.6,1.6,4.8,lower,.32,(0,-11.3),pi)
    for x,r,sp in lower:archring('城台后立面券石',x,-.87,.32,r,sp,.23,.17,18,pi,(0,-11.3))
    upper=[(x,.76,1.08) for x in [-9,-6,-3,0,3,6,9]]
    archwall('上层七处藏兵洞',22,2.8,2.8,upper,5.30,(0,-13),pi)
    box('上层藏兵洞背墙',(0,-14.49,6.7),(22.15,.32,2.8),BRICK,'03_屋顶或城墙')
    for x,r,sp in upper:archring('上层藏兵洞石券',x,-1.47,5.30,r,sp,.19,.16,18,pi,(0,-13))
    box('主城台上层铺石',(0,-13,8.16),(22.4,3.5,.24),PAVING,'03_屋顶或城墙')
    for y in [-14.55,-11.45]:crenels('主城台上层垛口',(-11,y),(11,y),8.29,21)
    for x in [-11,11]:crenels('主城台上层侧垛',(x,-14.55),(x,-11.45),8.29,3)
    # Broad stone corner quoins and base courses, visibly modelled without individual tiny bricks.
    for x in [-12.85,12.85]:
        for y in [-14.9,14.35]:
            for j in range(10):box('城角大块护角石',(x,y,.58+j*.43),(.49 if j%2 else .8,.55,.40),STONE,'04_门窗装饰',.018)
    # Entrance portal reaches ground. Only flanking foundations, no false floor blockage.
    for s in [-1,1]:box('城门外基础石带',(s*7.4,-14.96,.51),(11.45,.28,.38),STONE,'01_基础台阶')

if ID in ['jiming','zifeng','yuejiang']:
    from north_landmarks import build
    build(ID,globals())
elif ID in ['fuzimiao','presidential','baoen']:
    from old_city_landmarks import build
    build(ID,globals())
else:
    {'meiling':build_meiling,'museum':build_museum,'zhonghua':build_zhonghua}[ID]()

def active(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
objects=[o for o in root.children if o.type=='MESH']
for o in objects:
    active(o)
    for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
    o.data.calc_loop_triangles()
tri=sum(len(o.data.loop_triangles) for o in objects)
print('GEOMETRY_TRIANGLES',ID,tri,flush=True)
if '--geometry-only' in sys.argv:
    print(sorted([(len(o.data.loop_triangles),o.name) for o in objects],reverse=True)[:18],flush=True)
    sys.exit(0)
assert 20000<=tri<=40000,(ID,tri)
floor=box('摄影棚地面',(0,0,-.16),(240,240,.25),BACK,'06_摄影棚');floor.parent=None
if ID in ['fuzimiao','presidential','baoen','jiming','zifeng','yuejiang']:floor.scale.x=5;floor.scale.y=5
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.cycles.max_bounces=6
world=bpy.data.worlds.new('柔和日光');scene.world=world;world.use_nodes=True;bg=world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.71,.79,.93,1);bg.inputs['Strength'].default_value=.45
def area(name,loc,power,size,color):
    if ID=='zifeng':loc=tuple(v*2.5 for v in loc);power*=5;size*=2.5
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(name,d);G.COL['06_摄影棚'].objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,30 if ID=='zifeng' else 4))-o.location).to_track_quat('-Z','Y').to_euler()
area('主光',(-20,-25,38),8000,16,(1,.88,.73));area('补光',(22,-4,26),5500,20,(.72,.83,1));area('轮廓光',(5,28,32),6500,14,(1,.97,.89))
d=bpy.data.lights.new('太阳','SUN');d.energy=1.7;d.angle=.14;d.color=(1,.91,.8);o=bpy.data.objects.new('太阳',d);G.COL['06_摄影棚'].objects.link(o);o.rotation_euler=(.48,-.45,-.35)
extent={'meiling':28,'museum':43,'zhonghua':46,'fuzimiao':42,'presidential':40,'baoen':45,'jiming':38,'zifeng':100,'yuejiang':43}[ID]
def camera(name,loc,target,scale):
    d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=scale;d.clip_end=500;o=bpy.data.objects.new(name,d);G.COL['06_摄影棚'].objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
cams={'侧前方':camera('侧前方',(36,-48,39 if ID=='zhonghua' else 30),(0,0,3.5),extent),'正面':camera('正面',(0,-60,5.3),(0,0,5.3),extent*.88),'侧面':camera('侧面',(60,0,5.3),(0,0,5.3),extent*.88)}
if ID=='baoen':
    cams={'侧前方':camera('塔侧前方',(38,-52,34),(0,0,17),45),'正面':camera('塔正面',(0,-70,17),(0,0,17),45),'侧面':camera('塔侧面',(70,0,17),(0,0,17),45)}
if ID in ['jiming','yuejiang','zifeng']:
    target={'jiming':11,'yuejiang':13,'zifeng':39}[ID];distance=140 if ID=='zifeng' else 65
    cams={'侧前方':camera('建筑侧前方',(distance*.7,-distance,target+distance*.45),(0,0,target),extent),'正面':camera('建筑正面',(0,-distance,target),(0,0,target),extent),'侧面':camera('建筑侧面',(distance,0,target),(0,0,target),extent)}
scene.camera=cams['侧前方'];scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.render.resolution_x=1500;scene.render.resolution_y=1500;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.unit_settings.system='METRIC'
for f in ['build_landmark.py','geometry.py']+(['old_city_landmarks.py'] if ID in ['fuzimiao','presidential','baoen'] else ['north_landmarks.py'] if ID in ['jiming','zifeng','yuejiang'] else []):
    t=bpy.data.texts.new(f);t.write((HERE/f).read_text())
t=bpy.data.texts.new('模型说明');t.write(NAME+'：按同项目 imagegen 概念图创作，非测绘复原。01–05 为建筑，06 为摄影棚；纹理已打包。整体控制器可缩放，正面 -Y / Z-up。网页使用导出的 GLB，Y-up，正面 +Z。')
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':a.spaces.active.shading.type='MATERIAL';a.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT/(NAME+'_分组可编辑_带材质.blend')))
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();asset=bpy.context.object;asset.name=NAME+'_WEB_建筑';asset.parent=root
if ID in ['jiming','zifeng','yuejiang']:
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
color=asset.data.color_attributes.new(name='AO_Contact',type='FLOAT_COLOR',domain='CORNER');asset.data.color_attributes.active_color=color;asset.data.color_attributes.render_color_index=asset.data.color_attributes.find(color.name)
scene.cycles.samples=24;active(asset);bpy.ops.object.bake(type='AO',target='VERTEX_COLORS',use_clear=True)
values=np.empty(len(color.data)*4,dtype=np.float32);color.data.foreach_get('color',values);values=values.reshape(-1,4);values[:,:3]=.60+.40*np.clip(values[:,:3],0,1);values[:,3]=1;color.data.foreach_set('color',values.ravel())
active(asset);root.select_set(True)
glb=OUT/(NAME+'_网页版.glb')
bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_vertex_color='ACTIVE',export_all_vertex_colors=False,export_cameras=False,export_lights=False)
blob=glb.read_bytes();doc=json.loads(blob[20:20+struct.unpack_from('<I',blob,12)[0]])
actual=sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives']);assert 20000<=actual<=40000,(ID,actual)
assert all('COLOR_0' in p['attributes'] for m in doc['meshes'] for p in m['primitives']);assert all('uri' not in im for im in doc.get('images',[]))
# Multiply baked AO exactly once in Blender previews. glTF already carries COLOR_0.
for m in set(slot.material for slot in asset.material_slots):
    bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');n=m.node_tree.nodes;l=m.node_tree.links;vc=n.new('ShaderNodeVertexColor');vc.layer_name='AO_Contact';mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
    if bs.inputs['Base Color'].links:
        link=bs.inputs['Base Color'].links[0];src=link.from_socket;l.remove(link);l.new(src,mix.inputs[1])
    else:mix.inputs[1].default_value=bs.inputs['Base Color'].default_value
    l.new(vc.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],bs.inputs['Base Color'])
scene.cycles.samples=32;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(NAME+'_网页版.blend')))
bpy.context.view_layer.update()
report={'id':ID,'triangles':actual,'glb_bytes':len(blob),'glb_mib':round(len(blob)/1024**2,3),'material_count':len(doc['materials']),'embedded_images':len(doc.get('images',[])),'vertex_ao':True,'sha256':hashlib.sha256(blob).hexdigest(),'blender_dimensions':[round(v,4) for v in asset.dimensions],'scene_scale':SCALE}
if ID=='zhonghua':report.update(scene_offset=[1.8202913, 0, -3.8261449],scene_rotation_y=-0.3437929796)
if ID=='museum':report['scene_offset']=[-3.25,0,0]
if ID=='jiming':report['scene_offset']=[0,0,3.6]
if ID=='yuejiang':report['scene_offset']=[4.9,0,.65]
(OUT/'web-model-stats.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('MODEL_READY',report,flush=True)
for name in ['侧前方','正面','侧面']:
    scene.camera=cams[name];scene.render.resolution_x=1500 if name=='侧前方' else 1200;scene.render.resolution_y=1500 if name=='侧前方' else 1000;scene.render.filepath=str(OUT/(NAME+'_实模_'+name+'.png'));bpy.ops.render.render(write_still=True)
