"""VR9: lidar re-drape. Applies a smooth vertical warp field D(x,z) (USGS 3DEP 2020 1 m DEM, project IA_WesternIA_2020_D21)
to EVERY vertex / AC_ dummy of every kn5 in vf_i29_speedway/ (visual + physics + props + spawns), plus the AI lines.
  F(x,z)  = normalised-convolution of the DEM over PAVED physics cells only (sigma 10 m, ditches/embankments ignored),
            blended to sigma-25 m terrain away from pavement, then smoothed again (sigma 6 m)
  D       = w(x,z) * (F - F(start/finish)),  w = 1 within 120 m of pavement -> 0 at 400 m (far ground + north extension untouched)
One continuous field for everything => visual/physics stay consistent, joins stay continuous, T1/T5 bumps are kept (added on top).
Coarse flat meshes are first refined (conforming red-green edge splits, xz edges > 4 m drivable / 8 m visual ground) so the
linear interpolation across a triangle follows D (zwiss 1DRAGstrip had 374 m triangles).
Input = backup /workspace/rpotm/backup/pre_vr9/vf_i29_speedway (idempotent). Run: venv python tools/vr9_lidar.py"""
import sys,os,struct,json,numpy as np,rasterio
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import kn5patch as K,kn5tree as KT,vr7_common as C
from scipy import ndimage
SRC='/workspace/rpotm/backup/pre_vr9/vf_i29_speedway/';DST=C.Z;ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A=np.load('/workspace/rpotm/geo/xz_to_utm.npy')
PAVED={'ROAD','CURB','PITS','CONCRETE','DRAG','LAUNCHA','LAUNCHB','LAUNCHC','XROAD','XLOT','GRAVEL','SCUT'}
GX0,GX1,GZ0,GZ1=-800.0,700.0,-1400.0,700.0
SF=(-224.27,-291.61)
def build_field():
    r=rasterio.open(f'{ROOT}/docs/elevation/dem_crop_1m.tif');D=r.read(1).astype(np.float64);Ti=~r.transform
    gx=np.arange(GX0,GX1+1);gz=np.arange(GZ0,GZ1+1);X,Zg=np.meshgrid(gx,gz)
    u=np.c_[X.ravel(),Zg.ravel(),np.ones(X.size)]@A;c,rr=Ti*(u[:,0],u[:,1])
    dem=ndimage.map_coordinates(D,[rr-0.5,c-0.5],order=1,mode='nearest').reshape(X.shape)
    import physraster as PR
    c_='/workspace/vr9/raster_wide.npz'
    WB=(-500,300,-1000,300);TRK=[f for f in C.FILES['main'] if f!='zw_ext.kn5']
    if not os.path.exists(c_):
        PR.Z=SRC;r_=PR.raster(PR.physmeshes(TRK,WB),WB,0.5);np.savez(c_,xs=r_[0],zs=r_[1],H=r_[2],KEY=r_[3],UP=r_[4],names=np.array(r_[5],object))
        r2=PR.raster(PR.physmeshes(['zw_ext.kn5'],WB),WB,0.5);np.savez('/workspace/vr9/raster_ext.npz',xs=r2[0],zs=r2[1],KEY=r2[3],UP=r2[4],names=np.array(r2[5],object))
    r_=np.load(c_,allow_pickle=True);xs,zs,H,KEY,UP,names=r_['xs'],r_['zs'],r_['H'],r_['KEY'],r_['UP'],list(r_['names']);Kd=C.keys();kn=np.array([C.mesh_key(n,Kd) or '' for n in names]+[''])
    pav=np.isin(kn[KEY],list(PAVED))&UP
    # 0.5 m raster -> 1 m field grid
    M=np.zeros(X.shape);jj,ii=np.nonzero(pav);gi=np.round(xs[ii]-GX0).astype(int);gj=np.round(zs[jj]-GZ0).astype(int);M[gj,gi]=1
    # extra pavement outside the raster box (north-extension roads are > 1.4 km away; drag lot roads are inside)
    num=ndimage.gaussian_filter(M*dem,10);den=ndimage.gaussian_filter(M,10);Fp=num/np.maximum(den,1e-9)
    Ft=ndimage.gaussian_filter(dem,25);a=np.clip(den/0.15,0,1);F=ndimage.gaussian_filter(a*Fp+(1-a)*Ft,6)
    dist=ndimage.distance_transform_edt(M==0);w=np.clip(1-(dist-120)/280,0,1);w=w*w*(3-2*w)
    # the north-extension roads (zw_ext.kn5, built flat at the zwiss level here) are NOT re-draped: fade D to 0 near them
    e_=np.load('/workspace/vr9/raster_ext.npz',allow_pickle=True);ek=np.array([C.mesh_key(n,Kd) or '' for n in e_['names']]+[''])
    ed=np.isin(ek[e_['KEY']],list(PAVED|{'GRASS'}))&e_['UP'];Me=np.zeros(X.shape);jj,ii=np.nonzero(ed&np.isin(ek[e_['KEY']],list(PAVED)))
    Me[np.round(e_['zs'][jj]-GZ0).astype(int),np.round(e_['xs'][ii]-GX0).astype(int)]=1
    de=ndimage.distance_transform_edt(Me==0);we=np.clip((de-25)/60,0,1);we=we*we*(3-2*we);w=w*we
    f0=ndimage.map_coordinates(F,[[SF[1]-GZ0],[SF[0]-GX0]],order=1)[0];Dl=w*(F-f0)
    np.savez('/workspace/vr9/field.npz',D=Dl,dem=dem,M=M,F=F);return Dl,dem,M
