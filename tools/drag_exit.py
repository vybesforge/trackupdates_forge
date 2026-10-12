"""Drag-strip exits (A z-628.5, B z-801, C z-952.4 west crossovers + N-S return road x-298; E z-733 east stub to the circuit). Original note: exit lane (1/8 mile strip, 1DRAGstrip, run = staging z-333 -> north/-z).
Real site (NAIP 2021 0.6 m + Apple Maps): paved crossover on the LEFT (west) of the shutdown area at z≈-628.5 (~8 m wide)
joins the N-S return road at x≈-297 that runs back south to the staging/pit lot (paved from z≈-555).
Builds zw_dragexit.kn5 (1XROAD_dragexit = visual + physics, KEY XROAD: drivable, not valid track, no black flag),
cuts a 16 m gap in the west drag-strip armco (visual armco000*/physics 1WALL_armco) at the crossover,
adds MODEL_6 to models_main/short.ini. Sources read from /workspace/rpotm/backup/*.pre_dragexit."""
import sys,os,struct,re,math,numpy as np
sys.path.insert(0,os.path.dirname(__file__));sys.path.insert(0,os.path.join(os.path.dirname(__file__),'north_ext'))
import kn5patch as K,kn5write as W,build_open_textures as B
from PIL import Image
ROOT=os.path.join(os.path.dirname(__file__),'..');Z=f'{ROOT}/zw_rpm';NO=f'{ROOT}/assets_src/north';BK='/workspace/rpotm/backup'
GAPS=[(-636.0,-620.0),(-808.0,-794.0),(-960.0,-944.0)]   # west armco openings (A, B, C)
Y0=-0.1;YR=Y0+0.012
def sx(z,side): # drag-strip edge x at z (1DRAGstrip: west -260@-333.4 -> -268.5@-958.1, east -242@-333.4 -> -250.5@-958.3)
    t=(z+333.4)/(-958.2+333.4);return (-260-8.5*t) if side=='W' else (-242-8.5*t)
RX=-298.0;RW=8.0  # real return road (NAIP): x≈-298, ~8 m, z -956 .. pit lot (-548)
# lanes: (name, centreline pts, width fn(s,L), blend-edge flags fn(s)->(left,right), start-flush length)
def straight(p0,p1,n): return np.c_[np.linspace(p0[0],p1[0],n),np.linspace(p0[1],p1[1],n)]
STUBS=[('A',-628.5,8.0),('B',-801.0,7.0),('C',-952.4,6.5)]
LANES=[]
for nm,z,wd in STUBS:   # west crossovers: strip west edge -> return road east asphalt edge
    LANES.append((f'1XROAD_dragexit_{nm}',straight((sx(z,'W')+2.0,z),(RX+RW/2,z),16),lambda s,L,wd=wd:wd+5.0*np.clip(1-s/10,0,1),lambda s,L:(1,1),3.0))
ze=-735.5;LANES.append(('1XROAD_dragexit_E',straight((sx(ze,'E')-2.0,ze),(-234.1,ze),10),lambda s,L:6.0+1.0*np.clip(1-s/5,0,1),lambda s,L:(1,1),3.0))
def rr_w(s,L): return RW+np.where(s>L-10,3.5*np.clip((s-(L-10))/10,0,1),0)
def rr_edges(s,L):  # no east blend where a crossover joins
    z=-956.0+s;east=all(abs(z-zc)>wd/2+1.5 for _,zc,wd in STUBS);return (1,1 if east else 0)
