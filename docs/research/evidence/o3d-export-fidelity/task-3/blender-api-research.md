# Blender 4.2+ exporter contracts: independent primary-source research

Research date: 2026-11-11 (Asia/Hong_Kong). Scope: evaluated corner normals, tessellation, affine normal directions, render-active UVs, and shader Mapping semantics. No production files, shared ledger, other reports, or git commits changed.

## Evidence and limits

- **Source evidence:** Blender `v4.2.0` resolves to commit `a51f293548adba0dda086f5771401e8d8ab66227`; all source links below pin that exact revision, rather than a moving branch. The release-tag identity was fetched from the [official Blender repository tag API][S0]. Versioned 4.2 manual/API pages supplement the implementation.
- **Runtime observations:** installed Blender reports `5.0.1`, build hash `a3db93c5b259`, build date 2025-12-16. Fresh `--background --factory-startup` processes ran the geometry/affine checks and five CPU Cycles emission-bake checks described below. These observations are **not** a claim that Blender 4.2 was executed.
- **Verification:** the three exact Python code blocks embedded in this report were re-extracted and each executed in a fresh Blender process, with a 120-second per-process timeout. All three exited `0`; all five shader cases again matched their encoded analytic result with measured error `0.0`. All 24 citation definitions were checked for resolution and all three probe blocks parsed successfully.
- **Math:** explicitly identified derivations use column vectors. They are independently checkable identities, not exporter-reference behavior.
- **Policy:** recommendations about unsupported inputs or O3D conversion are identified as policy, not Blender or native-engine facts. No reference exporter was used as an oracle.
- **Tool limitation:** web search was attempted but the installed search provider returned a missing-API-key error. Installed Tavily could not start because its wrapper attempted a cache write outside the allowed workspace; no bypass, installation, authentication, or reconfiguration was performed. Official pages and pinned upstream source were successfully retrieved directly. Board tools `team_task_get`/`team_task_update` are not exposed to this child; the parent was notified to perform the current-revision claim/completion rather than hand-edit board persistence.

## 1. Preserve evaluated corner normals while tessellating

### Verified API/source facts

1. `Object.to_mesh()` on an **evaluated** object includes evaluated modifiers; on the original object it does not provide the same modifier/animation result. The documented result is temporary and object-owned. `preserve_all_data_layers=True` preserves UV maps/vertex groups and requires the dependency graph. Release it with the same evaluated object's `to_mesh_clear()`. Sources: [dependency-graph exporter example][D1], [Object API][D2], [RNA ownership and arguments][S1].
2. `Mesh.corner_normals` represents the final face-corner split directions, including sharp-face, sharp-edge, smooth-vertex, and custom-normal effects. Its 4.2 implementation lazily ensures the corner-normal cache, expands point/face normals when appropriate, and computes corner normals using custom normal data otherwise. Sources: [Mesh API][D3], [normal cache implementation][S2]. Reading this API is sufficient to request its cache; the verified 4.2 path does not require an extra split-normal recalculation call.
3. `calc_loop_triangles()` calls `mesh->corner_tris()`. That ensures a cached array of corner-index triples from existing positions, faces, and corner-to-vertex data; it does not replace the mesh's polygons or manufacture a new mesh. Sources: [RNA entry point][S3], [corner-triangle cache][S4]. This is tessellation for access, not an instruction to destructively triangulate topology.
4. `MeshLoopTriangle.loops` indexes mesh loops/corners; `vertices` is the corner-to-vertex lookup. Its `split_normals` getter directly copies `mesh->corner_normals()[tri[j]]` for each of the three triangle corners. `normal` is the geometric triangle normal and is a different property. `polygon_index` identifies the original face; `material_index` is available on the triangle. Sources: [triangle API][D4], [vertex lookup and split-normal getter][S5].
5. **Derived preservation contract:** export the evaluated mesh's `corner_normals[loop_index].vector`, `loops[loop_index].vertex_index`, and selected UV value at that same loop index, while iterating `loop_triangles`. Do not substitute a triangle normal for a flat/custom corner merely because an n-gon is being emitted as triangles. In particular, a nonplanar polygon's authored/evaluated corner normals need not equal each generated triangle's cross-product normal. This follows directly from the separate getter implementations in [S5] and the corner-normal domains in [S2].

