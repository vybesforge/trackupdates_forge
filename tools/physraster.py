import sys,struct,numpy as np,re,os
sys.path.insert(0,'/workspace/rpotm/project/tools');import kn5patch as K
Z='/workspace/rpotm/project/vf_i29_speedway/'
def physmeshes(files,box):
    out=[]
    for fn in files:
        d=open(Z+fn,'rb').read();_,nodes=K.scan(Z+fn)
        for name,o,l,c in nodes:
            if c!=2 or not re.match(r'^\d+[A-Z]',name): continue
            q=o+l+8;nv,=struct.unpack_from('<I',d,q);V=np.frombuffer(d,'<f4',nv*11,q+4).reshape(nv,11)[:,:3].astype(float)
            q2=q+4+nv*44;ni,=struct.unpack_from('<I',d,q2);I=np.frombuffer(d,'<u2',ni,q2+4).reshape(-1,3).astype(int)
            I=I[(I[:,0]!=I[:,1])&(I[:,1]!=I[:,2])]
            T=V[I];C=T[:,:,[0,2]]
            k=(C[:,:,0].max(1)>box[0])&(C[:,:,0].min(1)<box[1])&(C[:,:,1].max(1)>box[2])&(C[:,:,1].min(1)<box[3])
            if k.any(): out.append((fn,name,T[k]))
    return out
def raster(meshes,box,res=0.5):
    xs=np.arange(box[0],box[1],res);zs=np.arange(box[2],box[3],res)
    H=np.full((len(zs),len(xs)),np.nan);KEY=np.full(H.shape,-1);UP=np.zeros(H.shape,bool);names=[]
    for mi,(fn,name,T) in enumerate(meshes):
        names.append(name)
        for t in T:
            a,b,c=t;n=np.cross(b-a,c-a)
            if abs(n[1])<1e-6*np.linalg.norm(n)+1e-12: continue
            x0,x1=t[:,0].min(),t[:,0].max();z0,z1=t[:,2].min(),t[:,2].max()
            i0=max(0,int(np.ceil((x0-box[0])/res)));i1=min(len(xs)-1,int((x1-box[0])/res))
            j0=max(0,int(np.ceil((z0-box[2])/res)));j1=min(len(zs)-1,int((z1-box[2])/res))
            if i1<i0 or j1<j0: continue
            X,Zg=np.meshgrid(xs[i0:i1+1],zs[j0:j1+1])
            # barycentric in xz
            v0=np.array([b[0]-a[0],b[2]-a[2]]);v1=np.array([c[0]-a[0],c[2]-a[2]]);den=v0[0]*v1[1]-v1[0]*v0[1]
            px=X-a[0];pz=Zg-a[2];u=(px*v1[1]-v1[0]*pz)/den;v=(v0[0]*pz-px*v0[1])/den
            inside=(u>=-1e-6)&(v>=-1e-6)&(u+v<=1+1e-6)
            if not inside.any(): continue
            y=a[1]+u*(b[1]-a[1])+v*(c[1]-a[1])
            sub=H[j0:j1+1,i0:i1+1];kk=KEY[j0:j1+1,i0:i1+1];uu=UP[j0:j1+1,i0:i1+1]
            upd=inside&(np.isnan(sub)|(y>sub))
            sub[upd]=y[upd];kk[upd]=mi;uu[upd]=n[1]>0
    return xs,zs,H,KEY,UP,names
