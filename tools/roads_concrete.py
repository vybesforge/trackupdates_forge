"""roads-concrete: cracked-concrete surface (Concrete01 look, physics key CONCRETE) on
 (1) the drag-strip return road west of the strip: vf_dragexit 1XROAD_dragexit_return + east connectors _B and _C
     (copies of their triangles lifted 2 cm, so the overlay is what the wheels and the camera see);
 (2) the south boundary road (Jesup Ave, satellite texture only, no mesh before): new 8 m overlay x -399..205 along the
     painted road in the google aerial. Its bumps are smoothed 50 %: terrain vertices (1GRASS_*, vf_i29_speedway.kn5, visual =
     physics) within 7 m the overlay centre follows h + 0.5*(lowpass - h) (full inside 2.5 m, fading to plain terrain + 2 cm at the 4 m edge and over 12 m at the ends);
     terrain vertices (1GRASS_*, vf_i29_speedway.kn5, visual = physics) under it are lowered where needed so the overlay stays on top.
Writes vf_i29_speedway/vf_roads.kn5 and patches vertex heights in vf_i29_speedway/vf_i29_speedway.kn5 (same size, in place).
Run: python3 tools/roads_concrete.py [--dry]"""
import os,sys,struct,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import kn5write as W,kn5patch as K,vr5_meshlib as ML,vismeshes as VM,physraster as PR
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));Z=f'{ROOT}/vf_i29_speedway';MAIN=f'{Z}/vf_i29_speedway.kn5'
# terrain is read from the UNPATCHED v1.1.0 main kn5 (so reruns don't smooth twice): VF_MAIN_SRC=/path/to/v1.1.0/vf_i29_speedway.kn5
SRC=os.environ.get('VF_MAIN_SRC','/tmp/main_before.kn5')
LIFT=0.02;T_=np.array([0.8396,0,-0.5432])
def uv(x,z): return (-0.0168*x+0.0109*z+1.79,-0.0109*x-0.0167*z)   # same world mapping as the drift pad (1CONCRETE_DRIFT)
# south road centre line (x, z) from the google aerial road (light grey band), every 25 m; width 8 m
SR=np.array([(-399,243.4),(-380,243.2),(-355,243.2),(-330,243.8),(-305,244),(-280,244.2),(-255,244.5),(-230,244.5),(-205,244),(-180,244.8),
             (-155,244.5),(-130,244.8),(-105,244.8),(-80,244.8),(-55,245),(-30,245.2),(-5,245.2),(20,245.8),(45,246.8),(70,246.5),(95,246.5),
             (120,247),(145,246.5),(170,247.2),(205,247.5)],float)
HALF=4.0;INNER=2.5;END=12.0;SIG=8.0
def centreline(step=1.0):
    s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(SR,axis=0),axis=1))];q=np.arange(0,s[-1]+1e-6,step)
    P=np.stack([np.interp(q,s,SR[:,0]),np.interp(q,s,SR[:,1])],1);t=np.gradient(P,axis=0);t/=np.linalg.norm(t,axis=1,keepdims=True)
    return q,P,t,np.stack([t[:,1],-t[:,0]],1)
