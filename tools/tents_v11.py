"""Tents v1.1: 12 pop-up canopy ad tents in the gravel paddock lot, one material + one texture per slot.
Builds vf_i29_speedway/zw_tents.kn5 (replaces the 6 stretched tentm_SUB3 copies), the CSP override textures
vf_i29_speedway/extension/tent_slotNN.dds and the art PNGs assets_src/brand/tent_slotNN.png. Self-contained (no backups needed).
Geometry (6 x 6 m, front = -z, towards the pits): 4 galvanised legs + feet + eave frame, 4-panel peaked roof (eave 2.4 m,
apex 3.4 m), 0.35 m valance on all sides, fabric back wall on +z (optional, BACK_WALL). Roof/valance/wall are double-sided.
UV atlas (2048, DXT1): rows 0-1024 roof triangle (apex top-centre), 1024-1280 valance strip, 1280-2032 back wall,
2032-2048 plain fabric (undersides/inner faces). All 12 slots are open/sellable: YOUR AD HERE + slot number
(the vfad/cm art kinds stay available in art() but are not used). Run:  python3 tools/tents_v11.py [--verify-only]"""
import sys,os,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import kn5write as W,vr5_meshlib as ML,build_open_textures as B
from PIL import Image,ImageDraw,ImageFont
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));Z=f'{ROOT}/vf_i29_speedway';EXT=f'{Z}/extension';OUT=f'{ROOT}/assets_src/brand'
FONT=f'{OUT}/fonts/SpaceGrotesk-wght.ttf';LOGO=f'{OUT}/vf_logo.jpg'
BG=(2,6,15);CY=(41,213,233);MG=(191,51,138);AM=(255,176,0);TX=(232,236,245);N=2048
W_,D_,EAVE,APEX,VAL,BACK_WALL=6.0,6.0,2.4,3.4,0.35,True
# slot, x, z, kind. Vendor row (01,11,02,12,03) at z 98: directly behind the 36 spawns (rows z 72/83, cars face -z towards the
# exit strip z 50-60), as close as the margin allows: >=8 m gap between tent footprint and any spawned car footprint (5.2 x 2.2 m).
# 04-10 stay further back in the lot.
SLOTS=[(1,12,98,'adhere'),(2,66,98,'adhere'),(3,119,98,'adhere'),(4,39,185,'adhere'),(5,60,210,'adhere'),(6,90,190,'adhere'),
       (7,14,170,'adhere'),(8,14,200,'adhere'),(9,140,165,'adhere'),(10,140,200,'adhere'),(11,39,98,'adhere'),(12,93,98,'adhere')]
def font(sz,w=700):
    f=ImageFont.truetype(FONT,sz)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
