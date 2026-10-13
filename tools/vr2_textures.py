"""VR2 texture builder -> assets_src/vr2/*.dds (+ .png previews). Sources: ambientCG CC0, Poly Haven CC0 renders, NAIP (PD), procedural."""
import sys,os,io,numpy as np,cv2
sys.path.insert(0,os.path.dirname(__file__))
import build_open_textures as B,kn5patch as K,topview as T
from scipy import ndimage
from PIL import Image
OUT=os.path.join(os.path.dirname(__file__),'..','assets_src','vr2');os.makedirs(OUT,exist_ok=True)
BK='/workspace/rpotm/backup/vr2'
def save(name,rgb,a=None,fmt='DXT1',hdr=None):
    h,w=rgb.shape[:2];a=np.full((h,w),255,np.uint8) if a is None else a
    rgba=np.dstack([np.asarray(rgb)[...,:3],a]).astype(np.uint8);mips=int(np.log2(max(w,h)))+1
    open(f'{OUT}/{name}.dds','wb').write(B.write_dds(rgba,fmt,mips,hdr));Image.fromarray(rgba).save(f'{OUT}/{name}.png')
f=B.fit;cc=B.cc;t=B.tint
def maps(h,w,spec,gloss,refl,var=None):
    m=np.zeros((h,w,3),np.float32);m[...]=[spec,gloss,refl]
    if var is not None: m*=(0.75+0.5*var[...,None])
    return np.clip(m*255,0,255).astype(np.uint8)
def rough_var(id,w,h):
    r=f(cc(id,'Roughness'),w,h).astype(np.float32)/255;r=r.mean(2) if r.ndim==3 else r;return 1-r
# 1) ground mask: force grass in the track infield + 18 m border (was B=gravel/G=soil patches -> Gravel022 "cobble" look at corners)
def ground_mask():
    m=np.array(Image.open(io.BytesIO(K.get_tex(f'{BK}/vf_i29_speedway.kn5','google_mask.dds'))).convert('RGBA'))
    road=np.zeros((4096,8192),np.uint8)
    for fn,pred in((f'{BK}/vf_i29_speedway_physical.kn5',lambda n:n.startswith('1ROAD') or n.startswith('1PIT')),(f'{BK}/vf_i29_speedway.kn5',lambda n:n.startswith('1DRAG') or n.startswith('1CURB'))):
        for n,V,I in T.meshes(fn,pred):
            P=T.px(V[:,[0,2]].astype(float)).astype(np.int32)
            for tr in I: cv2.fillConvexPoly(road,P[tr],1)
    s=cv2.resize(road,(2048,1024),interpolation=cv2.INTER_AREA)>0
    k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(95,95))
    c=ndimage.binary_fill_holes(cv2.morphologyEx(s.astype(np.uint8),cv2.MORPH_CLOSE,k)>0)|ndimage.binary_dilation(s,iterations=8)
    g=cv2.resize(c.astype(np.uint8),(8192,4096),interpolation=cv2.INTER_NEAREST)>0
    w=ndimage.gaussian_filter(g.astype(np.float32),3)
    for ch in (1,2): m[...,ch]=(m[...,ch]*(1-w)).astype(np.uint8)
    m[...,0]=np.maximum(m[...,0],(255*w*(m[...,3]<128)).astype(np.uint8))
    hdr=K.get_tex(f'{BK}/vf_i29_speedway.kn5','google_mask.dds')[:128]
    open(f'{OUT}/google_mask.dds','wb').write(B.write_dds(m,'DXT5',14,hdr));Image.fromarray(m).resize((2048,1024)).save(f'{OUT}/google_mask.png')
# 2) concrete with expansion joints (ground detail B: roads outside the track)
def concrete_seams(N=1024):
    c=f(cc('Concrete034'),N,N).astype(np.float32);c=c/c.mean((0,1))*np.array([186,184,178])
    nz=B.noise(N,N,128,3);slab=np.ones((N,N),np.float32);H=N//2
    for i in range(2):
        for j in range(2): slab[j*H:(j+1)*H,i*H:(i+1)*H]=0.94+0.08*((i*7+j*3)%5)/4
    c*=slab[...,None]*(0.95+0.1*nz[...,None])
    jt=np.zeros((N,N),np.float32)
    for p in (0,H):
        jt[:,max(p-2,0):p+2]=1;jt[max(p-2,0):p+2,:]=1
    jt[:,N-2:]=1;jt[N-2:,:]=1;jt=cv2.GaussianBlur(jt,(0,0),0.8)
    c=c*(1-0.6*jt[...,None]);save('concrete_seams',np.clip(c,0,255).astype(np.uint8),hdr=K.get_tex(f'{BK}/vf_i29_speedway.kn5','gravelroad.dds')[:128])
