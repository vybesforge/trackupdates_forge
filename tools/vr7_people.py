"""VR7: the 2 paddock people, now under the LARGE verandah canopy of the green paddock building (paddock_bulds, posts at
z ~17.5, wall z ~22, x 84..117) instead of the small scrutineering canopy. Same model as our corner workers: zwiss's
marshal figure `marsh001` (908 tris, 1.78 m, UV atlas commissario_new.dds) is copied, rotated and placed; each copy gets
its own recoloured atlas (shirt/torso + sleeves islands only; trousers, head, hands keep the corner-worker look).
Static, visual only (no physics). Contact shadows: round decals in vf_vr6.kn5 (tools/vr6_props.py uses PEOPLE)."""
import sys,os,io,struct,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));import kn5patch as K,build_open_textures as B,vr5_meshlib as L
from PIL import Image,ImageDraw,ImageFilter
Z=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','vf_i29_speedway'))
# (x, z, facing yaw [rad, 0 = -z/north toward the paddock lot], shirt RGB, name)
# VR8: moved to the open east end (carport-style roof overhang, roof x 74.3..82.4 has no walls) of the small shed
# paddock_bulds_SUB7/SUB8 (x 64..82, z 34..42), directly west of the large green/grey-roofed paddock building (paddock_bulds, x 84..117).
PEOPLE=[(79.6,37.4,-1.35,(38,78,175),'blue',(52,36,24)),(78.3,38.6,1.9,(128,130,136),'grey',(28,26,25))]
Y=0.0   # concrete under the overhang (physics 1CONCRETE_001 y -0.0)
def marshal():
    f=f'{Z}/vf_i29_speedway.kn5';d=open(f,'rb').read()
    for n,o,l,c in K.scan(f)[1]:
        if n=='marsh001' and c==2:
            q=o+l+8;nv,=struct.unpack_from('<I',d,q);V=np.frombuffer(d,'<f4',nv*11,q+4).reshape(nv,11).copy();q2=q+4+nv*44;ni,=struct.unpack_from('<I',d,q2)
            return V,np.frombuffer(d,'<u2',ni,q2+4).reshape(-1,3).copy(),K.get_tex(f,'commissario_new.dds')
def facing(V):
    h=V[:,1]-V[:,1].min();ft=V[h<0.12,:3][:,[0,2]].mean(0);tor=V[(h>0.9)&(h<1.4),:3][:,[0,2]].mean(0);v=ft-tor;return np.arctan2(v[0],-v[1])
def shirt_tex(atlas,rgb,V,I,hair=(40,30,22),fwd=None):
    im=Image.open(io.BytesIO(atlas)).convert('RGB');W_,H_=im.size;m=Image.new('L',im.size,0);D=ImageDraw.Draw(m);h=V[:,1]-V[:,1].min()
    for t in I:
        uv=V[t][:,6:8];uv=uv-np.floor(uv.mean(0));u,v=uv.mean(0);hh=h[t].mean()
        if hh>0.84 and ((u<0.72 and v<0.55) or (u>0.66 and v>0.53)): D.polygon([(a*W_,b*H_) for a,b in uv],fill=255)
    m=np.asarray(m.filter(ImageFilter.MaxFilter(7)),np.float32)/255;a=np.asarray(im,np.float32)
    lum=a.mean(2);ref=np.median(lum[m>0.5]);new=np.clip(np.array(rgb)[None,None,:]*(lum/ref)[...,None]*1.0,0,255)
    out=(a*(1-m[...,None])+new*m[...,None])
    if hair is None: return np.clip(out,0,255).astype(np.uint8)
    # VR8: no helmet -> skin-tone head, hair on top/back (paint per head triangle in UV space)
    skin=np.array([196,150,118],np.float32);hm=Image.new('L',im.size,0);sm=Image.new('L',im.size,0);Dh=ImageDraw.Draw(hm);Ds=ImageDraw.Draw(sm)
    hc=V[h>1.5][:,[0,2]].mean(0)
    for t in I:
        hh=h[t].mean()
        if hh<1.47: continue
        uv=V[t][:,6:8];uv=uv-np.floor(uv.mean(0))
        if uv.mean(0)[0]<0.72 and uv.mean(0)[1]>0.14: continue   # shoulder/collar = shirt islands
        poly=[(a_*W_,b_*H_) for a_,b_ in uv]
        back=fwd is not None and np.dot(V[t][:,[0,2]].mean(0)-hc,fwd)<-0.03
        (Dh if (hh>1.66 or (back and hh>1.54)) else Ds).polygon(poly,fill=255)
    hm=np.asarray(hm.filter(ImageFilter.MaxFilter(3)),np.float32)/255;sm=np.asarray(sm.filter(ImageFilter.MaxFilter(3)),np.float32)/255*(1-hm)
    a2=out;l2=a2.mean(2,keepdims=True)
    # keep existing face detail where it already is skin (warm, not white): only white/blue helmet pixels become skin
    white=((a2.min(2)>150)|(a2[...,2]>a2[...,0]+10)).astype(np.float32)[...,None]
    skin_px=skin*np.clip(l2/l2.mean(),0.85,1.1);out=a2*(1-sm[...,None]*white)+skin_px*sm[...,None]*white
    hair_px=np.array(hair,np.float32)*np.clip(0.8+0.4*(l2/255),0.8,1.2);out=out*(1-hm[...,None])+hair_px*hm[...,None]
    return np.clip(out,0,255).astype(np.uint8)
