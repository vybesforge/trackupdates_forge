"""NOTE: apply ONCE to the pre_vr3 files (TREEWALL move is not idempotent). VR3 edits on the CURRENT vf_i29_speedway.kn5 / zw_vegetation.kn5 (backups: /workspace/rpotm/backup/zw_rpm.pre_vr3/):
- hide paddock tents tentm_SUB0/5/6 (keep Vybes Forge tentm_SUB3 + big pit tent)          [item 6]
- hide both wrecker/lifter trucks (liftertrucks_SUB1: staging/tower and pit-exit road)       [item 8]
- FENCE_001: cut openings at drag exits A/B/C (A widened) so the west fence no longer crosses them [item 5]
- TREEWALL_001: move the north tree billboard band (in front of the fuel stations) 330 m further north, on terrain [item 10]
Hidden = degenerate triangles (node, material, counts unchanged). All visual only; none of these have physics meshes."""
import sys,os,struct,numpy as np
sys.path.insert(0,os.path.dirname(__file__));sys.path.insert(0,os.path.join(os.path.dirname(__file__),'north_ext'))
import kn5patch as K
ROOT=os.path.join(os.path.dirname(__file__),'..');Z=f'{ROOT}/vf_i29_speedway'
def clip_tri(tv,keep):
    out=tv
    for f_ in keep:
        res=[];n_=len(out)
        for i in range(n_):
            a,b=out[i],out[(i+1)%n_];fa,fb=f_(a),f_(b)
            if fa>=0: res.append(a)
            if (fa>=0)!=(fb>=0): t=fa/(fa-fb);res.append(a+(b-a)*t)
        out=res
        if not out: break
    return out
def edit(path,fn):
    d=open(path,'rb').read();_,nodes=K.scan(path);edits=[]
    for name,o,l,c in nodes:
        if c!=2: continue
        q=o+l+8;nv,=struct.unpack_from('<I',d,q);V=np.frombuffer(d,'<f4',nv*11,q+4).reshape(nv,11).astype(np.float64)
        q2=q+4+nv*44;ni,=struct.unpack_from('<I',d,q2);I=np.frombuffer(d,'<u2',ni,q2+4).reshape(-1,3).astype(np.int64)
        r=fn(name,V,I)
        if r is None: continue
        V2,I2=r;V2=np.asarray(V2,'<f4');I2=np.asarray(I2,'<u2');assert len(V2)<65536
        edits.append((q,q2+4+ni*2,struct.pack('<I',len(V2))+V2.tobytes()+struct.pack('<I',I2.size)+I2.tobytes()))
    edits.sort();out=bytearray();pos=0
    for a,b,r in edits: out+=d[pos:a]+r;pos=b
    out+=d[pos:];open(path,'wb').write(bytes(out));return len(edits)
HIDE={'tentm_SUB0','tentm_SUB5','tentm_SUB6','liftertrucks_SUB1'}
GAPS=[(-642.0,-614.0),(-808.0,-794.0),(-960.0,-944.0)]
def f_rpm(name,V,I):
    if name in HIDE: print('hidden',name,len(I),'tris');I=I.copy();I[:,1]=I[:,0];I[:,2]=I[:,0];return V,I
    if name=='FENCE_001':
        NV=list(V);NI=[];cut=0
        for t in I:
            tv=V[t];zmin,zmax=tv[:,2].min(),tv[:,2].max()
            if tv[:,0].max()>-262 or not any(zmax>g0 and zmin<g1 for g0,g1 in GAPS): NI.append(list(t));continue
            cut+=1;pieces=[[x for x in tv]]
            for g0,g1 in GAPS:
                nxt=[]
                for pc in pieces:
                    for keep in([lambda v,g0=g0:g0-v[2]],[lambda v,g1=g1:v[2]-g1]):
                        q_=clip_tri(pc,keep)
                        if len(q_)>=3: nxt.append(q_)
                pieces=nxt
            for poly in pieces:
                b=len(NV);NV+=poly
                for j in range(1,len(poly)-1): NI.append([b,b+j,b+j+1])
        print('FENCE_001 openings at drag exits:',cut,'tris clipped');return np.array(NV),np.array(NI)
print('vf_i29_speedway.kn5 nodes edited:',edit(f'{Z}/vf_i29_speedway.kn5',f_rpm))
import geo
def f_veg(name,V,I):
    if name!='TREEWALL_001': return None
    V=V.copy();moved=set()
    C=V[I][:,:,[0,2]].mean(1);sel=(C[:,1]<-2450)&(C[:,0]>-1150)&(C[:,0]<450)
    vs=np.unique(I[sel]);V[vs,2]-=330.0
    nat,_=geo.natural(V[vs][:,[0,2]]);V[vs,1]+=np.maximum(nat,-0.1)+0.1
    print('TREEWALL_001: moved',sel.sum(),'tris /',len(vs),'verts 330 m north (now z',V[vs,2].min().round(),'..',V[vs,2].max().round(),')');return V,I
print('zw_vegetation.kn5 nodes edited:',edit(f'{Z}/zw_vegetation.kn5',f_veg))
# (appended) big tents: keep only the one nearest the pit lane (x 51..70, z 63..88), hide the other three
def f_big(name,V,I):
    if name!='bigtents': return None
    C=V[I][:,:,[0,2]].mean(1);k=~((C[:,0]>50)&(C[:,0]<71)&(C[:,1]>62)&(C[:,1]<89));I=I.copy();I[k,1]=I[k,0];I[k,2]=I[k,0]
    print('bigtents: hid',int(k.sum()),'tris (3 tents), kept',int((~k).sum()));return V,I
if __name__=='__main__' and '--bigtents-only' in sys.argv: pass
print('vf_i29_speedway.kn5 bigtents:',edit(f'{Z}/vf_i29_speedway.kn5',f_big))