def field_eval(Dl,x,z):
    return ndimage.map_coordinates(Dl,[np.asarray(z)-GZ0,np.asarray(x)-GX0],order=1,mode='constant',cval=0.0)
# ---------------- kn5 parsing with offsets
def nodes_full(p):
    d=open(p,'rb').read();sc=K.scan(p)[1];wk=KT.walk(p);assert len(sc)==len(wk)
    out=[]
    for (name,o,l,cls),w in zip(sc,wk):
        assert name==w['name']
        n=dict(name=name,cls=cls,W=w['W'],PW=w['parentW'],path=w['path'],moff=w.get('moff'))
        if cls==2:
            q=o+l+8;nv,=struct.unpack_from('<I',d,q);n['vo']=q;q2=q+4+nv*44;ni,=struct.unpack_from('<I',d,q2);n['end']=q2+4+ni*2
            n['V']=np.frombuffer(d,'<f4',nv*11,q+4).reshape(nv,11).copy();n['I']=np.frombuffer(d,'<u2',ni,q2+4).reshape(-1,3).copy()
            n['mat'],=struct.unpack_from('<I',d,n['end']);n['bs']=n['end']+16
        out.append(n)
    return d,out
def refine(V,I,L,near=None):
    """conforming red-green refinement of edges with xz length > L (or L_far where near() is False)"""
    V=[v for v in V];I=[tuple(t) for t in I]
    for _ in range(14):
        Va=np.array(V);mid={}
        def need(a,b):
            e=np.hypot(Va[a,0]-Va[b,0],Va[a,2]-Va[b,2])
            lim=L if near is None else near((Va[a,0]+Va[b,0])/2,(Va[a,2]+Va[b,2])/2,L)
            return e>lim
        marked=set()
        Ia=np.array(I);a0,b0,c0=Va[Ia[:,0],:3],Va[Ia[:,1],:3],Va[Ia[:,2],:3];nn=np.cross(b0-a0,c0-a0);hz=np.abs(nn[:,1])>0.9*(np.linalg.norm(nn,axis=1)+1e-12)
        for t,h_ in zip(I,hz):
            if not h_: continue
            for a,b in((t[0],t[1]),(t[1],t[2]),(t[2],t[0])):
                k=(min(a,b),max(a,b))
                if k not in marked and need(a,b): marked.add(k)
        if not marked: break
        for k in marked:
            v=(Va[k[0]]+Va[k[1]])/2;n=v[3:6];v[3:6]=n/(np.linalg.norm(n)+1e-12);mid[k]=len(V);V.append(v)
        J=[]
        for a,b,c in I:
            m=[mid.get((min(a,b),max(a,b))),mid.get((min(b,c),max(b,c))),mid.get((min(c,a),max(c,a)))]
            cnt=sum(x is not None for x in m)
            if cnt==0: J.append((a,b,c));continue
            if cnt==3:
                ab,bc,ca=m;J+=[(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)];continue
            # rotate so that the first marked edge is (a,b)
            vs=[a,b,c];ms=m
            while ms[0] is None: vs=vs[1:]+vs[:1];ms=ms[1:]+ms[:1]
            a_,b_,c_=vs;ab,bc,ca=ms
            if cnt==1: J+=[(a_,ab,c_),(ab,b_,c_)]
            elif bc is not None: J+=[(a_,ab,c_),(ab,b_,bc),(ab,bc,c_)]
            else: J+=[(a_,ab,ca),(ab,b_,c_),(ab,c_,ca)]
        I=J
    return np.array(V,np.float32),np.array(I,np.int64)
