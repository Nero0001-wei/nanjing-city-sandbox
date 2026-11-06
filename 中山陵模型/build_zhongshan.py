"""Create a fully modeled, material-assigned miniature from the approved concept.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b --python build_zhongshan.py
All geometry is original. Units are artistic meters, not a survey of the monument.
"""
import bpy, bmesh, math, random, json, sys
from pathlib import Path
from mathutils import Vector
from math import sin, cos, pi
random.seed(31)
OUT = Path(__file__).resolve().parent
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name != 'Collection': bpy.data.collections.remove(c)
def collection(name):
    c=bpy.data.collections.new(name); bpy.context.scene.collection.children.link(c); return c
COL={n:collection(n) for n in ['01_基座与叠台','02_三段台阶','03_石栏与望柱','04_祭堂墙体','05_拱门与木门','06_檐部与装饰','07_蓝瓦与屋脊','08_摄影棚']}
root=bpy.data.objects.new('中山陵_整体控制器',None);COL['01_基座与叠台'].objects.link(root)
root['说明']='无树木概念版；正面朝 -Y；Z 向上；原点为底座中心地面；并非测绘复原。'
root['参考图']='中山陵-正面-无树木.png / 中山陵-侧前方-无树木.png'
def linear(c): return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
def material(name,hexcolor,rough=.5,noise=False,coat=0):
    m=bpy.data.materials.new(name);m.diffuse_color=tuple(linear(int(hexcolor[i:i+2],16)/255) for i in (0,2,4))+(1,)
    m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear();bs=n.new('ShaderNodeBsdfPrincipled');out=n.new('ShaderNodeOutputMaterial');l.new(bs.outputs['BSDF'],out.inputs['Surface']);bs.inputs['Base Color'].default_value=m.diffuse_color
    bs.inputs['Roughness'].default_value=rough;bs.inputs['Coat Weight'].default_value=coat;bs.inputs['Coat Roughness'].default_value=.23
    if noise:
        tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=28;tex.inputs['Detail'].default_value=2
        bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.018
        l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal'])
    return m
