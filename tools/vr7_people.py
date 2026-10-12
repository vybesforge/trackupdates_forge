"""VR7: the 2 paddock people, now under the LARGE verandah canopy of the green paddock building (paddock_bulds, posts at
z ~17.5, wall z ~22, x 84..117) instead of the small scrutineering canopy. Same model as our corner workers: zwiss's
marshal figure `marsh001` (908 tris, 1.78 m, UV atlas commissario_new.dds) is copied, rotated and placed; each copy gets
its own recoloured atlas (shirt/torso + sleeves islands only; trousers, head, hands keep the corner-worker look).
Static, visual only (no physics). Contact shadows: round decals in zw_vr6.kn5 (tools/vr6_props.py uses PEOPLE)."""
import sys,os,io,struct,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));import kn5patch as K,build_open_textures as B
from PIL import Image,ImageDraw,ImageFilter
Z=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','zw_rpm'))
# (x, z, facing yaw [rad, 0 = -z/north toward the paddock lot], shirt RGB, name)
PEOPLE=[(99.0,23.2,-1.15,(38,78,175),'blue'),(97.7,23.7,1.25,(128,130,136),'grey')]
Y=0.0   # verandah floor (physics 1CONCRETE_001 y -0.0 at x 96..104, z 22..26)
def marshal():
    f=f'{Z}/zw_rpm.kn5';d=open(f,'rb').read()
    for n,o,l,c in K.scan(f)[1]:
        if n=='marsh001' and c==2:
            q=o+l+8;nv,=struct.unpack_from('<I',d,q);V=np.frombuffer(d,'<f4',nv*11,q+4).reshape(nv,11).copy();q2=q+4+nv*44;ni,=struct.unpack_from('<I',d,q2)
            return V,np.frombuffer(d,'<u2',ni,q2+4).reshape(-1,3).copy(),K.get_tex(f,'commissario_new.dds')
def facing(V):
    h=V[:,1]-V[:,1].min();ft=V[h<0.12,:3][:,[0,2]].mean(0);tor=V[(h>0.9)&(h<1.4),:3][:,[0,2]].mean(0);v=ft-tor;return np.arctan2(v[0],-v[1])
def shirt_tex(atlas,rgb,V,I):
    im=Image.open(io.BytesIO(atlas)).convert('RGB');W_,H_=im.size;m=Image.new('L',im.size,0);D=ImageDraw.Draw(m);h=V[:,1]-V[:,1].min()
    for t in I:
        uv=V[t][:,6:8];uv=uv-np.floor(uv.mean(0));u,v=uv.mean(0);hh=h[t].mean()
        if hh>0.84 and ((u<0.72 and v<0.55) or (u>0.66 and v>0.53)): D.polygon([(a*W_,b*H_) for a,b in uv],fill=255)
    m=np.asarray(m.filter(ImageFilter.MaxFilter(7)),np.float32)/255;a=np.asarray(im,np.float32)
    lum=a.mean(2);ref=np.median(lum[m>0.5]);new=np.clip(np.array(rgb)[None,None,:]*(lum/ref)[...,None]*1.0,0,255)
    out=(a*(1-m[...,None])+new*m[...,None]).astype(np.uint8);return out
def people_meshes():
    V0,I0,atlas=marshal();base=V0[:,:3].copy();c=np.r_[base[:,0].mean(),base[:,1].min(),base[:,2].mean()];yaw0=facing(V0)
    T=[];M=[];ME=[]
    for x,z,yaw,rgb,nm in PEOPLE:
        tex=shirt_tex(atlas,rgb,V0,I0);Image.fromarray(tex).save(f'/workspace/vr7/person_{nm}.png')
        T.append((f'vr7_person_{nm}.dds',B.write_dds(np.dstack([tex,np.full(tex.shape[:2],255,np.uint8)]),'DXT1',10,None)))
        a=yaw-yaw0;R=np.array([[np.cos(a),0,np.sin(a)],[0,1,0],[-np.sin(a),0,np.cos(a)]])
        V=V0.copy();V[:,:3]=(base-c)@R.T+[x,Y,z];V[:,3:6]=V0[:,3:6]@R.T;V[:,8:11]=V0[:,8:11]@R.T
        ME.append((f'vr7_person_{nm}',f'vr7_person_{nm}.dds',V.astype(np.float32),I0))
    return T,ME
