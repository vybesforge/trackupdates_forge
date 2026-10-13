"""VR7 AI-line validator. python tools/vr7_ai_validate.py [layout ...]  (default main short). Exit 1 on any failure.
Checks: (1) format: v7 header, point count == extra count, exact file size (points*20 + extra*72 + tail), finite values,
ids 0..n-1, cumulative length monotonic; (2) continuity: spacing 0.5-3 m, heading change < 25 deg/point (fast) / 35 (pit);
fast lane closed (end->start < 3 m); (3) direction: >= 95 % of points run the same way as zwiss's recorded line;
(4) surface: the point and +-1.0 m laterally lie on drivable physics (fast: ROAD/CURB only, i.e. IS_VALID_TRACK=1 and not the
long-course SCUT cut; pit: ROAD/CURB/PITS/CONCRETE/GRAVEL), y within 0.25..0.55 m above the physics;
(5) pit lane starts and ends within 6 m of the fast lane, and every paddock box is within 18 m (2nd row: lane runs in front of row 1) of it; speeds 0 < v < 90 m/s."""
import sys,os,struct,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import vr7_common as C,kn5tree as T
from vr7_ai import Grid,ORIG
from scipy.spatial import cKDTree
def check(lay):
    g=Grid(lay);fails=[];rep={}
    def F(c,msg):
        if not c: fails.append(msg)
    for lane in('fast_lane','pit_lane'):
        f=C.Z+f'{lay}/ai/{lane}.ai';d=open(f,'rb').read();a=C.read_ai(f);n=len(a['P']);P=a['P']['p'].astype(float);E=a['E']
        F(a['version']==7,f'{lane}: version {a["version"]}');F(len(E)==n,f'{lane}: extra count')
        tl=len(a['tail']);F(len(d)==16+n*20+4+n*72+tl and tl>=4,f'{lane}: size');F(np.isfinite(P).all() and np.isfinite(E).all(),f'{lane}: NaN')
        F((a['P']['id']==np.arange(n)).all(),f'{lane}: ids');F((np.diff(a['P']['l'])>0).all(),f'{lane}: length not monotonic')
        xz=P[:,[0,2]];closed=lane=='fast_lane';seg=np.linalg.norm(np.diff(np.vstack([xz,xz[:1]]) if closed else xz,axis=0),axis=1)
        F(seg.min()>0.5 and seg.max()<3,f'{lane}: spacing {seg.min():.2f}..{seg.max():.2f}')
        t=np.diff(np.vstack([xz,xz[:1]]) if closed else xz,axis=0);h=np.arctan2(t[:,1],t[:,0]);dh=np.degrees(np.abs((np.diff(h)+np.pi)%(2*np.pi)-np.pi))
        F(dh.max()<(25 if closed else 35),f'{lane}: heading jump {dh.max():.1f} deg')
        if closed: F(seg[-1]<3,f'{lane}: not closed ({seg[-1]:.1f} m)')
        o=C.read_ai(f'{ORIG}/{lay}/{lane}.ai')['P']['p'][:,[0,2]];to=np.gradient(o,axis=0);nn=cKDTree(o).query(xz)
        tp=np.gradient(xz,axis=0);same=(np.sum(to[nn[1]]*tp,1)>0)[nn[0]<4].mean() if (nn[0]<4).any() else 0
        F(same>=0.95,f'{lane}: direction agreement {same:.2%}')
        keys={'ROAD','CURB'} if closed else {'ROAD','CURB','PITS','CONCRETE','GRAVEL'}
        nrm=np.c_[tp[:,1],-tp[:,0]]/np.linalg.norm(tp,axis=1)[:,None];off=[]
        for s in(-1.0,0,1.0):
            k,hh=g.key(xz[:,0]+s*nrm[:,0],xz[:,1]+s*nrm[:,1]);off.append(~np.isin(k,list(keys)))
            if s==0: dy=P[:,1]-hh
        off=np.any(off,0);F(off.sum()==0,f'{lane}: {off.sum()} points off valid surface, e.g. {xz[off][:3].round(1).tolist()}')
        F(np.nanmin(dy)>0.25 and np.nanmax(dy)<0.55,f'{lane}: y offset {np.nanmin(dy):.2f}..{np.nanmax(dy):.2f}')
        F(E[:,0].min()>0 and E[:,0].max()<90,f'{lane}: speed range')
        rep[lane]=dict(points=n,length_m=round(float(seg.sum()),1),v_kmh=(round(float(E[:,0].min()*3.6)),round(float(E[:,0].max()*3.6))),dir_agree=round(float(same),3))
        if closed: fast=xz
        else:
            tf=cKDTree(fast);F(tf.query(xz[0])[0]<6 and tf.query(xz[-1])[0]<6,f'pit_lane: ends not on fast lane ({tf.query(xz[0])[0]:.1f}, {tf.query(xz[-1])[0]:.1f} m)')
            B=np.array([n_['W'][3,[0,2]] for n_ in T.walk(C.Z+'vf_i29_speedway.kn5') if n_['cls']==1 and n_['name'].startswith('AC_PIT_')])
            db=cKDTree(xz).query(B)[0];F(db.max()<18,f'pit_lane: box max distance {db.max():.1f} m');rep[lane]['box_dist_max_m']=round(float(db.max()),1)
    print(lay,rep);[print('  FAIL',lay,x) for x in fails];return not fails
if __name__=='__main__':
    ok=all([check(l) for l in (sys.argv[1:] or ['main','short'])]);print('ALL OK' if ok else 'FAILED');sys.exit(0 if ok else 1)
