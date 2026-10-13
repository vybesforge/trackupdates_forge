"""Generic unbranded 4-door crew-cab full-size pickup (Silverado-like proportions), modelled procedurally in Blender 4.2.
blender -b -P tools/vr6_pickup_blender.py -- <outdir>
Writes <outdir>/pickup.obj (+.mtl), <outdir>/pickup_diffuse.png (base colours x baked AO, 2048^2), preview renders.
Local frame (Blender): +X = front, +Y = left, +Z = up, ground at z=0. Size ~5.9 x 2.03 x 1.92 m."""
import bpy,bmesh,sys,math,os
from mathutils import Vector
OUT=sys.argv[sys.argv.index('--')+1];os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene
M={}
def mat(n,c,metal=0.0,rough=0.5):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=(*c,1);b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough;M[n]=m;return m
mat('paint',(0.035,0.055,0.11),0.6,0.3);mat('chrome',(0.75,0.76,0.78),1.0,0.15);mat('trim',(0.025,0.025,0.028),0,0.6)
mat('glass',(0.03,0.04,0.05),0,0.05);mat('tire',(0.03,0.03,0.03),0,0.85);mat('rim',(0.55,0.56,0.58),0.9,0.3)
mat('light',(0.9,0.9,0.85),0,0.1);mat('tail',(0.55,0.03,0.02),0,0.2);mat('grille',(0.04,0.04,0.045),0.3,0.5);mat('bedliner',(0.03,0.03,0.03),0,0.9)
objs=[]
def new(name,bm,m):
    me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);sc.collection.objects.link(o);o.data.materials.append(M[m]);objs.append(o);return o
def prism(name,prof,y0,y1,m,bev=0.0,seg=3):
    """profile [(x,z)] extruded along y from y0 to y1"""
    bm=bmesh.new();a=[bm.verts.new((x,y0,z)) for x,z in prof];b=[bm.verts.new((x,y1,z)) for x,z in prof]
    bm.faces.new(a[::-1]);bm.faces.new(b)
    n=len(prof)
    for i in range(n): bm.faces.new([a[i],a[(i+1)%n],b[(i+1)%n],b[i]])
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);o=new(name,bm,m)
    if bev:
        md=o.modifiers.new('b','BEVEL');md.width=bev;md.segments=seg;md.limit_method='ANGLE';md.angle_limit=math.radians(30)
    return o
def box(name,c,s,m,bev=0.0):
    bm=bmesh.new();bmesh.ops.create_cube(bm,size=1.0);
    for v in bm.verts: v.co=Vector((v.co.x*s[0]+c[0],v.co.y*s[1]+c[1],v.co.z*s[2]+c[2]))
    o=new(name,bm,m)
    if bev: md=o.modifiers.new('b','BEVEL');md.width=bev;md.segments=2
    return o
def cyl(name,c,r,depth,m,axis='Y',verts=32,bev=0.0):
    bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=True,segments=verts,radius1=r,radius2=r,depth=depth)
    for v in bm.verts:
        x,y,z=v.co
        if axis=='Y': v.co=Vector((x+c[0],z+c[1],y+c[2]))
        else: v.co=Vector((x+c[0],y+c[1],z+c[2]))
    o=new(name,bm,m)
    if bev: md=o.modifiers.new('b','BEVEL');md.width=bev;md.segments=3
    return o
W=1.0   # half width body
# --- lower body side profile (x,z): front bumper top -> hood -> cowl -> (cab cut) -> bed rail -> tailgate
body=[(2.95,0.42),(2.98,0.80),(2.93,1.12),(2.75,1.20),(1.35,1.27),(1.05,1.30),(-1.35,1.30),(-1.35,1.24),(-2.95,1.24),(-2.97,0.45),(-2.6,0.38),(2.6,0.38)]
b=prism('body',body,-W,W,'paint',bev=0.04)
# wheel arches: boolean cut
for wx in(1.86,-1.86):
    cut=cyl('arch',(wx,0,0.42),0.50,2.4,'trim',verts=40);md=b.modifiers.new('arch','BOOLEAN');md.object=cut;md.operation='DIFFERENCE';cut.hide_render=True;cut.display_type='WIRE'
# bed: cut the box from the rear part
bed=box('bedcut',(-2.15,0,1.05),(1.62,1.82,0.62),'trim');md=b.modifiers.new('bed','BOOLEAN');md.object=bed;md.operation='DIFFERENCE';bed.hide_render=True
box('bedfloor',(-2.15,0,0.76),(1.62,1.82,0.03),'bedliner')
# cab greenhouse: glass prism inset, roof + pillars painted
gh=[(1.02,1.30),(0.10,1.88),(-1.18,1.90),(-1.32,1.30)]
prism('glass',gh,-0.92,0.92,'glass',bev=0.03)
prism('roof',[(0.16,1.86),(0.06,1.925),(-1.20,1.935),(-1.26,1.87)],-0.90,0.90,'paint',bev=0.03)
for i,(x0,x1) in enumerate([(1.02,0.10),(-1.30,-1.18)]):   # A and C pillars both sides
    for sy in(1,-1): prism(f'pil{i}{sy}',[(x0,1.30),(x0-0.12 if i==0 else x0+0.1,1.30),(x1-0.1 if i==0 else x1+0.08,1.88),(x1,1.88)],sy*0.90,sy*0.935,'paint')