def is_flat_ground(n):
    V,I=n['V'],n['I']
    if len(I)==0: return False
    a,b,c=V[I[:,0],:3],V[I[:,1],:3],V[I[:,2],:3];nn=np.cross(b-a,c-a);ln=np.linalg.norm(nn,axis=1)+1e-12
    flat=(np.abs(nn[:,1])/ln>0.95).mean();span=V[:,[0,2]].max(0)-V[:,[0,2]].min(0)
    return flat>0.3 and V[:,1].max()-V[:,1].min()<12 and span.max()>20
def write(p,d,nodes,newmesh,dummy_dy):
    edits=[]
    for n in nodes:
        if n['cls']==1 and n['name'] in dummy_dy:
            M=np.frombuffer(d,'<f4',16,n['moff']).reshape(4,4).astype(float).copy()
            Rp=n['PW'][:3,:3];dl=np.array([0,dummy_dy[n['name']],0])@np.linalg.inv(Rp);M[3,:3]+=dl
            edits.append((n['moff'],n['moff']+64,M.astype('<f4').tobytes()))
        if n['cls']==2 and n['name']+'#'+str(n['vo']) in newmesh:
            V,I=newmesh[n['name']+'#'+str(n['vo'])];assert len(V)<65536,(n['name'],len(V))
            blk=struct.pack('<I',len(V))+np.asarray(V,'<f4').tobytes()+struct.pack('<I',I.size)+np.asarray(I,'<u2').tobytes()
            edits.append((n['vo'],n['end'],blk))
            Wm=n['W'];P=np.c_[V[:,:3],np.ones(len(V))]@Wm;cc=P[:,:3].mean(0);rad=float(np.linalg.norm(P[:,:3]-cc,axis=1).max())
            # bounding sphere stored in world? zwiss files store it in world coords (identity) - keep local frame consistent with AC: use local
            cl=V[:,:3].mean(0);rl=float(np.linalg.norm(V[:,:3]-cl,axis=1).max())
            edits.append((n['bs'],n['bs']+16,struct.pack('<3ff',*cl,rl)))
    edits.sort();out=bytearray();pos=0
    for a,b,r in edits: assert a>=pos;out+=d[pos:a]+r;pos=b
    out+=d[pos:];open(p,'wb').write(bytes(out))
