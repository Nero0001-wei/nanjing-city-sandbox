"""Seven small, texture-free Blender trees; paired web/compact meshes, one material.
Run with Blender --background --python 树木模型/build_trees.py.
"""
import bpy, math, random, json, struct, hashlib, shutil
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'web'; OUT.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
mat=bpy.data.materials.new('Foliage and bark · vertex colour');mat.use_nodes=True
nodes=mat.node_tree.nodes; nodes.clear(); bsdf=nodes.new('ShaderNodeBsdfPrincipled'); output=nodes.new('ShaderNodeOutputMaterial'); mat.node_tree.links.new(bsdf.outputs['BSDF'],output.inputs['Surface']); bsdf.inputs['Roughness'].default_value=.91
color=nodes.new('ShaderNodeVertexColor');color.layer_name='Color';mat.node_tree.links.new(color.outputs['Color'],bsdf.inputs['Base Color'])
PALETTE={'camphor':'62894d','plane':'7b9958','ginkgo':'a6ad58','willow':'789b64','pine':'4e7958','cedar':'4f7760','blossom':'bd9d9f'}
def linear(h):
 c=[int(h[i:i+2],16)/255 for i in (0,2,4)]
 return [(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4) for v in c]
objects=[]
def make(species,compact):
 rng=random.Random(119+list(PALETTE).index(species));verts=[];faces=[];colors=[];n=(6 if compact else 9) if species=='pine' else (8 if compact else 12)
 def v(p,c):verts.append((p[0],p[1],max(0,p[2])));colors.append(c);return len(verts)-1
 def branch(a,b,r):
  a,b=Vector(a),Vector(b);axis=(b-a).normalized();u=axis.cross(Vector((0,1,0))).normalized();w=axis.cross(u).normalized();ids=[]
  for p,rad in [(a,r),(b,r*.48)]:
   ids.append([v(tuple(p+rad*(u*math.cos(k*2*math.pi/5)+w*math.sin(k*2*math.pi/5))),linear('80715c')) for k in range(5)])
  for k in range(5):j=(k+1)%5;faces.extend([(ids[0][k],ids[0][j],ids[1][j]),(ids[0][k],ids[1][j],ids[1][k])])
  faces.extend([tuple(reversed(ids[0])),tuple(ids[1])])
 def crown(center,radii,seed=0,kind='round'):
  cx,cy,cz=center;rx,ry,rz=radii;phase=seed*1.73
  # One connected crown with asymmetrical shoulders and subtle lobes, no leaf spheres.
  levels=[(-.91,.16),(-.57,.73),(-.06,1),(.47,.85),(.86,.4)] if not compact else [(-.85,.23),(-.3,.93),(.4,.89),(.88,.32)]
  if kind=='fan':levels=[(-.94,.15),(-.48,.53),(.1,.92),(.58,1),(.92,.43)] if not compact else [(-.9,.16),(-.2,.7),(.5,1),(.9,.4)]
  if kind=='weeping':levels=[(-.94,.18),(-.72,.83),(-.15,1),(.45,.82),(.88,.32)] if not compact else [(-.92,.2),(-.5,.9),(.3,.87),(.9,.3)]
  base=linear(PALETTE[species]); rings=[]
  for z,r in levels:
   row=[]
   for k in range(n):
    a=k/n*2*math.pi
    lobe=1+.105*math.cos(3*a+phase)+.065*math.sin(5*a-phase)
    zz=z+.065*math.sin(a*3+phase)*(1-abs(z))
    if kind=='weeping' and z<-.5:zz-=.22*(.5+.5*math.cos(5*a))
    p=(cx+rx*(math.cos(a)*r*lobe+.06*z),cy+ry*(math.sin(a)*r*lobe+.045*z),cz+rz*zz)
    shade=.74+.24*(z+1)/2+.055*math.cos(a-.7)
    row.append(v(p,[c*shade for c in base]))
   rings.append(row)
  bottom=v((cx,cy,cz-rz),[c*.7 for c in base]);top=v((cx+.04*rx,cy,cz+rz),base)
  for k in range(n):
   j=(k+1)%n;faces.append((bottom,rings[0][j],rings[0][k]));faces.append((rings[-1][k],rings[-1][j],top))
  for lower,upper in zip(rings,rings[1:]):
   for k in range(n):
    j=(k+1)%n;faces.extend([(lower[k],lower[j],upper[j]),(lower[k],upper[j],upper[k])])
 if species=='cedar':
  branch((0,0,0),(.035,0,3.72),.12)
  # A continuous, layered conifer silhouette; short skirts, a narrow closed tip.
  base=linear(PALETTE[species]);nn=8 if compact else 10;rows=[]
  for z,r in [(1,.35),(1.12,1),(1.8,.38),(1.85,.78),(2.45,.26),(2.5,.55),(3.05,.17),(3.1,.34),(3.9,.015)]:
   row=[]
   for k in range(nn):
    a=2*math.pi*k/nn;rr=r*(1+.07*math.sin(a*3+z));row.append(v((rr*math.cos(a),rr*math.sin(a),z+.025*math.sin(2*a)),[c*(.8+.2*z/4) for c in base]))
   rows.append(row)
  faces.append(tuple(reversed(rows[0])));faces.append(tuple(rows[-1]))
  for a,b in zip(rows,rows[1:]):
   for k in range(nn):j=(k+1)%nn;faces.extend([(a[k],a[j],b[j]),(a[k],b[j],b[k])])
 elif species=='pine':
  branch((0,0,0),(.22,.03,3.3),.14)
  for j,(a,z) in enumerate([(0,1.9),(2.45,2.65),(4.6,3.25)]):
   tip=(math.cos(a)*(.65-j*.18),math.sin(a)*(.65-j*.18),z)
   branch((.1,0,z-.7),tip,.075);crown(tip,(.95-j*.14,.8-j*.1,.43),j)
 else:
  top=2.4 if species in ['plane','willow','blossom'] else 2.65
  branch((0,0,0),(.06,0,top),.16 if species=='plane' else .12)
  for j in range(2 if compact else 3):
   a=j*2.4+.3;radius=.36 if species=='ginkgo' else .6;branch((0,0,1.05),(radius*math.cos(a),radius*math.sin(a),2.15),.065)
  dims={'camphor':(1.16,1.05,1.23,2.65),'plane':(1.35,1.17,1.03,2.55),'ginkgo':(.98,.9,1.3,2.75),'willow':(1.23,1.1,1.11,2.28),'blossom':(1.16,1.07,.94,2.28)}[species]
  rx,ry,rz,z=dims;crown((.06,0,z),(rx,ry,rz),list(PALETTE).index(species), 'fan' if species=='ginkgo' else 'weeping' if species=='willow' else 'round')
 name=species+('_compact' if compact else '_full');mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
 obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj);mesh.materials.append(mat)
 attr=mesh.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
 for i,c in enumerate(colors):attr.data[i].color=(*c,1)
 for f in mesh.polygons:f.use_smooth=True
 objects.append(obj)
