"""Read-back check of all four delivered Blender files."""
from pathlib import Path
import bpy,json
root=Path(__file__).resolve().parents[2];reports=[]
for name in ['南京长江大桥','南京眼']:
 for web in [False,True]:
  p=root/(name+'模型')/('web' if web else '')/(name+('_网页版.blend' if web else '_分组可编辑_带材质.blend'))
  bpy.ops.wm.open_mainfile(filepath=str(p))
  images=[i for i in bpy.data.images if i.source=='FILE']
  assert images and all(i.packed_file for i in images), 'external texture dependency'
  assert not bpy.data.libraries, 'linked external blend dependency'
  controller=bpy.data.objects[name+'_整体控制器'];meshes=[o for o in controller.children if o.type=='MESH']
  assert len(meshes)==1 if web else len(meshes)>10
  reports.append({'file':str(p.relative_to(root)),'packed_images':len(images),'model_meshes':len(meshes),'collections':[c.name for c in bpy.data.collections],'vertex_ao':bool(meshes[0].data.color_attributes) if web else False})
(root/'景点建模工具/桥梁验收/blend-check.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2))
print('DELIVERY_BLEND_CHECK_OK',len(reports))
