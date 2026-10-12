"""Build zw_ext.kn5 (north extension: ground band, roads + physics, lots, two fuel stations, I-29 interchange visuals,
roadside dressing, invisible walls). Run after textures.py. AC frame = track frame (see geo.py)."""
import sys,os,json,math,struct,numpy as np,cv2
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..'));sys.path.insert(0,os.path.dirname(__file__))
import geo,kn5write as W,kn5patch as K,kn5mat as KM
from meshlib import M,ribbon,resample,fix
from scipy.spatial import cKDTree
from scipy.ndimage import gaussian_filter1d,map_coordinates,maximum_filter1d,minimum_filter1d,distance_transform_edt
import shapely.geometry as sg,shapely.ops as so,mapbox_earcut as earcut
ROOT=os.path.join(os.path.dirname(__file__),'..','..');NO=f'{ROOT}/assets_src/north';Z=f'{ROOT}/zw_rpm';KN=f'{Z}/zw_rpm.kn5'
OSM=json.load(open('/workspace/rpotm/geo/ext/osm_ac.json'));WAY={w['id']:w for w in OSM['ways']}
X0,X1,Z0,Z1=geo.BOX;WALLX=-335.0
LOG=[]
# ---------------------------------------------------------------- road specs
lanes=lambda w,d=2:int(str(w['tags'].get('lanes',d)).split(';')[0])
PHYS=[]  # (name, poly xz, half width, surface)
VIS=[]
def runs(P,keep):
    P,_=resample(P,1.0);k=keep(P);out=[];cur=[]
    for p,ok in zip(P,k):
        if ok: cur.append(p)
        elif len(cur)>5: out.append(np.array(cur));cur=[]
        else: cur=[]
    if len(cur)>5: out.append(np.array(cur))
    return out
inroute=lambda P:(P[:,0]>=X0)&(P[:,0]<=WALLX-2)&(P[:,1]>=Z0)&(P[:,1]<=700)
inband_e=lambda P:(P[:,0]>WALLX-40)&(P[:,0]<=X1)&(P[:,1]>=Z0)&(P[:,1]<geo.zb(P[:,0])-4)
for wid,w in WAY.items():
    t=w['tags'];h=t.get('highway');P=np.array(w['ac'])
    if h=='tertiary' or (h=='residential' and t.get('name')=='188th Street') or wid in(309854951,15976346):
        for R in runs(P,lambda Q:inroute(Q)&(Q[:,1]>-2960)): PHYS.append((f'r{wid}',R,3.7 if h=='tertiary' else 3.5,'asphalt',t.get('name','')))
    elif h in('trunk','trunk_link','primary'):
        hw=lanes(w)*3.65/2+(0.6 if h!='trunk_link' else 0.3)
        for R in runs(P,inroute): PHYS.append((f'r{wid}',R,hw,'concrete' if t.get('surface')=='concrete' else 'asphalt','US 34'))
        for R in runs(P,inband_e): VIS.append((f'v{wid}',R,hw,'concrete','US 34'))
    elif h in('motorway','motorway_link'):
        hw=(lanes(w,1)*3.65+ (4.0 if h=='motorway' else 2.5))/2
        for R in runs(P,inband_e): VIS.append((f'v{wid}',R,hw,'concrete','I-29' if h=='motorway' else 'ramp'))
# ---------------------------------------------------------------- height raster (1 m) over box
gx=np.arange(X0,X1+1,1.0);gz=np.arange(Z0,Z1+1,1.0);GX,GZ=np.meshgrid(gx,gz);GP=np.c_[GX.ravel(),GZ.ravel()]
NAT,WB=geo.natural(GP);NAT=NAT.reshape(GX.shape);WB=WB.reshape(GX.shape);H=NAT.copy()
from scipy.ndimage import gaussian_filter
NATS=gaussian_filter(NAT,12,mode='nearest')  # VR3: smoothed terrain shared by roads + lots (consistent junctions, gentle grades)
def nats(P):
    P=np.atleast_2d(P);v=map_coordinates(NATS,[P[:,1]-Z0,P[:,0]-X0],order=1,mode='nearest');v[P[:,1]>=geo.zb(P[:,0])]=-0.1;return v
def Hs(P):
    P=np.atleast_2d(P);r=(P[:,1]-Z0);c=(P[:,0]-X0);v=map_coordinates(H,[r,c],order=1,mode='nearest')
    south=P[:,1]>=geo.zb(P[:,0]);v[south]=-0.1;return v
def road_profile(R,visual=False):
    if not visual: return gaussian_filter1d(nats(R),15,mode='nearest')
    y,_=geo.natural(R)
    if visual:  # bridge-fill: close dips (bare-earth DEM removes bridge decks)
        y=minimum_filter1d(maximum_filter1d(y,121),121)
    return gaussian_filter1d(y,8,mode='nearest')
