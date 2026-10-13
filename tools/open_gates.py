"""Open the visual-only gates in vf_i29_speedway.kn5 (no colliders). Each closed leaf is swung 180 deg about its hinge post
(vertical axis) so it lies folded back along the fence line outside the opening, offset 8 cm from the fence plane;
positions, normals and tangents are rotated in place (vertex/index counts unchanged). Hinge posts = gate_poles_*
vertices (<=0.06 m from the leaf end). Single leaves with posts at both ends: hinge chosen so the folded leaf
lands on the fewest driveable pixels (physics meshes + ground-mask road class). Reads backup *.pre_gates."""
import sys,os,io,struct,math,numpy as np,cv2
sys.path.insert(0,os.path.dirname(__file__));import kn5patch as K,topview as T
from PIL import Image
ROOT=os.path.join(os.path.dirname(__file__),'..');SRC='/workspace/rpotm/backup/zw_rpm.kn5.pre_gates';DST=f'{ROOT}/vf_i29_speedway/vf_i29_speedway.kn5'
# (mesh, leaf end A, leaf end B, hinge or None=auto)   leaf ends in AC x,z
PLAN=[('drag_gate002',(-29.6,36.2),(-26.3,34.1),(-26.3,34.1),'pit exit -> tent lot/paddock, inner leaf (outer leaf at post (-34.3,40) is already open in v0.9, untouched)'),
      ('drag_gate002',(190.1,-107.2),(194.1,-109.5),(194.1,-109.5),'double gate in fence at (190,-107), leaf 1'),
      ('drag_gate002',(186.0,-104.9),(190.0,-107.2),(186.0,-104.9),'double gate in fence at (190,-107), leaf 2'),
      ('gate_01',(153.7,219.6),(159.0,219.5),None,'single gate across the concrete road south-east of the gravel paddock'),
      ('gate_02',(-378.8,-325.9),(-378.7,-317.8),None,'single gate at the west entrance from the county road')]
m=np.array(Image.open(io.BytesIO(K.get_tex(SRC,'google_mask.dds'))).convert('RGBA'));drv=(m[...,2]>100).astype(np.uint8)
for fn,pred in((f'{ROOT}/vf_i29_speedway/vf_i29_speedway_physical.kn5',lambda n:n[0]=='1' and 'WALL' not in n),(SRC,lambda n:n[0]=='1' and n!='1GRASS'),(f'{ROOT}/vf_i29_speedway/vf_i29_speedway_own.kn5',lambda n:n[0]=='1')):
    for n,V,I in T.meshes(fn,pred):
        P=T.px(V[:,[0,2]].astype(float)).astype(np.int32)
        for t in I: cv2.fillConvexPoly(drv,P[t],1)
def hits(a,b):
    P=T.px(np.linspace(a,b,25)[1:]).astype(int);return int(drv[P[:,1],P[:,0]].sum())
def fold(V,h,off):
    O=V.copy();O[:,0]=2*h[0]-V[:,0]+off[0];O[:,2]=2*h[1]-V[:,2]+off[1]
    for k in (3,8): O[:,k]=-V[:,k];O[:,k+2]=-V[:,k+2]
    return O
d=bytearray(open(SRC,'rb').read());_,nodes=K.scan(SRC);log=[]
loc={}
for name,o,l,cl in nodes:
    if cl==2 and name in {p[0] for p in PLAN}:
        q=o+l+8;nv,=struct.unpack_from('<I',d,q);loc[name]=(q+4,np.frombuffer(bytes(d),'<f4',nv*11,q+4).reshape(nv,11).astype(np.float64))
for name,a,b,h,why in PLAN:
    q,V=loc[name];a=np.array(a);b=np.array(b)
    sel=np.zeros(len(V),bool)
    for i in range(0,len(V),4):  # leaves are 4-vertex quads (double-sided = 2 quads)
        Q=V[i:i+4][:,[0,2]];ok=all(min(np.linalg.norm(x-a),np.linalg.norm(x-b))<0.12 for x in Q)
        if ok: sel[i:i+4]=True
    opts=[np.array(h)] if h else [a,b]
    sc=[]
    for hh in opts:
        f=a if np.allclose(hh,b) else b;nf=2*hh-f;sc.append((hits(hh,nf),hh,f,nf))
    s,hh,f,nf=min(sc,key=lambda t:t[0])
    dv=(f-hh)/np.linalg.norm(f-hh);off=np.array([-dv[1],dv[0]])*0.08
    V[sel]=fold(V[sel],hh,off)
    log.append(f'{name}: {why}. leaf {a.tolist()}-{b.tolist()} hinge {np.round(hh,1).tolist()}, folded 180 deg -> now {np.round(hh,1).tolist()}-{np.round(nf,1).tolist()}; driveable samples closed={hits(a,b)}/24 open={s}/24; verts moved={sel.sum()}')
for name,(q,V) in loc.items(): struct.pack_into(f'<{V.size}f',d,q,*V.astype(np.float32).ravel())
open(DST,'wb').write(bytes(d));print('\n'.join(log))
