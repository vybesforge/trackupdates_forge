"""Drag-strip end gantry billboards (z -606) as 2 sellable ad slots. Rewrites vf_i29_speedway/zw_vr5.kn5 (MODEL_9; it holds only
the 4 vr5_billboard_end_* panels) with one material + texture per billboard, same geometry as v1.0.4:
  vfboard_slot01 = east billboard (x -247..-242.5: big upper panel vr5_billboard_end_1 + small lower panel _end_0)
  vfboard_slot02 = west billboard (x -267..-262.3: upper _end_3 + lower _end_2)
Art 2048x1024 DXT1 'PLACE YOUR AD HERE' + slot label -> assets_src/brand/board_slotNN.png, embedded in the kn5 and copied to
vf_i29_speedway/extension/board_slotNN.dds (CSP SHADER_REPLACEMENT override, rotate ads without touching the kn5)."""
import json as _json
import sys,os,struct,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import kn5patch as K,kn5write as W,build_open_textures as B
from PIL import Image,ImageDraw,ImageFont
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));Z=f'{ROOT}/vf_i29_speedway';KN5=f'{Z}/zw_vr5.kn5'
FONT=f'{ROOT}/assets_src/brand/fonts/SpaceGrotesk-wght.ttf';BG=(2,6,15);CY=(41,213,233);MG=(191,51,138);TX=(232,236,245)
SLOTS={1:('vr5_billboard_end_0','vr5_billboard_end_1'),2:('vr5_billboard_end_2','vr5_billboard_end_3')}
def font(sz,w=700):
    f=ImageFont.truetype(FONT,sz)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
def art(slot):
    """v2 neutral style: light grey board, black frame bars, Space Grotesk"""
    Wd,H=2048,1024;BK=(14,14,16);im=Image.new('RGB',(Wd,H),(236,236,234));D=ImageDraw.Draw(im)
    D.rectangle([0,0,Wd,30],fill=BK);D.rectangle([0,H-30,Wd,H],fill=BK);D.rectangle([300,668,Wd-300,676],fill=(150,150,154))
    def ct(y,s,f,c):
        bb=D.textbbox((0,0),s,font=f);D.text(((Wd-(bb[2]-bb[0]))/2-bb[0],y-(bb[3]-bb[1])/2-bb[1]),s,font=f,fill=c)
    ct(250,'PLACE YOUR',font(210),BK);ct(500,'AD HERE',font(270),BK)
    ct(790,'Advertise: vybesforge.com',font(110,500),(40,40,44));ct(925,f'BILLBOARD SLOT {slot:02d}',font(56,600),(100,100,104))
    im.save(f'{ROOT}/assets_src/brand/board_slot{slot:02d}.png');a=np.array(im)
    return B.write_dds(np.dstack([a,np.full(a.shape[:2],255,np.uint8)]),'DXT1',11,None)
_bj=os.path.join(ROOT,'assets_src','ads','brands.json')
_SOLD={x for k,v in (_json.load(open(_bj)).items() if os.path.exists(_bj) else []) if not k.startswith('_') and not v.get('pending') for x in v.get('board_slots',[])}   # slots with advertiser art in extension/ (tools/make_ad.py): never overwritten
if __name__=='__main__':
    d=open(KN5,'rb').read();_,nodes=K.scan(KN5);M=W.read_materials(KN5);base=M.get('billboard_adhere') or M['vfboard_slot01'];mesh={}
    for name,o,l,c in nodes:
        if c!=2: continue
        q=o+l+8;nv,=struct.unpack_from('<I',d,q);V=np.frombuffer(d,'<f4',nv*11,q+4).reshape(nv,11).copy()
        q2=q+4+nv*44;ni,=struct.unpack_from('<I',d,q2);mesh[name]=(V,np.frombuffer(d,'<u2',ni,q2+4).reshape(-1,3).copy())
    assert sorted(mesh)==sorted(sum(SLOTS.values(),())),sorted(mesh)
    texs=[];mats=[];ME=[];os.makedirs(f'{Z}/extension',exist_ok=True)
    for s,names in SLOTS.items():
        tn=f'board_slot{s:02d}.dds';b=art(s);texs.append((tn,b));(None if s in _SOLD else open(f'{Z}/extension/{tn}','wb').write(b))
        mats.append(dict(name=f'vfboard_slot{s:02d}',shader=base['shader'],ab=0,at=0,dm=base['dm'],props=base['props'],samplers=[('txDiffuse',0,tn)]))
        for n in names: ME.append(dict(name=n,mat_index=len(mats)-1,verts=mesh[n][0],idx=mesh[n][1]))
    W.write_kn5(KN5,texs,mats,ME,rootname='zw_vr5');print('zw_vr5.kn5:',[(m['name'],mats[m['mat_index']]['name']) for m in ME])
