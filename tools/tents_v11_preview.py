"""Previews for tents + drag billboards v1.1 without Blender: top-down map (matplotlib) + textured perspective renders (numpy z-buffer rasterizer).
Writes to /workspace/tent_previews/ (or argv[1])."""
import sys,os,io,struct,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import kn5patch as K,kn5write as W,tents_v11 as TV
from PIL import Image
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
OUT=sys.argv[1] if len(sys.argv)>1 else '/workspace/tent_previews/v3';os.makedirs(OUT,exist_ok=True);KN5=f'{TV.Z}/zw_tents.kn5'
def load(KN5=KN5):
    d=open(KN5,'rb').read();_,nodes=K.scan(KN5);mats=list(W.read_materials(KN5).items());tex={};ms=[]
    for name,o,l,c in nodes:
        if c!=2: continue
        q=o+l+8;nv,=struct.unpack_from('<I',d,q);V=np.frombuffer(d,'<f4',nv*11,q+4).reshape(nv,11).astype(float)
        q2=q+4+nv*44;ni,=struct.unpack_from('<I',d,q2);I=np.frombuffer(d,'<u2',ni,q2+4).reshape(-1,3).astype(int)
        mi,=struct.unpack_from('<I',d,q2+4+ni*2);tn=[t for s,_,t in mats[mi][1]['samplers'] if s=='txDiffuse'][0]
        if 'shadow' in name: continue
        if tn not in tex: tex[tn]=np.array(Image.open(io.BytesIO(K.get_tex(KN5,tn))).convert('RGB').resize((1024,1024)),np.float32)/255 if 'galv' not in tn else np.full((4,4,3),0.75,np.float32)
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
        for t in I: tris.append((V[t,:3],V[t,6:8],tex[tn],None,V[t[0],3:6]) if True else None)
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
            c=TX[np.clip((uv[...,1]%1)*(TX.shape[0]-1),0,TX.shape[0]-1).astype(int),np.clip((uv[...,0]%1)*(TX.shape[1]-1),0,TX.shape[1]-1).astype(int)]*(shade+(0.35 if night else 0))
        else: c=np.broadcast_to(np.array(col)*shade,m.shape+(3,))
        sub[m]=z[m];im=img[y0:y1+1,x0:x1+1];im[m]=c[m]
    return Image.fromarray((np.clip(img,0,1)*255).astype(np.uint8))
