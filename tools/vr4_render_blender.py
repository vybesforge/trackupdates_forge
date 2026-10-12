"""VR4 top-down renders: blender -b -P tools/vr4_render_blender.py -- <exportdir> out.png=camx,y,z,tgtx,y,z,lens ... (AC coords)"""
import bpy,glob,numpy as np,math,sys,mathutils
args=sys.argv[sys.argv.index('--')+1:];SRC=args.pop(0)  # VR4: first arg = export dir
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene
mats={}
def mat(tex,at):
    key=(tex,at)
    if key in mats: return mats[key]
    m=bpy.data.materials.new('m');m.use_nodes=True;nt=m.node_tree;b=nt.nodes['Principled BSDF'];b.inputs['Roughness'].default_value=0.85
    if tex!='None':
        t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(tex);t.interpolation='Cubic'
        nt.links.new(t.outputs['Color'],b.inputs['Base Color'])
        if at:
            mt=nt.nodes.new('ShaderNodeMath');mt.operation='GREATER_THAN';mt.inputs[1].default_value=0.5
            nt.links.new(t.outputs['Alpha'],mt.inputs[0]);nt.links.new(mt.outputs[0],b.inputs['Alpha'])
            if 'rubber' in tex: nt.links.new(t.outputs['Alpha'],b.inputs['Alpha'])   # VR5: blended decal
    else: b.inputs['Base Color'].default_value=(0.5,0.5,0.5,1)
    mats[key]=m;return m
for f in sorted(glob.glob(SRC+'/m*.npz')):
    d=np.load(f);V=d['V'];I=d['I'];u=np.unique(I);rm=-np.ones(len(V),int);rm[u]=np.arange(len(u));I=rm[I];V=V[u]
    me=bpy.data.meshes.new(str(d['name']));P=np.c_[V[:,0],-V[:,2],V[:,1]]
    me.from_pydata(P.tolist(),[],I[:,[0,2,1]].tolist());uv=me.uv_layers.new()
    loops=I[:,[0,2,1]].ravel();uvs=np.c_[V[loops,6],1-V[loops,7]];uv.data.foreach_set('uv',uvs.ravel())
    me.materials.append(mat(str(d['tex']),bool(d['at'])))
    for p in me.polygons: p.use_smooth=False
    o=bpy.data.objects.new(me.name,me);sc.collection.objects.link(o)
import os   # VR5: VR5_EMIT="mesh:r,g,b;mesh2:r,g,b" -> emissive override (tree states); VR5_NIGHT=1 -> dark sky, weak sun
for spec in [x for x in os.environ.get('VR5_EMIT','').split(';') if x]:
    nm,c=spec.split(':');c=[float(v) for v in c.split(',')]
    em=bpy.data.materials.new('emit_'+nm);em.use_nodes=True;b=em.node_tree.nodes['Principled BSDF'];b.inputs['Base Color'].default_value=(*c,1)
    b.inputs['Emission Color'].default_value=(*c,1);b.inputs['Emission Strength'].default_value=25
    for o in sc.objects:
        if o.name.startswith(nm): o.data.materials.clear();o.data.materials.append(em)
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(0.55,0.68,0.85,1);w.node_tree.nodes['Background'].inputs[1].default_value=0.03 if os.environ.get('VR5_NIGHT') else 0.8
s=bpy.data.lights.new('sun','SUN');s.energy=0.15 if os.environ.get('VR5_NIGHT') else 3.5;so=bpy.data.objects.new('sun',s);so.rotation_euler=(math.radians(25),0,math.radians(-35));sc.collection.objects.link(so)
sc.render.engine='CYCLES';sc.cycles.samples=48;sc.cycles.device='CPU';sc.render.resolution_x=1600;sc.render.resolution_y=int(__import__('os').environ.get('VR4_RESY','1000'))
sc.view_settings.view_transform='Standard'
def shot(loc,tgt,lens,out):
    c=bpy.data.cameras.new('c');c.lens=lens;c.clip_end=5000;co=bpy.data.objects.new('c',c);sc.collection.objects.link(co);co.location=loc
    d=mathutils.Vector(tgt)-mathutils.Vector(loc);co.rotation_euler=(0,0,0) if abs(d.x)+abs(d.y)<1e-6 else d.to_track_quat('-Z','Y').to_euler();sc.camera=co  # straight down: image up = north (-z)
    sc.render.filepath=out;bpy.ops.render.render(write_still=True)
def ac(x,y,z): return (x,-z,y)
for a in args:
    n,rest=a.split('=');v=[float(t) for t in rest.split(',')]
    shot(ac(*v[0:3]),ac(*v[3:6]),v[6],n)
