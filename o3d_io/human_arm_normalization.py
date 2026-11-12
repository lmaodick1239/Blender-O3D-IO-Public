"""Read-only world-space arm elevation plans for canonical human rigs."""
import math

from mathutils import Matrix, Vector

from .mmd_rig import CANONICAL_NAMES


def _horizontal_yaw(delta, sign):
    delta = Vector(delta)
    length = delta.length
    projected = math.hypot(delta.x, delta.z)
    epsilon = max(1e-8, length * 1e-6)
    if not all(math.isfinite(value) for value in delta):
        raise ValueError('Arm normalization requires finite joint coordinates')
    if length <= 1e-8 or projected <= epsilon or sign * delta.x <= epsilon:
        raise ValueError('Arm normalization requires nonzero outward arm segments')
    if abs(delta.y) > max(.01, projected * .25):
        raise ValueError('Arm normalization supports coronal A/T poses; align forward-pointing arms first')
    angle = math.atan2(sign * delta.z, sign * delta.x)
    return Matrix.Identity(4) if abs(angle) <= 1e-6 else Matrix.Rotation(angle, 4, 'Y')


def _about(point, rotation):
    return Matrix.Translation(point) @ rotation @ Matrix.Translation(-point)


def build_arm_transforms(armature) -> dict[str, Matrix]:
    """Return per-canonical-bone rest transforms without changing the rig.

    The human export backend remains responsible for upright/uniform rig frames.
    Joint heads and pivots here are in world space; pose bones are never used.
    """
    if getattr(armature, 'type', None) != 'ARMATURE':
        raise ValueError('Arm normalization requires a canonical armature')
    missing = set(CANONICAL_NAMES) - set(armature.data.bones.keys())
    if missing:
        raise ValueError('Missing canonical rest bones: ' + ', '.join(sorted(missing)))
    world = armature.matrix_world
    if not all(math.isfinite(value) for row in world for value in row):
        raise ValueError('OA_L/OA_R: Arm normalization requires a finite world matrix')
    points = {name: world @ armature.data.bones[name].head_local for name in CANONICAL_NAMES}
    for name, point in points.items():
        if not all(math.isfinite(value) for value in point):
            raise ValueError(f'{name}: Arm normalization requires finite joint coordinates')
    if points['OA_L'].x * points['OA_R'].x >= 0:
        raise ValueError('OA_L/OA_R: Arm normalization requires opposite-X shoulders')

    transforms = {name: Matrix.Identity(4) for name in CANONICAL_NAMES}
    for side in ('L', 'R'):
        oa, ua, hand = (stem + '_' + side for stem in ('OA', 'UA', 'Hand'))
        shoulder, elbow, wrist = (points[name] for name in (oa, ua, hand))
        sign = 1 if shoulder.x > 0 else -1
        bone_name = oa
        try:
            upper = _about(shoulder, _horizontal_yaw(elbow - shoulder, sign))
            elbow_raised = upper @ elbow
            wrist_raised = upper @ wrist
            bone_name = ua
            forearm = _about(elbow_raised,
                             _horizontal_yaw(wrist_raised - elbow_raised, sign)) @ upper
        except ValueError as error:
            raise ValueError(f'{bone_name}: {error}') from error
        transforms[oa] = upper
        transforms[ua] = forearm
        transforms[hand] = forearm.copy()
    return transforms


def transform_landmark(transforms, bone_name, point_world) -> Vector:
    """Transform a world-space landmark; unlisted bones use identity."""
    return transforms.get(bone_name, Matrix.Identity(4)) @ Vector(point_world)
