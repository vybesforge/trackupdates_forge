"""Previews for the 'Paddock Drift' camera set: one render per camera position + top-down map of positions, aim and the
spline windows each camera got (main layout). -> /workspace/tent_previews/v10_cams/"""
import os,sys,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import paddock_cams as PC,tents_v11 as TV,tents_v11_preview as PV,drift_course as DC
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
OUT='/workspace/tent_previews/v10_cams';os.makedirs(OUT,exist_ok=True)
fails,GY,(xs,zs,H,KEY,names,pits,path,hat,_R)=TV.verify(lambda s:None)
sp,used=PC.build('main');L=DC.LINE;active={u[0] for u in used}
ms,tex=PV.load();G=(-20,170,60,235,float(np.nanmin(H[(zs[:,None]>60)&(zs[:,None]<222)&(xs[None,:]>0)&(xs[None,:]<160)]))-0.03)
for nm,pos,aim,mount in PC.CAMS:
    fv=[u for u in used if u[0]==nm];f=np.mean([(u[3]+u[4])/2 for u in fv]) if fv else 40
    PV.render(ms,tex,pos,(aim[0],PC.G+0.8,aim[1]),f,ground=G).save(f'{OUT}/cam_{nm}.png')
fig,ax=plt.subplots(figsize=(11,10),dpi=130);ax.set_facecolor('#cfcfc8')
cmap=plt.get_cmap('tab10');col={c[0]:cmap(i) for i,c in enumerate(PC.CAMS)}
own=np.full(len(L),None,object)
for nm,lo,hi,*_ in used: own[(sp>=lo)&(sp<hi)]=nm
for i in range(len(L)-1): ax.plot(L[i:i+2,0],L[i:i+2,1],c=col[own[i]] if own[i] else 'k',lw=4)
for w in DC.course()['walls']: ax.plot(w[:,0],w[:,1],c='#c01818',lw=1.5)
for s,x,z,yaw in TV.SLOTS: ax.add_patch(plt.Rectangle((x-3,z-3),6,6,fc='#3a3b3e'))
for nm,pos,aim,mount in PC.CAMS:
    c=col[nm];ax.scatter(pos[0],pos[2],s=90,marker='^',color=c,edgecolors='k',zorder=6);ax.annotate('',xy=aim,xytext=(pos[0],pos[2]),arrowprops=dict(arrowstyle='->',color=c,lw=1.5))
    ax.add_patch(plt.Circle((pos[0],pos[2]),1.5,fill=False,ec=c));ax.text(pos[0]+2,pos[2]+2,f'{nm} ({pos[1]:.0f} m){"" if nm in active else "  [no window]"}',fontsize=7,color='k')
P=np.array(pits);ax.scatter(P[:,0],P[:,2],s=6,c='white',marker='s')
ax.set_xlim(0,160);ax.set_ylim(60,225);ax.set_aspect('equal')
ax.set_title('Paddock Drift camera set (cameras_3.ini, main): positions, aim, and drift-line sections by active camera\n(line colour = camera AC selects there via fast_lane projection; black = none)',fontsize=9)
fig.tight_layout();fig.savefig(f'{OUT}/cams_topdown.png');print('done',sorted(active))
