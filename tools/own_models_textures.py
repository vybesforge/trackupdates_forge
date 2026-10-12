import sys,os,numpy as np,cv2
sys.path.insert(0,os.path.dirname(__file__))
import build_open_textures as B
from PIL import Image,ImageDraw,ImageFont
OUT=os.path.join(os.path.dirname(__file__),'..','assets_src','textures')
def save(name,rgb,a=None,fmt='DXT1'):
    h,w=rgb.shape[:2];a=np.full((h,w),255,np.uint8) if a is None else a
    rgba=np.dstack([rgb[...,:3],a]).astype(np.uint8);mips=int(np.log2(max(w,h)))+1
    open(f'{OUT}/{name}.dds','wb').write(B.write_dds(rgba,fmt,mips,None));Image.fromarray(rgba).save(f'{OUT}/{name}.png')
t=B.tint;f=B.fit;cc=B.cc
save('own_tower_paint',t(f(cc('PaintedPlaster017'),1024,1024),(150,195,225),0.85))
save('own_tower_paint_nm',f(cc('PaintedPlaster017','NormalDX'),1024,1024))
g=np.zeros((512,512,3),np.float32);yy=np.linspace(0,1,512)[:,None];g[...]=np.dstack([40+50*yy,50+60*yy,60+70*yy]);save('own_tower_glass',g.astype(np.uint8))
save('own_galv',np.clip(f(cc('Metal032'),1024,1024)*1.1,0,255).astype(np.uint8))
save('own_alu',np.clip(f(cc('Metal032'),1024,1024)*1.25+15,0,255).astype(np.uint8))
save('own_hut_white',t(f(cc('PaintedPlaster017'),1024,1024),(235,235,232),0.9))
save('own_awning',np.clip(t(f(cc('Fabric026'),1024,1024),(230,230,225),0.85).astype(np.float32)*0.5+120,0,255).astype(np.uint8))
# brake boards atlas: black panels, white numerals 3 | 2 | 1
W,H=1536,512;im=Image.new('RGB',(W,H),(14,14,14));d=ImageDraw.Draw(im)
try: font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',380)
except Exception: font=ImageFont.load_default(380)
for i,n in enumerate('321'):
    cx=i*W/3+W/6;bb=d.textbbox((0,0),n,font=font);d.text((cx-(bb[2]-bb[0])/2-bb[0],H/2-(bb[3]-bb[1])/2-bb[1]),n,fill=(245,245,245),font=font)
arr=np.array(im);arr=cv2.resize(arr,(2048,512));save('own_boards',arr)
# US flag (public-domain design), 1024x512
w,h=1024,512;fl=Image.new('RGB',(w,h));d=ImageDraw.Draw(fl)
for i in range(13): d.rectangle([0,i*h/13,w,(i+1)*h/13],fill=(178,34,52) if i%2==0 else (255,255,255))
cw,ch=w*0.4,h*7/13;d.rectangle([0,0,cw,ch],fill=(60,59,110))
for r in range(9):
    for c in range(6 if r%2==0 else 5):
        x=(c*2+(1 if r%2 else 0)+1)*cw/12;y=(r+1)*ch/10;d.regular_polygon((x,y,7),5,fill='white')
save('own_flag',np.array(fl))
print(sorted(os.listdir(OUT)))
