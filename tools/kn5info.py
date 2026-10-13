import struct,sys,re,collections
def rd(f,fmt):
    s=struct.calcsize(fmt);return struct.unpack('<'+fmt,f.read(s))
def rs(f):
    n,=rd(f,'I');return f.read(n).decode('utf8','replace')
def parse(p):
    f=open(p,'rb');assert f.read(6)==b'sc6969';ver,=rd(f,'I')
    if ver>5: rd(f,'I')
    nt,=rd(f,'I');tex=[]
    for _ in range(nt):
        rd(f,'i');name=rs(f);sz,=rd(f,'I');f.seek(sz,1);tex.append((name,sz))
    nm,=rd(f,'I');mats=[]
    for _ in range(nm):
        name=rs(f);sh=rs(f);rd(f,'B');rd(f,'B');
        if ver>4: rd(f,'I')
        np_,=rd(f,'I')
        for _ in range(np_): rs(f);rd(f,'f');f.seek(36,1)
        ns,=rd(f,'I')
        for _ in range(ns): rs(f);rd(f,'I');rs(f)
        mats.append((name,sh))
    nodes=[];ymin=[1e9];ymax=[-1e9]
    def node(depth):
        cls,=rd(f,'I');name=rs(f);nc,=rd(f,'I');rd(f,'B')
        info={'cls':cls,'name':name}
        if cls==1: f.seek(64,1)
        elif cls in(2,3):
            f.seek(3,1);nv,=rd(f,'I')
            if cls==2:
                data=f.read(nv*44)
                for i in range(0,len(data),44*max(1,nv//200)):
                    y=struct.unpack_from('<f',data,i+4)[0];ymin[0]=min(ymin[0],y);ymax[0]=max(ymax[0],y)
            else:
                f.seek(nv*76,1)
            ni,=rd(f,'I');f.seek(ni*2,1);rd(f,'I');rd(f,'I')
            if cls==3:
                nb,=rd(f,'I')
                for _ in range(nb): rs(f);f.seek(64,1)
                # (skinned rarely in tracks)
            else:
                f.seek(4*2+12+4+1,1)
            info['nv']=nv
        nodes.append(info)
        for _ in range(nc): node(depth+1)
    node(0)
    return ver,tex,mats,nodes,(ymin[0],ymax[0])
for p in sys.argv[1:]:
    try: ver,tex,mats,nodes,yr=parse(p)
    except Exception as e: print(p,'PARSE FAIL',e);continue
    names=[n['name'] for n in nodes]
    pit=sorted(n for n in names if re.match(r'AC_PIT_\d+$',n)); st=[n for n in names if re.match(r'AC_START_\d+$',n)]
    acx=sorted(set(re.sub(r'\d+$','',n) for n in names if n.startswith('AC_')))
    phys=[n for n in names if re.match(r'^\d+[A-Z]+',n)]
    pref=collections.Counter(re.match(r'^\d+([A-Z]+)',n).group(1) for n in phys)
    print(f'== {p}\n ver={ver} textures={len(tex)} ({sum(s for _,s in tex)/1e6:.1f}MB) materials={len(mats)} nodes={len(nodes)} meshes={sum(1 for n in nodes if n["cls"]==2)} verts={sum(n.get("nv",0) for n in nodes)}')
    print(f' Y range (sampled) {yr[0]:.2f}..{yr[1]:.2f}  pits={len(pit)} starts={len(st)} AC_ nodes={acx}')
    print(f' physics-surface meshes by key={dict(pref)}')
    print(' sample names:',names[:40])
