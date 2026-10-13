"""VR2: move the gravel paddock triangles of 1CONCRETE_001 (vf_i29_speedway.kn5) into a separate 1GRAVEL_PADDOCK mesh.
Paddock tris (NAIP: gravel lot west of the pit buildings) -> degenerate in vf_i29_speedway.kn5 (index buffer size unchanged),
and written to assets_src/paddock/paddock_mesh.npz (AC coords, world-planar UV, 2 m tile) for build_own_kn5.py."""
import sys,os,struct,numpy as np
sys.path.insert(0,os.path.dirname(__file__));import kn5patch as K,topview as T
SRC='/workspace/rpotm/backup/vr2/vf_i29_speedway.kn5';DST=sys.argv[1] if len(sys.argv)>1 else 'vf_i29_speedway/vf_i29_speedway.kn5'
d=bytearray(open(SRC,'rb').read());_,nodes=K.scan(SRC)
for name,o,l,c in nodes:
    if c==2 and name=='1CONCRETE_001':
        q=o+l+8;nv,=struct.unpack_from('<I',d,q);V=np.frombuffer(bytes(d),'<f4',nv*11,q+4).reshape(nv,11).copy();q+=4+nv*44
        ni,=struct.unpack_from('<I',d,q);I=np.frombuffer(bytes(d),'<u2',ni,q+4).reshape(-1,3).copy();iq=q+4
P=T.px(V[I][:,:,[0,2]].mean(1).astype(float))
pad=np.zeros(len(I),bool);pad[[2,4,5,6,16]]=True  # big lot tris (checked on NAIP overlay); slivers 3,15,17-20,66,67 = concrete access road stay
print('paddock tris',pad.sum(),'of',len(I))
I2=I.copy();I2[pad]=I2[pad][:,[0]]  # degenerate (a,a,a)
d[iq:iq+I2.size*2]=I2.astype('<u2').tobytes();open(DST,'wb').write(bytes(d))
sel=I[pad];used=np.unique(sel);remap={v:i for i,v in enumerate(used)}
PV=V[used].copy();PV[:,6]=PV[:,0]/2.0;PV[:,7]=PV[:,2]/2.0;PV[:,8:11]=[1,0,0];PV[:,1]+=0.0
os.makedirs('assets_src/paddock',exist_ok=True)
np.savez('assets_src/paddock/paddock_mesh.npz',verts=PV,idx=np.vectorize(remap.get)(sel).astype(np.uint16))
print('area m2',sum(0.5*np.linalg.norm(np.cross(*(V[t[1:],:3]-V[t[0],:3]))) for t in sel))
