"""VR7: regenerate AI lines (fast_lane.ai + pit_lane.ai) for main (long) and short layouts from the CURRENT physics.
Also builds zw_vr7_longcut.kn5 (main/long only): invisible physics copy (+1 cm, bumps kept) of the short-course T1 hairpin road,
KEY SCUT = IS_VALID_TRACK 0, so cutting through the short course on the long layout counts as off-track.
Seeds = zwiss's recorded 2023 lines (assets_src/ai_zwiss_orig/), which are only used as a lateral reference / direction:
 fast lane: lateral corridor from the physics raster (valid ROAD/CURB only), min-curvature relaxation inside the corridor
            (1.1 m margin), y = physics + 0.40 m, speeds from curvature (mu*g) + accel/brake passes, gas/brake from the passes.
 pit lane : pit-in .. pit lane (zwiss) -> east concrete link -> paddock lane in front of the 36 paddock boxes -> west concrete
            link -> pit exit (zwiss), routed by A* on drivable physics with a centre-preferring cost, then smoothed.
Run: venv python tools/vr7_ai.py   (then tools/vr7_ai_validate.py)."""
import sys,os,struct,heapq,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import vr7_common as C,kn5patch as K,kn5write as W,kn5tree as T
from scipy.spatial import cKDTree
from scipy import ndimage
Z=C.Z;ORIG='/workspace/rpotm/project/assets_src/ai_zwiss_orig'
RES=0.5;G=9.81
# ---------------- 0. long-course cut mesh (main only)
def build_cut():
    m=C.read_ai(f'{ORIG}/main/fast_lane.ai')['P']['p'][:,[0,2]];s=C.read_ai(f'{ORIG}/short/fast_lane.ai')['P']['p'][:,[0,2]]
    so=s[cKDTree(m).query(s)[0]>8];ts=cKDTree(so)
    # long-course road band = smoothed corridor centre of the long line (short raster has no SCUT) +- half width + 0.3 m
    g=Grid('short');mm=resample(m,1.5,True);t,n=normals(mm,True);L,R=corridor(g,mm,n,{'ROAD','CURB'})
    w=ndimage.median_filter(R-L,41,mode='wrap');cen=mm+ndimage.gaussian_filter1d((L+R)/2,15,mode='wrap')[:,None]*n
    tm=cKDTree(cen);half=w/2+0.3
    d=open(Z+'zw_rpm_physical.kn5','rb').read();V_=[];I_=[]
    for nm,o,l,c in K.scan(Z+'zw_rpm_physical.kn5')[1]:
        if c!=2 or not nm.startswith('1ROAD_0'): continue
        q=o+l+8;nv,=struct.unpack_from('<I',d,q);V=np.frombuffer(d,'<f4',nv*11,q+4).reshape(nv,11);q2=q+4+nv*44;ni,=struct.unpack_from('<I',d,q2);I=np.frombuffer(d,'<u2',ni,q2+4).reshape(-1,3)
        P=V[I][:,:,[0,2]].reshape(-1,2);dq,iq=tm.query(P);dm=(dq-half[iq]).reshape(-1,3);ds=ts.query(P)[0].reshape(-1,3)
        k=(dm>0).all(1)&(ds<12).all(1)
        if not k.any(): continue
        u,inv=np.unique(I[k],return_inverse=True);Vo=V[u].copy();Vo[:,1]+=0.01;V_.append(Vo);I_.append(inv.reshape(-1,3))
    off=0;VV=[];II=[]
    for v,i in zip(V_,I_): VV.append(v);II.append(i+off);off+=len(v)
    VV=np.vstack(VV);II=np.vstack(II);print('long-course cut mesh 1SCUT_hairpin tris',len(II))
    mat=W.read_materials(Z+'zw_tents.kn5');m0=list(mat.values())[0]
    M=[dict(name='vr7_cut_invisible',shader='ksPerPixel',ab=0,at=0,dm=m0['dm'],props=m0['props'],samplers=[])]
    W.write_kn5(Z+'zw_vr7_longcut.kn5',[],M,[dict(name='1SCUT_hairpin',mat_index=0,verts=VV.astype(np.float32),idx=II)],rootname='zw_vr7_longcut')
    print('hidden',W.hide_nodes(Z+'zw_vr7_longcut.kn5',Z+'zw_vr7_longcut.kn5',['1SCUT_hairpin']))
