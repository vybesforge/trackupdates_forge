"""North-extension textures -> assets_src/north/*.dds (+png). CC0 ambientCG, NAIP 2021 (PD), procedural (CC0)."""
import sys,os,io,numpy as np,cv2,rasterio
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..'));sys.path.insert(0,os.path.dirname(__file__))
import build_open_textures as B,kn5patch as K,topview as T,geo
from PIL import Image,ImageDraw,ImageFont
ROOT=os.path.join(os.path.dirname(__file__),'..','..');OUT=f'{ROOT}/assets_src/north';os.makedirs(OUT,exist_ok=True)
VR2=f'{ROOT}/assets_src/vr2';KN=f'{ROOT}/zw_rpm/zw_rpm.kn5'
def save(name,rgb,a=None,fmt='DXT1'):
    h,w=rgb.shape[:2];a=np.full((h,w),255,np.uint8) if a is None else a
    rgba=np.dstack([np.asarray(rgb)[...,:3],a]).astype(np.uint8);mips=int(np.log2(max(w,h)))+1
    open(f'{OUT}/{name}.dds','wb').write(B.write_dds(rgba,fmt,mips,None));Image.fromarray(rgba).save(f'{OUT}/{name}.png')
f=B.fit;cc=B.cc;t=B.tint
def maps(h,w,s,g,r): m=np.zeros((h,w,3),np.uint8);m[...]=[int(s*255),int(g*255),int(r*255)];return m
FB='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def ground():
    x0,x1,z0,z1=geo.BOX;W,H=4096,1024
    xs=np.linspace(x0,x1,W);zs=np.linspace(z0,z1,H);X,Z=np.meshgrid(xs,zs);P=np.c_[X.ravel(),Z.ravel()]
    r=rasterio.open('/workspace/rpotm/geo/ext/naip2021_ext_06.tif');D=r.read().astype(np.float32);it=~r.transform
    u=geo.utm(P);c,rr=it*(u[:,0],u[:,1])
    from scipy.ndimage import map_coordinates
    img=np.stack([map_coordinates(D[i],[rr-0.5,c-0.5],order=1,mode='nearest').reshape(H,W) for i in range(4)],-1)
    # colour-match to zwiss google2 (NAIP, normalised to v0.9) over the overlap band just south of the edge
    g2=np.array(Image.open(io.BytesIO(K.get_tex(KN,'google2.dds'))).convert('RGB')).astype(np.float32)
    sel=(Z.ravel()>-2636)&(Z.ravel()<-2560)&(X.ravel()>-830)&(X.ravel()<290)
    p=T.px(P[sel]).astype(int);ok=(p[:,0]>=0)&(p[:,0]<8192)&(p[:,1]>=0)&(p[:,1]<4096)
    ref=g2[p[ok,1],p[ok,0]];src=img.reshape(-1,4)[sel][ok][:,:3]
    rgb=(img[...,:3]-src.mean(0))/src.std(0)*ref.std(0)+ref.mean(0);rgb=np.clip(rgb,0,255).astype(np.uint8)
    save('ext_ground',rgb)
    R,Gc,Bc,N=[img[...,i] for i in range(4)];ndvi=(N-R)/(N+R+1e-3);bri=img[...,:3].mean(-1);sat=img[...,:3].max(-1)-img[...,:3].min(-1)
    road=(ndvi<0.12)&(bri>120)&(sat<40);water=(ndvi<0)&(bri<70);soil=(ndvi<0.25)&~road&~water
    m=np.zeros((H,W,4),np.uint8);m[...,0]=255
    for ch,mk in((1,soil),(2,road),(3,water)):
        mk=cv2.GaussianBlur(mk.astype(np.float32),(0,0),1.5);m[...,ch]=(mk*255).astype(np.uint8);m[...,0]=np.minimum(m[...,0],(255*(1-mk)).astype(np.uint8))
    m=cv2.resize(m,(2048,512),interpolation=cv2.INTER_AREA);save('ext_ground_mask',m[...,:3],m[...,3],'DXT5')
    np.save(f'{OUT}/naip_box_rgbn.npy',img[::2,::2].astype(np.uint8))
