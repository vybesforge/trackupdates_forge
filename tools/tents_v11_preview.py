"""Previews for tents + drag billboards v1.1 without Blender: top-down map (matplotlib) + textured perspective renders (numpy z-buffer rasterizer).
Writes to /workspace/tent_previews/ (or argv[1])."""
import sys,os,io,struct,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import kn5patch as K,kn5write as W,tents_v11 as TV
from PIL import Image
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
OUT=sys.argv[1] if len(sys.argv)>1 else '/workspace/tent_previews';os.makedirs(OUT,exist_ok=True);KN5=f'{TV.Z}/zw_tents.kn5'
def load(KN5=KN5):
    d=open(KN5,'rb').read();_,nodes=K.scan(KN5);mats=list(W.read_materials(KN5).items());tex={};ms=[]
    for name,o,l,c in nodes:
        if c!=2: continue
        q=o+l+8;nv,=struct.unpack_from('<I',d,q);V=np.frombuffer(d,'<f4',nv*11,q+4).reshape(nv,11).astype(float)
        q2=q+4+nv*44;ni,=struct.unpack_from('<I',d,q2);I=np.frombuffer(d,'<u2',ni,q2+4).reshape(-1,3).astype(int)
        mi,=struct.unpack_from('<I',d,q2+4+ni*2);tn=[t for s,_,t in mats[mi][1]['samplers'] if s=='txDiffuse'][0]
        if 'frame' in name: ms.append((name,V,I,tn));continue
        if tn not in tex: tex[tn]=np.array(Image.open(io.BytesIO(K.get_tex(KN5,tn))).convert('RGB').resize((1024,1024)),np.float32)/255
        ms.append((name,V,I,tn))
    return ms,tex
def render(ms,tex,eye,target,fov=50,size=(1600,900),night=False,ground=None):
    w,h=size;eye=np.array(eye,float);f=np.array(target,float)-eye;f/=np.linalg.norm(f);r=np.cross(f,[0,1,0]);r/=np.linalg.norm(r);u=np.cross(r,f)   # AC world is right-handed, y up (looking -z: right = +x)
    fl=0.5*w/np.tan(np.radians(fov)/2);img=np.zeros((h,w,3));zb=np.full((h,w),np.inf)
    sky=np.linspace(0,1,h)[:,None,None];img[:]=(np.array([0.02,0.03,0.07]) if night else np.array([0.55,0.72,0.92]))*(1-0.4*sky)
    L=np.array([0.4,0.8,-0.45]);L/=np.linalg.norm(L)
    def proj(P):
        q=P-eye;x=q@r;y=q@u;z=q@f;return np.stack([w/2+fl*x/z,h/2-fl*y/z,z],1)
    tris=[]
    if ground is not None:   # gravel plane
        gx0,gx1,gz0,gz1,gy=ground;G=np.array([[gx0,gy,gz0],[gx1,gy,gz0],[gx1,gy,gz1],[gx0,gy,gz1]],float)
        for a in range(20):
            for b in range(20):
                p=lambda i,j:G[0]+(G[1]-G[0])*i/20+(G[3]-G[0])*j/20
                tris.append(([p(a,b),p(a+1,b),p(a+1,b+1)],None,None,(0.47,0.43,0.37)));tris.append(([p(a,b),p(a+1,b+1),p(a,b+1)],None,None,(0.47,0.43,0.37)))
    for name,V,I,tn in ms:
        for t in I: tris.append((V[t,:3],V[t,6:8],tex[tn] if 'frame' not in name else None,(0.75,0.76,0.78) if 'frame' in name else None,V[t[0],3:6]) if True else None)
    for T in tris:
        P,UV,TX,col=T[:4];nrm=T[4] if len(T)>4 else np.array([0,1,0.]);S=proj(np.array(P,float))
        if (S[:,2]<0.5).any(): continue
        x0,x1=int(max(0,np.floor(S[:,0].min()))),int(min(w-1,np.ceil(S[:,0].max())));y0,y1=int(max(0,np.floor(S[:,1].min()))),int(min(h-1,np.ceil(S[:,1].max())))
        if x1<x0 or y1<y0: continue
        X,Y=np.meshgrid(np.arange(x0,x1+1)+0.5,np.arange(y0,y1+1)+0.5);(ax,ay,_),(bx,by,_),(cx,cy,_)=S
        den=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
        if abs(den)<1e-9: continue
        l0=((by-cy)*(X-cx)+(cx-bx)*(Y-cy))/den;l1=((cy-ay)*(X-cx)+(ax-cx)*(Y-cy))/den;l2=1-l0-l1;m=(l0>=0)&(l1>=0)&(l2>=0)
        if not m.any(): continue
        iz=l0/S[0,2]+l1/S[1,2]+l2/S[2,2];z=1/iz;sub=zb[y0:y1+1,x0:x1+1];m&=z<sub
        if not m.any(): continue
        facing=np.dot(nrm,eye-np.mean(P,0))>0
        if not facing: continue
        shade=0.45+0.55*max(0,np.dot(nrm,L)) if not night else 0.25
        if TX is not None:
            uv=(l0[...,None]*UV[0]/S[0,2]+l1[...,None]*UV[1]/S[1,2]+l2[...,None]*UV[2]/S[2,2])*z[...,None]
            c=TX[np.clip((uv[...,1]%1)*1023,0,1023).astype(int),np.clip((uv[...,0]%1)*1023,0,1023).astype(int)]*(shade+(0.35 if night else 0))
        else: c=np.broadcast_to(np.array(col)*shade,m.shape+(3,))
        sub[m]=z[m];im=img[y0:y1+1,x0:x1+1];im[m]=c[m]
    return Image.fromarray((np.clip(img,0,1)*255).astype(np.uint8))
