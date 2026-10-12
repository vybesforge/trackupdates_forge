"""VR4 preview export (generalised tents2_export): python tools/vr4_preview_export.py X0 X1 Z0 Z1 OUTDIR file1.kn5,file2.kn5"""
import sys,io,os,struct,numpy as np;sys.path.insert(0,'tools');import kn5patch as K,kn5mat as KM
from PIL import Image
X0,X1,Z0,Z1=[float(v) for v in sys.argv[1:5]];O=sys.argv[5];FILES=sys.argv[6].split(',');os.makedirs(O,exist_ok=True)
def meshes(path):
    d=open(path,'rb').read();_,nodes=K.scan(path)
    mats=KM.load(path)['materials'];mi=[]
    # material index per mesh: read after idx
    for name,o,l,c in nodes:
        if c!=2: continue
        q=o+l+8;nv,=struct.unpack_from('<I',d,q);V=np.frombuffer(d,'<f4',nv*11,q+4).reshape(nv,11)
        q2=q+4+nv*44;ni,=struct.unpack_from('<I',d,q2);I=np.frombuffer(d,'<u2',ni,q2+4).reshape(-1,3);m,=struct.unpack_from('<I',d,q2+4+ni*2)
        yield name,V,I,mats[m]
k=0;texdone={}
for f in FILES:
    p='zw_rpm/'+f
    for name,V,I,M in meshes(p):
        if name[0].isdigit() and not name.startswith(('1GRASS','1GRAVEL','1CONCRETE','1CURB')): pass
        I=I[(I[:,0]!=I[:,1])|(I[:,0]!=I[:,2])]
        if not len(I): continue
        C=V[I][:,:,[0,2]].mean(1);sel=(C[:,0]>X0)&(C[:,0]<X1)&(C[:,1]>Z0)&(C[:,1]<Z1)
        if not sel.any(): continue
        I=I[sel];tex=dict((s,t) for s,_,t in M['samplers']).get('txDiffuse')
        tn=None
        if tex and tex!='NULL.dds':
            key=f+tex
            if key not in texdone:
                try:
                    im=Image.open(io.BytesIO(K.get_tex(p,tex)));im=im.convert('RGBA')
                    if im.width>2048: im=im.resize((2048,int(2048*im.height/im.width)))
                    tn=f'{O}/t{len(texdone)}.png';im.save(tn)
                except Exception as e: print('tex fail',tex,e);tn=None
                texdone[key]=tn
            tn=texdone[key]
        np.savez(f'{O}/m{k:04d}.npz',V=V,I=I,tex=str(tn),at=('_AT' in M['shader']) or M['name'].startswith(('tree','grass','drag_rubber')),name=name,mat=M['name']);k+=1
print(k,'meshes',len(texdone),'tex')
