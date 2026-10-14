"""v1.1: replay/TV camera set 4 'Paddock Drift' (cameras_3.ini) for both layouts, covering the paddock drift course.
AC picks the replay camera from the car's normalized position on the fast_lane spline (IN_POINT..OUT_POINT). A car in the
paddock is projected onto the nearest fast_lane point (the pit straight, 150-250 m away), so the whole 309 m drift course
maps into a narrow spline band (main ~0.847-0.858, short ~0.770-0.785). Approach: a dedicated set = copy of 'TV High'
(cameras_1.ini) with that band cut out and partitioned among 7 paddock cameras: the drift line is sampled, each sample
projected to its spline position, the band is split into bins and every bin gets the paddock camera that frames its
samples best (distance, preferring the closest; the high overview takes far bins). Existing sets are not touched.
Tradeoff: north and south parts of the loop at the same x share a spline position, so cuts are approximate (cameras
turn to follow the car, IS_FIXED=0); on-track cars in that band (pit straight) get a paddock camera in this set only.
Run: python3 tools/paddock_cams.py   -> vf_i29_speedway/{main,short}/data/cameras_3.ini (LF)"""
import os,sys,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import vr7_common as C,drift_course as DC
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));Z=f'{ROOT}/vf_i29_speedway'
G=-0.3   # approx paddock ground (lidar -0.5..0.1)
# name, position (x,y,z), aim point (x,z) on the course, mount
CAMS=[('pd_entry',(24.0,6.0,90.0),(38,110),'6 m pole SW corner, behind the entry'),
      ('pd_west',(14.0,5.5,140.0),(36,148),'5.5 m pole between tents 02/03 (west transitions)'),
      ('pd_northwest',(30.0,4.2,192.0),(46,180),'roof of tent slot06 (north-west entry of the sweeper)'),
      ('pd_north',(90.0,8.0,216.0),(80,192),'8 m pole behind tent slot09 (north sweeper)'),
      ('pd_donut',(72.0,4.2,207.0),(78,170),'roof of tent slot08 looking at the donut'),
      ('pd_east',(140.0,6.0,150.0),(116,154),'6 m pole east side (east S)'),
      ('pd_overview',(150.0,26.0,96.0),(78,160),'26 m crane/light-mast SE corner, wide overview')]
TEMPLATE=dict(SHADOW_SPLIT0=50,SHADOW_SPLIT1=200,SHADOW_SPLIT2=600,NEAR_PLANE=0.3,FAR_PLANE=5000,MIN_EXPOSURE=0.35,MAX_EXPOSURE=0.55,
              DOF_FACTOR=10,DOF_RANGE=10000,DOF_FOCUS=0,DOF_MANUAL=0,SPLINE='',SPLINE_ROTATION=0,FOV_GAMMA=1,SPLINE_ANIMATION_LENGTH=15,IS_FIXED=0)
def parse(path):
    txt=open(path,'rb').read().decode().replace('\r\n','\n');secs={};cur=None
    for ln in txt.split('\n'):
        ln=ln.strip()
        if ln.startswith('['): cur=ln[1:-1];secs[cur]={}
        elif '=' in ln and cur: k,v=ln.split('=',1);secs[cur][k]=v
    return secs
def spline(lay):
    P=C.read_ai(f'{Z}/{lay}/ai/fast_lane.ai')['P']['p'].astype(float);seg=np.linalg.norm(np.diff(np.r_[P,P[:1]],axis=0),axis=1)
    return P,np.r_[0,np.cumsum(seg)[:-1]]/seg.sum()
def proj(P,S,x,z): return float(S[np.hypot(P[:,0]-x,P[:,2]-z).argmin()])
def fov(dmin,dmax):
    f=lambda w,d:float(np.clip(np.degrees(2*np.arctan(w/2/max(d,1))),6,60))
    return round(f(14,dmax),1),round(f(26,dmin),1)
