"""Advertiser ad template: renders tent_slotNN.dds (2048, tent UV atlas) and board_slotNN.dds (2048x1024) for a brand.
Tent atlas (see tents_v11.py): rows 0-1024 roof triangle (apex top centre, base row 1024; one panel art used on all 4 roof
panels), 1024-1280 valance strip (also the table front skirt, u 0.15-0.85, and the feather flag, u 0.1-0.9 running bottom->top),
1280-2032 back wall (6 x 2.4 m), 2032-2048 plain fabric (undersides). Art is drawn readable; the mesh UVs handle orientation.
Usage:
  python3 tools/make_ad.py --brand pussynip --apply            # brands from assets_src/ads/brands.json -> skins/default/ (AC track-skin texture override)
  python3 tools/make_ad.py --name "ACME" --domain acme.com --bg "#111" --fg "#fff" --accent "#f40" [--logo x.png] --tent 7 --board 2 --apply
  (without --apply files go to assets_src/ads/out/). Only vf_i29_speedway/skins/default/*.dds are written: no kn5 / checksummed file changes."""
import os,sys,json,argparse,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import build_open_textures as B
from PIL import Image,ImageDraw,ImageFont,ImageColor
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));EXT=f'{ROOT}/vf_i29_speedway/skins/default';FONT=f'{ROOT}/assets_src/brand/fonts/SpaceGrotesk-wght.ttf'
N=2048
def C(c): return ImageColor.getrgb(c) if isinstance(c,str) else tuple(c)
def font(sz,w=700):
    f=ImageFont.truetype(FONT,sz)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
def fit(text,maxw,size,w=700):
    while size>20 and font(size,w).getlength(text)>maxw: size-=4
    return font(size,w)
class Canvas:
    def __init__(s,w,h,bg): s.im=Image.new('RGB',(w,h),C(bg));s.D=ImageDraw.Draw(s.im)
    def text(s,cx,cy,t,f,fill,sp=0,sy=1.0):
        bb=f.getbbox(t);W=int(f.getlength(t)+sp*len(t))+8;H=bb[3]-bb[1]+8;tt=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(tt);x=4
        for ch in t: d.text((x,4-bb[1]),ch,font=f,fill=C(fill));x+=f.getlength(ch)+sp
        if sy!=1.0: tt=tt.resize((W,max(1,int(H*sy))),Image.LANCZOS)
        s.im.paste(tt,(int(cx-tt.width/2),int(cy-tt.height/2)),tt);return tt.width
    def logo(s,path,cx,cy,size):
        lg=Image.open(path).convert('RGBA');r=size/max(lg.size);lg=lg.resize((int(lg.width*r),int(lg.height*r)),Image.LANCZOS)
        if lg.getextrema()[3][0]==255:   # no alpha -> soft round mask
            yy,xx=np.mgrid[0:lg.height,0:lg.width];rr=np.hypot((xx-lg.width/2)/(lg.width/2),(yy-lg.height/2)/(lg.height/2));lg.putalpha(Image.fromarray((np.clip((1-rr)/0.18,0,1)*255).astype(np.uint8)))
        s.im.paste(lg,(int(cx-lg.width/2),int(cy-lg.height/2)),lg)
