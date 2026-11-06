"""Tree-free miniature bridge assets, based on the saved imagegen concept sheets.
Blender -b --factory-startup --python build_bridge.py -- yangtze-bridge|nanjing-eye
Add --geometry-only to check evaluated geometry before baking and rendering.
"""
import bpy,sys,json,struct,hashlib,math
import numpy as np
from pathlib import Path
from math import sin,cos,pi
from mathutils import Vector
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));import geometry as G
ID=sys.argv[sys.argv.index('--')+1]
NAME,LENGTH,ENDS,LIFT={
 'yangtze-bridge':('南京长江大桥',60,[[238.54166458590976, 199.24266141397703], [287.63972107952617, 244.2587059534653]],3.425),
 'nanjing-eye':('南京眼',40,[[121.304078,604.629209],[136.910675,619.464255]],1.64),
}[ID]
SCALE=math.dist(*ENDS)*.6/LENGTH;DECK=(LIFT+.018)/SCALE
ANCHOR={'yangtze-bridge':[251.82207999995444,207.8233166267164],'nanjing-eye':[132.6339413332753,613.8021951375995]}[ID]
PROJECT=HERE.parent/(NAME+'模型');OUT=PROJECT/'web';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
G.COL={}
for name in ['01_桥墩基础','02_桥面与梁架','03_桥塔','04_索缆与连接件','05_栏杆与灯具','06_摄影棚']:
 c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c);G.COL[name]=c
root=bpy.data.objects.new(NAME+'_整体控制器',None);G.COL['01_桥墩基础'].objects.link(root);G.root=root
root['说明']='建筑概念模型，无树木。原生长轴 +X / Z-up，GLB 长轴 +X / Y-up。桥面由既有道路高程校准。'
root['网页等比缩放']=SCALE;root['桥面标高']=DECK;root['桥长']=LENGTH
Mesh=G.Mesh;material=G.material
STONE=material('米白石材','D7C8A9',.83);CREAM=material('暖米黄桥头堡','E3D2AE',.78)
STEEL=material('蓝灰防锈钢构','637D8C',.43,coat=.12);WHITE=material('象牙白钢塔','E9E7DB',.36,coat=.2)
RED=material('红旗雕塑','BD3C31',.44,coat=.15);DARK=material('深灰钢轨及窗玻璃','33454D',.38)
METAL=material('银灰索缆','858F91',.48);GOLD=material('暖铜栏杆饰条','B89B64',.39)
LAMP=material('玉兰灯磨砂罩','F5E5B8',.35);ROAD=material('浅灰桥面','9C9E99',.88)
PAVING=material('暖灰铺装','C9C9BD',.87);BACK=material('摄影棚背景','EAE9E4',.9)

def texture(mat,name,kind):
 yy,xx=np.mgrid[:1024,:1024];u=xx/1024;v=yy/1024
 if kind=='stone':
  row=np.floor(v*8);seam=((u*4+row*.5)%1<.018)|(v*8%1<.024);rgb=np.array([.83,.79,.69]);shade=1-.12*seam+.012*np.sin(xx*.23+yy*.17)
 elif kind=='paving':
  seam=(u*8%1<.026)|(v*8%1<.026);rgb=np.array([.76,.77,.74]);shade=1-.16*seam+.009*np.sin(xx*.37+yy*.41)
 else:
  rgb=np.array([.59,.61,.60]);shade=1+.018*np.sin(xx*.97+yy*.59)+.012*np.cos(xx*.39-yy*.61)
 pixels=np.ones((1024,1024,4),np.float32);pixels[:,:,:3]=rgb*shade[:,:,None]
 im=bpy.data.images.new(name,width=1024,height=1024,alpha=False);im.pixels.foreach_set(pixels.ravel());im.filepath_raw=str(OUT/(kind+'_1024.png'));im.file_format='PNG';im.save();im.pack()
 n=mat.node_tree.nodes;tex=n.new('ShaderNodeTexImage');tex.image=im;bs=next(n for n in n if n.type=='BSDF_PRINCIPLED');mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
texture(STONE,'砌石纹理','stone');texture(PAVING,'人行桥铺装纹理','paving');texture(ROAD,'细颗粒公路桥面','asphalt')

def box(name,p,d,mat=STONE,col='02_桥面与梁架',bevel=0):
 m=Mesh(name,col,mat);m.box(p,d);o=m.finish()
 if bevel:
  mod=o.modifiers.new('单段轮廓倒角','BEVEL');mod.width=bevel;mod.segments=1
  mod=o.modifiers.new('加权法线','WEIGHTED_NORMAL');mod.keep_sharp=True
 return o

