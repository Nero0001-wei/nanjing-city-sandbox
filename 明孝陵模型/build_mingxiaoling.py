"""Ming Xiaoling Fangcheng Minglou, tree-free miniature, 20–40k exported triangles.
Blender -b --factory-startup --python build_mingxiaoling.py
Artistic interpretation of the imagegen sheet, not a surveyed reconstruction.
"""
import bpy, math, json, struct, hashlib, sys
from pathlib import Path
from mathutils import Vector
from math import sin, cos, pi
import numpy as np
HERE=Path(__file__).resolve().parent
OUT=HERE/'web'; OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(HERE)); import geometry as G
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name!='Collection':bpy.data.collections.remove(c)
COL={}
for name in ['01_方城与拱券','02_明楼红墙','03_台阶与石栏','04_双层琉璃瓦','05_檐下彩绘','06_门窗','07_摄影棚']:
    c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c);COL[name]=c
root=bpy.data.objects.new('明孝陵_整体控制器',None);COL['01_方城与拱券'].objects.link(root)
root['说明']='方城明楼微缩概念模型；无树木；Z-up / 正面 -Y；非测绘复原。'
root['预算']='导出 GLB 20,000–40,000 三角面；保留材质和顶点 AO'
root['参考']='../../明孝陵效果图/明孝陵-方城明楼-三视图.png'
G.COL=COL;G.root=root;Mesh=G.Mesh;material=G.material
STONE=material('象牙石栏与拱券','E6D6BA',.73)
YELLOW=material('金黄琉璃筒瓦','D89A36',.32,coat=.23)
TILEBASE=material('琉璃瓦底色','AC762B',.42,coat=.12)
WOOD=material('深棕门扇','42362C',.74)
WOODTRIM=material('木门框线','79614B',.62)
TEAL=material('檐下青绿木构','304D49',.64)
GOLD=material('彩绘金线','BD9B59',.55)
RED=material('山墙朱红','A64E38',.78)
BACK=material('摄影棚暖灰','E9E9E6',.85)

def box(name,p,d,mat=STONE,col='01_方城与拱券',bevel=0):
    m=Mesh(name,col,mat);m.box(p,d);o=m.finish()
    if bevel:
        mod=o.modifiers.new('单段轮廓倒角','BEVEL');mod.width=bevel;mod.segments=1
        n=o.modifiers.new('加权法线','WEIGHTED_NORMAL');n.keep_sharp=True
    return o

def texture_material(name,filename,kind):
    width=1024;height=256 if kind=='frieze' else 1024
    yy,xx=np.mgrid[0:height,0:width].astype(np.float32);u=xx/width;v=yy/height
    if kind=='frieze':
        x=u*4%1;y=v
        rgb=np.full((height,width,3),[.21,.34,.31],dtype=np.float32)
        border=(y<.08)|(y>.92)|((x<.025)|(x>.975))
        panel=(x>.08)&(x<.92)&(y>.19)&(y<.81)
        rgb[panel]=[.25,.40,.40];rgb[border]=[.73,.57,.29]
        diamond=abs(x-.5)/.32+abs(y-.5)/.28
        motif=(abs(diamond-1)<.045)|(abs(np.sqrt(((x-.5)/.17)**2+((y-.5)/.21)**2)-1)<.09)
        rgb[motif]=[.81,.65,.36]
    else:
        nx,ny=(3,5) if kind=='stone' else (4,7) if kind=='red' else (4,4)
        row=np.floor(v*ny);x=u*nx+(row%2)*(.5 if kind!='paving' else 0);y=v*ny
        edge=np.minimum(np.minimum(x%1,1-x%1),np.minimum(y%1,1-y%1))
        seam=np.clip((.014-edge)/.009,0,1)
        variation=.028*np.sin(np.floor(x)*23.1+row*31.7)
        col=np.array([.77,.735,.65] if kind=='stone' else [.65,.29,.20] if kind=='red' else [.87,.81,.70])
        rgb=np.clip(col*(1-.21*seam[...,None]+variation[...,None]),0,1).astype(np.float32)
    px=np.ones((height,width,4),np.float32);px[:,:,:3]=rgb
    im=bpy.data.images.new(name,width=width,height=height,alpha=False);im.colorspace_settings.name='sRGB';im.pixels.foreach_set(px.ravel());im.filepath_raw=str(OUT/filename);im.file_format='PNG';im.save();im.pack()
    mat=material(name,'FFFFFF',.76);n=mat.node_tree.nodes;l=mat.node_tree.links;bs=next(n for n in n if n.type=='BSDF_PRINCIPLED');tex=n.new('ShaderNodeTexImage');tex.image=im;tex.extension='REPEAT';l.new(tex.outputs['Color'],bs.inputs['Base Color'])
    return mat

