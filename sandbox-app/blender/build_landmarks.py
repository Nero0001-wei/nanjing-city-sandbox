"""Run with Blender --background --python blender/build_landmarks.py.
Original, deliberately simplified assets. Blender Z-up -> glTF Y-up on export.
Local origin = ground centre, front = Blender -Y (= glTF +Z).
"""
import bpy, math, json
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'public/models'; OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for block in list(bpy.data.materials): bpy.data.materials.remove(block)

def mat(name,hex):
    def linear(v): return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
    m=bpy.data.materials.new(name); m.diffuse_color=tuple(linear(int(hex[i:i+2],16)/255) for i in (0,2,4))+(1,)
    m.use_nodes=True; bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=m.diffuse_color;bs.inputs['Roughness'].default_value=.78
    return m
M={k:mat(k,v) for k,v in dict(cream='F0E5CA',stone='A6AD9C',light='FAF2DD',red='A74D3D',gold='D8AE50',blue='3E7081',jade='527F69',glass='6C9AAB',dark='3E574E',water='64ADB7').items()}
active=None; manifests=[]
def finish(o,name,material,bevel=0):
    o.name=name;o.data.materials.append(M[material])
    for c in list(o.users_collection):c.objects.unlink(o)
    active.objects.link(o)
    if bevel:
        mod=o.modifiers.new('Soft edges','BEVEL');mod.width=bevel;mod.segments=2
        o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return o
def box(name,p,size,material='cream',bevel=.05):
    bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,name,material,bevel)
def cylinder(name,p,r,depth,material='cream',vertices=12,r2=None):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices,radius1=r,radius2=r if r2 is None else r2,depth=depth,location=p)
    return finish(bpy.context.object,name,material,.025)
def beam(name,a,b,r=.1,material='light'):
    a,b=Vector(a),Vector(b);o=cylinder(name,(a+b)/2,r,(b-a).length,material,8)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def roof(name,x,y,z,w,d,h,color='blue'):
    pts=[(-1,-1),(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0)]
    vs=[(x+a*w/2,y+b*d/2,z+(.22 if a*b else 0)) for a,b in pts]
    vs += [(x+a*w*.25,y+b*d*.065,z+h) for a,b in pts]
    faces=[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]+[tuple(range(8,16))]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vs,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);active.objects.link(o);o.data.materials.append(M[color])
    beam(name+' ridge',(x-w*.25,y,z+h+.08),(x+w*.25,y,z+h+.08),.09,'gold' if color!='gold' else 'red')
    return o
def hall(name,x,y,z,w=7,d=4,h=2.6,roofcolor='blue',wall='cream'):
    box(name+' plinth',(x,y,z+.3),(w+1,d+1,.6),'stone')
    box(name+' body',(x,y,z+.6+h/2),(w,d,h),wall)
    for dx in [-.38,-.15,.15,.38]:
        box(name+' door',(x+dx*w,y-d/2-.035,z+1.4),(.55,.1,1.45),'dark',.015)
    for dx in [-.44,0,.44]: cylinder(name+' pillar',(x+dx*w,y-d/2-.3,z+.6+h/2),.13,h,'red',8)
    roof(name+' roof',x,y,z+.6+h,w+1.5,d+1.6,1.3,roofcolor)
def pagoda(name,x,y,levels=5,r=1.3,step=1.4,modern=False):
    cylinder(name+' foundation',(x,y,.3),r*1.5,.6,'light',8)
    for j in range(levels):
        rr=r*(1-j*.055);z=.6+j*step
        cylinder(name+' storey',(x,y,z+step*.42),rr,step*.84,'glass' if modern else 'gold',8)
        cylinder(name+' eave',(x,y,z+step*.9),rr*1.3,.26,'light' if modern else 'gold',8,r2=rr*.72)
        if modern:
            for k in range(8):
                a=k*math.pi/4;beam(name+' frame',(x+rr*math.cos(a),y+rr*math.sin(a),z),(x+rr*.95*math.cos(a),y+rr*.95*math.sin(a),z+step),.035,'light')
    cylinder(name+' spire',(x,y,.6+levels*step+.5),.18,1,'gold' if not modern else 'light',8,r2=0)
