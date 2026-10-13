"""Export kn5 meshes (optionally filtered to an AC xz box) to OBJ+MTL with PNG textures, for Blender previews. AC (x,y,z) -> Blender (x,-z,y)."""
import sys,os,io,struct,numpy as np
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..'));import kn5mat as KM,topview as T
from PIL import Image
def export(kns,out,box=None,skip=('1WALL',)):
    os.makedirs(out,exist_ok=True);ob=open(f'{out}/scene.obj','w');mt=open(f'{out}/scene.mtl','w');ob.write('mtllib scene.mtl\n');base=1;done=set()
    for kn in kns:
        K=KM.load(kn);TX={t[0]:t[1] for t in K['textures']};mats=K['materials']
        d=open(kn,'rb').read();_,nodes=__import__('kn5patch').scan(kn)
        for name,o,l,c in nodes:
            if c!=2 or name.startswith(skip): continue
            q=o+l+5;vis=d[q+1];nv,=struct.unpack_from('<I',d,q+3);V=np.frombuffer(d,'<f4',nv*11,q+7).reshape(nv,11);r=q+7+nv*44
            ni,=struct.unpack_from('<I',d,r);I=np.frombuffer(d,'<u2',ni,r+4).reshape(-1,3);r+=4+ni*2;mi,=struct.unpack_from('<I',d,r);rend=d[r+8+8+16]
            if not rend or len(I)==0: continue
            I=I[I[:,0]!=I[:,1]].astype(np.int64)
            if box is not None:
                C=V[I][:,:,[0,2]].mean(1);k=(C[:,0]>box[0])&(C[:,0]<box[1])&(C[:,1]>box[2])&(C[:,1]<box[3]);I=I[k]
                if len(I)==0: continue
            m=mats[mi];mn=f'{os.path.basename(kn)}_{m["name"]}'.replace(' ','_')
            if mn not in done:
                done.add(mn);dif=[t for s,i,t in m['samplers'] if s=='txDiffuse'];mt.write(f'newmtl {mn}\nKd 1 1 1\n')
                if dif and dif[0] in TX:
                    fn=dif[0].replace(' ','_')+'.png'
                    if not os.path.exists(f'{out}/{fn}'):
                        try:
                            im=Image.open(io.BytesIO(TX[dif[0]]));im.thumbnail((2048,2048));im.save(f'{out}/{fn}')
                        except Exception: fn=None
                    if fn: mt.write(f'map_Kd {fn}\n'+('map_d '+fn+'\n' if 'AT' in m['shader'] or m['ab'] else ''))
            ob.write(f'o {name}\nusemtl {mn}\n')
            for v in V: ob.write(f'v {v[0]:.3f} {-v[2]:.3f} {v[1]:.3f}\n')
            for v in V: ob.write(f'vt {v[6]:.5f} {1-v[7]:.5f}\n')
            for t in I: ob.write('f '+' '.join(f'{base+j}/{base+j}' for j in t)+'\n')
            base+=nv
    ob.close();mt.close()
if __name__=='__main__':
    export(sys.argv[3:],sys.argv[1],tuple(float(x) for x in sys.argv[2].split(',')) if sys.argv[2]!='-' else None)