MASONRY=texture_material('方城青灰石砌','stone_1024.png','stone')
BRICK=texture_material('明楼朱红砖墙','redbrick_1024.png','red')
PAVING=texture_material('浅色铺石','paving_1024.png','paving')
PAINT=texture_material('青绿金线彩绘','frieze_1024.png','frieze')

# Fortress block with an actual open arched tunnel. No box or false black door fills it.
box('整块紧凑铺地',(0,-.4,.16),(26,20,.32),PAVING,bevel=.04)
arch=Mesh('方城_通透券洞','01_方城与拱券',MASONRY)
r=1.65;spring=3.25;bottom=.82;top=6.65;hw=12;front=-6.45;rear=6.45
for s in [-1,1]:arch.box((s*(hw+r)/2,0,(bottom+top)/2),(hw-r,12.9,top-bottom))
for j in range(24):
    x1=-r+2*r*j/24;x2=-r+2*r*(j+1)/24
    z1=spring+math.sqrt(max(0,r*r-x1*x1));z2=spring+math.sqrt(max(0,r*r-x2*x2))
    arch.prism([(x1,z1),(x2,z2),(x2,top),(x1,top)],front,rear)
arch.finish()
# Plinths are split at the opening, so its entry remains clear all the way to ground.
for z,h,dx,dy in [(.47,.30,24.55,13.45),(.73,.22,24.28,13.18)]:
    for s in [-1,1]:box('方城_须弥座侧翼',(s*(dx/2+r)/2,0,z),(dx/2-r,dy,h),STONE)
for z,w,d,h in [(6.61,24.22,13.12,.20),(6.81,24.62,13.48,.20),(6.96,24.28,13.22,.12)]:box('方城_挑檐石线脚',(0,0,z),(w,d,h),STONE,bevel=.018)
box('方城_顶部铺石',(0,0,7.05),(24.05,13,.10),PAVING)

def arch_ring(cx,y,z,r,straight,width,depth,segments=20):
    m=Mesh('石拱圈','01_方城与拱券',STONE)
    for s in [-1,1]:m.box((cx+s*(r+width/2),y,z+straight/2),(width,depth,straight))
    for j in range(segments):
        a=j*pi/segments+.004;b=(j+1)*pi/segments-.004
        m.prism([(cx+rr*cos(t),z+straight+rr*sin(t)) for rr,t in [(r,a),(r,b),(r+width,b),(r+width,a)]],y-depth/2,y+depth/2)
    return m.finish()
for y in [front-.07,rear+.07]:arch_ring(0,y,bottom,r,spring-bottom,.35,.30,22)

def stair(name,x,y,width,length,z0,z1,n,axis='y'):
    m=Mesh(name,'03_台阶与石栏',STONE)
    for j in range(n):
        t=(j+.5)/n;h=(z1-z0)*(j+1)/n
        p=(x,y+length*t,z0+h/2);d=(width,length/n+.004,h)
        if axis=='x':p=(x+length*t,y,z0+h/2);d=(abs(length)/n+.004,width,h)
        m.box(p,d)
    return m.finish()
stair('入口_五级台阶',0,-9.0,5.4,2.55,.32,.82,5)
stair('券洞_内部缓升台阶',0,-6.4,3.22,12.8,.82,1.50,12)
# Rear stair rises laterally to the terrace and leaves the rear tunnel exit open.
stair('后部_登城石阶_右',1.8,7.45,1.8,9.5,1.50,7.10,28,'x')
stair('后部_登城石阶_左',-1.8,7.45,1.8,-9.5,1.50,7.10,28,'x')
for s in [-1,1]:box('后部_登城阶梯基座',(s*6.55,7.45,.91),(9.5,1.8,1.18),MASONRY)
box('后部_券洞出口踏台',(0,7.3,.91),(3.6,2.0,1.18),PAVING)

# Open balustrades with capped stone posts, no densely tessellated ornament.
posts=Mesh('石栏_望柱','03_台阶与石栏',STONE);rails=Mesh('石栏_扶手与栏板','03_台阶与石栏',STONE)
seen=set()
def post(x,y,z):
    k=(round(x,2),round(y,2),round(z,2))
    if k in seen:return
    seen.add(k)
    for dz,w,h in [(.08,.48,.16),(.51,.31,.75),(.93,.46,.14),(1.04,.52,.08),(1.10,.34,.08)]:posts.box((x,y,z+dz),(w,w,h))
