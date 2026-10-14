"""Tents v1.1 (v2 pass): 12-tent car-meet vendor cluster right behind the spawns, one material + texture per slot.
Builds vf_i29_speedway/zw_tents.kn5, CSP override textures vf_i29_speedway/extension/tent_slotNN.dds (2048) and art PNGs
assets_src/brand/tent_slotNN.png. kn5 embeds 1024 fallbacks (keeps the file < 20 MB); CSP loads the 2048 overrides.
Layout: two facing columns of 6 (x 68 opens +x, x 82 opens -x), z 98..135.5 every 7.5 m (1.5 m gaps), 8 m aisle opening
towards the spawns (-z). Tent: 6 x 6 m, black frame, charcoal sagging 4-panel roof (eave 2.4, apex 3.3), 0.30 m white
print valance, light-grey back wall, black base plates + 2 sandbags per leg, 1.8 m table with printed front skirt,
feather flag on every other tent, soft contact-shadow decal. UV atlas (2048): rows 0-1024 roof triangle, 1024-1280
valance/print strip (also table skirt + flag), 1280-2032 back wall, 2032-2048 plain. Run: python3 tools/tents_v11.py [--verify-only]"""
import sys,os,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import kn5write as W,vr5_meshlib as ML,build_open_textures as B
from PIL import Image,ImageDraw,ImageFont
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));Z=f'{ROOT}/vf_i29_speedway';EXT=f'{Z}/extension';OUT=f'{ROOT}/assets_src/brand'
FONT=f'{OUT}/fonts/SpaceGrotesk-wght.ttf';LOGO=f'{OUT}/vf_logo.jpg'
CH=(42,43,46);WH=(244,244,244);LG=(214,214,214);MG_=(120,120,124);BK=(14,14,16);N=2048;NK=1024
W_,D_,EAVE,APEX,VAL,SAG,BACK_WALL=6.0,6.0,2.4,3.3,0.30,0.07,True
# slot, x, z, yaw (rad; 0 = opening faces -z). Left column opens +x (yaw -pi/2), right column opens -x (yaw +pi/2).
SLOTS=[(i+1,68.0,98.0+7.5*i,-np.pi/2) for i in range(6)]+[(i+7,82.0,98.0+7.5*i,np.pi/2) for i in range(6)]
FLAGS={1,3,5,7,9,11}
def font(sz,w=600):
    f=ImageFont.truetype(FONT,sz)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