# 3) gravel paddock (Gravel022 toned to the NAIP lot colour, light grey-tan)
def gravel():
    g=f(cc('Gravel022'),2048,2048).astype(np.float32);L=g.mean(2,keepdims=True);g=0.3*g+0.7*L;g=g/g.mean((0,1))*np.array([168,161,148])  # crushed-limestone grey-tan, mostly desaturated
    save('own_gravel',np.clip(g,0,255).astype(np.uint8));save('own_gravel_nm',f(cc('Gravel022','NormalDX'),2048,2048))
    save('own_gravel_maps',maps(1024,1024,0.15,0.25,0.0,rough_var('Gravel022',1024,1024)))
# 4) MultiMap maps + normals for own models and upgraded zwiss props
def own_maps():
    save('own_tower_paint_maps',maps(1024,1024,0.35,0.35,0.05,rough_var('PaintedPlaster017',1024,1024)))
    for n,id_,sp,gl,rf in(('own_galv','Metal032',0.8,0.6,0.25),('own_alu','Metal032',0.9,0.7,0.3)):
        save(n+'_nm',f(cc(id_,'NormalDX'),1024,1024));save(n+'_maps',maps(1024,1024,sp,gl,rf,rough_var(id_,1024,1024)))
    save('own_hut_white_nm',f(cc('PaintedPlaster017','NormalDX'),1024,1024));save('own_hut_white_maps',maps(1024,1024,0.3,0.3,0.03))
    save('own_awning_nm',f(cc('Fabric026','NormalDX'),1024,1024));save('own_awning_maps',maps(512,512,0.1,0.15,0.0))
    save('own_glass_maps',maps(64,64,1.0,1.0,0.8))
    save('flat_nm',np.full((64,64,3),(128,128,255),np.uint8))
    save('rubber_maps',maps(512,512,0.12,0.2,0.0));save('armco_maps',maps(512,256,0.85,0.7,0.35))
    save('fabric_nm',f(cc('Fabric026','NormalDX'),1024,1024));save('fabric_maps',maps(512,512,0.15,0.15,0.0))
    save('concrete_maps',maps(512,512,0.15,0.2,0.0,rough_var('Concrete034',512,512)))
# 5) trees: Poly Haven renders -> 2x2 atlases 4096 DXT5 (same quadrant layout as zwiss tree2/tree3)
def trees():
    R='/workspace/rpotm/vr2/trees'
    for at in ('tree2','tree3'):
        A=np.zeros((4096,4096,4),np.uint8)
        for q in range(4):
            im=np.array(Image.open(f'{R}/{at}_{q}.png').convert('RGBA'))
            a=im[...,3].astype(np.float32)/255;rgb=im[...,:3].astype(np.float32)
            # bleed colour into transparent pixels (avoids dark fringes in mips), harden alpha for alpha-test
            dil=cv2.dilate(rgb*(a[...,None]>0.05),np.ones((9,9)));rgb=np.where(a[...,None]>0.05,rgb,dil)
            rgb=np.clip(rgb*np.array([0.95,1.0,0.9])*1.05,0,255)
            x,y=(q%2)*2048,(q//2)*2048;A[y:y+2048,x:x+2048,:3]=rgb;A[y:y+2048,x:x+2048,3]=(np.clip((a-0.35)*3+0.5,0,1)*255)
        hdr=K.get_tex(f'{BK}/zw_vegetation.kn5',f'{at}.dds')[:128]
        open(f'{OUT}/{at}.dds','wb').write(B.write_dds(A,'DXT5',13,hdr));Image.fromarray(A).resize((1024,1024)).save(f'{OUT}/{at}.png')
if __name__=='__main__':
    for fn in sys.argv[1:] or ['ground_mask','concrete_seams','gravel','own_maps','trees']:
        globals()[fn]();print('done',fn)