def beam(m,p,q,w,h=None,mi=0,section='box'):
 h=h or w;p=Vector(p);q=Vector(q);t=(q-p).normalized();guide=Vector((0,0,1))
 if abs(t.dot(guide))>.94:guide=Vector((0,1,0))
 a=t.cross(guide).normalized();b=t.cross(a).normalized()
 if section=='I':profile=[(-.5,-.5),(.5,-.5),(.5,-.3),(.12,-.3),(.12,.3),(.5,.3),(.5,.5),(-.5,.5),(-.5,.3),(-.12,.3),(-.12,-.3),(-.5,-.3)]
 else:profile=[(-.5,-.5),(.5,-.5),(.5,.5),(-.5,.5)]
 n=len(profile);vs=[tuple(v+a*x*w+b*y*h) for v in [p,q] for x,y in profile]
 m.add(vs,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],mi)

def pier(x,y,z,width,depth):
 box('桥墩承台',(x,y,-.12),(width+ .4,depth+.4,.4),STONE,'01_桥墩基础',.055)
 box('收分墩身',(x,y,z/2),(width,depth,z),STONE,'01_桥墩基础',.09)
 box('支座盖梁',(x,y,z+.08),(width+.24,depth+.28,.24),STONE,'01_桥墩基础',.035)

def build_yangtze():
 lower=DECK-2.8;top=DECK-.48
 box('完整公路桥面',(0,0,DECK-.19),(60,2.65,.38),ROAD,bevel=.035)
 box('下层铁路梁板',(0,0,lower-.16),(60,2.35,.32),STEEL)
 chords=Mesh('工字钢桁架与横联','02_桥面与梁架',STEEL)
 plates=Mesh('钢节点连接板','04_索缆与连接件',STEEL)
 for y in [-1.15,1.15]:
  for z in [lower,top]:beam(chords,(-29.9,y,z),(29.9,y,z),.22,.30,section='I')
  for i in range(25):
   x=-30+i*2.5;beam(chords,(x,y,lower),(x,y,top),.18,.23,section='I')
   for z in [lower,top,(lower+top)/2]:plates.box((x,y,z),(.33,.07,.30))
   if i<24:
    beam(chords,(x,y,lower),(x+2.5,y,top),.16,.20,section='I');beam(chords,(x,y,top),(x+2.5,y,lower),.16,.20,section='I')
    plates.box((x+1.25,y,(lower+top)/2),(.33,.075,.33))
 for i in range(25):
  x=-30+i*2.5
  for z in [lower-.2,top+.18]:beam(chords,(x,-1.15,z),(x,1.15,z),.16,.24,section='I')
  if i<24:beam(chords,(x,-1.1,top),(x+2.5,1.1,top),.09,.14,section='I')
 chords.finish();plates.finish()
 rail=Mesh('双线铁路与枕木','02_桥面与梁架',[DARK,STONE])
 for y in [-.83,-.38,.38,.83]:beam(rail,(-30,y,lower+.12),(30,y,lower+.12),.06,.11,section='I')
 for i in range(160):rail.box((-29.85+i*.375,0,lower+.015),(.14,2.12,.10),1)
 rail.finish()
 for x in [-24,-12,0,12,24]:pier(x,0,lower-.55,1.25,2.35)
 guards=Mesh('桥栏杆与装饰面板','05_栏杆与灯具',[CREAM,GOLD])
 for y in [-1.29,1.29]:
  for z in [DECK+.13,DECK+.65]:beam(guards,(-30,y,z),(30,y,z),.11,.11)
  for i in range(101):
   x=-30+i*.6;guards.box((x,y,DECK+.39),(.10,.12,.60))
   if i<100:
    # Readable sunflower-inspired opening rather than tiny sculpted relief.
    guards.tube([(x+.14,y,DECK+.36),(x+.3,y,DECK+.55),(x+.46,y,DECK+.36),(x+.3,y,DECK+.18),(x+.14,y,DECK+.36)],.022,4,1)
 guards.finish()
 lamps=Mesh('玉兰灯柱','05_栏杆与灯具',[DARK,GOLD,LAMP],smooth=True)
 for y in [-1.27,1.27]:
  for x in np.linspace(-22,22,16):
   lamps.tube([(x,y,DECK+.65),(x,y,DECK+1.65)],.046,8)
   for side in [-1,0,1]:
    px=x+side*.16;zz=DECK+1.63+(side==0)*.17
    lamps.tube([(x,y,DECK+1.35),(px,y,zz)],.026,6,1)
    lamps.tube([(px,y,zz),(px,y,zz+.20)],.068,8,2)
 lamps.finish()
 for x in [-25.8,25.8]:
  for y in [-2.05,2.05]:
   box('桥头堡基础',(x,y,.25),(2.20,1.5,1.0),STONE,'01_桥墩基础',.06)
   box('米黄色桥头堡',(x,y,5.4),(1.85,1.25,10.5),CREAM,'03_桥塔',.04)
   for z,w,d,h in [(1,2.1,1.43,.28),(DECK-.1,2.15,1.5,.32),(DECK+.2,2.28,1.6,.20),(10.6,2.1,1.45,.20),(10.9,2.28,1.6,.23),(11.16,2.1,1.45,.17)]:box('桥头堡石材檐线',(x,y,z),(w,d,h),STONE,'03_桥塔',.022)
   frames=Mesh('桥头堡竖向窗与线脚','03_桥塔',[DARK,CREAM])
   for face in [-1,1]:
    for dx in [-.43,.43]:
     for z,h in [(2.8,2.8),(8.2,3.5)]:
      frames.box((x+dx,y+face*.632,z),(.34,.025,h))
      for side in [-1,1]:frames.box((x+dx+side*.21,y+face*.65,z),(.065,.07,h+.13),1)
      for zz in np.arange(z-h/2,z+h/2+.1,.64):frames.box((x+dx,y+face*.66,zz),(.41,.08,.06),1)
   for face in [-1,1]:
    for z in [2.7,7.9]:frames.box((x+face*.932,y,z),(.025,.45,2.6))
   frames.finish()
   crown=Mesh('三面红旗雕塑','03_桥塔',[RED,GOLD])
   for k in range(3):
    xx=x-.72+k*.48;bottom=11.3;h=.82+k*.25
    profile=[(xx,bottom),(xx+.43,bottom+.09),(xx+.43,bottom+h),(xx+.10,bottom+h-.04),(xx,bottom+h-.17)]
    crown.prism(profile,y-.08,y+.08)
   crown.tube([(x+.8,y,11.3),(x+.8,y,12.9)],.035,8,1);crown.finish()
   balcony=Mesh('桥头堡阳台石栏','05_栏杆与灯具',CREAM)
   for side in [-1,1]:
    beam(balcony,(x-1.05,y+side*.72,DECK+.78),(x+1.05,y+side*.72,DECK+.78),.10)
    for k in range(11):balcony.box((x-1.05+k*.21,y+side*.72,DECK+.52),(.065,.07,.52))
   balcony.finish()
 # Subtle lane dashes; road network passes beneath this finished surface.
 markings=Mesh('公路中心虚线','02_桥面与梁架',LAMP)
 for x in np.arange(-29,29,1.4):markings.box((x,0,DECK+.006),(.65,.035,.008))
 markings.finish()