if __name__=='__main__':
    import drift_course as DC
    from matplotlib.patches import Patch,Polygon
    from matplotlib.lines import Line2D
    fails,GY,(xs,zs,H,KEY,names,pits,path,hat,_R)=TV.verify(lambda s:None);C=DC.course()
    fig,ax=plt.subplots(figsize=(12,10),dpi=130);lut={n:i for i,n in enumerate(names)};cls=np.full(KEY.shape,0.0)
    for n,i in lut.items():
        v=1 if 'GRAVEL' in n else 2 if ('CONCRETE' in n or 'PITS' in n or 'ROAD' in n or 'ASPH' in n) else 3 if 'GRASS' in n else 4
        cls[KEY==i]=v
    cls[(cls==1)&(zs[:,None]>=TV.CONC_Z0)]=5   # drift pad overlay (1CONCRETE_DRIFT_n)
    from matplotlib.colors import ListedColormap
    ax.imshow(cls,origin='lower',extent=(xs[0],xs[-1],zs[0],zs[-1]),cmap=ListedColormap(['#222','#b8a88a','#888','#6a9a55','#556','#cfcfc8']),vmin=0,vmax=5,interpolation='nearest')
    ax.axhline(TV.CONC_Z0,xmin=0,xmax=1,c='k',lw=0.8,ls=':')
    ax.plot(path[:,0],path[:,1],'-',c='orange',lw=2)
    P=np.array(pits);ax.scatter(P[:,0],P[:,2],s=10,c='white',marker='s')
    L=np.vstack([C['line'],C['line'][:1]]);ax.plot(L[:,0],L[:,1],'-',c='#d00000',lw=2.2)
    t,_,_=DC.frames()
    for i in range(0,len(C['line']),25): ax.annotate('',xy=C['line'][i]+t[i]*3,xytext=C['line'][i],arrowprops=dict(arrowstyle='->',color='#d00000',lw=1.5))
    for z_ in C['zones']: ax.plot(z_[:,0],z_[:,1],'--',c='white',lw=1)
    for w in C['walls']: ax.plot(w[:,0],w[:,1],'-',c='#2050ff',lw=3)
    ax.scatter(C['clips'][:,0],C['clips'][:,1],s=40,c='#ff7a00',edgecolors='k',zorder=5)
    dx,dz,dr=C['donut'];ax.add_patch(plt.Circle((dx,dz),dr,fill=False,ec='white',lw=1.5));ax.text(dx,dz,'DONUT',ha='center',va='center',fontsize=8,color='white')
    e=C['line'][0];ax.text(e[0]-9,e[1]-4,'ENTRY',fontsize=8,color='#d00000',weight='bold')
    for s_,x,z,yaw in TV.SLOTS:
        R=np.array([[np.cos(yaw),np.sin(yaw)],[-np.sin(yaw),np.cos(yaw)]]);corn=np.array([[-3,-3],[3,-3],[3,3],[-3,3]])
        q=np.array([[c[0]*np.cos(yaw)+c[1]*np.sin(yaw),-c[0]*np.sin(yaw)+c[1]*np.cos(yaw)] for c in corn])+[x,z]
        ax.add_patch(Polygon(q,fc='#3a3b3e',ec='k'));ax.plot(q[:2,0],q[:2,1],c='white',lw=2);ax.text(x,z,f'{s_:02d}',ha='center',va='center',fontsize=6,color='white',weight='bold')
    h=[Line2D([],[],c='#d00000',lw=2,label='drift line (direction ->)'),Line2D([],[],c='#2050ff',lw=3,label='jersey barrier, collision (1WALL_DRIFT_n)'),
       Line2D([],[],c='white',ls='--',label='painted outer clipping zone (5.5 m)'),Line2D([],[],marker='o',ls='',mfc='#ff7a00',mec='k',label='inner clip: tyre stack + cones'),
       Patch(fc='#3a3b3e',ec='k',label='vendor tent slot NN (white edge = open side)'),Line2D([],[],marker='s',ls='',mfc='white',mec='white',label='AC_PIT spawns (36)'),
       Line2D([],[],c='orange',lw=2,label='spawn exit route'),Patch(fc='#cfcfc8',label='drift pad: cracked concrete (1CONCRETE_DRIFT, CONCRETE grip 0.95)'),
       Patch(fc='#b8a88a',label='gravel (spawn zone, 1GRAVEL_PADDOCK)'),Patch(fc='#888',label='existing concrete / road'),Patch(fc='#6a9a55',label='grass')]
    ax.legend(handles=h,loc='lower left',fontsize=6.5,facecolor='#999');ax.set_xlim(-10,165);ax.set_ylim(40,228);ax.set_xlabel('x (m)');ax.set_ylabel('z (m)')
    ax.set_title(f'I-29 Speedway paddock drift course: {len(C["line"])} m line, {len(TV.SLOTS)} tent ad slots');fig.tight_layout();fig.savefig(f'{OUT}/course_topdown.png');print('topdown')
    ms,tex=load();gy=float(np.median(list(GY.values())));G=(0,160,60,222,float(np.nanmin(H[(zs[:,None]>60)&(zs[:,None]<222)&(xs[None,:]>0)&(xs[None,:]<160)]))-0.03)   # below the lowest lot point
    render(ms,tex,(78,55,40),(78,0,160),55,ground=G).save(f'{OUT}/course_aerial.png')
    render(ms,tex,(78,55,40),(78,0,160),55,night=True,ground=G).save(f'{OUT}/course_aerial_night.png')
    render(ms,tex,(150,30,90),(70,0,160),55,ground=G).save(f'{OUT}/course_aerial_se.png')
    Ln=C['line']
    for nm,i in (('driver_view_entry',5),('driver_view_west_transition',55),('driver_view_north_sweeper',125),('driver_view_east',200)):
        p0=Ln[i];p1=Ln[(i+14)%len(Ln)];render(ms,tex,(p0[0],hat(*p0)+1.15,p0[1]),(p1[0],hat(*p0)+1.0,p1[1]),70,ground=(G[0],G[1],G[2],G[3],hat(*p0)-0.01))   # local ground level (lidar grade).save(f'{OUT}/{nm}.png')
    render(ms,tex,(75,1.25,83),(75,1.8,120),70,ground=G).save(f'{OUT}/view_from_spawn.png')
    render(ms,tex,(60,6,78),(60,0,100),60,ground=(0,160,60,93,hat(60,90)-0.01)).save(f'{OUT}/gravel_concrete_edge.png')
    s1=TV.SLOTS[7];render(ms,tex,(s1[1]-11*np.sin(s1[3]),1.7,s1[2]-11*np.cos(s1[3])),(s1[1],1.6,s1[2]),60,ground=G).save(f'{OUT}/tent_closeup_slot{s1[0]:02d}.png')
    bm,bt=load(f'{TV.Z}/zw_vr5.kn5')
    render(bm,bt,(-255,2.5,-575),(-255,3.6,-606),50,ground=(-290,-220,-625,-560,-0.1)).save(f'{OUT}/boards_drag_end.png')
    print('renders done')
