"""v12 west-lot previews: before/after top-down + driver's views (190th St access road, lot)."""
import sys,os,numpy as np
sys.path.insert(0,os.path.dirname(__file__))
import tents_v11_preview as P
from PIL import Image,ImageDraw
OUT='/workspace/tent_previews/v12_west_lot';os.makedirs(OUT,exist_ok=True);D='vf_i29_speedway/'
def crop(ms,box):
    x0,x1,z0,z1=box;return [m for m in ms if (m[1][:,0].max()>x0)&(m[1][:,0].min()<x1)&(m[1][:,2].max()>z0)&(m[1][:,2].min()<z1)]
def load_set(files):
    ms=[];tex={}
    for f in files:
        a,b=P.load(f);ms+=a;tex.update(b)
    return ms,tex
before=load_set([D+'vf_i29_speedway.kn5',D+'vf_ext.kn5','/tmp/vf_roads_v11.kn5'])
after=load_set([D+'vf_i29_speedway.kn5',D+'vf_ext.kn5',D+'vf_roads.kn5',D+'vf_westlot.kn5'])
def topdown(ms,tex,c,ext,size):
    return P.render(crop(ms,(c[0]-ext,c[0]+ext,c[1]-ext*1.8,c[1]+ext*1.8)),tex,(c[0],ext*2.0,c[1]+0.01),(c[0],0,c[1]),60,size=size)
for nm,c,ext in (('north',(-345,-830),75),('south',(-345,-520),75)):
    b=topdown(*before,c,ext,(900,1000));a=topdown(*after,c,ext,(900,1000))
    im=Image.new('RGB',(1800,1040),'white');im.paste(b,(0,40));im.paste(a,(900,40));d=ImageDraw.Draw(im)
    d.text((20,10),f'BEFORE (v11 roads-concrete) west lot {nm}',fill='black');d.text((920,10),f'AFTER (v12) west lot {nm}: 190th access concrete, dirt=GRAVEL',fill='black')
    im.save(f'{OUT}/topdown_before_after_{nm}.png')
import west_lot as WL
q,Pc,t,nn=WL.cline(WL.WR)
def onc(z):
    i=int(np.argmin(abs(Pc[:,1]-z)));return tuple(Pc[i])
views=[('lot_access_road_north',onc(-866),onc(-700)),('lot_access_road_south',onc(-640),onc(-480)),
       ('lot_from_B_west',(-385,-800),(-330,-780)),('lot_middle',(-345,-650),(-345,-520))]
for nm,e,tg in views:
    for tag,(ms,tex) in (('before',before),('after',after)):
        sub=crop(ms,(min(e[0],tg[0])-120,max(e[0],tg[0])+120,min(e[1],tg[1])-120,max(e[1],tg[1])+120))
        ys=[m[1][np.argmin(np.hypot(m[1][:,0]-e[0],m[1][:,2]-e[1])),1] for m in sub if m[0][0]=='1' and np.hypot(m[1][:,0]-e[0],m[1][:,2]-e[1]).min()<4]
        g=max(ys) if ys else 0
        P.render(sub,tex,(e[0],g+1.15,e[1]),(tg[0],g+0.6,tg[1]),70).save(f'{OUT}/drivers_view_{nm}_{tag}.png')
print(sorted(os.listdir(OUT)))
