import bpy,json,struct
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parent
root=bpy.data.objects.get('中山陵_整体控制器')
assert root is not None
objects=[o for o in bpy.data.objects if o.type=='MESH' and o.parent==root]
assert len(objects)>50
assert all(o.data.materials for o in objects)
assert not [i.filepath for i in bpy.data.images if i.source=='FILE' and not i.packed_file]
assert len([o for o in bpy.data.objects if o.type=='CAMERA'])==4
bpy.context.view_layer.update()
points=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
lo=[min(v[i] for v in points) for i in range(3)];hi=[max(v[i] for v in points) for i in range(3)]
blob=(p/'中山陵_无树木_带材质.glb').read_bytes();magic,version,total=struct.unpack_from('<4sII',blob)
assert magic==b'glTF' and version==2 and total==len(blob)
length,typ=struct.unpack_from('<II',blob,12);g=json.loads(blob[20:20+length])
assert len(g['meshes'])>50 and len(g['materials'])>=10
assert not any('camera' in n for n in g['nodes'])
assert not g.get('images')
report={'status':'PASS','mesh_objects':len(objects),'dimensions':[round(hi[i]-lo[i],4) for i in range(3)],'bounds_min':lo,'bounds_max':hi,'external_texture_dependencies':0,'cameras':4,'gltf_meshes':len(g['meshes']),'gltf_materials':len(g['materials'])}
(p/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('VERIFIED',json.dumps(report,ensure_ascii=False))
