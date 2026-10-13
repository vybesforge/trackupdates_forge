import struct,numpy as np,sys
def rd(d,o,fmt): return struct.unpack_from('<'+fmt,d,o),o+struct.calcsize(fmt)
def walk(p):
    d=open(p,'rb').read();o=6;(ver,),o=rd(d,o,'I')
    if ver>5:o+=4
    (nt,),o=rd(d,o,'I')
    for _ in range(nt):
        o+=4;(n,),o=rd(d,o,'I');o+=n;(sz,),o=rd(d,o,'I');o+=sz
    (nm,),o=rd(d,o,'I')
    def rs(o):
        (n,),o=rd(d,o,'I');return d[o:o+n].decode('utf8','replace'),o+n
    for _ in range(nm):
        _,o=rs(o);_,o=rs(o);o+=2
        if ver>4:o+=4
        (np_,),o=rd(d,o,'I')
        for _ in range(np_): _,o=rs(o);o+=40
        (ns,),o=rd(d,o,'I')
        for _ in range(ns): _,o=rs(o);o+=4;_,o=rs(o)
    out=[]
    def node(o,W,path):
        (cls,),o=rd(d,o,'I');name,o=rs(o);(nc,),o=rd(d,o,'I');o+=1;mo=None;M=W
        if cls==1:
            mo=o;L=np.frombuffer(d,'<f4',16,o).reshape(4,4).astype(float);M=L@W;o+=64
        elif cls in(2,3):
            o+=3;(nv,),o=rd(d,o,'I');o+=nv*(44 if cls==2 else 76);(ni,),o=rd(d,o,'I');o+=ni*2+8
            if cls==3:
                (nb,),o=rd(d,o,'I')
                for _ in range(nb): _,o=rs(o);o+=64
            else:o+=25
        out.append(dict(name=name,cls=cls,moff=mo,W=M,parentW=W,path=path))
        for _ in range(nc): o=node(o,M,path+[name])
        return o
    node(o,np.eye(4),[]);return out
if __name__=='__main__':
    for n in walk(sys.argv[1]):
        if n['name'].startswith('AC_') and n['cls']==1 and n['name'] in ('AC_PIT_0','AC_START_0','AC_HOTLAP_START_0','AC_TIME_0_L'):
            print(n['name'],n['path'],np.round(n['W'],3).tolist(),np.round(n['parentW'],3).tolist())