def build_eye():
 box('连续人行桥面',(0,0,DECK-.16),(40,3.1,.32),PAVING,bevel=.045)
 beams=Mesh('钢箱梁下缘与横隔梁','02_桥面与梁架',WHITE)
 for y in [-1.35,0,1.35]:beam(beams,(-20,y,DECK-.42),(20,y,DECK-.42),.18,.38,section='I')
 for i in range(81):beam(beams,(-20+i*.5,-1.45,DECK-.35),(-20+i*.5,1.45,DECK-.35),.12,.27,section='I')
 beams.finish()
 guards=Mesh('连续栏杆与四道水平索','05_栏杆与灯具',[WHITE,METAL,GOLD])
 for y in [-1.5,1.5]:
  for i in range(101):guards.box((-20+i*.4,y,DECK+.40),(.075,.09,.8))
  for z in [.15,.29,.43,.57]:guards.tube([(-20,y,DECK+z),(20,y,DECK+z)],.017,6,1)
  guards.tube([(-20,y,DECK+.81),(20,y,DECK+.81)],.055,8,2)
 guards.finish()
 for x in [-18.3,18.3]:pier(x,0,DECK-.72,.58,1.42)
 # The mapped walking span ends on both banks; short stairs connect it to grade.
 stairs=Mesh('两岸落地台阶','02_桥面与梁架',PAVING)
 stairrails=Mesh('引桥台阶扶手','05_栏杆与灯具',[WHITE,METAL,GOLD])
 for sign in [-1,1]:
  for i in range(18):
   z=DECK-(DECK+.45)*(i+1)/18
   stairs.box((sign*(20+(i+.5)*8/18),0,(z-.60)/2),(8/18,3.1,z+.60))
  for y in [-1.5,1.5]:
   for i in range(1,19):
    x=sign*(20+i*8/18);z=DECK-(DECK+.45)*i/18
    stairrails.box((x,y,z+.40),(.075,.09,.8))
   for z in [.15,.29,.43,.57,.81]:
    stairrails.tube([(sign*20,y,DECK+z),(sign*28,y,-.45+z)],.055 if z==.81 else .017,8 if z==.81 else 6,2 if z==.81 else 1)
 stairs.finish();stairrails.finish()
 cables=Mesh('双索面扇形钢索','04_索缆与连接件',METAL,smooth=True)
 shoes=Mesh('钢索锚头与连接套','04_索缆与连接件',[WHITE,METAL],smooth=True)
 for sign in [-1,1]:
  foot=sign*7.0;ry=4.4;rz=5.7;zc=5.86;lean=math.tan(math.radians(35))
  def point(t):
   z=zc+rz*sin(t);return Vector((foot+sign*lean*(z-.16),ry*cos(t),z))
  shell=Mesh('向岸侧倾斜椭圆钢塔','03_桥塔',WHITE,smooth=False)
  seam=Mesh('椭圆塔拼装分缝','03_桥塔',STONE)
  n=128;cross=[(-.27,-.22),(.27,-.22),(.38,-.1),(.38,.1),(.27,.22),(-.27,.22),(-.38,.1),(-.38,-.1)]
  vs=[]
  for i in range(n):
   t=i*2*pi/n;p=point(t);tangent=(point(t+.001)-point(t-.001)).normalized();axis=Vector((1,0,-sign*lean)).normalized();radial=tangent.cross(axis).normalized()
   for a,b in cross:vs.append(tuple(p+axis*a+radial*b))
   if i%8==0:
    q=[tuple(p+axis*(a*1.015)+radial*(b*1.015)) for a,b in cross];seam.tube(q+[q[0]],.009,4)
  shell.add(vs,[(i*8+j,i*8+(j+1)%8,((i+1)%n)*8+(j+1)%8,((i+1)%n)*8+j) for i in range(n) for j in range(8)]);shell.finish();seam.finish()
  pier(foot,0,.37,1.75,2.1)
  for side in [-1,1]:
   for direction in [-1,1]:
    for k in range(20):
     t=.38+.94*k/19;p=point(t if side==1 else pi-t)
     x=sign*((10.8-10.4*k/19) if direction<0 else (14.2+5.5*k/19))
     q=Vector((x,side*1.43,DECK+.18));p.y+=side*.10
     cables.tube([tuple(q),tuple(p)],.024,8)
     tangent=(p-q).normalized()
     shoes.tube([tuple(q),tuple(q+tangent*.24)],.075,8)
     shoes.tube([tuple(p),tuple(p-tangent*.25)],.07,8,1)
     shoes.box(tuple(q-Vector((0,0,.07))),(.19,.19,.15))
  # Bridge-to-pylon saddles do not cross or obstruct the walking surface.
  saddle=Mesh('索塔横向承托','01_桥墩基础',WHITE)
  beam(saddle,(foot,-1.42,DECK-.55),(foot,1.42,DECK-.55),.30,.34,section='I');saddle.finish()
 cables.finish();shoes.finish()