roads=[]
for spec in PHYS: roads.append((*spec,road_profile(spec[1])+0.06,True))
for spec in VIS: roads.append((*spec,road_profile(spec[1],True)+0.08,False))
# burn roads into H: within hw+1.5 -> road y-0.15, feather 8 m
S=[];Y=[];HW=[]
for name,R,hw,surf,lab,y,ph in roads:
    S.append(R);Y.append(y);HW.append(np.full(len(R),hw))
S=np.vstack(S);Y=np.concatenate(Y);HW=np.concatenate(HW);tr=cKDTree(S)
d,ix=tr.query(GP,distance_upper_bound=40);ok=np.isfinite(d);dd=np.full(len(GP),1e9);dd[ok]=d[ok]
wgt=np.zeros(len(GP));wgt[ok]=np.clip(1-(dd[ok]-HW[ix[ok]]-6.0)/10,0,1)
tgt=np.zeros(len(GP));tgt[ok]=Y[ix[ok]]-0.2;Hf=H.ravel();Hf=Hf*(1-wgt)+tgt*wgt;H=Hf.reshape(H.shape)  # VR3: wider/deeper burn
# ---------------------------------------------------------------- lots from NAIP (bright, low NDVI) in search boxes
nb=np.load(f'{NO}/naip_box_rgbn.npy').astype(np.float32);nh,nw=nb.shape[:2]
r_,g_,b_,n_=[nb[...,i] for i in range(4)];ndvi=(n_-r_)/(n_+r_+1e-3);bri=nb[...,:3].mean(-1);sat=nb[...,:3].max(-1)-nb[...,:3].min(-1)
paved=((ndvi<0.10)&(bri>135)&(sat<45)).astype(np.uint8)
def px2ac(c,r): return np.c_[X0+c/(nw-1)*(X1-X0),Z0+r/(nh-1)*(Z1-Z0)]
LOTS=[('loves',(-870,-640,-2845,-2640),'concrete'),('bp',(-622,-505,-2790,-2640),'concrete'),('ne_yard',(-505,-378,-2945,-2645),'gravel')]
lotpolys=[]
for nm,(a0,a1,b0,b1),surf in LOTS:
    m=np.zeros_like(paved);c0=int((a0-X0)/(X1-X0)*(nw-1));c1=int((a1-X0)/(X1-X0)*(nw-1));r0=int((b0-Z0)/(Z1-Z0)*(nh-1));r1=int((b1-Z0)/(Z1-Z0)*(nh-1))
    m[r0:r1,c0:c1]=paved[r0:r1,c0:c1];m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8));m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
    cs,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    for c in cs:
        pts=px2ac(c[:,0,0].astype(float),c[:,0,1].astype(float))
        if len(pts)<4: continue
        pg=sg.Polygon(pts).buffer(0).buffer(3,join_style=1).buffer(-6,join_style=1).buffer(3,join_style=1).simplify(0.4)  # smooth pixel stair-steps
        if pg.area<400: continue
        for g in getattr(pg,'geoms',[pg]): lotpolys.append((nm,g,surf))
LOG.append('lots: '+', '.join(f'{n} {p.area:.0f} m2' for n,p,_ in lotpolys))
# lot heights: median natural inside; burn
for i,(nm,pg,surf) in enumerate(lotpolys):
    inside=np.array([pg.contains(sg.Point(p)) for p in GP[::7]]);yl=float(np.median(NAT.ravel()[::7][inside])) if inside.any() else 0.0
    mask=np.zeros(GX.shape,np.uint8);cv2.fillPoly(mask,[np.round(np.c_[np.array(pg.exterior.coords)[:,0]-X0,np.array(pg.exterior.coords)[:,1]-Z0]).astype(np.int32)],1)
    dist=distance_transform_edt(1-mask);w=np.clip(1-(dist-6)/8,0,1);H=H*(1-w)+(NATS+0.04-0.2)*w;lotpolys[i]=(nm,pg,surf,yl)  # VR3
# ---------------------------------------------------------------- materials
TM=W.read_materials(KN);MMp=TM['wc'];PPp=TM['roof_red'];ATp=TM['trackedge'];MLp=TM['google']
def P_(props,**kw):
    out=[]
    for p,r in props:
        out.append((p,struct.pack('<f',kw[p])+r[4:]) if p in kw else (p,r))
    return out
MATS=[];MI={};TEX={}
def tex(n,path=None):
    if n in TEX: return n
    for d in (path,NO,f'{ROOT}/assets_src/vr2',f'{ROOT}/assets_src/textures'):
        if d and os.path.exists(f'{d}/{n}'): TEX[n]=open(f'{d}/{n}','rb').read();return n
    TEX[n]=K.get_tex(KN,n);return n
def mat(name,shader,smp,tpl,**kw):
    MI[name]=len(MATS);MATS.append(dict(name=name,shader=shader,ab=tpl['ab'],at=tpl['at'],dm=tpl['dm'],props=P_(tpl['props'],**kw),samplers=[(s,i,tex(t)) for s,i,t in smp]))
