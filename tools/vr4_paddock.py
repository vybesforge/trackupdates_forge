"""VR4 paddock (Dylan's marked-up aerial A). Rerunnable: reads /workspace/rpotm/backup/pre_vr4/vf_i29_speedway/vf_i29_speedway.kn5.
- 36 AC_PIT_n in a tight staggered double row along the north edge of the gravel paddock lot (1GRAVEL_PADDOCK, gravel
  there is x 6..152 only, too short for 36 in one row at a sane pitch), just south of the paddock concrete / pit buildings:
  front row (PIT 0-17) z 72, x 11..143.6 every 7.8 m; back row (PIT 18-35) z 83, x 7..139.6 (offset 4 m, drives out through the
  5.6 m gaps). All face north (-z) toward the concrete; exit route north onto the gravel/concrete strip (z 50..60) then
  west to the pit-exit gate (-30,38) -> 1PITS_OUT -> track. AC_PIT_0 = front row west end (nearest the exit).
- zw_tents.kn5 rebuilt: 6 VF-style tents (scale 1.5 x/z, 1.1 y) inside the open gravel lot (red outline):
  top row z 142 at x 12 / 66 / 119, lower cluster (39,185) (60,210) (90,190).
  Middle tents: top-middle (66,142) vybesforge.com, lower-middle (60,210) drivenbycrusemob.com; other 4: YOUR AD HERE.
- vf_i29_speedway.kn5: hide the original VF tent tentm_SUB3 (40,67; on the new exit route; replaced by the top-middle copy),
  hide the containers_2 vertices inside the lot (x 6..15, z 167..227; other containers untouched) and the ambulance parked at (10..16, 67..73)
  (collapsed to a point). Visual meshes only; the gravel physics is untouched.
Base y = gravel -0.10, dummy y = gravel + 0.40."""
import sys,os,struct,numpy as np
sys.path.insert(0,os.path.dirname(__file__));import kn5tree as T,kn5patch as K,kn5write as W,vf_tents_paddock as VT
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));Z=f'{ROOT}/vf_i29_speedway'
SRC='/workspace/rpotm/backup/pre_vr4/vf_i29_speedway/vf_i29_speedway.kn5';DST=f'{Z}/vf_i29_speedway.kn5';GROUND=-0.10;LIFT=0.40
def spots(): return [(11+7.8*i,GROUND+LIFT,72.0) for i in range(18)]+[(7+7.8*i,GROUND+LIFT,83.0) for i in range(18)]
FWD=np.array([0,0,-1.0]);UP=np.array([0,1.0,0]);RIGHT=np.cross(UP,FWD)
BIG=(1.5,1.1,1.5)
TENTS=[('vftent_ad_top_w',12,142,'adhere'),('vftent_vf_top_mid',66,142,'vfad'),('vftent_ad_top_e',119,142,'adhere'),
       ('vftent_ad_low_w',39,185,'adhere'),('vftent_cm_low_mid',60,210,'cm'),('vftent_ad_low_e',90,190,'adhere')]
HIDE={'tentm_SUB3'};LOT=lambda V:(V[:,0]>-30)&(V[:,0]<160)&(V[:,2]>100)&(V[:,2]<232);AMB=('ambulances_SUB0','ambulances_SUB1','ambulances_SUB2')
def collapse(d,o,l,sel=None):
    q=o+l+8;nv,=struct.unpack_from('<I',d,q);V=np.frombuffer(bytes(d[q+4:q+4+nv*44]),'<f4').reshape(nv,11).copy()
    k=np.ones(nv,bool) if sel is None else sel(V)
    if k.any(): V[k,:3]=V[k][0,:3];d[q+4:q+4+nv*44]=V.astype('<f4').tobytes()
    return int(k.sum())
if __name__=='__main__':
    sx=1/1.36;tx={'cm':VT.art('cm',sx),'vfad':VT.art('vfad',sx),'adhere':VT.art('adhere',sx)}
    M=W.read_materials(VT.SRC)['tent_coke'];texs=[(f'tent_{k}_wide.dds',b) for k,b in tx.items()]
    for t in('fabric_nm.dds','fabric_maps.dds','NULL.dds'): texs.append((t,K.get_tex(VT.SRC,t)))
    mats=[];mi={}
    for k in tx:
        mi[k]=len(mats);mats.append(dict(name=f'vftent_{k}',shader=M['shader'],ab=M['ab'],at=M['at'],dm=M['dm'],props=M['props'],
            samplers=[(s,sl,f'tent_{k}_wide.dds' if s=='txDiffuse' else t) for s,sl,t in M['samplers']]))
    ms=[dict(name=n,mat_index=mi[k],verts=VT.place(x,z,BIG),idx=VT.TI,lod_out=0) for n,x,z,k in TENTS]
    W.write_kn5(f'{Z}/zw_tents.kn5',texs,mats,ms,rootname='zw_tents');print('zw_tents.kn5:',[m['name'] for m in ms])
    d=bytearray(open(SRC,'rb').read());S=spots();n=0
    for nd in T.walk(SRC):
        if nd['cls']==1 and nd['name'].startswith('AC_PIT_'):
            k=int(nd['name'][7:]);assert np.allclose(nd['parentW'],np.eye(4))
            Mx=np.eye(4);Mx[0,:3]=RIGHT;Mx[1,:3]=UP;Mx[2,:3]=FWD;Mx[3,:3]=S[k];d[nd['moff']:nd['moff']+64]=Mx.astype('<f4').tobytes();n+=1
    assert n==36,n
    for name,o,l,c in K.scan(SRC)[1]:
        if c!=2: continue
        if name in HIDE: print('hidden',name,collapse(d,o,l))
        if name=='containers_2': print('containers in lot',collapse(d,o,l,LOT))
        if name in AMB: print('ambulance',name,collapse(d,o,l,lambda V:(V[:,0]>9)&(V[:,0]<17)&(V[:,2]>66)&(V[:,2]<74)))
    open(DST,'wb').write(bytes(d));print('pits',n)
