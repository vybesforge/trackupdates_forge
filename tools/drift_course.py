"""Paddock-lot drift course (v1.1 pass 3): drift line, clipping points, outer zones, barriers, markings and tent slots.
Pure geometry/data; tents_v11.py builds the meshes into zw_tents.kn5 and the previews draw it.
Course (clockwise seen from above, x right / z up on the map): entry from the spawn side at the SW corner (38,106) heading +z, linked
left-right transitions up the west side, big sweeper around the north donut area (donut centre (78,166), painted ring r 9),
east sweeper/hairpin, then a long south straight back towards the entry. Width of the run-off: barriers 7.5 m outside the
drift line on the outer side of every turn, tents >= 15 m from the line (centre) = >= 10.7 m from any tent edge."""
import numpy as np
CTRL=np.array([(38,106),(32,128),(40,146),(35,166),(50,184),(78,192),(104,184),(116,166),(111,150),(120,134),(118,114),(96,104),(68,110)],float)
DONUT=(78,166,9.0)
def catmull(P,n=24):
    out=[];m=len(P)
    for i in range(m):
        p0,p1,p2,p3=P[i-1],P[i],P[(i+1)%m],P[(i+2)%m]
        for t in np.linspace(0,1,n,endpoint=False):
            t2,t3=t*t,t*t*t;out.append(0.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t2+(-p0+3*p1-3*p2+p3)*t3))
    return np.array(out)
def resample(L,step=1.0):
    L=np.vstack([L,L[:1]]);d=np.r_[0,np.cumsum(np.linalg.norm(np.diff(L,axis=0),axis=1))];s=np.arange(0,d[-1],step)
    return np.stack([np.interp(s,d,L[:,0]),np.interp(s,d,L[:,1])],1)
LINE=resample(catmull(CTRL),1.0)
def frames(L=LINE):
    t=np.roll(L,-1,0)-np.roll(L,1,0);t/=np.linalg.norm(t,axis=1,keepdims=True);n=np.stack([t[:,1],-t[:,0]],1)   # n = right-hand normal
    t1=np.roll(t,-1,0);k=t[:,0]*t1[:,1]-t[:,1]*t1[:,0];k=np.convolve(np.r_[k[-5:],k,k[:5]],np.ones(9)/9,'same')[5:-5]
    return t,n,k
def area_sign(L=LINE): x,z=L[:,0],L[:,1];return np.sign(np.sum(x*np.roll(z,-1)-np.roll(x,-1)*z))
def inside(p,L=LINE):
    x,z=p;c=False;X,Z=L[:,0],L[:,1];Xn,Zn=np.roll(X,-1),np.roll(Z,-1)
    m=((Z>z)!=(Zn>z))&(x<(Xn-X)*(z-Z)/(Zn-Z+1e-12)+X);return bool(m.sum()%2)
def dist_line(p,L=LINE): return float(np.hypot(L[:,0]-p[0],L[:,1]-p[1]).min())
def course():
    t,n,k=frames();sg=area_sign()
    centre_dir=np.where(k[:,None]>0,np.stack([-t[:,1],t[:,0]],1),np.stack([t[:,1],-t[:,0]],1))   # left normal if turning left
    turning=np.abs(k)>0.012
    # clipping points: local curvature maxima, inner side 2.5 m
    clips=[];o=[]
    for i in range(len(LINE)):
        if abs(k[i])>1/25 and abs(k[i])==np.abs(k[max(0,i-12):i+13]).max(): clips.append(LINE[i]+centre_dir[i]*2.5);o.append(i)
    clips=np.array(clips)
    # outer zone line (painted) at 5.5 m and barrier at 7.5 m outside, only where turning; split into runs
    runs=[];cur=[]
    for i in range(len(LINE)):
        if turning[i]: cur.append(i)
        elif cur: runs.append(cur);cur=[]
    if cur:
        if runs and runs[0][0]==0: runs[0]=cur+runs[0]
        else: runs.append(cur)
    runs=[r for r in runs if len(r)>=10]
    zone=[LINE[r]-centre_dir[r]*5.5 for r in runs];wall=[LINE[r]-centre_dir[r]*7.5 for r in runs]
    return dict(line=LINE,clips=clips,clip_idx=o,zones=zone,walls=wall,entry=LINE[0],donut=DONUT)
def tent_slots(onlot,carclear,exitclear,n=18,dmin=15.0,dmax=24.0,spacing=8.5,barrier_gap=3.5):
    """greedy: candidates on a 1 m grid outside the course loop, footprint ok, 15-24 m from the line, >= barrier_gap from walls.
    Each tent opens towards the nearest drift-line point (yaw), so the ad faces the cars."""
    C=course();W=np.vstack(C['walls']);cand=[]
    for x in np.arange(6,155,1.0):
        for z in np.arange(92,222,1.0):
            d=dist_line((x,z))
            if not(dmin<=d<=dmax) or inside((x,z)): continue
            if np.hypot(W[:,0]-x,W[:,1]-z).min()<4.3+barrier_gap: continue
            if np.hypot(x-DONUT[0],z-DONUT[1])<DONUT[2]+12: continue
            if not(onlot(x,z) and carclear(x,z) and exitclear(x,z)): continue
            cand.append((d,x,z))
    cand.sort();pick=[]
    for d,x,z in cand:     # prefer closest-to-line first, then spread
        if all(np.hypot(x-a,z-b)>=spacing for a,b in pick): pick.append((x,z))
    # spread: keep the n with the best coverage (farthest-point thinning from the line-closest set)
    pick=np.array(pick)
    if len(pick)>n:
        sel=[0]
        while len(sel)<n:
            dd=np.min(np.hypot(pick[:,None,0]-pick[sel][None,:,0],pick[:,None,1]-pick[sel][None,:,1]),axis=1);sel.append(int(dd.argmax()))
        pick=pick[sel]
    # order slots along the course
    L=C['line'];idx=[int(np.hypot(L[:,0]-x,L[:,1]-z).argmin()) for x,z in pick];o=np.argsort(idx)
    out=[]
    for j,i in enumerate(o):
        x,z=pick[i];lx,lz=L[idx[i]];dx,dz=lx-x,lz-z
        yaw=float(np.arctan2(-dx,-dz))   # local front (0,0,-1) rotated by yaw -> (-sin, -cos) must point at the line
        out.append((j+1,float(x),float(z),yaw))
    return out
