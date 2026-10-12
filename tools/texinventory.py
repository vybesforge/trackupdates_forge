import sys,re,csv,collections,glob,os
sys_argv_dir=sys.argv[1]; out=sys.argv[2]
sys.argv=['x'];exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'kn5info.py')).read().split('for p in sys.argv')[0])
SAT=r'^google'
BRAND=r'^(loves|JoeHunt|factory_logo|usa)|logo'
STOCK=r'tarmac|white-line|^NULL|^black_|^green|^red01|^line\.|grass_nm|grass_blend|waterbump|vesi_normal'
MOD=r'lagmannen|prantaren|duvan|larkan|hoken|jarvi|Puit vana|Muld Detailne|^vesi|commissario|toilette|containers|oil_build_vag|vag_d1|window_d7|door_d1|road_vara|detail_arlan|gryslate|gurdrc|twallb02|concw|^amb|crane1|tentchndp|tentcl|tentcok|tentmars|barrel|cables|^cone|rocky|mud2|wood|metal|glass2|door_blue|Tex_|1a_rail|gravelroad|concretebasic|banner02|roofe|skid1'
OWN=r'^(RPM|rpm)_|drag|tower|signs_new|marsh|paddock|pittent|highway|fence_|gate_|roadpit|roadsf|rmbl|tarmacmask5|track_cracks|tentroof|factory_w|silo|^grass|rpm'
PLAN={'satellite':('high','Replace with public-domain USDA NAIP / USGS orthoimagery or hand-painted ground'),
 'brand logo':('high','Replace with original/fictional signage or get written permission'),
 'third-party mod':('med','Recreate from CC0 (ambientCG, Poly Haven) or get original author OK'),
 'stock':('low','Generic detail/normal map; regenerate from CC0 to be safe'),
 'own/zwiss':('low','Keep under project asset license (zwiss reuse approval); spot-check for embedded photos'),
 'unknown':('med','Identify origin; replace with CC0 if unclear')}
def cls(t):
    for o,p in [('satellite',SAT),('brand logo',BRAND),('stock',STOCK),('third-party mod',MOD),('own/zwiss',OWN)]:
        if re.search(p,t,re.I): return o
    return 'unknown'
rows=[];cnt=collections.Counter()
for k in sorted(glob.glob(sys_argv_dir+'/*.kn5')):
    for name,sz in parse(k)[1]:
        o=cls(name);r,p=PLAN[o];rows.append([os.path.basename(k),name,sz,o,r,p]);cnt[o]+=1
w=csv.writer(open(out,'w',newline=''));w.writerow(['file','texture','size','likely_origin','license_risk','replacement_plan']);w.writerows(rows)
print(len(rows),dict(cnt));print('unknown:',[r[1] for r in rows if r[3]=='unknown'])
