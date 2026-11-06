import bpy
p='/Users/echo/Documents/AIGC/南京城市沙盘/总统府模型/总统府_分组可编辑_带材质.blend'
bpy.ops.wm.open_mainfile(filepath=p)
o=bpy.data.objects['總統府匾额']
print('PLAQUE',tuple(o.data.polygons[0].normal),[tuple(u.uv) for u in o.data.uv_layers.active.data])
for m in o.data.materials:
 print('MAT',m.name)
 for n in m.node_tree.nodes:
  if n.type=='TEX_IMAGE':
   im=n.image
   print('IMAGE',im.name,im.filepath,tuple(im.size),im.packed_file is not None,min(im.pixels),max(im.pixels),list(im.pixels[:16]))