def lowpass(h,sig=SIG):
    k=np.arange(-int(3*sig),int(3*sig)+1);g=np.exp(-0.5*(k/sig)**2);g/=g.sum();hp=np.pad(h,len(k)//2,mode='edge');return np.convolve(hp,g,'valid')
def rough(h,m=slice(None)): return float(np.sqrt(np.mean(((h-lowpass(h))[m])**2)))
def tri_raster(meshes,box,res=0.25):
    return PR.raster(meshes,box,res)
def terrain_meshes(path,box):
    return [m for m in VM.vismeshes(path,box) if m['name'].startswith('1GRASS')]
def sample(xs,zs,H,P):
    i=np.clip(np.round((P[:,0]-xs[0])/(xs[1]-xs[0])).astype(int),0,len(xs)-1);j=np.clip(np.round((P[:,1]-zs[0])/(zs[1]-zs[0])).astype(int),0,len(zs)-1);return H[j,i]
def main(dry=False):
    q,P,t,n=centreline();box=(-410,215,225,268)
    assert os.path.exists(SRC),'set VF_MAIN_SRC to the unpatched v1.1.0 vf_i29_speedway.kn5';TM=terrain_meshes(SRC,box);asT=lambda ms:[('m',m['name'],m['V'][m['I'].astype(int)][:,:,:3].astype(float)) for m in ms]
    xs,zs,H,KEY,UP,names=tri_raster(asT(TM),box);h0=sample(xs,zs,H,P)
    lp=lowpass(h0);L=q[-1];endw=np.clip(np.minimum(q,L-q)/END,0,1)
    dc=0.5*(lp-h0)*endw                                  # centre-line correction (50 % toward the low-pass profile)
    offs=np.arange(-HALF,HALF+0.5,0.5);G=P[:,None,:]+offs[None,:,None]*n[:,None,:]
    wl=np.clip((HALF-np.abs(offs))/(HALF-INNER),0,1)       # 1 inside INNER, 0 at the overlay edge -> no lip
    Hg=sample(xs,zs,H,G.reshape(-1,2)).reshape(G.shape[:2]);Y=Hg+LIFT+wl[None,:]*dc[:,None]
    # terrain vertices under the overlay are pushed down where the overlay was lowered (crests), iterated until terrain < overlay
    d=bytearray(open(SRC,'rb').read());moved=set();tmp='/tmp/_main_patched.kn5'
    def vert_list():
        out=[]
        for m in terrain_meshes(SRC,box):
            V=m['V'];x,z=V[:,0].astype(float),V[:,2].astype(float)
            for vi in np.nonzero((x>-402)&(x<212)&(z>230)&(z<262))[0]:
                dd=(P[:,0]-x[vi])**2+(P[:,1]-z[vi])**2;k=int(dd.argmin());lat=float((np.array([x[vi],z[vi]])-P[k])@n[k])
                if abs(lat)<HALF+1.5: out.append((m['vo']+vi*44+4,k,lat))
        return out
    VL=vert_list()
    for it in range(6):
        for o,k,lat in VL:
            j=int(np.clip(np.round((lat+HALF)/0.5),0,len(offs)-1));y,=struct.unpack_from('<f',d,o);lim=Y[k,j]-0.03
            if y>lim: struct.pack_into('<f',d,o,lim);moved.add(o)
        open(tmp,'wb').write(bytes(d));xs,zs,H2,*_=tri_raster(asT(terrain_meshes(tmp,box)),box)
        T2=sample(xs,zs,H2,G.reshape(-1,2)).reshape(G.shape[:2]);bad=(T2>Y-0.005)
        print(f'  iter {it}: terrain above overlay at {int(bad.sum())} of {bad.size} overlay points')
        if not bad.any(): break
        Y=np.where(bad,T2+0.01,Y)    # residual: lift the overlay locally instead of digging further
    h1=Y[:,len(offs)//2]-LIFT;maxd=max(abs(struct.unpack_from('<f',d,o)[0]-struct.unpack_from('<f',open(SRC,'rb').read(),o)[0]) for o in moved) if moved else 0
    print(f'south road: {L:.0f} m, terrain vertices lowered {len(moved)}, max {maxd:.3f} m')
    mi=endw>=1;r=lambda h:1000*np.sqrt(np.mean((h-lp)[mi]**2));c2=lambda h:1000*np.sqrt(np.mean(np.diff(h,2)[mi[1:-1]]**2))
    print(f'  bumps vs the original {SIG:.0f} m low-pass profile (centre line, outside the {END:.0f} m end tapers): RMS {r(h0):.1f} -> {r(h1):.1f} mm, '
          f'max {1000*np.abs(h0-lp)[mi].max():.0f} -> {1000*np.abs(h1-lp)[mi].max():.0f} mm, RMS 2nd difference (1 m) {c2(h0):.2f} -> {c2(h1):.2f} mm')
    meshes=[]
    for part in np.array_split(np.arange(len(P)-1),3):
        V=[];I=[];vid={}
        def v(a,b):
            if (a,b) not in vid:
                x,z=G[a,b];u,w_=uv(x,z);vid[a,b]=len(V);V.append([x,Y[a,b],z,0,1,0,u,w_,*T_])
            return vid[a,b]
        for a in part:
            for b in range(len(offs)-1):
                p0,p1,p2,p3=v(a,b),v(a+1,b),v(a+1,b+1),v(a,b+1);I+=[[p0,p2,p1],[p0,p3,p2]]
        V=np.array(V,'<f4');I=np.array(I);meshes.append((V,I))
    # drag return road overlays: copies of the 1XROAD triangles + LIFT
    DX=f'{Z}/vf_dragexit.kn5';drag=[]
    for m in VM.vismeshes(DX):
        if m['name'] in('1XROAD_dragexit_return','1XROAD_dragexit_B','1XROAD_dragexit_C'):
            V=m['V'].astype(float).copy();V[:,1]+=LIFT;u=np.array([uv(x,z) for x,z in V[:,[0,2]]]);V[:,6:8]=u;V[:,8:11]=T_
            drag.append((m['name'].replace('1XROAD_dragexit','1CONCRETE_DRAGX'),V.astype('<f4'),m['I'].astype(int)))
    def fixn(V,I):
        Pp=V[:,:3].astype(float);fn=np.cross(Pp[I[:,1]]-Pp[I[:,0]],Pp[I[:,2]]-Pp[I[:,0]]);fn*=np.sign(fn[:,1:2]+1e-12);vn=np.zeros_like(Pp)
        for c in range(3): np.add.at(vn,I[:,c],fn)
        V=V.copy();nl=np.linalg.norm(vn,axis=1,keepdims=True);vn[nl[:,0]<1e-9]=(0,1,0);nl[nl<1e-9]=1;V[:,3:6]=vn/nl;return V,ML.fix_winding(V,I).astype('<u2')
    cm=W.read_materials(MAIN)['Concrete01'];texs=[(tn,K.get_tex(MAIN,tn)) for tn in dict.fromkeys(t for _,_,t in cm['samplers'])]
    mats=[dict(name='Concrete01_roads',shader=cm['shader'],ab=cm['ab'],at=cm['at'],dm=cm['dm'],props=cm['props'],samplers=cm['samplers'])]
    out=[]
    for i,(V,I) in enumerate(meshes): V,I=fixn(V,I);out.append(dict(name=f'1CONCRETE_SOUTHRD_{i}',mat_index=0,verts=V,idx=I,lod_out=0))
    for nm,V,I in drag: V,I=fixn(V,I);out.append(dict(name=nm,mat_index=0,verts=V,idx=I,lod_out=0))
    info=dict(h0=h0,h1=h1,P=P,q=q)
    if dry: return info
    W.write_kn5(f'{Z}/vf_roads.kn5',texs,mats,out,rootname='vf_roads');open(MAIN,'wb').write(bytes(d))
    print('vf_roads.kn5:',[o['name'] for o in out],os.path.getsize(f'{Z}/vf_roads.kn5')//1024,'KB; vf_i29_speedway.kn5 terrain patched')
    np.savez('/tmp/roads_profile.npz',**info);return info
if __name__=='__main__': main('--dry' in sys.argv)
