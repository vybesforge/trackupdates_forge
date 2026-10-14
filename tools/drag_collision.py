"""roads-concrete: invisible collision proxies (1WALL_DRAG_*) for EXISTING objects around the drag strip -> vf_dragcol.kn5.
No new visible objects. Each proxy is a box around one connected part of an object, from the ground up to the part's
top (max 12 m); fences become thin boxes along each panel. Parts are skipped when they are overhead (bottom > 2.2 m),
tiny (< 0.3 m tall) or touch a keep-out zone: drag strip + staging/launch lanes, the start apron cars use to turn into
staging, the return road + connectors, the circuit (1ROAD) and the pit-out. Run: python3 tools/drag_collision.py"""
import os,sys,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import kn5write as W,vr5_meshlib as ML,vismeshes as VM,physraster as PR
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));Z=f'{ROOT}/vf_i29_speedway'
B=(-340,-200,-1000,-280)
# (kn5, mesh-name prefix, label, mode)  mode: box = box per connected part, fence = thin box per vertical panel
OBJ=[('vf_i29_speedway_own','own_tower_tower_','timing tower','box'),('vf_i29_speedway','tower_','timing tower (old shell)','box'),
     ('vf_i29_speedway_own','own_gs_','grandstand','box'),('vf_i29_speedway','Grandstand_001','grandstand (old shell)','box'),
     ('vf_i29_speedway','drag_catering','catering hut','box'),('vf_i29_speedway','drag_kiosk','kiosk','box'),
     ('vf_i29_speedway','tents001','staging tent','box'),('vf_i29_speedway','containers_2','container','box'),
     ('vf_i29_speedway','wc001','toilet block','box'),('vf_i29_speedway','drag_poles_SUB0','light pole','box'),
     ('vf_i29_speedway','drag_light_beton','light pole base','box'),('vf_i29_speedway','drag_metal_SUB0','end gantry leg','box'),
     ('vf_i29_speedway','drag_boards_SUB0','podium / board','box'),('vf_i29_speedway','whitepole_001','flag pole','box'),
     ('vf_i29_speedway_own','own_flag_flag_pole','flag pole','box'),('vf_i29_speedway','sign_001','brake/distance sign','box'),
     ('vf_i29_speedway','barrel002','barrel','box'),('vf_i29_speedway','FENCE_001','fence','fence'),('vf_i29_speedway','FENCE_outside','fence','fence'),
     ('vf_i29_speedway','Grandstand_001_SUB3','grandstand fence','fence')]
KEEP=[(-263.5,-240.5,-962,-333,'drag strip + staging lanes'),(-340,-226,-332.5,-311.5,'start apron'),(-306.5,-289.5,-960,-544,'return road'),
      (-296,-260,-636,-621,'connector A'),(-296,-262,-808,-794,'connector B'),(-296,-264,-959,-946,'connector C'),(-251,-232,-741,-730,'connector E')]
def ground():
    files=['vf_i29_speedway.kn5','vf_i29_speedway_physical.kn5','vf_dragexit.kn5','vf_draglaunch.kn5','vf_ext.kn5']
    M=PR.physmeshes(files,B);xs,zs,H,KEY,UP,names=PR.raster(M,B,0.5)
    road=np.isin(KEY,[i for i,nm in enumerate(names) if nm.startswith(('1ROAD','1PITS','1SCUT'))])
    def g(x,z):
        i=int(np.clip((x-xs[0])/0.5,0,len(xs)-1));j=int(np.clip((z-zs[0])/0.5,0,len(zs)-1));return H[j,i]
    def onroad(x0,x1,z0,z1,m=1.5):
        i0,i1=[int(np.clip((v-xs[0])/0.5,0,len(xs)-1)) for v in (x0-m,x1+m)];j0,j1=[int(np.clip((v-zs[0])/0.5,0,len(zs)-1)) for v in (z0-m,z1+m)]
        return road[j0:j1+1,i0:i1+1].any()
    return g,onroad
def parts(V,I):
    """connected components by shared (welded) vertex positions"""
    key=np.round(V[:,:3]*50).astype(np.int64);_,inv=np.unique(key,axis=0,return_inverse=True);inv=inv.ravel()
    par=np.arange(inv.max()+1)
    def f(a):
        while par[a]!=a: par[a]=par[par[a]];a=par[a]
        return a
    for t in I:
        a,b,c=f(inv[t[0]]),f(inv[t[1]]),f(inv[t[2]]);par[b]=a;par[f(c)]=a
    r=np.array([f(x) for x in inv]);return [np.nonzero(r==u)[0] for u in np.unique(r)]
def blocked(x0,x1,z0,z1,onroad):
    for a,b,c,d,nm in KEEP:
        if x1>a and x0<b and z1>c and z0<d: return nm
    return 'circuit/pits' if onroad(x0,x1,z0,z1) else None
