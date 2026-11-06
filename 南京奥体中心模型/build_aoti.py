"""Nanjing Olympic Sports Center stadium; run with Blender in background mode.
Tree-free miniature derived from the saved imagegen concept and official photos.
The editable master, packed web asset, materials and rendered views are delivered.
"""
from pathlib import Path
import sys,math,json,struct,hashlib
import bpy,numpy as np
from math import sin,cos,pi
from mathutils import Vector

PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parent
sys.path.insert(0,str(ROOT/'景点建模工具'))
import geometry as G
NAME='南京奥体中心体育场';ID='aoti';SCALE=.38
OUT=PROJECT/'web';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
G.COL={}
for name in ['01_石台与入口','02_看台与玻璃幕墙','03_曲面屋盖','04_红色双拱与支撑','05_运动场与设备','06_摄影棚']:
    c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c);G.COL[name]=c
root=bpy.data.objects.new(NAME+'_整体控制器',None);G.COL['01_石台与入口'].objects.link(root);G.root=root
root['说明']='主体育场，无树木；按官方照片与 imagegen 效果图作沙盘化概括，非测绘复原。'
root['网页等比缩放']=SCALE;root['方向']='Z-up，南面 -Y；GLB 为 Y-up，南面 +Z。'
Mesh=G.Mesh
STONE=G.material('暖白石材','DCCFB8',.82)
WHITE=G.material('象牙白钢构','E7E6DA',.48,coat=.1)
SILVER=G.material('银灰曲面屋盖','B8C5C7',.5,coat=.16)
RED=G.material('金陵红钢拱与外墙','D52D28',.4,coat=.2)
GLASS=G.material('青灰玻璃幕墙','52777A',.31,coat=.3)
DARK=G.material('内侧暗部与计分屏','253B3D',.78)
SEAT=G.material('灰绿色看台座椅','739494',.8)
TURF=G.material('运动场草坪','60863D',.95)
TRACK=G.material('赭红色跑道','B96E52',.92)
BACK=G.material('摄影棚暖灰','EAE9E4',.9)

def image_material(mat,name,kind):
    y,x=np.mgrid[:1024,:1024];u=x/1024;v=y/1024
    if kind=='stone':
        seam=((u*6+np.floor(v*6)%2*.5)%1<.018)|(v*6%1<.018)
        rgb=np.array([.86,.81,.72]);shade=1-seam*.12+.012*np.sin(x*.13+y*.31)
    elif kind=='seats':
        seam=(u*14%1<.09)|(v*14%1<.15)
        rgb=np.array([.44,.58,.58]);shade=1-seam*.27+.035*np.sin(np.floor(u*14)*19+np.floor(v*14)*7)
    else:
        rgb=np.array([.37,.53,.23]);shade=1+.10*(np.floor(v*12)%2)+.018*np.sin(x*.7+y*.49)
    pixels=np.ones((1024,1024,4),np.float32);pixels[:,:,:3]=rgb*shade[:,:,None]
    im=bpy.data.images.new(name,width=1024,height=1024,alpha=False);im.pixels.foreach_set(pixels.ravel())
    im.filepath_raw=str(OUT/(kind+'_1024.png'));im.file_format='PNG';im.save();im.pack()
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im
    bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
image_material(STONE,'浅石材铺装','stone');image_material(SEAT,'座椅分缝贴图','seats');image_material(TURF,'草坪条带','turf')

def box(name,p,d,mat=STONE,col='01_石台与入口',angle=0):
    m=Mesh(name,col,mat);m.box((0,0,0),d);o=m.finish();o.location=p;o.rotation_euler.z=angle;return o

def ring(name,inner,outer,z,mat,col,n=144,z1=None,start=0,end=2*pi):
    m=Mesh(name,col,mat);z1=z if z1 is None else z1
    vertices=[]
    for i in range(n+1):
        t=start+(end-start)*i/n
        vertices.extend([(inner[0]*cos(t),inner[1]*sin(t),z),(outer[0]*cos(t),outer[1]*sin(t),z1)])
    m.add(vertices,[(i*2,i*2+1,i*2+3,i*2+2) for i in range(n)])
    return m.finish()