{'yangtze-bridge':build_yangtze,'nanjing-eye':build_eye}[ID]()
def active(o):
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
objects=[o for o in root.children if o.type=='MESH']
for o in objects:
 active(o)
 for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
 o.data.calc_loop_triangles()
total=sum(len(o.data.loop_triangles) for o in objects);print('EVALUATED_TRIANGLES',ID,total,flush=True)
if '--geometry-only' in sys.argv:sys.exit(0)
assert 20000<=total<=40000,(ID,total)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.world.use_nodes=True;bg=scene.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.73,.80,.91,1);bg.inputs['Strength'].default_value=.45
for name,loc,power,size,color in [('主光',(-22,-27,40),10000,22,(1,.88,.73)),('补光',(24,-5,27),6500,24,(.76,.86,1)),('轮廓光',(5,30,36),8000,18,(1,.97,.88))]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(name,d);G.COL['06_摄影棚'].objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,4))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.lights.new('太阳','SUN');d.energy=1.5;d.angle=.15;o=bpy.data.objects.new('太阳',d);G.COL['06_摄影棚'].objects.link(o);o.rotation_euler=(.48,-.45,-.35)
floor=box('摄影棚地面',(0,0,-.42),(500,500,.1),BACK,'06_摄影棚');floor.parent=None
def camera(name,loc,target,scale):
 d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=scale;d.clip_end=1000;o=bpy.data.objects.new(name,d);G.COL['06_摄影棚'].objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