### Minimum practical contract (policy grounded in the facts above)

- Keep the existing exporter's intended evaluation state, including any deliberate rest-space/armature suppression; this research does not authorize changing that policy. Obtain a temporary evaluated mesh in that state, call `calc_loop_triangles()`, and serialize corner attributes without topology-changing round trips. [D1], [S1], [S3], [S4]
- Copy vectors if they must outlive the temporary mesh. Read normals/UVs before `to_mesh_clear()` and pair cleanup with `finally`; do not retain RNA references after freeing their owner. [D2], [S1]
- A normal/UV seam requires distinct output corner records even when the source vertex index is shared. A split-vertex key must not collapse distinct corner attributes. This is an export representation requirement inferred from the corner-indexed attributes, not a new Blender API. [D3], [D4], [D5]
- If a nonempty mesh unexpectedly has no readable corner normals, report that case rather than silently replacing all directions with vertex normals. The public API explicitly permits an empty collection; this research did not establish every condition that produces it. [D3]

### Executed observation G1

A fresh Blender 5.0.1 process created a disconnected nonplanar quad plus concave pentagon, smooth faces, nine deliberately varying oblique custom normals, and two UV maps. It evaluated the object and copied its temporary mesh with all layers preserved. Results:

| Check | Observed result |
| --- | --- |
| Before/after `(vertices, polygons, loops)` | `(9, 2, 9)` both times |
| Triangle count | `5` |
| Triangle corner triples | `(0,1,2)`, `(0,2,3)`, `(5,6,7)`, `(7,8,4)`, `(4,5,7)` |
| Maximum normal change across tessellation | `0.0` |
| Maximum `triangle.split_normals[j]` vs saved `corner_normals[triangle.loops[j]]` difference | `0.0` |
| Editing/render UV metadata on evaluated copy | active `Editing`; `Rendering.active_render == True` |
| Render map's first UV | `(10.0, 10.0)`; deliberately distinct from editing map |

