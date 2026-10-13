"""Vybes Forge branded tent (owner Dylan Cruse, used with permission): replaces texture of the tent nearest the
racing/pit lines (tentm_SUB3, material tent_coke -> own texture tent_vybesforge.dds; other tents untouched).
UV layout (v -2..-1 => image rows 0..1): top half = roof panel triangle (apex top centre, base at row H/2),
bottom half = side walls (valance rows 512-576, alpha cut-out rows 576-840 kept from original, skirt below).
Both roof and wall faces map u -> viewer's right, so artwork is drawn unmirrored. DXT5 kept (alpha cut-out), 256 -> 1024."""
import sys,os,io,struct,numpy as np
sys.path.insert(0,os.path.dirname(__file__));import kn5patch as K,build_open_textures as B
from PIL import Image,ImageDraw,ImageFont,ImageFilter
ROOT=os.path.join(os.path.dirname(__file__),'..');SRC='/workspace/rpotm/backup/zw_rpm.kn5.pre_vftent';DST=f'{ROOT}/vf_i29_speedway/vf_i29_speedway.kn5'
FONT='/workspace/rpotm/brand/fonts/SpaceGrotesk%5Bwght%5D.ttf';LOGO=f'{ROOT}/assets_src/brand/vf_logo.jpg'
BG=(2,6,15);CY=(41,213,233);MG=(191,51,138);AM=(255,176,0);TX=(232,236,245)
N=1024;orig=Image.open(io.BytesIO(K.get_tex(SRC,'tentcok.dds'))).convert('RGBA')
alpha=np.array(orig.resize((N,N),Image.NEAREST))[...,3]
# fabric: dark base + subtle weave from original luminance
lum=np.array(orig.convert('L').resize((N,N),Image.BILINEAR)).astype(np.float32);lum=(lum-lum.mean())/max(lum.std(),1)
img=np.clip(np.array(BG,np.float32)[None,None,:]+lum[...,None]*3.0+6,0,255)
im=Image.fromarray(img.astype(np.uint8),'RGB');D=ImageDraw.Draw(im)
def font(sz,w=700):
    f=ImageFont.truetype(FONT,sz)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
def ctext(cx,cy,s,f,fill,sx=1.0,sy=1.0):  # centred text with optional anisotropic scale (compensate UV stretch)
    bb=f.getbbox(s);w,h=bb[2]-bb[0],bb[3]-bb[1];t=Image.new('RGBA',(w+8,h+8),(0,0,0,0));ImageDraw.Draw(t).text((4-bb[0],4-bb[1]),s,font=f,fill=fill)
    t=t.resize((int(t.width*sx),int(t.height*sy)),Image.LANCZOS);im.paste(t,(int(cx-t.width/2),int(cy-t.height/2)),t)
# --- roof panel (triangle apex (N/2,0), base y=N/2). roof slant ~3.5 m over 512 px vs 5.2 m over 1024 px -> squash vertically 0.74
for i,(c,o) in enumerate(((MG,0),(CY,14))):           # trim along roof base (eave)
    D.rectangle([0,N//2-30+o,N,N//2-22+o],fill=c)
lg=Image.open(LOGO).convert('RGB');s=400;lg=lg.resize((s,int(s*0.74)),Image.LANCZOS)  # VR3: bigger roof logo
yy,xx=np.mgrid[0:lg.height,0:lg.width];r=np.hypot((xx-lg.width/2)/(lg.width/2),(yy-lg.height/2)/(lg.height/2))
mask=Image.fromarray((np.clip((1.0-r)/0.18,0,1)*255).astype(np.uint8))
im.paste(lg,(N//2-lg.width//2,205),mask)  # fits inside the roof triangle (half-width at row y = y)
# roof text dropped in VR3 (logo larger; eave/valance carry the name)
# --- walls: valance (rows 512-576) and skirt (840-1024)
D.rectangle([0,N//2,N,N//2+5],fill=CY);D.rectangle([0,570,N,575],fill=MG)
ctext(N//2,543,'VYBES FORGE',font(40),TX)
D.rectangle([0,846,N,851],fill=MG);D.rectangle([0,1016,N,N],fill=CY)
ctext(N//2+60,932,'VYBES FORGE',font(64),TX)
lg2=Image.open(LOGO).convert('RGB').resize((140,140),Image.LANCZOS);yy,xx=np.mgrid[0:140,0:140];r=np.hypot(xx-70,yy-70)/70
im.paste(lg2,(N//2-60-250,862),Image.fromarray((np.clip((1-r)/0.2,0,1)*255).astype(np.uint8)))
ctext(N//2+60,988,'vybesforge.com',font(26,400),CY)
rgba=np.dstack([np.array(im),alpha]);Image.fromarray(rgba).save(f'{ROOT}/assets_src/brand/tent_vybesforge.png')
dds=B.write_dds(rgba,'DXT5',11,None)
# add texture as new blob: rename-free approach -> replace the tent_coke material's txDiffuse by splicing the texture blob
# (tentcok.dds is used only by tent_coke / tentm_SUB3; verified below)
import kn5mat as KM
CUR=DST+'.tmp';import shutil;shutil.copy(DST,CUR)
users=[m['name'] for m in KM.load(SRC)['materials'] if any(t=='tentcok.dds' for _,_,t in m['samplers'])];assert users==['tent_coke'],users
K.patch(CUR,DST,texrep={'tentcok.dds':dds});os.remove(CUR);print('tentcok.dds replaced with Vybes Forge artwork (1024 DXT5), users:',users)
