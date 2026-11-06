import bpy
from pathlib import Path
root=Path('/Users/echo/Documents/AIGC/南京城市沙盘')
for folder,filename in [('大报恩寺模型','大报恩寺_分组可编辑_带材质.blend'),('大报恩寺模型/web','大报恩寺_网页版.blend')]:
 path=root/folder/filename;bpy.ops.wm.open_mainfile(filepath=str(path))
 floor=bpy.data.objects['摄影棚地面'];floor.scale.x=5;floor.scale.y=5
 for f in ['build_landmark.py','old_city_landmarks.py']:
  t=bpy.data.texts.get(f);t.clear();t.write((root/'景点建模工具'/f).read_text())
 bpy.ops.wm.save_as_mainfile(filepath=str(path))
 if folder.endswith('/web'):
  for label,cam in [('侧前方','塔侧前方'),('正面','塔正面'),('侧面','塔侧面')]:
   scene=bpy.context.scene;scene.camera=bpy.data.objects[cam];scene.render.resolution_x=1500 if label=='侧前方' else 1200;scene.render.resolution_y=1500 if label=='侧前方' else 1000
   scene.render.filepath=str(root/folder/('大报恩寺_实模_'+label+'.png'));bpy.ops.render.render(write_still=True)
