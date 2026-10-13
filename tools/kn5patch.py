"""Binary-safe KN5 patcher: rename nodes, replace texture blobs. Records offsets via parser, splices."""
import struct,sys,re
def rd(f,fmt):
    s=struct.calcsize(fmt);return struct.unpack('<'+fmt,f.read(s))
def rs(f):
    o=f.tell();n,=rd(f,'I');return f.read(n).decode('utf8','replace'),o,4+n
def scan(p):
    f=open(p,'rb');assert f.read(6)==b'sc6969';ver,=rd(f,'I')
    if ver>5: rd(f,'I')
    nt,=rd(f,'I');tex=[]
    for _ in range(nt):
        rd(f,'i');name,_,_=rs(f);so=f.tell();sz,=rd(f,'I');tex.append((name,so,sz));f.seek(sz,1)
    nm,=rd(f,'I')
    for _ in range(nm):
        rs(f);rs(f);rd(f,'B');rd(f,'B')
        if ver>4: rd(f,'I')
        np_,=rd(f,'I')
        for _ in range(np_): rs(f);f.seek(40,1)
        ns,=rd(f,'I')
        for _ in range(ns): rs(f);rd(f,'I');rs(f)
    nodes=[]
    def node():
        cls,=rd(f,'I');name,o,l=rs(f);nc,=rd(f,'I');rd(f,'B');nodes.append((name,o,l,cls))
        if cls==1: f.seek(64,1)
        elif cls in(2,3):
            f.seek(3,1);nv,=rd(f,'I');f.seek(nv*(44 if cls==2 else 76),1)
            ni,=rd(f,'I');f.seek(ni*2,1);rd(f,'I');rd(f,'I')
            if cls==3:
                nb,=rd(f,'I')
                for _ in range(nb): rs(f);f.seek(64,1)
            else: f.seek(25,1)
        for _ in range(nc): node()
    node();end=f.tell();f.seek(0,2);assert end==f.tell(),('trailing',end,f.tell())
    return tex,nodes
def patch(src,dst,renames=None,texrep=None):
    tex,nodes=scan(src);data=open(src,'rb').read();edits=[]
    for name,o,l,_ in nodes:
        if renames and name in renames:
            b=renames[name].encode();edits.append((o,o+l,struct.pack('<I',len(b))+b))
    for name,so,sz in tex:
        if texrep and name in texrep:
            b=texrep[name];edits.append((so,so+4+sz,struct.pack('<I',len(b))+b))
    edits.sort();out=bytearray();pos=0
    for a,b,r in edits: out+=data[pos:a]+r;pos=b
    out+=data[pos:];open(dst,'wb').write(out);return len(edits)
def get_tex(p,name):
    tex,_=scan(p);d=open(p,'rb').read()
    for n,so,sz in tex:
        if n==name: return d[so+4:so+4+sz]
