"""VR5 drag strip: high-grip launch area + rubbered-in lanes + self-made Christmas tree (zw_draglaunch.kn5, MODEL_8).
Rerunnable: reads /workspace/rpotm/backup/pre_vr5/vf_i29_speedway/vf_i29_speedway.kn5, writes vf_i29_speedway/vf_i29_speedway.kn5 + vf_i29_speedway/zw_draglaunch.kn5.
Geometry (1DRAGstrip, run toward -z, strip x -260..-242, flat y -0.10, start line / tree at z -347.5, centre x -251.25):
- 1DRAGstrip flat triangles are clipped at z -339 / -363.3 / -375.5 / -391 (Sutherland-Hodgman, full vertex interpolation,
  so UVs and heights are continuous). The pieces between -339 and -391 move to new meshes with the same material:
    1LAUNCHA_strip  z -339 .. -363.3  (behind the beams .. 60 ft)   KEY LAUNCHA  FRICTION 1.14
    1LAUNCHB_strip  z -363.3 .. -375.5 (60 .. 100 ft)               KEY LAUNCHB  FRICTION 1.08
    1LAUNCHC_strip  z -375.5 .. -391  (taper, ~150 ft)              KEY LAUNCHC  FRICTION 1.03
  then 1DRAGstrip (DRAG, 0.98) again. The small centre block (z -356) of 1DRAGstrip is untouched.
- drag_rubber_L/R: visual alpha-blended dark rubber decal per lane (3.4 m wide, z -341 .. -400, fades out), +1.5 cm.
- Christmas tree (visual only; VR6: mounted on the existing I-29 sign pole at z -368.3, Drag_tent mini head hidden): housing + per lane
  2 pre-stage, 2 stage, 3 amber, 1 green, 1 red bulb (facing the staging cars, +z). One mesh per bulb group, both lanes:
  drtree_prestage, drtree_stage, drtree_amber1..3, drtree_green, drtree_red -> animated by extension/drag_tree.lua."""
import sys,os,struct,numpy as np
sys.path.insert(0,os.path.dirname(__file__));import kn5patch as K,kn5write as W,vr5_meshlib as L
from PIL import Image
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));Z=f'{ROOT}/vf_i29_speedway';SRC='/workspace/rpotm/backup/pre_vr5/vf_i29_speedway/vf_i29_speedway.kn5'
CUTS=[-339.0,-363.3,-375.5,-391.0];BANDS=[('1LAUNCHA_strip',-339.0,-363.3),('1LAUNCHB_strip',-363.3,-375.5),('1LAUNCHC_strip',-375.5,-391.0)]
TX,TZ=-251.25,-347.5;LANES=(-255.75,-246.75);Y0=-0.10
def clip(poly,f):   # keep f(v)>=0
    out=[]
    for i in range(len(poly)):
        a,b=poly[i],poly[(i+1)%len(poly)];fa,fb=f(a),f(b)
        if fa>=0: out.append(a)
        if (fa>=0)!=(fb>=0): t=fa/(fa-fb);out.append(a+(b-a)*t)
    return out
def split_strip(d):
    for name,o,l,c in K.scan(SRC)[1]:
        if c==2 and name=='1DRAGstrip': break
    q=o+l+8;nv,=struct.unpack_from('<I',d,q);V=np.frombuffer(bytes(d[q+4:q+4+nv*44]),'<f4').reshape(nv,11).astype(np.float64)
    q2=q+4+nv*44;ni,=struct.unpack_from('<I',d,q2);I=np.frombuffer(bytes(d[q2+4:q2+4+ni*2]),'<u2').reshape(-1,3)
    keep=[];bands={b[0]:[] for b in BANDS}
    for t in I:
        tv=[V[k] for k in t]
        if not all(abs(v[1]-Y0)<1e-3 for v in tv): keep.append(tv);continue      # centre block etc.
        for lo,hi,dst in [(-1e9,CUTS[-1],'keep')]+[(b[2],b[1],b[0]) for b in BANDS]+[(CUTS[0],1e9,'keep')]:
            pc=clip(clip(tv,lambda v,lo=lo:v[2]-lo),lambda v,hi=hi:hi-v[2])
            if len(pc)<3: continue
            for j in range(1,len(pc)-1): (keep if dst=='keep' else bands[dst]).append([pc[0],pc[j],pc[j+1]])
    def pack(tris):
        Vn=np.array([v for t in tris for v in t],'<f4');In=np.arange(len(Vn)).reshape(-1,3).astype('<u2')
        g=np.cross(Vn[In[:,1],:3]-Vn[In[:,0],:3],Vn[In[:,2],:3]-Vn[In[:,0],:3])
        flat=np.abs(Vn[In[:,0],1]-Y0)<1e-3;bad=flat&(g[:,1]<0);In[bad]=In[bad][:,[0,2,1]];return Vn,In
    Vk,Ik=pack(keep);blob=struct.pack('<I',len(Vk))+Vk.tobytes()+struct.pack('<I',Ik.size)+Ik.tobytes()
    d=d[:q]+blob+d[q2+4+ni*2:];print('1DRAGstrip',len(I),'->',len(Ik),'tris')
    return d,{k:pack(v) for k,v in bands.items()}
