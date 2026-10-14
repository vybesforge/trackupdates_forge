"""Export the current ad art as a web bundle for the CSP live-ads script (server/ads/i29_ads.lua).
Writes <out>/ads.json + <out>/*.png (2048 tents, 2048x1024 boards) from vf_i29_speedway/skins/default/*.dds.
Upload <out>/ to any static HTTPS host (for example vybesforge.com/i29/ads/) and point the manifest URL at ads.json.
Usage: python3 tools/export_ads_web.py https://vybesforge.com/i29/ads [outdir]   (default outdir: assets_src/ads/web)"""
import sys,os,glob,json,time
from PIL import Image
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));SKIN=f'{ROOT}/vf_i29_speedway/skins/default'
base=sys.argv[1].rstrip('/');out=sys.argv[2] if len(sys.argv)>2 else f'{ROOT}/assets_src/ads/web';os.makedirs(out,exist_ok=True)
ver=int(time.time());slots={}
for f in sorted(glob.glob(f'{SKIN}/*_slot??.dds')):
    tn=os.path.basename(f)[:-4];kind,nn=tn.split('_slot');mat=f'vf{kind}_slot{nn}'
    Image.open(f).convert('RGB').save(f'{out}/{tn}.png',optimize=True);slots[mat]=f'{base}/{tn}.png?v={ver}'   # ?v= busts CSP's image cache
json.dump({'version':ver,'slots':slots},open(f'{out}/ads.json','w'),indent=1);print(f'{len(slots)} slots -> {out}/ads.json (version {ver})')