def mm(name,d,n,mp,**kw): mat(name,'ksPerPixelMultiMap',[('txDiffuse',0,d),('txNormal',1,n),('txMaps',2,mp),('txDetail',3,'ext_flat_nm.dds')],MMp,**{'ksAmbient':0.3,'ksDiffuse':0.3,**kw})
def pp(name,d,**kw): mat(name,'ksPerPixel',[('txDiffuse',0,d)],PPp,**{'ksAmbient':0.35,'ksDiffuse':0.35,'ksSpecular':0.05,**kw})
def at(name,d,**kw): mat(name,'ksPerPixelAT',[('txDiffuse',0,d)],ATp,**kw)
gs=[(s,i,t) for s,i,t in MLp['samplers']];gs=[(s,i,{'txDiffuse':'ext_ground.dds','txMask':'ext_ground_mask.dds'}.get(s,t)) for s,i,t in gs]
mat('ext_ground','ksMultilayer_fresnel_nm',gs,MLp)
mm('ext_asphalt','ext_asphalt.dds','ext_asphalt_nm.dds','ext_asphalt_maps.dds',ksSpecular=0.15,ksSpecularEXP=25)
mm('ext_concrete','concrete_seams.dds','ext_concrete_nm.dds','concrete_maps.dds',ksSpecular=0.1,ksSpecularEXP=20)
mm('ext_gravel','own_gravel.dds','own_gravel_nm.dds','own_gravel_maps.dds',ksSpecular=0.05,ksSpecularEXP=8)
pp('ext_white','ext_white.dds');pp('ext_yellow','ext_yellow.dds')
mm('ext_wall_tan','ext_wall_tan.dds','ext_wall_nm.dds','ext_paint_maps.dds',ksSpecular=0.12,ksSpecularEXP=20)
mm('ext_wall_grey','ext_wall_grey.dds','ext_corr_nm.dds','ext_metal_maps.dds',ksSpecular=0.3,ksSpecularEXP=30)
mm('ext_roof','own_galv.dds','own_galv_nm.dds','own_galv_maps.dds',ksSpecular=0.4,ksSpecularEXP=40)
mm('ext_canopy','ext_canopy.dds','ext_canopy_nm.dds','ext_paint_maps.dds',ksSpecular=0.25,ksSpecularEXP=30)
mm('ext_glass','own_tower_glass.dds','ext_flat_nm.dds','own_glass_maps.dds',ksSpecular=0.9,ksSpecularEXP=120)
mm('ext_metal','own_galv.dds','own_galv_nm.dds','own_galv_maps.dds',ksSpecular=0.5,ksSpecularEXP=40)
pp('ext_pump','ext_pump.dds',ksSpecular=0.2);pp('ext_wood','ext_wood.dds')
at('ext_fence','ext_fence.dds');at('ext_stop','ext_stop.dds');at('ext_stop_back','ext_stop_back.dds')
for s in('ext_sign_travelstop','ext_sign_fuel','ext_fascia_ts','ext_fascia_fuel','ext_street_188','ext_street_190','ext_allway'): pp(s,s+'.dds',ksEmissive=0.0)
pp('ext_invisible','ext_flat_nm.dds')
# stop sign back (grey, same octagon alpha)
from PIL import Image
st=np.array(Image.open(f'{NO}/ext_stop.png'));st[...,:3]=150
import build_open_textures as BO
TEX['ext_stop_back.dds']=BO.write_dds(st,'DXT5',10,None)
# ---------------------------------------------------------------- meshes
MESH=[]
def emit(name,matn,m,lod=0,phys=False):
    V,I=m.out() if isinstance(m,M) else m
    if len(V)==0: return
    # split >65k verts
    I=np.asarray(I);k=0;start=0
    while start<len(I):
        tris=I[start:start+21000];u,inv=np.unique(tris,return_inverse=True)
        MESH.append(dict(name=name if start==0 else f'{name}_{k}',mat_index=MI[matn],verts=V[u],idx=inv.reshape(-1,3),lod_out=lod));start+=21000;k+=1
# ground band
nx=261;nzr=92;xs=np.linspace(X0,X1,nx);GV=[]
for i,x in enumerate(xs):
    zb=float(geo.zb(x))
    for j in range(nzr+1):
        z=Z0+(zb-Z0)*j/nzr;GV.append((x,z))
GV=np.array(GV);gy=map_coordinates(H,[GV[:,1]-Z0,GV[:,0]-X0],order=1,mode='nearest');last=np.arange(nx)*(nzr+1)+nzr;gy[last]=-0.1
Gr=gy.reshape(nx,nzr+1);dx=np.gradient(Gr,axis=0)/(xs[1]-xs[0]);dz=np.gradient(Gr,axis=1)/((geo.zb(xs)[:,None]-Z0)/nzr)
N=np.dstack([-dx,np.ones_like(dx),-dz]).reshape(-1,3);N/=np.linalg.norm(N,axis=1)[:,None]
V=np.c_[GV[:,0],gy,GV[:,1],N,(GV[:,0]-X0)/(X1-X0),(GV[:,1]-Z0)/(Z1-Z0),np.tile([1,0,0],(len(GV),1))]
I=[]
for i in range(nx-1):
    for j in range(nzr):
        a=i*(nzr+1)+j;b=a+1;c=a+nzr+2;d_=a+nzr+1;I+=[[a,b,c],[a,c,d_]]