STONE=material('米白石材 · 细哑光','EBD8B9',.71,True)
LIGHT=material('浅色石材 · 檐口与栏杆','F4E5CA',.65,True)
DARKSTONE=material('凹槽与接缝 · 暖灰','BBA88D',.83)
PAVING=material('平台铺石 · 浅米色','E5D2B4',.76,True)
BLUE=material('钴蓝琉璃瓦 · 釉面','1557CE',.29,False,.28)
BLUELIGHT=material('琉璃瓦高光 · 天蓝','246BE0',.30,False,.28)
BLUEDARK=material('瓦底与脊阴影 · 深蓝','14449B',.36,False,.22)
WOOD=material('深棕木门','493D34',.55,True)
WOODLIGHT=material('木门线脚','625345',.55)
BRONZE=material('门环 · 旧铜','A28A5F',.34);next(n for n in BRONZE.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Metallic'].default_value=.65
SHADOW=material('门洞内壁阴影','524739',.87)
BACKDROP=material('摄影棚 · 暖灰白','E9E9E6',.85)
STONEV=[STONE]+[material('石材色差_%02d'%i,c,.71,True) for i,c in enumerate(['E8D5B7','EFDEC3','E6D1B1','F0DDC0'])]
class Mesh:
    def __init__(self,name,col,mat,bevel=0,smooth=False):
        self.name=name;self.col=col;self.mats=mat if isinstance(mat,list) else [mat];self.v=[];self.f=[];self.mi=[];self.bevel=bevel;self.smooth=smooth
    def add(self,verts,faces,mi=0):
        k=len(self.v);self.v.extend(verts);self.f.extend([tuple(k+i for i in face) for face in faces]);self.mi.extend([mi]*len(faces))
    def box(self,p,d,mi=0):
        x,y,z=p;a,b,c=[q/2 for q in d]
        self.add([(x-a,y-b,z-c),(x+a,y-b,z-c),(x+a,y+b,z-c),(x-a,y+b,z-c),(x-a,y-b,z+c),(x+a,y-b,z+c),(x+a,y+b,z+c),(x-a,y+b,z+c)],[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],mi)
    def tube(self,points,r,segments=8,mi=0):
        v=[];f=[];points=[Vector(p) for p in points]
        for i,p in enumerate(points):
            tangent=(points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized();other=Vector((0,0,1))
            if abs(tangent.dot(other))>.95:other=Vector((0,1,0))
            a=tangent.cross(other).normalized();b=tangent.cross(a).normalized()
            for j in range(segments):v.append(tuple(p+r*(cos(2*pi*j/segments)*a+sin(2*pi*j/segments)*b)))
        for i in range(len(points)-1):
            for j in range(segments):f.append((i*segments+j,i*segments+(j+1)%segments,(i+1)*segments+(j+1)%segments,(i+1)*segments+j))
        f.extend([tuple(reversed(range(segments))),tuple((len(points)-1)*segments+j for j in range(segments))]);self.add(v,f,mi)
    def prism(self,profile,y0,y1,mi=0):
        # closed polygon in X/Z, extruded in Y
        n=len(profile);self.add([(x,y0,z) for x,z in profile]+[(x,y1,z) for x,z in profile],[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],mi)
    def finish(self,parent=True):
        if not self.v:return None
        me=bpy.data.meshes.new(self.name);me.from_pydata(self.v,[],self.f);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update();o=bpy.data.objects.new(self.name,me);COL[self.col].objects.link(o)
        for m in self.mats:me.materials.append(m)
        for p,i in zip(me.polygons,self.mi):p.material_index=i;p.use_smooth=self.smooth
        # UVs remain useful for replacing procedural materials with image maps.
        uv=me.uv_layers.new(name='UVMap')
        for p in me.polygons:
            ax=max(range(3),key=lambda a:abs(p.normal[a]));dims=[a for a in range(3) if a!=ax]
            for li in p.loop_indices:
                co=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(co[dims[0]]*.3,co[dims[1]]*.3)
        if self.bevel:
            mod=o.modifiers.new('边缘微倒角','BEVEL');mod.width=self.bevel;mod.segments=2
            mod=o.modifiers.new('加权法线','WEIGHTED_NORMAL');mod.keep_sharp=True;mod.weight=30
        if parent:o.parent=root
        return o

def box(name,p,d,mat=STONE,col='04_祭堂墙体',bevel=.035):
    m=Mesh(name,col,mat,bevel);m.box(p,d);return m.finish()
# --- Platforms: three raised, solid tiers with real stair meshes. ---
base=.48; rise=2.10; flight=5.70; starts=[-15.4,-7.7,0.0]; tops=[base+rise*(i+1) for i in range(3)];half=[9.8,8.8,7.8]
box('底座_22x34',(0,0,base/2),(22,34,base),PAVING,'01_基座与叠台',.06)
for i,(ys,top,hw) in enumerate(zip(starts,tops,half)):
    low=base+i*rise; y0=ys+flight
    box('第%d层_实心平台'%(i+1),(0,(y0+16.7)/2,(low+top)/2),(hw*2,16.7-y0,rise),PAVING,'01_基座与叠台',.035)
# Fine physical seams on paving, clipped around steps / next terrace footprint.
pave=Mesh('平台_铺石分缝','01_基座与叠台',DARKSTONE)
levels=[(11,-17,17,base)]+[(hw,ys+flight,16.7,z) for hw,ys,z in zip(half,starts,tops)]
for level,(hw,y0,y1,z) in enumerate(levels):
    # visible tiles only, avoid covered central stair and upper tier area
    def visible(x,y):
        if level<3:
            st=starts[level];end=st+flight
            if st-.02<=y<=end+.02 and abs(x)<3.95:return False
            if y>=end and abs(x)<half[level]+.02:return False
        if level==3 and abs(x)<5.3 and y>8.75:return False
        return True
    step=1.25
    # short segments rather than long lines through stairs
    for ix in range(-int(hw/step),int(hw/step)+1):
        x=ix*step
        for j in range(int((y1-y0)/.25)):
            ya=y0+j*.25
            if visible(x,ya+.125):pave.box((x,ya+.125,z+.002),(.009,.25,.004))
    y=y0+1.1
    while y<y1:
        for j in range(int(2*hw/.25)):
            x=-hw+j*.25+.125
            if visible(x,y):pave.box((x,y,z+.002),(.25,.009,.004))
        y+=1.25
pave.finish()
# Terrace ashlar seams, on exposed riser faces and side walls.
joints=Mesh('叠台_石材拼缝','01_基座与叠台',DARKSTONE)
for i,(ys,top,hw) in enumerate(zip(starts,tops,half)):
    low=base+i*rise;y0=ys+flight
    for k in range(1,4):
        z=low+rise*k/4
        for s in [-1,1]:
            joints.box((s*(hw+3.7)/2,y0-.005,z),(hw-3.7,.01,.012))
            joints.box((s*(hw+.005),(y0+16.7)/2,z),(.01,16.7-y0,.012))
    for k in range(4):
        z=low+rise*(k+.5)/4
        for x in [a*1.2+(.6 if k%2 else 0) for a in range(-9,10)]:
            if 3.7<abs(x)<hw:joints.box((x,y0-.005,z),(.01,.01,rise/4))
        y=y0+(.6 if k%2 else 0)
        while y<16.7:
            for s in [-1,1]:joints.box((s*(hw+.005),y,z),(.01,.01,rise/4))
            y+=1.3
joints.finish()
for i,ys in enumerate(starts):
    m=Mesh('第%d段_28级台阶'%(i+1),'02_三段台阶',LIGHT,.012)
    low=base+i*rise;n=28
    # Closed stepped cross-section, extrusion across X.
    prof=[(ys,low),(ys+flight,low),(ys+flight,low+rise)]
    for k in range(n-1,-1,-1):
        prof.extend([(ys+k*flight/n,low+(k+1)*rise/n),(ys+k*flight/n,low+k*rise/n)])
    count=len(prof);v=[(-3.45,y,z) for y,z in prof]+[(3.45,y,z) for y,z in prof]
    f=[tuple(reversed(range(count))),tuple(range(count,2*count))]+[(j,(j+1)%count,(j+1)%count+count,j+count) for j in range(count)]
    m.add(v,f);m.finish()
    nosing=Mesh('第%d段_踏步前缘'%(i+1),'02_三段台阶',LIGHT,.008)
    for k in range(1,n+1):nosing.box((0,ys+(k-1)*flight/n+.02,low+k*rise/n),(6.90,.065,.028))
    nosing.finish()
# --- Railings. Capped pillars, inset panel borders, continuous sloped coping. ---
posts=Mesh('望柱_柱身与层叠柱帽','03_石栏与望柱',LIGHT,.025)
insets=Mesh('望柱_浅浮雕与凹框','03_石栏与望柱',STONE,.012)
rails=Mesh('石栏_栏板扶手与立柱','03_石栏与望柱',LIGHT,.025)
slopes=Mesh('台阶_斜栏板','03_石栏与望柱',STONE,.025)
postkeys=set()
def post(x,y,z):
    key=(round(x,2),round(y,2),round(z,2))
    if key in postkeys:return
    postkeys.add(key)
    for dz,w,h in [(.07,.74,.14),(.20,.62,.13),(.65,.49,.81),(1.10,.64,.15),(1.20,.72,.10),(1.30,.48,.13)]:posts.box((x,y,z+dz),(w,w,h))
    # four small picture-frame panels, visible from all sides
    for s in [-1,1]:
        for t in [-1,1]:insets.box((x+t*.145,y+s*.253,z+.66),(.025,.015,.42))
        for dz in [.45,.87]:insets.box((x,y+s*.253,z+dz),(.31,.015,.025))
        for t in [-1,1]:insets.box((x+s*.253,y+t*.145,z+.66),(.015,.025,.42))
        for dz in [.45,.87]:insets.box((x+s*.253,y,z+dz),(.015,.31,.025))
    # stylized geometric relief, kept understated
    insets.tube([(x-.09,y-.265,z+.63),(x,y-.265,z+.75),(x+.09,y-.265,z+.63),(x,y-.265,z+.54),(x-.09,y-.265,z+.63)],.012,6)
def rail(a,b,z):
    a,b=Vector((a[0],a[1],z)),Vector((b[0],b[1],z));d=b-a;L=d.length;n=max(2,round(L/.75));dr=d/L
    mid=(a+b)/2
    if abs(d.x)>.01:
        rails.box((mid.x,mid.y,z+.16),(L,.30,.24));rails.box((mid.x,mid.y,z+.87),(L,.32,.17))
    else:
        rails.box((mid.x,mid.y,z+.16),(.30,L,.24));rails.box((mid.x,mid.y,z+.87),(.32,L,.17))
    for j in range(n+1):
        p=a+d*j/n;rails.box((p.x,p.y,z+.51),(.16,.16,.55))
    # carved solid central panels interspersed with open balusters
    for j in range(n):
        if j%3==1:
            p=a+d*(j+.5)/n
            dims=(L/n*.82,.12,.37) if abs(d.x)>.01 else (.12,L/n*.82,.37)
            rails.box((p.x,p.y,z+.51),dims)
for i,ys in enumerate(starts):
    low=base+i*rise;high=low+rise;hw=half[i];end=ys+flight
    for s in [-1,1]:
        x=s*3.7;post(x,ys,low);post(x,end,high)
        # closed slanted parapet prism, with top rising alongside staircase
        ya,yb=ys+.22,end-.22;za=low+.25;zb=high+.25
        verts=[(x-.20,ya,low),(x+.20,ya,low),(x+.20,yb,high),(x-.20,yb,high),(x-.20,ya,za+.60),(x+.20,ya,za+.60),(x+.20,yb,zb+.60),(x-.20,yb,zb+.60)]
        faces=[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)];slopes.add(verts,faces)
        # rectangular sloping cap and base strips
        for dz,w,h in [(.88,.55,.13),(.13,.44,.11)]:
            verts=[]
            for y,z in [(ya,low+dz),(yb,high+dz)]:
                verts.extend([(x-w/2,y,z-h/2),(x+w/2,y,z-h/2),(x+w/2,y,z+h/2),(x-w/2,y,z+h/2)])
            rails.add(verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
        # wing railing on tier front (outside staircase)
        wy=end+.14;post(s*(hw-.30),wy,high);rail((s*3.7,wy),(s*(hw-.30),wy),high)
        if i==2:
            # top terrace sides/back complete the object when rotated
            post(s*(hw-.3),16.25,high);rail((s*(hw-.3),wy),(s*(hw-.3),16.25),high)
    if i==2:rail((-hw+.3,16.25),(hw-.3,16.25),high)
posts.finish();insets.finish();rails.finish();slopes.finish()
# --- Memorial hall, real recessed arched entrances and masonry. ---
Z=tops[-1];F=8.35;B=15.2;CY=(F+B)/2;W=9.9; H=4.25
box('祭堂_基脚',(0,CY,Z+.09),(W+.30,B-F+.25,.18),LIGHT)
# Masonry side and rear walls with fine joints and restrained color variation.
wall=Mesh('祭堂_侧后墙分块石砌','04_祭堂墙体',STONEV,.009)
rows=8;rh=3.65/rows
for k in range(rows):
    zz=Z+(k+.5)*rh
    for sx in [-1,1]:
        yy=F+.51
        while yy<B-.01:
            le=min(1.1 if yy>F else (.55 if k%2 else 1.1),B-yy)
            wall.box((sx*(W/2-.22),yy+le/2,zz),(.44,le-.012,rh-.012),random.randrange(5));yy+=le
    xx=-W/2+.44
    while xx<W/2-.44-.01:
        le=min(1.1,W/2-.44-xx);wall.box((xx+le/2,B-.22,zz),(le-.012,.44,rh-.012),random.randrange(5));xx+=le
wall.finish()
# Interior backing and floor
box('祭堂_内部地面',(0,CY,Z+.12),(W-.88,B-F-.6,.16),STONE)
box('祭堂_内部顶板',(0,CY,Z+H-.14),(W-.5,B-F-.3,.22),STONE)
# Entire front wall constructed around arched voids, no painted fake openings.
archcenters=[-2.0,0,2.0];R=.71;spring=Z+1.66;fronttop=Z+3.63
fac=Mesh('立面_三孔拱门实体墙','04_祭堂墙体',STONE,.012)
limits=[-W/2]+[v for c in archcenters for v in (c-R,c+R)]+[W/2]
for a,b in zip(limits[::2],limits[1::2]):fac.box(((a+b)/2,F+.25,(Z+fronttop)/2),(b-a,.5,fronttop-Z))
for cx in archcenters:
    # wedge strip over each curved opening
    for j in range(32):
        x1=cx-R+2*R*j/32;x2=cx-R+2*R*(j+1)/32
        z1=spring+math.sqrt(max(0,R*R-(x1-cx)**2));z2=spring+math.sqrt(max(0,R*R-(x2-cx)**2))
        fac.prism([(x1,z1),(x2,z2),(x2,fronttop),(x1,fronttop)],F,F+.5)
fac.finish()
# upper frieze / wall attic
box('祭堂_上层额枋',(0,CY,Z+3.95),(W,B-F,.6),STONE)
# Massive projecting flank piers + cornices
for sx in [-1,1]:
    x=sx*3.95
    box('立面_端部方塔柱',(x,F-.05,Z+1.98),(1.75,.9,3.96),STONE)
    for z,w,d,h in [(Z+.13,1.95,1.08,.26),(Z+3.9,1.92,1.06,.16),(Z+4.08,2.12,1.18,.18),(Z+4.22,1.64,.90,.14)]:box('方柱_基座及冠部',(x,F-.08,z),(w,d,h),LIGHT,bevel=.02)
    # ashlar on pier front
    for k in range(1,8):box('方柱_横缝',(x,F-.506,Z+k*.47),(1.72,.007,.008),DARKSTONE,bevel=0)
    for k in range(8):
        xx=x+(.4 if k%2 else -.3);box('方柱_竖缝',(xx,F-.507,Z+(k+.5)*.47),(.008,.007,.46),DARKSTONE,bevel=0)
# pilasters between doors; arch rings and recessed dark double doors
trim=Mesh('拱门_石拱圈与门套','05_拱门与木门',LIGHT,.016)
doors=Mesh('木门_拱形门扇','05_拱门与木门',WOOD,.009)
detail=Mesh('木门_框线与分格','05_拱门与木门',WOODLIGHT,.008)
hardware=Mesh('木门_铜门环','05_拱门与木门',BRONZE,0,True)
for cx in archcenters:
    for s in [-1,1]:trim.box((cx+s*(R+.10),F-.11,Z+.83),(.20,.23,1.66))
    for j in range(17):
        a=j*pi/17+.008;b=(j+1)*pi/17-.008
        profile=[(cx+r*cos(t),spring+r*sin(t)) for r,t in [(R,a),(R,b),(R+.21,b),(R+.21,a)]];trim.prism(profile,F-.24,F+.15)
    profile=[(cx-R,Z+.04),(cx+R,Z+.04),(cx+R,spring)]+[(cx+R*cos(j*pi/32),spring+R*sin(j*pi/32)) for j in range(1,33)]
    doors.prism(profile,F+.19,F+.30)
    # recessed reveal along jambs
    for s in [-1,1]:box('门洞_内返边',(cx+s*(R-.015),F+.09,Z+.80),(.035,.28,1.60),SHADOW,'05_拱门与木门',0)
    detail.box((cx,F+.175,Z+1.04),(.036,.035,2.02))
    for off in [-.38,.38]:
        for za,hh in [(Z+.43,.59),(Z+1.14,.60)]:
            for side in [-1,1]:detail.box((cx+off+side*.245,F+.16,za),(.038,.05,hh))
            for side in [-1,1]:detail.box((cx+off,F+.16,za+side*hh/2),(.51,.05,.036))
        # Ring plane X/Z
        x=cx+(.12 if off>0 else -.12);z=Z+.93
        hardware.tube([(x+.055*cos(t*2*pi/20),F+.11,z+.07*sin(t*2*pi/20)) for t in range(21)],.012,8)
    detail.tube([(cx+(R-.08)*cos(j*pi/32),F+.15,spring+(R-.08)*sin(j*pi/32)) for j in range(33)],.026,8)
    detail.box((cx,F+.15,spring),((R-.06)*2,.05,.05))
    for xoff in [-.4,-.2,0,.2,.4]:
        zz=math.sqrt(max(0,(R-.10)**2-xoff*xoff));detail.box((cx+xoff,F+.17,spring+zz/2),(.022,.035,zz))
trim.finish();doors.finish();detail.finish();hardware.finish()
columns=Mesh('立面_门间石柱','05_拱门与木门',LIGHT,.012)
for x in [-3.0,-1.,1.,3.0]:
    columns.tube([(x,F-.17,Z+.28),(x,F-.17,Z+2.77)],.135,16)
    for z,w,h in [(Z+.14,.40,.24),(Z+.30,.31,.12),(Z+2.79,.35,.14),(Z+2.92,.44,.13)]:columns.box((x,F-.17,z),(w,.45,h))
columns.finish()
# lintels and horizontal strips
for z,dx,dy,h in [(Z+3.10,6.18,.36,.16),(Z+3.25,6.40,.49,.16),(Z+3.43,9.9,.38,.12),(Z+4.34,10.35,7.25,.19),(Z+4.53,10.7,7.58,.18)]:
    if dy<1:box('立面_横向石线脚',(0,F-.18,z),(dx,dy,h),LIGHT,'06_檐部与装饰',.02)
    else:box('屋檐_叠涩石枋',(0,CY,z),(dx,dy,h),LIGHT,'06_檐部与装饰',.025)
# Simple framed side wall panels
sideframe=Mesh('侧墙_浅浮雕框线','06_檐部与装饰',LIGHT,.012)
for s in [-1,1]:
    x=s*(W/2+.015)
    for cy in [10.4,13.45]:
        for y in [cy-1.16,cy+1.16]:sideframe.box((x,y,Z+2.02),(.055,.10,2.18))
        for z in [Z+.93,Z+3.11]:sideframe.box((x,cy,z),(.055,2.42,.10))
sideframe.finish()
# decorative dentils + bracket blocks around the eave
brackets=Mesh('檐下_斗拱与齿饰','06_檐部与装饰',STONE,.016)
for side in [-1,1]:
    for j in range(25):
        x=-4.8+j*.4;y=CY+side*3.63
        brackets.box((x,y,Z+4.64),(.22,.36,.23));brackets.box((x,y+side*.08,Z+4.79),(.31,.48,.10))
    for j in range(16):
        y=F+.15+j*.42;x=side*5.08
        brackets.box((x,y,Z+4.64),(.36,.22,.23));brackets.box((x+side*.08,y,Z+4.79),(.48,.31,.10))
brackets.finish()
# Framed unlettered plaque matches the concept without invented writing.
for p,d in [((0,F-.10,Z+4.00),(.64,.16,.64)),((0,F-.20,Z+4.00),(.45,.07,.45))]:box('额枋_方形石饰',p,d,LIGHT,'06_檐部与装饰',.012)
# --- Xieshan-style blue tiled roof: curved central slopes, hip skirt, gable faces. ---
E=Z+5.35;Y=CY;upper_h=2.05;low_drop=.63
surface=Mesh('屋顶_连续曲面瓦底','07_蓝瓦与屋脊',BLUEDARK,0,True)
tiles=Mesh('屋顶_纵向筒瓦','07_蓝瓦与屋脊',[BLUE,BLUELIGHT],0,True)
seams=Mesh('屋顶_瓦片搭接','07_蓝瓦与屋脊',BLUE,0,True)
ridges=Mesh('屋顶_正脊与垂脊','07_蓝瓦与屋脊',BLUE,0,True)
def frontpoint(u,t,s):
    if t<=.68:
        q=t/.68;hw=4.60;dy=2.85*q;z=E+upper_h*(1-q)**1.55
    else:
        q=(t-.68)/.32;hw=4.60+1.35*q;dy=2.85+1.45*q;z=E-low_drop*q+.25*q**4+.20*abs(u)**8*q**3
    return (u*hw,Y+s*dy,z)
def sidepoint(u,t,s):
    return (s*(4.60+1.35*t),Y+u*(2.85+1.45*t),E-low_drop*t+.25*t**4+.20*abs(u)**8*t**3)
def sheet(fn,nu,nv):
    v=[fn(-1+2*i/nu,j/nv) for j in range(nv+1) for i in range(nu+1)];f=[]
    for j in range(nv):
        for i in range(nu):a=j*(nu+1)+i;f.append((a,a+1,a+nu+2,a+nu+1))
    surface.add(v,f)
for s in [-1,1]:
    fn=lambda u,t:frontpoint(u,t,s);sheet(fn,56,42)
    for i in range(59):
        u=-1+2*i/58;pts=[Vector(fn(u,j/64))+Vector((0,0,.045)) for j in range(65)]
        tiles.tube(pts,.066,8,1 if i%7==0 else 0)
        # Narrow raised collars across each tube describe overlapping tile units
        for j in range(1,26):
            t=j/26;p=Vector(fn(u,t))+Vector((0,0,.045));tan=(Vector(fn(u,min(1,t+.003)))-Vector(fn(u,max(0,t-.003)))).normalized()
            a=Vector((1,0,0));b=tan.cross(a).normalized()
            seams.tube([p+.071*(cos(k*pi/8)*a+sin(k*pi/8)*b) for k in range(9)],.007,5)
    fn=lambda u,t:sidepoint(u,t,s);sheet(fn,38,18)
    for i in range(39):
        u=-1+2*i/38;pts=[Vector(fn(u,j/24))+Vector((0,0,.05)) for j in range(25)];tiles.tube(pts,.064,8,1 if i%7==0 else 0)
    # gable inset fills the triangle under the upper roof
    profile=[(Y-2.85,E),(Y+2.85,E)]+[(Y+2.85*(1-j/32),E+upper_h*(j/32)**1.55) for j in range(1,33)]+[(Y-2.85*j/32,E+upper_h*(1-j/32)**1.55) for j in range(1,33)]
    g=Mesh('山墙_三角石饰_'+str(s),'06_檐部与装饰',STONE)
    n=len(profile);xx=s*4.57;v=[(xx-.06,y,z) for y,z in profile]+[(xx+.06,y,z) for y,z in profile];g.add(v,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]);g.finish()
    # main gable bargeboards
    for sy in [-1,1]:ridges.tube([(s*4.63,Y+sy*2.85*t,E+upper_h*(1-t)**1.55+.07) for t in [j/32 for j in range(33)]],.11,10)
    # hip ridges curl upward at all four corners
    for sy in [-1,1]:
        pts=[(s*(4.6+1.35*t),Y+sy*(2.85+1.45*t),E-low_drop*t+.45*t**4+.08) for t in [j/24 for j in range(25)]]
        pts.extend([(s*6.1,Y+sy*4.45,E+.02),(s*6.14,Y+sy*4.50,E+.23)])
        ridges.tube(pts,.115,10)
    # eave trim, two stacked blue mouldings
    for dz,rr in [(-.06,.10),(-.18,.075)]:
        ridges.tube([Vector(frontpoint(-1+2*i/70,1,s))+Vector((0,0,dz)) for i in range(71)],rr,10)
        ridges.tube([Vector(sidepoint(-1+2*i/50,1,s))+Vector((0,0,dz)) for i in range(51)],rr,10)
# straight raised main ridge, with scroll finials on both ends
ridges.box((0,Y,E+upper_h+.15),(9.35,.28,.30))
ridges.tube([(-4.74,Y,E+upper_h+.33),(4.74,Y,E+upper_h+.33)],.10,12)
for s in [-1,1]:
    x=s*4.65;z=E+upper_h
    ridges.box((x,Y,z+.36),(.25,.40,.72))
    # elegant inward curling silhouette in the X/Z plane
    pts=[]
    for j in range(37):
        t=j/36;a=-pi/2+t*pi*1.65;r=.36*(1-.60*t)
        pts.append((x+s*(.07+r*cos(a)),Y,z+.73+r*sin(a)))
    ridges.tube(pts,.10,12)
    # embossed small disk in side face
    ridges.tube([(x+s*.07+.16*cos(j*2*pi/24),Y-.16,z+.58+.16*sin(j*2*pi/24)) for j in range(25)],.035,8)
roof_object=surface.finish();sol=roof_object.modifiers.new('瓦底厚度','SOLIDIFY');sol.thickness=.055;sol.offset=-1;tiles.finish();seams.finish();ridges.finish()
# A root custom property records scale and useful presentation dimensions.
root['建模尺寸']='底座 22 × 34 m；三段各 28 级台阶；示意尺寸，可整体缩放'
root['材质']='钴蓝琉璃釉面 / 米白石材 / 深棕木门 / 铜门环；程序材质内置，无外部贴图依赖'
# --- Studio, cameras and lighting. ---
box('摄影棚地面',(0,0,-.13),(200,200,.20),BACKDROP,'08_摄影棚',.02).parent=None
world=bpy.data.worlds.new('柔和日光环境');bpy.context.scene.world=world;world.use_nodes=True
world.node_tree.nodes.clear();wn=world.node_tree.nodes.new('ShaderNodeBackground');wo=world.node_tree.nodes.new('ShaderNodeOutputWorld');world.node_tree.links.new(wn.outputs[0],wo.inputs['Surface']);wn.inputs['Color'].default_value=(.71,.79,.93,1);wn.inputs['Strength'].default_value=.45
def area(name,loc,power,size,color):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(name,d);COL['08_摄影棚'].objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,2,4))-o.location).to_track_quat('-Z','Y').to_euler()
area('主光_暖日光',(-15,-16,32),6500,14,(1,.88,.73));area('补光_天空',(18,-4,22),4300,18,(.72,.83,1));area('轮廓光',(5,23,28),5500,12,(1,.97,.89))
sun=bpy.data.lights.new('日光','SUN');sun.energy=1.7;sun.angle=.14;sun.color=(1,.91,.80);so=bpy.data.objects.new('日光',sun);COL['08_摄影棚'].objects.link(so);so.rotation_euler=(.48,-.45,-.35)
def camera(name,loc,target,scale):
    d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=scale;d.lens=50;d.clip_end=500
    o=bpy.data.objects.new(name,d);COL['08_摄影棚'].objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
