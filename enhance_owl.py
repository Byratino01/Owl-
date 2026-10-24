"""Non-destructive Cyber Owl Blender lighting prototype.

Preserves imported GLB meshes and PBR materials. Adds independently named,
procedurally surface-projected emissive geometry. It is NOT a verified
under-feather placement or an exported material animation.
Usage: blender -b -P enhance_owl.py -- source.glb output_directory
"""
import json
import math
import os
import struct
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(argv) != 2:
    raise SystemExit("Usage: blender -b -P enhance_owl.py -- source.glb output_directory")
source, outdir = argv
source = os.path.abspath(source)
outdir = os.path.abspath(outdir)
if not os.path.isfile(source):
    raise FileNotFoundError(source)
os.makedirs(outdir, exist_ok=True)

# Clearing Blender's empty/default *working scene* does not alter source GLB.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=source)
originals = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
if not originals:
    raise RuntimeError("Input GLB has no meshes")
original_names = [o.name for o in originals]
original_faces = sum(len(o.data.polygons) for o in originals)
original_material_slots = sum(len(o.material_slots) for o in originals)

points = [obj.matrix_world @ Vector(corner) for obj in originals for corner in obj.bound_box]
lo = Vector(tuple(min(p[i] for p in points) for i in range(3)))
hi = Vector(tuple(max(p[i] for p in points) for i in range(3)))
center = (lo + hi) * 0.5
width, depth, height = hi.x-lo.x, hi.y-lo.y, hi.z-lo.z
if min(width, depth, height) <= 0:
    raise RuntimeError("Degenerate model dimensions")

front_sign = int(os.environ.get("OWL_FRONT_SIGN", "-1"))
if front_sign not in (-1, 1):
    raise ValueError("OWL_FRONT_SIGN must equal -1 or 1")
# -1 means face is on negative world Y; shoot rays inward along +Y.
front_y = lo.y - 0.1*depth if front_sign == -1 else hi.y + 0.1*depth
direction = Vector((0, -front_sign, 0))
depsgraph = bpy.context.evaluated_depsgraph_get()
scene = bpy.context.scene

# Cache the original mesh ray hits BEFORE generating any new mesh objects.
def surface_point(ux, uz):
    origin = Vector((center.x + ux*width/2, front_y, lo.z + uz*height))
    hit, position, normal, face_index, obj, matrix = scene.ray_cast(
        depsgraph, origin, direction, distance=depth*1.5
    )
    if not hit or obj.type != "MESH":
        return None
    # Offset along the actual surface normal, avoiding z-fighting.
    return position + normal.normalized() * max(height * 0.0008, 0.0003)

material = bpy.data.materials.new("Owl_Green_Light_Strips")
material.use_nodes = True
bsdf = material.node_tree.nodes.get("Principled BSDF")
if bsdf is None:
    raise RuntimeError("Principled BSDF missing")
bsdf.inputs["Base Color"].default_value = (0.004, 0.07, 0.02, 1)
bsdf.inputs["Metallic"].default_value = 0.08
bsdf.inputs["Roughness"].default_value = 0.25
emission_name = "Emission Color" if "Emission Color" in bsdf.inputs else "Emission"
bsdf.inputs[emission_name].default_value = (0.035, 1.0, 0.16, 1)
bsdf.inputs["Emission Strength"].default_value = 1.5
# Pulse is saved in the BLEND only. GLB export uses static emission.
for frame, strength in ((1, 1.1), (36, 1.8), (72, 1.1)):
    bsdf.inputs["Emission Strength"].default_value = strength
    bsdf.inputs["Emission Strength"].keyframe_insert("default_value", frame=frame)
scene.frame_start, scene.frame_end = 1, 72
scene.frame_set(1)

def arc(cx, cz, rx, rz, samples=32):
    return [(cx + rx*math.cos(2*math.pi*i/samples),
             cz + rz*math.sin(2*math.pi*i/samples))
            for i in range(samples + 1)]

patterns = [
    ("Left_Eye_Ring", arc(-0.29, 0.78, 0.108, 0.047), 0.0012),
    ("Right_Eye_Ring", arc(0.29, 0.78, 0.108, 0.047), 0.0012),
    ("Chest_Core_Ring", arc(0, 0.53, 0.104, 0.048), 0.00135),
]
for side, label in ((-1, "L"), (1, "R")):
    for i in range(4):
        x = side*(0.43 + i*0.115)
        patterns.append((f"Wing_{label}_Path_{i+1}",
            [(x, .69), (side*(.49+i*.108), .63),
             (side*(.53+i*.105), .55), (side*(.56+i*.092), .45),
             (side*(.58+i*.08), .36)], 0.0013))
    patterns.append((f"Chest_{label}_Channel",
        [(side*.085,.62),(side*.14,.59),(side*.12,.53),(side*.075,.47)],0.001))

# Resolve all mesh ray casts before introducing new geometry.
resolved = []
misses = {}
for name, coords, radius in patterns:
    hits = [surface_point(u,z) for u,z in coords]
    valid = [p for p in hits if p is not None]
    misses[name] = len(coords) - len(valid)
    # Missing points in between a line can create invalid cross-surface shortcuts.
    if any(p is None for p in hits) or len(valid) < 3:
        continue
    resolved.append((name, valid, radius))

added = []
for name, locations, radius in resolved:
    curve = bpy.data.curves.new(name, type="CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_resolution = 2
    curve.bevel_depth = radius
    spline = curve.splines.new("POLY")
    spline.points.add(len(locations) - 1)
    for point, position in zip(spline.points, locations):
        point.co = (*position, 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    # GLB supports mesh geometry reliably; explicitly convert the curve.
    bpy.ops.object.convert(target="MESH")
    added.append(bpy.context.view_layer.objects.active.name)

if not added:
    raise RuntimeError("No surface-projected strips created; verify OWL_FRONT_SIGN")
if sum(len(o.data.polygons) for o in originals) != original_faces:
    raise AssertionError("Original source geometry face count changed")
if sum(len(o.material_slots) for o in originals) != original_material_slots:
    raise AssertionError("Original material slots changed")

blend_path = os.path.join(outdir, "Cyber_Owl_Editable.blend")
glb_path = os.path.join(outdir, "Cyber_Owl_LightPaths.glb")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
bpy.ops.export_scene.gltf(
    filepath=glb_path, export_format="GLB",
    export_animations=False, export_materials="EXPORT"
)
# Binary GLB structure and payload check, not a visual validation.
with open(glb_path, "rb") as fh:
    header = fh.read(12)
magic, version, declared = struct.unpack("<4sII", header)
if magic != b"glTF" or version != 2 or declared != os.path.getsize(glb_path):
    raise RuntimeError("Exported GLB header or size is invalid")

report = {
    "source_filename": os.path.basename(source),
    "original_meshes": len(originals),
    "original_faces": original_faces,
    "original_material_slots": original_material_slots,
    "source_mesh_names": original_names,
    "bounds_min": list(lo),
    "bounds_max": list(hi),
    "front_sign": front_sign,
    "created_light_meshes": added,
    "omitted_paths": [name for name,_,_ in patterns if name not in added],
    "raycast_misses": misses,
    "glb_bytes": declared,
    "visual_validation": "NOT PERFORMED: placement is approximate",
    "under_feather_recessed": False,
    "emission_animation_in_glb": False,
    "notes": "BLEND has emissive keyframes; exported GLB emission is static."
}
with open(os.path.join(outdir, "inspection.json"), "w") as fh:
    json.dump(report, fh, indent=2)
print("OWL_VALIDATION", json.dumps(report))