emit('1GRASS_EXT','ext_ground',(V,fix(V,I)),phys=True)
# roads + shoulders + markings
rm={'asphalt':'ext_asphalt','concrete':'ext_concrete'};nphys=0;nvis=0
for name,R,hw,surf,lab,y,ph in roads:
    R2,s=resample(R,3.0);y2=np.interp(s,np.r_[0,np.cumsum(np.linalg.norm(np.diff(R,axis=0),axis=1))],y)
    vs=9.0 if surf=='concrete' else 6.0
    V,I=ribbon(R2,y2,[(hw,0),(-hw,0)],[0,2*hw/(7.3 if surf=='concrete' else 6.0)],vs,s)
    pre=('1XROAD_' if ph else 'xroad_')
    emit(pre+name,rm[surf],(V,I),lod=0 if ph else 2500)
    V,I=ribbon(R2,y2,[(hw+1.0,-0.1),(hw,0)],[0,0.5],2.0,s);emit(('1GRAVEL_EXT_' if ph else 'xshoulder_')+name+'L','ext_gravel',(V,I),lod=0 if ph else 1500)
    V,I=ribbon(R2,y2,[(-hw,0),(-hw-1.0,-0.1)],[0,0.5],2.0,s);emit(('1GRAVEL_EXT_' if ph else 'xshoulder_')+name+'R','ext_gravel',(V,I),lod=0 if ph else 1500)
    # markings (visual): white edge lines; yellow centre (2-lane two-way) or yellow left edge (divided one-way)
    edge=hw-0.45 if hw>3 else hw-0.3
    for o in (edge,-edge):
        V,I=ribbon(R2,y2+0.012,[(o+0.06,0),(o-0.06,0)],[0,1],1,s);emit(f'xline_{name}_{o:+.0f}','ext_white' if (lab!='US 34' or o<0) else 'ext_yellow',(V,I),lod=900)
    if lab in('190th Street','188th Street',''):
        R3,s3=resample(R2,1.0);y3=np.interp(s3,s,y2);keep=(s3%12)<4.5
        segs=np.split(np.arange(len(R3)),np.flatnonzero(np.diff(keep.astype(int)))+1)
        mmk=M()
        for sg_ in segs:
            if keep[sg_[0]] and len(sg_)>1: Vv,Ii=ribbon(R3[sg_],y3[sg_]+0.012,[(0.06,0),(-0.06,0)],[0,1],1,s3[sg_]);mmk.add(Vv,Ii)
        emit(f'xline_{name}_c','ext_yellow',mmk,lod=700)
    if ph: nphys+=1
    else: nvis+=1
LOG.append(f'roads: {nphys} drivable ribbons (+gravel shoulders), {nvis} visual (I-29/ramps/US-34 east)')
# bridges (visual): where bridge-filled profile is >2.5 m above terrain
mb=M()
for name,R,hw,surf,lab,y,ph in roads:
    if ph: continue
    nat,_=geo.natural(R);gap=y-nat;br=gap>2.5
    if br.sum()<5: continue
    idx=np.flatnonzero(br);T_=np.gradient(R,axis=0);T_/=np.linalg.norm(T_,axis=1)[:,None];L=np.c_[-T_[:,1],T_[:,0]]
    for i in idx[::2]:
        for sgn in(1,-1):
            p=R[i]+L[i]*sgn*(hw+0.2);mb.box((p[0],y[i]-0.05,p[1]),(2.1,0.85,0.35),yaw=math.atan2(T_[i,0],T_[i,1]),uvscale=2)
        mb.box((R[i,0],y[i]-1.3,R[i,1]),(2.1,1.22,2*hw+0.6),yaw=math.atan2(T_[i,0],T_[i,1]),uvscale=3,bottom=True,top=False)
    LOG.append(f'bridge {name}: {br.sum()} m')
emit('xbridges','ext_concrete',mb,lod=2500)
# lots
for i,(nm,pg,surf,yl) in enumerate(lotpolys):
    ext=np.array(pg.exterior.coords)[:-1];holes=[np.array(h.coords)[:-1] for h in pg.interiors];allp=np.vstack([ext]+holes)
    rings=np.cumsum([len(ext)]+[len(h) for h in holes]).astype(np.uint32)
    # VR3: Delaunay over boundary + 4 m interior grid so the lot follows the smoothed terrain (no ground poking through)
    from scipy.spatial import Delaunay
    bx=pg.bounds;gg=np.array([(x_,z_) for x_ in np.arange(bx[0]+2,bx[2],4.0) for z_ in np.arange(bx[1]+2,bx[3],4.0)])
    if len(gg): gg=gg[[pg.buffer(-1.0).contains(sg.Point(q)) for q in gg]]
    allp=np.vstack([allp,gg]) if len(gg) else allp
    tri=Delaunay(allp).simplices;cen=allp[tri].mean(1);tri=tri[[pg.contains(sg.Point(q)) for q in cen]]
    V=np.c_[allp[:,0],nats(allp)+0.04,allp[:,1],np.tile([0,1,0],(len(allp),1)),allp[:,0]/(9.0 if surf=='concrete' else 2.0),allp[:,1]/(9.0 if surf=='concrete' else 2.0),np.tile([1,0,0],(len(allp),1))]
    emit(f'1XLOT_{nm}_{i}' if surf=='concrete' else f'1GRAVEL_EXT_lot{i}','ext_concrete' if surf=='concrete' else 'ext_gravel',(V,fix(V,tri)))
