"""Compact, tree-free Jiming, Nanjing Zifeng and Yuejiang concept geometry."""
import math
from math import sin,cos,pi
import bpy
import numpy as np

def build(identifier,a):
    Mesh=a['Mesh'];box=a['box'];roof=a['roof'];rail=a['rail'];stairs=a['stairs'];window=a['window'];column=a['column']
    STONE=a['STONE'];RED=a['RED'];WOOD=a['WOOD'];TEAL=a['TEAL'];GOLD=a['GOLD'];DARK=a['DARK']
    TILE=a['TILE'];TILEBASE=a['TILEBASE'];BRICK=a['BRICK'];PAVING=a['PAVING'];PAINT=a['PAINT'];material=a['material']
    YELLOW=material('鸡鸣寺赭黄粉墙','D7A04D',.86)
    if identifier in ['jiming','yuejiang']:
        yy,xx=np.mgrid[:1024,:1024];u=xx/1024;v=yy/1024;row=np.floor(v*24)
        seam=(v*24%1<.045)|((u*12+row*.5)%1<.025)
        rgb=np.array([61,68,72] if identifier=='jiming' else [171,116,43],dtype=float)/255
        variation=1-.10*seam+.018*np.sin(xx*.17+yy*.13)
        pixels=np.ones((1024,1024,4),np.float32);pixels[:,:,:3]=rgb*variation[:,:,None]
        im=bpy.data.images.new('细瓦搭接纹理',width=1024,height=1024,alpha=False);im.pixels.foreach_set(pixels.ravel());im.filepath_raw=str(a['OUT']/'roof_tiles_1024.png');im.file_format='PNG';im.save();im.pack()
        n=TILEBASE.node_tree.nodes;tex=n.new('ShaderNodeTexImage');tex.image=im;bs=next(n for n in n if n.type=='BSDF_PRINCIPLED');TILEBASE.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])

    def beam(m,p,q,width,depth=None,mi=0):
        # A rectangular beam in any horizontal direction, with no hidden subdivisions.
        depth=depth or width;dx=q[0]-p[0];dy=q[1]-p[1];length=math.hypot(dx,dy)
        if length<1e-6:return
        nx=-dy/length*width/2;ny=dx/length*width/2
        vs=[(v[0]+s*nx,v[1]+s*ny,v[2]+z*depth/2) for v,s,z in [(p,-1,-1),(q,-1,-1),(q,1,-1),(p,1,-1),(p,-1,1),(q,-1,1),(q,1,1),(p,1,1)]]
        m.add(vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mi)

    def polygon_prism(name,ring,z0,z1,mat,col='02_主体墙柱'):
        m=Mesh(name,col,mat);n=len(ring);tops=[z1]*n if isinstance(z1,(int,float)) else z1
        m.add([(x,y,z0) for x,y in ring]+[(x,y,z) for (x,y),z in zip(ring,tops)],
            [tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)])
        return m.finish()

    def octagon(cx,cy,r):return [(cx+r*cos(pi/8+i*pi/4),cy+r*sin(pi/8+i*pi/4)) for i in range(8)]

    def ornament(name,x,y,z,height,mat=GOLD):
        m=Mesh(name,'04_门窗装饰',mat,smooth=True)
        profile=[(0,.20),(.12,.29),(.24,.20),(.32,.11),(.42,.24),(.55,.12),(.64,.18),(.76,.08),(1,.012)]
        n=10;vs=[(x+r*height*.65*cos(i*2*pi/n),y+r*height*.65*sin(i*2*pi/n),z+t*height) for t,r in profile for i in range(n)]
        m.add(vs,[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(len(profile)-1) for i in range(n)])
        m.finish()

    def pagoda_eave(name,cx,cy,z,inner,outer,height):
        surface=Mesh(name+'八角曲面瓦底','03_屋顶或城墙',TILEBASE)
        ribs=Mesh(name+'瓦垄翘脊','03_屋顶或城墙',TILE,smooth=True)
        steps=3;sub=3
        def point(side,u,t):
            p=pi/8+side*pi/4;q=p+pi/4;r=inner+(outer-inner)*t
            x=(1-u)*cos(p)+u*cos(q);y=(1-u)*sin(p)+u*sin(q)
            corner=abs(u*2-1)**6
            return (cx+r*x,cy+r*y,z+height*(1-t)**1.7+.20*corner*t**3)
        for side in range(8):
            surface.add([point(side,i/sub,j/steps) for j in range(steps+1) for i in range(sub+1)],[(j*(sub+1)+i,j*(sub+1)+i+1,(j+1)*(sub+1)+i+1,(j+1)*(sub+1)+i) for j in range(steps) for i in range(sub)])
            for i in range(sub):ribs.tube([tuple(v+(0 if k<2 else .035) for k,v in enumerate(point(side,i/sub,j/steps))) for j in range(steps+1)],.055,4)
            ribs.tube([point(side,i/3,1) for i in range(4)],.085,4)
        o=surface.finish();solid=o.modifiers.new('瓦檐厚度','SOLIDIFY');solid.thickness=.06;ribs.finish()

    def pagoda_window(name,cx,cy,r,z,height,side):
        angle=pi/8+(side+.5)*pi/4;nx,ny=cos(angle),sin(angle);tx,ty=-ny,nx;radius=.34
        profile=[(-radius,0),(radius,0),(radius,height-radius)]+[(radius*cos(j*pi/8),height-radius+radius*sin(j*pi/8)) for j in range(1,9)]
        m=Mesh(name,'04_门窗装饰',[WOOD,GOLD])
        pts=[(cx+nx*r+tx*x,cy+ny*r+ty*x,z+zz) for x,zz in profile];m.add(pts,[tuple(range(len(pts)))])
        # Slim raised frame around the arch; the door remains shut.
        m.tube(pts+[pts[0]],.04,4,1)
        m.tube([(cx+nx*(r+.02),cy+ny*(r+.02),z+.05),(cx+nx*(r+.02),cy+ny*(r+.02),z+height-.10)],.025,4)
        m.finish()

    def jiming():
        box('鸡鸣寺紧凑基座',(0,0,.18),(24,16,.36),PAVING,'01_基础台阶',.035)
        box('寺院石台',(0,.35,.75),(23,14.7,.82),BRICK,'01_基础台阶')
        box('平台压顶',(0,.35,1.20),(23.3,15,.18),PAVING,'01_基础台阶')
        stairs('主殿前石阶',-3.6,-7.96,6.5,2.45,.36,1.3,9)
        # The low hall stays to the left of the seven-storey medicine pagoda.
        box('黄墙大殿',(-3.7,-.2,3.5),(12.4,8,4.4),YELLOW,bevel=.025)
        for x in [-8.9,-6.3,-3.7,-1.1,1.5]:
            column('主殿前檐朱柱',x,-4.65,1.3,4.65,.21)
            window('殿门红木格扇',x,-4.24,3.1,1.85,3.0,door=True)
        for side in [-1,1]:
            for y in [-2,1.3]:window('大殿侧窗',-3.7+side*6.24,y,3.7,1.65,2.3,side*pi/2)
        roof('大殿下檐',-3.7,-.2,6.0,7.35,5,1.05,4.8,nu=18,ns=7,rows=3)
        box('重檐间黄墙',(-3.7,-.2,7.05),(10.7,6.1,1.55),YELLOW)
        roof('大殿上檐',-3.7,-.2,7.65,6.75,4.1,2.05,4.2,nu=18,ns=7,rows=4)
        # One connecting cloister leaves the front of the pagoda visible.
        box('东侧庑墙',(7,-4.1,2.8),(7,2.1,3.0),YELLOW)
        for x in [4.2,6.3,8.4,10.3]:column('东廊朱柱',x,-5.4,1.3,2.85,.15)
        roof('东廊灰瓦',7,-4.1,4.4,4,1.8,.85,2.5,nu=10,ns=4,rows=3)
        cx,cy=6.8,3.2
        polygon_prism('塔基八角须弥座',octagon(cx,cy,3.3),1.29,1.75,STONE,'01_基础台阶')
        for j in range(7):
            z=1.75+j*2.95;r=2.48-j*.075
            polygon_prism('药师塔第%d层黄墙'%(j+1),octagon(cx,cy,r),z,z+2.35,YELLOW)
            polygon_prism('第%d层回廊板'%(j+1),octagon(cx,cy,r+.48),z,z+.14,STONE if j==0 else WOOD,'05_栏杆线脚')
            m=Mesh('第%d层红栏杆'%(j+1),'05_栏杆线脚',RED)
            corners=octagon(cx,cy,r+.40)
            for k in range(8):
                p=corners[k];q=corners[(k+1)%8]
                for t in [0,.5]:m.box((p[0]*(1-t)+q[0]*t,p[1]*(1-t)+q[1]*t,z+.50),(.10,.10,.82))
                for h in [.35,.90]:beam(m,(*p,z+h),(*q,z+h),.075)
                pagoda_window('第%d层弧窗'%(j+1),cx,cy,r*cos(pi/8)+.015,z+.18,1.55,k)
            m.finish()
            pagoda_eave('第%d层塔檐'%(j+1),cx,cy,z+2.35,r-.10 if j<6 else .03,r+.77,.78 if j<6 else 1.10)
        ornament('药师佛塔塔刹',cx,cy,22.90,2.4)
        for x in [-11.25,11.25]:rail('寺院侧石栏',(x,-6.6),(x,7.4),1.3,12,.74)
        rail('寺院后石栏',(-11.25,7.4),(11.25,7.4),1.3,18,.74)
        for x0,x1 in [(-11.25,-7.4),(.2,11.25)]:rail('殿前台栏',(x0,-6.6),(x1,-6.6),1.3,7,.74)

    def gable_crown(cx,cy,z,aa,bb,height):
        # Upper gable above the lower hipped skirt, giving a readable xieshan crown.
        roof('顶层歇山下围檐',cx,cy,z,aa,bb,.95,aa*.70,nu=16,ns=6,rows=3)
        az=aa*.72;bz=bb*.57;base=z+.64
        surf=Mesh('歇山上部双坡','03_屋顶或城墙',TILEBASE);ribs=Mesh('歇山上瓦垄','03_屋顶或城墙',TILE,smooth=True)
        def p(u,t,s):return (cx+u*az,cy+s*bz*t,base+height*(1-t)**1.55+.19*abs(u)**8*t**4)
        for s in [-1,1]:
            n=18;steps=4;surf.add([p(-1+2*i/n,j/steps,s) for j in range(steps+1) for i in range(n+1)],[(j*(n+1)+i,j*(n+1)+i+1,(j+1)*(n+1)+i+1,(j+1)*(n+1)+i) for j in range(steps) for i in range(n)])
            for i in range(n+1):ribs.tube([p(-1+2*i/n,j/steps,s) for j in range(steps+1)],.067,5)
            ribs.tube([p(-1+2*i/8,1,s) for i in range(9)],.11,6)
        ribs.tube([(cx-az,cy,base+height+.06),(cx+az,cy,base+height+.06)],.14,8)
        for sign in [-1,1]:
            g=Mesh('歇山山花','04_门窗装饰',[RED,GOLD]);x=cx+sign*(az-.06)
            g.add([(x,cy-bz,base),(x,cy+bz,base),(x,cy,base+height-.02)],[(0,1,2)])
            for side in [-1,1]:g.tube([(x,cy+side*bz*t,base+height*(1-t)**1.55) for t in [0,.2,.4,.6,.8,1]],.07,5,1)
            g.finish();ornament('屋脊吻兽',cx+sign*az,cy,base+height+.08,.75)
        o=surf.finish();o.modifiers.new('上檐厚度','SOLIDIFY').thickness=.065;ribs.finish()

    def yuejiang():
        def column(name,x,y,z,h,r):
            m=Mesh(name,'02_主体墙柱',[RED,STONE]);m.tube([(x,y,z+.15),(x,y,z+h)],r,8)
            m.box((x,y,z+.08),(r*2.6,r*2.6,.16),1);m.box((x,y,z+h),(r*2.4,r*2.4,.13));return m.finish()
        def window(name,x,y,z,w,h,angle=0,door=False):
            m=Mesh(name,'04_门窗装饰',[WOOD,TEAL]);m.box((0,0,0),(w,.09,h))
            for dx in [-w/2,w/2]:m.box((dx,-.07,0),(.09,.12,h+.12))
            for dz in [-h/2,h/2]:m.box((0,-.07,dz),(w,.12,.09))
            for dx in [-w*.25,0,w*.25]:m.box((dx,-.07,.18),(.032,.12,h*.65),1)
            m.box((0,-.08,.25),(w,.12,.04),1)
            o=m.finish();o.location=(x,y,z);o.rotation_euler.z=angle;return o
        box('阅江楼石台底座',(0,0,.21),(24,19,.42),PAVING,'01_基础台阶',.04)
        box('高台石砌',(0,.6,.98),(23,16.8,1.12),BRICK,'01_基础台阶')
        box('高台面石',(0,.6,1.61),(23.3,17.1,.18),PAVING,'01_基础台阶')
        stairs('正面登楼阶',-3.8,-9.45,6.3,2.5,.42,1.7,11)
        cx,cy=-3.0,1.3
        for j,(w,d) in enumerate([(14.2,11.1),(13.3,10.5),(12.3,9.7),(11.4,8.8)]):
            z=1.70+j*5.45
            box('阅江楼第%d层朱墙'%(j+1),(cx,cy,z+1.85),(w-2.4,d-2.4,3.7),RED)
            box('第%d层楼板'%(j+1),(cx,cy,z+.02),(w+.2,d+.2,.20),STONE)
            for side in [-1,1]:
                for i in range(5):
                    x=cx+(i-2)*(w-1)/4;column('各层外廊朱柱',x,cy+side*d/2,z+.13,3.75,.18)
                    if i<4:window('各层正背格扇',cx+(i-1.5)*(w-2.5)/4,cy+side*(d/2-1.16),z+2.0,(w-3)/4-.16,2.75,pi if side==1 else 0,door=True)
                for k in [-1,0,1]:
                    y=cy+k*(d-1)/3;column('侧廊朱柱',cx+side*w/2,y,z+.13,3.75,.18)
                    window('侧向格窗',cx+side*(w/2-1.16),y,z+2.0,1.8,2.6,side*pi/2)
            if j>0:
                for side in [-1,1]:
                    rail('楼层前后栏杆',(cx-w/2,cy+side*d/2),(cx+w/2,cy+side*d/2),z+.15,11,.78)
                    rail('楼层侧栏',(cx+side*w/2,cy-d/2),(cx+side*w/2,cy+d/2),z+.15,8,.78)
            if j<3:roof('第%d重金瓦飞檐'%(j+1),cx,cy,z+4.0,w/2+1.25,d/2+1.15,1.25,w*.34,nu=12,ns=4,rows=3)
            else:
                roof('顶层重檐下檐',cx,cy,z+4.0,w/2+1.2,d/2+1.0,1.10,w*.33,nu=15,ns=6,rows=3)
                gable_crown(cx,cy,z+5.15,w/2+.65,d/2+.55,2.1)
        box('相连侧翼朱墙',(8.25,-.5,3.55),(5.6,10.6,3.7),RED)
        for y in [-4.8,-2.6,-.4,1.8,4]:
            column('侧翼外廊柱',11.1,y,1.7,3.85,.17)
            window('侧翼格窗',11.08,y,3.7,1.6,2.7,pi/2)
        roof('侧翼金瓦',8.1,-.5,5.75,3.3,6.1,1.6,1.7,nu=10,ns=9,rows=3)
        for x in [-11.25,11.25]:rail('高台侧石栏',(x,-7.8),(x,8.5),1.72,12,.85)
        rail('高台后石栏',(-11.25,8.5),(11.25,8.5),1.72,17,.85)
        for p,q in [((-11.25,-7.8),(-7.3,-7.8)),((-.2,-7.8),(11.25,-7.8))]:rail('高台前石栏',p,q,1.72,7,.85)

    def facade_material():
        # A reusable fine window grid; broader seams are actual silhouette geometry.
        w=h=1024;yy,xx=np.mgrid[:h,:w];u=xx/w;v=yy/h
        grid=(np.minimum(u%(.125),.125-u%(.125))<.002)|(np.minimum(v%(.125),.125-v%(.125))<.003)
        tint=.93+.06*np.sin(np.floor(u*8)*1.7+np.floor(v*8)*2.1)
        pixels=np.ones((h,w,4),np.float32);pixels[:,:,:3]=np.array([.29,.43,.53])*tint[:,:,None];pixels[grid,:3]=[.52,.61,.66]
        im=bpy.data.images.new('蓝灰玻璃窗格',width=w,height=h,alpha=False);im.pixels.foreach_set(pixels.ravel());im.filepath_raw=str(a['OUT']/'facade_1024.png');im.file_format='PNG';im.save();im.pack()
        mat=material('蓝灰玻璃幕墙','FFFFFF',.30,coat=.3);n=mat.node_tree.nodes;bs=next(n for n in n if n.type=='BSDF_PRINCIPLED');bs.inputs['Metallic'].default_value=.15;tex=n.new('ShaderNodeTexImage');tex.image=im;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);return mat

    def zifeng():
        GLASS=facade_material();SILVER=material('银灰铝框','A7B5BF',.34);DEEP=material('幕墙深色退缝','405569',.45);BEIGE=material('浅米石材裙房','D7CAB5',.75)
        box('紫峰广场石底座',(0,0,.18),(20,16,.36),PAVING,'01_基础台阶',.045)
        box('首层平台',(0,.1,.43),(19,14.9,.18),STONE,'01_基础台阶')
        stairs('前入口台阶',0,-7.9,6,1,.36,.55,4)

        def glazed_volume(name,ring,z0,tops,spacing=.92,bays=8):
            top=[tops]*len(ring) if isinstance(tops,(int,float)) else tops
            polygon_prism(name+'深色芯体',ring,z0,top,DEEP)
            panels=Mesh(name+'分层玻璃面','02_主体墙柱',GLASS)
            frames=Mesh(name+'竖框与横向楼层线','05_栏杆线脚',SILVER)
            for i,p in enumerate(ring):
                q=ring[(i+1)%len(ring)];h0=top[i];h1=top[(i+1)%len(ring)];dx=q[0]-p[0];dy=q[1]-p[1];length=math.hypot(dx,dy);nx=dy/length;ny=-dx/length
                def pt(u,z,out=.028):return(p[0]+u*dx+nx*out,p[1]+u*dy+ny*out,z)
                n=max(2,round(length*bays/7))
                for j in range(n):
                    u0=(j+.025)/n;u1=(j+.975)/n;cap0=h0+(h1-h0)*u0;cap1=h0+(h1-h0)*u1
                    for k in range(math.ceil((max(h0,h1)-z0)/spacing)):
                        low=z0+k*spacing+.025;hi0=min(low+spacing-.06,cap0-.03);hi1=min(low+spacing-.06,cap1-.03)
                        if min(hi0,hi1)<=low:continue
                        panels.add([pt(u0,low),pt(u1,low),pt(u1,hi1),pt(u0,hi0)],[(0,1,2,3)])
                for j in range(n+1):
                    u=j/n;h=h0+(h1-h0)*u;v=pt(u,(z0+h)/2,.065)
                    frames.box(v,(.055,.055,h-z0))
                for k in range(math.ceil((max(h0,h1)-z0)/spacing)+1):
                    z=z0+k*spacing
                    if z>max(h0,h1):continue
                    lo,hi=0.,1.
                    if z>min(h0,h1):
                        t=(z-h0)/(h1-h0)
                        if h1>h0:lo=max(0,t)
                        else:hi=min(1,t)
                    if hi>lo:beam(frames,pt(lo,z,.065),pt(hi,z,.065),.09,.055)
                # Accent the corners and sloping tops with a thicker silver seam.
                frames.tube([pt(0,z0,.07),pt(0,h0,.07)],.052,6)
                frames.tube([pt(0,h0,.07),pt(1,h1,.07)],.06,6)
            panels.finish();frames.finish()

        main=[(-4.0,-2.8),(-1.7,-4.0),(2.7,-2.5),(3.4,1.2),(0,4.1),(-3.8,2.1)]
        glazed_volume('主塔三角折面',main,4.3,[58,59,62,64,64,59],bays=10)
        glazed_volume('西侧低退台',[(-6,-2.9),(-3.7,-3.4),(-3.7,2.2),(-6,1.5)],4.3,[29,30,30,29],bays=7)
        glazed_volume('东侧中退台',[(2.4,-2.5),(5.1,-1.0),(5.1,3.2),(2.4,3.5)],4.3,[43,41,43,44],bays=8)
        glazed_volume('北侧高退台',[(-1.4,1.2),(1.4,.6),(2.4,2.8),(-.2,4.3)],4.3,[69,72,73,70],bays=7)
        glazed_volume('顶冠细塔',[(-.35,2.25),(.9,1.9),(1.7,3.15),(.35,3.65)],69.0,[76.5,77.3,77.3,76.5],spacing=.7,bays=6)
        mast=Mesh('偏置尖顶与竖向冠框','04_门窗装饰',SILVER,smooth=True)
        for x,y,z,h,r in [(.8,2.8,76.8,6.0,.10),(-.15,2.5,74.0,4.1,.085),(1.4,3.1,75,3.2,.075)]:mast.tube([(x,y,z),(x,y,z+h)],r,10)
        mast.finish()
        # Connected, compact stone retail podium, never a surrounding city block.
        for name,x,y,w,d,h in [('西裙楼',-6.4,-.1,5,11.8,6.0),('前大堂',-.4,-4.9,8,3.5,4.5),('东裙楼',6.5,.1,5.2,11.3,4.8)]:
            box(name+'米色石体',(x,y,.55+h/2),(w,d,h),BEIGE)
            box(name+'屋顶压边',(x,y,.55+h),(w+.12,d+.12,.18),STONE,'05_栏杆线脚')
            for side in [-1,1]:
                for k in range(max(3,round(w/.8))):
                    px=x-w/2+.45+k*(w-.9)/(max(3,round(w/.8))-1)
                    box(name+'竖向橱窗',(px,y+side*(d/2+.016),.65+h*.47),(.56,.045,h*.76),GLASS,'04_门窗装饰')
                for k in range(round(d/.85)):
                    py=y-d/2+.45+k*(d-.9)/(round(d/.85)-1)
                    box(name+'侧向橱窗',(x+side*(w/2+.016),py,.65+h*.47),(.045,.56,h*.76),GLASS,'04_门窗装饰')
            for z in [2.55,4.55]:
                if z<h:box(name+'石材横檐',(x,y,z),(w+.09,d+.09,.13),BEIGE,'05_栏杆线脚')
        box('正门雨棚',(0,-7.0,2.55),(4.8,1.35,.16),GOLD,'04_门窗装饰')
        for x in [-2,-.7,.7,2]:box('雨棚支柱',(x,-7.45,1.52),(.11,.11,2.0),SILVER,'02_主体墙柱')

    {'jiming':jiming,'zifeng':zifeng,'yuejiang':yuejiang}[identifier]()
