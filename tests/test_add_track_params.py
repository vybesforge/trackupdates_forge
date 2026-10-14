import os, subprocess, sys, tempfile
S = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'server', 'add_track_params.py')
def run(*a): return subprocess.run([sys.executable, S, *a], capture_output=True, text=True)

def test_append_only_and_idempotent():
    with tempfile.TemporaryDirectory() as d:
        cfg = os.path.join(d, 'cfg'); os.makedirs(cfg); p = os.path.join(cfg, 'data_track_params.ini')
        orig = b'[ks_nurburgring]\r\nNAME=Nurburgring\r\nLATITUDE=50.341648\r\n' * 200
        open(p, 'wb').write(orig)
        assert run(d).returncode == 0
        new = open(p, 'rb').read()
        assert new.startswith(orig) and b'[vf_i29_speedway]' in new and len(new) > len(orig)
        assert open(p + '.bak', 'rb').read() == orig
        assert run(d).returncode == 0 and open(p, 'rb').read() == new

def test_missing_or_empty_refused_without_create():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, 'cfg', 'data_track_params.ini')
        assert run(d).returncode != 0 and not os.path.exists(p)
        os.makedirs(os.path.dirname(p)); open(p, 'wb').close()
        assert run(d).returncode != 0 and os.path.getsize(p) == 0
        assert run('--create', d).returncode == 0 and b'[vf_i29_speedway]' in open(p, 'rb').read()

def test_system_data_refused():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, 'system', 'data', 'data_track_params.ini'); os.makedirs(os.path.dirname(p))
        open(p, 'wb').write(b'[x]\nNAME=x\n' * 100)
        assert run(p).returncode != 0 and open(p, 'rb').read() == b'[x]\nNAME=x\n' * 100

if __name__ == '__main__':
    for n, f in list(globals().items()):
        if n.startswith('test_'): f(); print('ok', n)