# ---------------- helpers
class Grid:
    def __init__(s,lay):
        s.xs,s.zs,s.H,s.KEY,s.UP,s.names=C.layout_raster(lay);s.Kd=C.keys()
        s.kn=np.array([C.mesh_key(n,s.Kd) or '' for n in s.names]+[''])  # index -1 -> ''
    def key(s,x,z):
        i=np.clip(np.round((np.asarray(x)-s.xs[0])/RES).astype(int),0,len(s.xs)-1);j=np.clip(np.round((np.asarray(z)-s.zs[0])/RES).astype(int),0,len(s.zs)-1)
        return s.kn[s.KEY[j,i]],s.H[j,i]
    def mask(s,keys): return np.isin(s.kn[s.KEY],list(keys))&s.UP
def resample(p,ds,closed):
    if closed: p=np.vstack([p,p[:1]])
    L=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))];n=int(L[-1]/ds);t=np.linspace(0,L[-1],n+1)
    if closed: t=t[:-1]
    return np.c_[[np.interp(t,L,p[:,k]) for k in range(p.shape[1])]].T
def normals(p,closed):
    t=(np.roll(p,-1,0)-np.roll(p,1,0)) if closed else np.gradient(p,axis=0)
    t/=np.linalg.norm(t,axis=1)[:,None];return t,np.c_[t[:,1],-t[:,0]]   # 'left' normal in x,z (AC: x right? sign checked by sides)
def curvature(p,k,closed):
    a=np.roll(p,k,0);c=np.roll(p,-k,0)
    if not closed: a[:k]=p[:k];c[-k:]=p[-k:]
    ab=np.linalg.norm(p-a,axis=1);bc=np.linalg.norm(c-p,axis=1);ac=np.linalg.norm(c-a,axis=1)
    cr=(p[:,0]-a[:,0])*(c[:,1]-a[:,1])-(p[:,1]-a[:,1])*(c[:,0]-a[:,0])
    return 2*cr/np.maximum(ab*bc*ac,1e-9)
def corridor(g,p,nrm,keys,span=16):
    o=np.arange(-span,span+1e-6,0.25);L=np.zeros(len(p));R=np.zeros(len(p))
    for i in range(len(p)):
        q=p[i]+o[:,None]*nrm[i];k,_=g.key(q[:,0],q[:,1]);ok=np.isin(k,list(keys))
        c=len(o)//2
        if not ok[c]:
            idx=np.nonzero(ok)[0]
            if not len(idx): L[i]=R[i]=0;continue
            c=idx[np.argmin(abs(idx-c))]
        a=c
        while a>0 and ok[a-1]: a-=1
        b=c
        while b<len(o)-1 and ok[b+1]: b+=1
        L[i]=o[a];R[i]=o[b]
    return L,R   # lateral offsets (along nrm) of the corridor edges
def clamp(g,p,keys,closed,m=1.4,it=12):
    # push points back inside their lateral corridor (edge + m) with a SMOOTHED offset field (no kinks), repeat
    mode='wrap' if closed else 'nearest'
    for _ in range(it):
        t,nrm=normals(p,closed);L,R=corridor(g,p,nrm,keys,span=10);lo=L+m;hi=R-m;mid=(L+R)/2
        e=np.where(lo<=hi,np.clip(0,lo,hi),mid)
        if not np.any(np.abs(e)>0.01): break
        e=ndimage.gaussian_filter1d(e*1.6,3,mode=mode);p=p+e[:,None]*nrm
    return p
def speeds(p,ds,closed,vmax,mu,acc,brk,v0=None,v1=None):
    kap=np.abs(curvature(p,4,closed));v=np.minimum(vmax,np.sqrt(mu*G/np.maximum(kap,1e-6)))
    if v0 is not None: v[0]=min(v[0],v0)
    if v1 is not None: v[-1]=min(v[-1],v1)
    n=len(v);rng=2 if closed else 1;lim=v.copy()
    for _ in range(rng):
        for i in range(n if closed else n-1):
            j=(i+1)%n;a=acc(v[i]);v[j]=min(v[j],np.sqrt(v[i]**2+2*a*ds))
    acc_lim=v.copy()
    for _ in range(rng):
        for i in range(n-1,0 if not closed else -1,-1):
            j=(i-1)%n;v[j]=min(v[j],np.sqrt(v[i]**2+2*brk*ds))
    brake=np.clip((acc_lim-v)/np.maximum(acc_lim,1)*6,0,1);gas=np.where(brake>0.02,0,np.where(v<lim-0.3,1,np.clip(0.35+v/vmax*0.4,0,1)))
    gas[(v<lim-0.3)&(brake<=0.02)]=1
    return v,gas,brake,kap
