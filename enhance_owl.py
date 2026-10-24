"""Non-destructive Cyber Owl lighting experiment in Blender (bpy).

Imports an original GLB, adds physically separate light-strip geometry, and exports
an editable .blend and enhanced .glb. Procedural strips are *surface projected*;
actual recessed placement remains to be evaluated after inspecting renders.
"""
import bpy, math, os, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree

args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if len(args)<2:
    raise SystemExit('usage: blender -b -P enhance_owl.py -- source.glb output_directory')
source,outdir=args[:2]
os.makedirs(outdir,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(source))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
if not meshes: raise ValueError('Input has no mesh')
# Imported glTF mesh will generally point toward -Y in Blender coordinates.
# FRONT_SIGN can be flipped and the full test repeated without modifying the source.
front_sign=int(os.environ.get('OWL_FRONT_SIGN','-1'))
if front_sign not in (-1,1):raise ValueError('OWL_FRONT_SIGN must be -1 or 1')
coords=[]
for o in meshes:
    coords.extend([o.matrix_world @ Vector(v) for v in o.bound_box])
lo=Vector([min(v[i] for v in coords) for i in range(3)])
hi=Vector([max(v[i] for v in coords) for i in range(3)])
center=(lo+hi)/2
width=hi.x-lo.x;height=hi.z-lo.z;depth=hi.y-lo.y
print('OWL_BOUNDS',tuple(lo),tuple(hi),'MESHES',len(meshes),'TRIS',sum(len(o.data.polygons) for o in meshes))
# Cached BVH trees for world-space ray casts; full-res mesh is not modified.
# Meshes assumed static, no destructively applied modifiers.
trees=[]
for o in meshes:
    verts=[o.matrix_world @ v.co for v in o.data.vertices]
    tree=BVHTree.FromPolygons(verts,[tuple(p.vertices) for p in o.data.polygons], all_triangles=True)
    trees.append(tree)

front_y=(lo.y - .1*depth) if front_sign==-1 else (hi.y+.1*depth)
direction=Vector((0,-front_sign,0))
def project(x,z):
    origin=Vector((x,front_y,z)); best=None; distmax=float('inf')
    for tree in trees:
        point,normal,idx,dist=tree.ray_cast(origin,direction)
        if point is not None and dist<distmax:
            best=(point,normal);distmax=dist
    if best is None:return None
    point,normal=best
    return point + Vector((0,front_sign*0.0015,0))

mat=bpy.data.materials.new('Owl_Green_Internal_Emitter');mat.use_nodes=True
bsdf=mat.node_tree.nodes.get('Principled BSDF')
bsdf.inputs['Base Color'].default_value=(.004,.085,.025,1)
bsdf.inputs['Metallic'].default_value=.15
bsdf.inputs['Roughness'].default_value=.22
# Compatible with Blender's older/newer Principled shader input names.
color_key = 'Emission Color' if 'Emission Color' in bsdf.inputs else 'Emission'
strength_key = 'Emission Strength'
bsdf.inputs[color_key].default_value=(.03,1.,.19,1.)
bsdf.inputs[strength_key].default_value=1.8
# Pulse keyframes: glTF export serializes supported node-transform animations only,
# so emissive keyframes are retained in the .blend master, NOT promised in the GLB.
for frame,value in [(1,1.25),(36,2.1),(72,1.25)]:
    bsdf.inputs[strength_key].default_value=value
    bsdf.inputs[strength_key].keyframe_insert('default_value',frame=frame)

# Approximate eye/chest/wing design regions in normalized front orthographic view.
# These patterns are test placements and must be verified against an actual render.
patterns=[]
def add_polyline(name,pts,radius):
    measured=[]
    for ux,uz in pts:
        x=center.x+ux*width/2;z=lo.z+uz*height
        p=project(x,z)
        if p: measured.append(p)
    if len(measured)<3:return False
    cr=bpy.data.curves.new(name,'CURVE');cr.dimensions='3D';cr.resolution_u=2
    cr.bevel_depth=radius;cr.resolution_u=2;cr.bevel_resolution=2
    spline=cr.splines.new('POLY');spline.points.add(len(measured)-1)
    for item,p in zip(spline.points,measured): item.co=(*p,1)
    obj=bpy.data.objects.new(name,cr);bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return True

def arc(cx,cz,rx,rz,n=32):
    return [(cx+rx*math.cos(t*2*math.pi/n),cz+rz*math.sin(t*2*math.pi/n)) for t in range(n+1)]
# Normalized values chosen to minimize changes to the original owl's silhouette.
patterns.extend([('Left_Eye_Inner_Ring',arc(-.29,.78,.108,.047),.0012),('Right_Eye_Inner_Ring',arc(.29,.78,.108,.047),.0012)])
patterns.append(('Chest_Core_Rim',arc(0,.53,.104,.048),.00135))
for side,side_name in [(-1,'L'),(1,'R')]:
    for i in range(4):
        u0=side*(.43+i*.115)
        patterns.append((f'Wing_{side_name}_Recess_Path_{i+1}',[(u0,.69),(side*(.49+i*.108),.63),(side*(.53+i*.105),.55),(side*(.56+i*.092),.45),(side*(.58+i*.08),.36)],.0013))
for side,name in [(-1,'Left'),(1,'Right')]:
    patterns.append((f'{name}_Chest_Channel',[(side*.085,.62),(side*.14,.59),(side*.12,.53),(side*.075,.47)],.001))
created=[n for n,pts,rad in patterns if add_polyline(n,pts,rad)]
print('ADDED_LIGHT_PATHS',len(created),created)
# Leave input geometry and original mesh materials unchanged.
scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=72
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(outdir,'Cyber_Owl_Editable.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(outdir,'Cyber_Owl_LightPaths.glb'),export_format='GLB',export_animations=False,export_materials='EXPORT')
with open(os.path.join(outdir,'inspection.txt'),'w') as f:
    f.write('Source: '+os.path.basename(source)+'\n')
    f.write('Original meshes: '+str(len(meshes))+'\n')
    f.write('Original triangles: '+str(sum(len(o.data.polygons) for o in meshes))+'\n')
    f.write('Added path objects: '+str(len(created))+'\n')
    f.write('Front sign: '+str(front_sign)+'\n')
    f.write('Visual placement: NOT VERIFIED. Surface strips may cross armor.\n')
    f.write('Emissive animation: BLEND ONLY; exported GLB static.\n')
print('COMPLETE',outdir)
