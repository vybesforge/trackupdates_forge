"""Append the [vf_i29_speedway] entry to an AssettoServer cfg/data_track_params.ini if missing (idempotent, keeps .bak).
Usage: python add_track_params.py <AssettoServer root folder>      -> edits <root>/cfg/data_track_params.ini
       python add_track_params.py <path/to/cfg/data_track_params.ini>
Refuses system/data/data_track_params.ini (shared AC file; AssettoServer never reads it, vanilla acServer doesn't need it)."""
import os, re, shutil, sys
SNIP = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data_track_params_vf_i29_speedway.ini')

def target(arg):
    p = os.path.abspath(arg)
    if os.path.isdir(p):
        p = os.path.join(p, 'cfg', 'data_track_params.ini')
    parts = [x.lower() for x in re.split(r'[\\/]+', p)]
    if len(parts) >= 3 and parts[-3:-1] == ['system', 'data']:
        sys.exit('refusing: %s is the shared system/data file. Use <server root>/cfg/data_track_params.ini instead.' % p)
    if parts[-2:-1] != ['cfg']:
        print('warning: %s is not in a cfg folder; AssettoServer reads <server root>/cfg/data_track_params.ini' % p)
    return p

def add(path):
    text = open(path, encoding='utf-8', errors='replace').read() if os.path.exists(path) else ''
    if re.search(r'^\s*\[vf_i29_speedway\]\s*$', text, re.M | re.I):
        print('already present:', path); return
    if text:
        shutil.copy2(path, path + '.bak')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lines = open(SNIP, encoding='utf-8').read().replace('\r\n', '\n').split('\n')
    snip = '\n'.join(l for l in lines if l.strip() and not l.startswith(';'))
    nl = '\r\n' if '\r\n' in text or not text else '\n'
    sep = '' if not text or text.endswith('\n') else nl
    with open(path, 'a', encoding='utf-8', newline='') as f:
        f.write(sep + (nl if text else '') + snip.replace('\n', nl) + nl)
    print('added:', path)

if __name__ == '__main__':
    if len(sys.argv) < 2: sys.exit(__doc__)
    for a in sys.argv[1:]: add(target(a))
