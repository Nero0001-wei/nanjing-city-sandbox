"""Generate the 20–40k-triangle web derivative without changing the high-poly master.
Blender -b --python build_zhongshan_web.py
Architecture is reused from build_zhongshan.py; dense repetition is resampled,
small seams are textures, and local contact shading is baked into vertex colors.
"""
import bpy, math, json, struct, hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
HERE=Path(__file__).resolve().parent
OUT_WEB=HERE/'web';OUT_WEB.mkdir(exist_ok=True)
SOURCE=HERE/'build_zhongshan.py'
source=SOURCE.read_text().split('# --- Studio, cameras and lighting. ---')[0]
def replace_once(old,new):
    global source
    assert source.count(old)==1,old
    source=source.replace(old,new)
# Structural details keep their original dimensions. These changes only reduce sampling.
replace_once('if self.bevel:', 'if False and self.bevel:')
replace_once("if not self.v:return None", "if not self.v or self.name in ['屋顶_瓦片搭接','平台_铺石分缝','叠台_石材拼缝','望柱_浅浮雕与凹框']:return None")
replace_once('sheet(fn,56,42)','sheet(fn,24,14)')
replace_once('sheet(fn,38,18)','sheet(fn,12,5)')
replace_once('for i in range(59):','for i in range(29):')
replace_once('u=-1+2*i/58;pts=[Vector(fn(u,j/64))+Vector((0,0,.045)) for j in range(65)]','u=-1+2*i/28;pts=[Vector(fn(u,j/14))+Vector((0,0,.045)) for j in range(15)]')
replace_once('tiles.tube(pts,.066,8,','tiles.tube(pts,.074,6,')
replace_once('for j in range(1,26):','for j in range(0):')
replace_once('for i in range(39):','for i in range(17):')
replace_once('u=-1+2*i/38;pts=[Vector(fn(u,j/24))+Vector((0,0,.05)) for j in range(25)];tiles.tube(pts,.064,8,','u=-1+2*i/16;pts=[Vector(fn(u,j/6))+Vector((0,0,.05)) for j in range(7)];tiles.tube(pts,.074,6,')
# Keep source globals isolated so web paths and source paths cannot be confused.
ns={'__file__':str(SOURCE),'__name__':'__web_geometry__'}
exec(compile(source,str(SOURCE),'exec'),ns)
root=bpy.data.objects['中山陵_整体控制器'];root['版本']='网页版；20,000–40,000 triangles；原高精度文件保留'
root['材质']='琉璃瓦、石材与木门；铺石/墙缝内嵌贴图；顶点接触阴影'
# Remove tiny isolated face overlays; replace platform joints with tileable maps.
for o in list(bpy.data.objects):
    if o.name.startswith(('方柱_横缝','方柱_竖缝')):bpy.data.objects.remove(o,do_unlink=True)
def active(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
# Decimate only curved ornament and rings; do not collapse stairs, arches or railings.
for name,ratio in [('屋顶_正脊与垂脊',.24),('木门_铜门环',.2)]:
    o=bpy.data.objects[name];active(o);d=o.modifiers.new('网页曲线采样','DECIMATE');d.ratio=ratio;bpy.ops.object.modifier_apply(modifier=d.name)
# Retain a single restrained bevel on the main architectural blocks.
for o in list(bpy.data.objects):
    if o.type=='MESH' and (o.name in ['底座_22x34','第1层_实心平台','第2层_实心平台','第3层_实心平台'] or o.name.startswith(('方柱_基座及冠部','屋檐_叠涩'))):
        b=o.modifiers.new('轮廓倒角','BEVEL');b.width=.025;b.segments=1
# Make ordinary architectural tiling maps locally; no imagery or external texture dependencies.
def tiled_material(name,filename,brick=False):
    size=1024;yy,xx=np.mgrid[0:size,0:size].astype(np.float32);u=xx/size;v=yy/size
    nx=2 if brick else 4;ny=4;row=np.floor(v*ny);x=u*nx+(row%2)*(.5 if brick else 0);y=v*ny
    edge=np.minimum(np.minimum(x%1,1-x%1),np.minimum(y%1,1-y%1))
    seam=np.clip((.010-edge)/.007,0,1)
    rng=np.random.default_rng(83 if brick else 51);grain=rng.normal(0,.0015,(size,size))
    colors=np.array([.92,.855,.735],dtype=np.float32) if brick else np.array([.94,.875,.765],dtype=np.float32)
    pixels=np.ones((size,size,4),dtype=np.float32)
    value=(1-.13*seam+grain)[...,None]
    pixels[:,:,:3]=np.clip(colors*value,0,1)
    im=bpy.data.images.new(name,width=size,height=size,alpha=False);im.colorspace_settings.name='sRGB';im.pixels.foreach_set(pixels.ravel());im.filepath_raw=str(OUT_WEB/filename);im.file_format='PNG';im.save();im.pack()
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*colors,1);m.node_tree.nodes.clear();n=m.node_tree.nodes;l=m.node_tree.links
    bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Roughness'].default_value=.76;tex=n.new('ShaderNodeTexImage');tex.image=im;tex.extension='REPEAT';tex.interpolation='Linear';out=n.new('ShaderNodeOutputMaterial');l.new(tex.outputs['Color'],bs.inputs['Base Color']);l.new(bs.outputs[0],out.inputs['Surface'])
    return m
