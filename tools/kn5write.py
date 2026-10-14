"""Minimal KN5 (v5) writer + helpers to read template materials and hide nodes."""
import struct,numpy as np
def ws(s): b=s.encode();return struct.pack('<I',len(b))+b
def read_materials(p):
    d=open(p,'rb').read();o=6;ver,=struct.unpack_from('<I',d,o);o+=4
    if ver>5:o+=4
    nt,=struct.unpack_from('<I',d,o);o+=4
    for _ in range(nt):
        o+=4;n,=struct.unpack_from('<I',d,o);o+=4+n;sz,=struct.unpack_from('<I',d,o);o+=4+sz
    nm,=struct.unpack_from('<I',d,o);o+=4;M={}
    def rs():
        nonlocal o;n,=struct.unpack_from('<I',d,o);s=d[o+4:o+4+n].decode();o+=4+n;return s
    for _ in range(nm):
        name=rs();sh=rs();ab,at=d[o],d[o+1];o+=2;dm=0
        if ver>4: dm,=struct.unpack_from('<I',d,o);o+=4
        np_,=struct.unpack_from('<I',d,o);o+=4;props=[]
        for _ in range(np_): pn=rs();props.append((pn,d[o:o+40]));o+=40
        ns,=struct.unpack_from('<I',d,o);o+=4;smp=[]
        for _ in range(ns): s=rs();sl,=struct.unpack_from('<I',d,o);o+=4;smp.append((s,sl,rs()))
        M[name]=dict(shader=sh,ab=ab,at=at,dm=dm,props=props,samplers=smp)
    return M
def write_kn5(path,textures,materials,meshes,rootname='vf_i29_speedway_own'):
    """textures: [(name,bytes)]; materials: [dict(name,shader,ab,at,dm,props,samplers=[(slotname,slot,tex)])];
    meshes: [dict(name,mat_index,verts Nx11 float32 (AC coords),idx Mx3 uint16)]"""
    out=bytearray(b'sc6969')+struct.pack('<I',5)
    out+=struct.pack('<I',len(textures))
    for n,b in textures: out+=struct.pack('<i',1)+ws(n)+struct.pack('<I',len(b))+b
    out+=struct.pack('<I',len(materials))
    for m in materials:
        out+=ws(m['name'])+ws(m['shader'])+bytes([m['ab'],m['at']])+struct.pack('<I',m['dm'])
        out+=struct.pack('<I',len(m['props']))
        for pn,raw in m['props']: out+=ws(pn)+raw
        out+=struct.pack('<I',len(m['samplers']))
        for s,sl,t in m['samplers']: out+=ws(s)+struct.pack('<I',sl)+ws(t)
    out+=struct.pack('<I',1)+ws(rootname)+struct.pack('<I',len(meshes))+b'\x01'+np.eye(4,dtype='<f4').tobytes()
    for me in meshes:
        V=np.asarray(me['verts'],'<f4');I=np.asarray(me['idx'],'<u2');assert len(V)<65536
        c=V[:,:3].mean(0);r=float(np.linalg.norm(V[:,:3]-c,axis=1).max())
        out+=struct.pack('<I',2)+ws(me['name'])+struct.pack('<I',0)+b'\x01'+bytes(me.get('flags',(1,1,0)))
        out+=struct.pack('<I',len(V))+V.tobytes()+struct.pack('<I',I.size)+I.tobytes()
        out+=struct.pack('<II',me['mat_index'],0)+struct.pack('<ff',0,me.get('lod_out',0))+struct.pack('<3ff',*c,r)+bytes([me.get('renderable',1)])
    open(path,'wb').write(bytes(out))
def hide_nodes(src,dst,names):
    import kn5patch as k
    tex,nodes=k.scan(src);d=bytearray(open(src,'rb').read());n=0
    for name,o,l,c in nodes:
        if c==2 and name in names:
            p=o+l+4+1;d[p]=0;d[p+1]=0  # castShadows, isVisible
            nv,=struct.unpack_from('<I',d,p+3);q=p+3+4+nv*44;ni,=struct.unpack_from('<I',d,q);q+=4+ni*2+8+4+4+16;d[q]=0;n+=1  # isRenderable
    open(dst,'wb').write(bytes(d));return n