def rail(a,b,z1,z2=None):
    z2=z1 if z2 is None else z2
    va=Vector((a[0],a[1],z1));vb=Vector((b[0],b[1],z2));d=vb-va;length=d.length
    xaxis=abs(d.x)>abs(d.y)
    for off,w,h in [(.16,.22,.20),(.82,.26,.14)]:
        vv=[]
        for p in [va,vb]:
            dx,dy=(0,w/2) if xaxis else (w/2,0)
            vv += [(p.x-dx,p.y-dy,p.z+off-h/2),(p.x+dx,p.y+dy,p.z+off-h/2),(p.x+dx,p.y+dy,p.z+off+h/2),(p.x-dx,p.y-dy,p.z+off+h/2)]
        rails.add(vv,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    n=max(1,round(length/.68))
    for j in range(n+1):
        p=va+d*j/n;rails.box((p.x,p.y,p.z+.49),(.13,.13,.60))
    for j in range(n):
        if j%3==1:
            p=va+d*(j+.5)/n;rails.box((p.x,p.y,p.z+.47),(.47,.13,.32) if xaxis else (.13,.47,.32))
def run(a,b,z,segments):
    for j in range(segments+1):post(a[0]+(b[0]-a[0])*j/segments,a[1]+(b[1]-a[1])*j/segments,z)
    rail(a,b,z)
run((-11.72,-6.14),(11.72,-6.14),7.10,8)
for s in [-1,1]:
    run((s*11.72,-6.14),(s*11.72,6.14),7.10,4)
run((-10.5,6.14),(10.5,6.14),7.10,7)
for s in [-1,1]:
    a=(s*1.8,8.38);b=(s*11.3,8.38)
    for j in range(5):post(a[0]+(b[0]-a[0])*j/4,8.38,1.50+5.6*j/4)
    rail(a,b,1.50,7.10)
    for yy,zz in [(-9.0,.32),(-6.45,.82)]:post(s*2.85,yy,zz)
    rail((s*2.85,-9),(s*2.85,-6.45),.32,.82)
posts.finish();rails.finish()

# Red Minglou walls: three recessed arch doors on front and back, intact side walls.
Z=7.18;F=-3.85;B=3.85;W=15.2;H=3.25
box('明楼_石基脚',(0,0,Z),(W+.40,8.1,.20),STONE,bevel=.025)
walls=Mesh('明楼_朱红墙体','02_明楼红墙',BRICK)
for s in [-1,1]:walls.box((s*(W/2-.24),0,Z+H/2),(.48,B-F,H))
centers=[-3.05,0,3.05];radius=.85;spring2=Z+1.45
for y in [F,B-.4]:
    edges=[-W/2]+[q for cx in centers for q in [cx-radius,cx+radius]]+[W/2]
    for j in range(0,len(edges)-1,2):walls.box(((edges[j]+edges[j+1])/2,y+.2,Z+H/2),(edges[j+1]-edges[j],.40,H))
    for cx in centers:
        for j in range(14):
            x1=cx-radius+2*radius*j/14;x2=cx-radius+2*radius*(j+1)/14
            z1=spring2+math.sqrt(max(0,radius**2-(x1-cx)**2));z2=spring2+math.sqrt(max(0,radius**2-(x2-cx)**2))
            walls.prism([(x1,z1),(x2,z2),(x2,Z+H),(x1,Z+H)],y,y+.4)
walls.finish()
doors=Mesh('明楼_拱形木门','06_门窗',WOOD);details=Mesh('明楼_门扇分格','06_门窗',WOODTRIM)
for sy in [-1,1]:
    face=sy*3.90;yd=sy*3.61
    for cx in centers:
        arch_ring(cx,face,Z,radius,1.45,.19,.22,14)
        profile=[(cx-radius,Z),(cx+radius,Z),(cx+radius,spring2)]+[(cx+radius*cos(j*pi/16),spring2+radius*sin(j*pi/16)) for j in range(1,17)]
        doors.prism(profile,yd-.055,yd+.055)
        for x in [cx-.62,cx-.31,cx,cx+.31,cx+.62]:
            h=1.45+math.sqrt(max(0,.79**2-(x-cx)**2));details.box((x,yd+sy*.07,Z+h/2),(.035,.035,h))
        for x in [cx-.4,cx+.4]:
            for z in [Z+.28,Z+.90,Z+1.38]:details.box((x,yd+sy*.085,z),(.67,.04,.055))
doors.finish();details.finish()
for sx in [-1,1]:
    for sy in [-1,1]:
        box('明楼_角柱',(sx*7.40,sy*3.70,Z+1.6),(.45,.45,3.2),STONE, '02_明楼红墙')
        box('明楼_柱脚',(sx*7.40,sy*3.70,Z+.15),(.60,.60,.30),STONE,'02_明楼红墙')

# Painted friezes use one repeating embedded map; brackets remain actual geometry.
brackets=Mesh('檐下_简化斗拱','05_檐下彩绘',TEAL)
def frieze(w,d,z,h):
    for sy in [-1,1]:
        box('檐下_横向彩绘',(0,sy*d/2,z),(w,.18,h),PAINT,'05_檐下彩绘')
        for x in np.linspace(-w/2+.3,w/2-.3,19):
            brackets.box((x,sy*(d/2+.08),z-h/2-.06),(.30,.35,.16))
            brackets.box((x,sy*(d/2+.13),z-h/2+.04),(.46,.42,.10))
    for sx in [-1,1]:box('檐下_侧向彩绘',(sx*w/2,0,z),(.18,d,h),PAINT,'05_檐下彩绘')
    for dz in [-h/2,h/2]:
        for sy in [-1,1]:box('彩绘_金边',(0,sy*(d/2+.10),z+dz),(w,.055,.045),GOLD,'05_檐下彩绘')
        for sx in [-1,1]:box('彩绘_金边',(sx*(w/2+.10),0,z+dz),(.055,d,.045),GOLD,'05_檐下彩绘')
frieze(15.4,7.9,10.52,.48)
box('重檐_上层红墙',(0,0,11.67),(13.8,6.5,1.02),RED,'02_明楼红墙')
frieze(13.95,6.65,12.04,.46);brackets.finish()

# Two clear roof tiers. The upper roof is hip-and-gable; the lower is a hip skirt.
surface=Mesh('双层屋顶_连续瓦底','04_双层琉璃瓦',TILEBASE,0,True)
tiles=Mesh('双层屋顶_筒瓦','04_双层琉璃瓦',YELLOW,0,True)
ridges=Mesh('双层屋顶_屋脊与吻兽','04_双层琉璃瓦',YELLOW,0,True)
def sheet(fn,nu,nv):
    v=[fn(-1+2*i/nu,j/nv) for j in range(nv+1) for i in range(nu+1)];f=[]
    for j in range(nv):
        for i in range(nu):a=j*(nu+1)+i;f.append((a,a+1,a+nu+2,a+nu+1))
    surface.add(v,f)
def upper_front(u,t,s):
    if t<=.70:
        q=t/.70;x=u*6.3;y=s*3.05*q;z=12.28+2.35*(1-q)**1.55
    else:
        q=(t-.70)/.30;x=u*(6.3+1.7*q);y=s*(3.05+1.1*q);z=12.28-.48*q+.25*q**4+.22*abs(u)**8*q**3
    return (x,y,z)
def upper_side(u,t,s):return (s*(6.3+1.7*t),u*(3.05+1.1*t),12.28-.48*t+.25*t**4+.22*abs(u)**8*t**3)
def lower_front(u,t,s):return (u*(6.95+1.9*t),s*(3.25+1.7*t),11.35-.75*t+.22*t**4+.25*abs(u)**8*t**3)
def lower_side(u,t,s):return (s*(6.95+1.9*t),u*(3.25+1.7*t),11.35-.75*t+.22*t**4+.25*abs(u)**8*t**3)
for tier,frontfn,sidefn,nf,ns,npath in [('上',upper_front,upper_side,29,15,11),('下',lower_front,lower_side,31,17,5)]:
    for s in [-1,1]:
        for fn,n,nu,nv,npth in [(lambda u,t:frontfn(u,t,s),nf,20,10 if tier=='上' else 4,npath),(lambda u,t:sidefn(u,t,s),ns,10,4,5)]:
            sheet(fn,nu,nv)
            for i in range(n):
                u=-1+2*i/(n-1);tiles.tube([Vector(fn(u,j/(npth-1)))+Vector((0,0,.045)) for j in range(npth)],.071,6)
            for off,rr in [(-.025,.085),(-.16,.060)]:ridges.tube([Vector(fn(-1+2*j/18,1))+Vector((0,0,off)) for j in range(19)],rr,6)
        for sy in [-1,1]:
            fn=sidefn;pts=[Vector(fn(sy,j/10,s))+Vector((0,0,.075)) for j in range(11)]
            end=pts[-1];pts += [end+Vector((s*.15,sy*.10,.10)),end+Vector((s*.22,sy*.15,.28))];ridges.tube(pts,.12,7)
            for t in [.62,.80,.94]:
                p=Vector(fn(sy,t,s))+Vector((0,0,.12));ridges.tube([p,p+Vector((0,0,.16)),p+Vector((s*.08,0,.20))],.045,5)
for sx in [-1,1]:
    profile=[(-3.05,12.28),(3.05,12.28)]+[(3.05*(1-j/12),12.28+2.35*(j/12)**1.55) for j in range(1,13)]+[(-3.05*j/12,12.28+2.35*(1-j/12)**1.55) for j in range(1,13)]
    g=Mesh('上檐_三角山墙','02_明楼红墙',RED);n=len(profile);xx=sx*6.27
    g.add([(xx-.06,y,z) for y,z in profile]+[(xx+.06,y,z) for y,z in profile],[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]);g.finish()
    for sy in [-1,1]:ridges.tube([(sx*6.32,sy*3.05*j/16,12.35+2.35*(1-j/16)**1.55) for j in range(17)],.12,7)
    x=sx*6.3;z=14.63;ridges.box((x,0,z+.28),(.24,.36,.60))
    pts=[]
    for j in range(17):
        t=j/16;a=-pi/2+t*pi*1.65;rr=.30*(1-.6*t);pts.append((x+sx*(.07+rr*cos(a)),0,z+.60+rr*sin(a)))
    ridges.tube(pts,.09,7)
    # Modest round gold gable medallion.
    med=Mesh('山花_金色团纹','05_檐下彩绘',GOLD,0,True)
    med.tube([(sx*6.36,.24*cos(j*2*pi/16),12.80+.24*sin(j*2*pi/16)) for j in range(17)],.038,5);med.finish()
ridges.box((0,0,14.75),(12.8,.24,.24))
ridges.tube([(-6.4,0,14.91),(6.4,0,14.91)],.09,7)
roof=surface.finish();sol=roof.modifiers.new('瓦底薄壳','SOLIDIFY');sol.thickness=.065;sol.offset=-1
tiles.finish();ridges.finish()

def active(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
objects=[o for o in bpy.data.objects if o.type=='MESH' and o.parent==root]
for o in objects:
    active(o)
    for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
    # UVs are aligned to wall height and repeat at architectural scales.
    uv=o.data.uv_layers.active
    for p in o.data.polygons:
        mat=o.data.materials[p.material_index];ax=max(range(3),key=lambda a:abs(p.normal[a]))
        for li in p.loop_indices:
            co=o.data.vertices[o.data.loops[li].vertex_index].co
            horizontal=co.y if ax==0 else co.x
            if mat==PAINT:
                center=10.52 if co.z<11.2 else 12.04;h=.48 if co.z<11.2 else .46
                uv.data[li].uv=(horizontal/6,(co.z-center)/h+.5)
            elif mat in [MASONRY,BRICK]:uv.data[li].uv=(horizontal/5,co.z/(3.2 if mat==MASONRY else 3.0))
            elif mat==PAVING:uv.data[li].uv=(co.x/5,co.y/5) if ax==2 else (horizontal/5,co.z/5)
    o.data.calc_loop_triangles()
tri=sum(len(o.data.loop_triangles) for o in objects);print('GEOMETRY_TRIANGLES',tri,flush=True);print(sorted([(o.name,len(o.data.loop_triangles)) for o in objects],key=lambda v:-v[1])[:12],flush=True)
assert 20000<=tri<=40000,tri

# Studio and cameras are separate from the model and never exported to GLB.
floor=box('摄影棚地面',(0,0,-.16),(200,200,.25),BACK,'07_摄影棚');floor.parent=None
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.cycles.max_bounces=6
world=bpy.data.worlds.new('柔和日光环境');scene.world=world;world.use_nodes=True;bg=world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.71,.79,.93,1);bg.inputs['Strength'].default_value=.45
def area(name,loc,power,size,color):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(name,d);COL['07_摄影棚'].objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,5))-o.location).to_track_quat('-Z','Y').to_euler()
area('主光_暖日光',(-15,-18,32),6500,14,(1,.88,.73));area('补光_天空',(18,-4,22),4300,18,(.72,.83,1));area('轮廓光',(5,23,28),5500,12,(1,.97,.89))
d=bpy.data.lights.new('日光','SUN');d.energy=1.7;d.angle=.14;d.color=(1,.91,.8);o=bpy.data.objects.new('日光',d);COL['07_摄影棚'].objects.link(o);o.rotation_euler=(.48,-.45,-.35)
def camera(name,loc,target,scale):
    d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=scale;d.clip_end=500;o=bpy.data.objects.new(name,d);COL['07_摄影棚'].objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
