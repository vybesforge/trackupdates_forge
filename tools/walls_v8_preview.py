"""v8 previews: painted drift barriers + tyre stacks (driver's view, aerial, close-ups, night)."""
import sys,os,numpy as np
sys.path.insert(0,os.path.dirname(__file__))
import tents_v11 as TV,tents_v11_preview as P,drift_course as DC
OUT='/workspace/tent_previews/v8_walls';os.makedirs(OUT,exist_ok=True)
fails,GY,RD=TV.verify();hat=RD[-2];xs,zs,H=RD[0],RD[1],RD[2]
G=(0,160,60,222,float(np.nanmin(H[(zs[:,None]>60)&(zs[:,None]<222)&(xs[None,:]>0)&(xs[None,:]<160)]))-0.03)
ms,tex=P.load();C=DC.course()
P.render(ms,tex,(78,45,60),(78,0,165),55,ground=G).save(f'{OUT}/aerial.png')
P.render(ms,tex,(78,45,60),(78,0,165),55,night=True,ground=G).save(f'{OUT}/aerial_night.png')
L=C['line'];i=len(L)//3;p0=L[i];p1=L[(i+14)%len(L)]
gl=lambda p:(G[0],G[1],G[2],G[3],hat(*p)-0.01)
P.render(ms,tex,(p0[0],hat(*p0)+1.15,p0[1]),(p1[0],hat(*p0)+1.0,p1[1]),70,ground=gl(p0)).save(f'{OUT}/drivers_view.png')
P.render(ms,tex,(p0[0],hat(*p0)+1.15,p0[1]),(p1[0],hat(*p0)+1.0,p1[1]),70,night=True,ground=gl(p0)).save(f'{OUT}/drivers_view_night.png')
w=max(C['walls'],key=len);m=w[len(w)//2];t=w[len(w)//2+3]-w[len(w)//2-3];t/=np.linalg.norm(t);n=np.array([t[1],-t[0]])
for sd,nm in ((1,'a'),(-1,'b')):
    e=m+sd*n*4.5-t*3;P.render(ms,tex,(e[0],hat(*e)+1.3,e[1]),(m[0],hat(*m)+0.4,m[1]),55,ground=gl(m)).save(f'{OUT}/barrier_closeup_{nm}.png')
c=C['clips'][2];e=(c[0]+3.2,hat(*c)+1.4,c[1]+2.4);P.render(ms,tex,e,(c[0],hat(*c)+0.35,c[1]),55,ground=gl(c)).save(f'{OUT}/tyre_stack_closeup.png')
print('ok',os.listdir(OUT))