def begin(id):
    global active
    active=bpy.data.collections.new(id);bpy.context.scene.collection.children.link(active)
def end(id):
    bpy.ops.object.select_all(action='DESELECT')
    for o in active.objects:o.select_set(True)
    bpy.context.view_layer.objects.active=next(iter(active.objects))
    bpy.context.view_layer.update()
    bounds=[o.matrix_world@Vector(c) for o in active.objects for c in o.bound_box]
    dims=[max(p[i] for p in bounds)-min(p[i] for p in bounds) for i in range(3)]
    bpy.ops.export_scene.gltf(filepath=str(OUT/(id+'.glb')),use_selection=True,export_format='GLB',export_apply=True,export_yup=True)
    manifests.append(dict(id=id,file=id+'.glb',blender_dimensions=[round(d,3) for d in dims],origin='ground centre',front='glTF +Z',status='original simplified landmark model'))

begin('zifeng')
box('plaza',(0,0,.2),(7,6,.4),'stone')
for x,y,z,w,d,h in [(-.8,0,6,3.2,3.4,12),(.9,.4,9.2,2.3,2.9,18.4),(.8,.6,19,1.75,2.25,3.2),(.5,.7,21,1.1,1.6,1.1)]:
    box('stepped tower',(x,y,z),(w,d,h),'glass',.12)
    for sx in [-1,1]:box('vertical mullion',(x+sx*w*.42,y-d*.51,z),(.07,.07,h),'light',.01)
box('podium',(-1.2,-.4,1.1),(6,5,2),'cream')
cylinder('offset spire',(.5,.7,23.3),.075,3.4,'light',8,r2=.02)
end('zifeng')

begin('zhongshan')
box('terrace',(0,0,.3),(11,18,.6),'stone')
for i in range(10):box('ceremonial steps',(0,-7+i*.75,.65+i*.17),(6,.9,.3),'light',.025)
box('upper terrace',(0,3,1.35),(10,6,2.1),'light')
hall('memorial hall',0,3,2.4,7,4,3,'blue','light')
for x in [-4.4,4.4]:box('balustrade',(x,-1.3,1.5),(.25,8,.6),'light')
end('zhongshan')

begin('zhonghua')
# Real opening: separate piers and lintels instead of a painted black doorway.
box('courtyard',(0,0,.2),(11,10,.4),'stone')
for x in [-4,4]:box('gate pier',(x,-3.5,1.65),(3,2.2,3.3),'stone')
box('gate lintel',(0,-3.5,3),(5,2.2,1.3),'stone')
for x in [-5,5]:box('barbican wall',(x,0,1.2),(1,8,2.4),'stone')
for x in [-3.8,3.8]:box('inner gate',(x,3.5,1.4),(3.5,1.2,2.8),'stone')
box('inner lintel',(0,3.5,2.5),(4,1.2,.6),'stone')
for x in range(-5,6):box('battlement',(x,-3.5,3.9),(.55,2.1,.5),'stone',.025)
for y in range(-2,4):
    for x in [-5,5]:box('side battlement',(x,y,2.7),(1,.5,.6),'stone',.025)
end('zhonghua')

begin('yuejiang')
for j,(w,d) in enumerate([(7,5),(5.6,4.2),(4.3,3.3)]):
    box('tower level',(0,0,1.3+j*2.4),(w,d,2.5),'red')
    roof('golden tier',0,0,2.3+j*2.4,w+1.5,d+1.4,1.1,'gold')
box('stone terrace',(0,0,.2),(9,7,.4),'stone')
end('yuejiang')

begin('jiming')
hall('temple',-2,0,0,5,3.2,2,'gold','red');pagoda('medicine buddha tower',2.5,1,5,1.1,1.25)
end('jiming')

begin('mingxiaoling')
box('citadel',(0,1,1.1),(8,5,2.2),'red');hall('Ming tower',0,1,2.2,6,3.5,2,'gold','red')
for j in range(5):box('stairs',(0,-4+j*.65,.25+j*.22),(3,.8,.4),'stone')
for x in [-4,4]:box('enclosing wall',(x,4,1),(1,6,2),'red')
end('mingxiaoling')

