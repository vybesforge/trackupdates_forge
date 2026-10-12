"""Tiny mesh helpers for VR5 self-made props (AC vertex = pos3, normal3, uv2, tangent3)."""
import numpy as np,struct
def quad(p0,p1,p2,p3,uv=((0,0),(1,0),(1,1),(0,1))):
    P=np.array([p0,p1,p2,p3],float);n=np.cross(P[1]-P[0],P[3]-P[0]);n/=np.linalg.norm(n)+1e-12;t=(P[1]-P[0]);t/=np.linalg.norm(t)+1e-12
    V=np.zeros((4,11));V[:,:3]=P;V[:,3:6]=n;V[:,6:8]=uv;V[:,8:11]=t;return V,np.array([[0,1,2],[0,2,3]])
def merge(parts):
    Vs=[];Is=[];o=0
    for V,I in parts: Vs.append(V);Is.append(I+o);o+=len(V)
    return np.vstack(Vs).astype('<f4'),np.vstack(Is).astype('<u2')
def fix_winding(V,I):
    """make every face's geometric normal agree with its stored vertex normal"""
    I=I.copy();g=np.cross(V[I[:,1],:3]-V[I[:,0],:3],V[I[:,2],:3]-V[I[:,0],:3]);bad=(g*V[I[:,0],3:6]).sum(1)<0;I[bad]=I[bad][:,[0,2,1]];return I
def box(c,s,rot=0.0,uvs=1.0):
    """axis box centre c=(x,y,z), size s=(sx,sy,sz), rotated rot rad about y. 6 outward quads."""
    c=np.array(c,float);h=np.array(s,float)/2;R=np.array([[np.cos(rot),0,np.sin(rot)],[0,1,0],[-np.sin(rot),0,np.cos(rot)]])
    def P(x,y,z): return c+R@(np.array([x,y,z])*h)
    F=[((1,-1,-1),(1,-1,1),(1,1,1),(1,1,-1)),((-1,-1,1),(-1,-1,-1),(-1,1,-1),(-1,1,1)),((-1,1,-1),(1,1,-1),(1,1,1),(-1,1,1)),
       ((-1,-1,1),(1,-1,1),(1,-1,-1),(-1,-1,-1)),((-1,-1,1),(-1,1,1),(1,1,1),(1,-1,1)),((1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,-1))]
    parts=[]
    for f in F:
        V,I=quad(*[P(*v) for v in f]);V[:,6:8]*=uvs;n=V[0,3:6]
        ctr=V[:,:3].mean(0)
        if np.dot(n,ctr-c)<0: V[:,3:6]*=-1
        parts.append((V,I))
    V,I=merge(parts);return V,fix_winding(V,I)
def cyl(c,r,h,axis='y',n=12,cap=True):
    """cylinder: base centre c, radius r, length h along +axis ('y' or 'z')."""
    c=np.array(c,float);a=np.linspace(0,2*np.pi,n+1)[:-1]
    def P(ang,t):
        if axis=='y': return c+np.array([r*np.cos(ang),t,r*np.sin(ang)])
        return c+np.array([r*np.cos(ang),r*np.sin(ang),t])
    def N(ang): return np.array([np.cos(ang),0,np.sin(ang)]) if axis=='y' else np.array([np.cos(ang),np.sin(ang),0])
    parts=[]
    for i in range(n):
        a0,a1=a[i],a[(i+1)%n];V,I=quad(P(a0,0),P(a1,0),P(a1,h),P(a0,h));V[0,3:6]=V[3,3:6]=N(a0);V[1,3:6]=V[2,3:6]=N(a1);parts.append((V,I))
    if cap:
        ax=np.array([0,1,0]) if axis=='y' else np.array([0,0,1])
        for t,sg in((h,1),(0,-1)):
            V=np.zeros((n+1,11));V[0,:3]=P(0,t)-np.array([r,0,0]) if False else (c+ax*t);V[1:,:3]=[P(x,t) for x in a];V[:,3:6]=ax*sg
            V[:,6]=0.5+0.5*np.r_[0,np.cos(a)];V[:,7]=0.5+0.5*np.r_[0,np.sin(a)];V[:,8:11]=[1,0,0]
            I=np.array([[0,i+1,(i+1)%n+1] for i in range(n)]);parts.append((V,I))
    V,I=merge(parts);return V,fix_winding(V,I)
def disc(c,r,normal=(0,0,1),n=16):
    c=np.array(c,float);nz=np.array(normal,float);a=np.linspace(0,2*np.pi,n+1)[:-1]
    u=np.cross(nz,[0,1,0]);u=u/np.linalg.norm(u) if np.linalg.norm(u)>1e-6 else np.array([1,0,0]);v=np.cross(u,nz)
    V=np.zeros((n+1,11));V[0,:3]=c;V[1:,:3]=c+r*(np.cos(a)[:,None]*u+np.sin(a)[:,None]*v);V[:,3:6]=nz
    V[:,6]=0.5+0.5*np.r_[0,np.cos(a)];V[:,7]=0.5-0.5*np.r_[0,np.sin(a)];V[:,8:11]=u
    I=np.array([[0,i+1,(i+1)%n+1] for i in range(n)]);return V.astype('<f4'),fix_winding(V,I)
def xform(VI,rot=0.0,off=(0,0,0)):
    V,I=VI;V=V.copy().astype(float);R=np.array([[np.cos(rot),0,np.sin(rot)],[0,1,0],[-np.sin(rot),0,np.cos(rot)]])
    V[:,:3]=V[:,:3]@R.T+off;V[:,3:6]=V[:,3:6]@R.T;V[:,8:11]=V[:,8:11]@R.T;return V.astype('<f4'),I
def solid_dds(rgb,a=255,n=8):
    import build_open_textures as B
    return B.write_dds(np.dstack([np.full((n,n,3),rgb,np.uint8),np.full((n,n),a,np.uint8)]),'DXT1',4,None)
def props(template,**kw):
    out=[]
    for p,r in template:
        if p in kw:
            v=kw[p];v=v if isinstance(v,(list,tuple)) else (v,)
            out.append((p,struct.pack('<f',v[0])+(r[4:] if len(v)==1 else r[4:12]+struct.pack('<3f',*v)+r[24:])))
        else: out.append((p,r))
    return out