def cylinder(name,r,z0,z1,mat=STONE,col='01_石台与入口',n=160):
    m=Mesh(name,col,mat,smooth=True)
    vs=[(r*cos(2*pi*i/n),r*sin(2*pi*i/n),z) for z in [z0,z1] for i in range(n)]
    m.add(vs,[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)])
    return m.finish()

def band(name,rx,ry,z0,z1,mat,col='02_看台与玻璃幕墙',start=0,end=2*pi,n=144):
    m=Mesh(name,col,mat,smooth=True)
    vs=[(rx*cos(start+(end-start)*i/n),ry*sin(start+(end-start)*i/n),z) for i in range(n+1) for z in [z0,z1]]
    m.add(vs,[(2*i,2*i+2,2*i+3,2*i+1) for i in range(n)])
    return m.finish()

# A small embedded base avoids a floating gap above the scene's ground anchor.
cylinder('圆形石台基础',20.5,-.5,.12)
cylinder('上层铺装',20.15,.12,.23)
ring('环形入口平台',(13.7,14.1),(16.65,16.65),1.05,STONE,'01_石台与入口')
band('平台外缘',16.65,16.65,.23,1.05,STONE,'01_石台与入口')
for j in range(12):
    a=2*pi*j/12
    for i in range(10):
        r=19.05-i*.24;h=.23+(i+1)*.082
        box('放射入口阶梯', (r*cos(a),r*sin(a),(.23+h)/2),(.26,2.1,h-.23),angle=a)

# The facade stays a reusable set of glass bands, columns and slab edges.
band('内侧深色碗体',12.95,13.75,.55,4.45,DARK)
band('底层连续玻璃',14.1,14.6,.72,2.04,GLASS)
band('上层连续玻璃',14.1,14.6,2.22,4.35,GLASS)
for z in [.65,2.12,4.46]:
    ring('环形石材楼板',(12.8,13.5),(14.4,14.9),z,STONE,'02_看台与玻璃幕墙')
    band('楼板边缘',14.4,14.9,z-.10,z+.06,WHITE)
for i in range(72):
    t=2*pi*i/72
    box('幕墙竖向龙骨',(14.16*cos(t),14.66*sin(t),2.53),(.075,.075,3.72),WHITE,'02_看台与玻璃幕墙')
for z in [1.3,2.75,3.45]:band('幕墙水平龙骨',14.16,14.66,z,z+.055,WHITE)
for i in range(24):
    t=2*pi*i/24
    box('外侧白色立柱',(14.3*cos(t),14.8*sin(t),2.54),(.29,.34,3.9),STONE,'02_看台与玻璃幕墙',t)
for a,b in [(-.46,-.10),(.10,.25),(pi-.35,pi+.12)]:
    band('红色立面板',14.28,14.78,1.5,4.47,RED,start=a,end=b,n=18)

# Stepped seating bands with a real opening. Seats are textured, not thousands
# of disconnected chairs. Radial aisles remain visible between seating blocks.
for row in range(20):
    f=row/20;g=(row+1)/20
    inner=(6.0+6.85*f,10+3.65*f);outer=(6+6.85*g,10+3.65*g)
    z=.62+row*.172+(.25 if row>=10 else 0)
    ring('看台第%02d排'%row,inner,outer,z,SEAT,'02_看台与玻璃幕墙',n=128)
    band('看台踢面',outer[0],outer[1],z,z+.172,SEAT,n=128)
    aisle=Mesh('放射楼梯踏面','02_看台与玻璃幕墙',STONE)
    for j in range(20):
        t=2*pi*j/20;da=.012
        aisle.add([(rx*cos(a),ry*sin(a),z+.018) for rx,ry,a in [(inner[0],inner[1],t-da),(outer[0],outer[1],t-da),(outer[0],outer[1],t+da),(inner[0],inner[1],t+da)]],[(0,1,2,3)])
    aisle.finish()
