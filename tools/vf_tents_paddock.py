"""Paddock tents in Vybes Forge style (rerunnable; reads /workspace/rpotm/backup/pre_tents2/vf_i29_speedway.kn5).
- vf_i29_speedway.kn5: hide the 2 remaining zwiss big pit tents (bigtents, degenerate tris); tentm_SUB3 (VF tent) unchanged.
- new zw_tents.kn5 (MODEL_7, both layouts): copies of the VF tent model (tentm_SUB3 geometry, material based on tent_coke /
  ksPerPixelMultiMap_AT, fabric normal/maps) with own textures:
    replacements at the old big-tent spots (scaled 1.5 x/z, 1.1 y): drivenbycrusemob.com, neutral (trim only)
    3 advertising tents behind them (z 116, standard size): vybesforge.com, drivenbycrusemob.com, vybesforge.com
  Visual only like all zwiss tents (no collision). Base y = gravel height -0.10."""
import sys,os,io,struct,numpy as np
sys.path.insert(0,os.path.dirname(__file__));import kn5patch as K,kn5write as W,build_open_textures as B
from PIL import Image,ImageDraw,ImageFont
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));Z=f'{ROOT}/vf_i29_speedway';SRC='/workspace/rpotm/backup/pre_tents2/vf_i29_speedway.kn5'
FONT='/workspace/rpotm/brand/fonts/SpaceGrotesk%5Bwght%5D.ttf';LOGO=f'{ROOT}/assets_src/brand/vf_logo.jpg';OUT=f'{ROOT}/assets_src/brand'
BG=(2,6,15);CY=(41,213,233);MG=(191,51,138);AM=(255,176,0);TX=(232,236,245);N=1024;GROUND=-0.10
def meshes(path):
    d=open(path,'rb').read();_,nodes=K.scan(path)
    for name,o,l,c in nodes:
        if c!=2: continue
        q=o+l+8;nv,=struct.unpack_from('<I',d,q);V=np.frombuffer(d,'<f4',nv*11,q+4).reshape(nv,11)
        q2=q+4+nv*44;ni,=struct.unpack_from('<I',d,q2);I=np.frombuffer(d,'<u2',ni,q2+4).reshape(-1,3);yield name,V,I
def font(sz,w=700):
    f=ImageFont.truetype(FONT,sz)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
