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
bad={k:v for k,v in c.items() if k.startswith(('1WALL','1CONCRETE'))};print('drag lanes top surfaces:',c,'-> walls/concrete on lanes:',bad or 'none');fails+=bool(bad)
# 2) south road + return road: concrete on top
import roads_concrete as R
q,P,t,nn=R.centreline();G=(P[:,None,:]+np.linspace(-3.5,3.5,8)[None,:,None]*nn[:,None,:]).reshape(-1,2)
xs,zs,H,KEY,names=top((-402,210,232,260),0.25);i=np.round((G[:,0]-xs[0])/0.25).astype(int);j=np.round((G[:,1]-zs[0])/0.25).astype(int)
share=np.mean([names[k].startswith('1CONCRETE') for k in KEY[j,i]]);print(f'south road (8 m wide, sampled +-3.5 m): {100*share:.1f} % concrete on top');fails+=share<0.98
xs,zs,H,KEY,names=top((-302,-294,-950,-552));n=np.array(names)[KEY[KEY>=0]];share=np.mean([k.startswith('1CONCRETE') for k in n]);print(f'return road: {100*share:.1f} % concrete on top');fails+=share<0.9
# 3) collision proxies vs AI lines (both layouts) and pit spawns
M=[t for fn,nm,t in PR.physmeshes(['vf_dragcol.kn5'],(-5000,5000,-5000,5000))];W_=np.vstack([t.reshape(-1,3) for t in M])
for lay in ('main','short'):
    for ln in ('fast_lane','pit_lane'):
        p=f'{Z}{lay}/ai/{ln}.ai'
        if not os.path.exists(p): continue
        P=C.read_ai(p)['P']['p'].astype(float);d=min(np.hypot(W_[:,0]-x,W_[:,2]-z).min() for x,_,z in P[::2]);print(f'{lay} {ln}: nearest collision proxy {d:.1f} m');fails+=d<4
pits=[n['W'][3,:3] for n in T.walk(f'{Z}vf_i29_speedway.kn5') if n['cls']==1 and n['name'].startswith(('AC_PIT_','AC_START_','AC_HOTLAP'))]
d=min(np.hypot(W_[:,0]-p[0],W_[:,2]-p[2]).min() for p in pits);print(f'spawns/start points: nearest proxy {d:.1f} m');fails+=d<6
print('roads_verify fails:',fails);sys.exit(1 if fails else 0)