begin('meiling')
box('garden platform',(0,0,.2),(9,8,.4),'stone')
box('mansion',(0,0,1.7),(6,4,3),'cream');roof('green roof',0,0,3.2,7,5,1.35,'jade')
box('portico',(0,-2.4,1.2),(3,1.3,2.1),'light');roof('portico roof',0,-2.5,2.3,3.5,1.8,.6,'jade')
for x in [-2,-1,1,2]:box('window',(x,-2.03,1.9),(.5,.08,.8),'blue',.02)
end('meiling')

begin('museum')
hall('main museum hall',0,0,.5,11,5,3,'gold','cream')
box('wide terrace',(0,0,.3),(14,8,.6),'light')
for i in range(4):box('front stairs',(0,-4.8+i*.45,.15+i*.16),(8,.6,.3),'light')
end('museum')

begin('presidential')
box('compound',(0,1,.15),(9,10,.3),'stone')
box('entrance',(0,-3,1.4),(7,1.8,2.8),'light')
box('entrance parapet',(0,-3,3),(7.4,2,.5),'light')
for x in [-2.2,0,2.2]:box('portal',(x,-3.94,1.1),(1.1,.08,2),'dark',.05)
for x in [-4,4]:box('compound wall',(x,1,1),(.35,8,2),'cream')
hall('reception hall',0,3,0,5.8,3,1.8,'dark','cream')
end('presidential')

begin('fuzimiao')
hall('Dacheng hall',0,1,0,7,4,2.6,'blue','red')
for x in [-4,4]:hall('side court',x,-2,0,1.8,3.6,1.3,'dark','cream')
box('temple square',(0,-1,.1),(10,10,.2),'stone')
end('fuzimiao')

begin('baoen')
pagoda('modern porcelain tower',0,0,7,1.25,1.35,True)
box('heritage platform',(0,0,.15),(5,5,.3),'light')
end('baoen')

begin('yangtze-bridge')
# Bridge local X follows the crossing, span scaled to its geospatial endpoints in Three.js.
box('upper deck',(0,0,3.2),(58,2.8,.45),'stone')
box('rail deck',(0,0,1.6),(58,2.4,.25),'dark')
for x in [-23,-11.5,0,11.5,23]:box('pier',(x,0,.4),(1.3,1.8,2.4),'cream')
for y in [-1.35,1.35]:
    beam('top chord',(-29,y,3),(29,y,3),.12,'light');beam('bottom chord',(-29,y,1.6),(29,y,1.6),.12,'light')
    for i in range(20):
        x=-29+i*2.9;beam('truss',(x,y,1.6),(x+2.9,y,3),.085,'light');beam('truss',(x,y,3),(x+2.9,y,1.6),.085,'light')
for x in [-25,25]:
    for y in [-2.4,2.4]:
        box('bridgehead tower',(x,y,4.4),(1.9,1.7,6.8),'cream')
        box('tower crown',(x,y,8),(1.5,1.4,.8),'red');cylinder('flag tip',(x,y,8.6),.1,.5,'gold',8)
end('yangtze-bridge')

begin('nanjing-eye')
box('pedestrian deck',(0,0,1.5),(13,1.1,.28),'cream')
for x in [-3,3]:
    bpy.ops.mesh.primitive_torus_add(major_radius=2.1,minor_radius=.11,major_segments=40,minor_segments=6,location=(x,0,3.1),rotation=(math.pi/2,.28 if x<0 else -.28,0))
    finish(bpy.context.object,'inclined eye','light')
    for k in [-1,0,1]:beam('suspension',(x+k*.7,0,1.5),(x+k*.7,0,4.8),.035,'light')
for x in [-4,4]:box('bridge foot',(x,0,.5),(.7,1.3,1.8),'stone')
end('nanjing-eye')

# A readable asset library rather than thirteen models stacked at the origin.
for idx,m in enumerate(manifests):
    col=bpy.data.collections[m['id']]
    for o in col.objects:o.location.x+=(idx%4)*75;o.location.y+=(idx//4)*40
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/nanjing-landmarks.blend'))
(OUT/'manifest.json').write_text(json.dumps({'generator':'Blender '+bpy.app.version_string,'coordinate_convention':'glTF Y-up, +Z front, bottom origin','models':manifests},ensure_ascii=False,indent=2))
print('EXPORTED',len(manifests),'landmarks')
