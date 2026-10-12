"""VR7 shared: AC .ai read/write (v7) + cached physics rasters per layout."""
import sys,os,struct,re,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
Z='/workspace/rpotm/project/zw_rpm/'
FILES={'main':['zw_rpm.kn5','zw_rpm_physical.kn5','zw_rpm_gp.kn5','zw_rpm_own.kn5','zw_ext.kn5','zw_dragexit.kn5','zw_draglaunch.kn5','zw_tents.kn5','zw_vegetation.kn5','zw_vr5.kn5','zw_vr6.kn5','zw_vr7_longcut.kn5'],
       'short':['zw_rpm.kn5','zw_rpm_physical.kn5','zw_rpm_sh.kn5','zw_rpm_own.kn5','zw_ext.kn5','zw_dragexit.kn5','zw_draglaunch.kn5','zw_tents.kn5','zw_vegetation.kn5','zw_vr5.kn5','zw_vr6.kn5']}
EXTRA=['speed','gas','brake','obsLatG','radius','sideLeft','sideRight','camber','direction','nx','ny','nz','length','fx','fy','fz','tag','grade']
def read_ai(f):
    d=open(f,'rb').read();v,n,lt,sc=struct.unpack_from('<4i',d,0)
    P=np.frombuffer(d,np.dtype([('p','<3f4'),('l','<f4'),('id','<i4')]),n,16).copy()
    o=16+n*20;ne,=struct.unpack_from('<i',d,o);E=np.frombuffer(d,'<f4',ne*18,o+4).reshape(ne,18).copy()
    return dict(version=v,laptime=lt,samples=sc,P=P,E=E,tail=d[o+4+ne*72:])
def write_ai(f,pos,E):
    n=len(pos);L=np.r_[0,np.cumsum(np.linalg.norm(np.diff(pos,axis=0),axis=1))]
    P=np.zeros(n,np.dtype([('p','<3f4'),('l','<f4'),('id','<i4')]));P['p']=pos;P['l']=L;P['id']=np.arange(n)
    with open(f,'wb') as fh:
        fh.write(struct.pack('<4i',7,n,0,0));fh.write(P.tobytes());fh.write(struct.pack('<i',n));fh.write(np.asarray(E,'<f4').tobytes());fh.write(struct.pack('<i',0))
def keys():
    s=open(Z+'main/data/surfaces.ini').read();out={}
    for sec in re.split(r'\n(?=\[SURFACE_)',s):
        k=re.search(r'^KEY=(\w+)',sec,re.M)
        if k: out[k.group(1)]=dict(valid=int(re.search(r'IS_VALID_TRACK=(\d)',sec).group(1)),pit=int(re.search(r'IS_PITLANE=(\d)',sec).group(1)))
    return out
def mesh_key(name,K):
    m=re.match(r'^\d+([A-Z]+)',name);s=m.group(1)
    best=[k for k in K if s.startswith(k)];return max(best,key=len) if best else None
def layout_raster(lay,res=0.5,box=(-260,300,-950,260)):
    c=f'/workspace/vr7/raster_{lay}.npz'
    if os.path.exists(c):
        r=np.load(c,allow_pickle=True);return r['xs'],r['zs'],r['H'],r['KEY'],r['UP'],list(r['names'])
    from physraster import physmeshes,raster
    xs,zs,H,KEY,UP,names=raster(physmeshes(FILES[lay],box),box,res)
    np.savez(c,xs=xs,zs=zs,H=H,KEY=KEY,UP=UP,names=np.array(names,object));return xs,zs,H,KEY,UP,names