def rubber_tex():
    H,Wd=1024,128;rng=np.random.default_rng(5);v=np.arange(H)[:,None]/H;u=np.arange(Wd)[None,:]/Wd
    a=np.zeros((H,Wd))
    for c0 in(0.27,0.73):   # two tyre tracks per lane
        a+=0.85*np.exp(-((u-c0)/0.11)**4)
    a+=0.25*np.exp(-((u-0.5)/0.45)**6);n=np.array(Image.fromarray((rng.random((128,16))*255).astype(np.uint8)).resize((Wd,H),Image.BILINEAR))/255
    fade=np.clip(1-(v-0.45)/0.55,0,1)**1.5;a=np.clip(a*(0.8+0.4*n)*fade,0,0.92)
    rgb=np.dstack([np.full((H,Wd),12),np.full((H,Wd),12),np.full((H,Wd),13)]).astype(np.uint8)
    Image.fromarray(np.dstack([rgb,(a*255).astype(np.uint8)])).save(f'{ROOT}/assets_src/drag_rubber.png')
    import build_open_textures as B;return B.write_dds(np.dstack([rgb,(a*255).astype(np.uint8)]),'DXT5',11,None)
# VR6: tree mounted on zwiss's existing pole with the small I-29 sign (drag_metal_SUB0 post x -251.67, z -368.27, top y 2.43;
# sign adds_drag_SUB1 y 0.59..1.19), housing y 1.35..3.35 on the pole's +z face (facing the staging cars), sign stays visible.
PX,PZ,HY=-251.67,-368.27,1.35
def tree_parts():
    P={'pole':[],'housing':[],'visor':[]}
    P['pole'].append(L.box((PX,2.43+0.47,PZ),(0.12,0.94,0.06)))                                  # post extension behind housing
    for y in(1.55,2.35,3.15): P['pole'].append(L.box((PX,y,PZ+0.07),(0.30,0.06,0.10)))            # mounting brackets
    hz=PZ+0.23;cy=HY+1.0
    P['housing'].append(L.box((PX,cy,hz),(0.86,2.0,0.22)));P['housing'].append(L.box((PX,HY+2.07,hz),(0.5,0.14,0.18)))
    fz=hz+0.111;bulbs={k:[] for k in('prestage','stage','amber1','amber2','amber3','green','red')}
    d=cy-2.65
    rows=[('prestage',3.48+d,0.055,2),('stage',3.30+d,0.055,2),('amber1',3.02+d,0.10,1),('amber2',2.70+d,0.10,1),('amber3',2.38+d,0.10,1),('green',2.06+d,0.10,1),('red',1.78+d,0.10,1)]
    for sx in(-1,1):        # -1: west (left) lane column, +1: east lane
        cx=PX+sx*0.21
        for k,y,r,nb in rows:
            xs=[cx-0.06,cx+0.06] if nb==2 else [cx]
            for x in xs:
                bulbs[k].append(L.disc((x,y,fz+0.004),r,(0,0,1),16))
                P['visor'].append(L.cyl((x,y,fz),r*1.15,0.07 if nb==1 else 0.04,'z',12,cap=False))
    return {k:L.merge(v) for k,v in P.items()},{k:L.merge(v) for k,v in bulbs.items()}
