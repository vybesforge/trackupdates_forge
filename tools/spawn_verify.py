# VR9: footprint flatness limit 6 cm over the 5.2 m box (lidar paddock grade up to ~1 %; was 2 cm on zwiss's flat paddock)
import sys,numpy as np,collections
import os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));import kn5patch as K,kn5tree as T
from physraster import physmeshes,raster
Z=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','vf_i29_speedway')+'/'
for f in ['vf_i29_speedway.kn5']: K.scan(Z+f);print('scan OK',f)
pits=sorted([(int(n['name'][7:]),n['W']) for n in T.walk(Z+'vf_i29_speedway.kn5') if n['cls']==1 and n['name'].startswith('AC_PIT_')])
print('pits',len(pits),'unique idx',len(set(i for i,_ in pits)))
res=0.5;box=(-230,180,-60,245)
for lay,files in [('main',['vf_i29_speedway.kn5','vf_i29_speedway_physical.kn5','vf_i29_speedway_gp.kn5','vf_i29_speedway_own.kn5','vf_ext.kn5','vf_dragexit.kn5','vf_tents.kn5','vf_vegetation.kn5']),('short',['vf_i29_speedway.kn5','vf_i29_speedway_physical.kn5','vf_i29_speedway_sh.kn5','vf_i29_speedway_own.kn5','vf_ext.kn5','vf_dragexit.kn5','vf_tents.kn5','vf_vegetation.kn5'])]:
    M=physmeshes(files,box);xs,zs,H,KEY,UP,names=raster(M,box,res)
    ok=0;worst=0
    for i,W in pits:
        p=W[3,:3];f=W[2,:3];r=W[0,:3]
        hs=[];ks=set()
        for a in np.linspace(-2.6,2.6,9):
            for b in np.linspace(-1.1,1.1,5):
                q=p+a*f+b*r;ii=int(round((q[0]-xs[0])/res));jj=int(round((q[2]-zs[0])/res))
                hs.append(H[jj,ii]);ks.add(names[KEY[jj,ii]] if KEY[jj,ii]>=0 else None)
        hs=np.array(hs);flat=np.nanmax(hs)-np.nanmin(hs);clear=p[1]-np.nanmax(hs)
        good=(ks=={'1GRAVEL_PADDOCK'}) and flat<0.06 and 0.2<clear<1.0 and UP[int(round((p[2]-zs[0])/res)),int(round((p[0]-xs[0])/res))]
        ok+=good;worst=max(worst,flat)
        if not good: print(lay,'PIT',i,ks,flat,clear)
    print(lay,'footprint OK',ok,'/36, max height variation %.3f m, dummy clearance %.2f m'%(worst,clear))
    # walls
    wall=np.zeros(H.shape,bool)
    for fn,n,Tr in M:
        if 'WALL' in n or 'FENCE' in n:
            for t in Tr:
                for s in np.linspace(0,1,40):
                    for u in np.linspace(0,1-s,max(2,int(40*(1-s)))):
                        q=t[0]+s*(t[1]-t[0])+u*(t[2]-t[0]);ii=int(round((q[0]-xs[0])/res));jj=int(round((q[2]-zs[0])/res))
                        if 0<=ii<len(xs) and 0<=jj<len(zs): wall[jj,ii]=True
    # inflate walls by 1.2 m (half car width + margin)
    from numpy.lib.stride_tricks import sliding_window_view
    rr=int(1.2/res);pad=np.pad(wall,rr);blk=sliding_window_view(pad,(2*rr+1,2*rr+1)).any((2,3))
    drv=(KEY>=0)&UP&~blk&(KEY!=(names.index('1GRASS') if '1GRASS' in names else -9))
    # target: the pit-out road at the track junction
    tgt=set()
    for jj in range(len(zs)):
        for ii in range(len(xs)):
            if KEY[jj,ii]>=0 and names[KEY[jj,ii]]=='1ROAD_pitout' and xs[ii]<-170: tgt.add((jj,ii))
    # also count track road
    s0=(int(round((56-zs[0])/res)),int(round((92-xs[0])/res)))
    prev={s0:None};dq=collections.deque([s0]);hit=None
    while dq:
        c=dq.popleft()
        if c in tgt and hit is None: hit=c
        for dj,di in((1,0),(-1,0),(0,1),(0,-1)):
            n=(c[0]+dj,c[1]+di)
            if 0<=n[0]<len(zs) and 0<=n[1]<len(xs) and drv[n] and n not in prev and abs(H[n]-H[c])<0.15: prev[n]=c;dq.append(n)
    reach=set(prev)
    print(lay,'path PIT_0 -> pit-out road at x<-170:', 'FOUND' if hit else 'NONE', 'len %.0f m'%(len(reach) and 0))
    path=[];c=hit
    while c: path.append(c);c=prev[c]
    surf=collections.Counter(names[KEY[c]] for c in path);print(lay,'path length %.0f m, surfaces'%(len(path)*res),dict(surf))
    allr=sum(1 for i,W in pits if (int(round((W[3,2]-zs[0])/res)),int(round((W[3,0]-xs[0])/res))) in reach);print(lay,'pits connected',allr)
    np.save(f'path_{lay}.npy',np.array([[xs[c[1]],zs[c[0]]] for c in path]))