cams={
 '侧前方':camera('相机_侧前方',(33,-47,35),(0,0,4.6),42),
 '正面':camera('相机_正面',(0,-60,27),(0,0,6.3),31),
 '右侧正交':camera('相机_右侧正交',(55,0,7.5),(0,0,7.5),38),
 '建筑细节':camera('相机_建筑细节',(22,-16,19),(0,11.6,10),20)
}
scene=bpy.context.scene;scene.camera=cams['侧前方'];scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True
scene.cycles.max_bounces=6;scene.render.resolution_x=1500;scene.render.resolution_y=1500;scene.render.resolution_percentage=100
scene.world.color=(.7,.7,.7);scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
# Select asset root; show materials in interactive viewport and frame model.
bpy.ops.object.select_all(action='DESELECT');root.select_set(True);bpy.context.view_layer.objects.active=root
for screen in bpy.data.screens:
    for ar in screen.areas:
        if ar.type=='VIEW_3D':
            ar.spaces.active.clip_end=1000;ar.spaces.active.shading.type='MATERIAL';ar.spaces.active.region_3d.view_perspective='CAMERA'
# Hide studio objects only in viewport, not in final renders; keep cameras usable.
for o in COL['08_摄影棚'].objects:
    if o.type=='LIGHT' or o.name=='摄影棚地面':o.hide_set(True)
