"""roads-concrete checks: overlays on top where intended, drag lanes untouched, no collision proxy near AI lines / pit spawns."""
import os,sys,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import physraster as PR,vr7_common as C,kn5tree as T
Z=PR.Z;fails=0
files=[f for f in os.listdir(Z) if f.endswith('.kn5')]
def top(box,res=0.5):
    M=PR.physmeshes(files,box);xs,zs,H,KEY,UP,names=PR.raster(M,box,res);return xs,zs,H,KEY,names
# 1) drag strip + launch lanes: the top surface must still be the strip / launch pads (not concrete, not a wall)
xs,zs,H,KEY,names=top((-261,-243,-955,-340));n=np.array(names)[KEY[KEY>=0]];c={str(k):int((n==k).sum()) for k in set(n)}
bad={k:v for k,v in c.items() if k.startswith(('1WALL','1CONCRETE','1GRAVEL'))};print('drag lanes top surfaces:',c,'-> walls/concrete on lanes:',bad or 'none');fails+=bool(bad)
# 2) south road + return road: concrete on top
import roads_concrete as R
q,P,t,nn=R.centreline();G=(P[:,None,:]+np.linspace(-3.5,3.5,8)[None,:,None]*nn[:,None,:]).reshape(-1,2)
xs,zs,H,KEY,names=top((-402,210,232,260),0.25);i=np.round((G[:,0]-xs[0])/0.25).astype(int);j=np.round((G[:,1]-zs[0])/0.25).astype(int)
share=np.mean([names[k].startswith('1CONCRETE') for k in KEY[j,i]]);print(f'south road (8 m wide, sampled +-3.5 m): {100*share:.1f} % concrete on top');fails+=share<0.98
xs,zs,H,KEY,names=top((-302,-294,-950,-552));n=np.array(names)[KEY[KEY>=0]];share=np.mean([k.startswith('1CONCRETE') for k in n]);print(f'return road: {100*share:.1f} % concrete on top');fails+=share<0.9
# west-lot access road (x~-345) concrete on top; 190th St (vf_ext asphalt) untouched
import west_lot as WL
q,P,t,nn=WL.cline(WL.WR);G=(P[:,None,:]+np.linspace(-2.5,2.5,6)[None,:,None]*nn[:,None,:]).reshape(-1,2)
xs,zs,H,KEY,names=top((-360,-330,-875,-325),0.25)
i=np.clip(np.round((G[:,0]-xs[0])/0.25).astype(int),0,len(xs)-1);j=np.clip(np.round((G[:,1]-zs[0])/0.25).astype(int),0,len(zs)-1)
share=np.mean([names[k].startswith('1CONCRETE') for k in KEY[j,i]]);print(f'west-lot access road (sampled +-2.5 m): {100*share:.1f} % concrete on top');fails+=share<0.97
q,P,t,nn=WL.cline(WL.EXIT);G=(P[:,None,:]+np.linspace(-2.5,2.5,6)[None,:,None]*nn[:,None,:]).reshape(-1,2);xs,zs,H,KEY,names=top((-392,-340,-855,-835),0.25)
i=np.clip(np.round((G[:,0]-xs[0])/0.25).astype(int),0,len(xs)-1);j=np.clip(np.round((G[:,1]-zs[0])/0.25).astype(int),0,len(zs)-1)
share=np.mean([names[k].startswith('1CONCRETE') for k in KEY[j,i]]);print(f'west-lot 190th exit (sampled +-2.5 m): {100*share:.1f} % concrete on top');fails+=share<0.97
for nm,pts,hw in WL.LOOP:
    q,P,t,nn=WL.cline(pts);G=(P[:,None,:]+np.linspace(-(hw-0.5),hw-0.5,6)[None,:,None]*nn[:,None,:]).reshape(-1,2)
    bx=(G[:,0].min()-2,G[:,0].max()+2,G[:,1].min()-2,G[:,1].max()+2);xs,zs,H,KEY,names=top(bx,0.25)
    i=np.clip(np.round((G[:,0]-xs[0])/0.25).astype(int),0,len(xs)-1);j=np.clip(np.round((G[:,1]-zs[0])/0.25).astype(int),0,len(zs)-1)
    share=np.mean([names[k].startswith('1CONCRETE') for k in KEY[j,i]]);print(f'{nm}: {100*share:.1f} % concrete on top');fails+=share<0.97
# loop connectivity: walk 1 m cells of concrete from the lot road north end; all loop pieces + apron must be reachable
xs,zs,H,KEY,names=top((-395,-285,-875,-320),1.0);CON=np.vectorize(lambda k:k>=0 and names[k].startswith('1CONCRETE'))(KEY)
from collections import deque
st=(int(round(-866-zs[0])),int(round(-344.5-xs[0])));seen=np.zeros_like(CON);dq=deque([st]);seen[st]=True
while dq:
    j,i=dq.popleft()
    for dj,di in ((0,1),(0,-1),(1,0),(-1,0)):
        a,b=j+dj,i+di
        if 0<=a<CON.shape[0] and 0<=b<CON.shape[1] and CON[a,b] and not seen[a,b]: seen[a,b]=True;dq.append((a,b))
probes={'lot exit @190th':(-386,-845.5),'link800 east':(-305,-801),'link624 east':(-305,-624),'return road N':(-298,-900),'return ext S':(-300,-335),'apron':(-320,-325)}
for k,(x,z) in probes.items():
    ok=bool(seen[int(round(z-zs[0])),int(round(x-xs[0]))]);print(f'connected: {k}: {ok}');fails+=not ok