LANES.append(('1XROAD_dragexit_return',straight((RX,-956.0),(RX,-548.0),205),rr_w,rr_edges,0.0))
fr=np.array([-0.5,-0.5,-0.32,-0.18,0,0.18,0.32,0.5,0.5]);dy=np.array([-0.012,0,0.004,0.008,0.01,0.008,0.004,0,-0.012])
MESHES=[];PW=[]
for name,P,wf,ef,flush in LANES:
    s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))];L=s[-1];T=np.gradient(P,axis=0);T/=np.linalg.norm(T,axis=1)[:,None];Lf=np.c_[-T[:,1],T[:,0]]
    w=np.array([wf(si,L) for si in s]);V=[];k=len(fr)
    for i in range(len(P)):
        yb=Y0+0.012*(np.clip(s[i]/flush,0,1) if flush else 1);el,er=ef(s[i],L)
        for j in range(k):
            ext=(-1.2*el if j==0 else 1.2*er if j==k-1 else 0);o=fr[j]*w[i]+ext;q=P[i]+Lf[i]*o
            V.append([q[0],yb+(dy[j] if (j not in(0,k-1) or ext!=0) else 0),q[1],0,1,0,0.5+o/7.5,s[i]/16.0,T[i,0],0,T[i,1]])
    V=np.array(V,np.float32);I=[]
    for i in range(len(P)-1):
        for j in range(k-1): a_=i*k+j;I+=[[a_,a_+k+1,a_+1],[a_,a_+k,a_+k+1]]
    I=np.array(I);g=np.cross(V[I[:,1],:3]-V[I[:,0],:3],V[I[:,2],:3]-V[I[:,0],:3]);bad=g[:,1]<0;I[bad]=I[bad][:,[0,2,1]]
    MESHES.append(dict(name=name,mat_index=0,verts=V,idx=I,lod_out=0));PW.append(np.c_[P,w]);print(f'{name}: {L:.0f} m, width {w.min():.1f}-{w.max():.1f} m, {len(I)} tris')
# ---------------- texture: CC0 Asphalt012 base (ext_asphalt) + dark rubber grooves / tyre marks along the lane
rng=np.random.default_rng(29);base=np.array(Image.open(f'{NO}/ext_asphalt.png').convert('RGB')).astype(np.float32);base=base/base.mean((0,1))*np.array([176,174,165])  # light grey to match NAIP crossover (~189,187,177)
H,Wd=2048,1024;tex=np.tile(base,(2,1,1))[:H,:Wd].copy();u=np.arange(Wd)/Wd;v=np.arange(H)/H
dark=np.zeros((H,Wd),np.float32)
for c0 in(0.5-1.6/7.5,0.5+1.6/7.5,0.5-0.85/7.5,0.5+0.85/7.5):   # two wheel tracks per lane, rubber groove
    sig=0.025+0.01*rng.random();dark+=0.35*np.exp(-((u[None,:]-c0)/sig)**2)*np.ones((H,1))
for _ in range(14):                     # individual curving tyre streaks
    c0=rng.uniform(0.25,0.75);amp=rng.uniform(0.005,0.03);ph=rng.uniform(0,6.28);wd=rng.uniform(0.006,0.015)
    cu=c0+amp*np.sin(2*np.pi*v+ph);a0=rng.uniform(0.2,0.55)
    dark+=a0*np.exp(-((u[None,:]-cu[:,None])/wd)**2)*np.clip(np.sin(np.pi*(v[:,None]*rng.integers(1,3)+ph))*1.5,0,1)
n=np.array(Image.fromarray((rng.random((64,32))*255).astype(np.uint8)).resize((Wd,H),Image.BILINEAR))/255.0
dark=np.clip(dark*(0.75+0.5*n),0,0.6);tex*=(1-dark[...,None]);tex[...,:]+=(-3*dark)[...,None]
tex=tex/tex[dark<0.05].mean(0)*np.array([176,174,165]) if False else tex
tex=np.clip(tex,0,255).astype(np.uint8);rgba=np.dstack([tex,np.full((H,Wd),255,np.uint8)])
Image.fromarray(tex).save(f'{NO}/drag_exit_asphalt.png');DDS=B.write_dds(rgba,'DXT1',12,None);open(f'{NO}/drag_exit_asphalt.dds','wb').write(DDS)
TEX=[('drag_exit_asphalt.dds',DDS)]+[(n_,open(f'{NO}/{n_}','rb').read()) for n_ in('ext_asphalt_nm.dds','ext_asphalt_maps.dds','ext_flat_nm.dds')]
TM=W.read_materials(f'{BK}/zw_rpm.kn5.pre_dragexit');MMp=TM['wc']
def P_(props,**kw): return [(p,struct.pack('<f',kw[p])+r[4:]) if p in kw else (p,r) for p,r in props]
MAT=[dict(name='drag_exit_asphalt',shader='ksPerPixelMultiMap',ab=MMp['ab'],at=MMp['at'],dm=MMp['dm'],props=P_(MMp['props'],ksAmbient=0.3,ksDiffuse=0.3,ksSpecular=0.15,ksSpecularEXP=25),
     samplers=[('txDiffuse',0,'drag_exit_asphalt.dds'),('txNormal',1,'ext_asphalt_nm.dds'),('txMaps',2,'ext_asphalt_maps.dds'),('txDetail',3,'ext_flat_nm.dds')])]