def lot_y(p):
    for nm,pg,surf,yl in lotpolys:
        if pg.contains(sg.Point(p)): return float(nats(np.array([p]))[0])+0.04
    return float(Hs(np.array([p]))[0])+0.1
# buildings / canopies from OSM
mw=M();mg=M();mr=M();mc=M();mgl=M();mcol=M();mpump=M();misl=M();mfas_ts=M();mfas_f=M()
def footprint(wid): return sg.Polygon(WAY[wid]['ac']).buffer(0)
def walls(m,pg,y0,h,uvs=3.0):
    c=np.array(pg.exterior.coords)
    if not sg.LinearRing(c).is_ccw: c=c[::-1]
    for a,b in zip(c[:-1],c[1:]):
        e=b-a;L_=np.linalg.norm(e)
        if L_<0.2: continue
        n=np.array([e[1],0,-e[0]])/L_  # outward for ccw in (x,z)? fix() orients winding to normal
        cen=np.array([(a[0]+b[0])/2,0,(a[1]+b[1])/2]);
        if sg.Point(cen[[0,2]]+n[[0,2]]*0.5).within(pg): n=-n
        m.quad([[a[0],y0,a[1]],[b[0],y0,b[1]],[b[0],y0+h,b[1]],[a[0],y0+h,a[1]]],n,[(0,h/uvs),(L_/uvs,h/uvs),(L_/uvs,0),(0,0)])
def flat(m,pg,y,uvs=4.0,down=False):
    ext=np.array(pg.exterior.coords)[:-1];tri=earcut.triangulate_float64(ext,np.array([len(ext)],np.uint32)).reshape(-1,3)
    V=np.c_[ext[:,0],np.full(len(ext),y),ext[:,1],np.tile([0,-1 if down else 1,0],(len(ext),1)),ext[:,0]/uvs,ext[:,1]/uvs,np.tile([1,0,0],(len(ext),1))];m.add(V,tri)
STORES={1092228301:('Love\'s-type travel store',7.0,mw,'ts'),1092228302:('BP-type store',5.2,mw,'f'),1092228300:('tire/service shop',8.0,mg,None)}
CANOP={1092228306:('diesel canopy',6.2,True,'ts'),1092228305:('car canopy',5.2,True,'ts'),1092228304:('car canopy',5.2,True,'f'),1092228303:('small canopy',4.0,False,'f')}
canopy_cent={}
for wid,(lab,clr,pumps,who) in CANOP.items():
    pg=footprint(wid);r=pg.minimum_rotated_rectangle;c=np.array(r.exterior.coords)[:4];e1=c[1]-c[0];e2=c[2]-c[1]
    if np.linalg.norm(e1)<np.linalg.norm(e2): e1,e2=e2,e1
    Lg,Wd=np.linalg.norm(e1),np.linalg.norm(e2);ax=e1/Lg;yaw=math.atan2(ax[0],ax[1]);cen=np.array(r.centroid.coords[0]);y0=lot_y(cen)
    canopy_cent[who]=canopy_cent.get(who,[])+[cen]
    mc.box((cen[0],y0+clr,cen[1]),(Wd,0.9,Lg),yaw=yaw,uvscale=4,bottom=True)
    ncol=max(2,int(round(Lg/9)));cols=[cen+ax*(-Lg/2+Lg*(k+0.5)/ncol) for k in range(ncol)]
    for p in cols:
        mcol.box((p[0],y0,p[1]),(0.45,clr,0.45),yaw=yaw,uvscale=2)
        if pumps:
            isl=min(Wd*0.75,7.5);misl.box((p[0],y0,p[1]),(isl,0.18,1.3),yaw=yaw,uvscale=2)
            perp=np.array([ax[1],-ax[0]])
            for o in(-isl/3,isl/3):
                q=p+perp*o;mpump.box((q[0],y0+0.18,q[1]),(0.95,1.85,0.55),yaw=yaw,uvscale=1.85)
    # fascia signs on both long sides
    perp=np.array([ax[1],-ax[0]])
    for sgn in(1,-1):
        q=cen+perp*sgn*(Wd/2+0.03);n_=perp*sgn;r_=np.array([n_[1],-n_[0]]);a=q-r_*Lg*0.3;b=q+r_*Lg*0.3;yy=y0+clr+0.1  # r_ = viewer's right -> text reads correctly on both sides
        (mfas_ts if who=='ts' else mfas_f).quad([[a[0],yy,a[1]],[b[0],yy,b[1]],[b[0],yy+0.7,b[1]],[a[0],yy+0.7,a[1]]],[n_[0],0,n_[1]],[(0,1),(1,1),(1,0),(0,0)])
    LOG.append(f'{lab} ({who}): {Lg:.0f}x{Wd:.0f} m, clearance {clr} m, {ncol} columns' + (f', {ncol} islands/{2*ncol} dispensers' if pumps else ''))
