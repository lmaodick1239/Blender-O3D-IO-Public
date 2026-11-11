"""Build synthetic native validation assets, never a native rendering claim.

Blender: blender -b --factory-startup --python-exit-code 1 --python
        tests/build_native_validation.py -- [--output-dir NEW_DIR]
        [--compare-reference EXPLICIT_CHECKOUT]
Python: python3 tests/build_native_validation.py --self-test
        python3 tests/build_native_validation.py --verify-package PACKAGE
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / 'tests') not in sys.path:
    sys.path.insert(0, str(ROOT / 'tests'))


def self_test():
    """Catch escaped/missing asset acceptance and destructive output reuse."""
    scratch = ROOT / '.superpowers/native-validation'
    scratch.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix='verifier-test-', dir=scratch))
    (directory / 'mesh.o3d').write_bytes(b'sentinel')
    assert inside_file(directory, 'mesh.o3d') == directory / 'mesh.o3d'
    for bad in ('missing.o3d', '../outside.o3d', '/absolute.o3d', 'C:\\outside.o3d'):
        try:
            inside_file(directory, bad)
        except (ValueError, FileNotFoundError):
            pass
        else:
            raise AssertionError(f'accepted unsafe/missing reference {bad}')
    try:
        new_output(directory)
    except FileExistsError:
        pass
    else:
        raise AssertionError('accepted existing output directory')
    assert (directory / 'mesh.o3d').read_bytes() == b'sentinel'
    (directory / 'bad.cfg').write_text('[mesh]\nmissing.o3d\n', encoding='ascii')
    try:
        config_references(directory, directory / 'bad.cfg')
    except FileNotFoundError:
        pass
    else:
        raise AssertionError('accepted missing CFG mesh')
    empty = directory / 'false-ready'
    empty.mkdir()
    (empty / 'manifest.json').write_text(json.dumps({
        'native_status': 'NOT RENDERED', 'origin_animation_ready': False,
        'files': {}, 'cases': [{'name': str(i), 'exports': {}} for i in range(13)]}), encoding='ascii')
    try:
        verify_package(empty)
    except (AssertionError, ValueError, KeyError):
        pass
    else:
        raise AssertionError('accepted falsely ready package with no corrected meshes')
    print('NATIVE PACKAGE SELF TEST PASS (scratch retained)', directory)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inside_file(root, relative):
    """Resolve only existing, package-contained, non-symlink regular files."""
    from pathlib import PureWindowsPath
    path = Path(relative.replace('\\', '/'))
    if (path.is_absolute() or PureWindowsPath(relative).drive or '..' in path.parts
            or not path.parts):
        raise ValueError(f'unsafe relative asset path: {relative}')
    root = root.resolve()
    candidate = root / path
    if not candidate.resolve().is_relative_to(root):
        raise ValueError(f'asset escapes package: {relative}')
    if any(p.is_symlink() for p in (candidate, *candidate.parents) if p != root.parent):
        raise ValueError(f'symlink asset: {relative}')
    if not candidate.is_file():
        raise FileNotFoundError(candidate)
    return candidate


def new_output(path):
    # Never clean or overwrite a caller's existing input/output directory.
    path = path.absolute()
    if path.exists() or path.is_symlink():
        raise FileExistsError(f'output must not exist: {path}')
    path.mkdir(parents=True, exist_ok=False)
    return path.resolve()


def config_references(root, path):
    """Check every emitted command, not a best-effort search for known paths."""
    lines = path.read_text(encoding='ascii').splitlines()
    references = []
    arities = {'[mesh]': 1, '[groups]': 2, '[friendlyname]': 1,
               '[matl]': 2, '[matl_alpha]': 1}
    i = 0
    while i < len(lines):
        command = lines[i].strip()
        i += 1
        if not command:
            continue
        if command not in arities:
            raise ValueError(f'unsupported package command {command} in {path}')
        count = arities[command]
        args = lines[i:i + count]
        if len(args) != count or any(not arg for arg in args):
            raise ValueError(f'incomplete {command} in {path}')
        i += count
        if command == '[mesh]':
            base = path.parent / 'model' if path.suffix == '.sco' else path.parent
            references.append(inside_file(root, (base.relative_to(root) / args[0]).as_posix()))
        elif command == '[matl]':
            base = path.parent / 'texture' if path.suffix == '.sco' else path.parent.parent / 'texture'
            references.append(inside_file(root, (base.relative_to(root) / args[0]).as_posix()))
            if int(args[1]) != 0:
                raise ValueError('package has only one material per mesh')
        elif command == '[matl_alpha]' and args[0] not in ('0', '1', '2'):
            raise ValueError('invalid alpha mode')
    return references


def verify_package(root):
    """Stdlib + independent strict decoder; runs without Blender or add-on."""
    import math
    from o3d_export_support import read_export
    root = root.resolve()
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest['native_status'] == 'NOT RENDERED'
    assert manifest['origin_animation_ready'] is False
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    assert actual == set(manifest['files']) | {'manifest.json'}, 'inventory mismatch'
    for relative, expected_hash in manifest['files'].items():
        assert digest(inside_file(root, relative)) == expected_hash, relative
    required = {'flat_wedge', 'smooth_wedge', 'oblique_triangle', 'negative_scale',
                'roughness_0', 'roughness_quarter', 'roughness_half', 'roughness_1',
                'emission', 'mapping_point', 'mapping_vector', 'translation', 'weighted_rest'}
    assert {case['name'] for case in manifest['cases']} == required
    assert len(manifest['cases']) == len(required)
    for case in manifest['cases']:
        assert case['exports']['corrected']['status'] == 'EXPORTED', 'missing corrected mesh'
    checked_meshes, referenced_meshes = set(), set()
    for path in sorted(root.rglob('*')):
        if path.suffix in ('.cfg', '.sco'):
            referenced_meshes.update(p for p in config_references(root, path) if p.suffix == '.o3d')
    powers = {'roughness_0': 1000., 'roughness_quarter': 750.,
              'roughness_half': 500., 'roughness_1': 0.}
    for case in manifest['cases']:
        for label, entry in case['exports'].items():
            if entry['status'] != 'EXPORTED':
                assert 'mesh' not in entry and 'comparison' not in entry
                continue
            path = inside_file(root, entry['mesh'])
            checked_meshes.add(path)
            records = read_export(path.read_bytes())
            assert records['version'] == 7 and records['vertices'] and records['triangles']
            for tri in records['triangles']:
                assert all(0 <= index < len(records['vertices']) for index in tri[:3])
                assert 0 <= tri[3] < len(records['materials'])
            for vertex in records['vertices']:
                assert all(math.isfinite(v) for v in vertex)
            for material in records['materials']:
                if material[-1]:
                    texture = inside_file(root, str(Path(entry['texture_dir']) / material[-1]))
                    assert digest(texture) == manifest['texture_sha256']
            if label != 'corrected':
                continue  # Reference is observation, not our correctness oracle.
            expected = case['expected_corners']
            actual_corners = [records['vertices'][i] for tri in records['triangles'] for i in tri[:3]]
            for left, right in ((actual_corners, expected), (expected, actual_corners)):
                assert all(any(max(abs(a-b) for a, b in zip(v, w)) < 2e-4
                               for w in right) for v in left), case['name']
            assert max(abs(a-b) for row, want in zip(records['matrix'], case['expected_origin'])
                       for a, b in zip(row, want)) < 2e-4
            material = records['materials'][0]
            if case['name'] in powers:
                assert material[10] == powers[case['name']]
                assert any(v > 0 for v in material[4:7]), 'invisible specular swatch'
            if case['name'] == 'emission':
                assert all(abs(a-b) < 2e-6 for a, b in zip(material[7:10], (.6, .9, 1.2)))
            if case['name'] == 'oblique_triangle':
                assert all(max(abs(a-b) for a, b in zip(v[3:6], (.3, math.sqrt(.75), .4))) < 2e-4
                           for v in records['vertices'])
            if case['name'] == 'translation':
                assert records['matrix'][3][:3] == (2., 4., -3.)
            if case['name'] == 'weighted_rest':
                assert [name for name, _ in records['bones']] == ['Main']
                weights = dict(records['bones'][0][1])
                assert set(weights) == set(range(len(records['vertices'])))
                assert all(weight == 1. for weight in weights.values())
                assert len(records['vertices']) > 4, 'weighted UV splits missing'
    assert checked_meshes == referenced_meshes, 'missing or orphan mesh declaration'
    assert checked_meshes == set(root.rglob('*.o3d')), 'unverified/failed mesh output'
    return manifest


README = '''# Synthetic O3D native validation package — NOT RENDERED

No OMSI/Wine was launched. Structural verification is NOT a native load test,
texture-orientation result, BRDF equivalence result, or origin-animation result.
No original motivating user asset was supplied. All meshes/materials/textures
are generated by the repository's deterministic smoke_export_fidelity corpus;
no .blend, third-party model, executable, research dump or external image is here.
Generated synthetic assets may be redistributed under CC0-1.0.

## Layout and installation (manual, authorized host only)

Each cases/<case>/<variant>/ directory is a separate scenery object root with
model/*.o3d, model/*.cfg, texture/arrow-checker.png and a root *.sco. The SCO
uses the conventional model-relative mesh and object-relative texture layout;
the paired model CFG uses CFG-relative mesh names. Load ONE declaration, not
both CFG and SCO. CFGs are fragments for an existing authorized host, not a bus.
Native loader search, SCO parsing, editor visibility, sizing and texture decode
remain UNOBSERVED. Exact-case references and content hashes are checked locally.

1. Have an authorized usable OMSI installation, complete map/host and rendering
   device first. This package supplies none. Do not create a prefix, install a
   runtime or change graphics configuration merely to validate it.
2. Copy this synthetic object's case/variant directory to a NEW directory under
   that installation's Sceneryobjects. Do not overwrite existing user assets.
   Open its SCO with the normal OMSI map editor/object placement UI. No guessed
   CLI launch flags or scripted system variables are supplied.
3. Place corrected and reference at the SAME transform, testing one at a time
   to prevent overlap. Preserve identical camera pose/FOV, placement, sun and
   lights, date/time, weather, wetness, exposure/render mode and material/texture
   overrides; record exact values, runtime build, settings and asset hashes.
4. First confirm logs show the actual mesh and texture loaded. Missing files,
   unsupported reference exports or absent host wiring are NOT passing results.
5. Capture each comparison separately; retain images only after actual native
   observation and name the draw path (ordinary / clone / special / effect).

## Separate checks and expected observables (predictions, not observations)

- Normals: flat/smooth wedge and oblique_triangle: compare face boundaries versus
  smooth shading under a grazing light. Corrected literal normal is
  (.3,sqrt(.75),.4). The asymmetric triangle and wedge are deliberately small.
- Mirror/culling: negative_scale has negative X scale on an asymmetric triangle.
  Inspect front and back separately, recording cull state, not just brightness.
- Specular: four roughness cases have nonzero specular level .5 (the one explicit
  swatch adaptation to corpus defaults). Power is 1000/750/500/0. Compare highlight
  width under the SAME light and camera; these are lossy authoring policy values,
  not a PBR/OMSI BRDF equivalence claim. Zero Power behavior still needs capture.
- Emission: constant (.2,.3,.4)*3 is serialized (.6,.9,1.2), including HDR blue.
  Compare in a separately fixed dark scene, no night/light/env/bump overrides.
- UV: mapping_point and mapping_vector use the render UV layer, not the editing
  layer, then their Mapping transform and one final V conversion. The asymmetric
  arrow/checker has rows RBBB/GRBW/GGRA/YWGY bottom-to-top. Distinguish both axes,
  coordinate baking, loader orientation, wrap/mips and texture color transfer.
- Alpha: use mapping_point's identical textured geometry in model alpha0/1/2 CFG
  or root alpha0/1/2 SCO variants, swapping only mode. Texture alpha varies
  1/.75/.5/.25. Capture 2->1 and 0->1 order, then a textureless wedge. Do not infer
  material-alpha multiplication or history independence from serialized alpha.
- Origin: translation has location (2,-3,4) Blender / pivot (2,4,-3) export plus
  Euler rotation (.31,-.27,.49). Exact row-vector frame and source geometry are
  in manifest.json. It is STATIC-LOAD ONLY, NOT ANIMATION-READY: no complete
  primary-supported animation declaration/variable driver contract was retained.
  On a separately authorized, known-working host, bind exactly this mesh's origin
  using that host's documented animation syntax. Keep parents absent and placement
  W fixed; first B=I, then row-vector Rx(.37 radians), then return B=I. Capture O,
  inverse(O), B and W and compare O^-1 B O W. Pivot must stay fixed and neutral
  animation must cancel O. Bound this to those three states; do not invent .osc
  variables or compensate geometry. Without host wiring record NOT TESTED.
- Skin/rest: weighted_rest is SEPARATE. Export ignores the posed armature so rest
  geometry and split weights survive; HelperNotABone is omitted, Main weights=1.
  Scenery declaration is a static rest-view only. Native bone binding/animation
  needs an existing documented host; no guessed setbone slot, smoothskin or rig
  driver is supplied. Reference is deliberately not comparable: its weights=False
  does not establish legal fixed-Hf weights or runtime skinning behavior.

## Exact Task3 native gates still OPEN

Task3 contract source: docs/research/evidence/o3d-export-fidelity/task-3/README.md
in the source repository (not shipped here); its SHA256 is in manifest provenance.
All below require retained native draw-state captures, not byte agreement:

- Original/clone/special draws 007c7624/007c765e/007c759c: mesh/subset/HRESULT,
  FVF/stride/VB/IB, world/view/projection, shader/stateblock IDs, CULLMODE22,
  NORMALIZENORMALS143, LIGHTING137, SPECULARENABLE29. Skin clone recomputes normals;
  ordinary, skin, spline and encrypted branches must not be conflated.
- Effect 007fda51, 007fdb1d/007fdb78, 007c75e8: actual technique/shaders, parameters,
  constants and whether fixed-function SetMaterial 007fe2ce is bypassed.
- Alpha/history and stale binding: stage COLOR/ALPHA args/ops, blend/test/ref/func,
  separate-alpha and texture transitions, including negative-handle 007fc500 and
  binding 007fc828. Mode1 may inherit blend state from mode2.
- Texture transfer: loader 007f88a4/resolver 007f93f8/bind 007fc828, formats/mips,
  sampler SRGBTEXTURE11, SRGBWRITEENABLE194, target format and display transfer.
- Dynamic env/bump/light/night maps: P+0a/+0b/+0d/+12, handles +34/+3c/+44/+50,
  factors +4c/+54 and variable arrays +40; this simple package does NOT close them.
- Origin: 005ef49f/005ef4be, 005fc757/005fcc92/005fcccc, 005fd641, 007c3263:
  O/inverse return/B/accumulator/W/branch flags. Singular/encrypted/special paths
  and noncommuting global frame remain outside this package.
- CFG: 005f4b44, 007fc04d/007fc197/007fc203 provider/line strings/selected P/null;
  repeated-texture ranks and fourteen-float allcolor are regression contracts,
  not runtime-proven by these override-free single-material declarations.
- UV: 00800d73, 007fe6b9 and final draw stage11/24, transforms/bindings/technique;
  effect/loader orientation and cross-backend parity remain unobserved.

## Rebuild and verify from the source repository

Use a new output directory; existing directories are refused, never cleaned.
Reference generation is opt-in; without the last option reference entries are
NOT_REQUESTED. The unmodified private reference source is never copied here.

```sh
blender --background --factory-startup --python-exit-code 1 --python tests/build_native_validation.py -- --output-dir .superpowers/native-validation/new-package --compare-reference /explicit/reference/checkout
python3 -B tests/build_native_validation.py --self-test
python3 -B tests/build_native_validation.py --verify-package .superpowers/native-validation/new-package/bundle
```

The manifest records exact source SHA256 values, HEAD and paths differing from
HEAD, exporter settings, source geometry, expected corners/origin and Blender
build. That provenance, not HEAD alone, identifies a pre-final-freeze package.
The source repository is required to regenerate; no software installer is bundled.

## Recording results

Record PASS/DIFFERENT/NOT TESTED per isolated check and draw branch, plus source,
package and runtime hashes. Reference byte differences are comparison observations,
not native failures or successes. VECTOR may throw in the unmodified reference;
its manifest entry has no mesh/config and is not a passing comparison. No reference
was requested unless explicitly supplied on the generator command line. A successful
package verifier only proves local inventory, paths, hashes and decoded values.
'''


def source_provenance(reference):
    import subprocess
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    sources = [ROOT / '__init__.py', *sorted((ROOT / 'o3d_io').rglob('*.py')),
               *(ROOT / 'tests' / name for name in ('build_native_validation.py',
                 'smoke_export_fidelity.py', 'smoke_support.py', 'o3d_export_support.py'))]
    contract = ROOT / 'docs/research/evidence/o3d-export-fidelity/task-3/README.md'
    hashes = {p.relative_to(ROOT).as_posix(): digest(p) for p in sources}
    differences = []
    for relative, actual in hashes.items():
        archived = subprocess.run(['git', 'show', f'{commit}:{relative}'], cwd=ROOT,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if archived.returncode or hashlib.sha256(archived.stdout).hexdigest() != actual:
            differences.append(relative)
    result = {'head': commit, 'sha256': hashes, 'source_paths_differing_from_head': differences,
              'task3_contract_sha256': digest(contract) if contract.is_file() else None}
    if reference:
        result['reference_sha256'] = {p.relative_to(reference).as_posix(): digest(p)
                                     for p in sorted((reference / 'io_export_o3d').glob('*.py'))}
    return result


def build(output, reference_path=None, addon=None):
    """Reuse a caller-owned registered add-on, or own standalone registration."""
    import contextlib
    import io
    import shutil
    import bpy
    from bpy_extras import node_shader_utils
    from mathutils import Matrix
    import smoke_export_fidelity as corpus
    from smoke_support import load_addon
    from o3d_export_support import read_export, oriented_surface

    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        raise RuntimeError('run in Object mode; caller context will not be coerced')
    reference_path = Path(reference_path).resolve() if reference_path else None
    reference = corpus._reference_exporter(reference_path) if reference_path else None
    provenance = source_provenance(reference_path)
    output = new_output(output)
    root = output / 'bundle'
    root.mkdir()
    manifest = {'native_status': 'NOT RENDERED', 'origin_animation_ready': False,
                'structural_status': 'INCOMPLETE', 'blender': bpy.app.version_string,
                'blender_build': bpy.app.build_hash.decode(), 'source': provenance,
                'reference_requested': reference is not None,
                'evidence_limits': ['No native runtime/load/render observation',
                    'Bytes do not prove texture/BRDF/alpha/culling/origin parity',
                    'Origin has no executable animation declaration; manual host setup required',
                    'Skin case has no native bone driver/binding; static rest-view only',
                    'Reference VECTOR may fail; wide bone output deliberately not compared',
                    'Only this exact Blender build used for package generation; not a compatibility matrix'],
                'cases': []}
    selections = [('custom_normal', n) for n in ('flat_wedge', 'smooth_wedge', 'oblique_triangle')]
    selections += [('transforms', 'negative_scale')]
    selections += [('materials', n) for n in ('roughness_0', 'roughness_quarter', 'roughness_half', 'roughness_1', 'emission')]
    selections += [('uv_mapping', n) for n in ('mapping_point', 'mapping_vector')]
    # Add translation and skin; alpha variants reuse mapping_point's checker.
    selections += [('transforms', 'translation'), ('transforms', 'weighted_rest')]
    owned = addon is None
    addon = load_addon() if owned else addon
    if owned:
        addon.register()
    try:
        for group, name in selections:
            collections = (bpy.data.objects, bpy.data.meshes, bpy.data.armatures,
                           bpy.data.materials, bpy.data.images)
            before = [set(collection) for collection in collections]
            active, selected = bpy.context.view_layer.objects.active, list(bpy.context.selected_objects)
            scratch = root / 'cases' / name
            scratch.mkdir(parents=True)
            try:
                obj, settings = corpus._make_case(group, name, scratch)
                adaptations = []
                if name.startswith('roughness_'):
                    wrapper = node_shader_utils.PrincipledBSDFWrapper(obj.data.materials[0], is_readonly=False)
                    wrapper.specular = .5
                    settings['shader']['specular'] = .5
                    adaptations.append('specular level .5 instead of corpus zero, so highlight is observable')
                if name == 'translation':
                    obj.rotation_euler = (.31, -.27, .49)
                    adaptations.append('add corpus Euler rotation to translated-origin fixture')
                    bpy.context.view_layer.update()
                snapshot = corpus._snapshot(obj)
                rest = corpus._evaluated_rest_snapshot(obj, settings['export_custom_normals'])
                expected = corpus._expected_corners(obj, settings, rest)
                origin = (corpus.AXIS.to_4x4() @ obj.matrix_world @ corpus.AXIS.to_4x4()).transposed()
                case = {'group': group, 'name': name, 'settings': settings, 'adaptations': adaptations,
                        'input': snapshot, 'expected_corners': expected,
                        'expected_origin': [list(row) for row in origin], 'exports': {}}
                manifest['cases'].append(case)
                image = scratch / 'arrow-checker.png'
                if not image.exists():
                    corpus._image(scratch)
                texture_hash = digest(image)
                if 'texture_sha256' in manifest:
                    assert manifest['texture_sha256'] == texture_hash
                manifest['texture_sha256'] = texture_hash
                for label in ('corrected', 'reference'):
                    entry = case['exports'][label] = {}
                    if label == 'reference' and (reference is None or name == 'weighted_rest'):
                        entry.update(status='NOT_REQUESTED' if reference is None else 'NOT_COMPARABLE',
                                     reason='explicit reference path absent' if reference is None else
                                     'reference weights=False cannot compare fixed-Hf rest/skin contract')
                        continue
                    variant = scratch / label
                    model, texture = variant / 'model', variant / 'texture'
                    model.mkdir(parents=True)
                    texture.mkdir()
                    shutil.copyfile(image, texture / image.name)
                    path = model / (label + '.o3d')
                    stdout = io.StringIO()
                    context = corpus._context_snapshot()
                    try:
                        with contextlib.redirect_stdout(stdout):
                            if label == 'corrected':
                                addon.o3d_io.io_o3d_export.do_export(str(path), bpy.context,
                                    Matrix.Identity(4), True, 7, settings['export_custom_normals'], objects=[obj])
                            else:
                                reference(compatibility=False, transforms={'LOC', 'ROT', 'SCA'},
                                          origin=True, weights=False).export([obj], path)
                    except Exception as error:
                        if label != 'reference':
                            raise
                        entry.update(status='EXPORT_ERROR', error=f'{type(error).__name__}: {error}',
                                     reason='unmodified reference limitation; NO comparison result')
                        if path.exists():
                            raise RuntimeError('reference left partial mesh; package cannot be ready') from error
                        continue
                    finally:
                        entry['stdout'] = stdout.getvalue()
                        assert corpus._context_snapshot() == context
                        assert corpus._snapshot(obj) == snapshot, 'export mutated source'
                    records = read_export(path.read_bytes())
                    entry.update(status='EXPORTED', mesh=path.relative_to(root).as_posix(),
                                 texture_dir=texture.relative_to(root).as_posix(),
                                 settings={'version': 7, 'origin': True, 'global_scale': 1.,
                                           'local_transforms': ['LOC', 'ROT', 'SCA'],
                                           'weights': label == 'corrected' and bool(obj.vertex_groups)})
                    block = f'[mesh]\n{path.name}\n\n'
                    (model / (label + '.cfg')).write_text(block, encoding='ascii')
                    header = f'[groups]\n1\nO3D fidelity synthetic\n\n[friendlyname]\n{name} {label} NOT RENDERED\n\n'
                    (variant / (label + '.sco')).write_text(header + block, encoding='ascii')
                    if name == 'mapping_point':
                        for mode in (0, 1, 2):
                            alpha = block + f'[matl]\narrow-checker.png\n0\n\n[matl_alpha]\n{mode}\n'
                            (model / f'alpha{mode}.cfg').write_text(alpha, encoding='ascii')
                            (variant / f'alpha{mode}.sco').write_text(header + alpha, encoding='ascii')
                    if label == 'corrected':
                        corpus._assert_corners(records, expected)
                        corpus._assert_winding(records, rest, expected, obj, settings)
                        if name == 'weighted_rest':
                            corpus._assert_rest(records, obj, rest, expected)
                    else:
                        current = read_export(inside_file(root, case['exports']['corrected']['mesh']).read_bytes())
                        entry['comparison'] = {
                            'oriented_surface_equal_5dp': corpus._rounded(oriented_surface(current)) == corpus._rounded(oriented_surface(records)),
                            'matrix_equal_5dp': corpus._rounded(current['matrix']) == corpus._rounded(records['matrix']),
                            'evidence': 'byte/value observation only; not native rendering parity'}
            finally:
                if bpy.context.object and bpy.context.object.mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode='OBJECT')
                for collection, existing in zip(collections, before):
                    for item in set(collection) - existing:
                        collection.remove(item, do_unlink=True)
                bpy.ops.object.select_all(action='DESELECT')
                for obj in selected:
                    obj.select_set(True)
                bpy.context.view_layer.objects.active = active
    finally:
        if owned:
            addon.unregister()
    assert source_provenance(reference_path) == provenance, 'source changed during generation'
    (root / 'README.md').write_text(README, encoding='utf-8')
    manifest['structural_status'] = 'VERIFIED; native load/render NOT TESTED'
    manifest['files'] = {p.relative_to(root).as_posix(): digest(p)
                         for p in sorted(root.rglob('*')) if p.is_file()}
    (root / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')
    verify_package(root)
    archive = output / 'bundle.zip'
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as zipped:
        for path in sorted(root.rglob('*')):
            if path.is_file():
                zipped.write(path, path.relative_to(root).as_posix())
    with zipfile.ZipFile(archive) as zipped:
        assert zipped.testzip() is None
        assert set(zipped.namelist()) == set(manifest['files']) | {'manifest.json'}
        for name in zipped.namelist():
            assert hashlib.sha256(zipped.read(name)).hexdigest() == digest(inside_file(root, name))
    print('NATIVE PACKAGE VERIFIED — NOT RENDERED', root, 'zip SHA256', digest(archive))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / '.superpowers/native-validation/package')
    parser.add_argument('--compare-reference', type=Path, help='explicit unmodified exporter checkout; never auto-discovered')
    parser.add_argument('--verify-package', type=Path)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else None)
    if args.self_test:
        self_test()
    elif args.verify_package:
        verify_package(args.verify_package)
        print('NATIVE PACKAGE VERIFIED — NOT RENDERED')
    else:
        build(args.output_dir, args.compare_reference)


if __name__ == '__main__':
    main()