cams={'侧前方':camera('相机_侧前方',(32,-42,29),(0,0,6.0),35),'正面':camera('相机_正面',(0,-60,8),(0,0,8),30),'侧面':camera('相机_侧面',(60,0,8),(0,0,8),26)}
scene.camera=cams['侧前方'];scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.render.resolution_x=1500;scene.render.resolution_y=1500;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.unit_settings.system='METRIC'
for f in ['build_mingxiaoling.py','geometry.py']:
    t=bpy.data.texts.new(f);t.write((HERE/f).read_text())
t=bpy.data.texts.new('README');t.write('明孝陵方城明楼。按同目录效果图创作，非测绘复原。01–06 为建筑，07 为摄影棚。正面 -Y / Z-up，导出 glTF +Z / Y-up。纹理已打包。单一整体控制器可缩放。\n')
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':a.spaces.active.shading.type='MATERIAL';a.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'明孝陵_分组可编辑_带材质.blend'))
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();asset=bpy.context.object;asset.name='明孝陵_WEB_建筑';asset.parent=root
color=asset.data.color_attributes.new(name='AO_Contact',type='FLOAT_COLOR',domain='CORNER');asset.data.color_attributes.active_color=color;asset.data.color_attributes.render_color_index=asset.data.color_attributes.find(color.name)
scene.cycles.samples=24;active(asset);bpy.ops.object.bake(type='AO',target='VERTEX_COLORS',use_clear=True)
values=np.empty(len(color.data)*4,dtype=np.float32);color.data.foreach_get('color',values);values=values.reshape(-1,4);values[:,:3]=.60+.40*np.clip(values[:,:3],0,1);values[:,3]=1;color.data.foreach_set('color',values.ravel())
active(asset);root.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'明孝陵_网页版.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_vertex_color='ACTIVE',export_all_vertex_colors=False,export_cameras=False,export_lights=False)
blob=(OUT/'明孝陵_网页版.glb').read_bytes();doc=json.loads(blob[20:20+struct.unpack_from('<I',blob,12)[0]])
tri=sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives']);assert 20000<=tri<=40000,tri
assert all('COLOR_0' in p['attributes'] for m in doc['meshes'] for p in m['primitives'])
assert all('uri' not in im for im in doc.get('images',[]))
for m in set(slot.material for slot in asset.material_slots):
    bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');n=m.node_tree.nodes;l=m.node_tree.links;vc=n.new('ShaderNodeVertexColor');vc.layer_name='AO_Contact';mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
    if bs.inputs['Base Color'].links:
        link=bs.inputs['Base Color'].links[0];src=link.from_socket;l.remove(link);l.new(src,mix.inputs[1])
    else:mix.inputs[1].default_value=bs.inputs['Base Color'].default_value
    l.new(vc.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],bs.inputs['Base Color'])
scene.cycles.samples=40;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'明孝陵_网页版.blend'))
bpy.context.view_layer.update()
report={'triangles':tri,'previous_triangles':2414,'glb_bytes':len(blob),'previous_glb_bytes':122596,'glb_mib':round(len(blob)/1024**2,3),'material_count':len(doc['materials']),'embedded_images':len(doc.get('images',[])),'vertex_ao':True,'sha256':hashlib.sha256(blob).hexdigest(),'blender_dimensions':[round(v,4) for v in asset.dimensions],'scene_scale':.45}
(OUT/'web-model-stats.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('MODEL_READY',report,flush=True)
for name in ['侧前方','正面','侧面']:
    scene.camera=cams[name];scene.render.resolution_x=1500 if name=='侧前方' else 1200;scene.render.resolution_y=1500 if name=='侧前方' else 1000;scene.render.filepath=str(OUT/('明孝陵_实模_'+name+'.png'));bpy.ops.render.render(write_still=True)
