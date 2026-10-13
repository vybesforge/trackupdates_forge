"""VR7 preview: AI lines (main/long + short, fast + pit) on the NAIP aerial ground texture (google2.dds), AC top-down."""
import sys,os,io,struct,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));import kn5patch as K,kn5write as W,vr7_common as C
from PIL import Image,ImageDraw,ImageFont
Image.MAX_IMAGE_PIXELS=None
f=C.Z+'vf_i29_speedway.kn5';d=open(f,'rb').read();mats=W.read_materials(f);ml=list(mats)
X=[];U=[]
for n,o,l,c in K.scan(f)[1]:
    if c!=2: continue
    q=o+l+8;nv,=struct.unpack_from('<I',d,q);V=np.frombuffer(d,'<f4',nv*11,q+4).reshape(nv,11);q2=q+4+nv*44;ni,=struct.unpack_from('<I',d,q2);mi,=struct.unpack_from('<I',d,q2+4+ni*2)
    if any(t=='google2.dds' for _,_,t in mats[ml[mi]]['samplers']): X.append(V[:,[0,2]]);U.append(V[:,6:8])
X=np.vstack(X);U=np.vstack(U);A=np.linalg.lstsq(np.c_[X,np.ones(len(X))],U,rcond=None)[0];print('uv fit rms',np.sqrt(((np.c_[X,np.ones(len(X))]@A-U)**2).mean()))
tex=Image.open(io.BytesIO(K.get_tex(f,'google2.dds'))).convert('RGB');tw,th=tex.size;T=np.asarray(tex)
x0,x1,z0,z1,s=-270,300,-960,250,0.5   # m per px
xs=np.arange(x0,x1,s);zs=np.arange(z0,z1,s);XX,ZZ=np.meshgrid(xs,zs);uv=np.c_[XX.ravel(),ZZ.ravel(),np.ones(XX.size)]@A
pu=np.clip(((uv[:,0]%1)*tw).astype(int),0,tw-1);pv=np.clip(((uv[:,1]%1)*th).astype(int),0,th-1);img=(T[pv,pu].reshape(XX.shape+(3,))*0.75).astype(np.uint8)
F=ImageFont.truetype('/workspace/rpotm/brand/fonts/SpaceGrotesk%5Bwght%5D.ttf',26);FS=ImageFont.truetype('/workspace/rpotm/brand/fonts/SpaceGrotesk%5Bwght%5D.ttf',18)
P=lambda x,z:((x-x0)/s,(z-z0)/s)
def speedcol(v,vmax):
    t=np.clip(v/vmax,0,1);return (int(255*(1-t)),int(80+175*t),int(255*t*0.3))
panels=[]
for lay,title in(('main','LONG course (main layout)'),('short','SHORT course')):
    im=Image.fromarray(img.copy());D=ImageDraw.Draw(im,'RGBA')
    for lane,w in(('pit_lane',4),('fast_lane',5)):
        a=C.read_ai(C.Z+f'{lay}/ai/{lane}.ai');p=a['P']['p'];v=a['E'][:,0];vm=v.max()
        o=C.read_ai(f'/workspace/rpotm/project/assets_src/ai_zwiss_orig/{lay}/{lane}.ai')['P']['p']
        D.line([P(q[0],q[2]) for q in o],fill=(255,255,255,140),width=2)
        for i in range(len(p)-1): D.line([P(p[i,0],p[i,2]),P(p[i+1,0],p[i+1,2])],fill=speedcol(v[i],65 if lane=='fast_lane' else 30)+(255,) if lane=='fast_lane' else (60,160,255,255),width=w)
        D.ellipse([*(np.array(P(p[0,0],p[0,2]))-8),*(np.array(P(p[0,0],p[0,2]))+8)],outline='white',width=3)
        if lane=='fast_lane':
            for i in range(0,len(p)-8,60):
                a1=np.array(P(p[i,0],p[i,2]));b1=np.array(P(p[i+4,0],p[i+4,2]));dv=(b1-a1)/max(np.linalg.norm(b1-a1),1e-6);nn=np.r_[-dv[1],dv[0]]
                D.polygon([tuple(b1+dv*10),tuple(b1-dv*6+nn*7),tuple(b1-dv*6-nn*7)],fill=(255,255,255,230))
    D.rectangle([0,0,im.width,44],fill=(0,0,0,190));D.text((12,8),f'{title}: fast_lane coloured by speed (red slow -> green fast), pit_lane blue, zwiss 2023 lines thin white',font=FS,fill='white')
    panels.append(im)