if __name__=='__main__':
    d=bytearray(open(SRC,'rb').read());d,bands=split_strip(bytes(d));d=bytearray(d)
    for name,o,l,c in K.scan(SRC)[1]: pass
    open(f'{Z}/vf_i29_speedway.kn5','wb').write(bytes(d))
    # hide the old mini tree head (Drag_tent) by collapsing it (scan the NEW file: offsets changed)
    d=bytearray(open(f'{Z}/vf_i29_speedway.kn5','rb').read())
    for name,o,l,c in K.scan(f'{Z}/vf_i29_speedway.kn5')[1]:
        if c==2 and name=='Drag_tent':
            q=o+l+8;nv,=struct.unpack_from('<I',d,q);V=np.frombuffer(bytes(d[q+4:q+4+nv*44]),'<f4').reshape(nv,11).copy();V[:,:3]=V[0,:3];d[q+4:q+4+nv*44]=V.tobytes();print('Drag_tent hidden')
    open(f'{Z}/vf_i29_speedway.kn5','wb').write(bytes(d))
    MS=W.read_materials(SRC);DR=MS['dragroad'];texs=[(t,K.get_tex(SRC,t)) for _,_,t in DR['samplers']]
    OWN=W.read_materials(f'{Z}/vf_i29_speedway_own.kn5');G=OWN['own_galv']
    texs+= [(t,K.get_tex(f'{Z}/vf_i29_speedway_own.kn5',t)) for _,_,t in G['samplers'] if t!='NULL.dds']+[('NULL.dds',K.get_tex(f'{Z}/vf_i29_speedway_own.kn5','NULL.dds'))]
    texs+=[('drag_rubber.dds',rubber_tex()),('drtree_black.dds',L.solid_dds((14,14,16))),('drtree_lens_y.dds',L.solid_dds((70,62,40))),
           ('drtree_lens_a.dds',L.solid_dds((80,45,8))),('drtree_lens_g.dds',L.solid_dds((10,60,20))),('drtree_lens_r.dds',L.solid_dds((70,10,10)))]
    mats=[dict(name='dragroad_launch',**{k:DR[k] for k in('shader','ab','at','dm','props','samplers')}),
          dict(name='drtree_galv',**{k:G[k] for k in('shader','ab','at','dm','props','samplers')})]
    base=dict(shader='ksPerPixel',ab=0,at=0,dm=0)
    PP=W.read_materials(SRC)
    tpl=next(m for m in PP.values() if m['shader']=='ksPerPixel')['props']
    def m(name,tex,ab=0,dm=0,**kw): mats.append(dict(name=name,shader='ksPerPixel',ab=ab,at=0,dm=dm,props=L.props(tpl,**kw),samplers=[('txDiffuse',0,tex)]))
    m('drag_rubber','drag_rubber.dds',ab=1,dm=1,ksAmbient=0.25,ksDiffuse=0.25,ksSpecular=0.05,ksSpecularEXP=10,ksEmissive=(0,0,0))
    m('drtree_black','drtree_black.dds',ksAmbient=0.4,ksDiffuse=0.4,ksSpecular=0.1,ksSpecularEXP=20,ksEmissive=(0,0,0))
    for k,t in [('prestage','y'),('stage','y'),('amber1','a'),('amber2','a'),('amber3','a'),('green','g'),('red','r')]:
        m(f'drtree_{k}',f'drtree_lens_{t}.dds',ksAmbient=0.5,ksDiffuse=0.5,ksSpecular=0.6,ksSpecularEXP=60,ksEmissive=(0,0,0))
    mi={x['name']:i for i,x in enumerate(mats)};ME=[]
    for n,(V,I) in bands.items(): ME.append(dict(name=n,mat_index=mi['dragroad_launch'],verts=V,idx=I))
    for sx in LANES:   # rubber decal per lane, v 0 at -341 -> 1 at -400
        z0,z1=-341.0,-400.0;nz=24;zz=np.linspace(z0,z1,nz+1);Vs=[]
        for i,z in enumerate(zz):
            for j,x in enumerate((sx-1.7,sx+1.7)): Vs.append([x,Y0+0.015,z,0,1,0,j,(z-z0)/(z1-z0),1,0,0])
        Vr=np.array(Vs,'<f4');Ir=np.array([[2*i,2*i+2,2*i+1] for i in range(nz)]+[[2*i+1,2*i+2,2*i+3] for i in range(nz)],'<u2');Ir=L.fix_winding(Vr,Ir)
        ME.append(dict(name=f'drag_rubber_{"L" if sx<TX else "R"}',mat_index=mi['drag_rubber'],verts=Vr,idx=Ir))
    parts,bulbs=tree_parts()
    ME.append(dict(name='drtree_pole',mat_index=mi['drtree_galv'],verts=parts['pole'][0],idx=parts['pole'][1]))
    ME.append(dict(name='drtree_housing',mat_index=mi['drtree_black'],verts=L.merge([parts['housing'],parts['visor']])[0],idx=L.merge([parts['housing'],parts['visor']])[1]))
    for k,(V,I) in bulbs.items(): ME.append(dict(name=f'drtree_{k}',mat_index=mi[f'drtree_{k}'],verts=V,idx=I))
    W.write_kn5(f'{Z}/zw_draglaunch.kn5',texs,mats,ME,rootname='zw_draglaunch');print('zw_draglaunch.kn5',[x['name'] for x in ME])
    for ini in('models_main.ini','models_short.ini'):
        p=f'{Z}/{ini}';s=open(p).read()
        if 'zw_draglaunch.kn5' not in s: open(p,'a').write('\n[MODEL_8]\nFILE=zw_draglaunch.kn5\nPOSITION=0,0,0\nROTATION=0,0,0\n')