def main():
    Dl,dem,M=build_field()
    def near(x,z,L):   # grass refinement by distance to pavement: L[0] within 12 m, L[1] within 60 m, else L[2]
        dd=NEARD[int(np.clip(round(z-GZ0),0,NEARD.shape[0]-1)),int(np.clip(round(x-GX0),0,NEARD.shape[1]-1))]
        return L[0] if dd<12 else (L[1] if dd<60 else L[2])
    global NEARD;NEARD=ndimage.distance_transform_edt(M==0)
    rep={'refined':{},'files':{}}
    allD=[]
    for fn in sorted(os.listdir(SRC)):
        if not fn.endswith('.kn5'): continue
        if fn=='zw_ext.kn5':
            import shutil;shutil.copy(SRC+fn,DST+fn);print(fn,'copied unchanged (north extension: not re-draped, D faded to 0 within 25..85 m of its roads)');continue
        d,nodes=nodes_full(SRC+fn);newmesh={};dummy={}
        moved_paths=set()
        for n in nodes:
            if n['cls']==1 and n['name'].startswith('AC_'):
                p=n['W'][3,:3];dummy[n['name']]=float(field_eval(Dl,[p[0]],[p[2]])[0]);moved_paths.add(tuple(n['path']+[n['name']]))
        for n in nodes:
            if n['cls']!=2: continue
            if any(tuple(n['path'][:k]) in moved_paths for k in range(1,len(n['path'])+1)): continue   # rides on a moved AC_ dummy
            V,I=n['V'],n['I'].astype(np.int64)
            Pw=np.c_[V[:,:3],np.ones(len(V))]@n['W'].astype(float);dyv=field_eval(Dl,Pw[:,0],Pw[:,2])
            if is_flat_ground(n) and len(V)<60000 and np.abs(dyv).max()>0.002:
                drv=n['name'][:1].isdigit() and 'WALL' not in n['name']
                if n['name']=='1GRASS' or 'google' in n['name'].lower(): V2,I2=refine(V,I,(4.0,10.0,50.0),near)
                else: V2,I2=refine(V,I,4.0 if drv else 16.0)
                if len(V2)>=65536:
                    V2,I2=refine(V,I,(5.0,14.0,60.0),near) if n['name']=='1GRASS' else refine(V,I,6.0 if drv else 24.0)
                if len(V2)>len(V): rep['refined'][f'{fn}:{n["name"]}']=(len(I),len(I2));V,I=V2,I2
            Wm=n['W'].astype(float);P=np.c_[V[:,:3],np.ones(len(V))]@Wm
            dy=field_eval(Dl,P[:,0],P[:,2]);P[:,1]+=dy
            Vn=V.copy();Vn[:,:3]=(np.c_[P[:,:3],np.ones(len(P))]@np.linalg.inv(Wm))[:,:3]
            if n['name'][:1].isdigit() and C.mesh_key(n['name'],C.keys()) in PAVED:
                a_,b_,c_=Vn[I[:,0],:3],Vn[I[:,1],:3],Vn[I[:,2],:3];nn=np.cross(b_-a_,c_-a_);ar=np.linalg.norm(nn,axis=1)+1e-12;ny=nn[:,1]/ar
                flip=ny<-0.9;I=I.copy();I[flip]=I[flip][:,[0,2,1]]          # zwiss down-facing road tris (1PITS 22, 1DRAGstrip 2) -> up
                drop=(ny<0)&~flip&(ar/2<0.01);I=I[~drop]                      # down-tilted sub-cm2 skirt slivers
                rep.setdefault('fixed',{})[f'{fn}:{n["name"]}']=(int(flip.sum()),int(drop.sum())) if flip.any() or drop.any() else None
            newmesh[n['name']+'#'+str(n['vo'])]=(Vn,I)
            if n['name'][:1].isdigit() and C.mesh_key(n['name'],C.keys()) in PAVED: allD.append(dy)
        write(DST+fn,d,nodes,newmesh,dummy);rep['files'][fn]=dict(meshes=len(newmesh),dummies=len(dummy))
        print(fn,len(newmesh),'meshes',len(dummy),'dummies')
    allD=np.concatenate(allD);rep['paved_vertex_delta']=dict(rms=float(np.sqrt((allD**2).mean())),min=float(allD.min()),max=float(allD.max()))
    json.dump(rep,open('/workspace/vr9/lidar_report.json','w'),indent=1);print(rep['paved_vertex_delta']);print(rep['refined'])
    # AI lines (from the VR7 lines in the backup)
    for lay in('main','short'):
        for lane in('fast_lane','pit_lane'):
            a=C.read_ai(SRC+f'{lay}/ai/{lane}.ai');p=a['P']['p'].astype(float);p[:,1]+=field_eval(Dl,p[:,0],p[:,2]);E=a['E'].copy()
            C.write_ai(DST+f'{lay}/ai/{lane}.ai',p,E)
if __name__=='__main__': main()
