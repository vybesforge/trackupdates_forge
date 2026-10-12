import bpy,sys,os,math
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:];blend,tex,out=a
bpy.ops.wm.open_mainfile(filepath=blend)
for m in bpy.data.materials:
    nt=m.node_tree;b=nt.nodes.get('Principled BSDF');img=nt.nodes.new('ShaderNodeTexImage')
    img.image=bpy.data.images.load(f'{tex}/{m.name}.png');nt.links.new(img.outputs['Color'],b.inputs['Base Color'])
    b.inputs['Roughness'].default_value=0.6
for o in bpy.context.scene.objects:
    if o.name[:2]=='bb' and o.name[2].isdigit(): o.location.x+=(2-int(o.name[2]))*2.0
objs=[o for o in bpy.context.scene.objects if o.type=='MESH']
pts=[o.matrix_world@Vector(c) for o in objs for c in o.bound_box];mn=Vector([min(p[i] for p in pts) for i in range(3)]);mx=Vector([max(p[i] for p in pts) for i in range(3)])
c=(mn+mx)/2;r=(mx-mn).length/2
bpy.ops.object.camera_add();cam=bpy.context.object;bpy.context.scene.camera=cam;cam.data.lens=35
d=Vector((0.4,1.6,0.5)).normalized();cam.location=c+d*r*2.6
cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.light_add(type='SUN');s=bpy.context.object;s.rotation_euler=(math.radians(50),0,math.radians(30));s.data.energy=4
bpy.ops.mesh.primitive_plane_add(size=r*8,location=(c.x,c.y,mn.z-0.01));g=bpy.context.object;gm=bpy.data.materials.new('g');gm.use_nodes=True;gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.18,0.3,0.12,1);g.data.materials.append(gm)
w=bpy.data.worlds.new('w');bpy.context.scene.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(0.55,0.7,0.95,1);w.node_tree.nodes['Background'].inputs[1].default_value=0.8
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=24;sc.render.resolution_x=960;sc.render.resolution_y=640;sc.render.filepath=out
bpy.ops.render.render(write_still=True)
