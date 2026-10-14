"""v16 previews: old staging tents -> 2 v2 ad tents (slots 19/20)."""
import sys,os,numpy as np
sys.path.insert(0,os.path.dirname(__file__))
import tents_v11_preview as P
from PIL import Image,ImageDraw
OUT='/workspace/tent_previews/v16_dragtents';os.makedirs(OUT,exist_ok=True);D='vf_i29_speedway/'
def crop(ms,box):
    x0,x1,z0,z1=box;return [m for m in ms if (m[1][:,0].max()>x0)&(m[1][:,0].min()<x1)&(m[1][:,2].max()>z0)&(m[1][:,2].min()<z1)]
def load_set(files):
    ms=[];tex={}
    for f in files: a,b=P.load(f);ms+=a;tex.update(b)
    return ms,tex
before=load_set(['/tmp/main_v15.kn5',D+'vf_roads.kn5','/tmp/vf_westlot_v15.kn5'])
after=load_set([D+'vf_i29_speedway.kn5',D+'vf_roads.kn5',D+'vf_westlot.kn5',D+'vf_dragtents.kn5'])
views=[('from_staging_road',(-298,1.6,-344),(-318,1.5,-344.5),60),('aerial',(-300,22,-330),(-318,0,-345),55),('topdown',(-318,60,-344+0.01),(-318,0,-344),60)]
for nm,e,t,f in views:
    ims=[P.render(crop(ms,(-420,-200,-480,-250)),tex,e,t,f,size=(900,600)) for ms,tex in (before,after)]
    im=Image.new('RGB',(1800,640),'white');im.paste(ims[0],(0,40));im.paste(ims[1],(900,40));d=ImageDraw.Draw(im)
    d.text((10,10),'BEFORE (v15): 3 old staging tents',fill='black');d.text((910,10),'AFTER: back tent removed, front 2 -> ad tents SLOT 19 / SLOT 20',fill='black');im.save(f'{OUT}/{nm}.png')
print(sorted(os.listdir(OUT)))
