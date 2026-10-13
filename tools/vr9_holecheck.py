"""VR9 hotfix verification: full-map 1 m top-down collision raster (all physics meshes of all kn5s
in models_main/short.ini, whole map incl. north extension), vs the pre-VR9 flat stage.
Writes /workspace/vr9/cov_<tag>.npz.  Usage: python tools/vr9_holecheck.py <tag> <track dir>"""
import os, re, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import physraster as PR
BOX = (-1530.0, 1220.0, -3005.0, 1170.0)
def files(Z):
    fs = []
    for ini in ('models_main.ini', 'models_short.ini'):
        for l in open(os.path.join(Z, ini)):
            m = re.match(r'\s*FILE\s*=\s*(\S+)', l)
            if m and m.group(1) not in fs: fs.append(m.group(1))
    return fs
def run(tag, Z, layout_files=None):
    PR.Z = Z.rstrip('/') + '/'
    r = PR.raster(PR.physmeshes(layout_files or files(Z), BOX), BOX, 1.0)
    np.savez('/workspace/vr9/cov_%s.npz' % tag, xs=r[0], zs=r[1], H=r[2], KEY=r[3], UP=r[4], names=np.array(r[5], object))
    return r
if __name__ == '__main__':
    r = run(sys.argv[1], sys.argv[2]); print(sys.argv[1], 'hit cells', int(np.isfinite(r[2]).sum()))