for wid,(lab,h,mm_,who) in STORES.items():
    pg=footprint(wid);cen=np.array(pg.centroid.coords[0]);y0=lot_y(cen)
    walls(mm_,pg,y0,h);flat(mr,pg,y0+h);walls(mr,pg.buffer(0.25,join_style=2),y0+h,0.6)  # roof + parapet
    if who:
        cc=np.mean(canopy_cent[who],0);c=np.array(pg.exterior.coords);best=None
        for a,b in zip(c[:-1],c[1:]):
            mid=(a+b)/2;dd=np.linalg.norm(mid-cc)
            if np.linalg.norm(b-a)>6 and (best is None or dd<best[0]): best=(dd,a,b)
        _,a,b=best;e=(b-a)/np.linalg.norm(b-a);n=np.array([e[1],-e[0]])
        if sg.Point((a+b)/2+n*0.5).within(pg): n=-n
        q=lambda p,o:p+n*0.06+e*o
        L_=np.linalg.norm(b-a);g0,g1=q(a,L_*0.2),q(a,L_*0.8)
        mgl.quad([[g0[0],y0+0.3,g0[1]],[g1[0],y0+0.3,g1[1]],[g1[0],y0+2.7,g1[1]],[g0[0],y0+2.7,g0[1]]],[n[0],0,n[1]],[(0,1),(1,1),(1,0),(0,0)])
        f0,f1=q(a,L_*0.25),q(a,L_*0.75)
        (mfas_ts if who=='ts' else mfas_f).quad([[f0[0],y0+h-2.2,f0[1]],[f1[0],y0+h-2.2,f1[1]],[f1[0],y0+h-0.6,f1[1]],[f0[0],y0+h-0.6,f0[1]]],[n[0],0,n[1]],[(0,1),(1,1),(1,0),(0,0)])
    LOG.append(f'{lab}: {pg.area:.0f} m2 footprint, {h} m high')
for nm,m_,mt,lod in(('stores','x',None,0),):pass
emit('xstore_walls','ext_wall_tan',mw,1500);emit('xshop_walls','ext_wall_grey',mg,1500);emit('xroofs','ext_roof',mr,1500);emit('xcanopies','ext_canopy',mc,1500)
emit('xglass','ext_glass',mgl,800);emit('xcolumns','ext_canopy',mcol,800);emit('xislands','ext_concrete',misl,500);emit('xpumps','ext_pump',mpump,500)
emit('xfascia_ts','ext_fascia_ts',mfas_ts,1200);emit('xfascia_fuel','ext_fascia_fuel',mfas_f,1200)
# signs: pylon (travel stop) + monument (fuel)
def panel(m,c,y,w,h,yaw,double=True):
    co,si=math.cos(yaw),math.sin(yaw);ax=np.array([co,-si]);n=np.array([si,co])
    for sgn in((1,-1) if double else (1,)):
        nn=n*sgn;r_=np.array([nn[1],-nn[0]]);p=c+nn*0.15;a=p-r_*w/2;b=p+r_*w/2
        m.quad([[a[0],y,a[1]],[b[0],y,b[1]],[b[0],y+h,b[1]],[a[0],y+h,a[1]]],[nn[0],0,nn[1]],[(0,1),(1,1),(1,0),(0,0)])
mts=M();mfs=M();mpost=M()
c=np.array([-662.0,-2652.0]);y0=lot_y(c);[mpost.cyl((c[0]+o,y0,c[1]),0.35,18,10,3) for o in(-2,2)];panel(mts,c,y0+12,6.5,6.5,0.0);mpost.box((c[0],y0+11.6,c[1]),(7.0,0.4,0.5),uvscale=2)
c=np.array([-603.0,-2650.0]);y0=lot_y(c);mpost.box((c[0],y0,c[1]),(3.4,1.0,0.7),uvscale=1);panel(mfs,c,y0+1.0,3.2,1.6,0.0)
emit('xsign_travelstop','ext_sign_travelstop',mts,1500);emit('xsign_fuel','ext_sign_fuel',mfs,900)
# 4-way stop at 188th St x US-34 (two carriageways)
def poly(wid): return np.array(WAY[wid]['ac'])
st=poly(309854950);usn=[r for r in PHYS if r[4]=='US 34']
def nearest_cross(A_,B_):
    tA=cKDTree(A_);d,i=tA.query(B_);k=int(np.argmin(d));return B_[k],k