ACC=lambda v:max(1.2,7.5*(1-v/75)); BRK=11.0
# ---------------- fast lane
def fast_lane(lay,g):
    o=C.read_ai(f'{ORIG}/{lay}/fast_lane.ai');ref=resample(o['P']['p'][:,[0,2]],1.5,True)
    keys={'ROAD','CURB'}
    # smooth the recorded seed a little, then build corridor on its normals
    for _ in range(3): ref=(np.roll(ref,1,0)+2*ref+np.roll(ref,-1,0))/4
    t,nrm=normals(ref,True);L,R=corridor(g,ref,nrm,keys)
    m=1.1;lo=L+m;hi=R-m;bad=lo>hi;lo[bad]=hi[bad]=(L[bad]+R[bad])/2
    e=np.clip(0,lo,hi)
    for it in range(400):    # min-curvature relaxation: move toward neighbour mean (wide stencil) along the fixed normals
        p=ref+e[:,None]*nrm;q=(np.roll(p,4,0)+np.roll(p,-4,0))/2;e=np.clip(e+0.5*((q-p)*nrm).sum(1),lo,hi)
    p=ref+e[:,None]*nrm
    for _ in range(2): p=(np.roll(p,1,0)+2*p+np.roll(p,-1,0))/4
    p=resample(p,1.5,True);p=clamp(g,p,keys,True);t,nrm=normals(p,True);L,R=corridor(g,p,nrm,keys)
    v,gas,brk,kap=speeds(p,1.5,True,72.0,1.55,ACC,BRK)
    _,h=g.key(p[:,0],p[:,1]);pos=np.c_[p[:,0],h+0.40,p[:,1]]
    # copy seed-only fields (camber, direction, normal, 'length', grade) from the nearest zwiss sample
    so=o['P']['p'][:,[0,2]];nn=cKDTree(so).query(p)[1];E=np.zeros((len(p),18),np.float32);E[:]=o['E'][nn]
    E[:,0]=v;E[:,1]=gas;E[:,2]=brk;E[:,3]=0;E[:,4]=np.minimum(1/np.maximum(kap,1e-7),9e5)
    # zwiss sides: sideLeft/sideRight distance to edges; orientation from the seed (its median right>left check)
    E[:,5]=np.maximum(0,-L);E[:,6]=np.maximum(0,R)
    if np.corrcoef(o['E'][nn,5],E[:,5])[0,1]<np.corrcoef(o['E'][nn,5],E[:,6])[0,1]: E[:,[5,6]]=E[:,[6,5]]
    # start at the zwiss start index (same s/f line)
    i0=int(cKDTree(p).query(so[0])[1]);pos=np.roll(pos,-i0,0);E=np.roll(E,-i0,0)
    return pos,E
# ---------------- pit lane
def astar(free,cost,a,b):
    H_,W_=free.shape;dist={a:0};pq=[(0,a)];prev={a:None}
    while pq:
        f,c=heapq.heappop(pq)
        if c==b: break
        for dj in(-1,0,1):
            for di in(-1,0,1):
                if not dj and not di: continue
                n=(c[0]+dj,c[1]+di)
                if not(0<=n[0]<H_ and 0<=n[1]<W_) or not free[n]: continue
                nd=dist[c]+np.hypot(dj,di)*cost[n]
                if nd<dist.get(n,1e18): dist[n]=nd;prev[n]=c;heapq.heappush(pq,(nd+np.hypot(n[0]-b[0],n[1]-b[1]),n))
    if b not in prev: raise RuntimeError('no route')
    out=[];c=b
    while c: out.append(c);c=prev[c]
    return out[::-1]