def art(slot):
    rng=np.random.default_rng(slot);w=rng.normal(0,1,(N//8,N//8))
    w=np.array(Image.fromarray(((w*20)+128).clip(0,255).astype(np.uint8)).resize((N,N),Image.BILINEAR),np.float32)-128
    im=Image.new('RGB',(N,N),CH);D=ImageDraw.Draw(im)
    D.rectangle([0,1024,N,1280],fill=WH);D.rectangle([0,1280,N,2032],fill=LG);D.rectangle([0,2032,N,N],fill=(58,59,62))
    def ct(cx,cy,s,f,fill,sy=1.0,sp=0):
        bb=f.getbbox(s);t=Image.new('RGBA',(bb[2]-bb[0]+8+sp*len(s),bb[3]-bb[1]+8),(0,0,0,0));d=ImageDraw.Draw(t)
        if sp:
            x=4
            for ch in s: d.text((x-bb[0],4-bb[1]),ch,font=f,fill=fill);x+=f.getlength(ch)+sp
        else: d.text((4-bb[0],4-bb[1]),s,font=f,fill=fill)
        t=t.resize((t.width,max(1,int(t.height*sy))),Image.LANCZOS);im.paste(t,(int(cx-t.width/2),int(cy-t.height/2)),t);return t.width
    # roof (charcoal): clean wordmark + thin rule
    ct(N//2,700,'YOUR BRAND',font(150,700),WH,sp=6);D.rectangle([N//2-260,800,N//2+260,806],fill=MG_);ct(N//2,880,'AD SPACE',font(70,400),(190,190,194),sp=18)
    # valance print strip (white): 256 px = 0.30 m, 2048 px = 6 m -> text squashed 2.0x vertically compensated
    ct(N//2,1152,f'YOUR BRAND HERE   |   AD SLOT {slot:02d}   |   I-29 SPEEDWAY',font(64,600),BK,sy=1.0)
    # back wall (light grey)
    D.rectangle([160,1340,N-160,1346],fill=BK)
    ct(N//2,1560,'YOUR AD HERE',font(230,700),BK,0.95,sp=4);ct(N//2,1760,'ADVERTISE AT I-29 SPEEDWAY',font(80,400),(60,60,64),0.95,sp=10)
    ct(N//2,1900,f'VENDOR SLOT {slot:02d}',font(56,500),(90,90,94),0.95,sp=14)
    a=np.array(im).astype(np.float32);a=np.clip(a+w[...,None]*0.08,0,255).astype(np.uint8)
    rgba=np.dstack([a,np.full((N,N),255,np.uint8)]);Image.fromarray(rgba).save(f'{OUT}/tent_slot{slot:02d}.png')
    small=np.array(Image.fromarray(rgba).resize((NK,NK),Image.LANCZOS))
    return B.write_dds(rgba,'DXT1',12,None),B.write_dds(small,'DXT1',11,None)
def fabric_normal(n=512):
    """procedural plain-weave normal map (tiles), stronger and finer than the old fabric_nm"""
    y,x=np.mgrid[0:n,0:n]/n*2*np.pi*48;wx=np.sin(x)*(np.sin(y/2)>0)+np.sin(x+np.pi)*(np.sin(y/2)<=0);wy=np.sin(y)*(np.sin(x/2)>0)+np.sin(y+np.pi)*(np.sin(x/2)<=0)
    h=0.5*wx+0.5*wy+np.random.default_rng(0).normal(0,0.15,(n,n));gx=np.gradient(h,axis=1)*0.9;gy=np.gradient(h,axis=0)*0.9
    nz=1/np.sqrt(1+gx**2+gy**2);rgb=np.dstack([(-gx*nz+1)*127.5,(-gy*nz+1)*127.5,(nz+1)*127.5]).clip(0,255).astype(np.uint8)
    rgba=np.dstack([rgb,np.full((n,n),255,np.uint8)]);Image.fromarray(rgb).save(f'{ROOT}/assets_src/vr2/fabric_nm_v2.png');return B.write_dds(rgba,'DXT1',10,None)
PLAIN=(0.5,2040/N)
def face(P,UV,out):
    P=np.array(P,float);UV=np.array(UV,float);n=np.cross(P[1]-P[0],P[2]-P[0]);n/=np.linalg.norm(n)
    if np.dot(n,out)<0: n=-n
    e1,e2=P[1]-P[0],P[2]-P[0];d1,d2=UV[1]-UV[0],UV[2]-UV[0];det=d1[0]*d2[1]-d2[0]*d1[1]
    t=(e1*d2[1]-e2*d1[1])/det if abs(det)>1e-9 else e1;t-=n*np.dot(t,n);t/=np.linalg.norm(t)+1e-12
    V=np.zeros((len(P),11));V[:,:3]=P;V[:,3:6]=n;V[:,6:8]=UV;V[:,8:11]=t
    I=np.array([[0,1,2]] if len(P)==3 else [[0,1,2],[0,2,3]]);return V,ML.fix_winding(V,I)
def two(P,UV,out,UVback=None):
    ub=UVback if UVback is not None else [PLAIN]*len(P);return [face(P,UV,out),face(P,ub,-np.asarray(out,float))]
def roof_panel(L,R,A,out,n=6):
    """sagging triangular roof panel (barycentric grid), outside + underside; smooth normals"""
    L,R,A=map(np.array,(L,R,A));pts=[];uvs=[];idx={}
    for i in range(n+1):
        for j in range(n+1-i):
            k=n-i-j;a,b,c=i/n,j/n,k/n;p=a*L+b*R+c*A;p[1]-=SAG*27*a*b*c;idx[i,j]=len(pts);pts.append(p)
            uvs.append(a*np.array([0,1024/N])+b*np.array([1,1024/N])+c*np.array([0.5,0]))
    T=[]
    for i in range(n):
        for j in range(n-i):
            T.append((idx[i,j],idx[i+1,j],idx[i,j+1]))
            if i+j<n-1: T.append((idx[i+1,j],idx[i+1,j+1],idx[i,j+1]))
    P=np.array(pts);UV=np.array(uvs);T=np.array(T);out=np.array(out,float);out/=np.linalg.norm(out)
    fn=np.cross(P[T[:,1]]-P[T[:,0]],P[T[:,2]]-P[T[:,0]]);fn*=np.sign((fn@out))[:,None];vn=np.zeros_like(P)
    for k in range(3): np.add.at(vn,T[:,k],fn)
    vn/=np.linalg.norm(vn,axis=1,keepdims=True);t=R-L;t/=np.linalg.norm(t)
    def mk(nrm,uv):
        V=np.zeros((len(P),11));V[:,:3]=P;V[:,3:6]=nrm;V[:,6:8]=uv;V[:,8:11]=t;return V,ML.fix_winding(V,T)
    UVu=UV.copy();UVu[:,0]=1-UVu[:,0]
    return [mk(vn,UV),mk(-vn,UVu)]
def strip_uv(u0,u1): return [(u0,1024/N),(u1,1024/N),(u1,1280/N),(u0,1280/N)]
def canopy_local(slot):
    """local coords: centre (0,0,0) on the ground, opening towards -z. returns dict material-> (V,I)"""
    hw,hd=W_/2,D_/2;e=EAVE;A=(0,APEX,0);fab=[];fr=[];bag=[];top=[]
    C={'fl':(-hw,-hd),'fr':(hw,-hd),'br':(hw,hd),'bl':(-hw,hd)}
    for l,r,o in (('fl','fr',(0,1,-1)),('fr','br',(1,1,0)),('br','bl',(0,1,1)),('bl','fl',(-1,1,0))):
        L=(C[l][0],e,C[l][1]);R=(C[r][0],e,C[r][1]);fab+=roof_panel(L,R,A,o)
        Lb=(L[0],e-VAL,L[2]);Rb=(R[0],e-VAL,R[2]);fab+=two([L,R,Rb,Lb],strip_uv(0,1),(o[0],0,o[2]))
    if BACK_WALL:
        L=(hw,e-VAL,hd-0.02);R=(-hw,e-VAL,hd-0.02);Rb=(-hw,-0.03,hd-0.02);Lb=(hw,-0.03,hd-0.02)
        fab.append(face([L,R,Rb,Lb],[(0,1280/N),(1,1280/N),(1,2032/N),(0,2032/N)],(0,0,1)))
        fab.append(face([L,R,Rb,Lb],[(1,1280/N),(0,1280/N),(0,2032/N),(1,2032/N)],(0,0,-1)))
    for k,(x,z) in C.items():
        sx,sz=np.sign(x),np.sign(z);ix,iz=x-sx*0.03,z-sz*0.03
        fr.append(ML.box((ix,e/2,iz),(0.045,e,0.045)));fr.append(ML.box((ix,0.01,iz),(0.26,0.02,0.26)))          # leg + base plate
        bag.append(ML.box((ix-sx*0.24,0.065,iz),(0.24,0.13,0.42),0.12));bag.append(ML.box((ix,0.18,iz-sz*0.22),(0.42,0.11,0.22),-0.08))  # 2 sandbags
    for z0 in(-hd+0.03,hd-0.03): fr.append(ML.box((0,e-0.05,z0),(W_-0.06,0.05,0.04)))
    for x0 in(-hw+0.03,hw-0.03): fr.append(ML.box((x0,e-0.05,0),(0.04,0.05,D_-0.06)))
    for sz in(-1,1):
        z=sz*(hd-0.03)
        for sx in(-1,1):
            p0=np.array([sx*hw*0.98,e-0.08,z]);p1=np.array([0,e-0.32,z]);m=(p0+p1)/2;Ln=np.linalg.norm(p1-p0)
            V,I=ML.box((0,0,0),(Ln,0.028,0.022));ang=np.arctan2(p1[1]-p0[1],p1[0]-p0[0])
            R=np.array([[np.cos(ang),-np.sin(ang),0],[np.sin(ang),np.cos(ang),0],[0,0,1]]);V=V.astype(float);V[:,:3]=V[:,:3]@R.T+m;V[:,3:6]=V[:,3:6]@R.T;V[:,8:11]=V[:,8:11]@R.T
            fr.append((V.astype('<f4'),I))
    # table 1.8 x 0.75, top 0.75 m, 1.4 m behind the front edge; printed front skirt + plain side skirts
    tz=-hd+1.4;top.append(ML.box((0,0.75,tz),(1.8,0.035,0.75)))
    zf=tz-0.375-0.01;fab+=two([(-0.9,0.73,zf),(0.9,0.73,zf),(0.9,0.04,zf),(-0.9,0.04,zf)],[(0.15,1024/N),(0.85,1024/N),(0.85,1280/N),(0.15,1280/N)],(0,0,-1))
    for sx in(-1,1):
        x=sx*0.91;fab+=two([(x,0.73,zf),(x,0.73,tz+0.375),(x,0.04,tz+0.375),(x,0.04,zf)],[PLAIN]*4,(sx,0,0))
    for sx in(-1,1): fr.append(ML.box((sx*0.85,0.37,tz+0.33),(0.03,0.73,0.03)))
    if slot in FLAGS:   # feather flag at the front-right corner, 0.9 m in front of the tent
        px,pz=hw-0.2,-hd-0.9;fr.append(ML.cyl((px,0,pz),0.015,3.4,n=8));fr.append(ML.box((px,0.02,pz),(0.5,0.04,0.5)))
        n=10;pts=[]
        for i in range(n+1):
            t=i/n;y=0.9+2.4*t;wd=0.72*np.sin(np.pi*min(1,0.15+t*0.95))**0.6 if t<1 else 0.25;bend=0.06*np.sin(np.pi*t)
            pts.append(((px,y,pz),(px-bend*0.3,y-0.05*t,pz-wd)))
        for i in range(n):
            (a0,b0),(a1,b1)=pts[i],pts[i+1];u0,u1=0.1+0.8*i/n,0.1+0.8*(i+1)/n
            fab+=two([a0,a1,b1,b0],[(u0,1024/N),(u1,1024/N),(u1,1280/N),(u0,1280/N)],(1,0,0),[(u0,1280/N),(u1,1280/N),(u1,1024/N),(u0,1024/N)])
    sh=[ML.quad((-hw-0.4,0.012,hd+0.4),(hw+0.4,0.012,hd+0.4),(hw+0.4,0.012,-hd-0.4),(-hw-0.4,0.012,-hd-0.4))]
    FV,FI=ML.merge(fab);FV=FV.copy()
    # AC world is right-handed (y up; looking +z the viewer's right is -x): flip u once for all fabric -> art unmirrored
    FV[:,6]=1-FV[:,6];FV[:,8:11]*=-1
    return {'fab':(FV,FI),'frame':ML.merge(fr),'bag':ML.merge(bag),'top':ML.merge(top),'shadow':ML.merge(sh)}
def canopy(cx,cz,gy,yaw,slot):
    return {k:ML.xform(VI,yaw,(cx,gy,cz)) for k,VI in canopy_local(slot).items()}
# ---------------- verification (spawns, exit route, footprints on gravel)
def verify(report=print):
    from physraster import physmeshes,raster
    import kn5tree as T
    box=(-40,170,30,240);res=0.25;fails=0;heights={}
    files=['vf_i29_speedway.kn5','vf_i29_speedway_physical.kn5','vf_i29_speedway_gp.kn5','vf_i29_speedway_own.kn5','zw_ext.kn5','zw_dragexit.kn5','zw_vegetation.kn5']
    M=physmeshes(files,box);xs,zs,H,KEY,UP,names=raster(M,box,res)
    pits=[n['W'][3,:3] for n in T.walk(f'{Z}/vf_i29_speedway.kn5') if n['cls']==1 and n['name'].startswith('AC_PIT_')]
    path=np.load(f'{ROOT}/tools/data/path_main.npy')
    for s,x,z,yaw in SLOTS:
        k='v2';ks=set();hs=[]
        for a in np.linspace(-W_/2-1,W_/2+1,15):
            for b in np.linspace(-D_/2-1,D_/2+1,15):
                ii=int(round((x+a-xs[0])/res));jj=int(round((z+b-zs[0])/res));kk=KEY[jj,ii];ks.add(names[kk] if kk>=0 else None);hs.append(H[jj,ii])
        hs=np.array(hs);dp=min(np.hypot(max(0,abs(p[0]-x)-W_/2-1.1),max(0,abs(p[2]-z)-D_/2-2.6)) for p in pits);dr=np.hypot(path[:,0]-x,path[:,1]-z).min()   # dp: gap tent<->car footprint;dr=np.hypot(path[:,0]-x,path[:,1]-z).min()
        dt=min(np.hypot(x-x2,z-z2) for s2,x2,z2,_ in SLOTS if s2!=s)
        ok=ks=={'1GRAVEL_PADDOCK'} and np.ptp(hs)<0.15 and dp>=8 and dr>=25 and dt>=7.4
        fails+=not ok;heights[s]=float(np.nanmin(hs))  # lowest point: nothing floats, high side sinks <=15 cm
        report(f'slot{s:02d} ({x:4},{z:4}) {k:6} surf={sorted(map(str,ks))} dz={np.ptp(hs):.3f} m  ground={heights[s]:+.3f}  car gap {dp:5.1f} m  exit-route {dr:5.1f} m  next tent {dt:4.1f} m  {"OK" if ok else "FAIL"}')
    report(f'{len(SLOTS)-fails}/{len(SLOTS)} slots OK (footprint +1 m margin on 1GRAVEL_PADDOCK, flat <15 cm, >=8 m gap to spawned cars, >=25 m from exit route, >=7.4 m centre spacing (1.5 m gaps))')
    return fails,heights,(xs,zs,H,KEY,names,pits,path)
if __name__=='__main__':
    fails,GY,_=verify()
    if fails or '--verify-only' in sys.argv: sys.exit(1 if fails else 0)
    _m=W.read_materials(f'{Z}/zw_tents.kn5');base=_m.get('vftent_adhere') or _m['vftent_slot01']
    blob=None
    import kn5patch as KP
    blob=KP.get_tex(f'{Z}/zw_vr6.kn5','vr6_blob_rect.dds');shm=W.read_materials(f'{Z}/zw_vr6.kn5')['vr6_shadow_rect']
    fmp=open(f'{ROOT}/assets_src/vr2/fabric_maps.dds','rb').read()
    texs=[('fabric_nm_v2.dds',fabric_normal()),('fabric_maps.dds',fmp),('NULL.dds',ML.solid_dds((255,255,255))),('vft_black.dds',ML.solid_dds((18,18,20))),
          ('vft_sandbag.dds',ML.solid_dds((52,50,46))),('vft_tabletop.dds',ML.solid_dds((236,236,236))),('vr6_blob_rect.dds',blob)]
    def solid(name,tn,spec=0.1,exp=10):
        return dict(name=name,shader='ksPerPixel',ab=0,at=0,dm=0,props=ML.props(base['props'],ksAmbient=0.45,ksDiffuse=0.5,ksSpecular=spec,ksSpecularEXP=exp,ksEmissive=(0,0,0)),samplers=[('txDiffuse',0,tn)])
    mats=[solid('vftent_frame_black','vft_black.dds',0.5,40),solid('vftent_sandbag','vft_sandbag.dds',0.03,4),solid('vftent_tabletop','vft_tabletop.dds',0.15,20),
          dict(name='vftent_shadow',shader=shm['shader'],ab=shm['ab'],at=shm['at'],dm=shm['dm'],props=shm['props'],samplers=[('txDiffuse',0,'vr6_blob_rect.dds')])]
    MI={'frame':0,'bag':1,'top':2,'shadow':3};meshes=[];os.makedirs(EXT,exist_ok=True)
    for s,x,z,yaw in SLOTS:
        big,small=art(s);tn=f'tent_slot{s:02d}.dds';texs.append((tn,small));open(f'{EXT}/{tn}','wb').write(big)
        mats.append(dict(name=f'vftent_slot{s:02d}',shader=base['shader'],ab=0,at=0,dm=base['dm'],props=base['props'],
                         samplers=[('txDiffuse',0,tn),('txNormal',1,'fabric_nm_v2.dds'),('txMaps',2,'fabric_maps.dds'),('txDetail',3,'NULL.dds')]))
        parts=canopy(x,z,GY[s],yaw,s)
        meshes.append(dict(name=f'vftent_slot{s:02d}',mat_index=len(mats)-1,verts=parts['fab'][0],idx=parts['fab'][1],lod_out=0))
        for k in ('frame','bag','top'): meshes.append(dict(name=f'vftent_slot{s:02d}_{k}',mat_index=MI[k],verts=parts[k][0],idx=parts[k][1],lod_out=400))
        meshes.append(dict(name=f'vftent_slot{s:02d}_shadow',mat_index=3,verts=parts['shadow'][0],idx=parts['shadow'][1],lod_out=300,flags=(1,0,0)))
    W.write_kn5(f'{Z}/zw_tents.kn5',texs,mats,meshes,rootname='zw_tents')
    print('zw_tents.kn5:',len(meshes),'meshes',sum(len(m['idx']) for m in meshes),'tris',len(mats),'materials',os.path.getsize(f'{Z}/zw_tents.kn5')//1024,'KB')
    # stale VR6 contact-shadow quads under the old paddock tents (lot x>0, z>100) -> collapsed (zw_vr6.kn5, byte splice)
    import struct
    p6=f'{Z}/zw_vr6.kn5';d=bytearray(open(p6,'rb').read());n=0
    for name,o,l,c in KP.scan(p6)[1]:
        if c==2 and name=='vr6_contact_shadow_rect':
            q=o+l+8;nv,=struct.unpack_from('<I',d,q);V=np.frombuffer(bytes(d[q+4:q+4+nv*44]),'<f4').reshape(nv,11).copy()
            for g in range(0,nv,4):
                Q=V[g:g+4]
                if (Q[:,0].mean()>0) and (Q[:,2].mean()>100): V[g:g+4,:3]=Q[0,:3];n+=1
            d[q+4:q+4+nv*44]=V.astype('<f4').tobytes()
    open(p6,'wb').write(bytes(d));print('zw_vr6.kn5: stale tent shadow quads collapsed:',n)
