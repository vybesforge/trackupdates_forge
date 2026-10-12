import sys,re,struct,hashlib,os,glob,json,collections,numpy as np
sys.path.insert(0,'project/tools');import kn5patch as K,kn5write as W
NEW=os.environ.get('PROV_NEW','project/zw_rpm/');OLD='original/zwiss_rpotm_v0.9/zw_rpm/'
def load(fn):
    d=open(fn,'rb').read();tex,nodes=K.scan(fn);mats=list(W.read_materials(fn).items())
    T={n:hashlib.md5(d[so+4:so+4+sz]).hexdigest() for n,so,sz in tex};TS={n:sz for n,so,sz in tex}
    M=[]
    for name,o,l,c in nodes:
        if c!=2:continue
        p=o+l+5;fl=d[p:p+3];q=p+3;nv,=struct.unpack_from('<I',d,q);V=d[q+4:q+4+nv*44];q2=q+4+nv*44;ni,=struct.unpack_from('<I',d,q2)
        I=d[q2+4:q2+4+ni*2];mat,=struct.unpack_from('<I',d,q2+4+ni*2);rend=d[q2+4+ni*2+32]
        P=np.frombuffer(V,'<f4').reshape(nv,11)
        M.append(dict(name=name,tris=ni//3,vis=fl[1]==1 and rend==1,phys=bool(re.match(r'^\d+[A-Z]',name)),pos=hashlib.md5(P[:,:3].tobytes()+I).hexdigest(),xz=hashlib.md5(P[:,[0,2]].tobytes()+I).hexdigest(),full=hashlib.md5(V+I).hexdigest(),mat=mats[mat][0] if mat<len(mats) else '?',samp=[t for _,_,t in mats[mat][1]['samplers']] if mat<len(mats) else [],matdef=json.dumps([mats[mat][1]['shader'],[(a,b.hex()) for a,b in mats[mat][1]['props']],mats[mat][1]['samplers']]) if mat<len(mats) else ''))
    return M,T,TS
ZW={'zw_rpm.kn5','zw_rpm_physical.kn5','zw_rpm_gp.kn5','zw_rpm_sh.kn5','zw_vegetation.kn5'}
COPIES=('vr7_person_','shortT_overlay_','1SCUT_hairpin')
cat=collections.Counter();pcat=collections.Counter();texcat=collections.defaultdict(lambda:[0,0])
seen_tex={}
for fn in sorted(glob.glob(NEW+'*.kn5')):
    b=os.path.basename(fn);M,T,TS=load(fn)
    if b in ZW:
        Mo,To,_=load(OLD+b);om=collections.defaultdict(list)
        for m in Mo: om[m['name']].append(m)
        for t in T: seen_tex[(b,t)]=('zwiss' if To.get(t)==T[t] else ('ours-replaced' if t in To else 'ours-new'),TS[t])
    for m in M:
        if b in ZW:
            o=om.get(m['name'])
            if o:
                o=o.pop(0) if o else None
            texsame=all(seen_tex[(b,t)][0]=='zwiss' for t in m['samp'] if (b,t) in seen_tex);matsame=o is not None and o['matdef']==m['matdef'] and texsame
            if o is None and re.match(r'1GRASS_\d\d(_\d\d)?$',m['name']): k='grass'   # split/refined zwiss 1GRASS
            elif o is None: k='ours'
            elif not m['vis'] and o['vis']: k='hidden'
            elif o['pos']==m['pos'] and matsame: k='unchanged'
            elif matsame: k='redrape'   # same material/textures, heights moved (incl. lidar refinement)
            elif o['pos']==m['pos']: k='retex'
            else: k='redrape+retex'
        else:
            k='copied' if m['name'].startswith(COPIES) else 'ours'
            for t in T: seen_tex.setdefault((b,t),('ours-file',TS[t]))
        if m['vis']: cat[k]+=m['tris']
        if m['phys']: pcat[k]+=m['tris']
tv=sum(cat.values());tp=sum(pcat.values());print('VISUAL',tv,{k:(v,round(100*v/tv,1)) for k,v in cat.items()});print('PHYS',tp,{k:(v,round(100*v/tp,1)) for k,v in pcat.items()})
# textures: unique by name across files
tx=collections.defaultdict(lambda:[0,0.0])
for (b,t),(k,s) in seen_tex.items(): tx[k][0]+=1;tx[k][1]+=s/1e6
print('TEX',{k:(v[0],round(v[1],1)) for k,v in tx.items()})
print([t for (b,t),(k,s) in seen_tex.items() if k=='ours-replaced'])

# ---- refined
import csv
src={}
for r in csv.DictReader(open('project/docs/assets.csv')): src[r['texture']]=(r['source'] or '')+' '+(r['license_url'] or '')+' '+(r['likely_origin'] or '')
zh={}
for f in glob.glob(OLD+'*.kn5'):
    d=open(f,'rb').read();tex,_=K.scan(f)
    for n,so,sz in tex: zh[hashlib.md5(d[so+4:so+4+sz]).hexdigest()]=n
U={}
for fn in sorted(glob.glob(NEW+'*.kn5')):
    d=open(fn,'rb').read();tex,_=K.scan(fn)
    for n,so,sz in tex:
        h=hashlib.md5(d[so+4:so+4+sz]).hexdigest()
        if h in U: continue
        if h in zh: k='zwiss'
        else:
            s=src.get(n,'').lower()
            if re.search(r'ambientcg|poly ?haven|naip|usgs|cc0 1\.0|public domain',s) and 'procedural' not in s: k='CC0/PD third-party'
            elif n in('google2.dds','google_mask.dds') or n.startswith(('vr2_tree','tree2','tree3')): k='CC0/PD third-party'
            else: k='ours (project-made)'
        U[h]=(n,sz,k)
c=collections.defaultdict(lambda:[0,0.0])
for n,sz,k in U.values(): c[k][0]+=1;c[k][1]+=sz/1e6
print('UNIQUE TEX',{k:(v[0],round(v[1],1)) for k,v in c.items()})
