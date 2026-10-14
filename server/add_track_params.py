"""Append the [vf_i29_speedway] entry to an AssettoServer cfg/data_track_params.ini if missing.
Usage: python add_track_params.py [--create] <AssettoServer root folder | path/to/cfg/data_track_params.ini>
Safety (v1.0.4):
- Append-only: an existing file is never rewritten or truncated (opened only in 'a' mode); a .bak copy is made first.
- If the target file does not exist or is empty, nothing is written unless --create is given
  (AssettoServer normally downloads the full list itself; a missing file usually means a wrong path).
- Refuses any system/data/data_track_params.ini (shared AC file; AssettoServer never reads it; vanilla acServer needs none).
- Idempotent: does nothing if [vf_i29_speedway] is already present."""
import os, re, shutil, sys
SNIP = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data_track_params_vf_i29_speedway.ini')

def target(arg):
    p = os.path.abspath(arg)
    if os.path.isdir(p):
        p = os.path.join(p, 'cfg', 'data_track_params.ini')
    parts = [x.lower() for x in re.split(r'[\\/]+', p)]
    if len(parts) >= 3 and parts[-3:-1] == ['system', 'data']:
        raise SystemExit('refusing: %s is the shared system/data file. Use <server root>/cfg/data_track_params.ini instead.' % p)
    if parts[-2:-1] != ['cfg']:
        print('warning: %s is not in a cfg folder; AssettoServer reads <server root>/cfg/data_track_params.ini' % p)
    return p

def snippet():
    lines = open(SNIP, 'rb').read().decode('utf-8').replace('\r\n', '\n').split('\n')
    return [l for l in lines if l.strip() and not l.startswith(';')]

def add(path, create=False):
    exists = os.path.isfile(path)
    data = open(path, 'rb').read() if exists else b''
    if not data and not create:
        raise SystemExit('refusing: %s %s. Check the path; pass --create to create it with only this section.'
                         % (path, 'is empty' if exists else 'does not exist'))
    text = data.decode('utf-8', errors='replace')
    if re.search(r'^\s*\[vf_i29_speedway\]\s*$', text, re.M | re.I):
        print('already present:', path); return False
    if data:
        shutil.copy2(path, path + '.bak')
    else:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    nl = '\r\n' if (b'\r\n' in data or not data) else '\n'
    out = ('' if not data or data.endswith(b'\n') else nl) + (nl if data else '') + nl.join(snippet()) + nl
    size = len(data)
    with open(path, 'ab') as f:          # append-only, never 'w'
        f.write(out.encode('utf-8'))
    assert open(path, 'rb').read(size) == data, 'existing content changed'
    print('added:', path); return True

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--create']
    if not args: raise SystemExit(__doc__)
    for a in args: add(target(a), '--create' in sys.argv)