W.write_kn5(f'{Z}/zw_dragexit.kn5',TEX,MAT,MESHES,rootname='zw_dragexit')
print('zw_dragexit.kn5 tris',sum(len(m['idx']) for m in MESHES))
np.save('/tmp/dragexit_P.npy',np.vstack(PW))
# ---------------- armco gap: clip west-side armco triangles out of z in GAP (x < -258)
def clip_tri(tv,keep):  # Sutherland-Hodgman against half-plane keep(v)->signed value >=0 keeps
    out=tv
    for f_ in keep:
        res=[];n_=len(out)
        for i in range(n_):
            a,b=out[i],out[(i+1)%n_];fa,fb=f_(a),f_(b)
            if fa>=0: res.append(a)
            if (fa>=0)!=(fb>=0): t=fa/(fa-fb);res.append(a+(b-a)*t)
        out=res
        if not out: break
    return out
def gapcut(src,dst,names):
    d=open(src,'rb').read();_,nodes=K.scan(src);edits=[];tot=0
    for name,o,l,c in nodes:
        if c!=2 or name not in names: continue
        q=o+l+8;nv,=struct.unpack_from('<I',d,q);Vv=np.frombuffer(d,'<f4',nv*11,q+4).reshape(nv,11).astype(np.float64)
        q2=q+4+nv*44;ni,=struct.unpack_from('<I',d,q2);Ii=np.frombuffer(d,'<u2',ni,q2+4).reshape(-1,3)
        NV=list(Vv);NI=[];cut=0
        for t in Ii:
            tv=Vv[t];zmin,zmax=tv[:,2].min(),tv[:,2].max()
            if tv[:,0].max()>-258 or not any(zmax>g0 and zmin<g1 for g0,g1 in GAPS): NI.append(list(t));continue
            cut+=1;pieces=[[x for x in tv]]
            for g0,g1 in GAPS:
                nxt=[]
                for pc in pieces:
                    for keep in([lambda v,g0=g0:g0-v[2]],[lambda v,g1=g1:v[2]-g1]):
                        q_=clip_tri(pc,keep)
                        if len(q_)>=3: nxt.append(q_)
                pieces=nxt
            for poly in pieces:
                base=len(NV);NV+=poly
                for j in range(1,len(poly)-1): NI.append([base,base+j,base+j+1])
        if not cut: continue
        NV=np.array(NV,'<f4');NI=np.array(NI,'<u2');assert len(NV)<65536
        edits.append((q,q2+4+ni*2,struct.pack('<I',len(NV))+NV.tobytes()+struct.pack('<I',NI.size)+NI.tobytes()));tot+=cut;print(f'  {os.path.basename(dst)} {name}: {cut} tris clipped for gap')
    edits.sort();out=bytearray();pos=0
    for a,b,r in edits: out+=d[pos:a]+r;pos=b
    out+=d[pos:];open(dst,'wb').write(bytes(out));return tot
gapcut(f'{BK}/zw_rpm.kn5.pre_dragexit',f'{Z}/zw_rpm.kn5',{'armco000_SUB0','armco000BACK_SUB0'})
gapcut(f'{BK}/zw_rpm_physical.kn5.pre_dragexit',f'{Z}/zw_rpm_physical.kn5',{'1WALL_armco'})
for lay in('main','short'):
    p=f'{Z}/models_{lay}.ini';t=open(p,'rb').read().decode()
    if 'zw_dragexit.kn5' not in t:
        k=max(int(x) for x in re.findall(r'\[MODEL_(\d+)\]',t))+1;nl='\r\n' if '\r\n' in t else '\n'
        t=t.rstrip('\r\n')+f'{nl}{nl}[MODEL_{k}]{nl}FILE=zw_dragexit.kn5{nl}POSITION=0,0,0{nl}ROTATION=0,0,0{nl}';open(p,'wb').write(t.encode())
print('models ini updated')
