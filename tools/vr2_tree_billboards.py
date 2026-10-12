# blender -b -P tools/vr2_tree_billboards.py -- <outdir>
# Renders CC0 Poly Haven tree models as orthographic alpha billboards (2048 px) for the tree2/tree3 2x2 atlases.
import bpy,sys,math,os
from mathutils import Vector
OUT=sys.argv[sys.argv.index('--')+1];PH='/workspace/rpotm/cc0/polyhaven'
JOBS=[('tree2_0','tree_small_02',0),('tree2_1','island_tree_01',0),('tree2_2','tree_small_02',90),('tree2_3','island_tree_01',120),
      ('tree3_0','island_tree_01',240),('tree3_1','tree_small_02',180),('tree3_2','island_tree_01',60),('tree3_3','tree_small_02',270)]
for name,asset,rot in JOBS:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=f'{PH}/{asset}/{asset}.gltf')
    objs=[o for o in bpy.context.scene.objects if o.type=='MESH']
    piv=bpy.data.objects.new('pivot',None);bpy.context.scene.collection.objects.link(piv)
    for o in list(bpy.context.scene.objects):
        if o.parent is None and o is not piv: o.parent=piv
    piv.rotation_euler[2]=math.radians(rot)
    bpy.context.view_layer.update()
    pts=[o.matrix_world@Vector(c) for o in objs for c in o.bound_box]
    x0=min(p.x for p in pts);x1=max(p.x for p in pts);z0=min(p.z for p in pts);z1=max(p.z for p in pts)
    h=z1-z0;w=x1-x0;s=max(h/0.96,w/0.96)
    cam=bpy.data.cameras.new('c');cam.type='ORTHO';cam.ortho_scale=s;co=bpy.data.objects.new('c',cam);bpy.context.scene.collection.objects.link(co)
    co.location=((x0+x1)/2,-100,z0-0.02*s+s/2);co.rotation_euler=(math.radians(90),0,0);bpy.context.scene.camera=co
    sun=bpy.data.lights.new('s','SUN');sun.energy=4;so=bpy.data.objects.new('s',sun);so.rotation_euler=(math.radians(50),0,math.radians(25));bpy.context.scene.collection.objects.link(so)
    w_=bpy.data.worlds.new('w');w_.use_nodes=True;w_.node_tree.nodes['Background'].inputs[0].default_value=(0.55,0.62,0.7,1);w_.node_tree.nodes['Background'].inputs[1].default_value=0.9;bpy.context.scene.world=w_
    sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=48;sc.cycles.device='CPU';sc.render.film_transparent=True
    sc.render.resolution_x=sc.render.resolution_y=2048;sc.render.image_settings.color_mode='RGBA';sc.view_settings.view_transform='Standard'
    sc.render.filepath=f'{OUT}/{name}.png';bpy.ops.render.render(write_still=True);print('rendered',name,asset,rot,round(h,1),'m')