ring('看台中层环廊',(9.0,11.5),(9.55,11.98),2.3,STONE,'02_看台与玻璃幕墙')
band('中层环廊挡板',9.425,11.825,2.34,2.59,STONE)

def roof_point(t,r):
    x=(8.15+(14.65-8.15)*r)*cos(t);y=(11.15+(15.1-11.15)*r)*sin(t)
    z=(4.85+.45*cos(2*t))*(1-r)+(6.05+.6*cos(2*t))*r+.26*sin(pi*r)
    return (x,y,z)
roof=Mesh('开放式双曲面银灰屋盖','03_曲面屋盖',SILVER,smooth=True)
N,R=144,7
vs=[]
for lower in [False,True]:
    for i in range(N):
        for j in range(R+1):
            x,y,z=roof_point(2*pi*i/N,j/R);vs.append((x,y,z-(.1 if lower else 0)))
skin=N*(R+1);fs=[]
for k in [0,skin]:
    for i in range(N):
        for j in range(R):
            a=k+i*(R+1)+j;b=k+((i+1)%N)*(R+1)+j
            fs.append((a,b,b+1,a+1))
for i in range(N):
    for j in [0,R]:
        a=i*(R+1)+j;b=((i+1)%N)*(R+1)+j;fs.append((a,a+skin,b+skin,b))
roof.add(vs,fs);roof.finish()
ribs=Mesh('放射屋面分缝与压边','03_曲面屋盖',WHITE,smooth=True)
for i in range(36):
    t=2*pi*i/36;ribs.tube([(x,y,z+.035) for x,y,z in [roof_point(t,j/7) for j in range(8)]],.038,4)
for r in [0,1]:ribs.tube([roof_point(2*pi*i/96,r) for i in range(97)],.075,6)
ribs.finish()
supports=Mesh('环形屋盖白色V形支撑','03_曲面屋盖',WHITE,smooth=True)
for i in range(48):
    t=2*pi*i/48;p=(13.9*cos(t),14.4*sin(t),4.45)
    for dt in [-pi/55,pi/55]:supports.tube([p,roof_point(t+dt,1)],.065,6)
supports.finish()

def arch_point(t,side):return Vector((side*(6.5+9.5*sin(t)),-18.2*cos(t),.55+9.5*sin(t)))
for side in [-1,1]:
    arch=Mesh('向外倾斜45度的红色巨拱','04_红色双拱与支撑',RED)
    vs=[];ns=96;plane_normal=Vector((side,0,-1)).normalized()
    for i in range(ns+1):
        t=pi*i/ns;p=arch_point(t,side);tangent=Vector((side*9.5*cos(t),18.2*sin(t),9.5*cos(t))).normalized()
        radial=tangent.cross(plane_normal).normalized()
        for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]:vs.append(tuple(p+radial*a*.54+plane_normal*b*.24))
    fs=[tuple(reversed(range(4))),tuple(ns*4+i for i in range(4))]
    for i in range(ns):
        for j in range(4):fs.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
    arch.add(vs,fs);arch.finish()
    for y in [-18.2,18.2]:box('红拱落地石墩',(side*6.5,y,.38),(2.0,1.7,.36))
    truss=Mesh('红拱与屋盖的白色连接桁架','04_红色双拱与支撑',WHITE,smooth=True)
    for y in np.linspace(-13.5,13.5,23):
        t=math.acos(-y/18.2);p=arch_point(t,side)
        for dy in [-.44,.44]:
            a=math.asin((y+dy)/15.1)
            if side<0:a=pi-a
            q=roof_point(a,1);truss.tube([p,q],.052,6)
    truss.finish()

