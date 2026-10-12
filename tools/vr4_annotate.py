"""VR4 preview annotation (top-down renders from tools/vr4_render_blender.py, straight-down camera, 1600 px wide).
python tools/vr4_annotate.py paddock|shortcourse raw.png out.png [inset_t1 inset_se inset_s]"""
import sys,os,json,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from PIL import Image,ImageDraw,ImageFont
from scipy import ndimage
mode,raw,out=sys.argv[1:4];im=Image.open(raw).convert('RGB');D=ImageDraw.Draw(im,'RGBA')
F=ImageFont.truetype('/workspace/rpotm/brand/fonts/SpaceGrotesk%5Bwght%5D.ttf',22);FS=ImageFont.truetype('/workspace/rpotm/brand/fonts/SpaceGrotesk%5Bwght%5D.ttf',16)
def cam(cx,cz,width):
    s=im.width/width;return lambda x,z:(im.width/2+(x-cx)*s,im.height/2+(z-cz)*s)
def lab(p,t,col=(255,255,255),f=F):
    D.text((p[0]+1,p[1]+1),t,font=f,fill=(0,0,0));D.text(p,t,font=f,fill=col)
if mode=='paddock':
    import vr4_paddock as VP,kn5tree as T;from physraster import physmeshes,raster
    P=cam(70,132,2*1500*18/180)
    box=(-45,165,30,240);M=physmeshes(['zw_rpm.kn5','zw_rpm_physical.kn5','zw_rpm_own.kn5'],box);xs,zs,H,KEY,UP,names=raster(M,box,0.5)
    g=KEY==names.index('1GRAVEL_PADDOCK');g[zs<88]=False;e=g&~ndimage.binary_erosion(g,iterations=2)
    jj,ii=np.nonzero(e)
    for j,i in zip(jj,ii): x,y=P(xs[i],zs[j]);D.rectangle([x-1,y-1,x+1,y+1],fill=(230,40,20,255))
    lab(P(100,92),'open gravel drift area (1GRAVEL_PADDOCK, drivable)',(255,120,90))
    pits=sorted([(int(n['name'][7:]),n['W']) for n in T.walk(VP.DST) if n['cls']==1 and n['name'].startswith('AC_PIT_')])
    for k,W in pits:
        p=W[3,:3];f=W[2,:3];r=W[0,:3];c=[p+a*f*2.3+b*r*1.0 for a,b in((1,1),(1,-1),(-1,-1),(-1,1))]
        D.polygon([P(q[0],q[2]) for q in c],fill=(40,230,60,230),outline=(0,0,0))
        if k in(0,17,18,35): lab(P(p[0]-2,p[2]+(3.5 if k<18 else 3.5)),str(k),f=FS)
    lab(P(8,62),'36 AC_PIT spawns: 2 staggered rows, facing north (PIT 0 = west end)',(120,255,120))
    if os.path.exists('path_main.npy'):
        pa=np.load('path_main.npy');D.line([P(x,z) for x,z in pa],fill=(40,220,255,255),width=4);lab(P(-80,52),'exit -> pit-exit gate',(40,220,255))
    names_={'vfad':'vybesforge.com','cm':'drivenbycrusemob.com','adhere':'Your Ad Here'}
    for n,x,z,k in VP.TENTS: lab(P(x-12,z+6),names_[k],(255,230,120) if k!='adhere' else (220,220,220),FS)
else:
    P=cam(20,-210,2*1500*18/103)
    ZN=json.load(open(os.path.join(os.path.dirname(__file__),'vr4_shortcourse_zones.json')))
    for n,pts in ZN.items():
        a=np.array(pts);x0,z0=a.min(0)-8;x1,z1=a.max(0)+8;D.rectangle([P(x0,z0),P(x1,z1)],outline=(200,60,255),width=4)
        lab(P(x0,z1+2),{'T1_hairpin':'T1 hairpin (short-course link)','pit_in_SE':'SE pit-in branch','pit_out_S':'S pit-out merge'}[n],(230,150,255))
    lab(P(-230,-110),'T5 (VR3)',(230,150,255))
    lab((20,20),'exit-road asphalt overlays (drag_exit_asphalt), physics unchanged',(255,255,255))
if mode!='paddock' and len(sys.argv)>4:   # optional close-up insets appended below (T1, SE, S)
    ins=[Image.open(f).convert('RGB').resize((im.width//3,im.width//3*1000//1600)) for f in sys.argv[4:7]];h=ins[0].height
    c=Image.new('RGB',(im.width,im.height+h));c.paste(im,(0,0))
    for i,t in enumerate(ins): c.paste(t,(i*(im.width//3),im.height))
    D2=ImageDraw.Draw(c)
    for i,t in enumerate(['T1 hairpin (close-up)','SE pit-in (close-up)','S pit-out (close-up)']): D2.text((i*(im.width//3)+10,im.height+8),t,font=F,fill=(255,255,255))
    im=c
im.save(out);print(out)
