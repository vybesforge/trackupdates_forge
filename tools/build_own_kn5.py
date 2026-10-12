import sys,os,json,csv,math,numpy as np
sys.path.insert(0,os.path.dirname(__file__));import kn5write as W,kn5patch as K
ROOT=os.path.join(os.path.dirname(__file__),'..');A=f'{ROOT}/assets_src';Z=f'{ROOT}/zw_rpm'
T=W.read_materials('/workspace/rpotm/backup/zw_rpm.kn5.pre_textures_open')
tpl={'ksPerPixel':T['roof_red'],'ksPerPixelNM':T['Beton_01']}
MATS={'own_tower_paint':('ksPerPixelNM',[('txDiffuse',0,'own_tower_paint.dds'),('txNormal',1,'own_tower_paint_nm.dds')]),
 'own_tower_glass':('ksPerPixel',[('txDiffuse',0,'own_tower_glass.dds')]),'own_galv':('ksPerPixel',[('txDiffuse',0,'own_galv.dds')]),
 'own_alu':('ksPerPixel',[('txDiffuse',0,'own_alu.dds')]),'own_hut_white':('ksPerPixel',[('txDiffuse',0,'own_hut_white.dds')]),
 'own_awning':('ksPerPixel',[('txDiffuse',0,'own_awning.dds')]),'own_boards':('ksPerPixel',[('txDiffuse',0,'own_boards.dds')]),'own_flag':('ksPerPixel',[('txDiffuse',0,'own_flag.dds')])}
mats=[];mi={}
for n,(sh,smp) in MATS.items():
    t=tpl[sh];mi[n]=len(mats);mats.append(dict(name=n,shader=sh,ab=t['ab'],at=t['at'],dm=t['dm'],props=t['props'],samplers=smp))
texnames=sorted({s[2] for _,(_,smp) in MATS.items() for s in smp})
texs=[(t,open(f'{A}/textures/{t}','rb').read()) for t in texnames]
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
W.write_kn5(f'{Z}/zw_rpm_own.kn5',texs,mats,meshes)
tex,nodes=K.scan(f'{Z}/zw_rpm_own.kn5');print('own kn5: textures',len(tex),'meshes',sum(1 for n in nodes if n[3]==2),'tris',sum(len(m['idx']) for m in meshes),'bytes',os.path.getsize(f'{Z}/zw_rpm_own.kn5'))