extent=68 if ID=='yangtze-bridge' else 64
cams={'侧前方':camera('侧前方',(38,-65,36),(0,0,4.8),extent),'侧面':camera('侧面',(0,-70,12),(0,0,5),extent),'桥端':camera('桥端',(80,0,14),(0,0,5),24)}
scene.camera=cams['侧前方'];scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.render.resolution_x=1800;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.unit_settings.system='METRIC'
for f in ['build_bridge.py','geometry.py']:
 t=bpy.data.texts.new(f);t.write((HERE/f).read_text())
t=bpy.data.texts.new('模型说明');t.write(NAME+'：imagegen 概念模型，非测绘复原。01–05 为建筑，06 为独立摄影棚；贴图已打包。源文件长轴 +X / Z-up，网页长轴 +X / Y-up，整体等比缩放。')
for screen in bpy.data.screens:
 for a in screen.areas:
  if a.type=='VIEW_3D':a.spaces.active.shading.type='MATERIAL';a.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT/(NAME+'_分组可编辑_带材质.blend')))
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();asset=bpy.context.object;asset.name=NAME+'_WEB_桥梁';asset.parent=root;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
color=asset.data.color_attributes.new(name='AO_Contact',type='FLOAT_COLOR',domain='CORNER');asset.data.color_attributes.active_color=color;asset.data.color_attributes.render_color_index=asset.data.color_attributes.find(color.name)
active(asset);bpy.ops.object.bake(type='AO',target='VERTEX_COLORS',use_clear=True)
values=np.empty(len(color.data)*4,dtype=np.float32);color.data.foreach_get('color',values);values=values.reshape(-1,4);values[:,:3]=.64+.36*np.clip(values[:,:3],0,1);values[:,3]=1;color.data.foreach_set('color',values.ravel())
active(asset);root.select_set(True);glb=OUT/(NAME+'_网页版.glb')
bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_vertex_color='ACTIVE',export_all_vertex_colors=False,export_cameras=False,export_lights=False)
blob=glb.read_bytes();doc=json.loads(blob[20:20+struct.unpack_from('<I',blob,12)[0]]);actual=sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives']);assert 20000<=actual<=40000,(ID,actual)
assert all('COLOR_0' in p['attributes'] for m in doc['meshes'] for p in m['primitives']);assert all('uri' not in im for im in doc.get('images',[]))
for m in set(slot.material for slot in asset.material_slots):
 bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');n=m.node_tree.nodes;l=m.node_tree.links;vc=n.new('ShaderNodeVertexColor');vc.layer_name='AO_Contact';mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
 if bs.inputs['Base Color'].links:
  link=bs.inputs['Base Color'].links[0];src=link.from_socket;l.remove(link);l.new(src,mix.inputs[1])
 else:mix.inputs[1].default_value=bs.inputs['Base Color'].default_value
 l.new(vc.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],bs.inputs['Base Color'])
scene.cycles.samples=32;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(NAME+'_网页版.blend')))
bpy.context.view_layer.update();anchor=ANCHOR
report={'id':ID,'triangles':actual,'glb_bytes':len(blob),'material_count':len(doc['materials']),'embedded_images':len(doc.get('images',[])),'vertex_ao':True,'sha256':hashlib.sha256(blob).hexdigest(),'blender_dimensions':[round(v,5) for v in asset.dimensions],'scene_scale':SCALE,'scene_offset':[(sum(c)/2-anchor[i])*.6 if i<2 else 0 for i,c in enumerate(zip(*ENDS))],'scene_rotation_y':-math.atan2(ENDS[1][1]-ENDS[0][1],ENDS[1][0]-ENDS[0][0]),'source_endpoints':ENDS,'native_deck_length':LENGTH,'native_deck_top':DECK,'road_lift':LIFT,'deck_surface_clearance':.018}
report['scene_offset']=[report['scene_offset'][0],.02,report['scene_offset'][1]]
(OUT/'web-model-stats.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('MODEL_READY',report,flush=True)
for name in ['侧前方','侧面','桥端']:
 scene.camera=cams[name];scene.render.resolution_x=1400 if name=='桥端' else 1800;scene.render.resolution_y=1100 if name=='桥端' else 900;scene.render.filepath=str(OUT/(NAME+'_实模_'+name+'.png'));bpy.ops.render.render(write_still=True)
