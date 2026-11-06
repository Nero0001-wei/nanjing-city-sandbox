import bpy
from pathlib import Path
root=Path('/Users/echo/Documents/AIGC/南京城市沙盘')
source=(root/'景点建模工具/build_landmark.py').read_text()
for name,scale,offset in [('美龄宫',.47,(0,0,0)),('南京博物院',.4,(-3.25,0,0)),('中华门',.38,(0,0,-2.5))]:
 for path in [root/(name+'模型')/(name+'_分组可编辑_带材质.blend'),root/(name+'模型/web')/(name+'_网页版.blend')]:
  bpy.ops.wm.open_mainfile(filepath=str(path))
  text=bpy.data.texts.get('build_landmark.py');text.clear();text.write(source)
  ctrl=bpy.data.objects.get(name+'_整体控制器');ctrl['网页等比缩放']=scale;ctrl['网页相对锚点偏移_XYZ']=offset
  bpy.ops.wm.save_as_mainfile(filepath=str(path))
