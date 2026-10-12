"""VR9: split the drag-tree bulb meshes per lane so the reactive tree can light lanes independently.
drtree_<grp> (both columns) -> drtree_<grp>_W (west/left lane, x < pole) and drtree_<grp>_E (east lane).
Usage: python tools/vr9_tree_lanes.py <dir containing zw_draglaunch.kn5>   (idempotent)
Run on the flat stage (backup/pre_vr9/zw_rpm) and then re-run vr9_lidar.py, or directly on zw_rpm
(the split is a pure re-partition of existing vertices, so it commutes with the lidar warp)."""
import sys,struct,os,numpy as np
sys.path.insert(0,os.path.dirname(__file__));import kn5patch as K
GROUPS=['prestage','stage','amber1','amber2','amber3','green','red']
def ws(s): b=s.encode();return struct.pack('<I',len(b))+b
def run(dirp):
    f=os.path.join(dirp,'zw_draglaunch.kn5');d=open(f,'rb').read();tex,nodes=K.scan(f)
    names=[n for n,o,l,c in nodes]
    if 'drtree_red_W' in names: print('already split');return
    root=nodes[0];head=d[:root[1]-4]
    meshes=[]
    for n,o,l,c in nodes[1:]:
        assert c==2
        p=o+l+4+1;nv,=struct.unpack_from('<I',d,p+3);V=np.frombuffer(d,'<f4',nv*11,p+7).reshape(nv,11)
        q=p+7+nv*44;ni,=struct.unpack_from('<I',d,q);I=np.frombuffer(d,'<u2',ni,q+4).reshape(-1,3);mat,=struct.unpack_from('<I',d,q+4+ni*2)
        if n.startswith('drtree_') and n[7:] in GROUPS:
            px=V[:,0].mean()   # columns are symmetric about the pole
            cx=V[I,0].mean(1)
            for suf,sel in (('_W',cx<px),('_E',cx>=px)):
                T=I[sel];u=np.unique(T);m=np.full(nv,-1);m[u]=np.arange(len(u))
                meshes.append((n+suf,V[u],m[T].astype('<u2'),mat))
        else: meshes.append((n,V,I,mat))
    out=bytearray(head)+struct.pack('<I',1)+ws(root[0])+struct.pack('<I',len(meshes))+b'\x01'+d[root[1]+root[2]+5:root[1]+root[2]+5+64]
    for n,V,I,mat in meshes:
        V=np.ascontiguousarray(V,'<f4');c=V[:,:3].mean(0);r=float(np.linalg.norm(V[:,:3]-c,axis=1).max())
        out+=struct.pack('<I',2)+ws(n)+struct.pack('<I',0)+b'\x01'+bytes([1,1,0])+struct.pack('<I',len(V))+V.tobytes()
        out+=struct.pack('<I',I.size)+np.ascontiguousarray(I).tobytes()+struct.pack('<II',mat,0)+struct.pack('<ff',0,0)+struct.pack('<3ff',*c,r)+b'\x01'
    open(f,'wb').write(bytes(out));print('split',f,len(meshes),'meshes')
if __name__=='__main__': run(sys.argv[1])
