"""Read-only Task 2 manifest/math checks; no native or Blender execution."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
I = [[float(i == j) for j in range(4)] for i in range(4)]
C = [[1., 0., 0., 0.], [0., 0., 1., 0.], [0., 1., 0., 0.], [0., 0., 0., 1.]]

def mul(a, b):
    return [[sum(x*y for x, y in zip(row, col)) for col in zip(*b)] for row in a]

def tr(a):
    return [list(c) for c in zip(*a)]

def inverse(a):
    n = len(a)
    rows = [list(row) + [float(i == j) for j in range(n)] for i, row in enumerate(a)]
    for j in range(n):
        pivot = max(range(j, n), key=lambda i: abs(rows[i][j]))
        rows[j], rows[pivot] = rows[pivot], rows[j]
        scale = rows[j][j]
        assert abs(scale) > 1e-14
        rows[j] = [x/scale for x in rows[j]]
        for k in range(n):
            if k != j:
                factor = rows[k][j]
                rows[k] = [x-factor*y for x, y in zip(rows[k], rows[j])]
    return [r[n:] for r in rows]

def diff(a, b):
    return max(abs(x-y) for ra, rb in zip(a, b) for x, y in zip(ra, rb))

def point(a, p):
    return [sum(x*y for x, y in zip(row, [*p, 1.])) for row in a][:3]

def unit(v):
    length = math.sqrt(sum(x*x for x in v))
    return [x/length for x in v]

base_path = ROOT/'docs/research/evidence/o3d-export-fidelity/task-2-baseline.json'
base = json.loads(base_path.read_text())
selected = {'identity', 'negative_scale', 'nonuniform_scale', 'translation', 'euler_rotation', 'quaternion_rotation', 'parent_transform', 'global_scale'}
records = []
for case in base['cases']:
    if case['group'] != 'transforms' or case['case'] not in selected:
        continue
    source, settings = case['input'], case['settings']
    scale = settings['global_scale']
    G = [[scale*x if i < 3 else x for x in row] for i, row in enumerate(I)]
    M = source['matrix_world']
    P = mul(mul(G, C), M)
    O = case['exporters']['current']['records']['matrix']
    origin_error = diff(O, tr(mul(P, C)))
    identity_error = diff(mul(inverse(O), O), I)
    assert origin_error < 3e-6 and identity_error < 1e-12
    theta = .37
    animation = [[1., 0., 0., 0.], [0., math.cos(theta), math.sin(theta), 0.], [0., -math.sin(theta), math.cos(theta), 0.], [0., 0., 0., 1.]]
    around_origin = mul(mul(inverse(O), animation), O)
    # Row origin translation is a fixed pivot of this conjugation.
    pivot = O[3][:3]
    pivot_after = point(tr(around_origin), pivot)
    pivot_error = max(abs(x-y) for x, y in zip(pivot, pivot_after))
    assert pivot_error < 1e-12
    L = [row[:3] for row in P[:3]]
    N = tr(inverse(L))
    authored = source['corner_normals'][0]
    normal = unit([sum(x*y for x, y in zip(row, authored)) for row in N])
    expected = case['expected_corners'][0]
    assert max(abs(x-y) for x, y in zip(normal, expected[3:6])) < 3e-6
    p = point(P, source['vertices'][source['loop_vertices'][0]])
    assert max(abs(x-y) for x, y in zip(p, expected[:3])) < 3e-6
    records.append({'case': case['case'], 'class': 'derived mathematics using retained Blender 5.0.1 observation inputs; not native execution', 'position_first_corner': p, 'normal_inverse_transpose': normal, 'row_origin': O, 'origin_vs_actual_position_frame_max_error': origin_error, 'no_animation_cancellation_error': identity_error, 'rotated_origin_pivot_error': pivot_error})
# Task 2's global matrix is scalar. A deliberately noncommuting extension is
# a derived counterexample, not a newly executed fixture or native result.
M = next(c for c in base['cases'] if c['case'] == 'parent_transform')['input']['matrix_world']
G = [[2., .3, 0., .7], [0., 3., 0., -.2], [0., 0., .5, 1.1], [0., 0., 0., 1.]]
P = mul(mul(G, C), M)
actual_frame = tr(mul(P, C))
old_frame = tr(mul(mul(mul(C, G), M), C))
noncommuting = {'class': 'derived mathematics only', 'G': G, 'M': M, 'actual_position_frame_row': actual_frame, 'current_formula_row': old_frame, 'max_error': diff(actual_frame, old_frame)}
assert noncommuting['max_error'] > 1.
result = {'input': str(base_path.relative_to(ROOT)), 'cases': records, 'noncommuting_global_extension': noncommuting, 'native_runtime_executed': False}
(OUT/'derived-math.json').write_text(json.dumps(result, indent=2)+'\n')
print(f'DERIVED_MATH_OK cases={len(records)} noncommuting_frame_error={noncommuting["max_error"]}')
