"""west-lot: (1) the west-lot access road (x~-345, z -868..-480: the road west of the drag return road, inside the lot;
190th St itself is a modelled asphalt public road in vf_ext.kn5 and is NOT touched) -> cracked concrete in vf_roads.kn5; (2) west parking lot dirt/gravel patches from google+NAIP -> 1GRAVEL overlays in vf_westlot.kn5.
Grass stays on the existing 1GRASS_* terrain (visual satellite + GRASS physics). Dirt gets own_gravel look + GRAVEL physics.
Does not touch drag lanes, spawns, or the exit route."""
import os,sys,struct,numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import kn5write as W,kn5patch as K,vr5_meshlib as ML,vismeshes as VM,physraster as PR
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));Z=f'{ROOT}/vf_i29_speedway';MAIN=f'{Z}/vf_i29_speedway.kn5'
LIFT=0.02;T_=np.array([0.8396,0,-0.5432]);HALF=3.0;END=4.0
ST190=np.array([
 (-394.7,-990.0),(-389.2,-966.0),(-391.6,-941.4),(-391.5,-916.4),(-390.8,-891.5),(-389.6,-866.5),
 (-391.0,-841.6),(-392.2,-816.7),(-389.7,-792.0),(-390.0,-767.3),(-391.0,-742.4),(-393.8,-717.6),
 (-394.0,-692.7),(-395.5,-667.8),(-395.3,-642.8),(-395.5,-617.9),(-395.5,-592.9),(-395.0,-568.0),
 (-396.4,-543.1),(-397.4,-518.1),(-397.8,-493.1),(-398.2,-468.1),(-397.9,-443.1),(-397.8,-418.2),
 (-398.2,-393.2),(-399.1,-368.2),(-400.0,-343.2),(-399.1,-318.3),(-392.9,-294.6),(-392.5,-270.8),
 (-397.5,-246.8),(-401.2,-222.9),(-399.4,-198.0),(-401.7,-173.2),(-401.8,-148.2),(-402.0,-123.3),
 (-399.7,-98.5),(-400.6,-73.6),(-402.0,-48.8),(-403.5,-23.8),(-403.9,1.2),(-404.6,26.2),
 (-404.7,51.1),(-401.9,75.9),(-397.6,100.5),(-398.9,125.4),(-398.7,150.4),(-398.7,175.4),
 (-400.3,200.3),(-402.0,225.0),(-400.4,238.0)],float)
# west-lot access road (inside the lot, between 190th St and the return road; google aerial light band, ~6 m wide)
WR=np.array([(-344.5,-868.0),(-344.5,-820.0),(-344.5,-760.0),(-345.5,-700.0),(-346.5,-640.0),(-347.5,-580.0),(-347.5,-520.0),(-348.0,-480.0),(-348.0,-420.0),(-348.0,-370.0),(-348.0,-331.0)],float)
EXIT=np.array([(-387.6,-845.5),(-366.0,-845.0),(-346.0,-845.0)],float)   # v14: lot's west exit to 190th St (satellite band z~-845), stops at the 190th shoulder
# v15 (Dylan's orange loop): return-road extension to the apron + two cross links lot road <-> return road
LOOP=[('1CONCRETE_LOOP_RETEXT',np.array([(-298.0,-552.0),(-299.0,-450.0),(-300.0,-331.0)],float),4.0),
      ('1CONCRETE_LOOP_LINK800',np.array([(-345.0,-801.0),(-302.0,-801.0)],float),4.0),
      ('1CONCRETE_LOOP_LINK624',np.array([(-345.5,-624.0),(-302.0,-624.0)],float),3.0)]
