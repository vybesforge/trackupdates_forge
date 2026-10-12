import sys,os,json,csv,math,numpy as np
sys.path.insert(0,os.path.dirname(__file__));import kn5write as W,kn5patch as K
ROOT=os.path.join(os.path.dirname(__file__),'..');A=f'{ROOT}/assets_src';Z=f'{ROOT}/zw_rpm'
T=W.read_materials('/workspace/rpotm/backup/zw_rpm.kn5.pre_textures_open')
tpl={'ksPerPixel':T['roof_red'],'ksPerPixelNM':T['Beton_01'],'ksPerPixelMultiMap':T['wc']}
MM='ksPerPixelMultiMap'
def mm(d,n,mp): return (MM,[('txDiffuse',0,d),('txNormal',1,n),('txMaps',2,mp),('txDetail',3,'NULL.dds')])
# VR2: own materials moved to ksPerPixelMultiMap (diffuse + normal + maps R=spec G=gloss B=reflection)
MATS={'own_tower_paint':mm('own_tower_paint.dds','own_tower_paint_nm.dds','own_tower_paint_maps.dds'),
 'own_tower_glass':mm('own_tower_glass.dds','flat_nm.dds','own_glass_maps.dds'),'own_galv':mm('own_galv.dds','own_galv_nm.dds','own_galv_maps.dds'),
 'own_alu':mm('own_alu.dds','own_alu_nm.dds','own_alu_maps.dds'),'own_hut_white':mm('own_hut_white.dds','own_hut_white_nm.dds','own_hut_white_maps.dds'),
 'own_awning':mm('own_awning.dds','own_awning_nm.dds','own_awning_maps.dds'),'own_boards':('ksPerPixel',[('txDiffuse',0,'own_boards.dds')]),'own_flag':('ksPerPixel',[('txDiffuse',0,'own_flag.dds')]),
 'own_gravel':mm('own_gravel.dds','own_gravel_nm.dds','own_gravel_maps.dds')}
SPEC={'own_tower_glass':(0.9,120),'own_galv':(0.5,40),'own_alu':(0.6,50),'own_gravel':(0.05,8),'own_tower_paint':(0.15,20),'own_hut_white':(0.15,20),'own_awning':(0.05,10)}
import struct
def setp(props,name,v): return [(p,struct.pack('<f',v)+r[4:]) if p==name else (p,r) for p,r in props]
mats=[];mi={}
for n,(sh,smp) in MATS.items():
    t=tpl[sh];pr=t['props']
    if sh==MM:
        pr=setp(setp(pr,'ksAmbient',0.3),'ksDiffuse',0.3)
        if n in SPEC: pr=setp(setp(pr,'ksSpecular',SPEC[n][0]),'ksSpecularEXP',SPEC[n][1])
    mi[n]=len(mats);mats.append(dict(name=n,shader=sh,ab=t['ab'],at=t['at'],dm=t['dm'],props=pr,samplers=smp))
texnames=sorted({s[2] for _,(_,smp) in MATS.items() for s in smp})
def tpath(t):
    for d in (f'{A}/vr2',f'{A}/textures'):
        if os.path.exists(f'{d}/{t}'): return f'{d}/{t}'
    return f'{A}/vr2/flat_nm.dds' if t=='NULL.dds' else None
texs=[(t,open(tpath(t),'rb').read()) for t in texnames]
def conv(V):  # blender (x,y,z) -> AC (x,z,-y); uv v flip
    V=np.array(V,np.float32);O=V.copy()
    for a,b in((0,0),(3,3),(8,8)): O[:,a]=V[:,b];O[:,a+1]=V[:,b+2];O[:,a+2]=-V[:,b+1]
    O[:,7]=1-V[:,7];return O
def place(V,x,y,z,yaw):
    c,s=math.cos(yaw),math.sin(yaw);R=np.array([[c,0,s],[0,1,0],[-s,0,c]],np.float32);O=V.copy()
    O[:,0:3]=V[:,0:3]@R.T+[x,y,z];O[:,3:6]=V[:,3:6]@R.T;O[:,8:11]=V[:,8:11]@R.T;return O
rows=list(csv.DictReader(open(f'{ROOT}/docs/own_models_placement.csv')))
meshes=[]
for r in rows:
    js=json.load(open(f"{A}/{r['model']}/{r['model']}_mesh.json"))
    for part in js:
        if r['model']=='brakeboards' and not part['name'].startswith(r['instance']+'_'): continue
        V=place(conv(part['verts']),float(r['x']),float(r['y']),float(r['z']),math.radians(float(r['yaw_deg'])));I=np.array(part['tris'])
        if part['name']=='flag_cloth':  # double-sided
            B=V.copy();B[:,3:6]*=-1;I=np.vstack([I,I[:,::-1]+len(V)]);V=np.vstack([V,B])
        lod=1500 if r['model'] in('tower','grandstand','flagpole') else 600
        meshes.append(dict(name=f"own_{r['instance']}_{part['name']}",mat_index=mi[part['material']],verts=V,idx=I,lod_out=lod))
# VR2: gravel paddock surface (split from 1CONCRETE_001, see tools/vr2_split_paddock.py); physics KEY=GRAVEL
import numpy as _np
_P=_np.load(f'{A}/paddock/paddock_mesh.npz');meshes.append(dict(name='1GRAVEL_PADDOCK',mat_index=mi['own_gravel'],verts=_P['verts'],idx=_P['idx'],lod_out=0))
W.write_kn5(f'{Z}/zw_rpm_own.kn5',texs,mats,meshes)
tex,nodes=K.scan(f'{Z}/zw_rpm_own.kn5');print('own kn5: textures',len(tex),'meshes',sum(1 for n in nodes if n[3]==2),'tris',sum(len(m['idx']) for m in meshes),'bytes',os.path.getsize(f'{Z}/zw_rpm_own.kn5'))
