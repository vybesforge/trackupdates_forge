"""VR5b extras (rerunnable: reads /workspace/rpotm/backup/pre_vr5b/zw_rpm.kn5 -> zw_rpm/zw_rpm.kn5, writes zw_rpm/zw_vr5.kn5 = MODEL_9).
1. Drag-strip end gantry (z -606): the 4 ad panels of adds_drag_SUB0 (rpm_adds_01 atlas) are collapsed; new panels at the
   same corners show own 'PLACE YOUR AD HERE' art (VF tent placeholder style). Atlas untouched for the other boards.
2. Exits B/C west extension: tools/drag_exit.py. Here: the north-extension power pole standing in the new B lane
   (xpoles, at x -382, z -802.8, zw_ext.kn5 from /workspace/rpotm/backup/pre_vr5/) is moved 6 m south (z -808.8).
3. Track entrance (west gate -> drag staging lot): ambulance (x -283..-276, z -333..-330) and the food kiosk
   drag_kiosk_SUB0..3 (x -290..-287, z -346..-340; the 'taco truck') collapsed. New generic unbranded 4-door crew-cab
   pickup (Silverado-like proportions, 6.0 x 2.03 x 1.95 m) parked in the ambulance spot, nose -x (toward the gate).
4. Two static people (1.78 / 1.70 m) under the open scrutineering shed (paddock_scrut, x 87..96, z 13..21) next to the
   large green paddock building. All new props are visual only (no physics)."""
import sys,os,struct,numpy as np
sys.path.insert(0,os.path.dirname(__file__));import kn5patch as K,kn5write as W,vr5_meshlib as L,build_open_textures as B
from PIL import Image,ImageDraw,ImageFont
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));Z=f'{ROOT}/zw_rpm';SRC='/workspace/rpotm/backup/pre_vr5b/zw_rpm.kn5'
FONT='/workspace/rpotm/brand/fonts/SpaceGrotesk%5Bwght%5D.ttf';G=-0.10
BG=(2,6,15);CY=(41,213,233);MG=(191,51,138);TX=(232,236,245)
def font(sz,w=700):
    f=ImageFont.truetype(FONT,sz)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
