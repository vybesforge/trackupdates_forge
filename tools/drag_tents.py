"""v1.1.1 drag-area ad tents: the 3 old staging tents (tents001, main kn5) are removed (vertices collapsed, file size unchanged);
the 2 front ones (nearest the drag lanes) are replaced by v2 ad tents vftent_slot19/20 in vf_dragtents.kn5 (same design/art as slots 1-18).
Collision: vf_dragcol 1WALL_DRAG_STAGING_TENT (old 3 boxes) -> 1WALL_DRAG_VFTENT (4 leg posts per new tent).
Run: python3 tools/drag_tents.py   (then tools/west_lot.py to re-cut gravel around the new tents)"""
import os,sys,struct,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import tents_v11 as TV,kn5write as W,kn5patch as K,vr5_meshlib as ML,vismeshes as VM,physraster as PR
Z=TV.Z;MAIN=f'{Z}/vf_i29_speedway.kn5'
# old tents (centres from tents001 clusters): A (-325.0,-340.5) = back (furthest from the lanes at x -262..-242) -> removed
# B (-317.3,-340.6), C (-317.4,-347.8) = front -> replaced. opening faces +x (towards the lanes / staging road)
DRAG=[(19,-317.3,-340.6,-np.pi/2),(20,-325.0,-340.5,np.pi)]   # v1.1.2: slot20 moved from (-317.4,-347.9) to the old back-tent spot, opening south (+z) towards the apron
def ground(x,z,r=3.6):
    files=[f for f in os.listdir(Z) if f.endswith('.kn5') and f not in('vf_dragcol.kn5','vf_westlot.kn5','vf_dragtents.kn5')]
    box=(x-r,x+r,z-r,z+r);xs,zs,H,KEY,UP,names=PR.raster(PR.physmeshes(files,box),box,0.25)
    return float(np.nanmax(H)),float(np.nanmin(H))
def hide_old():
    d=bytearray(open(MAIN,'rb').read());n=0
    for m in VM.vismeshes(MAIN):
        if m['name']=='tents001':
            V=np.frombuffer(bytes(d[m['vo']:m['vo']+m['nv']*44]),'<f4').reshape(-1,11).copy();V[:,:3]=V[0,:3]*0+np.array([-325.0,-50.0,-340.5]);n=m['nv']
            d[m['vo']:m['vo']+m['nv']*44]=V.astype('<f4').tobytes()
    open(MAIN,'wb').write(bytes(d));print('tents001: %d vertices collapsed below ground (hidden, no collision)'%n)
def main():
    base=W.read_materials(f'{Z}/vf_tents.kn5')['vftent_slot01'];tm=W.read_materials(f'{Z}/vf_tents.kn5')
    texs=[(t,K.get_tex(f'{Z}/vf_tents.kn5',t)) for t in ('fabric_nm_v2.dds','fabric_maps.dds','NULL.dds','vft_black.dds','vft_sandbag.dds','vft_tabletop.dds','vr6_blob_rect.dds')]
    mats=[dict(name=k,**{a:tm[k][a] for a in('shader','ab','at','dm','props','samplers')}) for k in ('vftent_frame_black','vftent_sandbag','vftent_tabletop','vftent_shadow')]
    MI={'frame':0,'bag':1,'top':2,'shadow':3};meshes=[];posts=[]
    for s,x,z,yaw in DRAG:
        hi,lo=ground(x,z);big,small=TV.art(s);tn=f'tent_slot{s:02d}.dds';texs.append((tn,small))
        if s not in TV._SOLD: open(f'{TV.SKIN}/{tn}','wb').write(big)
        mats.append(dict(name=f'vftent_slot{s:02d}',shader=base['shader'],ab=0,at=0,dm=base['dm'],props=base['props'],
                         samplers=[('txDiffuse',0,tn),('txNormal',1,'fabric_nm_v2.dds'),('txMaps',2,'fabric_maps.dds'),('txDetail',3,'NULL.dds')]))
        parts=TV.canopy(x,z,lo,yaw,s,lift=hi-lo+0.025)
        meshes.append(dict(name=f'vftent_slot{s:02d}',mat_index=len(mats)-1,verts=parts['fab'][0],idx=parts['fab'][1],lod_out=0))
        for k in ('frame','bag','top'): meshes.append(dict(name=f'vftent_slot{s:02d}_{k}',mat_index=MI[k],verts=parts[k][0],idx=parts[k][1],lod_out=400))
        meshes.append(dict(name=f'vftent_slot{s:02d}_shadow',mat_index=3,verts=parts['shadow'][0],idx=parts['shadow'][1],lod_out=300,flags=(1,0,0)))
        for sx in(-1,1):
            for sz in(-1,1):
                c=np.array([sx*(TV.W_/2-0.03),sz*(TV.D_/2-0.03)]);cy,sy=np.cos(yaw),np.sin(yaw)
                px,pz=x+c[0]*cy+c[1]*sy,z-c[0]*sy+c[1]*cy;posts.append(ML.box((px,lo+TV.EAVE/2,pz),(0.3,TV.EAVE+0.2,0.3)))
        print(f'slot{s}: ({x},{z}) ground {lo:.3f}..{hi:.3f} yaw {np.degrees(yaw):.0f}')
    W.write_kn5(f'{Z}/vf_dragtents.kn5',texs,mats,meshes,rootname='vf_dragtents');print('vf_dragtents.kn5',os.path.getsize(f'{Z}/vf_dragtents.kn5')//1024,'KB')
    # collision: drop the old staging-tent boxes, add the new leg posts
    col=f'{Z}/vf_dragcol.kn5';cm=W.read_materials(col)['vfcol_invisible'];out=[]
    for m in VM.vismeshes(col):
        if m['name'] in('1WALL_DRAG_STAGING_TENT','1WALL_DRAG_VFTENT'): continue
        out.append(dict(name=m['name'],mat_index=0,verts=m['V'].astype('<f4'),idx=m['I'].astype('<u2'),lod_out=0,flags=(0,0,0),renderable=0))
    V,I=ML.merge(posts);out.append(dict(name='1WALL_DRAG_VFTENT',mat_index=0,verts=V,idx=I,lod_out=0,flags=(0,0,0),renderable=0))
    W.write_kn5(col,[('vfcol_null.dds',K.get_tex(col,'vfcol_null.dds'))],[dict(name='vfcol_invisible',**{a:cm[a] for a in('shader','ab','at','dm','props','samplers')})],out,rootname='vf_dragcol')
    print('vf_dragcol: STAGING_TENT removed, VFTENT %d posts'%len(posts))
    hide_old()
    for fn in('models_main.ini','models_short.ini'):
        p=f'{Z}/{fn}';t=open(p).read()
        if 'vf_dragtents.kn5' in t: continue
        import re;n=max(int(v) for v in re.findall(r'\[MODEL_(\d+)\]',t))+1
        open(p,'w',newline='\n').write(t.rstrip('\n')+f'\n\n[MODEL_{n}]\nFILE=vf_dragtents.kn5\nPOSITION=0,0,0\nROTATION=0,0,0\nSCALE=1,1,1\n');print(fn,'MODEL',n)
if __name__=='__main__': main()