for species in PALETTE:
 for compact in [False,True]:make(species,compact)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'树木_网页版.blend'))
file=OUT/'trees.glb';bpy.ops.export_scene.gltf(filepath=str(file),export_format='GLB',export_yup=True,export_normals=True,export_texcoords=False,export_materials='EXPORT',export_vertex_color='ACTIVE',export_all_vertex_colors=False,export_cameras=False,export_lights=False)
b=file.read_bytes();doc=json.loads(b[20:20+struct.unpack_from('<I',b,12)[0]])
meshes={m['name']:sum(doc['accessors'][p.get('indices',p['attributes']['POSITION'])]['count']//3 for p in m['primitives']) for m in doc['meshes']}
assert max(meshes.values())<=400,meshes
stats={'file':'trees.glb','glb_bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'version':'blender-trees-v1-'+hashlib.sha256(b).hexdigest()[:8],'triangles':meshes,'total_library_triangles':sum(meshes.values()),'materials':len(doc['materials']),'textures':len(doc.get('images',[])),'coordinate_convention':'glTF Y-up, trunk foot origin; one mesh per species and detail level','source_blend':'../../../树木模型/树木_分组可编辑.blend','web_blend':'../../../树木模型/web/树木_网页版.blend','generator':'../../../树木模型/build_trees.py','max_triangles_per_tree':400,'vertex_colors':True}
(ROOT.parent/'sandbox-app/src/tree-asset.js').write_text("// Generated by 树木模型/build_trees.py; cache key follows exported bytes.\nexport const TREE_ASSET='/models/trees.glb?v="+stats['version']+"';\n")
(OUT/'stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2));shutil.copy2(file,ROOT.parent/'sandbox-app/public/models/trees.glb')
manifest_path=ROOT.parent/'sandbox-app/public/models/manifest.json';manifest=json.loads(manifest_path.read_text());manifest['vegetation']=stats;manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
# An editable, labelled lineup, separate from the origin-aligned runtime asset.
for i,obj in enumerate(objects):obj.location=((i//2)*4.1,3 if i%2 else 0,0)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'树木_分组可编辑.blend'))
# Render the actual exported geometry's full-detail shapes, not a concept image.
for o in objects:o.hide_render=o.name.endswith('_compact')
bpy.ops.mesh.primitive_plane_add(size=200,location=(12,0,-.02));floor=bpy.context.object
m=bpy.data.materials.new('Warm paper');m.diffuse_color=(.78,.77,.69,1);floor.data.materials.append(m)
bpy.ops.object.camera_add(location=(22,-26,18));cam=bpy.context.object;cam.rotation_euler=(Vector((12,0,1.7))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=30;bpy.context.scene.camera=cam
bpy.ops.object.light_add(type='AREA',location=(8,-10,18));bpy.context.object.data.energy=2800;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=12
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=32;sc.world.color=(.4,.4,.4);sc.view_settings.view_transform='AgX';sc.render.resolution_x=1800;sc.render.resolution_y=620;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.filepath=str(OUT/'树木实模预览.png');bpy.ops.render.render(write_still=True)
print(json.dumps(stats,ensure_ascii=False,indent=2))
