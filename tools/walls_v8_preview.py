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
# entrance lane
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
A=TV.open_path(TV.APPROACH);fig,ax=plt.subplots(figsize=(10,8));ax.set_facecolor('#cfcfc8')
ax.plot(C['line'][:,0],C['line'][:,1],'r-',lw=2,label='drift line')
for w in C['walls']: ax.plot(w[:,0],w[:,1],'-',c='#c01818',lw=3)
ta=np.gradient(A,axis=0);ta/=np.linalg.norm(ta,axis=1,keepdims=True);na=np.stack([ta[:,1],-ta[:,0]],1)
for sd in (-1,1): ax.plot(*(A+sd*3.5*na).T,'w-',lw=2)
ax.plot(*A.T,'k:',lw=1,label='entrance lane centre (painted edges + chevrons, cones)');pits=RD[5]
ax.plot([p[0] for p in pits],[p[2] for p in pits],'s',c='navy',ms=6,label='AC_PIT spawns');ax.plot(RD[6][:,0],RD[6][:,1],c='orange',lw=2,label='spawn exit route')
ax.annotate('DRIFT ENTRY',A[len(A)*3//4],fontsize=9,weight='bold');ax.set_xlim(-5,120);ax.set_ylim(40,140);ax.set_aspect('equal');ax.legend(fontsize=7,loc='upper right')
ax.set_title('v8 entrance lane: spawn rows -> drift entry');fig.savefig(f'{OUT}/entry_topdown.png',dpi=110)
gy=hat(70,83)
P.render(ms,tex,(70,gy+1.15,84),(48,gy+0.3,104),70,ground=gl((70,83))).save(f'{OUT}/entry_from_spawn.png')
P.render(ms,tex,(76,gy+1.15,89),(50,gy+0.5,104),70,ground=gl((70,83))).save(f'{OUT}/entry_drivers_view.png')
print('entry ok')
