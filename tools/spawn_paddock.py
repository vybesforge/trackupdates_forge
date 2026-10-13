"""Move the 36 car spawns (AC_PIT_0..35) to the old tent area of the gravel paddock, behind (north, +z) of the large
green paddock building (paddock_bulds, x 84..117, z 17..46). Rerunnable: reads /workspace/rpotm/backup/pre_spawn/vf_i29_speedway.kn5.
- 4 rows x 9 cars, all facing -x (west) toward the paddock access road -> pit-exit gate (-30,38) -> 1PITS_OUT -> track.
  Row r at x = 92 + 15 r, cars every 6 m in z from 56 (odd rows staggered +3 m). Aisles 10 m between rows.
- Dummy y = ground (1GRAVEL_PADDOCK, -0.10) + 0.40. Only the 4x4 dummy matrices are rewritten (same byte size).
- AC_START_n grid and AC_HOTLAP_START_0 stay on track (unchanged).
- The visual-only ambulance parked in the pit-exit gate opening (ambulances_SUB0/1/2 vertices with x > -40) is moved
  rigidly by (+44, 0, +28) to the gravel lot west of the VF tent (x 10..16, z 67..73), clear of the exit route."""
import sys,os,struct,numpy as np
sys.path.insert(0,os.path.dirname(__file__));import kn5tree as T,kn5patch as K
SRC='/workspace/rpotm/backup/pre_spawn/vf_i29_speedway.kn5';DST=os.path.join(os.path.dirname(__file__),'..','vf_i29_speedway','vf_i29_speedway.kn5')
GROUND=-0.10;LIFT=0.40
def spots():
    out=[]
    for r in range(4):
        for i in range(9): out.append((92+15*r,GROUND+LIFT,56+6*i+(3 if r%2 else 0)))
    return out
FWD=np.array([-1.0,0,0]);UP=np.array([0,1.0,0]);RIGHT=np.cross(UP,FWD)
AMB=('ambulances_SUB0','ambulances_SUB1','ambulances_SUB2');AMB_D=np.array([44.0,0,28.0])
if __name__=='__main__':
    d=bytearray(open(SRC,'rb').read());S=spots();n=0
    for nd in T.walk(SRC):
        if nd['cls']==1 and nd['name'].startswith('AC_PIT_'):
            k=int(nd['name'][7:]);assert np.allclose(nd['parentW'],np.eye(4))
            M=np.eye(4);M[0,:3]=RIGHT;M[1,:3]=UP;M[2,:3]=FWD;M[3,:3]=S[k]
            d[nd['moff']:nd['moff']+64]=M.astype('<f4').tobytes();n+=1
    assert n==36,n
    _,nodes=K.scan(SRC);m=0
    for name,o,l,c in nodes:
        if c==2 and name in AMB:
            q=o+l+8;nv,=struct.unpack_from('<I',d,q);V=np.frombuffer(bytes(d[q+4:q+4+nv*44]),'<f4').reshape(nv,11).copy()
            k=V[:,0]>-40;V[k,:3]+=AMB_D;m+=k.sum();d[q+4:q+4+nv*44]=V.astype('<f4').tobytes()
            q2=q+4+nv*44;ni,=struct.unpack_from('<I',d,q2);sp=q2+4+ni*2+16  # bounding sphere (center, radius) -> refit
            P=V[:,:3].astype(float);ctr=(P.min(0)+P.max(0))/2;rad=float(np.linalg.norm(P-ctr,axis=1).max())*1.01
            old=struct.unpack_from('<4f',d,sp);d[sp:sp+16]=struct.pack('<4f',*ctr,rad);print(name,'sphere',np.round(old,1),'->',np.round(ctr,1),round(rad,1))
    open(DST,'wb').write(bytes(d));print('pits',n,'ambulance verts moved',m)
