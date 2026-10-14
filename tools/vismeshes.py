"""List visual meshes (any name) of a kn5 with vertices, indices and material index (world = raw vertex coords)."""
import struct,numpy as np,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));import kn5patch as K,kn5write as W
def vismeshes(path,box=None):
    d=open(path,'rb').read();_,nodes=K.scan(path);mats=list(W.read_materials(path));out=[]
    for name,o,l,c in nodes:
        if c!=2: continue
        q=o+l+8;nv,=struct.unpack_from('<I',d,q);V=np.frombuffer(d,'<f4',nv*11,q+4).reshape(nv,11)
        q2=q+4+nv*44;ni,=struct.unpack_from('<I',d,q2);I=np.frombuffer(d,'<u2',ni,q2+4).reshape(-1,3)
        mi,=struct.unpack_from('<I',d,q2+4+ni*2)
        if box is not None:
            x,z=V[:,0],V[:,2]
            if x.max()<box[0] or x.min()>box[1] or z.max()<box[2] or z.min()>box[3]: continue
        out.append(dict(name=name,off=o,vo=q+4,nv=nv,V=V,I=I,mat=mats[mi] if mi<len(mats) else mi))
    return out
if __name__=='__main__':
    p=sys.argv[1];b=[float(x) for x in sys.argv[2:6]] if len(sys.argv)>5 else None
    for m in vismeshes(p,b): print(m['name'],m['mat'],m['nv'],np.round(m['V'][:,[0,2]].min(0)),np.round(m['V'][:,[0,2]].max(0)))
