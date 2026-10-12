"""VR2 before/after previews -> /workspace/rpotm/docs_preview/vr2_*.png"""
import sys,os,io,numpy as np
sys.path.insert(0,os.path.dirname(__file__));import kn5patch as K,topview as T
from PIL import Image,ImageDraw
BK='/workspace/rpotm/backup/vr2';Z='zw_rpm';O='/workspace/rpotm/docs_preview'
def tex(kn,n): return Image.open(io.BytesIO(K.get_tex(kn,n))).convert('RGBA')
def lab(im,s):
    d=ImageDraw.Draw(im);d.rectangle([0,0,len(s)*7+10,18],fill=(0,0,0));d.text((5,3),s,fill='white');return im
def pair(a,b,ta,tb,out,bg=(140,170,200)):
    W,H=a.size;c=Image.new('RGB',(W*2+10,H),'white')
    for i,(im,t) in enumerate(((a,ta),(b,tb))):
        x=Image.new('RGB',im.size,bg);x.paste(im,(0,0),im if im.mode=='RGBA' else None);c.paste(lab(x,t),(i*(W+10),0))
    c.save(f'{O}/{out}');print(out)
g=tex(f'{BK}/zw_rpm.kn5','google2.dds').convert('RGB');crop=(1400,800,5600,3400)
def maskviz(m):
    m=np.array(m).astype(float);base=np.array(g).astype(float);o=base*0.55
    o[...,0]+=m[...,2]*0.45;o[...,1]+=m[...,0]*0.3;o[...,2]+=m[...,1]*0.3
    return Image.fromarray(np.clip(o,0,255).astype(np.uint8)).crop(crop).resize((1050,650))
pair(maskviz(tex(f'{BK}/zw_rpm.kn5','google_mask.dds')),maskviz(tex(f'{Z}/zw_rpm.kn5','google_mask.dds')),
     'BEFORE ground mask (red=B gravel detail, green=grass, blue=soil)','AFTER: infield + 18 m track border forced to grass; B now = concrete','vr2_ground_mask.png')
def tile(im,n=2,s=512):
    im=im.convert('RGB').resize((s,s));c=Image.new('RGB',(s*n,s*n))
    for i in range(n):
        for j in range(n): c.paste(im,(i*s,j*s))
    return c.resize((512,512))
pair(tile(tex(f'{BK}/zw_rpm.kn5','track_cracksa.dds')),tile(tex(f'{Z}/zw_rpm_own.kn5','own_gravel.dds')),'BEFORE paddock: Concrete01 (track_cracksa)','AFTER paddock: own_gravel (ambientCG Gravel022, desat.) + normal','vr2_paddock_texture.png')
pair(tile(tex(f'{BK}/zw_rpm.kn5','gravelroad.dds')),tile(tex(f'{Z}/zw_rpm.kn5','concrete_seams.dds')),'BEFORE road detail: gravelroad (Gravel022)','AFTER: concrete_seams (Concrete034 + joints)','vr2_road_texture.png')
pair(tex(f'{BK}/zw_vegetation.kn5','tree2.dds').resize((768,768)),tex(f'{Z}/zw_vegetation.kn5','tree2.dds').resize((768,768)),'BEFORE tree2 atlas (procedural)','AFTER tree2 atlas (Poly Haven CC0 renders)','vr2_trees_tree2.png')
pair(tex(f'{BK}/zw_vegetation.kn5','tree3.dds').resize((768,768)),tex(f'{Z}/zw_vegetation.kn5','tree3.dds').resize((768,768)),'BEFORE tree3 atlas','AFTER tree3 atlas','vr2_trees_tree3.png')
# paddock top view: before (Concrete01 everywhere) vs after (gravel mesh)
L0=[(f'{BK}/zw_rpm.kn5',lambda n:n=='1CONCRETE_001',(255,255,0,110))]
L1=[(f'{Z}/zw_rpm.kn5',lambda n:n=='1CONCRETE_001',(255,255,0,110)),(f'{Z}/zw_rpm_own.kn5',lambda n:n.startswith('1GRAVEL'),(255,120,0,130))]
T.draw(g,L0,(1850,2050,2950,2950),'/tmp/p0.png',0.6);T.draw(g,L1,(1850,2050,2950,2950),'/tmp/p1.png',0.6)
pair(Image.open('/tmp/p0.png'),Image.open('/tmp/p1.png'),'BEFORE: 1CONCRETE_001 (yellow) incl. tent lot','AFTER: 1GRAVEL_PADDOCK (orange, KEY=GRAVEL); access road stays concrete','vr2_paddock_topview.png')
