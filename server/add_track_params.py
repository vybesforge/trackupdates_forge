"""Append the [vf_i29_speedway] entry to a data_track_params.ini if it is missing (idempotent).
Usage: python add_track_params.py <path/to/data_track_params.ini> [more paths...]
Examples: <server>/system/data/data_track_params.ini, <AC root>/system/data/data_track_params.ini,
          AssettoServer: <server>/cfg/data_track_params.ini"""
import os, re, shutil, sys
SNIP = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data_track_params_vf_i29_speedway.ini')

def add(path):
    text = open(path, encoding='utf-8', errors='replace').read() if os.path.exists(path) else ''
    if re.search(r'^\s*\[vf_i29_speedway\]\s*$', text, re.M | re.I):
        print('already present:', path); return
    if text:
        shutil.copy2(path, path + '.bak')
    snip = open(SNIP, encoding='utf-8').read().replace('\r\n', '\n').strip('\n')
    nl = '\r\n' if '\r\n' in text or not text else '\n'
    sep = '' if not text or text.endswith(('\n',)) else nl
    with open(path, 'a', encoding='utf-8', newline='') as f:
        f.write(sep + nl + snip.replace('\n', nl) + nl)
    print('added:', path)

if __name__ == '__main__':
    if len(sys.argv) < 2: sys.exit(__doc__)
    for p in sys.argv[1:]: add(p)