The exact diagonal/triangle ordering above is an observation for this mesh/build, **not** a cross-version order guarantee. To rerun G1 without creating a file, pass the following Python body as `blender --background --factory-startup --python-exit-code 1 --python-expr '<body>'` (or paste into Blender's Python console):

```python
import bpy
from mathutils import Vector
m = bpy.data.meshes.new('ResearchMesh')
m.from_pydata([(0,0,0),(2,0,0),(2,1,.25),(0,1,0),
              (3,0,0),(5,0,0),(5,2,0),(4,1,0),(3,2,0)],
             [], [(0,1,2,3),(4,5,6,7,8)])
m.update()
for p in m.polygons:
    p.use_smooth = True
m.normals_split_custom_set([
    Vector((.1+i*.015,.2,1)).normalized() for i in range(len(m.loops))])
a = m.uv_layers.new(name='Editing')
b = m.uv_layers.new(name='Rendering')
m.uv_layers.active_index = 0
b.active_render = True
for layer, offset in [(a,0),(b,10)]:
    for i, item in enumerate(layer.uv):
        item.vector = (offset+i*.1, offset+i*.2)
o = bpy.data.objects.new('ResearchObject',m)
bpy.context.collection.objects.link(o)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
e = o.evaluated_get(dg)
me = e.to_mesh(preserve_all_data_layers=True,depsgraph=dg)
try:
    counts = (len(me.vertices),len(me.polygons),len(me.loops))
    before = [n.vector.copy() for n in me.corner_normals]
    me.calc_loop_triangles()
    assert counts == (len(me.vertices),len(me.polygons),len(me.loops))
    assert len(me.loop_triangles) == 5
    assert max((a.vector-b).length for a,b in zip(me.corner_normals,before)) < 1e-6
    assert max((Vector(t.split_normals[j])-before[li]).length
               for t in me.loop_triangles for j,li in enumerate(t.loops)) < 1e-6
    print(counts, [tuple(t.loops) for t in me.loop_triangles])
    print(me.uv_layers.active.name, [(u.name,u.active_render) for u in me.uv_layers])
finally:
    e.to_mesh_clear()
```

**Suggested extension, not executed here:** repeat with a shared-vertex flat/smooth wedge, a sharp edge, a UV seam, and a topology-changing evaluated modifier. Compare against the evaluated mesh's own corner normal records, not the input object's corner count or a reference export. That targets the same API contracts without assuming modifier-specific topology preservation. [D1], [D3], [S2]

## 2. Affine normal directions, mirrors, and singular transforms

### Verified implementation and mathematical distinction

- **Source fact:** Cycles transforms an object-space normal by the transpose of the object's inverse transform and normalizes it, using a direction transform rather than a point transform. [S6]
- **Math:** for exported positions `p' = A p + t`, and invertible `A`, the corresponding normal direction is `normalize(A.inverted().transposed() @ n)`. Proof: for every original tangent `u` satisfying `n·u=0`, `(A^-T n)·(A u)=n·u=0`. Translation has no term in the tangent transform, so it must not enter the normal-direction multiplication. This derivation explains the [Cycles implementation][S6]; it is not an exporter convention.
- **Math:** this uses the **actual linear part of the position-space conversion**. It includes shear and nonuniform scale and must not be reconstructed from Euler angles alone. If a transform is retained in an output object matrix rather than baked into vertex positions, do not bake its normal transform a second time. How an O3D consumer combines stored object matrices and normals is a separate engine/format question, not answered by Blender APIs. [S6], plus the affine derivation above.
- **Math (mirror caveat):** `(A u) × (A v) = det(A) A^-T (u × v)`. Therefore, for negative determinant, an unchanged triangle index order has a geometric cross-product direction opposite to the inverse-transpose normal direction. Face winding and shading-normal direction are separate decisions. Cycles itself treats negative applied scale separately in geometric-normal cross-product ordering. [S7] Do not multiply every shading normal by `sign(det(A))` as a substitute for a deliberate winding contract.
- **Policy:** when baking a reflection into a target representation with fixed front-face rules, test whether triangle order must be reversed relative to the existing basis-conversion convention; carry the entire corner tuple (position/normal/UV/weights) with any index permutation. Do not infer the O3D engine's handedness/culling from Blender alone. [S7], plus the mirror identity above.
- **Source fact:** `Matrix.inverted()` rejects a noninvertible matrix unless an explicit fallback is supplied. `inverted_safe()` is **not** a genuine inverse of a singular transform: it perturbs the diagonal and may return identity if that fails. The source and embedded API docs state this behavior. [S8]
- **Math/policy:** at singular `A`, no general inverse-transpose exists. Some rank-two surfaces retain a geometric area normal, while other tangents collapse; that does not define a universally preserved authored shading normal. Rejecting singular export transforms with a specific diagnostic is the smallest unambiguous policy. If compatibility instead demands a fallback, label/test it as an approximation; do not claim `inverted_safe()` proves fidelity. Near-singular finite matrices also need a documented numerical policy rather than an unexplained universal determinant threshold. [S8], plus the affine derivation above.

### Executed observation A1 and compact reproduction

Blender 5.0.1 produced the following values from the code below: oblique/sheared normal `(0.0461757109, 0.0554108545, 0.9973952770)`; transformed tangent dot normal `1.9557774e-08`; mirror determinant `-1.5`; geometric/covector mirror normal dot `-1.0`. `diag(1,1,0).inverted()` raised `ValueError`; `inverted_safe()` returned a Z diagonal of `100000000.0`, demonstrating a perturbation rather than a physically meaningful inverse.

```python
from mathutils import Matrix, Vector
A = Matrix(((2,.4,0),(0,3,.5),(0,0,.25)))
n = Vector((1,2,3)).normalized()
n1 = (A.inverted().transposed() @ n).normalized()
u = n.cross(Vector((1,0,0)))
assert abs(n1.dot(A @ u)) < 1e-6
# Translation-independent by construction: only A, never affine t, enters n1.
mirror = Matrix.Diagonal(Vector((-2,3,.25)))
u, v = Vector((1,0,0)), Vector((0,1,0))
g = (mirror @ u).cross(mirror @ v).normalized()
s = (mirror.inverted().transposed() @ u.cross(v)).normalized()
assert g.dot(s) < -.999999
singular = Matrix.Diagonal(Vector((1,1,0)))
try:
    singular.inverted()
except ValueError:
    print('singular rejected', singular.inverted_safe())
else:
    raise AssertionError('singular inverse unexpectedly accepted')
```

**Suggested exporter probe:** use equivalent geometry with a translated parent, quaternion rotation, nonuniform/negative scale, and identical local oblique normals. Compare serialized directions with the actual chosen export-position matrix's inverse transpose; require finite, unit-length directions and translation invariance for nonsingular cases. This tests a mathematical contract rather than assuming every transform must always be baked.

## 3. Render-active UV selection is not editing-active selection

- **API/source fact:** `MeshUVLoopLayer.active` is the editing/display selection; `active_render` is the rendering selection. The RNA getters use separate CustomData selections. `uv_layers.active` therefore must not be treated as synonymous with the rendering default. [D5], [S9]
- **Renderer fact:** Cycles obtains `CustomData_get_render_layer_name(..., CD_PROP_FLOAT2)` and assigns that map to `ATTR_STD_UV`; it copies each triangle's UVs using the **same corner indices** from `corner_tris`. [S10]
- **Renderer fact:** a UV Map node with a nonempty name requests that attribute; an empty name requests `ATTR_STD_UV` (except its separate From Instances path). A named map is not overridden by whichever map happens to be render-active. [S11] The GPU image-texture node's unlinked coordinate input requests the default unnamed attribute. [S12]
- **Minimum policy:** resolve an explicitly supported named UV source first; otherwise select the evaluated mesh layer whose `active_render` flag is true. Read values per corner. If no render map exists, a chosen fallback/no-UV behavior must be explicit policy—not a claimed Blender guarantee that editing-active is equivalent. The API's modern `layer.uv[index].vector` is available in 4.2; `layer.data` is already marked deprecated there. [D5], [S9], [S10], [S11]
- **Scope/policy:** one exported UV stream cannot reproduce arbitrary different coordinate sources used simultaneously by multiple texture channels. Generated/Object coordinates, From Instances, linked Mapping inputs, and arbitrary shader expressions require their own support decision; this report does not endorse silently treating them as static UVs. [D1], [S11], [S12]

Observation G1 above independently demonstrated editing/render selection divergence surviving `to_mesh(preserve_all_data_layers=True, ...)`. It did **not** render the two maps; the render-default claim rests on the explicit Cycles source, not that metadata-only observation.

## 4. Mapping node POINT, TEXTURE, and VECTOR

### Minimum shader contract

Let `v` be the input 3-vector, `t` Location, `s` componentwise Scale, and `R = Euler(rotation, 'XYZ').to_matrix()`. These formulas are **shader implementation facts**, confirmed independently in the 4.2 GPU shader and Cycles SVM, with the manual explaining the semantic modes. [S13], [S14], [D6]

| Mode | Exact operation, column-vector notation | Homogeneous composition for nonsingular scale |
| --- | --- | --- |
| `POINT` | `R @ (v * s) + t` | `T @ R @ S` |
| `TEXTURE` | `safe_divide(R.transposed() @ (v - t), s)` | `(T @ R @ S)^-1 = S^-1 @ R^-1 @ T^-1` |
| `VECTOR` | `R @ (v * s)`; no translation | `R @ S`, applied as a direction |

- **Source fact:** XYZ Euler order is explicitly declared on the Rotation socket; the GPU Euler matrix is also inspectable. [S15], [S16] In column-vector notation, this corresponds to `Rz @ Ry @ Rx`; use Blender's `Euler(..., 'XYZ')` rather than guessing signs/order from a different convention.
- **Source fact:** TEXTURE is not merely POINT with negative translation, nor POINT with negated Euler components in the same forward order. Its rotation is transposed/inverted and its reciprocal scale is applied **after** inverse rotation. [S13], [S14]
- **Source fact:** `safe_divide(a,b)` yields `0` where the corresponding divisor is exactly zero. Thus the singular-scale TEXTURE operation is a defined shader componentwise fallback, **not** a matrix inverse. Negative scale remains signed division. [S13], [S17] This zero-scale behavior is distinct from the geometric singular-normal question in section 2.
- **API/source fact:** Location is only available for POINT and TEXTURE; Blender marks that socket unavailable for VECTOR/NORMAL. A caller must not unconditionally access `mapping.inputs['Location']` for every vector type. [D6], [S15] In the executed 5.0.1 probe, name lookup in VECTOR raised `KeyError` (and `.get('Location')` returned `None`) even though iteration could still list the socket.
- **Policy:** apply a supported Mapping transformation to UV input `(u,v,0)` before the exporter's established Blender-to-target V conversion. An extra V flip changes the coordinate convention and is not part of the Blender Mapping node formulas. Parent implementation/native evidence must establish the target UV convention separately. Preserve XYZ effects when evaluating a 3D rotation, even when only final X/Y are serialized. [S13], [S16]
- **Policy:** static socket defaults only define the shader result when the relevant inputs are unlinked and the evaluation time/state matches the export. These formulas do not justify ignoring links, animation, node groups, or unsupported coordinate sources. The node declares actual vector inputs, rather than static transform properties alone. [S15]

### Executed observation S1: actual CPU shader, not a Python-only formula check

A 4×4 internal float image was used as an emission-bake target; no image or blend file was saved. The shader was `Mapping -> VectorMath ADD(2,2,2) -> VectorMath SCALE(0.1) -> Emission -> Material Output`. The reversible encoding keeps the tested color channels positive while retaining negative mapped coordinates. CPU Cycles, one sample, one thread, and a 120-second process bound kept this probe small. Center-pixel encoded RGB matched the analytic formulas with **zero measured float-vector error** for all five cases on Blender 5.0.1.

Common values: `v=(.23,.41,.17)`, `t=(.11,-.07,.03)`, `rotation=(.31,-.27,.49)` radians, XYZ order. These intentionally exercise all rotation axes, nonuniform scale, and nonzero translation.

| Mode | Scale | Actual encoded center RGB |
| --- | --- | --- |
| POINT | `(1.3,.7,1.1)` | `(0.2199958861, 0.2223098725, 0.2365767062)` |
| TEXTURE | `(1.3,.7,1.1)` | `(0.2274694443, 0.2519590557, 0.1938407570)` |
| VECTOR | `(1.3,.7,1.1)` | `(0.2089958638, 0.2293098718, 0.2335767001)` |
| TEXTURE | `(0,.7,1.1)` | `(0.2000000030, 0.2519590557, 0.1938407570)` |
| TEXTURE | `(-1.3,.7,1.1)` | `(0.1725305766, 0.2519590557, 0.1938407570)` |

To reproduce with installed Blender only, use the following Python body with `timeout 120s blender --background --factory-startup --threads 1 --python-exit-code 1 --python-expr '<body>'`. It creates only in-memory datablocks. The first attempted probe incorrectly indexed the unavailable VECTOR Location socket and exited 1 after two successful bakes; the corrected mode-aware probe below ran all five and exited 0.

```python
import bpy
from mathutils import Vector, Euler
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 1
scene.cycles.use_denoising = False
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
m = bpy.data.meshes.new('ProbeMesh')
m.from_pydata([(0,0,0),(1,0,0),(1,1,0),(0,1,0)], [], [(0,1,2,3)])
m.update()
o = bpy.data.objects.new('Probe',m)
scene.collection.objects.link(o)
o.select_set(True)
bpy.context.view_layer.objects.active = o
uv = m.uv_layers.new(name='BakeUV')
for slot, co in zip(uv.uv, [(0,0),(1,0),(1,1),(0,1)]):
    slot.vector = co
mat = bpy.data.materials.new('ProbeMaterial')
mat.use_nodes = True
o.data.materials.append(mat)
nt = mat.node_tree
nt.nodes.clear()
mapping = nt.nodes.new('ShaderNodeMapping')
add = nt.nodes.new('ShaderNodeVectorMath')
add.operation = 'ADD'
add.inputs[1].default_value = (2,2,2)
scale = nt.nodes.new('ShaderNodeVectorMath')
scale.operation = 'SCALE'
scale.inputs['Scale'].default_value = .1
em = nt.nodes.new('ShaderNodeEmission')
out = nt.nodes.new('ShaderNodeOutputMaterial')
target = nt.nodes.new('ShaderNodeTexImage')
image = bpy.data.images.new('ProbeResult', width=4, height=4, float_buffer=True)
image.colorspace_settings.name = 'Non-Color'
target.image = image
nt.nodes.active = target
nt.links.new(mapping.outputs['Vector'], add.inputs[0])
nt.links.new(add.outputs['Vector'], scale.inputs[0])
nt.links.new(scale.outputs['Vector'], em.inputs['Color'])
nt.links.new(em.outputs[0], out.inputs['Surface'])
v, t = Vector((.23,.41,.17)), Vector((.11,-.07,.03))
rot = Euler((.31,-.27,.49), 'XYZ')
R = rot.to_matrix()
for mode, s in [('POINT',(1.3,.7,1.1)), ('TEXTURE',(1.3,.7,1.1)),
                ('VECTOR',(1.3,.7,1.1)), ('TEXTURE',(0,.7,1.1)),
                ('TEXTURE',(-1.3,.7,1.1))]:
    mapping.vector_type = mode
    mapping.inputs['Vector'].default_value = v
    if mapping.inputs.get('Location') is not None:
        mapping.inputs['Location'].default_value = t
    mapping.inputs['Rotation'].default_value = rot
    mapping.inputs['Scale'].default_value = s
    if mode == 'TEXTURE':
        pre = R.transposed() @ (v-t)
        expected = Vector(tuple(pre[i]/s[i] if s[i] != 0 else 0 for i in range(3)))
    else:
        expected = R @ Vector(tuple(v[i]*s[i] for i in range(3)))
        if mode == 'POINT':
            expected += t
    bpy.context.view_layer.update()
    bpy.ops.object.bake(type='EMIT', margin=0, use_clear=True)
    pixels = list(image.pixels)
    actual = Vector(pixels[4*(2*4+2):4*(2*4+2)+3])
    encoded = (expected+Vector((2,2,2)))*.1
    assert (actual-encoded).length < 3e-5, (mode,s,actual,encoded)
    print(mode, s, tuple(actual), (actual-encoded).length)
print('SHADER_PROBES_PASS', bpy.app.version_string, bpy.app.build_hash.decode())
```

## 5. What remains unknown / acceptance boundaries

1. **Version coverage:** the 4.2 API/source was inspected, but only installed Blender 5.0.1 was executed. Re-run the bounded probes on actual 4.2 and other supported runtime builds before claiming tested cross-version coverage. No all-future-4.2+ compatibility claim is made.
2. **Native-engine semantics:** Blender source does not determine O3D winding, UV origin, stored-matrix treatment, normal renormalization, or culling behavior. Those require the separate native-engine evidence; no renderer-policy guess should be recorded as an engine fact.
3. **Degenerate geometry:** G1 used nondegenerate polygons and a nonempty corner-normal collection. Empty normals, zero-area faces, singular transform acceptance, and numerical conditioning need explicit exporter failure/fallback policy; a successful `inverted_safe()` is not fidelity evidence. [D3], [S8]
4. **Shader coverage:** actual shader bakes exercised CPU Cycles with static constants only. EEVEE was source-checked through its GPU shader but not rendered; MaterialX, OSL, linked/animated Mapping inputs, node-group traversal, and From Instances were not runtime-tested. The report does not prescribe expanding support to them. [S11], [S13], [S14], [S15]
5. **UV stream limits:** explicit named maps and render-default maps have distinct semantics. This research establishes their selection contract, not a lossless solution for arbitrary simultaneous coordinate sources in one O3D UV stream. [S10], [S11]

## Primary-source index

[D1]: https://docs.blender.org/api/4.2/bpy.types.Depsgraph.html#dependency-graph-object-to-mesh
[D2]: https://docs.blender.org/api/4.2/bpy.types.Object.html#bpy.types.Object.to_mesh
[D3]: https://docs.blender.org/api/4.2/bpy.types.Mesh.html#bpy.types.Mesh.corner_normals
[D4]: https://docs.blender.org/api/4.2/bpy.types.MeshLoopTriangle.html#bpy.types.MeshLoopTriangle.split_normals
[D5]: https://docs.blender.org/api/4.2/bpy.types.MeshUVLoopLayer.html#bpy.types.MeshUVLoopLayer.active_render
[D6]: https://docs.blender.org/manual/en/4.2/render/shader_nodes/vector/mapping.html#properties
[S0]: https://api.github.com/repos/blender/blender/git/ref/tags/v4.2.0
[S1]: https://github.com/blender/blender/blob/a51f293548adba0dda086f5771401e8d8ab66227/source/blender/makesrna/intern/rna_object_api.cc#L1075-L1100
[S2]: https://github.com/blender/blender/blob/a51f293548adba0dda086f5771401e8d8ab66227/source/blender/blenkernel/intern/mesh_normals.cc#L266-L310
[S3]: https://github.com/blender/blender/blob/a51f293548adba0dda086f5771401e8d8ab66227/source/blender/makesrna/intern/rna_mesh_api.cc#L85-L88
[S4]: https://github.com/blender/blender/blob/a51f293548adba0dda086f5771401e8d8ab66227/source/blender/blenkernel/intern/mesh_runtime.cc#L229-L247
[S5]: https://github.com/blender/blender/blob/a51f293548adba0dda086f5771401e8d8ab66227/source/blender/makesrna/intern/rna_mesh.cc#L684-L714
[S6]: https://github.com/blender/blender/blob/a51f293548adba0dda086f5771401e8d8ab66227/intern/cycles/kernel/geom/object.h#L191-L211
[S7]: https://github.com/blender/blender/blob/a51f293548adba0dda086f5771401e8d8ab66227/intern/cycles/kernel/geom/triangle.h#L16-L32
[S8]: https://github.com/blender/blender/blob/a51f293548adba0dda086f5771401e8d8ab66227/source/blender/python/mathutils/mathutils_Matrix.cc#L1690-L1810
[S9]: https://github.com/blender/blender/blob/a51f293548adba0dda086f5771401e8d8ab66227/source/blender/makesrna/intern/rna_mesh.cc#L2385-L2410
[S10]: https://github.com/blender/blender/blob/a51f293548adba0dda086f5771401e8d8ab66227/intern/cycles/blender/mesh.cpp#L447-L484
[S11]: https://github.com/blender/blender/blob/a51f293548adba0dda086f5771401e8d8ab66227/intern/cycles/scene/shader_nodes.cpp#L3940-L3968
[S12]: https://github.com/blender/blender/blob/a51f293548adba0dda086f5771401e8d8ab66227/source/blender/nodes/shader/nodes/node_shader_tex_image.cc#L54-L58
[S13]: https://github.com/blender/blender/blob/a51f293548adba0dda086f5771401e8d8ab66227/source/blender/gpu/shaders/material/gpu_shader_material_mapping.glsl#L15-L32
[S14]: https://github.com/blender/blender/blob/a51f293548adba0dda086f5771401e8d8ab66227/intern/cycles/kernel/svm/mapping_util.h#L9-L24
[S15]: https://github.com/blender/blender/blob/a51f293548adba0dda086f5771401e8d8ab66227/source/blender/nodes/shader/nodes/node_shader_mapping.cc#L18-L81
[S16]: https://github.com/blender/blender/blob/a51f293548adba0dda086f5771401e8d8ab66227/source/blender/gpu/shaders/common/gpu_shader_common_math_utils.glsl#L188-L209
[S17]: https://github.com/blender/blender/blob/a51f293548adba0dda086f5771401e8d8ab66227/source/blender/gpu/shaders/common/gpu_shader_common_math_utils.glsl#L10-L12
