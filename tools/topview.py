import sys,struct,numpy as np,os
sys.path.insert(0,os.path.dirname(__file__));import kn5patch as K
from PIL import Image,ImageDraw
A=np.load('/workspace/rpotm/geo/xz_to_uv.npy')
def px(xz):
    uv=xz@A[:,:2].T+A[:,2];return np.c_[uv[:,0]*8192,(uv[:,1]+1)*4096]
def meshes(fn,pred):
    d=open(fn,'rb').read();_,nodes=K.scan(fn);out=[]
    for name,o,l,c in nodes:
        if c==2 and pred(name):
            q=o+l+8;nv,=struct.unpack_from('<I',d,q);V=np.frombuffer(d,'<f4',nv*11,q+4).reshape(nv,11);q+=4+nv*44;ni,=struct.unpack_from('<I',d,q);I=np.frombuffer(d,'<u2',ni,q+4).reshape(-1,3)
            out.append((name,V,I))
    return out
def draw(base,layers,crop,out,scale=1.0):
    im=base.copy().convert('RGB');d=ImageDraw.Draw(im,'RGBA')
    for fn,pred,col in layers:
        for name,V,I in meshes(fn,pred):
            P=px(V[:,[0,2]].astype(float))
            for t in I: d.polygon([tuple(P[j]) for j in t],fill=col)
    im=im.crop(crop);im=im.resize((int(im.size[0]*scale),int(im.size[1]*scale)));im.save(out)