cross=[]
for name,R,hw,surf,lab in [r for r in usn]:
    p,k=nearest_cross(st,R)
    if np.linalg.norm(st[np.argmin(np.linalg.norm(st-p,axis=1))]-p)<3 and -800<p[0]<-450: cross.append((p,R,k,hw))
cross.sort(key=lambda t:t[0][1])  # north carriageway first (more negative z)
mstop=M();mstopb=M();mall=M();mbl8=M()
def stop_sign(pos,face):  # face = unit xz vector the sign faces (toward approaching traffic)
    y0=float(Hs(np.array([pos]))[0]);mpost.cyl((pos[0],y0,pos[1]),0.04,2.6,6,1)
    yaw=math.atan2(face[0],face[1]);ax=np.array([math.cos(yaw),-math.sin(yaw)])
    a=pos+face*0.06-ax*0.38;b=pos+face*0.06+ax*0.38
    mstop.quad([[a[0],y0+1.9,a[1]],[b[0],y0+1.9,b[1]],[b[0],y0+2.66,b[1]],[a[0],y0+2.66,a[1]]],[face[0],0,face[1]],[(0,1),(1,1),(1,0),(0,0)])
    a2=pos+face*0.04-ax*0.38;b2=pos+face*0.04+ax*0.38
    mstopb.quad([[b2[0],y0+1.9,b2[1]],[a2[0],y0+1.9,a2[1]],[a2[0],y0+2.66,a2[1]],[b2[0],y0+2.66,b2[1]]],[-face[0],0,-face[1]],[(0,1),(1,1),(1,0),(0,0)])
    a=pos+face*0.06-ax*0.3;b=pos+face*0.06+ax*0.3
    mall.quad([[a[0],y0+1.55,a[1]],[b[0],y0+1.55,b[1]],[b[0],y0+1.85,b[1]],[a[0],y0+1.85,a[1]]],[face[0],0,face[1]],[(0,1),(1,1),(1,0),(0,0)])
if len(cross)>=2:
    (pn,Rn,kn,hwn),(ps,Rs,ks,hws)=cross[0],cross[-1];sd=st[-1]-st[0];sd/=np.linalg.norm(sd)
    north=np.array([0,-1.0]) if True else None
    # 188th northbound (travel -z) before south carriageway; southbound (+z) before north carriageway
    for p,hw_,trav in((ps,hws,np.array([0,-1.0])),(pn,hwn,np.array([0,1.0]))):
        right=np.array([-trav[1],trav[0]])*-1  # right-hand side of travel in AC frame (x east, z south)
        right=np.array([trav[1],-trav[0]])*-1
        pos=p-trav*(hw_+4)+np.array([-trav[1],trav[0]])*(-(3.5+1.8));stop_sign(pos,-trav)
    for p,R,k,hw_ in (cross[0],cross[-1]):  # one sign per US-34 approach (skip median carriageway duplicate)
        T_=R[min(k+1,len(R)-1)]-R[max(k-1,0)];T_/=np.linalg.norm(T_)
        pos=p-T_*(3.5+4)+np.array([-T_[1],T_[0]])*(-(hw_+1.8));stop_sign(pos,-T_)
    LOG.append(f'4-way stop: {len(cross)} carriageway crossings, 4 stop signs + ALL WAY plaques')
    c0=pn+np.array([-8,-10.0]);y0=float(Hs(np.array([c0]))[0]);mpost.cyl((c0[0],y0,c0[1]),0.04,3.3,6,1);panel(mbl8,c0,y0+2.9,1.4,0.32,math.pi/2)
emit('xstop','ext_stop',mstop,500);emit('xstop_back','ext_stop_back',mstopb,500);emit('xallway','ext_allway',mall,400);emit('xstreet188','ext_street_188',mbl8,400)
# power poles + fence along 190th St (west side)
mpole=M();mfence=M()
for name,R,hw,surf,lab,y,ph in roads:
    if lab!='190th Street': continue
    R2,s=resample(R,70.0);T_=np.gradient(R2,axis=0);T_/=np.linalg.norm(T_,axis=1)[:,None]+1e-9;L=np.c_[-T_[:,1],T_[:,0]]
    others=np.vstack([r[1] for r in roads if r[0]!=name]);tro=cKDTree(others)
    for i in range(len(R2)):
        p=R2[i]-L[i]*(hw+7)
        if tro.query(p)[0]<30: continue  # VR3: no poles at junctions/exits
        yy=float(Hs(np.array([p]))[0]) if p[1]<-2550 else -0.1
        mpole.cyl((p[0],yy-0.5,p[1]),0.15,11.5,7,3);mpole.box((p[0],yy+10.0,p[1]),(2.4,0.14,0.14),yaw=math.atan2(T_[i,1],-T_[i,0]),uvscale=1)
    R3,s3=resample(R,4.0);T_=np.gradient(R3,axis=0);T_/=np.linalg.norm(T_,axis=1)[:,None]+1e-9;L=np.c_[-T_[:,1],T_[:,0]];F=R3-L*(hw+10)
    keep=(F[:,1]<-1e9)&~np.array([any(pg.buffer(5).contains(sg.Point(p)) for _,pg,_,_ in lotpolys) for p in F])
    fy=np.array([float(Hs(np.array([p]))[0]) if p[1]<-2550 else -0.1 for p in F])
    for i in range(len(F)-1):
        if keep[i] and keep[i+1]:
            a,b=F[i],F[i+1];n=np.array([-(b-a)[1],0,(b-a)[0]]);n/=np.linalg.norm(n)+1e-9
            mfence.quad([[a[0],fy[i],a[1]],[b[0],fy[i+1],b[1]],[b[0],fy[i+1]+1.25,b[1]],[a[0],fy[i]+1.25,a[1]]],n,[(0,1),(1,1),(1,0),(0,0)])
            mfence.quad([[b[0],fy[i+1],b[1]],[a[0],fy[i],a[1]],[a[0],fy[i]+1.25,a[1]],[b[0],fy[i+1]+1.25,b[1]]],-n,[(1,1),(0,1),(0,0),(1,0)])
