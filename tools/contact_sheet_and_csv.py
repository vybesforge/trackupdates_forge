import json,sys,io,csv,os,collections
sys.path.insert(0,os.path.dirname(__file__));import kn5patch as k
from PIL import Image,ImageDraw
meta=json.load(open('/workspace/rpotm/tex/new/meta.json'));T=json.load(open('/workspace/rpotm/tex/targets.json'))
names=[];seen=set()
for t in T:
    if t[1] not in seen: seen.add(t[1]);names.append((t[0],t[1]))
def thumb(im,s=200):
    im=im.convert('RGBA');c=Image.new('RGBA',im.size,(90,90,90,255));d=ImageDraw.Draw(c);st=max(4,im.size[0]//16)
    for y in range(0,im.size[1],st):
        for x in range(0,im.size[0],st):
            if (x//st+y//st)%2: d.rectangle([x,y,x+st,y+st],fill=(160,160,160,255))
    c.alpha_composite(im);c.thumbnail((s,s));return c
per=12
for si in range(0,len(names),per):
    ch=names[si:si+per];cols=3;rows=(len(ch)+cols-1)//cols;CW=440;sheet=Image.new('RGB',(cols*CW,rows*250+30),(30,30,30));d=ImageDraw.Draw(sheet)
    d.text((10,8),'Each cell: BEFORE (left) | AFTER (right). Checker = alpha.',fill='white')
    for i,(kn,n) in enumerate(ch):
        x=(i%cols)*CW;y=30+(i//cols)*250
        o=Image.open(io.BytesIO(k.get_tex(f'/workspace/rpotm/backup/{kn}.pre_textures_open',n)));a=Image.open(io.BytesIO(k.get_tex(f'zw_rpm/{kn}',n)))
        sheet.paste(thumb(o),(x+5,y));sheet.paste(thumb(a),(x+215,y));m=meta[n]
        d.text((x+5,y+203),f"{n}  {m['old']} -> {m['new']}",fill='white');d.text((x+5,y+220),m['src'][:60],fill=(150,220,150))
    sheet.save(f'/workspace/rpotm/docs_preview/textures_open_{si//per+1}.png')
r=list(csv.DictReader(open('docs/assets.csv')));F=list(r[0].keys())+['source','license_url','new_format']
for row in r:
    m=meta.get(row['texture'])
    if m and (row['license_risk'] in('high','med') or row['likely_origin']=='unknown'):
        row.update(likely_origin='replaced',license_risk='low',replacement_plan='DONE textures/open'+(': '+m['note'] if m['note'] else ''),source=m['src'],license_url=m['lic'],new_format=m['new'])
    for f in F: row.setdefault(f,'')
w=csv.DictWriter(open('docs/assets.csv','w',newline=''),fieldnames=F);w.writeheader();w.writerows(r)
print(collections.Counter((x['likely_origin'],x['license_risk']) for x in r))