def build(lay):
    P,S=spline(lay);L=DC.LINE;sp=np.array([proj(P,S,x,z) for x,z in L]);a,b=sp.min()-0.0005,sp.max()+0.0005
    u=np.unique(sp);g=np.array_split(u,min(16,len(u)));edges=np.r_[a,[(x[-1]+y[0])/2 for x,y in zip(g[:-1],g[1:])],b];nb=len(g);assign=[]
    for i in range(nb):
        m=(sp>=edges[i])&(sp<edges[i+1]);pts=L[m] if m.any() else L
        sc=[]
        for nm,pos,aim,_ in CAMS:
            d=np.hypot(pts[:,0]-pos[0],pts[:,1]-pos[2]);sc.append(np.percentile(d,60)*(0.85 if nm=='pd_overview' else 1.0))
        assign.append(int(np.argmin(sc)))
    # merge consecutive bins with the same camera
    wins=[];
    for i,c in enumerate(assign):
        if wins and wins[-1][0]==c: wins[-1][2]=edges[i+1]
        else: wins.append([c,edges[i],edges[i+1]])
    # base: TV High with [a,b] cut out
    base=parse(f'{Z}/{lay}/data/cameras_1.ini');cams=[]
    for k,v in base.items():
        if not k.startswith('CAMERA_'): continue
        i0,i1=float(v['IN_POINT']),float(v['OUT_POINT'])
        for lo,hi in ((i0,min(i1,a)),(max(i0,b),i1)):
            if hi-lo>1e-6: w=dict(v);w['IN_POINT']=f'{lo:.6f}';w['OUT_POINT']=f'{hi:.6f}';cams.append(w)
    used=[]
    for c,lo,hi in wins:
        nm,pos,aim,mount=CAMS[c];m=(sp>=lo)&(sp<hi);pts=L[m] if m.any() else L;d=np.hypot(pts[:,0]-pos[0],pts[:,1]-pos[2]);mn,mx=fov(d.min(),d.max())
        f=np.array([aim[0]-pos[0],G+0.8-pos[1],aim[1]-pos[2]]);f/=np.linalg.norm(f);r=np.cross([0,1,0],f);r/=np.linalg.norm(r);u=np.cross(f,r)
        w=dict(NAME=f'{nm}_{len(used)}',POSITION=f'{pos[0]:.4f} ,{pos[1]:.4f} ,{pos[2]:.4f}',FORWARD=f'{f[0]:.4f} ,{f[1]:.4f} ,{f[2]:.4f}',
               UP=f'{u[0]:.4f} ,{u[1]:.4f} ,{u[2]:.4f}',MIN_FOV=f'{mn}',MAX_FOV=f'{mx}',IN_POINT=f'{lo:.6f}',OUT_POINT=f'{hi:.6f}',
               **{k:str(v) for k,v in TEMPLATE.items()});cams.append(w);used.append((nm,lo,hi,mn,mx,int(m.sum())))
    cams.sort(key=lambda w:float(w['IN_POINT']))
    out=['[HEADER]','VERSION=3',f'CAMERA_COUNT={len(cams)}','SET_NAME=Paddock Drift','']
    keys=['NAME','POSITION','FORWARD','UP','MIN_FOV','MAX_FOV','IN_POINT','OUT_POINT']+list(TEMPLATE)
    for i,w in enumerate(cams):
        out.append(f'[CAMERA_{i}]');out+=[f'{k}={w.get(k,"")}' for k in keys]+['']
    p=f'{Z}/{lay}/data/cameras_3.ini';open(p,'wb').write('\n'.join(out).encode())
    # coverage check: windows tile [0,1] without gaps/overlaps
    iv=sorted((float(w['IN_POINT']),float(w['OUT_POINT'])) for w in cams);gap=max([iv[0][0]]+[abs(iv[i+1][0]-iv[i][1]) for i in range(len(iv)-1)]+[1-iv[-1][1]])
    print(lay,f'band {a:.4f}-{b:.4f}',len(cams),'cameras, max gap/overlap %.6f'%gap);[print('  ',x) for x in used]
    return sp,used
if __name__=='__main__':
    for lay in('main','short'): build(lay)
