"""VR9 checks after tools/vr9_lidar.py: residual vs the warp field, new steps between neighbouring drivable cells,
down-facing drivable triangles, per-surface stats. Compares the current zw_rpm/ against backup/pre_vr9."""
import sys,os,struct,json,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import physraster as PR,vr7_common as C,kn5patch as K
import vr9_lidar as L
from scipy import ndimage
B='/workspace/rpotm/backup/pre_vr9/zw_rpm/'
DRV={'ROAD','CURB','PITS','CONCRETE','DRAG','LAUNCHA','LAUNCHB','LAUNCHC','XROAD','XLOT','GRAVEL','SCUT'}
F=np.load('/workspace/vr9/field.npz')['D']
def ras(Zdir,lay,box,res=0.5):
    PR.Z=Zdir;return PR.raster(PR.physmeshes(C.FILES[lay],box),box,res)
def down_faces(Zdir):
    n=0
    for fn in sorted(set(C.FILES['main']+C.FILES['short'])):
        d=open(Zdir+fn,'rb').read()
        for nm,o,l,c in K.scan(Zdir+fn)[1]:
            if c!=2 or not nm[:1].isdigit() or C.mesh_key(nm,C.keys()) not in DRV: continue
            q=o+l+8;nv,=struct.unpack_from('<I',d,q);V=np.frombuffer(d,'<f4',nv*11,q+4).reshape(nv,11)[:,:3];q2=q+4+nv*44;ni,=struct.unpack_from('<I',d,q2);I=np.frombuffer(d,'<u2',ni,q2+4).reshape(-1,3)
            a,b,cc=V[I[:,0]],V[I[:,1]],V[I[:,2]];nn=np.cross(b-a,cc-a);ar=np.linalg.norm(nn,axis=1);n+=int(((nn[:,1]<-1e-6*ar)&(ar>1e-6)).sum())
    return n
rep={}
for lay in('main','short'):
    box=(-400,300,-980,260)
    x0,z0,H0,K0,U0,n0=ras(B,lay,box);x1,z1,H1,K1,U1,n1=ras(C.Z,lay,box)
    kn0=np.array([C.mesh_key(n,C.keys()) or '' for n in n0]+['']);kn1=np.array([C.mesh_key(n,C.keys()) or '' for n in n1]+[''])
    k0=kn0[K0];k1=kn1[K1];X,Zg=np.meshgrid(x0,z0);D=L.field_eval(F,X.ravel(),Zg.ravel()).reshape(X.shape)
    drv=np.isin(k1,list(DRV))&np.isin(k0,list(DRV))
    r=(H1-H0-D)[drv];changed=(k0!=k1)&(np.isin(k0,list(DRV))|np.isin(k1,list(DRV)))
    st=[]
    for ax in(0,1):
        a=np.abs(np.diff(H1,axis=ax))-np.abs(np.diff(H0,axis=ax));m=np.diff(drv.astype(int),axis=ax)==0
        m=m&(drv[:-1] if ax==0 else drv[:,:-1]);st.append(a[m])
    st=np.concatenate(st);st=st[np.isfinite(st)]
    dd=D[drv]
    rep[lay]=dict(cells=int(drv.sum()),delta_rms=float(np.sqrt((dd**2).mean())),delta_min=float(dd.min()),delta_max=float(dd.max()),
        residual_abs_max=float(np.nanmax(np.abs(r))),residual_p999=float(np.nanpercentile(np.abs(r),99.9)),
        new_step_gt_1cm=int((st>0.01).sum()),new_step_max=float(st.max()),surface_key_changed_cells=int(changed.sum()),
        changed_examples=[(float(X[j,i]),float(Zg[j,i]),k0[j,i],k1[j,i]) for j,i in list(zip(*np.nonzero(changed)))[:6]])
    # grade from field along drivable cells
    gz,gx=np.gradient(D,0.5);g=np.hypot(gx,gz)[drv];rep[lay]['added_grade_max_pct']=float(g.max()*100)
    print(lay,json.dumps(rep[lay],indent=0)[:1500])
rep['down_faces_before']=down_faces(B);rep['down_faces_after']=down_faces(C.Z);print('down faces',rep['down_faces_before'],rep['down_faces_after'])
json.dump(rep,open('/workspace/vr9/verify.json','w'),indent=1,default=str)
