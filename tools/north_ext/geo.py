"""Georeference + height model for the north extension (AC track frame)."""
import numpy as np,rasterio,json,os
from scipy.ndimage import map_coordinates,gaussian_filter
G='/workspace/rpotm/geo';A=np.load(f'{G}/xz_to_utm.npy');Ai=np.linalg.inv(A[:2].T)
def utm(xz): xz=np.atleast_2d(xz);return np.c_[xz,np.ones(len(xz))]@A
def ac(u): return (np.atleast_2d(u)-A[2])@Ai.T
BOX=(-1000.0,300.0,-3000.0,-2550.0)  # x0,x1,z0(north),z1
EDGE=np.array([(-1521.7,-2397.7),(-837.9,-2637.2),(529.7,-2637.2),(1213.5,-2215.0)])  # north edge of zwiss 1GRASS (flat y=-0.1)
def zb(x): return np.interp(x,EDGE[:,0],EDGE[:,1])
_dem=rasterio.open(f'{G}/ext/dem_north_1m.tif');_D=_dem.read(1).astype(np.float32);_Dt=~_dem.transform
def dem(xz):
    u=utm(xz);c,r=_Dt*(u[:,0],u[:,1]);return map_coordinates(_D,[r-0.5,c-0.5],order=1,mode='nearest')
# field reference level = DEM median over flat fields just north of the edge
_s=np.array([(x,z) for x in np.arange(-990,-400,5) for z in np.arange(-2990,-2650,5)]);_h=dem(_s);REF=float(np.median(_h[_h<np.median(_h)+1.0]))
def natural(xz):
    """terrain y: zwiss flat ground (-0.1) south of the edge, DEM-REF north of it, 40 m blend"""
    xz=np.atleast_2d(xz);w=np.clip((zb(xz[:,0])-xz[:,1])/40.0,0,1);return -0.1*(1-w)+(dem(xz)-REF)*w,w
