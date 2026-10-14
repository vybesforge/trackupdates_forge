"""Build the I-29 Speedway release zip (local only; publishing is a separate, manual step).
Usage: python tools/build_release.py [version] [outdir]      default: v1.0.2  /workspace/rpotm/release
Zip layout (drop-in for the Assetto Corsa root folder or Content Manager drag & drop):
  content/tracks/vf_i29_speedway/...          track (all layouts, CSP extension incl. reactive drag tree)
  apps/python/i29_dragtree/...       vanilla-AC Python drag tree + timeslip app
  server/                            data_track_params snippet + add_track_params.py (dedicated server / CM hosting)
  I-29_Speedway_docs/                LICENSE, NOTICE, CREDITS.md, README.md, RELEASE_NOTES.md
Refuses to build if any LFS file is still a pointer, or if forbidden branding strings are found in text files."""
import hashlib, os, re, sys, zipfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VER = sys.argv[1] if len(sys.argv) > 1 else 'v1.0.2'
OUT = sys.argv[2] if len(sys.argv) > 2 else '/workspace/rpotm/release'
FORBID = re.compile(r'1320|smile\s*like\s*kyle|drivenbycruise', re.I)
TEXT = ('.ini', '.json', '.lua', '.py', '.md', '.txt', '.csv')

def files(base, skip=()):
    for dp, dn, fn in os.walk(base):
        dn[:] = [d for d in dn if d not in ('__pycache__',) + tuple(skip)]
        for f in sorted(fn):
            if not f.endswith('.pyc'):
                yield os.path.join(dp, f)

def main():
    notes = os.path.join(ROOT, 'docs', 'RELEASE_NOTES_%s.md' % VER)
    assert os.path.exists(notes), 'missing ' + notes
    entries = []
    for p in files(os.path.join(ROOT, 'vf_i29_speedway')):
        entries.append((p, 'content/tracks/vf_i29_speedway/' + os.path.relpath(p, os.path.join(ROOT, 'vf_i29_speedway'))))
    for p in files(os.path.join(ROOT, 'apps', 'python', 'i29_dragtree')):
        entries.append((p, 'apps/python/i29_dragtree/' + os.path.basename(p)))
    for f in ('data_track_params_vf_i29_speedway.ini', 'add_track_params.py'):
        entries.append((os.path.join(ROOT, 'server', f), 'server/' + f))
    for f in ('LICENSE', 'NOTICE', 'CREDITS.md', 'README.md'):
        entries.append((os.path.join(ROOT, f), 'I-29_Speedway_docs/' + f))
    entries.append((notes, 'I-29_Speedway_docs/RELEASE_NOTES.md'))
    bad = []
    for p, a in entries:
        with open(p, 'rb') as fh:
            head = fh.read(200)
        if head.startswith(b'version https://git-lfs'):
            bad.append('LFS pointer: ' + a)
        if p.endswith(TEXT) and a.startswith(('content', 'apps')):
            if FORBID.search(open(p, encoding='utf-8', errors='replace').read()):
                bad.append('forbidden branding: ' + a)
    if bad:
        sys.exit('\n'.join(bad))
    os.makedirs(OUT, exist_ok=True)
    zp = os.path.join(OUT, 'I-29_Speedway_%s.zip' % VER)
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p, a in entries:
            z.write(p, a)
    h = hashlib.sha256(open(zp, 'rb').read()).hexdigest()
    open(zp + '.sha256', 'w').write('%s  %s\n' % (h, os.path.basename(zp)))
    print(zp, '%.1f MB' % (os.path.getsize(zp) / 1e6), len(entries), 'files', 'sha256', h)

if __name__ == '__main__':
    main()
