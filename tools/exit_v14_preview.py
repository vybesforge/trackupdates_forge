"""v14 previews: west-lot exit to 190th St (north end)."""
import sys,os,numpy as np
sys.path.insert(0,os.path.dirname(__file__))
import tents_v11_preview as P
from PIL import Image,ImageDraw
OUT='/workspace/tent_previews/v14_exit';os.makedirs(OUT,exist_ok=True);D='vf_i29_speedway/'
def crop(ms,box):
    x0,x1,z0,z1=box;return [m for m in ms if (m[1][:,0].max()>x0)&(m[1][:,0].min()<x1)&(m[1][:,2].max()>z0)&(m[1][:,2].min()<z1)]
def load_set(files):
    ms=[];tex={}
    for f in files: a,b=P.load(f);ms+=a;tex.update(b)
    return ms,tex
base=[D+'vf_i29_speedway.kn5',D+'vf_ext.kn5']
before=load_set(base+[os.environ.get('V12_ROADS','/tmp/vf_roads_v13.kn5'),os.environ.get('V12_LOT','/tmp/vf_westlot_v13.kn5')])
after=load_set(base+[D+'vf_roads.kn5',D+'vf_westlot.kn5'])
def pair(fn,title,render):
    b=render(*before);a=render(*after);w,h=b.size;im=Image.new('RGB',(2*w,h+40),'white');im.paste(b,(0,40));im.paste(a,(w,40))
    d=ImageDraw.Draw(im);d.text((20,10),'BEFORE (v13 c52ee7a) '+title,fill='black');d.text((w+20,10),'AFTER (v14) '+title,fill='black');im.save(f'{OUT}/{fn}')
c=(-362,-845);ext=45
pair('topdown_before_after_exit.png','west-lot north exit to 190th St',lambda ms,tex:P.render(crop(ms,(c[0]-ext*1.6,c[0]+ext*1.6,c[1]-ext,c[1]+ext)),tex,(c[0],ext*2.2,c[1]+0.01),(c[0],0,c[1]),60,size=(1000,900)))
def drv(ms,tex,e,tg):
    sub=crop(ms,(-480,-220,-1000,-700));ys=[m[1][np.argmin(np.hypot(m[1][:,0]-e[0],m[1][:,2]-e[1])),1] for m in sub if m[0][0]=='1' and np.hypot(m[1][:,0]-e[0],m[1][:,2]-e[1]).min()<4]
    g=max(ys) if ys else 0;return P.render(sub,tex,(e[0],g+1.15,e[1]),(tg[0],g+0.6,tg[1]),70,size=(900,600))
pair('drivers_view_exit_from_lot.png',"driver's view: lot road -> exit -> 190th St",lambda ms,tex:drv(ms,tex,(-344.5,-800),(-360,-845)))
pair('drivers_view_exit_westbound.png',"driver's view westbound along the exit",lambda ms,tex:drv(ms,tex,(-350,-845),(-400,-845.5)))
print(sorted(os.listdir(OUT)))
