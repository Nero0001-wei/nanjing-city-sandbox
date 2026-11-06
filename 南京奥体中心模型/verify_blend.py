"""Read back the delivered Blender files without modifying them."""
from pathlib import Path
import bpy,json
p=Path(__file__).resolve().parent
report=[]
for file in [p/'南京奥体中心体育场_分组可编辑_带材质.blend',p/'web/南京奥体中心体育场_网页版.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(file))
    meshes=[o for o in bpy.data.objects if o.type=='MESH' and o.parent and '整体控制器' in o.parent.name]
    for o in meshes:o.data.calc_loop_triangles()
    images=[i for i in bpy.data.images if i.type=='IMAGE' and i.name!='Render Result']
    stats={'file':file.name,'asset_meshes':len(meshes),'triangles':sum(len(o.data.loop_triangles) for o in meshes),'packed_images':len(images),'all_images_packed':all(i.packed_file is not None for i in images)}
    assert stats['triangles']==38018 and stats['all_images_packed'] and stats['packed_images']==3
    report.append(stats)
(p/'web/blend-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
