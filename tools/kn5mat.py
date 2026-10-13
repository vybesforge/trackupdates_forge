"""Rewrite the texture + material sections of a kn5, copying the node tree byte-for-byte.
load(p)->dict(head,textures=[[name,bytes]],materials=[dict],nodes=bytes); save(K,p)"""
import struct
def ws(s): b=s.encode();return struct.pack('<I',len(b))+b
def load(p):
    d=open(p,'rb').read();o=6;ver,=struct.unpack_from('<I',d,o);o+=4
    if ver>5:o+=4
    head=d[:o];nt,=struct.unpack_from('<I',d,o);o+=4;T=[]
    def rs():
        nonlocal o;n,=struct.unpack_from('<I',d,o);s=d[o+4:o+4+n].decode('latin1');o+=4+n;return s
    for _ in range(nt):
        act,=struct.unpack_from('<i',d,o);o+=4;n=rs();sz,=struct.unpack_from('<I',d,o);T.append([n,d[o+4:o+4+sz],act]);o+=4+sz
    nm,=struct.unpack_from('<I',d,o);o+=4;M=[]
    for _ in range(nm):
        name=rs();sh=rs();ab,at=d[o],d[o+1];o+=2;dm=None
        if ver>4: dm,=struct.unpack_from('<I',d,o);o+=4
        npp,=struct.unpack_from('<I',d,o);o+=4;props=[]
        for _ in range(npp): pn=rs();props.append([pn,d[o:o+40]]);o+=40
        ns,=struct.unpack_from('<I',d,o);o+=4;smp=[]
        for _ in range(ns): s=rs();sl,=struct.unpack_from('<I',d,o);o+=4;smp.append([s,sl,rs()])
        M.append(dict(name=name,shader=sh,ab=ab,at=at,dm=dm,props=props,samplers=smp))
    return dict(head=head,ver=ver,textures=T,materials=M,nodes=d[o:])
def save(K,p):
    out=bytearray(K['head'])+struct.pack('<I',len(K['textures']))
    for t in K['textures']: out+=struct.pack('<i',t[2] if len(t)>2 else 1)+ws(t[0])+struct.pack('<I',len(t[1]))+t[1]
    out+=struct.pack('<I',len(K['materials']))
    for m in K['materials']:
        out+=ws(m['name'])+ws(m['shader'])+bytes([m['ab'],m['at']])
        if K['ver']>4: out+=struct.pack('<I',m['dm'])
        out+=struct.pack('<I',len(m['props']))
        for pn,raw in m['props']: out+=ws(pn)+raw
        out+=struct.pack('<I',len(m['samplers']))
        for s,sl,t in m['samplers']: out+=ws(s)+struct.pack('<I',sl)+ws(t)
    out+=K['nodes'];open(p,'wb').write(bytes(out))
def prop(v): return struct.pack('<f',v)+bytes(36)
def setprop(m,name,v):
    for pr in m['props']:
        if pr[0]==name: pr[1]=prop(v)+b'' if False else struct.pack('<f',v)+pr[1][4:];return
    m['props'].append([name,prop(v)])