for sy in(1,-1): box(f'bpil{sy}',(-0.42,sy*0.925,1.6),(0.12,0.03,0.62),'paint')
# door seams + handles + mirrors + steps
for sy in(1,-1):
    for x in(1.02,-0.42,-1.32): box(f'seam{x}{sy}',(x,sy*(W+0.002),0.85),(0.012,0.006,0.9),'trim')
    for x in(0.55,-0.85): box(f'hdl{x}{sy}',(x,sy*(W+0.012),1.1),(0.18,0.02,0.045),'chrome')
    box(f'mirr{sy}',(0.98,sy*1.13,1.42),(0.22,0.22,0.2),'trim',bev=0.02)
    box(f'step{sy}',(-0.2,sy*0.98,0.36),(2.6,0.14,0.05),'trim',bev=0.01)
    box(f'flare_f{sy}',(1.86,sy*(W+0.01),0.86),(1.1,0.03,0.08),'trim')
    box(f'flare_r{sy}',(-1.86,sy*(W+0.01),0.86),(1.1,0.03,0.08),'trim')
# front: grille, headlights, bumper; rear: taillights, bumper, tailgate handle
box('grille_frame',(2.965,0,0.96),(0.06,1.55,0.42),'chrome',bev=0.02);box('grille',(2.985,0,0.96),(0.03,1.35,0.32),'grille')
for yb in(-0.25,0.0,0.25): box(f'gbar{yb}',(2.995,0,0.96+yb*0.4),(0.02,1.35,0.025),'chrome')
for sy in(1,-1): box(f'head{sy}',(2.94,sy*0.83,1.04),(0.08,0.30,0.16),'light',bev=0.01)
box('fbump',(2.98,0,0.55),(0.22,2.02,0.26),'chrome',bev=0.04);box('fbump_low',(2.92,0,0.38),(0.2,1.7,0.08),'trim')
for sy in(1,-1): box(f'tail{sy}',(-2.965,sy*0.93,1.02),(0.05,0.12,0.38),'tail',bev=0.01)
box('rbump',(-3.0,0,0.52),(0.18,2.0,0.2),'chrome',bev=0.03);box('tg_handle',(-2.975,0,1.13),(0.02,0.28,0.06),'trim')
# wheels
for wx in(1.86,-1.86):
    for sy in(1,-1):
        cyl(f'tire{wx}{sy}',(wx,sy*0.86,0.40),0.40,0.28,'tire',bev=0.06)
        cyl(f'rim{wx}{sy}',(wx,sy*0.995,0.40),0.25,0.03,'rim',verts=24)
        cyl(f'hub{wx}{sy}',(wx,sy*1.012,0.40),0.07,0.02,'chrome',verts=16)
        for k in range(6):
            a=k*math.pi/3;o=box(f'sp{wx}{sy}{k}',(wx+0.13*math.cos(a),sy*1.0,0.40+0.13*math.sin(a)),(0.05,0.02,0.2),'rim');o.rotation_euler=(0,-a+math.pi/2,0)
# apply modifiers, join
bpy.context.view_layer.update()
for o in list(sc.objects):
    if o.hide_render: continue
    bpy.context.view_layer.objects.active=o;o.select_set(True)
    for md in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=md.name)
    o.select_set(False)
for o in [o for o in sc.objects if o.hide_render]: bpy.data.objects.remove(o)
for o in sc.objects: o.select_set(True)
bpy.context.view_layer.objects.active=sc.objects['body'];bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);bpy.ops.object.join()
T=bpy.context.active_object;T.name='pickup'
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.quads_convert_to_tris()
bpy.ops.uv.smart_project(angle_limit=math.radians(60),island_margin=0.004);bpy.ops.object.mode_set(mode='OBJECT')
# ground plane (for AO only)
bpy.ops.mesh.primitive_plane_add(size=12,location=(0,0,0));G=bpy.context.active_object
# bake AO and diffuse colour
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=64
def bake(kind,name):
    img=bpy.data.images.new(name,2048,2048)
    for m in M.values():
        nt=m.node_tree;n=nt.nodes.get('bake') or nt.nodes.new('ShaderNodeTexImage');n.name='bake';n.image=img;nt.nodes.active=n
    for o in sc.objects: o.select_set(False)
    T.select_set(True);bpy.context.view_layer.objects.active=T
    if kind=='DIFFUSE': sc.render.bake.use_pass_direct=False;sc.render.bake.use_pass_indirect=False;sc.render.bake.use_pass_color=True
    sc.render.bake.margin=8;bpy.ops.object.bake(type=kind);img.filepath_raw=f'{OUT}/{name}.png';img.file_format='PNG';img.save();return img
bake('AO','pickup_ao');bake('DIFFUSE','pickup_col')
bpy.data.objects.remove(G)
for m in M.values():
    n=m.node_tree.nodes.get('bake')
    if n: m.node_tree.nodes.remove(n)
bpy.ops.wm.obj_export(filepath=f'{OUT}/pickup.obj',export_selected_objects=False,export_uv=True,export_normals=True,export_materials=True,forward_axis='Y',up_axis='Z',export_triangulated_mesh=True)
print('faces',len(T.data.polygons))