JOIN_Z=-480.0   # v13: south of this the road is the new join to the 1CONCRETE_001 apron (z~-333)
def uv_c(x,z): return (-0.0168*x+0.0109*z+1.79,-0.0109*x-0.0167*z)
def uv_g(x,z): return (0.5*x,0.5*z)
def fixn(V,I):
    Pp=V[:,:3].astype(float);fn=np.cross(Pp[I[:,1]]-Pp[I[:,0]],Pp[I[:,2]]-Pp[I[:,0]]);fn*=np.sign(fn[:,1:2]+1e-12);vn=np.zeros_like(Pp)
    for c in range(3): np.add.at(vn,I[:,c],fn)
    V=V.copy();nl=np.linalg.norm(vn,axis=1,keepdims=True);vn[nl[:,0]<1e-9]=(0,1,0);nl[nl<1e-9]=1;V[:,3:6]=vn/nl;return V,ML.fix_winding(V,I).astype('<u2')
def cline(pts,step=1.0):
    s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))];q=np.arange(0,s[-1]+1e-6,step)
    P=np.stack([np.interp(q,s,pts[:,0]),np.interp(q,s,pts[:,1])],1);t=np.gradient(P,axis=0);t/=np.linalg.norm(t,axis=1,keepdims=True)+1e-12
    return q,P,t,np.stack([t[:,1],-t[:,0]],1)