def surfaces():
    a=f(cc('Asphalt012'),1024,1024).astype(np.float32);a=a/a.mean((0,1))*np.array([92,92,94]);save('ext_asphalt',np.clip(a,0,255).astype(np.uint8))
    save('ext_asphalt_nm',f(cc('Asphalt012','NormalDX'),1024,1024));save('ext_asphalt_maps',maps(256,256,0.25,0.35,0.02))
    save('ext_concrete_nm',f(cc('Concrete034','NormalDX'),1024,1024))
    save('ext_white',np.full((32,32,3),235,np.uint8));save('ext_yellow',np.tile(np.array([230,180,30],np.uint8),(32,32,1)))
    save('ext_lot_paint',np.full((32,32,3),225,np.uint8))
    w=t(f(cc('PaintedPlaster017'),1024,1024),(214,200,176),0.85);save('ext_wall_tan',w);save('ext_wall_nm',f(cc('PaintedPlaster017','NormalDX'),1024,1024))
    save('ext_wall_grey',t(f(cc('CorrugatedSteel005'),1024,1024),(200,203,205),0.7));save('ext_corr_nm',f(cc('CorrugatedSteel005','NormalDX'),1024,1024))
    save('ext_canopy',t(f(cc('PaintedMetal004'),512,512),(240,240,238),0.9));save('ext_canopy_nm',f(cc('PaintedMetal004','NormalDX'),512,512))
    save('ext_paint_maps',maps(64,64,0.3,0.35,0.05));save('ext_metal_maps',maps(64,64,0.7,0.6,0.25));save('ext_matte_maps',maps(64,64,0.08,0.1,0.0))
    save('ext_wood',t(f(cc('Wood049'),512,512),(110,90,70),0.6));save('ext_flat_nm',np.full((32,32,3),(128,128,255),np.uint8))
    # pump: white body, dark display band, red/green nozzle strip (generic)
    p=np.full((256,256,3),236,np.uint8);p[40:110,30:226]=(35,38,42);p[140:160,30:226]=(60,60,64);p[200:256]=(150,150,150);save('ext_pump',p)
    # fence: 4 m panel, posts at both ends, 3 barbed strands; alpha
    W_,H_=512,128;im=np.zeros((H_,W_,3),np.uint8)+90;al=np.zeros((H_,W_),np.uint8)
    for y in (20,55,90): al[y-1:y+1,:]=255
    al[:,0:6]=255;al[:,-6:]=255;im[:,0:6]=(110,85,60);im[:,-6:]=(110,85,60);save('ext_fence',im,al,'DXT5')
def signs():
    def panel(w,h,bg,lines,name):
        im=Image.new('RGB',(w,h),bg);d=ImageDraw.Draw(im);y=h*0.08
        for txt,sz,col in lines:
            fo=ImageFont.truetype(FB,sz);bb=d.textbbox((0,0),txt,font=fo);d.text(((w-(bb[2]-bb[0]))/2-bb[0],y-bb[1]),txt,font=fo,fill=col);y+=(bb[3]-bb[1])+h*0.07
        save(name,np.array(im))
    panel(1024,1024,(24,44,90),[('TRAVEL',170,'white'),('STOP',170,'white'),('DIESEL • GAS',90,(250,210,60)),('FOOD • SHOWERS',80,'white')],'ext_sign_travelstop')
    panel(1024,512,(40,40,44),[('FUEL',150,'white'),('DELI • STORE',90,(120,220,120))],'ext_sign_fuel')
    panel(1024,256,(24,44,90),[('TRAVEL STOP',150,'white')],'ext_fascia_ts')
    panel(1024,256,(40,40,44),[('FUEL • DELI',150,'white')],'ext_fascia_fuel')
    # stop sign (MUTCD R1-1 design, public domain), alpha octagon; back grey
    S=512;im=Image.new('RGB',(S,S),(190,20,30));al=Image.new('L',(S,S),0);d=ImageDraw.Draw(im);da=ImageDraw.Draw(al)
    import math
    oc=[(S/2+S/2*math.cos(math.radians(22.5+45*i)),S/2+S/2*math.sin(math.radians(22.5+45*i))) for i in range(8)]
    da.polygon(oc,fill=255);oc2=[(S/2+(S/2-18)*math.cos(math.radians(22.5+45*i)),S/2+(S/2-18)*math.sin(math.radians(22.5+45*i))) for i in range(8)]
    d.polygon(oc,fill='white');d.polygon(oc2,fill=(190,20,30));fo=ImageFont.truetype(FB,150);bb=d.textbbox((0,0),'STOP',font=fo);d.text(((S-bb[2]+bb[0])/2-bb[0],(S-bb[3]+bb[1])/2-bb[1]),'STOP',font=fo,fill='white')
    save('ext_stop',np.array(im),np.array(al),'DXT5')
    panel(1024,256,(0,110,60),[('188TH ST',150,'white')],'ext_street_188');panel(1024,256,(0,110,60),[('190TH ST',150,'white')],'ext_street_190')
    panel(512,256,(250,250,250),[('ALL WAY',110,(190,20,30))],'ext_allway')
if __name__=='__main__':
    for fn in sys.argv[1:] or ['ground','surfaces','signs']: globals()[fn]();print('done',fn)