emit('xpoles','ext_wood',mpole,1200);emit('xposts','ext_metal',mpost,900);emit('xfence','ext_fence',mfence,350)
# lot light poles (unlit) at Love's / BP lots
mlp=M()
for nm,pg,surf,yl in lotpolys:
    if nm=='ne_yard': continue
    b=pg.bounds
    for gx_ in np.linspace(b[0]+15,b[2]-15,3):
        for gz_ in np.linspace(b[1]+15,b[3]-15,2):
            if pg.contains(sg.Point(gx_,gz_)): mlp.cyl((gx_,yl,gz_),0.12,10,6,2);mlp.box((gx_,yl+9.8,gz_),(1.2,0.25,0.5),uvscale=1)
emit('xlotlights','ext_metal',mlp,700)
# invisible walls (physics)
mwall=M()
def wall(P):
    P,_=resample(np.array(P,float),8.0)
    for a,b in zip(P[:-1],P[1:]):
        ya=float(Hs(np.array([a]))[0]);yb=float(Hs(np.array([b]))[0]);n=np.array([-(b-a)[1],0,(b-a)[0]]);n/=np.linalg.norm(n)
        mwall.quad([[a[0],ya-3,a[1]],[b[0],yb-3,b[1]],[b[0],yb+5,b[1]],[a[0],ya+5,a[1]]],n,[(0,1),(1,1),(1,0),(0,0)])
        mwall.quad([[b[0],yb-3,b[1]],[a[0],ya-3,a[1]],[a[0],ya+5,a[1]],[b[0],yb+5,b[1]]],-n,[(0,1),(1,1),(1,0),(0,0)])
wall([(WALLX,float(geo.zb(WALLX))),(WALLX,Z0)]);wall([(WALLX,Z0),(X0,Z0)]);wall([(X0,Z0),(X0,float(geo.zb(X0)))]);wall([(WALLX,float(geo.zb(WALLX))+0.5)]+[(x,float(geo.zb(x))+0.5) for x in np.linspace(WALLX+20,X1,10)])
emit('1WALL_EXT','ext_invisible',mwall)
# ---------------------------------------------------------------- write
TEXL=[(n,b) for n,b in TEX.items()]
out=f'{Z}/zw_ext.kn5';W.write_kn5(out,TEXL,MATS,MESH,rootname='zw_ext')
# physics-only / invisible meshes: castShadows 0, renderable 0 (like zw_rpm_physical); visual roads stay rendered
d=bytearray(open(out,'rb').read());_,nodes=K.scan(out);ninv=0
for name,o,l,c in nodes:
    if c==2 and name.startswith('1WALL_EXT'):
        q=o+l+5;d[q]=0;nv,=struct.unpack_from('<I',d,q+3);r=q+3+4+nv*44;ni,=struct.unpack_from('<I',d,r);r+=4+ni*2+8+4+4+16;d[r]=0;ninv+=1
open(out,'wb').write(bytes(d))
tris=sum(len(m['idx']) for m in MESH);LOG.append(f'zw_ext.kn5: {len(MESH)} meshes, {tris} tris, {len(TEXL)} textures, {os.path.getsize(out)/1e6:.1f} MB; invisible wall meshes {ninv}')
by={}
for m in MESH: k=m['name'].split('_')[0];by[k]=by.get(k,0)+len(m['idx'])
LOG.append('tris by group: '+', '.join(f'{k} {v}' for k,v in sorted(by.items(),key=lambda t:-t[1])))
json.dump(dict(lots=[(n,list(pg.exterior.coords),yl) for n,pg,_,yl in lotpolys],roads=[(n,R.tolist(),hw,s_,l_,ph) for n,R,hw,s_,l_,y,ph in roads]),open(f'{NO}/layout.json','w'))
open(f'{NO}/build_log.txt','w').write('\n'.join(LOG));print('\n'.join(LOG))