out=Image.new('RGB',(panels[0].width*2+10,panels[0].height+50),'black')
for i,pn in enumerate(panels): out.paste(pn,(i*(pn.width+10),50))
ImageDraw.Draw(out).text((12,10),'VR7 AI lines (generated from current physics by tools/vr7_ai.py, validated by tools/vr7_ai_validate.py) on NAIP 2021 aerial',font=F,fill='white')
out=out.resize((out.width//2*1,out.height//2*1)) if out.width>3000 else out
out.save('/workspace/rpotm/docs_preview/vr7_ai.png');print(out.size)
# ---- vr7_long.png: long course (main) = full course; hairpin closed by Cones_gp + 1SCUT (off-track) overlay
import vr7_ai as AI
g=AI.Grid('main');sc=(g.kn[g.KEY]=='SCUT')
full=Image.fromarray(img.copy());D=ImageDraw.Draw(full,'RGBA')
jj,ii=np.nonzero(sc[::1,::1])
for j,i in zip(jj[::2],ii[::2]):
    x,y=P(g.xs[i],g.zs[j]);D.point((x,y),fill=(255,40,40,200))
dd=open(C.Z+'vf_i29_speedway_gp.kn5','rb').read()
for n,o,l,c in K.scan(C.Z+'vf_i29_speedway_gp.kn5')[1]:
    if n=='Cones_gp' and c==2:
        q=o+l+8;nv,=struct.unpack_from('<I',dd,q);CV=np.frombuffer(dd,'<f4',nv*11,q+4).reshape(nv,11)
        for v in CV[::10]: x,y=P(v[0],v[2]);D.ellipse([x-2,y-2,x+2,y+2],fill=(255,150,0,255))
a=C.read_ai(C.Z+'main/ai/fast_lane.ai');p=a['P']['p'];v=a['E'][:,0]
for i in range(len(p)-1): D.line([P(p[i,0],p[i,2]),P(p[i+1,0],p[i+1,2])],fill=speedcol(v[i],65)+(255,),width=4)
x,y=P(p[0,0],p[0,2]);D.ellipse([x-9,y-9,x+9,y+9],outline='white',width=3);D.text((x+12,y-10),'S/F',font=FS,fill='white')
cx0,cz0,cx1,cz1=-250,-470,-90,-350;crop=full.crop((*P(cx0,cz0),*P(cx1,cz1))).resize((int((cx1-cx0)/s*2.5),int((cz1-cz0)/s*2.5)))
D2=ImageDraw.Draw(crop);D2.rectangle([0,0,crop.width,30],fill=(0,0,0));D2.text((8,4),'T1 hairpin: red = 1SCUT_hairpin (IS_VALID_TRACK=0, long only), orange = Cones_gp',font=FS,fill='white')
ov=full.resize((full.width//2,full.height//2));outL=Image.new('RGB',(ov.width+crop.width+10,max(ov.height,crop.height)+50),'black')
outL.paste(ov,(0,50));outL.paste(crop,(ov.width+10,50))
ImageDraw.Draw(outL).text((10,10),f'VR7 LONG course = existing main layout ("I-29 Speedway Long Course"), {3.644:.3f} km centreline, AI line by speed',font=F,fill='white')
outL.save('/workspace/rpotm/docs_preview/vr7_long.png');print('long',outL.size)
