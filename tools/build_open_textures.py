"""Build CC0/procedural replacements for medium/high/unknown-risk textures. Run with venv python."""
import json,io,struct,glob,os,sys,math
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFilter
sys.path.insert(0,os.path.dirname(__file__));import kn5patch as k
CC='/workspace/rpotm/cc0';OUT='/workspace/rpotm/tex/new';PROJ=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rng=np.random.default_rng(29)
def cc(id,m='Color'):
    f=glob.glob(f'{CC}/{id}/*_{m}.jpg')[0];return np.array(Image.open(f).convert('RGB'))
def fit(img,w,h):  # tile/crop to aspect then resize
    H,W=img.shape[:2];ta=w/h
    if W/H>ta: nw=int(H*ta);img=img[:, :nw]
    else: nh=int(W/ta);img=img[:nh]
    return cv2.resize(img,(w,h),interpolation=cv2.INTER_AREA)
def noise(w,h,scale=32,oct=4):
    acc=np.zeros((h,w),np.float32);a=1
    for o in range(oct):
        s=max(2,int(scale/(2**o)));n=rng.random((h//s+2,w//s+2)).astype(np.float32)
        acc+=a*cv2.resize(n,(w,h),interpolation=cv2.INTER_CUBIC)[:h,:w];a*=0.5
    acc-=acc.min();return acc/acc.max()
def h2n(hgt,strength=4):
    hgt=np.asarray(hgt,np.float32)
    gx=cv2.Sobel(hgt,cv2.CV_32F,1,0,ksize=3);gy=cv2.Sobel(hgt,cv2.CV_32F,0,1,ksize=3)
    n=np.dstack([-gx*strength,gy*strength,np.ones_like(hgt)]);n/=np.linalg.norm(n,axis=2,keepdims=True)
    return ((n*0.5+0.5)*255).astype(np.uint8)
def tint(img,rgb,amt=1.0):
    l=img.mean(2,keepdims=True)/255.0;t=np.array(rgb,np.float32)*l*(1.2)
    return np.clip(img*(1-amt)+t*amt,0,255).astype(np.uint8)
def coarse(orig,w,h,f):  # orig colour layout at very low res only
    small=cv2.resize(orig,(max(2,orig.shape[1]//f),max(2,orig.shape[0]//f)),interpolation=cv2.INTER_AREA)
    return cv2.resize(small,(w,h),interpolation=cv2.INTER_CUBIC)
def atlas(orig,w,h,detail,f=16):
    base=coarse(orig[...,:3].astype(np.float32),w,h,f);d=fit(detail,w,h).astype(np.float32);dl=d.mean(2,keepdims=True)/d.mean()
    return np.clip(base*(0.75+0.25*dl),0,255).astype(np.uint8)
def coarse_alpha(a,w,h,f):
    s=cv2.resize(a.astype(np.float32),(max(2,a.shape[1]//f),max(2,a.shape[0]//f)),interpolation=cv2.INTER_AREA)
    return cv2.resize(s,(w,h),interpolation=cv2.INTER_CUBIC)
def write_dds(rgba,fmt,mips,orighdr):
    im=Image.fromarray(rgba,'RGBA');w,h=im.size
    if fmt in('DXT1','DXT3','DXT5'):
        lv=[]
        for i in range(mips):
            b=io.BytesIO();im.resize((max(1,w>>i),max(1,h>>i)),Image.LANCZOS).save(b,'DDS',pixel_format=fmt);bb=b.getvalue();lv.append((bb[:128],bb[128:]))
        hdr=bytearray(lv[0][0])
        if mips>1:
            struct.pack_into('<I',hdr,8,struct.unpack_from('<I',hdr,8)[0]|0x20000);struct.pack_into('<I',hdr,28,mips);struct.pack_into('<I',hdr,108,struct.unpack_from('<I',hdr,108)[0]|0x400008)
        return bytes(hdr)+b''.join(x[1] for x in lv)
    # uncompressed: reuse original pixel format masks, 32bpp assumed
    hdr=bytearray(orighdr);bits=struct.unpack_from('<I',hdr,88)[0];rm,gm,bm,am=struct.unpack_from('<4I',hdr,92)
    struct.pack_into('<II',hdr,12,h,w);struct.pack_into('<I',hdr,16+4,0) if False else None
    struct.pack_into('<I',hdr,20,w*bits//8);struct.pack_into('<I',hdr,28,1)
    px=np.zeros((h,w),np.uint32)
    for ch,m in zip(range(4),(rm,gm,bm,am)):
        if m: sh=(m&-m).bit_length()-1;px|=(rgba[...,ch].astype(np.uint32)<<sh)&m
    assert bits==32,bits
    return bytes(hdr)+px.astype('<u4').tobytes()
def info(b):
    h,w=struct.unpack_from('<II',b,12);mm=max(1,struct.unpack_from('<I',b,28)[0]);fc=b[84:88].decode('latin1')
    return w,h,mm,(fc if fc.startswith('DXT') else 'RAW')
def pot(x): return x&(x-1)==0
# ---------------- recipes ----------------
def R(name,w,h,orig):
    """returns (rgb uint8 HxWx3, alpha HxW or None, source, license, note)"""
    o=orig;oa=o[...,3]; A0=None
    CC0='CC0 1.0 https://docs.ambientcg.com/license/'
    PROC='CC0 1.0 (procedural, project-made) https://creativecommons.org/publicdomain/zero/1.0/'
    s=lambda *ids:'ambientCG '+', '.join(ids)
    if name=='metal_001.dds': return fit(cc('Metal032'),w,h),None,s('Metal032'),CC0,''
    if name=='metal1.dds': return (fit(cc('Metal032'),w,h)*0.45).astype(np.uint8),None,s('Metal032'),CC0,'darkened'
    if name=='metal_blanco.dds': return np.clip(fit(cc('Metal032'),w,h)*1.25+20,0,255).astype(np.uint8),None,s('Metal032'),CC0,'brightened (grandstand seats)'
    if name=='glass2.dds': return np.full((h,w,3),(70,85,95),np.uint8),np.full((h,w),int(oa.mean()),np.uint8),'procedural',PROC,'flat glass tint, alpha level kept as a number'
    if name=='concretebasic6m.dds': return fit(cc('Concrete034'),w,h),None,s('Concrete034'),CC0,''
    if name in('concwalla_n.dds','concwallc_n.dds'): return fit(cc('Concrete034','NormalDX'),w,h),None,s('Concrete034 NormalDX'),CC0,''
    if name=='barrel.dds': return atlas(o,w,h,cc('PaintedMetal004'),16),None,s('PaintedMetal004')+' + coarse colour layout',CC0,'UV atlas: 1/16-res colour layout only'
    if name=='barrel_b.dds': return fit(cc('PaintedMetal004','NormalDX'),w,h),None,s('PaintedMetal004 NormalDX'),CC0,''
    if name in('wood.dds','Puit vana DIFF.dds'): return fit(cc('Planks021'),w,h),None,s('Planks021'),CC0,''
    if name=='wood_NORM.dds': return fit(cc('Planks021','NormalDX'),w,h),None,s('Planks021 NormalDX'),CC0,''
    if name in('wood_02.dds','marshwood.dds'):
        a=coarse_alpha(oa,w,h,8);a=np.where(a>127,255,0).astype(np.uint8)
        base=fit(cc('WoodSiding008' if name=='marshwood.dds' else 'Wood049'),w,h)
        if name=='marshwood.dds': base=np.clip(base.astype(np.float32)*0.5+128,0,255).astype(np.uint8)  # white-painted marshal wood
        return base,a,s('WoodSiding008' if name=='marshwood.dds' else 'Wood049'),CC0,'cut-out alpha from 1/8-res threshold of original (shape only)'
    if name=='rocky.dds': return fit(cc('Rock030'),w,h),None,s('Rock030'),CC0,''
    if name=='z_rocky_nm.dds': return fit(cc('Rock030','NormalDX'),w,h),None,s('Rock030 NormalDX'),CC0,''
    if name in('twallb02.dds','twallb02_NM.dds'):  # black tire stacks (trackday notes)
        hh=np.zeros((h,w),np.float32);rows=4;cols=8
        for r in range(rows):
            for c in range(cols):
                cx=(c+0.5+0.5*(r%2))*w/cols;cy=(r+0.5)*h/rows;R_=min(w/cols,h/rows)*0.5
                yy,xx=np.ogrid[:h,:w];d=np.hypot(xx-cx,yy-cy)/R_
                hh=np.maximum(hh,np.clip(1-np.abs(d-0.75)/0.3,0,1))
        hh=hh*0.9+noise(w,h,8,3)*0.1
        if name=='twallb02_NM.dds': return h2n(hh,6),None,'procedural',PROC,'tire-stack normal'
        rgb=np.dstack([18+hh*22]*3).astype(np.uint8);return rgb,None,'procedural',PROC,'black tire stacks per trackday notes'
    if name=='props_post-toilette-cabin_d.dds': return atlas(o,w,h,cc('Plastic006'),32),None,s('Plastic006')+' + coarse colour layout',CC0,'UV atlas: 1/32-res colour layout only'
    if name=='props_post-toilette-cabin_n.dds': return fit(cc('Plastic006','NormalDX'),w,h),None,s('Plastic006 NormalDX'),CC0,''
    if name=='props_post-toilette-cabin_maps.dds':
        m=o[...,:3].reshape(-1,3).mean(0).astype(np.uint8);return np.tile(m,(h,w,1)),None,'procedural',PROC,'flat spec/gloss/refl values (channel means only)'
    if name=='vesi_NM_2.dds':
        n=noise(w,h,64,5)+noise(w,h,16,3)*0.5;n=cv2.GaussianBlur(n,(0,0),2)
        return h2n(n,3),np.full((h,w),255,np.uint8),'procedural',PROC,'water ripple normal'
    if name in('jarvi_map.dds','jarvi_ref.dds'):
        m=o.reshape(-1,4).mean(0).astype(np.uint8);return np.tile(m[:3],(h,w,1)),np.full((h,w),m[3],np.uint8),'procedural',PROC,'flat values (channel means only)'
    if name in('door_d1_1 - Copy.dds','door_blue.dds'):
        col=(60,95,160) if 'blue' in name else (120,120,115)
        img=Image.fromarray(tint(fit(cc('Metal032'),w,h),col,0.9));d=ImageDraw.Draw(img)
        d.rectangle([w*0.08,h*0.05,w*0.92,h*0.97],outline=(40,40,40),width=max(1,w//32));d.ellipse([w*0.75,h*0.5,w*0.85,h*0.55],fill=(200,200,200))
        return np.array(img),None,s('Metal032')+' + procedural',CC0,'door'
    if name in('window_d7_1.dds','wwindows03_duvan01.dds'):
        img=Image.new('RGB',(w,h),(200,200,195));d=ImageDraw.Draw(img);m=w//10
        d.rectangle([m,m,w-m,h-m],fill=(55,70,85));d.line([w/2,m,w/2,h-m],fill=(200,200,195),width=max(1,w//24));d.line([m,h/2,w-m,h/2],fill=(200,200,195),width=max(1,w//24))
        return np.array(img),None,'procedural',PROC,'window'
    if name=='banner02.dds':
        img=Image.new('RGB',(w,h),(20,20,24));d=ImageDraw.Draw(img)
        d.rectangle([0,h*0.78,w,h],fill=(200,20,30));d.text((w*0.06,h*0.22),'I-29 SPEEDWAY',fill=(240,240,240),font_size=int(h*0.32))
        return np.array(img),oa if oa.min()<255 else None,'procedural',PROC,'neutral track banner'
    if name in('cables.dds','gurdrc.dds','1a_rail.dds','roofe.dds','racegroove.dds'):
        a=coarse_alpha(oa,w,h,4).astype(np.uint8) if name!='racegroove.dds' else None
        if name=='cables.dds': rgb=np.full((h,w,3),25,np.uint8)
        elif name=='gurdrc.dds': rgb=fit(cc('Metal032'),w,h)
        elif name=='1a_rail.dds': rgb=fit(cc('Metal032'),w,h)
        elif name=='roofe.dds': rgb=fit(cc('CorrugatedSteel005'),w,h)
        else:
            rgb=np.full((h,w,3),12,np.uint8);x=np.linspace(-1,1,w);a=(np.clip(1-np.abs(x)*1.1,0,1)**1.5*255*np.ones((h,1))*(0.7+0.3*noise(w,h,8,3))).astype(np.uint8)
            return rgb,a,'procedural',PROC,'rubbered-in racing groove, alpha procedural'
        return rgb,a,s({'gurdrc.dds':'Metal032','1a_rail.dds':'Metal032','roofe.dds':'CorrugatedSteel005'}.get(name,'')) if name!='cables.dds' else 'procedural',CC0 if name!='cables.dds' else PROC,'alpha: blurred 1/4-res shape of original'
    if name in('containers.dds','containers_a_02_d.dds','crane1.dds','amb1.dds','ambwheel.dds','ambwheeltire.dds','cone.dds','commissario_new.dds'):
        f=32 if max(w,h)>=1024 else 16 if max(w,h)>=256 else 4
        det={'cone.dds':'Plastic006','commissario_new.dds':'Fabric026','ambwheeltire.dds':'Plastic006'}.get(name,'CorrugatedSteel005' if 'contain' in name else 'PaintedMetal004')
        a=None
        if oa.min()<255: a=(coarse_alpha(oa,w,h,4)>127).astype(np.uint8)*255
        return atlas(o,w,h,cc(det),f),a,s(det)+' + coarse colour layout',CC0,f'UV atlas: 1/{f}-res colour layout only'
    if name in('oil_build_vag4.dds','wall_hoken_03.dds','wall_prantaren4.1.dds','wall_lagmannen_02.dds'):
        src={'oil_build_vag4.dds':'CorrugatedSteel005','wall_hoken_03.dds':'PaintedPlaster017','wall_prantaren4.1.dds':'WoodSiding008','wall_lagmannen_02.dds':'CorrugatedSteel005'}[name]
        return tint(fit(cc(src),w,h),o[...,:3].reshape(-1,3).mean(0),0.5),None,s(src),CC0,'tinted to original average colour'
    if name in('detail_arlan_02.dds','roof_larkan_01.dds','gryslate.dds','vag_d1_1.dds'):
        src={'roof_larkan_01.dds':'RoofingTiles008','gryslate.dds':'RoofingTiles008'}.get(name,'CorrugatedSteel005')
        return tint(fit(cc(src),w,h),o[...,:3].reshape(-1,3).mean(0),0.5),None,s(src),CC0,'tinted to original average colour'
    mc=o[...,:3].reshape(-1,3).mean(0)
    if name=='Muld Detailne.dds': return tint(fit(cc('Ground054'),w,h),mc,0.6),None,s('Ground054'),CC0,''
    if name=='gravelroad.dds': return tint(fit(cc('Gravel022'),w,h),mc,0.6),None,s('Gravel022'),CC0,''
    if name=='mud2.dds': return tint(fit(cc('Ground037'),w,h),mc,0.9),None,s('Ground037'),CC0,''
    if name=='road_vara_04.dds': return tint(fit(cc('Asphalt012'),w,h),mc,0.5),None,s('Asphalt012'),CC0,''
    if name=='skid1.dds':
        x=np.linspace(0,1,w);a=np.zeros((h,w),np.float32)
        for c in (0.3,0.7): a+=np.exp(-((x-c)/0.08)**2)
        a=(np.clip(a,0,1)*(0.5+0.5*noise(w,h,16,3))*200).astype(np.uint8);return np.full((h,w,3),10,np.uint8),a,'procedural',PROC,'tyre skid streaks'
    if name.startswith('tent') and name!='tentroof.dds':
        col={'tentmars.dds':(200,30,30),'tentchndp.dds':(230,200,40),'tentcok.dds':(200,200,200),'tentcl.dds':(40,80,170)}[name]
        a=(coarse_alpha(oa,w,h,4)>127).astype(np.uint8)*255
        return tint(fit(cc('Fabric026'),w,h),col,0.85),a,s('Fabric026'),CC0,'plain unbranded tent fabric; alpha 1/4-res shape'
    if name in('tree2.dds','tree3.dds'):
        sil=coarse_alpha(oa,w,h,32)/255.0;leaf=noise(w,h,6,4);leaf2=noise(w,h,24,3)
        a=((sil*0.9+leaf*0.5-0.55)>0).astype(np.float32)*(sil>0.15)
        g=np.dstack([40+60*leaf2,70+70*leaf,25+30*leaf2]).astype(np.float32)*(0.7+0.3*leaf[...,None])
        return np.clip(g,0,255).astype(np.uint8),(a*255).astype(np.uint8),'procedural',PROC,'procedural foliage inside 1/32-res billboard silhouette'
    raise KeyError(name)
def naip_mask(w,h):
    import rasterio
    G=np.load('/workspace/rpotm/geo/g2_to_naip2021_px.npy')
    with rasterio.open('/workspace/rpotm/geo/naip2021.tif') as s_: rgb=np.moveaxis(s_.read(),0,-1)
    nir=np.load('/workspace/rpotm/geo/naip_nir.npy')
    img=np.dstack([rgb,nir]);sc=w/8192;Gs=G.copy();Gs[:,:2]/=sc
    W=cv2.warpAffine(img,Gs,(w,h),flags=cv2.INTER_AREA|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REFLECT).astype(np.float32)
    r,g,b,n=[W[...,i] for i in range(4)];ndvi=(n-r)/(n+r+1e-3);bri=(r+g+b)/3;sat=W[...,:3].max(2)-W[...,:3].min(2)
    road=(ndvi<0.12)&(bri>120)&(sat<40);water=(ndvi<0)&(bri<70);soil=(ndvi<0.25)&~road&~water
    m=np.zeros((h,w,4),np.uint8);m[...,0]=255
    for ch,mk in((1,soil),(2,road),(3,water)):
        mk=cv2.GaussianBlur(mk.astype(np.float32),(0,0),1.5);m[...,ch]=(mk*255).astype(np.uint8);m[...,0]=np.minimum(m[...,0],(255*(1-mk)).astype(np.uint8))
    return m
UPSCALE_SKIP=('barrel.dds','props_post-toilette-cabin_d.dds','containers.dds','containers_a_02_d.dds','crane1.dds','amb1.dds','ambwheel.dds','ambwheeltire.dds','cone.dds','commissario_new.dds','tree2.dds','tree3.dds','google_mask.dds','glass2.dds','jarvi_map.dds','jarvi_ref.dds','vesi_NM_2.dds','cables.dds','gurdrc.dds','1a_rail.dds','roofe.dds','wood_02.dds','marshwood.dds','props_post-toilette-cabin_maps.dds')
def build_all(targets):
    done={};meta={}
    for kn,name,*_ in targets:
        if name in done: continue
        b=k.get_tex(f'/workspace/rpotm/backup/{kn}.pre_textures_open',name);w,h,mm,fmt=info(b)
        orig=np.array(Image.open(io.BytesIO(b)).convert('RGBA'))
        up=2 if (name not in UPSCALE_SKIP and pot(w) and pot(h) and max(w,h)<=1024) else 1
        W,H=w*up,h*up
        if name=='google_mask.dds':
            rgba=naip_mask(W,H);src,lic,note='USDA NAIP 2021 (RGB+NIR) classification','Public domain (USDA FSA) https://naip-usdaonline.hub.arcgis.com/','R=vegetation,G=bare soil (NDVI<0.25),B=road/gravel (bright,low sat),A=water'
        else:
            rgb,a,src,lic,note=R(name,W,H,orig)
            if a is None: a=np.full((H,W),255,np.uint8) if orig[...,3].min()==255 else cv2.resize(orig[...,3],(W,H),interpolation=cv2.INTER_LINEAR)

            rgba=np.dstack([rgb[...,:3],a]).astype(np.uint8)
        mips=1 if mm==1 else int(math.log2(max(W,H)))+1
        nb=write_dds(rgba,fmt,mips,b[:128]);done[name]=nb
        Image.fromarray(rgba).save(f'{OUT}/{name}.png')
        meta[name]=dict(old=f'{w}x{h} {fmt} mips{mm}',new=f'{W}x{H} {fmt} mips{mips}',src=src,lic=lic,note=note,bytes=len(nb))
        print(name,meta[name]['old'],'->',meta[name]['new'],src)
    return done,meta
if __name__=='__main__':
    T=json.load(open('/workspace/rpotm/tex/targets.json'))
    done,meta=build_all(T)
    json.dump(meta,open(f'{OUT}/meta.json','w'),indent=1)
    import pickle;pickle.dump(done,open(f'{OUT}/blobs.pkl','wb'))