orig=Image.open(io.BytesIO(K.get_tex(SRC,'tentcok.dds'))).convert('RGBA')   # already VF art; alpha cut-out reused
alpha=np.array(orig.resize((N,N),Image.NEAREST))[...,3]
def art(kind,sx=1.0):
    """kind: cm (drivenbycrusemob.com), vfad (vybesforge.com ad), neutral. sx: horizontal text squeeze for stretched tents."""
    rng=np.random.default_rng(1);w=rng.normal(0,1,(N//4,N//4));w=np.array(Image.fromarray(((w*20)+128).clip(0,255).astype(np.uint8)).resize((N,N),Image.BILINEAR),np.float32)-128
    img=np.clip(np.array(BG,np.float32)[None,None,:]+w[...,None]*0.15+6,0,255);im=Image.fromarray(img.astype(np.uint8),'RGB');D=ImageDraw.Draw(im)
    def ctext(cx,cy,s,f,fill,tsx=1.0,tsy=1.0):
        bb=f.getbbox(s);ww,hh=bb[2]-bb[0],bb[3]-bb[1];t=Image.new('RGBA',(ww+8,hh+8),(0,0,0,0));ImageDraw.Draw(t).text((4-bb[0],4-bb[1]),s,font=f,fill=fill)
        t=t.resize((max(1,int(t.width*tsx*sx)),max(1,int(t.height*tsy))),Image.LANCZOS);im.paste(t,(int(cx-t.width/2),int(cy-t.height/2)),t);return t.width
    acc=AM if kind=='cm' else CY
    D.rectangle([0,N//2-30,N,N//2-22],fill=MG);D.rectangle([0,N//2-16,N,N//2-8],fill=acc)      # eave trim
    D.rectangle([0,N//2,N,N//2+5],fill=acc);D.rectangle([0,570,N,575],fill=MG)                  # valance
    D.rectangle([0,846,N,851],fill=MG);D.rectangle([0,1016,N,N],fill=acc)                        # skirt
    def logo(s,x,y,sy=1.0):
        lg=Image.open(LOGO).convert('RGB').resize((int(s*sx),int(s*sy)),Image.LANCZOS);yy,xx=np.mgrid[0:lg.height,0:lg.width]
        r=np.hypot((xx-lg.width/2)/(lg.width/2),(yy-lg.height/2)/(lg.height/2));im.paste(lg,(int(x-lg.width/2),int(y)),Image.fromarray((np.clip((1-r)/0.18,0,1)*255).astype(np.uint8)))
    if kind=='cm':   # text wordmark (no logo file exists): two-line, amber rule
        ctext(N//2,300,'DRIVEN BY',font(46,500),TX,tsy=0.74)
        wd=ctext(N//2,370,'CRUSE MOB',font(96,700),AM,tsy=0.74)
        D.rectangle([N//2-wd//2,410,N//2+wd//2,415],fill=TX)
        ctext(N//2,543,'DRIVEN BY CRUSE MOB',font(38),TX)
        ctext(N//2,915,'DRIVEN BY CRUSE MOB',font(60),TX);ctext(N//2,980,'drivenbycrusemob.com',font(34,500),AM)
    elif kind=='vfad':
        logo(330,N//2,240,0.74)
        ctext(N//2,543,'VYBES FORGE',font(40),TX)
        ctext(N//2,930,'vybesforge.com',font(84,700),CY);ctext(N//2,990,'VYBES FORGE',font(28,500),TX)
    elif kind=='adhere':   # VR4 placeholder advertising tent (same VF fabric/trim, no brand)
        ctext(N//2,265,'YOUR AD',font(120,700),CY,tsy=0.74)
        ctext(N//2,365,'HERE',font(120,700),TX,tsy=0.74)
        D.rectangle([N//2-180,425,N//2+180,430],fill=MG)
        ctext(N//2,543,'ADVERTISE HERE',font(38),TX)
        ctext(N//2,915,'YOUR AD HERE',font(80,700),CY);ctext(N//2,985,'ADVERTISE HERE',font(30,500),TX)
    elif kind=='neutral':
        logo(150,N//2,330,0.74)   # small mark only, plain fabric
    rgba=np.dstack([np.array(im),alpha]);Image.fromarray(rgba).save(f'{OUT}/tent_{kind}{"_wide" if sx!=1 else ""}.png')
    return B.write_dds(rgba,'DXT5',11,None)
# --- template geometry
tpl=[(V.copy(),I.copy()) for n,V,I in meshes(SRC) if n=='tentm_SUB3'][0];TV,TI=tpl
c0=np.array([(TV[:,0].min()+TV[:,0].max())/2,0,(TV[:,2].min()+TV[:,2].max())/2]);ybase=TV[:,1].min()
def place(cx,cz,s=(1,1,1)):
    V=TV.copy().astype(np.float64);s=np.array(s,float)
    V[:,0]=(V[:,0]-c0[0])*s[0]+cx;V[:,2]=(V[:,2]-c0[2])*s[2]+cz;V[:,1]=(V[:,1]-ybase)*s[1]+GROUND
    V[TV[:,1]<0.5,1]=GROUND-0.03   # skirt bottom: level, 3 cm into the gravel (vertical faces only -> no z-fight, no gap)
    n=V[:,3:6]/s;V[:,3:6]=n/np.linalg.norm(n,axis=1,keepdims=True);t=V[:,8:11]*s;V[:,8:11]=t/np.maximum(np.linalg.norm(t,axis=1,keepdims=True),1e-9)
    return V.astype('<f4')
BIG=(1.5,1.1,1.5)
TENTS=[('vftent_cm_big',60.8,67.0,BIG,'cm_wide'),('vftent_neutral_big',60.1,83.0,BIG,'neutral'),
       ('vftent_ad_vf1',46.0,116.0,(1,1,1),'vfad'),('vftent_ad_cm',60.0,116.0,(1,1,1),'cm'),('vftent_ad_vf2',74.0,116.0,(1,1,1),'vfad')]
if __name__=='__main__':
    tx={'cm':art('cm'),'cm_wide':art('cm',1/1.36),'neutral':art('neutral'),'vfad':art('vfad')}
    M=W.read_materials(SRC)['tent_coke'];texs=[(f'tent_{k}.dds',b) for k,b in tx.items()]
    for t in('fabric_nm.dds','fabric_maps.dds','NULL.dds'): texs.append((t,K.get_tex(SRC,t)))
    mats=[];mi={}
    for k in tx:
        mi[k]=len(mats);mats.append(dict(name=f'vftent_{k}',shader=M['shader'],ab=M['ab'],at=M['at'],dm=M['dm'],props=M['props'],
            samplers=[(s,sl,f'tent_{k}.dds' if s=='txDiffuse' else t) for s,sl,t in M['samplers']]))
    ms=[dict(name=n,mat_index=mi[k],verts=place(x,z,s),idx=TI,lod_out=0) for n,x,z,s,k in TENTS]
    W.write_kn5(f'{Z}/zw_tents.kn5',texs,mats,ms,rootname='zw_tents');print('zw_tents.kn5:',[m['name'] for m in ms])
    # hide remaining big tents in vf_i29_speedway.kn5 (byte splice of the index buffer only)
    d=bytearray(open(SRC,'rb').read());_,nodes=K.scan(SRC)
    for name,o,l,c in nodes:
        if c==2 and name=='bigtents':
            q=o+l+8;nv,=struct.unpack_from('<I',d,q);q2=q+4+nv*44;ni,=struct.unpack_from('<I',d,q2)
            I=np.frombuffer(bytes(d[q2+4:q2+4+ni*2]),'<u2').reshape(-1,3).copy();I[:,1]=I[:,0];I[:,2]=I[:,0];d[q2+4:q2+4+ni*2]=I.tobytes()
    open(f'{Z}/vf_i29_speedway.kn5','wb').write(bytes(d));print('bigtents hidden')
    for ini in('models_main.ini','models_short.ini'):
        p=f'{Z}/{ini}';s=open(p).read()
        if 'zw_tents.kn5' not in s: open(p,'a').write('\n[MODEL_7]\nFILE=zw_tents.kn5\nPOSITION=0,0,0\nROTATION=0,0,0\n')