if __name__=='__main__':
    fails,GY,(xs,zs,H,KEY,names,pits,path)=TV.verify(lambda s:None)
    # top-down
    fig,ax=plt.subplots(figsize=(12,9),dpi=130);lut={n:i for i,n in enumerate(names)};cls=np.full(KEY.shape,0.0)
    for n,i in lut.items():
        v=1 if 'GRAVEL' in n else 2 if ('CONCRETE' in n or 'PITS' in n or 'ROAD' in n or 'ASPH' in n) else 3 if 'GRASS' in n else 4
        cls[KEY==i]=v
    from matplotlib.colors import ListedColormap
    ax.imshow(cls,origin='lower',extent=(xs[0],xs[-1],zs[0],zs[-1]),cmap=ListedColormap(['#222','#b8a88a','#888','#6a9a55','#556']),vmin=0,vmax=4,interpolation='nearest')
    ax.plot(path[:,0],path[:,1],'-',c='orange',lw=2,label='spawn exit route (path_main)')
    P=np.array(pits);ax.scatter(P[:,0],P[:,2],s=10,c='white',marker='s',label='AC_PIT spawns (36)')
    for s,x,z,k in TV.SLOTS:
        c='#bf338a' if s<=6 else '#ff4060';ax.add_patch(plt.Rectangle((x-3,z-3),6,6,fc=c,ec='k',lw=1))
        ax.text(x,z+4.5,f'{s:02d}{" NEW" if s>6 else ""}',ha='center',fontsize=8,color='k',weight='bold')
    ax.set_xlim(-40,170);ax.set_ylim(30,240);ax.set_xlabel('x (m)');ax.set_ylabel('z (m)  (pits at low z)');ax.legend(loc='lower left',fontsize=8)
    ax.set_title('I-29 Speedway tents v1.1: 12 open ad slots (magenta = v1.0.4 spot, red = new spot)');fig.tight_layout();fig.savefig(f'{OUT}/tents_v11_topdown.png');print('topdown')
    ms,tex=load();gy=float(np.median(list(GY.values())))
    render(ms,tex,(66,14,95),(66,1,170),55,ground=(-10,165,100,225,gy-0.02)).save(f'{OUT}/tents_v11_aerial.png')
    render(ms,tex,(66,1.7,128),(66,1.8,142),60,ground=(30,100,120,170,GY[2])).save(f'{OUT}/tents_v11_closeup_slot02.png')
    render(ms,tex,(30,1.7,128),(39,1.8,142),60,ground=(0,80,120,170,GY[11])).save(f'{OUT}/tents_v11_closeup_slot11.png')
    render(ms,tex,(66,14,95),(66,1,170),55,night=True,ground=(-10,165,100,225,gy-0.02)).save(f'{OUT}/tents_v11_aerial_night.png')
    bm,bt=load(f'{TV.Z}/zw_vr5.kn5')
    render(bm,bt,(-255,2.5,-575),(-255,3.6,-606),50,ground=(-290,-220,-625,-560,-0.1)).save(f'{OUT}/boards_v11_drag_end.png')
    render(bm,bt,(-255,2.5,-575),(-255,3.6,-606),50,night=True,ground=(-290,-220,-625,-560,-0.1)).save(f'{OUT}/boards_v11_drag_end_night.png')
    print('renders done')
