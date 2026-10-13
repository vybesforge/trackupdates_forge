"""Aerial preview of the paddock spawns. blender -b -P spawn_render_blender.py -- <objdir> <out.png>
Scene: OBJ from tools/north_ext/kn5_to_obj.py; markers.json (pits: idx,x,y,z,fx,fy,fz; path: [[x,z],..]). AC (x,y,z) -> Blender (x,-z,y)."""
import bpy,json,math,sys,mathutils
a=sys.argv[sys.argv.index('--')+1:];D,OUT=a[0],a[1]
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene
bpy.ops.wm.obj_import(filepath=f'{D}/scene.obj',forward_axis='Y',up_axis='Z')
for o in list(sc.objects):
    if o.name.startswith('AC_'): bpy.data.objects.remove(o)
for m in bpy.data.materials:
    if m.node_tree:
        for n in m.node_tree.nodes:
            if n.type=='BSDF_PRINCIPLED': n.inputs['Roughness'].default_value=0.9
def emat(name,col,strength=1.5):
    m=bpy.data.materials.new(name);m.use_nodes=True;b=m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=col;b.inputs['Emission Color'].default_value=col;b.inputs['Emission Strength'].default_value=strength;return m
J=json.load(open(f'{D}/markers.json'))
mc=emat('car',(1,0.15,0.05,1));ma=emat('arrow',(1,0.9,0.1,1));mp=emat('path',(0.1,0.9,1,1),2.5)
def ac(x,y,z): return mathutils.Vector((x,-z,y))
for i,x,y,z,fx,fy,fz in J['pits']:
    g=-0.10;ang=math.atan2(-fz,fx)  # heading in Blender xy
    bpy.ops.mesh.primitive_cube_add(size=1,location=ac(x,g+0.6,z));o=bpy.context.object;o.scale=(4.4,1.9,1.2);o.rotation_euler=(0,0,ang);o.data.materials.append(mc)
    tip=ac(x+fx*3.4,g+1.4,z+fz*3.4);bpy.ops.mesh.primitive_cone_add(radius1=1.2,depth=2.4,location=tip,rotation=(0,math.pi/2,ang));c=bpy.context.object;c.data.materials.append(ma)
    bpy.ops.object.text_add(location=ac(x,g+1.3,z));t=bpy.context.object;t.rotation_euler=(0,0,math.pi);t.data.body=str(i);t.data.size=1.6;t.data.align_x='CENTER';t.data.align_y='CENTER';t.data.materials.append(emat('t',(1,1,1,1),3))
P=J['path'][::4]
cu=bpy.data.curves.new('path','CURVE');cu.dimensions='3D';sp=cu.splines.new('POLY');sp.points.add(len(P)-1)
for k,(x,z) in enumerate(P): sp.points[k].co=(*ac(x,0.4,z),1)
cu.bevel_depth=0.5;po=bpy.data.objects.new('path',cu);po.data.materials.append(mp);sc.collection.objects.link(po)
for txt,(x,z),s in [('large green paddock building',(100,31),3.5),('old tent area (paddock lot)',(118,118),3.5),('exit -> pit-exit gate -> pit-out road -> track',(-20,60),3.0)]:
    bpy.ops.object.text_add(location=ac(x,8,z));t=bpy.context.object;t.rotation_euler=(0,0,math.pi);t.data.body=txt;t.data.size=s;t.data.align_x='CENTER';t.data.materials.append(emat('l',(1,1,1,1),4))
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;bg=w.node_tree.nodes['Background'];bg.inputs[0].default_value=(0.55,0.68,0.85,1);bg.inputs[1].default_value=0.9
s=bpy.data.lights.new('sun','SUN');s.energy=3.5;so=bpy.data.objects.new('sun',s);so.rotation_euler=(math.radians(35),0,math.radians(-30));sc.collection.objects.link(so)
sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.device='CPU';sc.render.resolution_x=1800;sc.render.resolution_y=1200;sc.view_settings.view_transform='Standard'
cam=bpy.data.cameras.new('c');cam.lens=24;cam.clip_end=3000;co=bpy.data.objects.new('c',cam);sc.collection.objects.link(co)
co.location=ac(55,120,-25);d=ac(60,0,70)-co.location;co.rotation_euler=d.to_track_quat('-Z','Y').to_euler();sc.camera=co
sc.render.filepath=OUT;bpy.ops.render.render(write_still=True)