def main():
    g,onroad=ground();out=[];report=[];skipped=[];cache={};cand={}
    for f,pre,label,mode in OBJ:
        if f not in cache: cache[f]=VM.vismeshes(f'{Z}/{f}.kn5',B)
        for m in cache[f]:
            if not m['name'].startswith(pre): continue
            V=m['V'].astype(float);I=m['I'].astype(int)
            if mode=='fence':
                nrm=np.cross(V[I[:,1],:3]-V[I[:,0],:3],V[I[:,2],:3]-V[I[:,0],:3]);vert=np.abs(nrm[:,1])<0.2*np.linalg.norm(nrm,axis=1)+1e-9
                segs=set()
                for t in I[vert]:
                    P=V[t,:3];lo=P[np.argsort(P[:,1])[:2]];a,b=lo[:,[0,2]];L=np.linalg.norm(b-a)
                    if L<0.3 or not (B[0]<a[0]<B[1] and B[2]<a[1]<B[3]): continue
                    segs.add((tuple(np.round(a,1)),tuple(np.round(b,1)),round(float(P[:,1].max()),1)))
                for a,b,top in segs:
                    a,b=np.array(a),np.array(b);c=(a+b)/2;gy=g(*c);h=top-gy
                    x0,x1,z0,z1=min(a[0],b[0]),max(a[0],b[0]),min(a[1],b[1]),max(a[1],b[1]);why=blocked(x0-0.1,x1+0.1,z0-0.1,z1+0.1,onroad)
                    if h<0.3 or why: skipped.append((label,m['name'],why or 'too low'));continue
                    L=np.linalg.norm(b-a);rot=np.arctan2(b[0]-a[0],b[1]-a[1]);out.append((label,ML.box((c[0],gy-0.2+(h+0.2)/2,c[1]),(0.15,h+0.2,L),rot)))
                continue
            for ix in parts(V,I):
                P=V[ix,:3];x0,x1,z0,z1=P[:,0].min(),P[:,0].max(),P[:,2].min(),P[:,2].max()
                if not (x1>B[0] and x0<B[1] and z1>B[2] and z0<B[3]): continue
                gy=min(g(x0,z0),g(x1,z1),g((x0+x1)/2,(z0+z1)/2));bot,top=P[:,1].min(),min(P[:,1].max(),gy+12)
                if bot>gy+2.2: skipped.append((label,m['name'],'overhead'));continue
                if top-gy<0.3: skipped.append((label,m['name'],'too low'));continue
                cand.setdefault(label,[]).append([x0,x1,z0,z1,gy,top,m['name']])
    # cluster parts of the same object type whose footprints touch (gap < 0.6 m) -> one box per building / stand / pole
    for label,L in cand.items():
        L=[list(x) for x in L];merged=True
        while merged:
            merged=False
            for i in range(len(L)):
                for j in range(i+1,len(L)):
                    a_,b_=L[i],L[j]
                    if a_[0]-0.6<b_[1] and b_[0]-0.6<a_[1] and a_[2]-0.6<b_[3] and b_[2]-0.6<a_[3]:
                        L[i]=[min(a_[0],b_[0]),max(a_[1],b_[1]),min(a_[2],b_[2]),max(a_[3],b_[3]),min(a_[4],b_[4]),max(a_[5],b_[5]),a_[6]];del L[j];merged=True;break
                if merged: break
        for x0,x1,z0,z1,gy,top,nm in L:
            if (x1-x0)*(z1-z0)>2500: skipped.append((label,nm,'too big for one box'));continue
            why=blocked(x0,x1,z0,z1,onroad)
            if why: skipped.append((label,nm,why));continue
            out.append((label,ML.box(((x0+x1)/2,(gy-0.2+top)/2,(z0+z1)/2),(max(x1-x0,0.2)+0.05,top-gy+0.2,max(z1-z0,0.2)+0.05))))
            report.append((label,nm,round(x0,1),round(x1,1),round(z0,1),round(z1,1),round(top-gy,1)))
    # merge per label into meshes (<65k verts)
    meshes=[];cnt={}
    for label in dict.fromkeys(l for l,_ in out):
        bx=[b for l,b in out if l==label];cnt[label]=len(bx)
        for k in range(0,len(bx),2000):
            V,I=ML.merge(bx[k:k+2000]);nm='1WALL_DRAG_'+''.join(ch if ch.isalnum() else '_' for ch in label.upper()).strip('_')+(f'_{k//2000}' if len(bx)>2000 else '')
            meshes.append(dict(name=nm,mat_index=0,verts=V,idx=I,lod_out=0,flags=(0,0,0),renderable=0))
    texs=[('vfcol_null.dds',ML.solid_dds((128,128,128)))]
    mats=[dict(name='vfcol_invisible',shader='ksPerPixel',ab=0,at=0,dm=0,props=W.read_materials(f'{Z}/vf_tents.kn5')['vftent_frame_black']['props'],samplers=[('txDiffuse',0,'vfcol_null.dds')])]
    W.write_kn5(f'{Z}/vf_dragcol.kn5',texs,mats,meshes,rootname='vf_dragcol')
    print('vf_dragcol.kn5:',len(meshes),'physics meshes,',sum(cnt.values()),'proxies');[print(f'  {k}: {v}') for k,v in cnt.items()]
    from collections import Counter;print('skipped parts:',dict(Counter((l,w) for l,_,w in skipped)))
    import json;json.dump(report,open(f'{ROOT}/tools/data/drag_collision_list.json','w'),indent=0)
    for r in report: print('   ',r)
    return cnt,skipped
if __name__=='__main__': main()
