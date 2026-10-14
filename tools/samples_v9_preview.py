"""v9: previews of the sold sample tents with skins/default overrides applied (as AC does by texture name)."""
import sys,os,glob,numpy as np
from PIL import Image
sys.path.insert(0,os.path.dirname(__file__))
import tents_v11 as TV,tents_v11_preview as P
OUT=sys.argv[1] if len(sys.argv)>1 else '/workspace/tent_previews/v9_samples';os.makedirs(OUT,exist_ok=True)
fails,GY,RD=TV.verify();xs,zs,H=RD[0],RD[1],RD[2]
G=(0,160,60,222,float(np.nanmin(H[(zs[:,None]>60)&(zs[:,None]<222)&(xs[None,:]>0)&(xs[None,:]<160)]))-0.03)
ms,tex=P.load()
for f in glob.glob(f'{TV.SKIN}/*.dds'):
    tn=os.path.basename(f)
    if tn in tex: tex[tn]=np.array(Image.open(f).convert('RGB').resize((1024,1024)),np.float32)/255
for s,x,z,yaw in TV.SLOTS:
    if s in (13,18,1,5,9):
        P.render(ms,tex,(x-11*np.sin(yaw),1.7+GY[s],z-11*np.cos(yaw)),(x,1.6+GY[s],z),60,ground=G).save(f'{OUT}/tent_slot{s:02d}.png')
P.render(ms,tex,(150,30,90),(70,0,160),55,ground=G).save(f'{OUT}/aerial_se.png')
P.render(ms,tex,(78,55,40),(78,0,160),55,ground=G).save(f'{OUT}/aerial.png')
print(sorted(os.listdir(OUT)))
