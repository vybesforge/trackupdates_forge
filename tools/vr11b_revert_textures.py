"""VR11b: revert the VR11 texture replacement (tools/vr11_textures.py, 68 textures) back to the exact pre-VR11 blobs
from commit 795a672 (kn5s named zw_rpm*.kn5 there). Only texture blobs are spliced; geometry/materials untouched.
Gravel/dirt textures from tools/vr11_dirt.py (own_gravel*, concrete_seams.dds, Muld Detailne.dds) are not in the set and are kept.
Usage: python tools/vr11b_revert_textures.py  (extracts 795a672 kn5s via git + git lfs)"""
import os, sys, re, glob, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import kn5patch as K
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); Z = ROOT + '/vf_i29_speedway/'; REF = '795a672'
T = set(re.findall(r"'([^']+\.dds)': \(", open(ROOT + '/tools/vr11_textures.py').read())); assert len(T) == 68
def old_kn5(b):
    raw = subprocess.run(['git', 'show', f'{REF}:zw_rpm/{b}'], cwd=ROOT, capture_output=True).stdout
    if raw.startswith(b'version https://git-lfs'): raw = subprocess.run(['git', 'lfs', 'smudge'], cwd=ROOT, input=raw, capture_output=True).stdout
    p = f'/tmp/vr11b_{b}'; open(p, 'wb').write(raw); return p
def blobs(p):
    d = open(p, 'rb').read(); return {n: d[so + 4:so + 4 + sz] for n, so, sz in K.scan(p)[0]}
def main():
    for fn in sorted(glob.glob(Z + '*.kn5')):
        b = os.path.basename(fn).replace('vf_i29_speedway', 'zw_rpm')
        if subprocess.run(['git', 'cat-file', '-e', f'{REF}:zw_rpm/{b}'], cwd=ROOT).returncode: continue
        old = blobs(old_kn5(b)); cur = blobs(fn)
        rep = {n: old[n] for n in cur if n in T and n in old and cur[n] != old[n]}
        if rep: K.patch(fn, fn + '.tmp', texrep=rep); os.replace(fn + '.tmp', fn); K.scan(fn)
        print(os.path.basename(fn), 'reverted', len(rep), sorted(rep))
if __name__ == '__main__': main()
