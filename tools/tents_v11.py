"""Tents v1.1 (pass 3: v2 tent design around the paddock drift course in tools/drift_course.py): 12-tent car-meet vendor cluster right behind the spawns, one material + texture per slot.
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
CH=(42,43,46);WH=(244,244,244);LG=(214,214,214);MG_=(120,120,124);BK=(14,14,16);N=2048;NK=512   # kn5 fallback art 512 (CSP loads the 2048 overrides) to make room for the drift-pad concrete textures
W_,D_,EAVE,APEX,VAL,SAG,BACK_WALL=6.0,6.0,2.4,3.3,0.30,0.07,True
# slot, x, z, yaw (rad; 0 = opening faces -z). Left column opens +x (yaw -pi/2), right column opens -x (yaw +pi/2).
import drift_course as DC
NSLOTS=18
SLOTS=[]   # filled by verify(): (slot, x, z, yaw) placed along the outside of the drift course, opening towards the drift line
FLAGS=set(range(1,NSLOTS+1,2))
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
def canopy_local(slot,lift=0.012):
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
    sh=[ML.quad((-hw-0.4,lift,hd+0.4),(hw+0.4,lift,hd+0.4),(hw+0.4,lift,-hd-0.4),(-hw-0.4,lift,-hd-0.4))]
    FV,FI=ML.merge(fab);FV=FV.copy()
    # AC world is right-handed (y up; looking +z the viewer's right is -x): flip u once for all fabric -> art unmirrored
    FV[:,6]=1-FV[:,6];FV[:,8:11]*=-1
    return {'fab':(FV,FI),'frame':ML.merge(fr),'bag':ML.merge(bag),'top':ML.merge(top),'shadow':ML.merge(sh)}
def canopy(cx,cz,gy,yaw,slot,lift=0.012):
    return {k:ML.xform(VI,yaw,(cx,gy,cz)) for k,VI in canopy_local(slot,lift).items()}
# ---------------- verification (spawns, exit route, footprints on gravel)
HMAX={}
CONC_Z0=93.0   # drift pad (cracked concrete) starts here; spawn zone z < 93 stays gravel
CONC_LIFT=0.02
def verify(report=print):
    """course + tent placement checks on the physics raster; fills SLOTS. returns fails, ground heights, raster data"""
    from physraster import physmeshes,raster
    import kn5tree as T
    global SLOTS
    HMAX.clear()
    box=(-40,170,30,240);res=0.25;fails=0
    files=['vf_i29_speedway.kn5','vf_i29_speedway_physical.kn5','vf_i29_speedway_gp.kn5','vf_i29_speedway_own.kn5','zw_ext.kn5','zw_dragexit.kn5','zw_vegetation.kn5']
    M=physmeshes(files,box);xs,zs,H,KEY,UP,names=raster(M,box,res)
    pits=[n['W'][3,:3] for n in T.walk(f'{Z}/vf_i29_speedway.kn5') if n['cls']==1 and n['name'].startswith('AC_PIT_')]
    path=np.load(f'{ROOT}/tools/data/path_main.npy');GRAV=names.index('1GRAVEL_PADDOCK')
    def cell(x,z): return int(round((z-zs[0])/res)),int(round((x-xs[0])/res))
    def disc_ok(x,z,r):
        hs=[]
        for a in np.linspace(0,2*np.pi,24,endpoint=False):
            for rr in (0,r*0.5,r):
                j,i=cell(x+rr*np.cos(a),z+rr*np.sin(a))
                if KEY[j,i]!=GRAV: return False,None
                hs.append(H[j,i])
        HMAX[(round(x,2),round(z,2))]=float(np.max(hs));return np.ptp(hs)<0.15,float(np.min(hs))
    def cargap(x,z,half=4.25):
        return min(np.hypot(max(0,abs(p[0]-x)-half-1.1),max(0,abs(p[2]-z)-half-2.6)) for p in pits)
    onlot=lambda x,z:disc_ok(x,z,4.25+1)[0];carclear=lambda x,z:cargap(x,z)>=9;exitclear=lambda x,z:np.hypot(path[:,0]-x,path[:,1]-z).min()>=25
    SLOTS=DC.tent_slots(onlot,carclear,exitclear,n=NSLOTS,spacing=9.0)
    C=DC.course();L=C['line'];heights={}
    # course: drift line +-4 m on gravel, clear of spawned cars (>= 8 m) and the exit route
    bad=sum(1 for x,z in L[::2] if not disc_ok(x,z,4.0)[0]);cg=min(cargap(x,z,0.0) for x,z in L[::3])
    ok=bad==0 and cg>=8;fails+=not ok
    report(f'course: drift line {len(L)} m, {len(C["clips"])} clipping points, {len(C["walls"])} barrier runs; samples off-gravel/rough: {bad}; gap to spawned cars {cg:.1f} m  {"OK" if ok else "FAIL"}')
    wb=sum(1 for w in C['walls'] for x,z in w if not disc_ok(x,z,0.5)[0]);wg=min(cargap(x,z,0.3) for w in C['walls'] for x,z in w)
    wl=min(DC.dist_line((x,z)) for w in C['walls'] for x,z in w);ok=wb==0 and wg>=6;fails+=not ok
    report(f'barriers: {sum(len(w) for w in C["walls"])} m, off-gravel samples {wb}, min {wl:.1f} m from the drift line, gap to spawned cars {wg:.1f} m  {"OK" if ok else "FAIL"}')
    W_all=np.vstack(C['walls'])
    for s,x,z,yaw in SLOTS:
        okf,gy=disc_ok(x,z,4.25+1);dp=cargap(x,z);dr=np.hypot(path[:,0]-x,path[:,1]-z).min();dl=DC.dist_line((x,z))
        dw=np.hypot(W_all[:,0]-x,W_all[:,1]-z).min();dt=min(np.hypot(x-x2,z-z2) for s2,x2,z2,_ in SLOTS if s2!=s)
        ok=okf and dp>=9 and dr>=25 and dl>=15 and dw>=7.5 and dt>=9 and not DC.inside((x,z));fails+=not ok;heights[s]=gy if gy is not None else 0.0
        report(f'slot{s:02d} ({x:5.1f},{z:5.1f}) yaw {np.degrees(yaw):6.1f}  drift line {dl:4.1f} m (edge >= {dl-4.25:4.1f})  barrier {dw:4.1f} m  car gap {dp:5.1f} m  exit {dr:5.1f} m  next tent {dt:4.1f} m  {"OK" if ok else "FAIL"}')
    report(f'{len(SLOTS)}/{NSLOTS} slots placed, {len(SLOTS)-sum(1 for _ in [])} checked; fails total {fails} (tent footprint r 5.25 m on 1GRAVEL_PADDOCK, >=15 m from the drift line, outside the loop, >=7.5 m from barriers, >=9 m car gap, >=25 m exit route, >=9 m apart)')
    if len(SLOTS)<NSLOTS: fails+=1
    def hat(x,z):
        j,i=cell(x,z);v=H[j,i];return float(v) if np.isfinite(v) else -0.25
    return fails,heights,(xs,zs,H,KEY,names,pits,path,hat,(xs,zs,H,KEY,GRAV))
# ---------------- drift pad: cracked concrete overlay (same material/textures as 1CONCRETE_001 'Concrete01', surface key CONCRETE)
def concrete_pad(RAST,cell=1.0):
    """1 m grid over every gravel cell of the paddock lot with z >= CONC_Z0, +2 cm above the gravel (physics ray hits it first).
    Clean straight edge at z = CONC_Z0 towards the gravel spawn zone. Returns list of (V,I) meshes (<65k verts each)."""
    xs,zs,H,KEY,GRAV=RAST;res=xs[1]-xs[0]
    def k(x,z):
        j=int(round((z-zs[0])/res));i=int(round((x-xs[0])/res));return KEY[j,i]==GRAV,H[j,i]
    X=np.arange(4,160+cell,cell);Zs=np.arange(CONC_Z0,224+cell,cell);ok=np.zeros((len(Zs),len(X)),bool);hh=np.zeros(ok.shape)
    for a,z in enumerate(Zs):
        for b,x in enumerate(X): ok[a,b],hh[a,b]=k(x,z)
    cellok=ok[:-1,:-1]&ok[1:,:-1]&ok[:-1,1:]&ok[1:,1:]
    T=np.array([0.8396,0,-0.5432])
    def uv(x,z): return (-0.0168*x+0.0109*z+1.79,-0.0109*x-0.0167*z)
    meshes=[];rows=np.array_split(np.arange(cellok.shape[0]),3)
    for rr in rows:
        vid={};V=[];I=[]
        def v(a,b):
            if (a,b) not in vid:
                x,z=X[b],Zs[a];u,w=uv(x,z);vid[a,b]=len(V);V.append([x,hh[a,b]+CONC_LIFT,z,0,1,0,u,w,*T])
            return vid[a,b]
        for a in rr:
            for b in np.nonzero(cellok[a])[0]:
                p0,p1,p2,p3=v(a,b),v(a,b+1),v(a+1,b+1),v(a+1,b);I+=[[p0,p2,p1],[p0,p3,p2]]
        V=np.array(V,'<f4');I=np.array(I,'<u2')
        # smooth vertex normals from the lidar grade
        P=V[:,:3].astype(float);fn=np.cross(P[I[:,1]]-P[I[:,0]],P[I[:,2]]-P[I[:,0]]);fn*=np.sign(fn[:,1:2]+1e-12);vn=np.zeros_like(P)
        for c in range(3): np.add.at(vn,I[:,c].astype(int),fn)
        V[:,3:6]=vn/np.linalg.norm(vn,axis=1,keepdims=True);I=ML.fix_winding(V,I.astype(int)).astype('<u2');meshes.append((V,I))
    return meshes,int(cellok.sum())
# ---------------- course meshes
def course_meshes(hat):
    C=DC.course();out={'wall':[],'cone':[],'tyre':[],'paint':[]}
    prof=[(0.30,0.0),(0.30,0.08),(0.12,0.33),(0.08,0.81)]   # jersey barrier half-width / height
    for wi,w in enumerate(C['walls']):
        w=w[::2] if len(w)>4 else w;t=np.gradient(w,axis=0);t/=np.linalg.norm(t,axis=1,keepdims=True);nr=np.stack([t[:,1],-t[:,0]],1)
        parts=[]
        for side in (-1,1):
            for a in range(len(prof)-1):
                for i in range(len(w)-1):
                    P=[]
                    for (hw,hy),ii in ((prof[a],i),(prof[a],i+1),(prof[a+1],i+1),(prof[a+1],i)):
                        g=hat(*w[ii])-0.03;xy=w[ii]+side*hw*nr[ii];P.append((xy[0],g+hy+(0.03 if hy==0 else 0),xy[1]))
                    mid=w[i]+side*nr[i];parts.append(face(P,[(0,0),(1,0),(1,1),(0,1)],(side*nr[i][0],0.3,side*nr[i][1])))
        for i in (0,len(w)-1):   # end caps
            g=hat(*w[i]);d=t[i]*(-1 if i==0 else 1);P=[(w[i][0]+s_*hw*nr[i][0],g+hy,w[i][1]+s_*hw*nr[i][1]) for s_,(hw,hy) in [(-1,prof[0]),(1,prof[0]),(1,prof[-1]),(-1,prof[-1])]]
            parts.append(face(P,[(0,0),(1,0),(1,1),(0,1)],(d[0],0,d[1])))
        out['wall'].append(ML.merge(parts))
    cones=[];tyres=[];paint=[]
    def cone(x,z):
        g=hat(x,z);V,I=ML.cyl((x,g,z),0.15,0.7,n=10,cap=False);V=V.astype(float);top=V[:,1]>g+0.35;V[top,0]=x+(V[top,0]-x)*0.15;V[top,2]=z+(V[top,2]-z)*0.15
        return [(V.astype('<f4'),I),ML.box((x,g+0.015,z),(0.38,0.03,0.38))]
    t,n,k=DC.frames()
    for (cx,cz),ci in zip(C['clips'],C['clip_idx']):
        g=hat(cx,cz)
        for lvl in range(3): tyres.append(ML.cyl((cx,g+lvl*0.22,cz),0.33,0.21,n=14))
        for a in (0,2.1,4.2): cones+=cone(cx+1.3*np.cos(a),cz+1.3*np.sin(a))
    for cx,cz in C['line'][::40]: pass
    def ribbon(P,wd):
        P=np.asarray(P);t_=np.gradient(P,axis=0);t_/=np.linalg.norm(t_,axis=1,keepdims=True);nr=np.stack([t_[:,1],-t_[:,0]],1);parts=[]
        for i in range(len(P)-1):
            Q=[]
            for ii,sd in ((i,-1),(i+1,-1),(i+1,1),(i,1)): xy=P[ii]+sd*wd/2*nr[ii];Q.append((xy[0],hat(*xy)+CONC_LIFT+0.025,xy[1]))
            parts.append(face(Q,[(0,0),(1,0),(1,1),(0,1)],(0,1,0)))
        return ML.merge(parts)
    for zl in C['zones']: paint.append(ribbon(zl,0.15))
    for (cx,cz) in C['clips']:
        a=np.linspace(0,2*np.pi,25);paint.append(ribbon(np.stack([cx+2.0*np.cos(a),cz+2.0*np.sin(a)],1),0.12))
    dx,dz,dr_=C['donut'];a=np.linspace(0,2*np.pi,73);paint.append(ribbon(np.stack([dx+dr_*np.cos(a),dz+dr_*np.sin(a)],1),0.2))
    for lvl in range(3): tyres.append(ML.cyl((dx,hat(dx,dz)+lvl*0.22,dz),0.33,0.21,n=14))
    e=C['line'][0];tt=t[0];nr=np.array([tt[1],-tt[0]]);paint.append(ribbon(np.stack([e+s_*nr for s_ in np.linspace(-5,5,11)]),0.35))   # entry line
    out['cone']=ML.merge(cones);out['tyre']=ML.merge(tyres);out['paint']=ML.merge(paint);return out
def write_ext_config(n):
    e=f'{EXT}/ext_config.ini';c=open(e,'rb').read().decode();a=c.index('; >>> v1.1 tents');b=c.index('; <<< v1.1 tents')+len('; <<< v1.1 tents')
    L=['; >>> v1.1 tents: per-slot ad artwork (rotate ads by replacing extension/tent_slotNN.dds / board_slotNN.dds; kn5 files stay unchanged)',
       f'; {n} tent slots + 2 drag-end billboard slots, all open (YOUR AD HERE). Without CSP the art baked in the kn5 shows.']
    for i in range(1,n+1): L+=['',f'[SHADER_REPLACEMENT_TENT_SLOT{i:02d}]','ACTIVE = 1',f'MATERIALS = vftent_slot{i:02d}','RESOURCE_0 = txDiffuse',f'RESOURCE_FILE_0 = tent_slot{i:02d}.dds']
    L+=['','[MATERIAL_ADJUSTMENT_TENT_NIGHT]','DESCRIPTION = v1.1 tents: subtle self-lit fabric at night so ads stay readable','MATERIALS = vftent_slot??',
        'KEY_0 = ksEmissive','VALUE_0 = 1.0, 1.0, 1.0, 0.35','VALUE_0_OFF = 0, 0, 0','CONDITION = NIGHT_SMOOTH']
    for i in (1,2): L+=['',f'[SHADER_REPLACEMENT_BOARD_SLOT{i:02d}]','ACTIVE = 1',f'MATERIALS = vfboard_slot{i:02d}','RESOURCE_0 = txDiffuse',f'RESOURCE_FILE_0 = board_slot{i:02d}.dds']
    L+=['','[MATERIAL_ADJUSTMENT_BOARD_NIGHT]','DESCRIPTION = v1.1 drag-end billboards: backlit look at night','MATERIALS = vfboard_slot??',
        'KEY_0 = ksEmissive','VALUE_0 = 1.0, 1.0, 1.0, 0.6','VALUE_0_OFF = 0, 0, 0','CONDITION = NIGHT_SMOOTH','','; <<< v1.1 tents']
    c=c[:a]+'\n'.join(L)+c[b:];assert '\r' not in c;open(e,'wb').write(c.encode())
if __name__=='__main__':
    fails,GY,RD=verify();hat=RD[-2];RAST=RD[-1]
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
    texs+=[('vfc_concrete.dds',ML.solid_dds((178,176,170))),('vfc_cone.dds',ML.solid_dds((235,90,20))),('vfc_tyre.dds',ML.solid_dds((20,20,22))),('vfc_paint.dds',ML.solid_dds((235,235,230)))]
    mats+=[solid('vfc_concrete','vfc_concrete.dds',0.05,8),solid('vfc_cone','vfc_cone.dds',0.2,20),solid('vfc_tyre','vfc_tyre.dds',0.1,10),solid('vfc_paint','vfc_paint.dds',0.05,8)]
    MI={'frame':0,'bag':1,'top':2,'shadow':3};meshes=[];os.makedirs(EXT,exist_ok=True)
    CM=course_meshes(hat)
    import kn5patch as KP2
    SRCM=f'{Z}/vf_i29_speedway.kn5';cm=W.read_materials(SRCM)['Concrete01']
    for t in dict.fromkeys(t for _,_,t in cm['samplers']): texs.append((t,KP2.get_tex(SRCM,t)))
    mats.append(dict(name='Concrete01_drift',shader=cm['shader'],ab=cm['ab'],at=cm['at'],dm=cm['dm'],props=cm['props'],samplers=cm['samplers']));ci=len(mats)-1
    pads,ncell=concrete_pad(RAST)
    for pi,(V,I) in enumerate(pads): meshes.append(dict(name=f'1CONCRETE_DRIFT_{pi}',mat_index=ci,verts=V,idx=I,lod_out=0))   # physics: CONCRETE (surfaces.ini KEY=CONCRETE)
    print('drift pad: %d m2 cracked concrete'%ncell)
    for wi,(V,I) in enumerate(CM['wall']): meshes.append(dict(name=f'1WALL_DRIFT_{wi}',mat_index=4,verts=V,idx=I,lod_out=0))   # physics: collides (WALL)
    meshes.append(dict(name='vfc_cones',mat_index=5,verts=CM['cone'][0],idx=CM['cone'][1],lod_out=500))
    meshes.append(dict(name='vfc_tyre_stacks',mat_index=6,verts=CM['tyre'][0],idx=CM['tyre'][1],lod_out=500))
    meshes.append(dict(name='vfc_paint',mat_index=7,verts=CM['paint'][0],idx=CM['paint'][1],lod_out=400,flags=(1,0,0)))
    for f in os.listdir(EXT):
        if f.startswith('tent_slot') and int(f[9:11])>NSLOTS: os.remove(f'{EXT}/{f}')
    for s,x,z,yaw in SLOTS:
        big,small=art(s);tn=f'tent_slot{s:02d}.dds';texs.append((tn,small));open(f'{EXT}/{tn}','wb').write(big)
        mats.append(dict(name=f'vftent_slot{s:02d}',shader=base['shader'],ab=0,at=0,dm=base['dm'],props=base['props'],
                         samplers=[('txDiffuse',0,tn),('txNormal',1,'fabric_nm_v2.dds'),('txMaps',2,'fabric_maps.dds'),('txDetail',3,'NULL.dds')]))
        parts=canopy(x,z,GY[s],yaw,s,lift=HMAX[(round(x,2),round(z,2))]-GY[s]+CONC_LIFT+0.025)
        meshes.append(dict(name=f'vftent_slot{s:02d}',mat_index=len(mats)-1,verts=parts['fab'][0],idx=parts['fab'][1],lod_out=0))
        for k in ('frame','bag','top'): meshes.append(dict(name=f'vftent_slot{s:02d}_{k}',mat_index=MI[k],verts=parts[k][0],idx=parts[k][1],lod_out=400))
        meshes.append(dict(name=f'vftent_slot{s:02d}_shadow',mat_index=3,verts=parts['shadow'][0],idx=parts['shadow'][1],lod_out=300,flags=(1,0,0)))
    W.write_kn5(f'{Z}/zw_tents.kn5',texs,mats,meshes,rootname='zw_tents');write_ext_config(NSLOTS)
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
