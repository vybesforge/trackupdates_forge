# Run: blender -b -P tools/own_models_blender.py -- <outdir>
import bpy,bmesh,json,math,sys,os
from mathutils import Matrix,Vector
OUT=sys.argv[sys.argv.index('--')+1]
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
def mat(name):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True;return m
def box(bm,cx,cy,cz,sx,sy,sz,rot=0):
    r=bmesh.ops.create_cube(bm,size=1.0)['verts']
    M=Matrix.Translation((cx,cy,cz))@Matrix.Rotation(rot,4,'Z')@Matrix.Diagonal((sx,sy,sz,1))
    bmesh.ops.transform(bm,matrix=M,verts=r);return r
def cyl(bm,cx,cy,z0,z1,r0,r1,seg=8):
    res=bmesh.ops.create_cone(bm,cap_ends=True,segments=seg,radius1=r0,radius2=r1,depth=z1-z0)['verts']
    bmesh.ops.translate(bm,vec=(cx,cy,(z0+z1)/2),verts=res);return res
def obj(name,builder,matname,tile=2.0):
    bm=bmesh.new();builder(bm);bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>4]);me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free()
    o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o)
    me.materials.append(mat(matname));boxuv(me,tile);return o
def boxuv(me,tile):
    uv=me.uv_layers.new(name='UV')
    for p in me.polygons:
        n=p.normal;ax=max(range(3),key=lambda i:abs(n[i]))
        for li in p.loop_indices:
            co=me.vertices[me.loops[li].vertex_index].co
            a,b={0:(co.y,co.z),1:(co.x,co.z),2:(co.x,co.y)}[ax]
            uv.data[li].uv=(a/tile,b/tile)
def setuv_rect(o,uvrect):  # map +/-Y facing faces' bounding to a uv rect (u0,v0,u1,v1)
    me=o.data;uv=me.uv_layers['UV'];xs=[v.co.x for v in me.vertices];zs=[v.co.z for v in me.vertices]
    x0,x1,z0,z1=min(xs),max(xs),min(zs),max(zs)
    for p in me.polygons:
        if abs(p.normal.y)>0.9:
            for li in p.loop_indices:
                co=me.vertices[me.loops[li].vertex_index].co;fx=(co.x-x0)/(x1-x0);fz=(co.z-z0)/(z1-z0)
                if p.normal.y>0: fx=1-fx
                uv.data[li].uv=(uvrect[0]+fx*(uvrect[2]-uvrect[0]),uvrect[1]+fz*(uvrect[3]-uvrect[1]))
        else:
            for li in p.loop_indices: uv.data[li].uv=(uvrect[0]+0.001,uvrect[1]+0.001)  # edges: black border area
# ---------------- models (origin = ground centre, +Y = facing track side) ----------------
def tower():
    W,D=7.0,5.0
    obj('tower_body',lambda bm:(box(bm,0,0,1.6,W,D,3.2),box(bm,0,0,4.8,W,D,3.2)),'own_tower_paint',2)
    obj('tower_cab',lambda bm:(box(bm,0,0,6.4+0.5,W+1,D+1,1.0),box(bm,0,0,9.3,W+1,D+1,0.8)),'own_tower_paint',2)
    obj('tower_glass',lambda bm:box(bm,0,0,8.15,W+0.9,D+0.9,1.5),'own_tower_glass',2)
    obj('tower_roof',lambda bm:box(bm,0,0,9.9,W+2.4,D+2.4,0.35),'own_galv',3)
    def windows(bm):
        for z in (1.8,5.0):
            for x in (-2.2,0,2.2): box(bm,x,D/2+0.02,z,1.2,0.05,1.0)
        box(bm,-W/2-0.02,1.2,1.1,0.05,1.0,2.2)  # door
    obj('tower_windows',windows,'own_tower_glass',2)
    def stairs(bm):  # external switchback stair on +X side
        x0=W/2+0.75;steps=11;rise=3.2/2/steps
        for fl in range(2):  # floor 0->1 and 1->2 (two flights each)
            for f in range(2):
                for s in range(steps):
                    z=fl*3.2+f*1.6+s*rise+rise;y=(-D/2+0.6+s*0.28) if f==0 else (D/2-0.6-s*0.28)
                    xo=x0+(0 if f==0 else 1.1)
                    box(bm,xo,y,z,1.0,0.28,0.05)
                box(bm,x0+0.55,(D/2-0.3) if f==0 else (-D/2+0.3),fl*3.2+(f+1)*1.6,2.2,0.9,0.08)  # landing
        for (x,y) in((x0-0.5,-D/2),(x0+1.6,-D/2),(x0-0.5,D/2),(x0+1.6,D/2)): box(bm,x,y,3.2,0.1,0.1,6.4)  # posts
        for z in (1.0,2.6,4.2,5.8): box(bm,x0+1.65,0,z+1.0,0.05,D,0.05)  # rails
    obj('tower_stairs',stairs,'own_galv',1)
    obj('tower_antenna',lambda bm:cyl(bm,-2.5,-1.5,10.0,13.3,0.04,0.02,6),'own_galv',1)
