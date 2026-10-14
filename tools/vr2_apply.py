"""VR2: apply material/texture changes to vf_i29_speedway.kn5 (after vr2_split_paddock.py) and vf_vegetation.kn5."""
import sys,os,struct,copy
sys.path.insert(0,os.path.dirname(__file__));import kn5mat as KM
ROOT=os.path.join(os.path.dirname(__file__),'..');S=f'{ROOT}/assets_src/vr2';Z=f'{ROOT}/vf_i29_speedway'
rd=lambda n:open(f'{S}/{n}','rb').read()
K=KM.load(f'{Z}/vf_i29_speedway.kn5');TX={t[0]:t for t in K['textures']};MM={m['name']:m for m in K['materials']}
def addtex(name,blob):
    if name in TX: TX[name][1]=blob
    else: t=[name,blob,1];K['textures'].append(t);TX[name]=t
# ground: new mask; detail B gravelroad (Gravel022) -> concrete_seams
addtex('google_mask.dds',rd('google_mask.dds'))
g=TX.pop('gravelroad.dds');g[0]='concrete_seams.dds';g[1]=rd('concrete_seams.dds');TX['concrete_seams.dds']=g
for s in MM['google']['samplers']:
    if s[2]=='gravelroad.dds': s[2]='concrete_seams.dds'
for n in ('rubber_maps','armco_maps','concrete_maps','fabric_nm','fabric_maps'): addtex(n+'.dds',rd(n+'.dds'))
if 'NULL.dds' not in TX: addtex('NULL.dds',rd('flat_nm.dds'))
WC=MM['wc']
def to_multimap(name,normal,mapsname,shader='ksPerPixelMultiMap',spec=None,exp=None):
    m=MM[name];old={p[0]:p[1] for p in m['props']};d=dict((s[0],s[2]) for s in m['samplers'])
    m['shader']=shader;m['props']=[[p,old.get(p,r)] for p,r in copy.deepcopy(WC['props'])]
    for p in ('ksAmbient','ksDiffuse','ksEmissive','ksAlphaRef'):
        if p in old: KM.setprop(m,p,struct.unpack('<f',old[p][:4])[0])
    if spec is not None: KM.setprop(m,'ksSpecular',spec)
    if exp is not None: KM.setprop(m,'ksSpecularEXP',exp)
    KM.setprop(m,'fresnelMaxLevel',0.08 if 'armco' in mapsname else 0.02)
    m['samplers']=[['txDiffuse',0,d['txDiffuse']],['txNormal',1,normal or d.get('txNormal')],['txMaps',2,mapsname],['txDetail',3,'NULL.dds']]
to_multimap('twallb02',None,'rubber_maps.dds',spec=0.12,exp=20)
for a in ('grdr01','grdr_blue'): to_multimap(a,None,'armco_maps.dds','ksPerPixelMultiMap_AT',spec=0.5,exp=60)
for c in ('Beton_01','Concrete02'): to_multimap(c,None,'concrete_maps.dds',spec=0.08,exp=15)
to_multimap('bigtent','fabric_nm.dds','fabric_maps.dds',spec=0.08,exp=12)
for tnt in ('tent_mars','tent_chipndip','tent_coke','tent_castle'): to_multimap(tnt,'fabric_nm.dds','fabric_maps.dds','ksPerPixelMultiMap_AT',spec=0.08,exp=12)
KM.save(K,f'{Z}/vf_i29_speedway.kn5')
V=KM.load(f'{Z}/vf_vegetation.kn5')
for t in V['textures']:
    if t[0] in('tree2.dds','tree3.dds'): t[1]=rd(t[0])
KM.save(V,f'{Z}/vf_vegetation.kn5');print('applied')