q,P,t,nn=WL.cline(WL.ST190);xs,zs,H,KEY,names=top((-412,-380,-990,240),0.5)
i=np.clip(np.round((P[:,0]-xs[0])/0.5).astype(int),0,len(xs)-1);j=np.clip(np.round((P[:,1]-zs[0])/0.5).astype(int),0,len(zs)-1)
bad=sum(names[k].startswith(('1CONCRETE_LOTRD','1CONCRETE_LOTEXIT','1GRAVEL_WESTLOT')) for k in KEY[j,i] if k>=0);print(f'190th St centreline: {bad} points covered by new overlays (expect 0)');fails+=bad>0
import vismeshes as VM
# v13: gravel lies on the ground (<=5 cm above 1GRASS terrain) and never on object footprints
xs_,zs_,Ht,_,_,_=WL.terrain_H((-390,-300,-970,-310),0.5)
gv=np.vstack([m['V'][:,:3].astype(float) for m in VM.vismeshes(f'{Z}vf_westlot.kn5')])
dh=gv[:,1]-WL.sampleH(xs_,zs_,Ht,gv[:,[0,2]]);print(f'gravel height above ground: max {dh.max()*100:.1f} cm, min {dh.min()*100:.1f} cm');fails+=dh.max()>0.05
bx=np.arange(-390,-300,0.5);bz=np.arange(-970,-310,0.5);OB=WL.object_block(bx,bz,0.0)
ii=np.clip(((gv[:,0]-bx[0])/0.5).astype(int),0,len(bx)-1);jj=np.clip(((gv[:,2]-bz[0])/0.5).astype(int),0,len(bz)-1)
inside=int(OB[jj,ii].sum());print(f'gravel vertices inside object footprints: {inside} (expect 0)');fails+=inside>0
# west lot: gravel share on dirt-classified cells, grass elsewhere
xs,zs,dirt,XX,ZZ=WL.dirt_mask();txs,tzs,H,KEY,names=top((-390,-308,-955,-325),1.0)
ok=0;tot=0;grav=0;grass=0
for j in range(0,dirt.shape[0],2):
  for i in range(0,dirt.shape[1],2):
    x,z=float(XX[j,i]),float(ZZ[j,i]);ii=int(round((x-txs[0])/1.0));jj=int(round((z-tzs[0])/1.0))
    if not (0<=ii<len(txs) and 0<=jj<len(tzs)): continue
    k=KEY[jj,ii]
    if k<0: continue
    nm=names[k];tot+=1
    if dirt[j,i]:
      grav+=nm.startswith('1GRAVEL');ok+=nm.startswith('1GRAVEL')
    else:
      grass+=nm.startswith('1GRASS');ok+=nm.startswith(('1GRASS','1CONCRETE'))  # concrete road edges OK
print(f'west lot sample: gravel-on-dirt {grav}, grass-on-non-dirt {grass}, ok {ok}/{tot}');fails+=tot and ok/tot<0.7
# 3) collision proxies vs AI lines (both layouts) and pit spawns
M=[t for fn,nm,t in PR.physmeshes(['vf_dragcol.kn5'],(-5000,5000,-5000,5000))];W_=np.vstack([t.reshape(-1,3) for t in M])
for lay in ('main','short'):
    for ln in ('fast_lane','pit_lane'):
        p=f'{Z}{lay}/ai/{ln}.ai'
        if not os.path.exists(p): continue
        P=C.read_ai(p)['P']['p'].astype(float);d=min(np.hypot(W_[:,0]-x,W_[:,2]-z).min() for x,_,z in P[::2]);print(f'{lay} {ln}: nearest collision proxy {d:.1f} m');fails+=d<4
pits=[n['W'][3,:3] for n in T.walk(f'{Z}vf_i29_speedway.kn5') if n['cls']==1 and n['name'].startswith(('AC_PIT_','AC_START_','AC_HOTLAP'))]
d=min(np.hypot(W_[:,0]-p[0],W_[:,2]-p[2]).min() for p in pits);print(f'spawns/start points: nearest proxy {d:.1f} m');fails+=d<6
# AI lines: new overlays must not be the top surface under any AI point
NEW=('1CONCRETE_LOTRD','1CONCRETE_LOTEXIT','1CONCRETE_LOOP','1GRAVEL_WESTLOT')
for lay in ('main','short'):
    for ln in ('fast_lane','pit_lane'):
        p=f'{Z}{lay}/ai/{ln}.ai'
        if not os.path.exists(p): continue
        P=C.read_ai(p)['P']['p'].astype(float);bx=(P[:,0].min()-2,P[:,0].max()+2,P[:,2].min()-2,P[:,2].max()+2)
        near=P[(P[:,0]<-300)]
        if not len(near): print(f'{lay} {ln}: no AI points west of x -300 -> new west overlays cannot affect it');continue
        b2=(near[:,0].min()-2,near[:,0].max()+2,near[:,2].min()-2,near[:,2].max()+2);xs,zs,H,KEY,names=top(b2,0.5)
        i=np.clip(np.round((near[:,0]-xs[0])/0.5).astype(int),0,len(xs)-1);j=np.clip(np.round((near[:,2]-zs[0])/0.5).astype(int),0,len(zs)-1)
        hit=sum(names[k].startswith(NEW) for k in KEY[j,i] if k>=0);print(f'{lay} {ln}: {hit} AI points on new west overlays');fails+=hit>0
print('roads_verify fails:',fails);sys.exit(1 if fails else 0)