def grandstand():
    L=20.0;rows=8;rise=0.40;depth=0.75
    def seats(bm):
        for r in range(rows):
            z=0.45+r*rise;y=-r*depth
            box(bm,0,y,z,L,0.30,0.05);box(bm,0,y-0.35,z-0.2,L,0.25,0.03)  # seat + foot plank
    obj('gs_seats',seats,'own_alu',2)
    def frame(bm):
        for x in [-L/2+0.2+i*(L-0.4)/5 for i in range(6)]:
            for r in range(rows):
                h=0.45+r*rise;box(bm,x,-r*depth,h/2,0.08,0.08,h)
            box(bm,x,-(rows-1)*depth/2,0.45+(rows-1)*rise/2,0.06,rows*depth,0.06,0)
        top=0.45+rows*rise
        box(bm,0,-(rows-1)*depth-0.3,top+0.6,L,0.05,0.05);box(bm,0,-(rows-1)*depth-0.3,top+0.1,L,0.05,0.05)
        for x in (-L/2,L/2): box(bm,x,-(rows-1)*depth/2,top/2+0.5,0.05,rows*depth,0.05)
    obj('gs_frame',frame,'own_galv',1)
def brakeboard(num):
    obj(f'bb{num}_post',lambda bm:(box(bm,-0.45,0,1.0,0.08,0.08,2.0),box(bm,0.45,0,1.0,0.08,0.08,2.0)),'own_galv',1)
    o=obj(f'bb{num}_board',lambda bm:box(bm,0,0,1.55,1.2,0.04,0.9),'own_boards',1)
    i={3:0,2:1,1:2}[num];setuv_rect(o,(i/3+0.005,0.02,(i+1)/3-0.005,0.98))
def hut():
    obj('hut_body',lambda bm:(box(bm,0,0,1.25,2.4,2.0,2.5),box(bm,0,0,2.6,2.7,2.3,0.2)),'own_hut_white',1)
    obj('hut_openings',lambda bm:(box(bm,0,1.01,1.5,1.4,0.04,0.8),box(bm,1.21,0,1.0,0.04,0.9,2.0)),'own_tower_glass',1)
    def awning(bm):
        v=box(bm,0,1.9,2.35,2.6,1.6,0.04);bmesh.ops.rotate(bm,cent=(0,1.9,2.35),matrix=Matrix.Rotation(math.radians(-12),3,'X'),verts=v)
        for x in (-1.2,1.2): cyl(bm,x,2.6,0,2.2,0.03,0.03,6)
    obj('hut_awning',awning,'own_awning',1)
def flagpole():
    obj('flag_pole',lambda bm:(cyl(bm,0,0,0,18,0.11,0.05,10),cyl(bm,0,0,18,18.15,0.09,0.09,8)),'own_galv',1)
    def flag(bm):
        bmesh.ops.create_grid(bm,x_segments=8,y_segments=4,size=1.0)
        for v in bm.verts: x,y=v.co.x,v.co.y;v.co=Vector(((x+1)/2*2.44+0.06,0.06*math.sin((x+1)*3),17.95-((y+1)/2)*1.52))
    o=obj('flag_cloth',flag,'own_flag',1)
    me=o.data;uv=me.uv_layers['UV']
    for p in me.polygons:
        for li in p.loop_indices:
            co=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=((co.x-0.06)/2.44,(co.z-(17.95-1.52))/1.52)
    me.update()
MODELS={'tower':tower,'grandstand':grandstand,'brakeboards':lambda:[brakeboard(n) for n in (3,2,1)],'hut':hut,'flagpole':flagpole}
def dump(name):
    data=[]
    for o in bpy.context.scene.objects:
        if o.type!='MESH':continue
        me=o.data;me.calc_loop_triangles();me.calc_tangents(uvmap='UV')
        uv=me.uv_layers['UV'].data;V=[];I=[]
        for t in me.loop_triangles:
            idx=[]
            for li in t.loops:
                l=me.loops[li];co=o.matrix_world@me.vertices[l.vertex_index].co
                n=t.normal if not t.use_smooth else l.normal
                V.append([co.x,co.y,co.z,n.x,n.y,n.z,uv[li].uv.x,uv[li].uv.y,l.tangent.x,l.tangent.y,l.tangent.z]);idx.append(len(V)-1)
            I.append(idx)
        data.append(dict(name=o.name,material=me.materials[0].name,verts=V,tris=I))
    return data
os.makedirs(OUT,exist_ok=True)
for name,fn in MODELS.items():
    reset();fn()
    d=f'{OUT}/{name}';os.makedirs(d,exist_ok=True)
    js=dump(name);json.dump(js,open(f'{d}/{name}_mesh.json','w'))
    print(name,'tris',sum(len(x['tris']) for x in js))
    bpy.ops.wm.save_as_mainfile(filepath=f'{d}/{name}.blend')
    bpy.ops.export_scene.fbx(filepath=f'{d}/{name}.fbx',axis_forward='-Z',axis_up='Y',apply_unit_scale=True,mesh_smooth_type='FACE')