def art(kind,slot):
    rng=np.random.default_rng(slot);w=rng.normal(0,1,(N//8,N//8))
    w=np.array(Image.fromarray(((w*20)+128).clip(0,255).astype(np.uint8)).resize((N,N),Image.BILINEAR),np.float32)-128
    im=Image.fromarray(np.clip(np.array(BG,np.float32)[None,None]+w[...,None]*0.15+6,0,255).astype(np.uint8),'RGB');D=ImageDraw.Draw(im)
    def ct(cx,cy,s,f,fill,sy=1.0):
        bb=f.getbbox(s);t=Image.new('RGBA',(bb[2]-bb[0]+8,bb[3]-bb[1]+8),(0,0,0,0));ImageDraw.Draw(t).text((4-bb[0],4-bb[1]),s,font=f,fill=fill)
        t=t.resize((t.width,max(1,int(t.height*sy))),Image.LANCZOS);im.paste(t,(int(cx-t.width/2),int(cy-t.height/2)),t);return t.width
    def logo(s,cx,cy,sy=1.0):
        lg=Image.open(LOGO).convert('RGB').resize((s,int(s*sy)),Image.LANCZOS);yy,xx=np.mgrid[0:lg.height,0:lg.width]
        r=np.hypot((xx-lg.width/2)/(lg.width/2),(yy-lg.height/2)/(lg.height/2))
        im.paste(lg,(int(cx-lg.width/2),int(cy-lg.height/2)),Image.fromarray((np.clip((1-r)/0.18,0,1)*255).astype(np.uint8)))
    acc=AM if kind=='cm' else CY
    # roof triangle: apex (1024,0), base y=1024. roof slant 3.16 m vs half-width 3 m -> close to 1:1 (no squash)
    D.rectangle([0,960,N,980],fill=MG);D.rectangle([0,992,N,1012],fill=acc)
    # valance 1024-1280 (6 m x 0.35 m -> squash text vertically: 256 px = 0.35 m, 2048 px = 6 m => 0.35/6*2048=119 px real -> sy 2.15)
    D.rectangle([0,1024,N,1036],fill=acc);D.rectangle([0,1266,N,1280],fill=MG)
    # back wall 1280-2032 (6 m x 2.4 m: 752 px for 2.4 m vs 2048 for 6 m -> 819 px real, sy 0.92)
    D.rectangle([0,1290,N,1300],fill=MG);D.rectangle([0,2010,N,2032],fill=acc)
    if kind=='vfad':
        logo(620,N//2,620,1.0);ct(N//2,1150,'VYBES FORGE  ·  vybesforge.com',font(110),TX,sy=1.0)
        logo(420,N//2,1560);ct(N//2,1850,'vybesforge.com',font(170),CY,0.92);ct(N//2,1965,'VYBES FORGE',font(64,500),TX,0.92)
    elif kind=='cm':
        ct(N//2,560,'DRIVEN BY',font(110,500),TX);wd=ct(N//2,720,'CRUSE MOB',font(220),AM);D.rectangle([N//2-wd//2,830,N//2+wd//2,842],fill=TX)
        ct(N//2,1150,'DRIVEN BY CRUSE MOB  ·  drivenbycrusemob.com',font(96),TX)
        ct(N//2,1560,'DRIVEN BY CRUSE MOB',font(170),TX,0.92);ct(N//2,1800,'drivenbycrusemob.com',font(120,500),AM,0.92)
    else:
        ct(N//2,700,'YOUR AD',font(180),CY);ct(N//2,865,'HERE',font(180),TX);D.rectangle([N//2-420,925,N//2+420,937],fill=MG)
        ct(N//2,1150,'ADVERTISE HERE  ·  I-29 SPEEDWAY',font(110),TX)
        ct(N//2,1560,'YOUR AD HERE',font(250),CY,0.92);ct(N//2,1800,'ADVERTISE AT I-29 SPEEDWAY',font(96,500),TX,0.92)
        ct(N//2,1920,f'TENT SLOT {slot:02d}',font(64,500),MG,0.92)
    D.rectangle([0,2032,N,N],fill=(10,14,24))
    rgba=np.dstack([np.array(im),np.full((N,N),255,np.uint8)]);Image.fromarray(rgba).save(f'{OUT}/tent_slot{slot:02d}.png')
    return B.write_dds(rgba,'DXT1',12,None)
PLAIN=(0.5,2040/N)
def face(P,UV,out):
    """polygon (3 or 4 pts) with UVs, normal forced towards `out` direction."""
    P=np.array(P,float);UV=np.array(UV,float);n=np.cross(P[1]-P[0],P[2]-P[0]);n/=np.linalg.norm(n)
    if np.dot(n,out)<0: n=-n
    # tangent along +u
    e1,e2=P[1]-P[0],P[2]-P[0];d1,d2=UV[1]-UV[0],UV[2]-UV[0];det=d1[0]*d2[1]-d2[0]*d1[1]
    t=(e1*d2[1]-e2*d1[1])/det if abs(det)>1e-9 else e1;t-=n*np.dot(t,n);t/=np.linalg.norm(t)+1e-12
    V=np.zeros((len(P),11));V[:,:3]=P;V[:,3:6]=n;V[:,6:8]=UV;V[:,8:11]=t
    I=np.array([[0,1,2]] if len(P)==3 else [[0,1,2],[0,2,3]]);return V,ML.fix_winding(V,I)
def two(P,UV,out,UVback=None):
    """double-sided: outside with UV, inside with UVback (default plain fabric)"""
    ub=UVback if UVback is not None else [PLAIN]*len(P);return [face(P,UV,out),face(P,ub,-np.asarray(out,float))]
def canopy(cx,cz,gy):
    hw,hd=W_/2,D_/2;e=gy+EAVE;a=gy+APEX;A=(cx,a,cz);fab=[];fr=[]
    C={'fl':(cx-hw,cz-hd),'fr':(cx+hw,cz-hd),'br':(cx+hw,cz+hd),'bl':(cx-hw,cz+hd)}
    # roof panels: (left corner, right corner) as seen from outside; outward dir
    for l,r,o in (('fl','fr',(0,1,-1)),('fr','br',(1,1,0)),('br','bl',(0,1,1)),('bl','fl',(-1,1,0))):
        L=(C[l][0],e,C[l][1]);R=(C[r][0],e,C[r][1])
        fab+=two([L,R,A],[(0,1024/N),(1,1024/N),(0.5,0)],o,[(1,1024/N),(0,1024/N),(0.5,0)])   # underside mirrored = readable from inside
        # valance below the eave
        Lb=(L[0],e-VAL,L[2]);Rb=(R[0],e-VAL,R[2])
        fab+=two([L,R,Rb,Lb],[(0,1024/N),(1,1024/N),(1,1280/N),(0,1280/N)],(o[0],0,o[2]))
    if BACK_WALL:   # +z side; seen from the front (inside) the art reads correctly, outside mirrored-correct too
        L=(cx+hw,e-VAL,cz+hd-0.02);R=(cx-hw,e-VAL,cz+hd-0.02);Rb=(cx-hw,gy-0.03,cz+hd-0.02);Lb=(cx+hw,gy-0.03,cz+hd-0.02)
        # outside (+z, viewer behind tent): left=+x
        fab.append(face([L,R,Rb,Lb],[(0,1280/N),(1,1280/N),(1,2032/N),(0,2032/N)],(0,0,1)))
        fab.append(face([L,R,Rb,Lb],[(1,1280/N),(0,1280/N),(0,2032/N),(1,2032/N)],(0,0,-1)))
    for k,(x,z) in C.items():
        ix=x-np.sign(x-cx)*0.03;iz=z-np.sign(z-cz)*0.03
        fr.append(ML.box((ix,gy+EAVE/2-0.02,iz),(0.05,EAVE+0.02,0.05)))          # square leg
        fr.append(ML.box((ix,gy+0.01,iz),(0.22,0.04,0.22)))                      # foot plate / weight
    for (x0,z0),(x1,z1) in ((C['fl'],C['fr']),(C['bl'],C['br'])): fr.append(ML.box((cx,e-0.06,z0-np.sign(z0-cz)*0.03),(W_-0.06,0.05,0.04)))
    for (x0,z0),(x1,z1) in ((C['fl'],C['bl']),(C['fr'],C['br'])): fr.append(ML.box((x0-np.sign(x0-cx)*0.03,e-0.06,cz),(0.04,0.05,D_-0.06)))
    # scissor truss (one diagonal per side, front + back) for the pop-up look
    for sz in (-1,1):
        z=cz+sz*(hd-0.03)
        for sx in(-1,1):
            p0=np.array([cx+sx*hw*0.98,e-0.08,z]);p1=np.array([cx,e-0.34,z]);m=(p0+p1)/2;L=np.linalg.norm(p1-p0)
            V,I=ML.box((0,0,0),(L,0.03,0.025));ang=np.arctan2(p1[1]-p0[1],p1[0]-p0[0])
            R=np.array([[np.cos(ang),-np.sin(ang),0],[np.sin(ang),np.cos(ang),0],[0,0,1]]);V=V.astype(float);V[:,:3]=V[:,:3]@R.T+m;V[:,3:6]=V[:,3:6]@R.T;V[:,8:11]=V[:,8:11]@R.T
            fr.append((V.astype('<f4'),I))
    FV,FI=ML.merge(fab);FV=FV.copy()
    # AC world is right-handed (y up; looking +z the viewer's right is -x): the UVs above were laid out with +x = right,
    # so flip u (and the tangent that follows +u) once for all fabric faces -> art reads unmirrored on every outer face
    FV[:,6]=1-FV[:,6];FV[:,8:11]*=-1
    return (FV,FI),ML.merge(fr)
# ---------------- verification (spawns, exit route, footprints on gravel)
def verify(report=print):
    from physraster import physmeshes,raster
    import kn5tree as T
    box=(-40,170,30,240);res=0.25;fails=0;heights={}
    files=['vf_i29_speedway.kn5','vf_i29_speedway_physical.kn5','vf_i29_speedway_gp.kn5','vf_i29_speedway_own.kn5','zw_ext.kn5','zw_dragexit.kn5','zw_vegetation.kn5']
    M=physmeshes(files,box);xs,zs,H,KEY,UP,names=raster(M,box,res)
    pits=[n['W'][3,:3] for n in T.walk(f'{Z}/vf_i29_speedway.kn5') if n['cls']==1 and n['name'].startswith('AC_PIT_')]
    path=np.load(f'{ROOT}/tools/data/path_main.npy')
    for s,x,z,k in SLOTS:
        ks=set();hs=[]
        for a in np.linspace(-W_/2-1,W_/2+1,15):
            for b in np.linspace(-D_/2-1,D_/2+1,15):
                ii=int(round((x+a-xs[0])/res));jj=int(round((z+b-zs[0])/res));kk=KEY[jj,ii];ks.add(names[kk] if kk>=0 else None);hs.append(H[jj,ii])
        hs=np.array(hs);dp=min(np.hypot(max(0,abs(p[0]-x)-W_/2-1.1),max(0,abs(p[2]-z)-D_/2-2.6)) for p in pits);dr=np.hypot(path[:,0]-x,path[:,1]-z).min()   # dp: gap tent<->car footprint;dr=np.hypot(path[:,0]-x,path[:,1]-z).min()
        dt=min(np.hypot(x-x2,z-z2) for s2,x2,z2,_ in SLOTS if s2!=s)
        ok=ks=={'1GRAVEL_PADDOCK'} and np.ptp(hs)<0.15 and dp>=8 and dr>=25 and dt>=15
        fails+=not ok;heights[s]=float(np.nanmin(hs))  # lowest point: nothing floats, high side sinks <=15 cm
        report(f'slot{s:02d} ({x:4},{z:4}) {k:6} surf={sorted(map(str,ks))} dz={np.ptp(hs):.3f} m  ground={heights[s]:+.3f}  car gap {dp:5.1f} m  exit-route {dr:5.1f} m  next tent {dt:4.1f} m  {"OK" if ok else "FAIL"}')
    report(f'{len(SLOTS)-fails}/{len(SLOTS)} slots OK (footprint +1 m margin on 1GRAVEL_PADDOCK, flat <15 cm, >=8 m gap to spawned cars, >=25 m from exit route, >=15 m apart)')
    return fails,heights,(xs,zs,H,KEY,names,pits,path)
if __name__=='__main__':
    fails,GY,_=verify()
    if fails or '--verify-only' in sys.argv: sys.exit(1 if fails else 0)
    _m=W.read_materials(f'{Z}/zw_tents.kn5');base=_m.get('vftent_adhere') or _m['vftent_slot01']   # v1.0.4 or v1.1 file (rerunnable)
    fnm=open(f'{ROOT}/assets_src/vr2/fabric_nm.dds','rb').read();fmp=open(f'{ROOT}/assets_src/vr2/fabric_maps.dds','rb').read()
    T_=lambda n:open(f'{ROOT}/assets_src/{n}','rb').read()
    texs=[('fabric_nm.dds',fnm),('fabric_maps.dds',fmp),('NULL.dds',ML.solid_dds((255,255,255))),
          ('own_galv.dds',T_('textures/own_galv.dds')),('own_galv_nm.dds',T_('vr2/own_galv_nm.dds')),('own_galv_maps.dds',T_('vr2/own_galv_maps.dds'))]
    mats=[dict(name='vftent_frame',shader=base['shader'],ab=0,at=0,dm=base['dm'],props=base['props'],
               samplers=[('txDiffuse',0,'own_galv.dds'),('txNormal',1,'own_galv_nm.dds'),('txMaps',2,'own_galv_maps.dds'),('txDetail',3,'NULL.dds')])]
    meshes=[];os.makedirs(EXT,exist_ok=True)
    for s,x,z,k in SLOTS:
        dds=art(k,s);tn=f'tent_slot{s:02d}.dds';texs.append((tn,dds));open(f'{EXT}/{tn}','wb').write(dds)
        mats.append(dict(name=f'vftent_slot{s:02d}',shader=base['shader'],ab=0,at=0,dm=base['dm'],props=base['props'],
                         samplers=[('txDiffuse',0,tn),('txNormal',1,'fabric_nm.dds'),('txMaps',2,'fabric_maps.dds'),('txDetail',3,'NULL.dds')]))
        (FV,FI),(RV,RI)=canopy(x,z,GY[s])
        meshes.append(dict(name=f'vftent_slot{s:02d}',mat_index=len(mats)-1,verts=FV,idx=FI,lod_out=0))
        meshes.append(dict(name=f'vftent_slot{s:02d}_frame',mat_index=0,verts=RV,idx=RI,lod_out=600))
    W.write_kn5(f'{Z}/zw_tents.kn5',texs,mats,meshes,rootname='zw_tents')
    print('zw_tents.kn5:',len(meshes),'meshes',sum(len(m['idx']) for m in meshes),'tris',len(mats),'materials')