def capsule(radius,n=144):
    return [(radius*cos(2*pi*i/n),radius*sin(2*pi*i/n)+(3.65 if i<n//2 else -3.65)) for i in range(n)]
def flat_ring(name,r0,r1,z,mat):
    a,b=capsule(r0),capsule(r1);m=Mesh(name,'05_运动场与设备',mat)
    m.add([(x,y,z) for x,y in a+b],[(i,(i+1)%len(a),(i+1)%len(a)+len(a),i+len(a)) for i in range(len(a))]);return m.finish()
field=Mesh('内场草坪','05_运动场与设备',TURF);pts=capsule(4.0);field.add([(x,y,.43) for x,y in pts],[tuple(range(len(pts)))]);field.finish()
flat_ring('八道环形跑道',4.0,5.55,.44,TRACK)
for i in range(9):flat_ring('跑道白线',4.0+i*1.55/8,4.014+i*1.55/8,.455,WHITE)
pitch=box('足球场',(0,0,.447),(6.8,10.5,.022),TURF,'05_运动场与设备')
uv=pitch.data.uv_layers.active
for poly in pitch.data.polygons:
    for li in poly.loop_indices:
        co=pitch.data.vertices[pitch.data.loops[li].vertex_index].co;uv.data[li].uv=(co.x/6.8+.5,co.y/10.5+.5)
marks=Mesh('球场边线与中线','05_运动场与设备',WHITE)
for x in [-3.37,3.37]:marks.box((x,0,.469),(.025,10.45,.012))
for y in [-5.22,0,5.22]:marks.box((0,y,.469),(6.76,.025,.012))
for sign in [-1,1]:
    for w,h in [(4.03,1.65),(1.83,.55)]:
        for x in [-w/2,w/2]:marks.box((x,sign*(5.22-h/2),.469),(.025,h,.012))
        marks.box((0,sign*(5.22-h),.469),(w,.025,.012))
marks.finish()
circle=Mesh('中圈与禁区弧线','05_运动场与设备',WHITE)
for cy,r,a,b in [(0,.915,0,2*pi),(4.12,.915,pi*1.19,pi*1.81),(-4.12,.915,pi*.19,pi*.81)]:
    vs=[];n=64
    for i in range(n+1):
        t=a+(b-a)*i/n;vs.extend([(rr*cos(t),cy+rr*sin(t),.478) for rr in [r-.012,r+.012]])
    circle.add(vs,[(i*2,i*2+1,i*2+3,i*2+2) for i in range(n)])
circle.finish()
for sign in [-1,1]:
    goal=Mesh('白色球门框','05_运动场与设备',WHITE,smooth=True)
    goal.tube([(-.37,sign*5.24,.48),(-.37,sign*5.24,.73),(.37,sign*5.24,.73),(.37,sign*5.24,.48)],.022,6)
    for x in [-.37,.37]:goal.tube([(x,sign*5.24,.73),(x,sign*5.52,.48),(x,sign*5.24,.48)],.018,6)
    goal.finish()
    box('端部计分屏',(0,sign*13.68,4.75),(3.0,.12,1.15),DARK,'05_运动场与设备')
    for x in [-1.55,1.55]:box('计分屏白色边框',(x,sign*13.68,4.75),(.09,.16,1.3),WHITE,'05_运动场与设备')
    for z in [4.12,5.38]:box('计分屏白色边框',(0,sign*13.68,z),(3.15,.16,.09),WHITE,'05_运动场与设备')

objects=[o for o in root.children if o.type=='MESH']
def active(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
for o in objects:
    active(o);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.data.calc_loop_triangles()
tri=sum(len(o.data.loop_triangles) for o in objects);print('GEOMETRY_TRIANGLES',tri,flush=True)
if '--geometry-only' in sys.argv:
    print(sorted([(len(o.data.loop_triangles),o.name) for o in objects],reverse=True)[:15],flush=True);sys.exit(0)
assert 20000<=tri<=40000,tri
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.cycles.max_bounces=6
scene.world=bpy.data.worlds.new('柔和日光');scene.world.use_nodes=True
bg=scene.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.72,.80,.92,1);bg.inputs['Strength'].default_value=.45
floor=box('摄影棚地面',(0,0,-.64),(400,400,.24),BACK,'06_摄影棚');floor.parent=None
for name,loc,power,size,color in [('主光',(-30,-40,55),13000,22,(1,.89,.76)),('补光',(38,8,40),8500,26,(.77,.86,1)),('轮廓光',(-5,40,45),11000,20,(1,.96,.88))]:
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(name,d);G.COL['06_摄影棚'].objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,4))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.lights.new('太阳','SUN');d.energy=1.5;d.angle=.15;o=bpy.data.objects.new('太阳',d);G.COL['06_摄影棚'].objects.link(o);o.rotation_euler=(.45,-.48,-.4)
def camera(name,p,target,scale):
    d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=scale;o=bpy.data.objects.new(name,d);G.COL['06_摄影棚'].objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
cams={'侧前方':camera('侧前方',(44,-56,42),(0,0,2.6),49),'正面':camera('南立面',(0,-70,10),(0,0,4),47),'侧面':camera('东立面',(70,0,10),(0,0,4),47)}
scene.camera=cams['侧前方'];scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
scene.render.resolution_x=1400;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
for p in [Path(__file__),ROOT/'景点建模工具/geometry.py']:
    t=bpy.data.texts.new(p.name);t.write(p.read_text())
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':a.spaces.active.shading.type='MATERIAL';a.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT/(NAME+'_分组可编辑_带材质.blend')))
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();asset=bpy.context.object;asset.name=NAME+'_WEB';asset.parent=root
color=asset.data.color_attributes.new(name='AO_Contact',type='FLOAT_COLOR',domain='CORNER');asset.data.color_attributes.active_color=color;asset.data.color_attributes.render_color_index=0
scene.cycles.samples=20;active(asset);bpy.ops.object.bake(type='AO',target='VERTEX_COLORS',use_clear=True)
values=np.empty(len(color.data)*4,dtype=np.float32);color.data.foreach_get('color',values);values=values.reshape(-1,4);values[:,:3]=.65+.35*np.clip(values[:,:3],0,1);values[:,3]=1;color.data.foreach_set('color',values.ravel())
active(asset);root.select_set(True);glb=OUT/(NAME+'_网页版.glb')
bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_vertex_color='ACTIVE',export_all_vertex_colors=False,export_cameras=False,export_lights=False)
blob=glb.read_bytes();doc=json.loads(blob[20:20+struct.unpack_from('<I',blob,12)[0]])
actual=sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives']);assert 20000<=actual<=40000,actual
assert all('COLOR_0' in p['attributes'] for m in doc['meshes'] for p in m['primitives']);assert all('uri' not in im for im in doc.get('images',[]))
for mat in {s.material for s in asset.material_slots}:
    nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');vc=nodes.new('ShaderNodeVertexColor');vc.layer_name='AO_Contact';mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
    if bs.inputs['Base Color'].links:
        old=bs.inputs['Base Color'].links[0];source=old.from_socket;links.remove(old);links.new(source,mix.inputs[1])
    else:mix.inputs[1].default_value=bs.inputs['Base Color'].default_value
    links.new(vc.outputs['Color'],mix.inputs[2]);links.new(mix.outputs[0],bs.inputs['Base Color'])
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(NAME+'_网页版.blend')))
bpy.context.view_layer.update()
stats={'id':ID,'triangles':actual,'glb_bytes':len(blob),'material_count':len(doc['materials']),'embedded_images':len(doc.get('images',[])),'vertex_ao':True,'sha256':hashlib.sha256(blob).hexdigest(),'blender_dimensions':[round(v,4) for v in asset.dimensions],'scene_scale':SCALE}
(OUT/'web-model-stats.json').write_text(json.dumps(stats,indent=2));print('MODEL_READY',stats,flush=True)
scene.cycles.samples=32
for name,cam in cams.items():
    scene.camera=cam;scene.render.filepath=str(OUT/(NAME+'_实模_'+name+'.png'));bpy.ops.render.render(write_still=True)
