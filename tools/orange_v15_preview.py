"""v15 previews: Dylan's orange loop -> concrete; before/after top-down, orange trace overlay, driver's views."""
import sys,os,numpy as np
sys.path.insert(0,os.path.dirname(__file__))
import tents_v11_preview as P
from PIL import Image,ImageDraw
OUT='/workspace/tent_previews/v15_orange';os.makedirs(OUT,exist_ok=True);D='vf_i29_speedway/'
def crop(ms,box):
    x0,x1,z0,z1=box;return [m for m in ms if (m[1][:,0].max()>x0)&(m[1][:,0].min()<x1)&(m[1][:,2].max()>z0)&(m[1][:,2].min()<z1)]
def load_set(files):
    ms=[];tex={}
    for f in files: a,b=P.load(f);ms+=a;tex.update(b)
    return ms,tex
base=[D+'vf_i29_speedway.kn5',D+'vf_ext.kn5']
before=load_set(base+['/tmp/vf_roads_v14.kn5','/tmp/vf_westlot_v14.kn5']);after=load_set(base+[D+'vf_roads.kn5',D+'vf_westlot.kn5'])
c=(-322,-600);H_=330;W,Hh=560,1100;eye=np.array([c[0],H_,c[1]+0.01]);tgt=np.array([c[0],0,c[1]])
def proj(pts):
    f=tgt-eye;f/=np.linalg.norm(f);r=np.cross(f,[0,1,0]);r/=np.linalg.norm(r);u=np.cross(r,f);fl=0.5*W/np.tan(np.radians(60)/2)
    q=pts-eye;return np.stack([W/2+fl*(q@r)/(q@f),Hh/2-fl*(q@u)/(q@f)],1)
td=lambda ms,tex:P.render(crop(ms,(-420,-220,-1000,-200)),tex,tuple(eye),tuple(tgt),60,size=(W,Hh))
b=td(*before);a=td(*after)
O=np.load('/tmp/orange15.npy');pp=proj(np.c_[O[:,0],np.zeros(len(O)),O[:,1]])
ov=a.copy();d=ImageDraw.Draw(ov,'RGBA')
for x,y in pp[::2]: d.rectangle([x-1,y-1,x+1,y+1],fill=(255,120,0,150))
im=Image.new('RGB',(3*W,Hh+40),'white');im.paste(b,(0,40));im.paste(a,(W,40));im.paste(ov,(2*W,40));d=ImageDraw.Draw(im)
d.text((10,10),'BEFORE (v14 71d1280)',fill='black');d.text((W+10,10),'AFTER (v15): orange loop in concrete',fill='black');d.text((2*W+10,10),"AFTER + Dylan's orange trace",fill='black')
im.save(f'{OUT}/topdown_before_after_orange.png');ov.save(f'{OUT}/orange_trace_overlay.png')
def drv(ms,tex,e,tg):
    sub=crop(ms,(-480,-220,-1000,-250));ys=[m[1][np.argmin(np.hypot(m[1][:,0]-e[0],m[1][:,2]-e[1])),1] for m in sub if m[0][0]=='1' and np.hypot(m[1][:,0]-e[0],m[1][:,2]-e[1]).min()<4]
    g=max(ys) if ys else 0;return P.render(sub,tex,(e[0],g+1.15,e[1]),(tg[0],g+0.6,tg[1]),70,size=(900,600))
for nm,e,tg in (('link624_eastbound',(-344,-624),(-298,-624)),('link800_eastbound',(-344,-801),(-298,-801)),('return_ext_southbound',(-298,-560),(-300,-340))):
    bb=drv(*before,e,tg);aa=drv(*after,e,tg);im=Image.new('RGB',(1800,640),'white');im.paste(bb,(0,40));im.paste(aa,(900,40))
    d=ImageDraw.Draw(im);d.text((10,10),'BEFORE (v14) '+nm,fill='black');d.text((910,10),'AFTER (v15) '+nm,fill='black');im.save(f'{OUT}/drivers_view_{nm}.png')
print(sorted(os.listdir(OUT)))
