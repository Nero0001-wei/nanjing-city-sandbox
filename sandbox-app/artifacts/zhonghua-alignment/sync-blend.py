import bpy,json
from pathlib import Path
root=Path('/Users/echo/Documents/AIGC/南京城市沙盘')
source=(root/'景点建模工具/build_landmark.py').read_text()
p=json.loads((root/'sandbox-app/artifacts/zhonghua-alignment/placement.json').read_text())['placement']
for name in ['中华门模型/中华门_分组可编辑_带材质.blend','中华门模型/web/中华门_网页版.blend']:
 path=root/name;bpy.ops.wm.open_mainfile(filepath=str(path))
 text=bpy.data.texts.get('build_landmark.py');text.clear();text.write(source)
 ctrl=bpy.data.objects.get('中华门_整体控制器');ctrl['网页相对锚点偏移_XYZ']=[p['offsetX'],0,p['offsetZ']];ctrl['网页绕Y轴朝向_弧度']=p['rotationY']
 bpy.ops.wm.save_as_mainfile(filepath=str(path))
