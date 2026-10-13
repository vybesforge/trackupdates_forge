"""Short-course transition bumps in vf_i29_speedway_physical.kn5 (physics only, vertex y offsets; topology unchanged).
T1 (short only): drag strip east edge x=-214.5, z -418..-378 -> 2 cm seam lip at the edge + 4 cm hump 5 m into the infield road (x>-215.5 only, main line stays at x<-224).
T5 (shared with main): drag strip south end z=-98 -> 2 cm seam lip + 3 cm hump 8 m before it on the approach (x -229..-211)."""
import sys,os,struct,numpy as np
sys.path.insert(0,os.path.dirname(__file__));import kn5patch as K
SRC='/workspace/rpotm/backup/zw_rpm_physical.kn5.pre_bumps';DST=os.path.join(os.path.dirname(__file__),'..','vf_i29_speedway','vf_i29_speedway_physical.kn5')
def tri(s,c,hw,h): return h*np.clip(1-abs(s-c)/hw,0,None)
def cosb(s,c,L,h): return h*0.5*(1+np.cos(np.clip((s-c)/(L/2),-1,1)*np.pi))
def fade(t,a,b,w=1.5): return np.clip((t-a)/w,0,1)*np.clip((b-t)/w,0,1)
def disp(x,z):
    dy=np.zeros_like(x)
    # T1: along-coordinate s = x (eastward into infield), lateral = z
    m=(x>-215.5)&(z>-418)&(z<-378);f=fade(z,-418,-378)
    dy+=np.where(m,f*(tri(x,-214.5,0.9,0.02)+cosb(x,-209.5,4,0.04)),0)
    # T5: along-coordinate s = -z (northward onto strip), lateral = x
    m=(x>-229)&(x<-211)&(z>-104)&(z<-80);f=fade(x,-229,-211)
    dy+=np.where(m,f*(tri(z,-98,0.9,0.02)+cosb(z,-90,4,0.03)),0)
    return dy
d=bytearray(open(SRC,'rb').read());_,nodes=K.scan(SRC);tot=0
for name,o,l,c in nodes:
    if c!=2 or not name.startswith('1ROAD'): continue
    q=o+l+8;nv,=struct.unpack_from('<I',d,q);V=np.frombuffer(bytes(d),'<f4',nv*11,q+4).reshape(nv,11).copy()
    dy=disp(V[:,0],V[:,2]);n=int((dy>1e-4).sum())
    if n: V[:,1]+=dy;d[q+4:q+4+nv*44]=V.astype('<f4').tobytes();tot+=n;print(f'{name}: {n} verts raised, max {dy.max()*100:.1f} cm')
open(DST,'wb').write(bytes(d));print('total verts',tot)
