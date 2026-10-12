import numpy as np,math
def fix(V,I):
    """make triangle winding agree with vertex normals (AC: cross(b-a,c-a) . n > 0)"""
    I=np.asarray(I,np.int64).reshape(-1,3);P=V[:,:3];a,b,c=P[I[:,0]],P[I[:,1]],P[I[:,2]]
    g=np.cross(b-a,c-a);n=V[I[:,0],3:6]+V[I[:,1],3:6]+V[I[:,2],3:6];bad=(g*n).sum(1)<0;I[bad]=I[bad][:,[0,2,1]];return I
class M:
    """mesh accumulator: verts Nx11 (pos, normal, uv, tangent)"""
    def __init__(s): s.V=[];s.I=[];s.n=0
    def add(s,V,I):
        V=np.asarray(V,np.float64);I=fix(V,I)+s.n;s.V.append(V);s.I.append(I);s.n+=len(V);return s
    def quad(s,p,nrm,uv,tan=None):
        p=np.asarray(p,float);tan=tan if tan is not None else (p[1]-p[0])/max(np.linalg.norm(p[1]-p[0]),1e-6)
        V=np.c_[p,np.tile(nrm,(4,1)),np.asarray(uv,float),np.tile(tan,(4,1))];return s.add(V,[[0,1,2],[0,2,3]])
    def box(s,c,size,yaw=0.0,uvscale=1.0,top=True,bottom=False):
        """c=(x,y_bottom,z); size=(sx,sy,sz) along local x/z rotated by yaw (rad, about +y)"""
        cx,cy,cz=c;sx,sy,sz=size;co,si=math.cos(yaw),math.sin(yaw)
        R=lambda x,z:(cx+co*x+si*z,cz-si*x+co*z);ex=np.array([co,0,-si]);ez=np.array([si,0,co])
        hx,hz=sx/2,sz/2;y0,y1=cy,cy+sy
        for sgn,ax,ln,w in((1,ex,ez,sz),(-1,ex,ez,sz),(1,ez,ex,sx),(-1,ez,ex,sx)):
            off=ax*(hx if ax is ex else hz)*sgn;cen=np.array([cx,0,cz])+off;half=ln*w/2
            p=[cen-half+[0,y0,0],cen+half+[0,y0,0],cen+half+[0,y1,0],cen-half+[0,y1,0]]
            s.quad(p,ax*sgn,[(0,sy/uvscale),(w/uvscale,sy/uvscale),(w/uvscale,0),(0,0)],ln)
        for yy,nn in(((y1,1),) if top else ())+(((y0,-1),) if bottom else ()):
            p=[np.array([cx,yy,cz])+ex*a*hx+ez*b*hz for a,b in((-1,-1),(1,-1),(1,1),(-1,1))]
            s.quad(p,[0,nn,0],[(p_[0]/uvscale,p_[2]/uvscale) for p_ in p],ex)
        return s
    def cyl(s,c,r,h,seg=8,uvscale=1.0):
        cx,cy,cz=c;V=[];I=[]
        for i in range(seg+1):
            a=2*math.pi*i/seg;n=np.array([math.cos(a),0,math.sin(a)]);t=np.array([-math.sin(a),0,math.cos(a)])
            for yy,vv in((cy,h/uvscale),(cy+h,0)): V.append([cx+r*n[0],yy,cz+r*n[2],*n,i/seg,vv,*t])
        for i in range(seg): I+= [[2*i,2*i+2,2*i+3],[2*i,2*i+3,2*i+1]]
        return s.add(V,I)
    def out(s):
        if not s.V: return np.zeros((0,11)),np.zeros((0,3),int)
        return np.vstack(s.V),np.vstack(s.I)
def resample(P,step):
    P=np.asarray(P,float);d=np.r_[0,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))];n=max(2,int(d[-1]/step)+1);s=np.linspace(0,d[-1],n)
    return np.c_[np.interp(s,d,P[:,0]),np.interp(s,d,P[:,1])],s
def ribbon(P,ys,offs,uvx,vscale,s,nrm_up=True):
    """P (n,2) centreline xz, ys (n,), offs list of lateral offsets (m, + = left), extra y per offset; returns V,I"""
    T=np.gradient(P,axis=0);T/=np.linalg.norm(T,axis=1)[:,None]+1e-9;L=np.c_[-T[:,1],T[:,0]]
    k=len(offs);V=[]
    for i in range(len(P)):
        for j,(o,dy) in enumerate(offs):
            q=P[i]+L[i]*o;V.append([q[0],ys[i]+dy,q[1],0,1,0,uvx[j],s[i]/vscale,T[i,0],0,T[i,1]])
    V=np.array(V);I=[]
    for i in range(len(P)-1):
        for j in range(k-1):
            a=i*k+j;b=a+1;c=a+k+1;d=a+k;I+=[[a,b,c],[a,c,d]]
    # normals from geometry
    I=np.array(I);Pp=V[:,:3];g=np.cross(Pp[I[:,1]]-Pp[I[:,0]],Pp[I[:,2]]-Pp[I[:,0]]);g[g[:,1]<0]*=-1
    N=np.zeros_like(Pp);
    for c_ in range(3): np.add.at(N,I[:,c_],g)
    N/=np.linalg.norm(N,axis=1)[:,None]+1e-9;V[:,3:6]=N;return V,I