def pit_lane(lay,g,fast):
    o=C.read_ai(f'{ORIG}/{lay}/pit_lane.ai');op=o['P']['p'][:,[0,2]]
    pits=sorted([(int(n['name'][7:]),n['W'][3,[0,2]]) for n in T.walk(Z+'zw_rpm.kn5') if n['cls']==1 and n['name'].startswith('AC_PIT_')])
    B=np.array([b for _,b in pits])
    keys={'ROAD','CURB','PITS','CONCRETE','GRAVEL'}
    free=g.mask(keys)
    # keep out of walls / boxes: car half width 1.1 m from non-drivable
    dt=ndimage.distance_transform_edt(free)*RES;free2=dt>1.1
    # no driving over the parked-car footprints (boxes +-2.6 x +-1.2 m): block them, lane in front of the rows
    xx,zz=np.meshgrid(g.xs,g.zs)
    for b in B: free2[(abs(xx-b[0])<1.6)&(abs(zz-b[1])<3.0)]=False
    cost=1+6/(1+dt)
    ij=lambda x,z:(int(round((z-g.zs[0])/RES)),int(round((x-g.xs[0])/RES)))
    # waypoints: leave the zwiss pit lane where the east concrete link joins, paddock lane north of the box rows, rejoin west
    zrow=B[:,1].min();xe=B[:,0].max()+6;xw=B[:,0].min()-6;zl=zrow-5.5
    def near_orig(x,z): return int(cKDTree(op).query([x,z])[1])
    ie=near_orig(188,-112);iw=near_orig(-25,30)+6
    wps=[tuple(op[ie]),(151,-40),(xe,zl),(xw,zl),(-20,52),tuple(op[iw])]
    lab,_=ndimage.label(free2);fz=np.argwhere(free2)
    def snap(w):
        c=ij(*w)
        if free2[c]: return c
        d=np.hypot(fz[:,0]-c[0],fz[:,1]-c[1]);return tuple(fz[np.argmin(d)])
    S=[snap(w) for w in wps];print(lay,'pit waypoints',[(round(g.xs[c[1]]),round(g.zs[c[0]]),int(lab[c])) for c in S])
    route=[]
    for a,b in zip(S[:-1],S[1:]):
        seg=astar(free2,cost,a,b);route+=seg if not route else seg[1:]
    rp=np.array([[g.xs[c[1]],g.zs[c[0]]] for c in route])
    for _ in range(60): rp[1:-1]=(rp[:-2]+2*rp[1:-1]+rp[2:])/4
    p=np.vstack([op[:ie],rp,op[iw+1:]]);p=resample(p,1.5,False)
    for _ in range(4): p[1:-1]=(p[:-2]+2*p[1:-1]+p[2:])/4
    p=clamp(g,p,keys,False,m=1.3);p=resample(p,1.5,False)
    # pit speed: 60 km/h on the pit lane (PITS), 25 km/h in the paddock / links, road speed on the roads in/out
    k,h=g.key(p[:,0],p[:,1])
    vmax=np.where(k=='PITS',16.7,np.where(np.isin(k,['GRAVEL','CONCRETE']),7.0,30.0))
    # the paddock box zone itself: 15 km/h
    near=cKDTree(B).query(p)[0]<12;vmax[near]=4.2
    vmax=ndimage.minimum_filter1d(vmax,9)
    v,gas,brk,kap=speeds(p,1.5,False,30.0,1.2,lambda v:3.5,6.0)
    v=np.minimum(v,vmax)
    for i in range(1,len(v)): v[i]=min(v[i],np.sqrt(v[i-1]**2+2*3.5*1.5))
    for i in range(len(v)-2,-1,-1): v[i]=min(v[i],np.sqrt(v[i+1]**2+2*6.0*1.5))
    dv=np.gradient(v);gas=np.clip(np.where(dv>=-0.01,0.3+dv*4,0),0,1);brk=np.clip(-dv*1.2,0,1)
    E=np.zeros((len(p),18),np.float32);E[:,0]=v;E[:,1]=gas;E[:,2]=brk;E[:,8]=1
    pos=np.c_[p[:,0],h+0.40,p[:,1]];return pos,E
if __name__=='__main__':
    build_cut()
    for lay in('main','short'):
        if lay=='main' and os.path.exists(f'/workspace/vr7/raster_main.npz'): os.remove('/workspace/vr7/raster_main.npz')  # longcut rebuilt
        g=Grid(lay);fp,fe=fast_lane(lay,g);C.write_ai(Z+f'{lay}/ai/fast_lane.ai',fp,fe)
        L=np.sum(np.linalg.norm(np.diff(np.vstack([fp,fp[:1]]),axis=0),axis=1));print(lay,'fast_lane',len(fp),'pts, %.0f m, v %.1f..%.1f m/s'%(L,fe[:,0].min(),fe[:,0].max()))
        pp,pe=pit_lane(lay,g,fp);C.write_ai(Z+f'{lay}/ai/pit_lane.ai',pp,pe);print(lay,'pit_lane',len(pp),'pts, v %.1f..%.1f'%(pe[:,0].min(),pe[:,0].max()))
