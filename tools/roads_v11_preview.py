"""v11 roads previews: before/after top-down + driver's views of the concrete roads."""
import sys,os,numpy as np
sys.path.insert(0,os.path.dirname(__file__))
import tents_v11_preview as P
from PIL import Image,ImageDraw
OUT='/workspace/tent_previews/v11_roads';os.makedirs(OUT,exist_ok=True);D='vf_i29_speedway/'
def crop(ms,box):
    x0,x1,z0,z1=box;return [m for m in ms if (m[1][:,0].max()>x0)&(m[1][:,0].min()<x1)&(m[1][:,2].max()>z0)&(m[1][:,2].min()<z1)]
bms,btex=P.load(os.environ.get('VF_MAIN_SRC','/tmp/main_before.kn5'));ams,atex=P.load(D+'vf_i29_speedway.kn5')
rms,rtex=P.load(D+'vf_roads.kn5');ams+=rms;atex.update(rtex)
def tops(ms,tex,tag):
    out=[]
    for nm,c,ext in (('south',(-100,245),300),('return',(-298,-760),220)):
        out.append(P.render(crop(ms,(c[0]-ext,c[0]+ext,c[1]-ext,c[1]+ext)),tex,(c[0],ext*1.9,c[1]+0.01),(c[0],0,c[1]),60,size=(1200,1000)))
    return out
B=tops(bms,btex,'before');A=tops(ams,atex,'after')
for i,nm in enumerate(('south_road','return_road')):
    im=Image.new('RGB',(2400,1040),'white');im.paste(B[i],(0,40));im.paste(A[i],(1200,40));d=ImageDraw.Draw(im)
    d.text((20,10),f'BEFORE (v1.1.0) {nm}',fill='black');d.text((1220,10),f'AFTER (roads-concrete) {nm}',fill='black');im.save(f'{OUT}/topdown_before_after_{nm}.png')
import roads_concrete as R
q,Pc,t,nn=R.centreline()
def onc(x):
    i=int(np.argmin(abs(Pc[:,0]-x)));return tuple(Pc[i])
views=[('south_road_west',onc(-330),onc(-180)),('south_road_east',onc(-20),onc(130)),('return_road',(-298,-955),(-298,-750))]
for nm,e,tg in views:
    for tag,ms,tex in (('before',bms,btex),('after',ams,atex)):
        y=float(np.interp(e[0],Pc[:,0],np.zeros(len(Pc)))) if 0 else None
        sub=crop(ms,(min(e[0],tg[0])-120,max(e[0],tg[0])+120,min(e[1],tg[1])-120,max(e[1],tg[1])+120))
        ys=[m[1][np.argmin(np.hypot(m[1][:,0]-e[0],m[1][:,2]-e[1])),1] for m in sub if np.hypot(m[1][:,0]-e[0],m[1][:,2]-e[1]).min()<6]
        g=max(ys) if ys else 0
        P.render(sub,tex,(e[0],g+1.15,e[1]),(tg[0],g+0.6,tg[1]),70).save(f'{OUT}/drivers_view_{nm}_{tag}.png')
print(sorted(os.listdir(OUT)))
