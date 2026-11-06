"""Tree-free old-city concepts: Dacheng Hall, Presidential Palace, modern Baoen tower.
Architectural meshes are built from reusable primitives; tiny carving stays in maps.
"""
import math
from math import sin, cos, pi
from pathlib import Path
import bpy

def build(identifier, a):
    Mesh=a['Mesh'];box=a['box'];roof=a['roof'];rail=a['rail'];stairs=a['stairs']
    window=a['window'];column=a['column'];archwall=a['archwall'];archring=a['archring']
    STONE=a['STONE'];CREAM=a['CREAM'];RED=a['RED'];WOOD=a['WOOD'];TEAL=a['TEAL']
    GOLD=a['GOLD'];DARK=a['DARK'];TILE=a['TILE'];BRICK=a['BRICK'];PAVING=a['PAVING'];PAINT=a['PAINT']
    root=a['root'];OUT=a['OUT'];G=a['G'];material=a['material']

    def mapped_material(name,filename,rough=.65):
        m=material(name,'FFFFFF',rough);im=bpy.data.images.load(str(OUT/filename));im.pack()
        n=m.node_tree.nodes;bs=next(x for x in n if x.type=='BSDF_PRINCIPLED');tex=n.new('ShaderNodeTexImage');tex.image=im
        m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);return m

    def plaque(text,x,y,z,w,h,filename):
        mat=mapped_material(text+'匾额贴图',filename)
        y-=.018
        m=Mesh(text+'匾额','04_门窗装饰',mat)
        m.add([(x-w/2,y,z-h/2),(x+w/2,y,z-h/2),(x+w/2,y,z+h/2),(x-w/2,y,z+h/2)],[(0,1,2,3)])
        o=m.finish();uv=o.data.uv_layers.active
        # BMesh may reverse an isolated face. Derive UVs from position, not loop order.
        if o.data.polygons[0].normal.y>0:o.data.polygons[0].flip()
        for loop in o.data.loops:
            co=o.data.vertices[loop.vertex_index].co
            uv.data[loop.index].uv=((co.x-x)/w+.5,(co.z-z)/h+.5)
        o.data.update()
        box(text+'匾背',(x,y+.08,z),(w+.12,.10,h+.12),GOLD if identifier=='fuzimiao' else STONE,'04_门窗装饰')

    def rotated_roof(name,x,y,z,length,width,h,nu=22,ns=8,rows=4):
        before=set(root.children)
        roof(name,0,0,z,length/2,width/2,h,max(.2,length/2-width*.42),nu=nu,ns=ns,rows=rows)
        for o in set(root.children)-before:o.rotation_euler.z=pi/2;o.location.x=x;o.location.y=y

    def bracket(name,x,y,z):
        m=Mesh(name,'04_门窗装饰',[TEAL,GOLD])
        for j in range(3):m.box((x,y,z+.17*j),(.40+.22*j,.60+.26*j,.13))
        m.box((x,y,z+.48),(1.08,1.24,.065),1);return m.finish()

    def edge_trim(name,x,y,z,w,h):
        m=Mesh(name,'04_门窗装饰',STONE)
        for dx in [-w/2,w/2]:m.box((x+dx,y,z),(.075,.09,h))
        for dz in [-h/2,h/2]:m.box((x,y,z+dz),(w+.075,.09,.075))
        return m.finish()

    def ring(name,profile,mat,n=8,phase=pi/8,col='03_屋顶或城墙'):
        m=Mesh(name,col,mat)
        vs=[(r*cos(phase+2*pi*i/n),r*sin(phase+2*pi*i/n),z) for r,z in profile for i in range(n)]
        fs=[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(len(profile)-1) for i in range(n)]
        m.add(vs,fs);return m.finish()

    def ball(name,p,r,mat,n=12,rings=7):
        m=Mesh(name,'04_门窗装饰',mat,smooth=True)
        vs=[(p[0]+r*cos(2*pi*i/n)*sin(pi*j/rings),p[1]+r*sin(2*pi*i/n)*sin(pi*j/rings),p[2]+r*cos(pi*j/rings)) for j in range(rings+1) for i in range(n)]
        m.add(vs,[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(rings) for i in range(n)])
        return m.finish()

    def dacheng():
        box('夫子庙紧凑石坪',(0,-1,.18),(28,26,.36),PAVING,'01_基础台阶',.04)
        box('院落石台',(0,-1,.51),(26.8,24.8,.30),BRICK,'01_基础台阶')
        box('院落铺地',(0,-1,.69),(26.9,24.9,.13),PAVING,'01_基础台阶')
        box('大成殿石基',(0,4,1.04),(23.3,11.8,.62),BRICK,'01_基础台阶')
        box('大成殿台面',(0,4,1.38),(23.65,12.1,.16),PAVING,'01_基础台阶')
        stairs('前广场入口石阶',0,-13.95,7.3,1.8,.36,.76,7)
        stairs('大成殿中央阶',0,-3.8,6.8,2.0,.76,1.46,7)
        box('大成殿红墙',(0,4,3.65),(20,8.8,4.4),RED,bevel=.035)
        for i in range(8):
            x=-9.8+i*2.8
            for y in [-1.1,9.1]:column('七开间檐柱',x,y,1.46,4.7,.23);bracket('前后檐斗拱',x,y,5.66)
        for i in range(7):
            x=-8.4+i*2.8
            window('大成殿格扇门',x,-.45,3.40,2.22,3.6,door=True)
            window('大成殿后窗',x,8.45,3.6,2.12,2.6,pi)
        for s in [-1,1]:
            for y in [1.3,4,6.7]:window('大殿侧窗',s*10.04,y,3.7,1.8,2.7,s*pi/2)
        roof('大成殿下重檐',0,4,6.15,11.85,6.1,1.25,8.8,nu=28,ns=10,rows=4)
        box('重檐间红墙',(0,4,7.35),(17.7,7.1,2.35),RED)
        for s in [-1,1]:box('重檐间彩绘枋',(0,4+s*3.58,7.93),(18,.09,.52),PAINT,'04_门窗装饰')
        roof('大成殿上重檐',0,4,8.45,10.8,5.25,2.65,6.85,nu=28,ns=10,rows=5)
        # A small sculptural ridge pair is sufficient at this map scale.
        m=Mesh('大成殿屋脊吻兽','04_门窗装饰',GOLD,smooth=True)
        for s in [-1,1]:m.tube([(s*(6.8+.6*t),4,11.22+.85*sin(t*pi/2)) for t in [0,.2,.4,.6,.8,1]],.10,7)
        m.finish();plaque('大成殿',0,-1.34,6.82,3.35,.92,'plaque_1024.png')
        for s in [-1,1]:
            x=s*10.6
            box('东西庑石台',(x,-5.1,.96),(4.45,11.4,.42),PAVING,'01_基础台阶')
            box('东西庑粉墙',(x+s*.95,-5.1,2.62),(1.7,10.1,2.9),CREAM,bevel=.025)
            for y in [-9.5,-7.3,-5.1,-2.9,-.7]:
                column('庑廊朱柱',x-s*1.45,y,1.18,2.9,.16)
                window('庑廊木格窗',x-s*.07,y,2.59,1.65,2.2,-s*pi/2)
            rotated_roof('东西庑灰瓦顶',x,-5.1,4.20,12.0,5.2,1.25,nu=14,ns=5,rows=3)
            rail('前广场石栏',(s*4,-12.9),(s*13,-12.9),.76,10,.75)
            rail('侧庭石栏',(s*13,-12.9),(s*13,10.8),.76,18,.75)
            rail('主殿台阶旁石栏',(s*3.7,-1.9),(s*8.2,-1.9),1.46,5,.8)
        rail('后庭石栏',(-13,10.8),(13,10.8),.76,22,.75)

    def palace():
        box('总统府紧凑院落底座',(0,0,.17),(26,28,.34),PAVING,'01_基础台阶',.04)
        # The three entrances are geometrically open through the front wall.
        openings=[(-7,1.13,2.2),(0,1.65,2.3),(7,1.13,2.2)]
        archwall('西式门楼三道真拱洞',24,2.0,5.3,openings,.34,(0,-11.2),mat=STONE)
        for x,r,sp in openings:
            for y in [-12.23,-10.17]:archring('门楼分缝券石',x,y,.34,r,sp,.26,.20,24,bevel=0)
            box('拱券顶石',(x,-12.35,.34+sp+r+.03),(.43,.22,.48),STONE,'04_门窗装饰',.04)
        for z,w,d,h in [(5.51,24.6,2.4,.23),(5.77,25,2.6,.21),(6.02,24.6,2.3,.28)]:box('门楼层叠檐口',(0,-11.2,z),(w,d,h),STONE,'05_栏杆线脚',.025)
        for s in [-1,1]:
            box('门楼侧女儿墙',(s*8.25,-11.2,6.47),(7.5,2.0,.76),STONE)
            box('女儿墙压顶',(s*8.25,-11.2,6.88),(7.8,2.25,.14),STONE,'05_栏杆线脚')
        for z,w,h in [(6.52,9.4,1.0),(7.12,8.1,.23),(7.40,6.9,.30),(7.61,5.6,.13)]:box('中央阶梯额墙',(0,-11.2,z),(w,2.15,h),STONE,'02_主体墙柱',.02)
        plaque('總統府',0,-12.30,6.61,5.0,.85,'plaque_1024.png')
        for s in [-1,1]:
            for x0 in [2.55,3.22,5.05,5.72,9.0,9.67,11.3]:
                x=s*x0;m=Mesh('门楼古典壁柱','02_主体墙柱',STONE,smooth=True)
                for r,z0,z1 in [(.25,.39,.58),(.20,.58,.77),(.155,.77,4.88),(.21,4.88,5.02),(.26,5.02,5.19)]:m.tube([(x,-12.3,z0),(x,-12.3,z1)],r,14)
                m.finish()
            for x0 in [4.13,10.56]:edge_trim('门楼浅浮雕线框',s*x0,-12.23,2.90,.50,3.8)
            x=s*11.45
            box('围墙石脚',(x,1.4,.70),(.55,24.6,.72),BRICK)
            box('院落白围墙',(x,1.4,1.90),(.42,24.6,1.8),STONE)
            box('回廊外檐木枋',(s*10.2,0,3.5),(2.8,20.9,.25),WOOD)
            for y in [-8.5,-5.8,-3.1,-.4,2.3,5,7.7]:
                column('回廊木柱',s*9.15,y,.36,3.0,.12)
                window('白墙花窗',s*11.20,y,1.9,1.35,1.15,-s*pi/2)
            rotated_roof('侧廊灰瓦长顶',s*10.4,0,3.65,21.8,3.5,.9,nu=24,ns=5,rows=3)
        box('接待大堂石基',(0,4.3,.64),(18.0,7.1,.60),BRICK,'01_基础台阶')
        box('接待大堂台面',(0,4.3,.98),(18.3,7.4,.15),PAVING,'01_基础台阶')
        box('接待大堂木墙',(0,4.65,2.87),(16,5.6,3.65),WOOD)
        for x in [-7.5,-5,-2.5,0,2.5,5,7.5]:
            column('大堂前后檐柱',x,.7,1.06,3.76,.18);bracket('接待堂木斗拱',x,.7,4.52)
        for x in [-6.3,-3.8,-1.3,1.3,3.8,6.3]:window('接待堂格扇门',x,1.80,2.69,1.95,3.0,door=True)
        roof('接待大堂灰瓦屋面',0,4.3,5.04,9.45,4.7,2.08,6.05,nu=26,ns=9,rows=4)
        stairs('大堂宽石阶',0,-.8,7.8,1.5,.34,1.06,7)
        box('后排堂屋白墙',(0,10.8,1.92),(15.3,3.4,3.16),STONE)
        for x in [-6,-3,0,3,6]:window('后堂格窗',x,9.08,1.95,1.8,2.3,door=x==0)
        roof('后堂灰瓦屋面',0,10.8,3.65,8.5,2.5,1.35,6.6,nu=20,ns=7,rows=3)

    def baoen():
        WHITE=material('现代塔象牙白钢构','E6E3D9',.46,coat=.12)
        GLASS=material('浅雾蓝玻璃面','8CA6AF',.28,coat=.28)
        ALT=material('浅雾蓝玻璃轻微变化','9AB1B8',.30,coat=.25)
        EDGE=material('浅色玻璃翼板','BED0D4',.32,coat=.28)
        METAL=material('银白细窗框','D8E0DC',.42)
        box('报恩塔石底座',(0,0,.16),(10,10,.32),PAVING,'01_基础台阶',.035)
        box('塔基砌石',(0,0,.47),(8.9,8.9,.30),BRICK,'01_基础台阶')
        box('塔基浅石台面',(0,0,.69),(9.05,9.05,.14),PAVING,'01_基础台阶')
        stairs('塔前浅石阶',0,-4.96,3.4,1.5,.32,.76,6)
        for s in [-1,1]:
            rail('塔基前石栏',(s*1.9,-4.4),(s*4.4,-4.4),.76,4,.68)
            rail('塔基侧石栏',(s*4.4,-4.4),(s*4.4,4.4),.76,12,.68)
        rail('塔基后石栏',(-4.4,4.4),(4.4,4.4),.76,12,.68)
        for level in range(9):
            z=.76+level*3.12;h=3.12;r=3.17-.125*level;apo=r*cos(pi/8);half=r*sin(pi/8)
            frame=Mesh('%02d层幕墙框架'%(level+1),'02_主体墙柱',METAL)
            posts=Mesh('%02d层八根主钢柱'%(level+1),'02_主体墙柱',WHITE,smooth=True)
            panels=Mesh('%02d层八面玻璃'%(level+1),'02_主体墙柱',[GLASS,ALT])
            bal=Mesh('%02d层廊台栏杆'%(level+1),'05_栏杆线脚',METAL,smooth=True)
            braces=Mesh('%02d层檐下撑杆'%(level+1),'03_屋顶或城墙',WHITE,smooth=True)
            def tr(x,y,zz,t):return (x*cos(t)-y*sin(t),x*sin(t)+y*cos(t),zz)
            for i in range(8):
                t=i*pi/4
                # Three glass panes per face; narrow mullions are geometric.
                for j in range(3):
                    x0=-half+2*half*j/3+.018;x1=-half+2*half*(j+1)/3-.018
                    panels.add([tr(x0,-apo,z+.10,t),tr(x1,-apo,z+.10,t),tr(x1,-apo,z+h-.12,t),tr(x0,-apo,z+h-.12,t)],[(0,1,2,3)],(i+j)%2)
                for xx in [-half,-half/3,half/3,half]:frame.tube([tr(xx,-apo-.015,z+.06,t),tr(xx,-apo-.015,z+h-.05,t)],.025,6)
                for zz in [z+.18,z+1.10,z+2.13,z+h-.12]:frame.tube([tr(-half,-apo-.018,zz,t),tr(half,-apo-.018,zz,t)],.023,6)
                corner=tr(half,-apo-.02,z,t);posts.tube([corner,(corner[0],corner[1],z+h)],.075,10)
                outer=apo+.49;hw=half+.20
                for zz in [z+.29,z+1.06]:bal.tube([tr(-hw,-outer,zz,t),tr(hw,-outer,zz,t)],.031,6)
                for xx in [-hw,0,hw]:bal.tube([tr(xx,-outer,z+.21,t),tr(xx,-outer,z+1.09,t)],.026,6)
                for sx in [-1,1]:braces.tube([tr(sx*half*.90,-apo-.07,z+h-1.0,t),tr(sx*(half+.25),-apo-.70,z+h-.27,t)],.059,8)
                if level==0 and i%2==0:
                    before=set(root.children)
                    archring('底层玻璃入口白石券',0,-apo-.08,.76,.67,1.40,.17,.15,20,bevel=0)
                    for o in set(root.children)-before:o.rotation_euler.z=t
            for m in [panels,frame,posts,bal,braces]:m.finish()
            ring('%02d层八角楼板'%(level+1),[(r+.47,z+.04),(r+.58,z+.12),(r+.58,z+.23),(r+.47,z+.28)],WHITE)
            ring('%02d层浅蓝翼板'%(level+1),[(r+.03,z+h-.03),(r+.25,z+h-.11),(r+.53,z+h-.30),(r+.76,z+h-.26)],EDGE)
            ring('%02d层翼板白边'%(level+1),[(r+.76,z+h-.32),(r+.76,z+h-.25),(r+.69,z+h-.22)],WHITE)
            # Delicate radial ribs make each eight-sided canopy read in silhouette.
            ribs=Mesh('%02d层翼板分格'%(level+1),'03_屋顶或城墙',WHITE)
            for j in range(24):
                t=pi/8+j*pi/12
                ribs.tube([((r+.04)*cos(t),(r+.04)*sin(t),z+h-.015),((r+.72)*cos(t),(r+.72)*sin(t),z+h-.25)],.027,6)
            ribs.finish()
        top=.76+9*3.12;rr=3.17-8*.125
        ring('塔顶八角收分罩',[(rr+.02,top-.05),(rr*.72,top+.45),(.55,top+1.5),(.31,top+1.8)],EDGE)
        cap=Mesh('塔冠八向斜梁','03_屋顶或城墙',WHITE,smooth=True)
        for i in range(8):
            t=pi/8+i*pi/4;cap.tube([(rr*cos(t),rr*sin(t),top),(.43*cos(t),.43*sin(t),top+1.7)],.075,8)
        cap.finish()
        ring('修长塔刹',[(.45,top+1.4),(.46,top+1.62),(.29,top+1.72),(.23,top+2.8),(.13,top+4.32),(.10,top+4.42)],WHITE,n=24)
        for z,r in [(top+1.70,.37),(top+2.88,.25),(top+4.43,.15)]:ring('塔刹环箍',[(r,z-.06),(r+.025,z),(r,z+.07)],GOLD,n=24)
        ball('塔顶浅金宝珠',(0,0,top+4.70),.22,GOLD,16,10)
        m=Mesh('塔尖','04_门窗装饰',GOLD,smooth=True);m.tube([(0,0,top+4.88),(0,0,top+5.80)],.028,10);m.finish()

    {'fuzimiao':dacheng,'presidential':palace,'baoen':baoen}[identifier]()