paving=tiled_material('WEB_浅色铺石','paving_1024.png');masonry=tiled_material('WEB_平台石砌','masonry_1024.png',True)
for o in bpy.data.objects:
    if o.type=='MESH' and (o.name=='底座_22x34' or '实心平台' in o.name):
        o.data.materials.clear();o.data.materials.append(paving);o.data.materials.append(masonry)
        uv=o.data.uv_layers.active
        for p in o.data.polygons:
            horizontal=abs(p.normal.z)>.7;p.material_index=0 if horizontal else 1
            for li in p.loop_indices:
                co=o.data.vertices[o.data.loops[li].vertex_index].co
                uv.data[li].uv=(co.x/5,co.y/5) if horizontal else ((co.y if abs(p.normal.x)>.7 else co.x)/2.4,co.z/2.1)
# Consolidate near-identical variants while preserving the principal material types.
stone=bpy.data.materials['米白石材 · 细哑光'];blue=bpy.data.materials['钴蓝琉璃瓦 · 釉面']
for o in bpy.data.objects:
    if o.type!='MESH':continue
    for slot in o.material_slots:
        if slot.material.name.startswith('石材色差_'):slot.material=stone
        if slot.material.name.startswith('琉璃瓦高光'):slot.material=blue
# Apply final modifiers before count, UV verification and AO baking.
objects=[o for o in bpy.data.objects if o.type=='MESH' and o.parent==root]
for o in objects:
    active(o)
    for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
    o.data.calc_loop_triangles()
pre=sum(len(o.data.loop_triangles) for o in objects)
print('WEB_PRE_JOIN_TRIANGLES',pre,flush=True)
assert 20000<=pre<=40000,pre
# Joined mesh has material groups and one compact color attribute; source remains separately editable.
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();asset=bpy.context.object;asset.name='中山陵_WEB_建筑';asset.parent=root
# Bake soft local occlusion to vertices instead of relying on a city-scale shadow map.
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
color=asset.data.color_attributes.new(name='AO_Contact',type='FLOAT_COLOR',domain='CORNER');asset.data.color_attributes.active_color=color
asset.data.color_attributes.render_color_index=asset.data.color_attributes.find(color.name)
if not scene.world:scene.world=bpy.data.worlds.new('Web environment')
if hasattr(scene.world,'light_settings'):scene.world.light_settings.distance=1.7
active(asset);bpy.ops.object.bake(type='AO',target='VERTEX_COLORS',use_clear=True)
values=np.empty(len(color.data)*4,dtype=np.float32);color.data.foreach_get('color',values);values=values.reshape(-1,4)
print('AO_RANGE',float(values[:,:3].min()),float(values[:,:3].max()),flush=True)
values[:,:3]=.62+.38*np.clip(values[:,:3],0,1);values[:,3]=1;color.data.foreach_set('color',values.ravel())
# Export a model-only, self-contained GLB with vertex AO and packed maps.
active(asset);root.select_set(True)
export_enums=[x.identifier for x in bpy.ops.export_scene.gltf.get_rna_type().properties['export_vertex_color'].enum_items]
print('VERTEX_COLOR_MODES',export_enums,flush=True)
bpy.ops.export_scene.gltf(filepath=str(OUT_WEB/'中山陵_网页版.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_vertex_color='ACTIVE',export_all_vertex_colors=False,export_cameras=False,export_lights=False)
blob=(OUT_WEB/'中山陵_网页版.glb').read_bytes();doc=json.loads(blob[20:20+struct.unpack_from('<I',blob,12)[0]])
triangles=sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives'])
assert 20000<=triangles<=40000,triangles
assert all('COLOR_0' in p['attributes'] for m in doc['meshes'] for p in m['primitives'])
assert all('uri' not in im for im in doc.get('images',[]))
# Blender shader preview uses the same vertex modulation as the exported glTF.
for m in set(slot.material for slot in asset.material_slots):
    bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');n=m.node_tree.nodes;l=m.node_tree.links
    vc=n.new('ShaderNodeVertexColor');vc.layer_name='AO_Contact';mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
    if bs.inputs['Base Color'].links:
        link=bs.inputs['Base Color'].links[0];src=link.from_socket;l.remove(link);l.new(src,mix.inputs[1])
    else:mix.inputs[1].default_value=bs.inputs['Base Color'].default_value
    l.new(vc.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],bs.inputs['Base Color'])
# Keep preview studio separate, using the existing reference cameras and lights.
master=HERE/'中山陵_无树木_带材质.blend'
with bpy.data.libraries.load(str(master),link=False) as (data_from,data_to):
    data_to.collections=['08_摄影棚'];data_to.worlds=['柔和日光环境']
for c in data_to.collections:scene.collection.children.link(c)
scene.world=data_to.worlds[0];scene.camera=bpy.data.objects['相机_侧前方'];scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
scene.render.resolution_x=1500;scene.render.resolution_y=1500;scene.render.resolution_percentage=100;scene.cycles.samples=48;scene.render.image_settings.file_format='PNG'
for sc in bpy.data.screens:
    for a in sc.areas:
        if a.type=='VIEW_3D':a.spaces.active.shading.type='MATERIAL';a.spaces.active.region_3d.view_perspective='CAMERA'
scene.unit_settings.system='METRIC';bpy.ops.wm.save_as_mainfile(filepath=str(OUT_WEB/'中山陵_网页版.blend'))
report={'triangles':triangles,'source_triangles':658332,'reduction_percent':round((1-triangles/658332)*100,2),'glb_bytes':len(blob),'glb_mib':round(len(blob)/1024**2,3),'material_count':len(doc['materials']),'embedded_images':len(doc.get('images',[])),'vertex_ao':True,'sha256':hashlib.sha256(blob).hexdigest(),'blender_dimensions':[22,34,15.2422]}
(OUT_WEB/'web-model-stats.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('WEB_MODEL_READY',report,flush=True)
scene.render.filepath=str(OUT_WEB/'中山陵_网页版_实模预览.png');bpy.ops.render.render(write_still=True)