def tent_art(b,slot):
    bg,fg,ac,ac2=b['bg'],b['fg'],b['accent'],b.get('accent2',b['accent']);cv=Canvas(N,N,bg);D=cv.D;logo=b.get('logo')
    lp=f'{ROOT}/{logo}' if logo and not os.path.isabs(logo) else logo
    # roof triangle: half-width at row y = y px -> keep content inside
    if lp and os.path.exists(lp): cv.logo(lp,N//2,560,360);ny=820
    else: ny=700
    cv.text(N//2,ny,b['name'],fit(b['name'],2*ny*0.78,200),ac);D.rectangle([N//2-300,ny+95,N//2+300,ny+102],fill=C(ac2))
    D.rectangle([0,1000,N,1012],fill=C(ac))
    # valance strip
    D.rectangle([0,1024,N,1280],fill=C(ac));val=f"{b['name']}   |   {b['domain'].upper()}"+(f"   |   {b['tagline']}" if b.get('tagline') else '')
    cv.text(N//2,1152,val,fit(val,N*0.9,96,700),bg)
    # back wall
    D.rectangle([0,1280,N,2032],fill=C(bg));D.rectangle([140,1330,N-140,1338],fill=C(ac2))
    if lp and os.path.exists(lp): cv.logo(lp,330,1640,420);cx,mw=1150,1450
    else: cx,mw=N//2,1800
    cv.text(cx,1570,b['name'],fit(b['name'],mw,250),fg,sp=4,sy=0.95)
    cv.text(cx,1790,b['domain'],fit(b['domain'],mw,140,500),ac,sy=0.95)
    if b.get('tagline'): cv.text(cx,1930,b['tagline'],fit(b['tagline'],mw,60,500),ac2,sp=12,sy=0.95)
    D.rectangle([0,2032,N,N],fill=tuple(max(0,v-8) for v in C(bg)))
    return cv.im
def board_art(b,slot):
    bg,fg,ac,ac2=b['bg'],b['fg'],b['accent'],b.get('accent2',b['accent']);W,H=2048,1024;cv=Canvas(W,H,bg);D=cv.D
    D.rectangle([0,0,W,30],fill=C(ac));D.rectangle([0,H-30,W,H],fill=C(ac));logo=b.get('logo');lp=f'{ROOT}/{logo}' if logo and not os.path.isabs(logo) else logo
    if lp and os.path.exists(lp): cv.logo(lp,300,H//2,460);cx,mw=1220,1500
    else: cx,mw=W//2,1850
    cv.text(cx,380,b['name'],fit(b['name'],mw,260),fg,sp=4);D.rectangle([cx-mw//3,530,cx+mw//3,538],fill=C(ac2))
    cv.text(cx,660,b['domain'],fit(b['domain'],mw,170,500),ac)
    if b.get('tagline'): cv.text(cx,840,b['tagline'],fit(b['tagline'],mw,70,500),ac2,sp=12)
    return cv.im
def dds(im,mips): a=np.array(im.convert('RGB'));return B.write_dds(np.dstack([a,np.full(a.shape[:2],255,np.uint8)]),'DXT1',mips,None)
def make(b,tents=(),boards=(),apply=False,key='custom'):
    out=EXT if apply else f'{ROOT}/assets_src/ads/out';os.makedirs(out,exist_ok=True);os.makedirs(f'{ROOT}/assets_src/ads/png',exist_ok=True);done=[]
    for s in tents:
        im=tent_art(b,s);im.save(f'{ROOT}/assets_src/ads/png/{key}_tent_slot{s:02d}.png');open(f'{out}/tent_slot{s:02d}.dds','wb').write(dds(im,12));done.append(f'{out}/tent_slot{s:02d}.dds')
    for s in boards:
        im=board_art(b,s);im.save(f'{ROOT}/assets_src/ads/png/{key}_board_slot{s:02d}.png');open(f'{out}/board_slot{s:02d}.dds','wb').write(dds(im,11));done.append(f'{out}/board_slot{s:02d}.dds')
    return done
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--brand');ap.add_argument('--name');ap.add_argument('--domain');ap.add_argument('--tagline',default='')
    ap.add_argument('--logo');ap.add_argument('--bg',default='#101010');ap.add_argument('--fg',default='#f0f0f0');ap.add_argument('--accent',default='#29d5e9');ap.add_argument('--accent2')
    ap.add_argument('--tent',type=int,nargs='*',default=None);ap.add_argument('--board',type=int,nargs='*',default=None);ap.add_argument('--apply',action='store_true')
    a=ap.parse_args()
    if a.brand:
        B_=json.load(open(f'{ROOT}/assets_src/ads/brands.json'))[a.brand]
        if B_.get('pending') and a.apply: sys.exit(f'{a.brand} is pending (domain not final); fill in brands.json first')
        key=a.brand
    else: B_=dict(name=a.name,domain=a.domain,tagline=a.tagline,logo=a.logo,bg=a.bg,fg=a.fg,accent=a.accent,accent2=a.accent2 or a.accent);key=a.name.lower().replace(' ','')
    t=a.tent if a.tent is not None else B_.get('tent_slots',[]);bo=a.board if a.board is not None else B_.get('board_slots',[])
    for f in make(B_,t,bo,a.apply,key): print('wrote',f)