def strip_mesh(P,n,Y,half,uvf,name_prefix,chunk=400):
    offs=np.linspace(-half,half,int(2*half/0.5)+1);G=P[:,None,:]+offs[None,:,None]*n[:,None,:]
    out=[];tg=T_ if uvf is uv_c else (1.0,0.0,0.0)
    for ci,part in enumerate(np.array_split(np.arange(len(P)-1),max(1,len(P)//chunk))):
        V=[];I=[];vid={}
        def v(a,b):
            if (a,b) not in vid:
                x,z=G[a,b];u,w=uvf(x,z);vid[a,b]=len(V);V.append([x,Y[a,b],z,0,1,0,u,w,*tg])
            return vid[a,b]
        for a in part:
            for b in range(len(offs)-1):
                p0,p1,p2,p3=v(a,b),v(a+1,b),v(a+1,b+1),v(a,b+1);I+=[[p0,p2,p1],[p0,p3,p2]]
        V,I=fixn(np.array(V,'<f4'),np.array(I));out.append((f'{name_prefix}_{ci}',V,I))
    return out
def terrain_H(box,res=0.5):
    TM=[m for m in VM.vismeshes(MAIN,box) if m['name'].startswith('1GRASS')]
    asT=[('m',m['name'],m['V'][m['I'].astype(int)][:,:,:3].astype(float)) for m in TM]
    return PR.raster(asT,box,res)
def top_H(box,res=0.5):
    files=[f for f in os.listdir(Z) if f.endswith('.kn5') and f not in('vf_roads.kn5','vf_westlot.kn5','vf_dragcol.kn5')]
    return PR.raster(PR.physmeshes(files,box),box,res)
def sampleH(xs,zs,H,P):
    i=np.clip(np.round((P[:,0]-xs[0])/(xs[1]-xs[0])).astype(int),0,len(xs)-1)
    j=np.clip(np.round((P[:,1]-zs[0])/(zs[1]-zs[0])).astype(int),0,len(zs)-1);return H[j,i]
def build_west_road():
    q,P,t,n=cline(WR);box=(-360,-330,-880,-320)
    xs,zs,H,KEY,UP,names=top_H(box,0.25)
    offs=np.linspace(-HALF,HALF,int(2*HALF/0.5)+1);G=P[:,None,:]+offs[None,:,None]*n[:,None,:]
    Y=sampleH(xs,zs,H,G.reshape(-1,2)).reshape(G.shape[:2])+LIFT
    meshes=strip_mesh(P,n,Y,HALF,uv_c,'1CONCRETE_LOTRD',chunk=10**6)
    q2,P2,t2,n2=cline(EXIT);box2=(-392,-340,-855,-835);xs2,zs2,H2,*_=top_H(box2,0.25)
    offs=np.linspace(-HALF,HALF,int(2*HALF/0.5)+1);G2=P2[:,None,:]+offs[None,:,None]*n2[:,None,:]
    Y2=sampleH(xs2,zs2,H2,G2.reshape(-1,2)).reshape(G2.shape[:2])+LIFT
    meshes+=strip_mesh(P2,n2,Y2,HALF,uv_c,'1CONCRETE_LOTEXIT',chunk=10**6)
    for nm,pts,hw in LOOP:
        _,Pl,_,nl=cline(pts);x0,x1=Pl[:,0].min()-hw-2,Pl[:,0].max()+hw+2;z0,z1=Pl[:,1].min()-hw-2,Pl[:,1].max()+hw+2
        xl,zl,Hl,*_=top_H((x0,x1,z0,z1),0.25);offs=np.linspace(-hw,hw,int(2*hw/0.5)+1);Gl=Pl[:,None,:]+offs[None,:,None]*nl[:,None,:]
        Yl=sampleH(xl,zl,Hl,Gl.reshape(-1,2)).reshape(Gl.shape[:2])+LIFT;meshes+=strip_mesh(Pl,nl,Yl,hw,uv_c,nm,chunk=10**6)
    return meshes,P,n
def object_block(xs,zs,margin=0.75):
    """Cells covered by any object (visual non-ground meshes + collision boxes), dilated by margin."""
    box=(xs[0]-2,xs[-1]+2,zs[0]-2,zs[-1]+2);B=np.zeros((len(zs),len(xs)),bool)
    skip=('1GRASS','1CONCRETE','1ROAD','1XROAD','1GRAVEL','1DRAG','1LAUNCH','skybox','highway','cables','xline','FENCE_outside','gate_poles')
    for fn in ('vf_i29_speedway.kn5','vf_dragcol.kn5','vf_tents.kn5','vf_i29_speedway_own.kn5'):
        p=f'{Z}/{fn}'
        if not os.path.exists(p): continue
        for m in VM.vismeshes(p,box):
            if m['name'].startswith(skip): continue
            T=m['V'][m['I'].astype(int)][:,:,[0,2]].astype(float)
            for t in T:
                x0,x1=t[:,0].min()-margin,t[:,0].max()+margin;z0,z1=t[:,1].min()-margin,t[:,1].max()+margin
                if x1<xs[0] or x0>xs[-1] or z1<zs[0] or z0>zs[-1] or (x1-x0)>40 or (z1-z0)>40: continue
                B[np.searchsorted(zs,z0):np.searchsorted(zs,z1,'right'),np.searchsorted(xs,x0):np.searchsorted(xs,x1,'right')]=True
    return B
def dirt_mask():
    A=np.load('/workspace/rpotm/geo/xz_to_uv.npy')
    G=np.array(Image.open('/tmp/google2.png'))
    N=np.array(Image.open('/workspace/rpotm/geo/naip_in_g2frame.png'))
    xs=np.arange(-386,-308,1.0);zs=np.arange(-955,-325,1.0);X,Zg=np.meshgrid(xs,zs)
    def samp(img):
        uv=np.c_[X.ravel(),Zg.ravel()]@A[:,:2].T+A[:,2]
        u=np.clip((uv[:,0]%1*8192).astype(int),0,8191);v=np.clip(((uv[:,1]%1)*4096).astype(int),0,4095)
        return img[v,u].reshape(X.shape+(img.shape[-1],)).astype(float)
    g,n=samp(G),samp(N)
    ndvi=(n[...,1]-n[...,0])/(n[...,1]+n[...,0]+1e-6)
    g_green=(g[...,1]>g[...,0]+8)&(g[...,1]>g[...,2]+8)
    dirt=(~g_green)&(ndvi<=0.06)&(g.mean(2)>125)&((g.max(2)-g.min(2))<55)
    _,P1,_,n1=cline(ST190);_,P2,_,n2=cline(WR);_,P3,_,n3=cline(EXIT);LOOPC=[(cline(p)[1],cline(p)[3],hw) for _,p,hw in LOOP]
    def lat(P,nn,x,z):
        k=int(np.argmin((P[:,0]-x)**2+(P[:,1]-z)**2));along=(k==0 or k==len(P)-1)
        d=np.array([x,z])-P[k];return abs(float(d@nn[k])) if not along else float(np.hypot(*d))
    for j in range(dirt.shape[0]):
        for i in range(dirt.shape[1]):
            if not dirt[j,i]: continue
            x,z=X[j,i],Zg[j,i]
            l2=lat(P2,n2,x,z)
            if lat(P1,n1,x,z)<5.0 or l2<HALF+1.0: dirt[j,i]=False
            elif z>JOIN_Z-10 and l2<HALF+5.0: dirt[j,i]=False
            elif lat(P3,n3,x,z)<HALF+5.0: dirt[j,i]=False   # v14: grass verge along the 190th exit
            elif any(lat(Pl,nl,x,z)<hw+5.0 for Pl,nl,hw in LOOPC): dirt[j,i]=False   # v15 verges   # v13: grass verge beside the new join
            if -306.5<=x<=-240.5 and -962<=z<=-333: dirt[j,i]=False
            if -391<=x<=-290 and ((-808<=z<=-794) or (-959<=z<=-945)): dirt[j,i]=False
    from numpy.lib.stride_tricks import sliding_window_view
    def mop(m):
        p=np.pad(m,1,constant_values=False);w=sliding_window_view(p,(3,3));er=w.all((-1,-2))
        p2=np.pad(er,1,constant_values=False);dil=sliding_window_view(p2,(3,3)).any((-1,-2))
        p3=np.pad(dil,1,constant_values=False);return sliding_window_view(p3,(3,3)).any((-1,-2))
    dirt=mop(dirt)
    # v13 softer edges: 5x5 majority
    from numpy.lib.stride_tricks import sliding_window_view as swv
    dirt=swv(np.pad(dirt,2),(5,5)).sum((-1,-2))>=13
    dirt&=~object_block(xs,zs)    # never on containers / tents / huts / poles
    return xs,zs,dirt,X,Zg
def build_gravel():
    xs,zs,dirt,X,Zg=dirt_mask()
    box=(-390,-300,-970,-310);tx,tz,H,KEY,UP,names=terrain_H(box,0.5)
    H_,W_=dirt.shape;seen=np.zeros_like(dirt);patches=[];from collections import deque
    for j0 in range(H_):
        for i0 in range(W_):
            if not dirt[j0,i0] or seen[j0,i0]: continue
            q=deque([(j0,i0)]);seen[j0,i0]=1;cells=[]
            while q:
                j,i=q.popleft();cells.append((j,i))
                for dj,di in ((0,1),(0,-1),(1,0),(-1,0)):
                    nj,ni=j+dj,i+di
                    if 0<=nj<H_ and 0<=ni<W_ and dirt[nj,ni] and not seen[nj,ni]:
                        seen[nj,ni]=1;q.append((nj,ni))
            if len(cells)>=4: patches.append(cells)
    print(f'west lot dirt: {dirt.mean()*100:.1f}% of lot box, {len(patches)} patches, {sum(map(len,patches))} cells')
    meshes=[]
    for pi,cells in enumerate(patches):
        V=[];I=[];vid={};part=0
        def v(gx,gz):
            if (gx,gz) not in vid:
                x,z=xs[0]-0.5+gx,zs[0]-0.5+gz;y=float(sampleH(tx,tz,H,np.array([[x,z]]))[0])+LIFT
                if np.isnan(y): y=0.0
                u,w=uv_g(x,z);vid[gx,gz]=len(V);V.append([x,y,z,0,1,0,u,w,1,0,0])
            return vid[gx,gz]
        for j,i in cells:
            cx=np.array([[xs[0]-0.5+i+dx,zs[0]-0.5+j+dz] for dx in (0,1) for dz in (0,1)])
            if np.isnan(sampleH(tx,tz,H,cx)).any(): continue   # no grass terrain here (other ground mesh) -> no gravel
            a0,a1,a2,a3=v(i,j),v(i+1,j),v(i+1,j+1),v(i,j+1);I+=[[a0,a2,a1],[a0,a3,a2]]
            if len(V)>60000:
                Vv,Ii=fixn(np.array(V,'<f4'),np.array(I));meshes.append((f'1GRAVEL_WESTLOT_{pi}_{part}',Vv,Ii));part+=1;V=[];I=[];vid={}
        if I:
            Vv,Ii=fixn(np.array(V,'<f4'),np.array(I));meshes.append((f'1GRAVEL_WESTLOT_{pi}'+(f'_{part}' if part else ''),Vv,Ii))
    return meshes,dirt.mean(),len(patches)
def rebuild_roads(west_meshes):
    src='/tmp/vf_roads_v11.kn5' if os.path.exists('/tmp/vf_roads_v11.kn5') else f'{Z}/vf_roads.kn5'
    existing=[]
    for m in VM.vismeshes(src):
        if m['name'].startswith(('1CONCRETE_WESTRD','1CONCRETE_LOTRD','1CONCRETE_LOTEXIT','1CONCRETE_LOOP','1CONCRETE_DRAGX_B_west','1CONCRETE_DRAGX_C_west')): continue
        existing.append(dict(name=m['name'],mat_index=0,verts=m['V'].astype('<f4'),idx=m['I'].astype('<u2'),lod_out=0))
    cm=W.read_materials(MAIN)['Concrete01'];texs=[(tn,K.get_tex(MAIN,tn)) for tn in dict.fromkeys(t for _,_,t in cm['samplers'])]
    mats=[dict(name='Concrete01_roads',shader=cm['shader'],ab=cm['ab'],at=cm['at'],dm=cm['dm'],props=cm['props'],samplers=cm['samplers'])]
    out=existing+[dict(name=nm,mat_index=0,verts=V,idx=I,lod_out=0) for nm,V,I in west_meshes]
    W.write_kn5(f'{Z}/vf_roads.kn5',texs,mats,out,rootname='vf_roads')
    print('vf_roads.kn5 now:',[o['name'] for o in out])
def write_westlot(gravel):
    own=f'{Z}/vf_i29_speedway_own.kn5';gm=W.read_materials(own)['own_gravel']
    texs=[(tn,K.get_tex(own,tn)) for tn in dict.fromkeys(t for _,_,t in gm['samplers'])]
    mats=[dict(name='westlot_gravel',shader=gm['shader'],ab=gm['ab'],at=gm['at'],dm=gm['dm'],props=gm['props'],samplers=gm['samplers'])]
    out=[dict(name=nm,mat_index=0,verts=V,idx=I,lod_out=0) for nm,V,I in gravel]
    W.write_kn5(f'{Z}/vf_westlot.kn5',texs,mats,out,rootname='vf_westlot')
    print('vf_westlot.kn5:',len(out),'meshes',os.path.getsize(f'{Z}/vf_westlot.kn5')//1024,'KB')
def ensure_models():
    import re
    for fn in ('models_main.ini','models_short.ini'):
        p=f'{Z}/{fn}';t=open(p,encoding='utf-8').read()
        if 'vf_westlot.kn5' in t: continue
        ns=[int(x) for x in re.findall(r'\[MODEL_(\d+)\]',t)];n=max(ns)+1 if ns else 14
        if not t.endswith('\n'): t+='\n'
        t+=f'\n[MODEL_{n}]\nFILE=vf_westlot.kn5\nPOSITION=0,0,0\nROTATION=0,0,0\nSCALE=1,1,1\n'
        open(p,'w',newline='\n').write(t);print('appended MODEL',n,'to',fn)
def main():
    print('=== west-lot access road ===')
    west,P,n=build_west_road();print('west meshes',[m[0] for m in west],'centreline',len(P),'m')
    rebuild_roads(west)
    print('=== west lot gravel ===')
    gravel,frac,np_=build_gravel();write_westlot(gravel);ensure_models()
    print(f'done: dirt coverage {100*frac:.1f}%, {np_} patches')
if __name__=='__main__': main()
