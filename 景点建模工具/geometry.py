"""Shared lightweight mesh primitives; copied locally so this asset is standalone."""
import bpy, bmesh, math
from mathutils import Vector
from math import sin, cos, pi
def linear(c): return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
def material(name,hexcolor,rough=.5,noise=False,coat=0):
    m=bpy.data.materials.new(name);m.diffuse_color=tuple(linear(int(hexcolor[i:i+2],16)/255) for i in (0,2,4))+(1,)
    m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear();bs=n.new('ShaderNodeBsdfPrincipled');out=n.new('ShaderNodeOutputMaterial');l.new(bs.outputs['BSDF'],out.inputs['Surface']);bs.inputs['Base Color'].default_value=m.diffuse_color
    bs.inputs['Roughness'].default_value=rough;bs.inputs['Coat Weight'].default_value=coat;bs.inputs['Coat Roughness'].default_value=.23
    if noise:
        tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=28;tex.inputs['Detail'].default_value=2
        bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.018
        l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal'])
    return m
class Mesh:
    def __init__(self,name,col,mat,bevel=0,smooth=False):
        self.name=name;self.col=col;self.mats=mat if isinstance(mat,list) else [mat];self.v=[];self.f=[];self.mi=[];self.bevel=bevel;self.smooth=smooth
    def add(self,verts,faces,mi=0):
        k=len(self.v);self.v.extend(verts);self.f.extend([tuple(k+i for i in face) for face in faces]);self.mi.extend([mi]*len(faces))
    def box(self,p,d,mi=0):
        x,y,z=p;a,b,c=[q/2 for q in d]
        self.add([(x-a,y-b,z-c),(x+a,y-b,z-c),(x+a,y+b,z-c),(x-a,y+b,z-c),(x-a,y-b,z+c),(x+a,y-b,z+c),(x+a,y+b,z+c),(x-a,y+b,z+c)],[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],mi)
    def tube(self,points,r,segments=8,mi=0):
        v=[];f=[];points=[Vector(p) for p in points]
        for i,p in enumerate(points):
            tangent=(points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized();other=Vector((0,0,1))
            if abs(tangent.dot(other))>.95:other=Vector((0,1,0))
            a=tangent.cross(other).normalized();b=tangent.cross(a).normalized()
            for j in range(segments):v.append(tuple(p+r*(cos(2*pi*j/segments)*a+sin(2*pi*j/segments)*b)))
        for i in range(len(points)-1):
            for j in range(segments):f.append((i*segments+j,i*segments+(j+1)%segments,(i+1)*segments+(j+1)%segments,(i+1)*segments+j))
        f.extend([tuple(reversed(range(segments))),tuple((len(points)-1)*segments+j for j in range(segments))]);self.add(v,f,mi)
    def prism(self,profile,y0,y1,mi=0):
        # closed polygon in X/Z, extruded in Y
        n=len(profile);self.add([(x,y0,z) for x,z in profile]+[(x,y1,z) for x,z in profile],[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],mi)
    def finish(self,parent=True):
        if not self.v:return None
        me=bpy.data.meshes.new(self.name);me.from_pydata(self.v,[],self.f);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update();o=bpy.data.objects.new(self.name,me);COL[self.col].objects.link(o)
        for m in self.mats:me.materials.append(m)
        for p,i in zip(me.polygons,self.mi):p.material_index=i;p.use_smooth=self.smooth
        # UVs remain useful for replacing procedural materials with image maps.
        uv=me.uv_layers.new(name='UVMap')
        for p in me.polygons:
            ax=max(range(3),key=lambda a:abs(p.normal[a]));dims=[a for a in range(3) if a!=ax]
            for li in p.loop_indices:
                co=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(co[dims[0]]*.3,co[dims[1]]*.3)
        if self.bevel:
            mod=o.modifiers.new('边缘微倒角','BEVEL');mod.width=self.bevel;mod.segments=2
            mod=o.modifiers.new('加权法线','WEIGHTED_NORMAL');mod.keep_sharp=True;mod.weight=30
        if parent:o.parent=root
        return o