def ellip(cen,r,fw,hair_cut=False,nu=18,nv=12):
    # UV ellipsoid (r = (side, up, front) radii) around cen, front axis = fw. hair_cut keeps the crown + back only.
    fw=np.asarray(fw,float);sd=np.cross([0,1,0],fw);V=[];I=[]
    for j in range(nv+1):
        th=np.pi*j/nv
        for i in range(nu+1):
            ph=2*np.pi*i/nu;n=np.array([np.sin(th)*np.cos(ph),np.cos(th),np.sin(th)*np.sin(ph)])
            p=cen+sd*n[0]*r[0]+np.array([0,1,0])*n[1]*r[1]+fw*n[2]*r[2]
            nn=sd*n[0]/r[0]+np.array([0,1.,0])*n[1]/r[1]+fw*n[2]/r[2];nn/=np.linalg.norm(nn)+1e-9
            V.append(np.r_[p,nn,i/nu,j/nv,sd])
    V=np.array(V,np.float32)
    for j in range(nv):
        for i in range(nu):
            a=j*(nu+1)+i;b=a+nu+1;q=[(a,a+1,b),(a+1,b+1,b)]
            for t in q:
                if hair_cut:
                    n=(V[list(t),:3]-cen).mean(0);up=n[1]/r[1];front=np.dot(n,fw)/r[2]
                    if up<-0.1+0.35*front: continue   # hairline: forehead ~0.25, temples ~-0.1, nape ~-0.45
                I.append(t)
    I=np.array(I);return V,L.fix_winding(V,I)
def neck(c,r,hgt):
    V,I=L.cyl(c,r,hgt,'y',10,cap=False);return V,I
def people_meshes():
    V0,I0,atlas=marshal();base=V0[:,:3].copy();c=np.r_[base[:,0].mean(),base[:,1].min(),base[:,2].mean()];yaw0=facing(V0)
    T=[];M=[];ME=[]
    h=base[:,1]-base[:,1].min();hc=base[(h>1.40)&(h<1.5)][:,[0,2]].mean(0);f0=np.array([np.sin(yaw0),-np.cos(yaw0)])
    # VR8: no helmet. The marshal's helmeted head (all tris above 1.44 m) is removed and replaced by a self-made
    # bare head: skin neck + ellipsoid head + hair shell with a hairline (higher at the forehead). Own solid textures.
    keep=~(h[I0].min(1)>1.44);Ik=I0[keep]
    T.append(('vr8_skin.dds',L.solid_dds((196,150,118))))
    for x,z,yaw,rgb,nm,hair in PEOPLE:
        tex=shirt_tex(atlas,rgb,V0,I0,None,None);Image.fromarray(tex).save(f'/workspace/vr7/person_{nm}.png')
        T.append((f'vr7_person_{nm}.dds',B.write_dds(np.dstack([tex,np.full(tex.shape[:2],255,np.uint8)]),'DXT1',10,None)))
        T.append((f'vr8_hair_{nm}.dds',L.solid_dds(hair)))
        a=yaw-yaw0;R=np.array([[np.cos(a),0,np.sin(a)],[0,1,0],[-np.sin(a),0,np.cos(a)]])
        put=lambda P_:(P_-c)@R.T+[x,Y,z]
        V=V0.copy();V[:,:3]=put(base);V[:,3:6]=V0[:,3:6]@R.T;V[:,8:11]=V0[:,8:11]@R.T
        ME.append((f'vr7_person_{nm}',f'vr7_person_{nm}.dds',V.astype(np.float32),Ik))
        y0=base[:,1].min();hcen=np.r_[hc[0],y0+1.635,hc[1]];fw=np.r_[f0[0],0,f0[1]]
        sk=[];hr=[]
        sk.append(ellip(hcen,(0.092,0.118,0.098),fw))
        sk.append(neck(np.r_[hc[0],y0+1.40,hc[1]],0.064,0.17))
        hr.append(ellip(hcen+[0,0.012,0]-fw*0.008,(0.099,0.118,0.106),fw,hair_cut=True))
        for parts,mn,tx in((sk,f'vr8_head_{nm}','vr8_skin.dds'),(hr,f'vr8_hair_{nm}',f'vr8_hair_{nm}.dds')):
            Vh,Ih=L.merge(parts);Vh=Vh.copy();Vh[:,:3]=put(Vh[:,:3]);Vh[:,3:6]=Vh[:,3:6]@R.T;Vh[:,8:11]=Vh[:,8:11]@R.T
            ME.append((mn,tx,Vh.astype(np.float32),Ih.astype('<u2')))
    return T,ME