def ad_art():
    Wd,H=1024,512;rng=np.random.default_rng(3);n=rng.normal(0,1,(H//4,Wd//4));n=np.array(Image.fromarray(((n*20)+128).clip(0,255).astype(np.uint8)).resize((Wd,H)),np.float32)-128
    im=Image.fromarray(np.clip(np.array(BG,np.float32)+n[...,None]*0.12+6,0,255).astype(np.uint8));D=ImageDraw.Draw(im)
    D.rectangle([0,0,Wd,14],fill=MG);D.rectangle([0,20,Wd,28],fill=CY);D.rectangle([0,H-28,Wd,H-20],fill=CY);D.rectangle([0,H-14,Wd,H],fill=MG)
    def ct(y,s,f,c):
        bb=D.textbbox((0,0),s,font=f);D.text(((Wd-(bb[2]-bb[0]))/2-bb[0],y-(bb[3]-bb[1])/2-bb[1]),s,font=f,fill=c)
    ct(150,'PLACE YOUR',font(118),TX);ct(290,'AD HERE',font(150),CY);D.rectangle([300,385,724,391],fill=MG);ct(435,'ADVERTISE AT I-29 SPEEDWAY',font(34,500),TX)
    im.save(f'{ROOT}/assets_src/brand/billboard_adhere.png');a=np.array(im);return B.write_dds(np.dstack([a,np.full(a.shape[:2],255,np.uint8)]),'DXT1',10,None)
def collapse(d,o,l,sel):
    q=o+l+8;nv,=struct.unpack_from('<I',d,q);V=np.frombuffer(bytes(d[q+4:q+4+nv*44]),'<f4').reshape(nv,11).copy();k=sel(V)
    if k.any(): V[k,:3]=V[k][0,:3];d[q+4:q+4+nv*44]=V.tobytes()
    return V,int(k.sum())
def pickup(cx,cz,rot):
    """parts dict material->list of (V,I). Local: +x = front, y up, z = right side. 6.0 long, 2.03 wide."""
    P={'paint':[],'trim':[],'glass':[],'chrome':[],'tire':[],'rim':[],'light':[],'tail':[]}
    b=lambda m,c,s: P[m].append(L.box(c,s))
    b('paint',(0.0,0.62,0),(5.6,0.62,1.98))             # lower body, y 0.31..0.93
    b('paint',(1.95,1.08,0),(1.7,0.30,1.94))           # hood  y 0.93..1.23
    b('paint',(0.25,1.25,0),(1.75,0.64,1.92))          # cab lower (doors) to 1.57
    b('paint',(0.12,1.83,0),(2.0,0.09,1.80))           # roof
    b('glass',(0.12,1.58,0),(2.06,0.42,1.76))          # greenhouse (windows all round)
    b('paint',(0.12,1.58,0),(0.10,0.44,1.84))          # B-pillar
    b('paint',(-1.85,1.12,0.94),(2.3,0.38,0.10));b('paint',(-1.85,1.12,-0.94),(2.3,0.38,0.10))   # bed sides
    b('paint',(-2.95,1.12,0),(0.10,0.38,1.98))         # tailgate
    b('trim',(-1.85,0.95,0),(2.2,0.04,1.78))           # bed floor
    b('chrome',(2.82,0.92,0),(0.10,0.42,1.6))          # grille surround
    b('trim',(2.86,0.92,0),(0.04,0.32,1.3))            # grille
    b('chrome',(2.88,0.48,0),(0.18,0.20,2.0));b('chrome',(-3.02,0.50,0),(0.14,0.18,2.0))  # bumpers
    b('light',(2.84,1.02,0.82),(0.06,0.14,0.30));b('light',(2.84,1.02,-0.82),(0.06,0.14,0.30))
    b('tail',(-3.01,1.12,0.88),(0.04,0.34,0.14));b('tail',(-3.01,1.12,-0.88),(0.04,0.34,0.14))
    b('trim',(0.9,1.52,1.00),(0.18,0.14,0.10));b('trim',(0.9,1.52,-1.00),(0.18,0.14,0.10))  # mirrors
    b('trim',(0.0,0.40,0.99),(5.0,0.12,0.04));b('trim',(0.0,0.40,-0.99),(5.0,0.12,0.04))   # rocker/steps
    for wx in(1.85,-1.95):
        for sz in(1,-1):
            P['tire'].append(L.cyl((wx,0.40,sz*0.86-(0.13 if sz>0 else -0.13)*0 - (0.0)),0.40,0.27*sz if sz>0 else -0.27,'z',16) if False else L.cyl((wx,0.40,(0.73 if sz>0 else -1.0)),0.40,0.27,'z',16))
            P['rim'].append(L.disc((wx,0.40,1.005 if sz>0 else -1.005),0.24,(0,0,sz),12))
    out={}
    for m,ps in P.items():
        V,I=L.merge(ps);V,I=L.xform((V,I),rot,(cx,G+0.0,cz));out[m]=(V,I)
    return out
def person(cx,cz,rot,h=1.78,shirt='shirt_a'):
    s=h/1.78;P={shirt:[],'jeans':[],'skin':[],'shoes':[],'hair':[]}
    b=lambda m,c,sz: P[m].append(L.box(np.array(c)*s,np.array(sz)*s))
    b('shoes',(0,0.04,0.11),(0.26,0.08,0.11));b('shoes',(0.03,0.04,-0.11),(0.26,0.08,0.11))
    b('jeans',(0,0.47,0.10),(0.15,0.80,0.15));b('jeans',(0,0.47,-0.10),(0.15,0.80,0.15));b('jeans',(0,0.92,0),(0.22,0.14,0.38))
    b(shirt,(0,1.21,0),(0.24,0.52,0.42))
    b(shirt,(0,1.33,0.27),(0.12,0.24,0.11));b(shirt,(0,1.33,-0.27),(0.12,0.24,0.11))
    b('skin',(0.03,1.05,0.27),(0.09,0.34,0.08));b('skin',(0.03,1.05,-0.27),(0.09,0.34,0.08))
    b('skin',(0,1.50,0),(0.10,0.07,0.10))
    P['skin'].append(L.cyl(np.array((0,1.54,0))*s,0.105*s,0.22*s,'y',12))
    b('hair',(0,1.77,0),(0.22,0.035,0.22))
    out={}
    for m,ps in P.items():
        V,I=L.merge(ps);out[m]=L.xform((V,I),rot,(cx,G,cz))
    return out
if __name__=='__main__':
    d=bytearray(open(SRC,'rb').read());panels=None
    for name,o,l,c in K.scan(SRC)[1]:
        if c!=2: continue
        if name=='adds_drag_SUB0':
            V0=np.frombuffer(bytes(d[o+l+12:o+l+12+struct.unpack_from('<I',d,o+l+8)[0]*44]),'<f4').reshape(-1,11).copy()
            panels=V0[V0[:,2]<-600].copy();print('end-gantry ad verts',collapse(d,o,l,lambda V:V[:,2]<-600)[1])
        if name.startswith('ambulances_SUB'): print(name,'entrance ambulance verts',collapse(d,o,l,lambda V:(V[:,0]>-284)&(V[:,0]<-275)&(V[:,2]>-334)&(V[:,2]<-329.5))[1])
        if name.startswith('drag_kiosk_SUB'): print(name,'kiosk verts',collapse(d,o,l,lambda V:(V[:,0]>-292)&(V[:,0]<-286)&(V[:,2]>-347)&(V[:,2]<-339))[1])
    open(f'{Z}/zw_rpm.kn5','wb').write(bytes(d))
    ESRC='/workspace/rpotm/backup/pre_vr5/zw_rpm/zw_ext.kn5';e=bytearray(open(ESRC,'rb').read())
    for name,o,l,c in K.scan(ESRC)[1]:
        if c==2 and name=='xpoles':
            q=o+l+8;nv,=struct.unpack_from('<I',e,q);V=np.frombuffer(bytes(e[q+4:q+4+nv*44]),'<f4').reshape(nv,11).copy()
            k=np.hypot(V[:,0]+382,V[:,2]+802.8)<2.5;V[k,2]-=6.0;e[q+4:q+4+nv*44]=V.tobytes();print('pole verts moved',int(k.sum()))
    open(f'{Z}/zw_ext.kn5','wb').write(bytes(e))
    # --- textures / materials
    T=[('billboard_adhere.dds',ad_art())]
    cols={'paint':(28,38,58),'trim':(18,18,20),'glass':(25,32,38),'chrome':(175,178,182),'tire':(22,22,22),'rim':(150,152,155),
          'light':(235,235,225),'tail':(150,14,12),'shirt_a':(40,90,160),'shirt_b':(170,40,40),'jeans':(40,52,80),'skin':(196,150,120),'shoes':(30,28,26),'hair':(45,32,22)}
    for k,cv in cols.items(): T.append((f'vr5_{k}.dds',L.solid_dds(cv)))
    PP=W.read_materials(SRC);tpl=next(m for m in PP.values() if m['shader']=='ksPerPixel')['props']
    mats=[dict(name='billboard_adhere',shader='ksPerPixel',ab=0,at=0,dm=0,props=L.props(tpl,ksAmbient=0.45,ksDiffuse=0.45,ksSpecular=0.05,ksSpecularEXP=10,ksEmissive=(0,0,0)),samplers=[('txDiffuse',0,'billboard_adhere.dds')])]
    spec={'paint':(0.6,40),'glass':(0.9,120),'chrome':(0.8,80),'light':(0.6,60),'tail':(0.5,40),'rim':(0.6,40)}
    for k in cols:
        sp,ex=spec.get(k,(0.08,10))
        mats.append(dict(name=f'vr5_{k}',shader='ksPerPixel',ab=0,at=0,dm=0,props=L.props(tpl,ksAmbient=0.45,ksDiffuse=0.45,ksSpecular=sp,ksSpecularEXP=ex,ksEmissive=(0,0,0)),samplers=[('txDiffuse',0,f'vr5_{k}.dds')]))
    mi={m['name']:i for i,m in enumerate(mats)};ME=[]
    # --- billboards: 4 quads from the original corners (each group of 4 verts in order), +1 cm toward the viewer (+z)
    for gi in range(4):
        q=panels[gi*4:gi*4+4,:3].astype(float);x0,x1=q[:,0].min(),q[:,0].max();y0,y1=q[:,1].min(),q[:,1].max();zc=q[:,2].mean()+0.01
        V,I=L.quad((x0,y0,zc),(x1,y0,zc),(x1,y1,zc),(x0,y1,zc),uv=((0,1),(1,1),(1,0),(0,0)))
        ME.append(dict(name=f'vr5_billboard_end_{gi}',mat_index=mi['billboard_adhere'],verts=V.astype('<f4'),idx=I.astype('<u2')))
    # VR6: the blocky pickup is replaced by the Blender-modelled one in zw_vr6.kn5 (tools/vr6_props.py)
    # VR7: the 2 simple VR5b figures are replaced by recoloured corner-worker figures (tools/vr7_people.py -> zw_vr6.kn5)
    for pi,(x,z,r,h,sh) in enumerate([]):
        for m,(V,I) in person(x,z,r,h,sh).items(): ME.append(dict(name=f'vr5_person{pi}_{m}',mat_index=mi[f'vr5_{m}'],verts=V,idx=I))
    W.write_kn5(f'{Z}/zw_vr5.kn5',T,mats,ME,rootname='zw_vr5');print('zw_vr5.kn5',len(ME),'meshes')
    for ini in('models_main.ini','models_short.ini'):
        p=f'{Z}/{ini}';s=open(p).read()
        if 'zw_vr5.kn5' not in s: open(p,'a').write('\n[MODEL_9]\nFILE=zw_vr5.kn5\nPOSITION=0,0,0\nROTATION=0,0,0\n')