# Embed editable generation source and project note inside the .blend.
t=bpy.data.texts.new('README_使用说明');t.write('中山陵 · 无绿化概念模型\n按已确认效果图制作，并非实测建筑复原。\n主入口朝 -Y；底座中心地面为原点。选择中山陵_整体控制器可整体变换。\n01—07 集合为模型，08 为摄影棚；正面、侧前方、右侧正交、细节相机已设置。\n石材微表面使用内置 Noise/Bump 节点；琉璃瓦、门及铜环已分配材质，无需下载纹理。\n台阶、墙体、石栏、瓦顶分组保留；细节采用合并网格减少对象数，编辑模式可按松散部分拆分。\nGLB 为便于场景导入的附加格式；程序纹理的微表面细节以 Blender 文件为准。\n')
t=bpy.data.texts.new('build_zhongshan.py');t.write(Path(__file__).read_text())
bpy.context.view_layer.update()
# Asset-only GLB with material colors/roughness; no cameras, lights or floor.
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
    if o.parent==root or o==root:o.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(OUT/'中山陵_无树木_带材质.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_cameras=False,export_lights=False,export_extras=True)
bpy.ops.object.select_all(action='DESELECT');root.select_set(True);bpy.context.view_layer.objects.active=root
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'中山陵_无树木_带材质.blend'))
stats={'blender':bpy.app.version_string,'mesh_objects':sum(o.type=='MESH' and o.parent==root for o in bpy.data.objects),'vertices':sum(len(o.data.vertices) for o in bpy.data.objects if o.type=='MESH' and o.parent==root),'polygons':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH' and o.parent==root),'materials':len(bpy.data.materials),'dimensions':[22,34,round(max((o.matrix_world@Vector(c)).z for o in bpy.data.objects if o.type=='MESH' and o.parent==root for c in o.bound_box),3)]}
(OUT/'model_stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2));print('MODEL_READY',stats,flush=True)
# Render preview first, then two useful modeling views.
for label in ['侧前方','正面','右侧正交','建筑细节']:
    scene.camera=cams[label]
    bpy.data.objects['摄影棚地面'].hide_render=(label=='右侧正交')
    scene.render.resolution_x=1500;scene.render.resolution_y=1500 if label not in ['右侧正交','建筑细节'] else (850 if label=='右侧正交' else 1100)
    scene.render.filepath=str(OUT/('中山陵_实模渲染_'+label+'.png'));bpy.ops.render.render(write_still=True);print('RENDERED',label,flush=True)
print('COMPLETE',flush=True)
